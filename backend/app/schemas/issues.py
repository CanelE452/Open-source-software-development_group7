"""선택한 Issue의 상세(본문·댓글·원문 링크) 응답 형식."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.collection import CollectedComment


class IssueDetailResponse(BaseModel):
    """Issue 본문과 댓글, 수집 범위·원문 링크. 요약 담당에게 넘기는 입력이기도 하다."""

    model_config = ConfigDict(extra="forbid")

    repository: str
    number: int
    title: str = ""
    html_url: str = ""
    state: str = "open"
    body: str | None = None
    author: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    comments: list[CollectedComment] = Field(default_factory=list)
    comment_count: int = 0
    collected_at: str
    # 댓글을 끝까지 못 받았으면 True.
    partial_collection: bool = False
    notes: list[str] = Field(default_factory=list)
