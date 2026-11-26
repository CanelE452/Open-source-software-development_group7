import json
import httpx
from pydantic import ValidationError

from backend.app.integrations.ollama import OllamaClient
from backend.app.schemas.summarization_schema import (
    Evidence,
    IssueInput,
    IssueSummary,
)


SECTION_NAMES = (
    "problem",
    "conditions",
    "solution",
    "discussion",
    "follow_up",
    "unknowns",
)

MAX_ISSUE_BODY_CHARS = 6000
MAX_PROMPT_COMMENTS = 10
MAX_COMMENT_BODY_CHARS = 800


class SummaryGenerationError(Exception):
    """Ollama 요약 실패."""


def build_sources(issue: IssueInput) -> dict[str, dict[str, object]]:
    sources = {}

    if issue.html_url:
        sources[issue.html_url] = {
            "text": issue.body or "",
            "source_type": "issue_body",
            "comment_id": None,
        }

    for comment in issue.comments:
        if comment.html_url:
            sources[comment.html_url] = {
                "text": comment.body or "",
                "source_type": "comment",
                "comment_id": comment.id,
            }

    return sources


def prepare_prompt_data(issue: IssueInput) -> dict:
    issue_data = issue.model_dump(mode="json")

    body = issue_data["body"] or ""
    if len(body) > MAX_ISSUE_BODY_CHARS:
        issue_data["body"] = body[:MAX_ISSUE_BODY_CHARS] + "\n...[내용 일부 생략]"

    comments = issue_data["comments"][-MAX_PROMPT_COMMENTS:]
    for comment in comments:
        comment_body = comment["body"] or ""
        if len(comment_body) > MAX_COMMENT_BODY_CHARS:
            comment["body"] = (
                comment_body[:MAX_COMMENT_BODY_CHARS] + "\n...[내용 일부 생략]"
            )

    issue_data["comments"] = comments
    return issue_data


def build_prompt(issue: IssueInput) -> str:
    schema = IssueSummary.model_json_schema()
    issue_data = prepare_prompt_data(issue)

    return f"""
You summarize GitHub Issues using only the supplied issue and comment data.
Return exactly one valid JSON object. Do not include Markdown fences or extra text.
Follow the JSON Schema below and include every required field.
Write the summary in Korean.
Do not invent facts, URLs, comments, or excerpts.
Every non-null section text must have at least one supporting evidence item.
Evidence excerpts must be copied from the supplied issue body or comments.
The evidence URL must exactly match the URL of its source.
Use source_type "issue_body" for the issue body and "comment" for a comment.
Include the exact comment_id when the source is a comment.
Do not include comment_id for issue_body evidence.
If a section cannot be supported by the supplied data, use null for text and [] for evidence.
Set status to "completed" only when the summary has sufficient supporting evidence;
otherwise set it to "insufficient_evidence".
Only the latest {MAX_PROMPT_COMMENTS} comments may be included. Long text may be truncated.

JSON Schema:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Issue data:
{json.dumps(issue_data, ensure_ascii=False, indent=2)}
"""


def parse_json_response(raw_response: str) -> dict:
    content = raw_response.strip()

    if content.startswith("```"):
        lines = content.splitlines()[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    data = json.loads(content)

    if not isinstance(data, dict):
        raise ValueError("요약 응답의 최상위 값은 JSON 객체여야 합니다.")

    return data


def validate_summary_evidence(issue: IssueInput, summary: IssueSummary) -> IssueSummary:
    sources = build_sources(issue)

    has_supported_text = False
    had_invalid_evidence = False

    for section_name in SECTION_NAMES:
        section = getattr(summary, section_name)
        valid_evidence = []

        for evidence in section.evidence:
            try:
                Evidence.model_validate(
                    evidence.model_dump(),
                    context={"sources": sources},
                )
            except ValidationError:
                had_invalid_evidence = True
                continue

            valid_evidence.append(evidence)

        section.evidence = valid_evidence

        if section.text and not valid_evidence:
            section.text = None
        elif section.text:
            has_supported_text = True

    if has_supported_text and not had_invalid_evidence:
        summary.status = "completed"
    else:
        summary.status = "insufficient_evidence"

    return summary


def summarize_issue(issue: IssueInput) -> IssueSummary:
    client = None

    try:
        client = OllamaClient()

        prompt = build_prompt(issue)
        raw_response = client.chat(prompt)

        result_data = parse_json_response(raw_response)
        result = IssueSummary.model_validate(result_data)

        return validate_summary_evidence(issue, result)

    except SummaryGenerationError:
        raise
    except (httpx.HTTPError, ValidationError, TypeError, ValueError, KeyError) as exc:
        raise SummaryGenerationError(
            "Ollama 요약에 실패했습니다."
        ) from exc
    finally:
        if client is not None:
            client.close()
