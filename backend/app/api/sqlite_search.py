"""수집 결과와 검색 HTTP 계약을 SQLite 스냅샷에 연결한다."""

import sqlite3
from contextlib import nullcontext
from pathlib import Path
from threading import Lock

from backend.app.api.backends import BackendUnavailable, SearchBackendError
from backend.app.core.config import REPO_ROOT
from backend.app.schemas.collection import (
    CollectedIssue,
    CollectionMetadata,
    CollectionScope,
)
from backend.app.schemas.search import (
    SearchMethod,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from backend.app.search import SearchEngine
from backend.app.search.embeddings import SentenceTransformerEmbedder
from backend.app.storage import Issue, SQLiteRepository


class SQLiteSearchBackend:
    available = True

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._embedder = SentenceTransformerEmbedder(cache_folder=REPO_ROOT / "data" / "models")
        self._embedding_lock = Lock()

    def index(
        self,
        repository: str,
        issues: list[CollectedIssue],
        metadata: CollectionMetadata,
    ) -> str:
        with SQLiteRepository(self._db_path) as db:
            snapshot = db.save_snapshot(
                repository,
                (
                    Issue(
                        number=issue.number,
                        title=issue.title,
                        body=issue.body or "",
                        url=issue.html_url,
                        state=issue.state,
                        updated_at=issue.updated_at,
                    )
                    for issue in issues
                ),
                collected_at=metadata.collected_at,
                collection_scope=metadata.scope.model_dump(),
                partial_collection=metadata.partial_collection,
            )
        return snapshot.snapshot_id

    def search(self, request: SearchRequest) -> SearchResponse:
        try:
            with SQLiteRepository(self._db_path) as db:
                return self._search(db, request)
        except (OSError, ValueError, sqlite3.DatabaseError) as exc:
            raise SearchBackendError from exc

    def _search(self, db: SQLiteRepository, request: SearchRequest) -> SearchResponse:
        use_model = request.method != SearchMethod.bm25
        engine = SearchEngine(db, embedder=self._embedder if use_model else None)
        try:
            with (self._embedding_lock if use_model else nullcontext()):
                result = engine.search(
                    request.repository,
                    request.problem,
                    error=request.error or "",
                    environment=request.environment or "",
                    method=request.method.value,
                    top_k=request.top_k,
                )
        except (ImportError, OSError, RuntimeError) as exc:
            if use_model:
                raise BackendUnavailable(
                    "search", "검색 모델을 불러오거나 실행할 수 없습니다."
                ) from exc
            raise

        snapshot = result.snapshot
        if snapshot is None:
            return SearchResponse(repository=request.repository, method=request.method)

        items = []
        for hit in result.results:
            issue = db.get_issue(snapshot.snapshot_id, hit.number)
            items.append(
                SearchResultItem(
                    number=hit.number,
                    title=hit.title,
                    html_url=hit.url,
                    score=hit.score,
                    score_type=request.method.value,
                    state=issue.state if issue else None,
                )
            )

        # CLI로 가져온 스냅샷의 범위 형식은 검색 API의 수집 범위와 다를 수 있다.
        scope = None
        fields = CollectionScope.model_fields.keys()
        if fields <= snapshot.collection_scope.keys():
            scope = CollectionScope(**{field: snapshot.collection_scope[field] for field in fields})

        return SearchResponse(
            repository=request.repository,
            method=request.method,
            results=items,
            snapshot_id=snapshot.snapshot_id,
            collected_at=snapshot.collected_at,
            partial_collection=snapshot.partial_collection,
            scope=scope,
        )
