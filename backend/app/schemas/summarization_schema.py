from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

# 요약 근거 원문 기록
class Evidence(BaseModel):
    """A quote that can be checked against the original Issue or comment."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1, description="Canonical URL of the source")
    excerpt: str = Field(min_length=1, max_length=500)
    source_type: Literal["issue_body", "comment"]
    comment_id: int | None = None

# 요약 개별 섹션 객체
class SummarySection(BaseModel):
    """One summary category and its supporting source quotes."""

    model_config = ConfigDict(extra="forbid")

    text: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)

# 전체 요약 결과 구조
class IssueSummary(BaseModel):
    """Unified schema for both LLM output validation and final API output.
    `status` and `partial_collection` have defaults so the LLM response can omit
    them; the summarization service always overwrites them with trusted values."""

    model_config = ConfigDict(extra="forbid")

    problem: SummarySection     # Issue에서 보고한 문제와 증상
    conditions: SummarySection  # 문제 발생 환경, 버전, 실행 조건
    solution: SummarySection    # 제안되거나 확인된 해결 방법
    discussion: SummarySection  # 댓글에서 논의한 원인, 의견, 결론
    follow_up: SummarySection   # 추가 작업, 재현 확인, 후속 이슈
    unknowns: SummarySection    # 원문만으로 확인할 수 없는 정보
    status: Literal["completed", "insufficient_evidence", "failed"] = (
        "insufficient_evidence"
    )
    partial_collection: bool = False

# 댓글 입력 구조
class IssueComment(BaseModel):
    """Minimum comment data required by the summarization pipeline."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    html_url: str | None = None
    body: str | None = None

# 이슈 입력 구조
class IssueInput(BaseModel):
    """Normalized Issue input; callers may pass a dict or this model."""

    model_config = ConfigDict(extra="ignore")

    number: int | None = None
    title: str = ""
    body: str | None = None
    html_url: str = ""
    comments: list[IssueComment] = Field(default_factory=list)
    partial_collection: bool = False
