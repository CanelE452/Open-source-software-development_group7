"""API가 `app.state`를 통해 사용하는 검색·요약 백엔드 계약."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.app.schemas.collection import CollectedIssue, CollectionMetadata
from backend.app.schemas.issues import IssueDetailResponse
from backend.app.schemas.search import SearchRequest, SearchResponse
from backend.app.schemas.summary import SummaryResponse


class BackendUnavailable(Exception):
    """요청한 백엔드를 실행할 수 없을 때."""

    def __init__(self, backend: str, message: str) -> None:
        super().__init__(message)
        self.backend = backend
        self.message = message


class SearchBackendError(Exception):
    """저장된 스냅샷을 읽거나 검색하는 도중 실패했다."""


@runtime_checkable
class SearchBackend(Protocol):
    """검색 담당이 구현할 계약."""

    available: bool

    def index(
        self,
        repository: str,
        issues: list[CollectedIssue],
        metadata: CollectionMetadata,
    ) -> str | None:
        """수집한 스냅샷을 색인하고 저장된 ID가 있으면 반환한다."""

    def search(self, request: SearchRequest) -> SearchResponse:
        """문제 설명으로 관련 Issue 후보를 찾는다."""


@runtime_checkable
class SummaryBackend(Protocol):
    """요약 담당이 구현할 계약."""

    available: bool

    def summarize(self, issue: IssueDetailResponse) -> SummaryResponse:
        """수집한 원문으로 근거 기반 구조화 요약을 만든다."""


class UnavailableSearchBackend:
    """검색 백엔드 미연결 상태를 나타낸다."""

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
