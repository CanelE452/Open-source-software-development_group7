import json
import os
import sys
from pathlib import Path
import httpx

BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

from app.integrations.ollama import OllamaClient
from app.schemas.summarization_schema import IssueInput, IssueSummary


# test issue https://github.com/huggingface/transformers/issues/876
GITHUB_API = "https://api.github.com"
OWNER = "huggingface"
REPO = "transformers"
ISSUE_NUMBER = 876


def fetch_issue(owner: str, repo: str, issue_number: int) -> IssueInput:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Issue-Finder",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    issue_path = f"/repos/{owner}/{repo}/issues/{issue_number}"
    comments_path = f"{issue_path}/comments"

    with httpx.Client(
        base_url=GITHUB_API,
        headers=headers,
        timeout=30.0,
    ) as client:
        issue_response = client.get(issue_path)
        issue_response.raise_for_status()
        issue_data = issue_response.json()

        comments_data = []
        page = 1
        while True:
            comments_response = client.get(
                comments_path,
                params={"per_page": 100, "page": page},
            )
            comments_response.raise_for_status()
            page_comments = comments_response.json()
            comments_data.extend(page_comments)

            if len(page_comments) < 100:
                break
            page += 1

    return IssueInput(
        number=issue_data["number"],
        title=issue_data.get("title") or "",
        body=issue_data.get("body"),
        html_url=issue_data["html_url"],
        comments=[
            {
                "id": comment.get("id"),
                "html_url": comment.get("html_url"),
                "body": comment.get("body"),
            }
            for comment in comments_data
        ],
        partial_collection=False,
    )


def main():
    ollama = OllamaClient()

    try:
        # 테스트 Issue와 댓글 가져오기
        issue = fetch_issue(OWNER, REPO, ISSUE_NUMBER)
        print(f"가져온 Issue: {issue.title}")
        print(f"Issue URL: {issue.html_url}")
        print(f"댓글 수: {len(issue.comments)}")

        # 스키마 생성
        schema = IssueSummary.model_json_schema()

        # Issue 데이터와 스키마를 프롬프트에 입력
        prompt = f"""
        You summarize GitHub Issues using only the supplied issue and comment data.

        Return exactly one valid JSON object. Do not include Markdown fences or extra text.
        Follow the JSON Schema below and include every required field.
        Write the summary in Korean.
        Do not invent facts, URLs, comments, or excerpts.
        Evidence excerpts must be copied exactly from the supplied issue body or comments.
        Use the URL of the corresponding source. Use source_type "issue_body" for the
        issue body and "comment" for a comment. Include comment_id when the source is a comment.
        If information is unavailable, use null for text and [] for evidence.
        Set status to "completed" if there is enough information to summarize, otherwise
        set it to "insufficient_evidence". Set partial_collection to false.

        JSON Schema:
        {json.dumps(schema, ensure_ascii=False, indent=2)}

        Issue data:
        {issue.model_dump_json(ensure_ascii=False, indent=2)}
        """
        raw_response = ollama.chat(prompt).strip()
        print(raw_response)

        # JSON 파싱 및 Pydantic 스키마 검증
        result_data = json.loads(raw_response)
        # 부분 수집 여부는 LLM 응답 대신 실제 입력 데이터 값을 사용
        result_data["partial_collection"] = issue.partial_collection
        result = IssueSummary.model_validate(result_data)

        # 6. 요약 결과 출력
        print("\n=== Issue Summary ===")
        print(result.model_dump_json(ensure_ascii=False, indent=2))

    except httpx.HTTPStatusError as exc:
        print(
            f"GitHub API 요청 실패: HTTP {exc.response.status_code}\n"
            f"URL: {exc.request.url}\n응답: {exc.response.text}"
        )
        raise
    finally:
        ollama.close()


if __name__ == "__main__":
    main()