import sys
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.summarization_schema import Evidence, IssueInput, IssueSummary
from app.summarization.summarize import summarize

SECTION_NAMES = (
    "problem",
    "conditions",
    "solution",
    "discussion",
    "follow_up",
    "unknowns",
)

# test issue https://github.com/huggingface/transformers/issues/876

REASON_MESSAGES = {
    "evidence_url_not_found": "근거 URL이 입력한 Issue 본문 또는 댓글 URL과 일치하지 않음",
    "source_type_mismatch": "source_type이 실제 출처 종류와 일치하지 않음",
    "comment_id_mismatch": "comment_id가 실제 댓글 ID와 일치하지 않음",
    "comment_id_for_issue_body": "Issue 본문 근거에 comment_id가 지정되어 있음",
    "excerpt_not_found": "발췌문이 해당 원문에 그대로 존재하지 않음",
}


def build_sources(issue: IssueInput) -> dict:
    sources = {}

    if issue.html_url:
        sources[issue.html_url] = {
            "text": issue.body or "",
            "source_type": "issue_body",
            "comment_id": None,
            "label": "Issue 본문",
        }

    for comment in issue.comments:
        if comment.html_url:
            sources[comment.html_url] = {
                "text": comment.body or "",
                "source_type": "comment",
                "comment_id": comment.id,
                "label": f"댓글 #{comment.id}" if comment.id is not None else "댓글",
            }

    return sources


def check_evidence(evidence: Evidence, sources: dict) -> str | None:
    try:
        Evidence.model_validate(
            evidence.model_dump(),
            context={"sources": sources},
        )
        return None
    except ValidationError as error:
        message = error.errors()[0]["msg"]
        for reason in REASON_MESSAGES:
            if reason in message:
                return reason
        return "other_validation_error"


def collect_mismatches(summary: IssueSummary, issue: IssueInput) -> list[dict]:
    sources = build_sources(issue)
    mismatches = []

    for section_name in SECTION_NAMES:
        section = getattr(summary, section_name)

        if section.text and not section.evidence:
            mismatches.append({
                "kind": "missing_evidence",
                "section": section_name,
                "summary_text": section.text,
                "reason": "요약 텍스트는 있지만 근거가 첨부되지 않음",
            })

        for index, evidence in enumerate(section.evidence, start=1):
            reason = check_evidence(evidence, sources)
            if reason is None:
                continue

            source = sources.get(evidence.url)
            mismatches.append({
                "kind": "invalid_evidence",
                "section": section_name,
                "evidence_index": index,
                "summary_text": section.text,
                "reason_code": reason,
                "reason": REASON_MESSAGES.get(reason, "Pydantic 근거 검증 중 기타 오류 발생"),
                "url": evidence.url,
                "source_type": evidence.source_type,
                "comment_id": evidence.comment_id,
                "excerpt": evidence.excerpt,
                "actual_source_type": source["source_type"] if source else None,
                "actual_comment_id": source["comment_id"] if source else None,
                "source_text": source["text"] if source else None,
            })

    return mismatches


def format_block(value: str | None) -> str:
    if value is None or value == "":
        return "(없음)"
    safe_value = value.replace("````", "''' '")
    return f"````text\n{safe_value}\n````"


def write_report(issue: IssueInput, summary: IssueSummary, mismatches: list[dict]) -> Path:
    report_dir = Path(__file__).resolve().parent / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"summary_validation_{timestamp}.md"

    lines = [
        "# GitHub Issue 요약 근거 검증 보고서",
        "",
        f"- 실행 시각: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- Issue: [{issue.title or f'Issue #{issue.number}'}]({issue.html_url})",
        f"- 요약 상태: `{summary.status}`",
        "",
        "## 검증 결과",
        "",
    ]

    if not mismatches:
        lines.append("근거 불일치 또는 근거 누락 항목이 없습니다.")
    else:
        for index, mismatch in enumerate(mismatches, start=1):
            section = mismatch["section"]
            lines.extend(["", f"## 불일치 {index}: `{section}`"])
            lines.extend(["", f"- 유형: `{mismatch['kind']}`"])
            lines.extend(["", f"- 사유: {mismatch['reason']}"])
            lines.extend(["", "### 요약 텍스트", "", format_block(mismatch.get("summary_text"))])

            if mismatch["kind"] == "missing_evidence":
                lines.extend([
                    "",
                    "근거가 첨부되지 않아 URL 및 원문 발췌문을 대조할 수 없습니다.",
                ])
                continue

            lines.extend([
                "",
                f"- 근거 순번: {mismatch['evidence_index']}",
                f"- 모델이 제시한 URL: {mismatch['url']}",
                f"- 모델이 제시한 출처 유형: `{mismatch['source_type']}`",
                f"- 모델이 제시한 댓글 ID: `{mismatch['comment_id']}`",
                "",
                "### 모델이 제시한 발췌문",
                "",
                format_block(mismatch["excerpt"]),
                "",
            ])

            if mismatch["actual_source_type"] is None:
                lines.append("- 해당 URL은 수집한 Issue 본문이나 댓글에서 찾을 수 없습니다.")
            else:
                lines.extend([
                    f"- 실제 출처 유형: `{mismatch['actual_source_type']}`",
                    f"- 실제 댓글 ID: `{mismatch['actual_comment_id']}`",
                    "",
                    "### 해당 URL의 실제 원문",
                    "",
                    format_block((mismatch.get("source_text") or "")[:2000]),
                ])
                source_text = mismatch.get("source_text") or ""
                if len(source_text) > 2000:
                    lines.append("(원문이 길어 앞부분 2,000자만 기록했습니다.)")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    url = input("Input GitHub Issue URL: ").strip()
    issue, summary = summarize(url)

    print("\n=== 요약 결과 ===")
    print(summary.model_dump_json(ensure_ascii=False, indent=2))

    mismatches = collect_mismatches(summary, issue)
    report_path = write_report(issue, summary, mismatches)
    print(f"\n검증 기록을 저장했습니다: {report_path}")


if __name__ == "__main__":
    main()