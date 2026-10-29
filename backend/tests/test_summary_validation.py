import sys
from collections import Counter
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

def build_sources(issue: IssueInput) -> dict:
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


def check_evidence(evidence: Evidence, sources: dict) -> tuple[bool, str | None]:
    try:
        Evidence.model_validate(
            evidence.model_dump(),
            context={"sources": sources},
        )
        return True, None
    except ValidationError as error:
        message = error.errors()[0]["msg"]

        if "evidence_url_not_found" in message:
            return False, "url_not_found"           # 없는 url로 근거를 만들었다
        if "source_type_mismatch" in message:
            return False, "source_type_mismatch"    # 출처의 유형이 다르다
        if "comment_id_mismatch" in message:
            return False, "comment_id_mismatch"     # 댓글 id가 다르다
        if "excerpt_not_found" in message:
            return False, "excerpt_not_found"       # 발췌문이 원문에 없다
        return False, "other_validation_error"      # 기타 오류


def collect_statistics(summary: IssueSummary, issue: IssueInput) -> dict:
    """모든 근거를 검사하고 간단한 통계를 반환한다."""
    sources = build_sources(issue)
    stats = {
        "total": 0,
        "matched": 0,
        "mismatched": 0,
        "source_types": Counter(),
        "mismatch_reasons": Counter(),
        "sections_without_evidence": [],
    }

    for section_name in SECTION_NAMES:
        section = getattr(summary, section_name)

        if section.text and not section.evidence:
            stats["sections_without_evidence"].append(section_name)

        for evidence in section.evidence:
            stats["total"] += 1
            stats["source_types"][evidence.source_type] += 1

            matched, reason = check_evidence(evidence, sources)
            if matched:
                stats["matched"] += 1
            else:
                stats["mismatched"] += 1
                stats["mismatch_reasons"][reason] += 1

    stats["match_rate"] = (
        stats["matched"] / stats["total"] * 100
        if stats["total"] else 0.0
    )
    return stats


def print_statistics(summary: IssueSummary, issue: IssueInput) -> None:
    stats = collect_statistics(summary, issue)

    print("\n=== 요약 근거 검증 통계 ===")
    print(f"요약 상태: {summary.status}")
    print(f"근거 총 개수: {stats['total']}")
    print(f"원문과 일치: {stats['matched']}")
    print(f"불일치: {stats['mismatched']}")
    print(f"근거 일치율: {stats['match_rate']:.2f}%")
    print(f"출처 유형별 개수: {dict(stats['source_types'])}")
    print(f"불일치 사유별 개수: {dict(stats['mismatch_reasons'])}")
    print(f"텍스트는 있지만 근거가 없는 섹션: {stats['sections_without_evidence']}")


def run_live_check() -> None:

    url = input("Input GitHub Issue URL: ")
    issue, summary = summarize(url)

    print("\n=== 요약 결과 ===")
    print(summary.model_dump_json(ensure_ascii=False, indent=2))
    print_statistics(summary, issue)


if __name__ == "__main__":
    run_live_check()