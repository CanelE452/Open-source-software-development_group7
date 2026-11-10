"""검색 API.

입력 검증·응답 형식은 여기서, 실제 점수 계산은 검색 모듈(`search/`)이 담당한다.
검색 모듈 미연결 시 503을 돌려준다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.api.backends import SearchBackend
from backend.app.api.dependencies import get_search_backend
from backend.app.collection.repository import parse_repository
from backend.app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search_issues(
    payload: SearchRequest,
    search_backend: SearchBackend = Depends(get_search_backend),
) -> SearchResponse:
    """문제 설명으로 관련 Issue 후보를 찾는다."""

    owner, repo = parse_repository(payload.repository)  # 잘못된 입력은 400
    normalized = payload.model_copy(update={"repository": f"{owner}/{repo}"})
    return search_backend.search(normalized)
