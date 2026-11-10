"""근거 기반 구조화 요약 요청·응답 형식.

요약 생성은 요약 담당(`summarization/`, 김민수)이 구현한다. 여기서는 API 입·출력
형식만 정의하며, 요약 담당의 `IssueSummary`와 같은 항목·근거 구조를 따른다.
설명할 근거가 없으면 만들어 채우지 않는다(`text=null`, `evidence=[]`).
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SummaryStatus(str, Enum):
    completed = "completed"
    insufficient_evidence = "insufficient_evidence"
    failed = "failed"


class Evidence(BaseModel):
    """원문에서 그대로 복사한 근거 조각."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1)
    excerpt: str = Field(min_length=1, max_length=500)
    source_type: Literal["issue_body", "comment"]
    comment_id: int | None = None


class SummarySection(BaseModel):
    """요약 항목 하나와 그 근거."""

    model_config = ConfigDict(extra="forbid")

    text: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class SummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # 요약 담당이 모델 선택을 허용할 경우를 위한 선택 입력.
    model: str | None = None


class SummaryResponse(BaseModel):
    """요약 실패·근거 부족 시에도 원문과 확보한 근거를 계속 확인할 수 있어야 한다."""

    model_config = ConfigDict(extra="forbid")

    repository: str
    number: int
    html_url: str = ""
    problem: SummarySection = Field(default_factory=SummarySection)
    conditions: SummarySection = Field(default_factory=SummarySection)
    solution: SummarySection = Field(default_factory=SummarySection)
    discussion: SummarySection = Field(default_factory=SummarySection)
    follow_up: SummarySection = Field(default_factory=SummarySection)
    unknowns: SummarySection = Field(default_factory=SummarySection)
    status: SummaryStatus = SummaryStatus.insufficient_evidence
    partial_collection: bool = False
