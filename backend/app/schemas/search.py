"""검색 요청·응답 형식.

실제 점수 계산은 검색 담당(`search/`, 김민재)이 구현한다. 여기서는 API 입력 검증과
응답 형식만 정의한다. 점수는 중복 확률이나 해결 성공률로 표현하지 않는다.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.collection import CollectionScope


class SearchMethod(str, Enum):
    bm25 = "bm25"
    semantic = "semantic"
    hybrid = "hybrid"


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository: str = Field(min_length=1, description="`owner/repo` 또는 전체 URL")
    problem: str = Field(min_length=1, description="관찰한 문제 상황(필수)")
    error: str | None = Field(default=None, description="선택적 오류 메시지")
    environment: str | None = Field(default=None, description="선택적 버전·환경")
    method: SearchMethod = SearchMethod.hybrid
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int
    title: str
    html_url: str
    score: float
    score_type: str = Field(description="점수 종류: bm25 | semantic | hybrid")
    state: str | None = None


class SearchResponse(BaseModel):
    """검색 결과와 함께 어떤 스냅샷을 검색했는지 알려 준다."""

    model_config = ConfigDict(extra="forbid")

    repository: str
    method: SearchMethod
    results: list[SearchResultItem] = Field(default_factory=list)
    snapshot_id: str | None = None
    collected_at: str | None = None
    partial_collection: bool = False
    scope: CollectionScope | None = None
