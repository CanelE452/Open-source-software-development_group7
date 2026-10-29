"""검색·요약 모듈과 API를 잇는 연결점(포트).

검색(`search/`, 김민재)과 요약(`summarization/`, 김민수)은 별도 브랜치에서 개발 중이다.
API는 아래 프로토콜에만 의존하고, 각 담당이 구현을 주입(`app.state`)한다. 아직 연결되지
않았으면 `Unavailable*Backend`가 `BackendUnavailable`을 던지고, 라우터는 이를 503으로
변환한다. 이렇게 하면 수집 API는 지금 동작하고, 검색·요약은 합류 시 교체만 하면 된다.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.app.schemas.collection import CollectedIssue, CollectionMetadata
from backend.app.schemas.issues import IssueDetailResponse
from backend.app.schemas.search import SearchRequest, SearchResponse
from backend.app.schemas.summary import SummaryResponse


class BackendUnavailable(Exception):
    """아직 연결되지 않은 모듈을 호출했을 때."""

    def __init__(self, backend: str, message: str) -> None:
        super().__init__(message)
        self.backend = backend
        self.message = message


@runtime_checkable
class SearchBackend(Protocol):
    """검색 담당이 구현할 계약."""

    available: bool

    def index(
        self,
        repository: str,
        issues: list[CollectedIssue],
        metadata: CollectionMetadata,
    ) -> None:
        """수집한 스냅샷을 색인한다."""

    def search(self, request: SearchRequest) -> SearchResponse:
        """문제 설명으로 관련 Issue 후보를 찾는다."""


@runtime_checkable
class SummaryBackend(Protocol):
    """요약 담당이 구현할 계약."""

    available: bool

    def summarize(self, issue: IssueDetailResponse) -> SummaryResponse:
        """수집한 원문으로 근거 기반 구조화 요약을 만든다."""


class UnavailableSearchBackend:
    """검색 모듈 합류 전 기본값."""

    available = False
    _message = "검색 모듈이 아직 연결되지 않았습니다 (search/, 김민재 담당)."

    def index(self, *args: object, **kwargs: object) -> None:
        raise BackendUnavailable("search", self._message)

    def search(self, request: SearchRequest) -> SearchResponse:
        raise BackendUnavailable("search", self._message)


class UnavailableSummaryBackend:
    """요약 모듈 합류 전 기본값."""

    available = False
    _message = "요약 모듈이 아직 연결되지 않았습니다 (summarization/, 김민수 담당)."

    def summarize(self, issue: IssueDetailResponse) -> SummaryResponse:
        raise BackendUnavailable("summary", self._message)
