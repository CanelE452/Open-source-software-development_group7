from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
from threading import RLock
from typing import Iterable
from uuid import uuid4

from backend.app.storage.models import Comment, Issue, Snapshot


def normalize_repository(repository: str) -> str:
    if not isinstance(repository, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+", repository
    ):
        raise ValueError("repository must have the form owner/name")
    if repository.split("/", 1)[1] in {".", ".."}:
        raise ValueError("repository must have the form owner/name")
    return repository.lower()


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _collection_time(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if not isinstance(value, str):
        raise ValueError("collected_at must be a timezone-aware ISO timestamp")
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("collected_at must be a timezone-aware ISO timestamp") from exc
    if timestamp.tzinfo is None:
        raise ValueError("collected_at must include a timezone")
    return timestamp.astimezone(timezone.utc).isoformat()


def _vector(value: Iterable[float]) -> list[float]:
    values = list(value)
    if not values or any(
        isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item)
        for item in values
    ):
        raise ValueError("embedding must be a nonempty vector of finite numbers")
    return [float(item) for item in values]


class SQLiteRepository:
    """Immutable collection snapshots and content-addressed embedding cache."""

    def __init__(self, db_path: str | Path):
        self._lock = RLock()
        if str(db_path) != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(db_path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        version = self._connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in {0, 1}:
            self._connection.close()
            raise ValueError(f"unsupported SQLite schema version: {version}")
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    repository TEXT NOT NULL,
                    collected_at TEXT NOT NULL,
                    collection_scope TEXT NOT NULL,
                    partial_collection INTEGER NOT NULL CHECK (partial_collection IN (0, 1)),
                    content_hash TEXT NOT NULL,
                    issue_count INTEGER NOT NULL CHECK (issue_count >= 0)
                );
                CREATE INDEX IF NOT EXISTS snapshots_repository_time
                    ON snapshots (repository, collected_at DESC);
                CREATE TABLE IF NOT EXISTS issues (
                    snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id),
                    number INTEGER NOT NULL CHECK (number > 0),
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    url TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('open', 'closed')),
                    updated_at TEXT,
                    PRIMARY KEY (snapshot_id, number)
                );
                CREATE TABLE IF NOT EXISTS comments (
                    snapshot_id TEXT NOT NULL,
                    issue_number INTEGER NOT NULL,
                    id INTEGER NOT NULL CHECK (id > 0),
                    position INTEGER NOT NULL,
                    body TEXT NOT NULL,
                    url TEXT NOT NULL,
                    author TEXT,
                    created_at TEXT,
                    PRIMARY KEY (snapshot_id, issue_number, id),
                    FOREIGN KEY (snapshot_id, issue_number)
                        REFERENCES issues(snapshot_id, number)
                );
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    model_id TEXT NOT NULL,
                    model_revision TEXT NOT NULL,
                    text_hash TEXT NOT NULL,
                    vector TEXT NOT NULL,
                    PRIMARY KEY (model_id, model_revision, text_hash)
                );
                PRAGMA user_version = 1;
                """
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def save_snapshot(
        self,
        repository: str,
        issues: Iterable[Issue],
        *,
        collected_at: str | None = None,
        collection_scope: dict | None = None,
        partial_collection: bool = False,
        snapshot_id: str | None = None,
    ) -> Snapshot:
        repository = normalize_repository(repository)
        collected_at = _collection_time(collected_at)
        if collection_scope is None:
            collection_scope = {}
        if not isinstance(collection_scope, dict):
            raise ValueError("collection_scope must be a JSON object")
        scope_json = _json(collection_scope)
        if not isinstance(partial_collection, bool):
            raise ValueError("partial_collection must be a boolean")
        if snapshot_id is None:
            snapshot_id = str(uuid4())
        if not isinstance(snapshot_id, str) or not snapshot_id.strip():
            raise ValueError("snapshot_id must be nonempty text")
        items = list(issues)
        if any(not isinstance(issue, Issue) for issue in items):
            raise ValueError("issues must contain Issue objects")
        items.sort(key=lambda issue: issue.number)
        if len({issue.number for issue in items}) != len(items):
            raise ValueError("duplicate issue number in snapshot")
        canonical_issues = []
        for issue in items:
            item = asdict(issue)
            item["comments"] = sorted(item["comments"], key=lambda comment: comment["id"])
            canonical_issues.append(item)
        content_hash = hashlib.sha256(
            _json(
                {
                    "repository": repository,
                    "collection_scope": json.loads(scope_json),
                    "partial_collection": partial_collection,
                    "issues": canonical_issues,
                }
            ).encode("utf-8")
        ).hexdigest()
        snapshot = Snapshot(
            snapshot_id,
            repository,
            collected_at,
            json.loads(scope_json),
            partial_collection,
            content_hash,
            len(items),
        )
        with self._lock, self._connection:
            if self._connection.execute(
                "SELECT 1 FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchone():
                raise ValueError(f"snapshot already exists: {snapshot_id}")
            self._connection.execute(
                "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
                (snapshot_id, repository, collected_at, scope_json, int(partial_collection), content_hash, len(items)),
            )
            self._connection.executemany(
                "INSERT INTO issues VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(snapshot_id, issue.number, issue.title, issue.body, issue.url, issue.state, issue.updated_at) for issue in items],
            )
            self._connection.executemany(
                "INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (snapshot_id, issue.number, comment.id, position, comment.body, comment.url, comment.author, comment.created_at)
                    for issue in items
                    for position, comment in enumerate(issue.comments)
                ],
            )
        return snapshot

    @staticmethod
    def _snapshot(row: sqlite3.Row) -> Snapshot:
        return Snapshot(
            row["snapshot_id"], row["repository"], row["collected_at"],
            json.loads(row["collection_scope"]), bool(row["partial_collection"]),
            row["content_hash"], row["issue_count"],
        )

    def get_snapshot(self, snapshot_id: str) -> Snapshot:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchone()
            if row is None:
                raise KeyError(snapshot_id)
            return self._snapshot(row)

    def latest_snapshot(self, repository: str) -> Snapshot | None:
        repository = normalize_repository(repository)
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM snapshots WHERE repository = ? ORDER BY collected_at DESC, rowid DESC LIMIT 1",
                (repository,),
            ).fetchone()
            return self._snapshot(row) if row is not None else None

    def _issue(self, row: sqlite3.Row) -> Issue:
        comment_rows = self._connection.execute(
            "SELECT * FROM comments WHERE snapshot_id = ? AND issue_number = ? ORDER BY position",
            (row["snapshot_id"], row["number"]),
        ).fetchall()
        comments = tuple(
            Comment(item["id"], item["body"], item["url"], item["author"], item["created_at"])
            for item in comment_rows
        )
        return Issue(
            row["number"], row["title"], row["body"], row["url"], row["state"], comments, row["updated_at"]
        )

    def list_issues(self, snapshot_id: str) -> list[Issue]:
        with self._lock:
            self.get_snapshot(snapshot_id)
            rows = self._connection.execute(
                "SELECT * FROM issues WHERE snapshot_id = ? ORDER BY number", (snapshot_id,)
            ).fetchall()
            return [self._issue(row) for row in rows]

    def get_issue(self, snapshot_id: str, number: int) -> Issue | None:
        with self._lock:
            self.get_snapshot(snapshot_id)
            row = self._connection.execute(
                "SELECT * FROM issues WHERE snapshot_id = ? AND number = ?", (snapshot_id, number)
            ).fetchone()
            return self._issue(row) if row is not None else None

    def get_embedding(self, model_id: str, model_revision: str, text_hash: str) -> list[float] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT vector FROM embedding_cache WHERE model_id = ? AND model_revision = ? AND text_hash = ?",
                (model_id, model_revision, text_hash),
            ).fetchone()
            return _vector(json.loads(row["vector"])) if row is not None else None

    def put_embedding(self, model_id: str, model_revision: str, text_hash: str, vector: Iterable[float]) -> None:
        for name, value in (("model_id", model_id), ("model_revision", model_revision), ("text_hash", text_hash)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonempty text")
        vector_json = _json(_vector(vector))
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO embedding_cache VALUES (?, ?, ?, ?)
                ON CONFLICT (model_id, model_revision, text_hash) DO UPDATE SET vector = excluded.vector""",
                (model_id, model_revision, text_hash, vector_json),
            )
