"""수집 결과 데이터 형식.

GitHub에서 수집한 Issue·댓글과, 수집 범위·시각·누락 여부를 기록하는 메타데이터를
정의한다. 저장(`storage/`)·검색(`search/`)·요약(`summarization/`)이 공유한다.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CollectedComment(BaseModel):
    """Issue 댓글 하나."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    html_url: str | None = None
    body: str | None = None
    author: str | None = None
    created_at: str | None = None


class CollectedIssue(BaseModel):
    """목록 수집으로 얻는 Issue 요약 정보(댓글 본문은 상세 수집에서 가져온다)."""

    model_config = ConfigDict(extra="ignore")

    number: int
    title: str = ""
    html_url: str = ""
    state: str = "open"
    body: str | None = None
    author: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    comment_count: int = 0
    labels: list[str] = Field(default_factory=list)


class CollectionScope(BaseModel):
    """어디까지 수집했는지 기록한다."""

    model_config = ConfigDict(extra="forbid")

    state: str = "all"
    per_page: int = 100
    max_issues: int = 0
    pages_fetched: int = 0
    issue_count: int = 0
    pull_requests_excluded: int = 0


class CollectionMetadata(BaseModel):
    """수집 시각·범위·부분 수집 여부. 스냅샷을 식별하는 `snapshot_id`를 포함한다."""

    model_config = ConfigDict(extra="forbid")

    repository: str
    collected_at: str
    snapshot_id: str
    scope: CollectionScope
    partial_collection: bool = False
    # 부분 수집·누락이 생긴 이유를 사람이 읽을 수 있게 남긴다.
    notes: list[str] = Field(default_factory=list)
