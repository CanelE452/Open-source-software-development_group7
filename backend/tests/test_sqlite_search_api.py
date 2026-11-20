import sqlite3
from contextlib import closing

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.collection import issues as collection
from backend.app.core.config import get_settings
from backend.app.main import create_app
from backend.app.search.embeddings import SentenceTransformerEmbedder
from backend.app.storage import Issue, SQLiteRepository
from backend.tests.conftest import factory_for, issue, pull_request


GITHUB_ISSUE = issue(7, title="Database deadlock", state="closed", body=None)


@pytest.fixture
def search_app(tmp_path, monkeypatch):
    db_path = tmp_path / "issues.sqlite3"
    monkeypatch.setenv("ISSUE_FINDER_DB_PATH", str(db_path))
    monkeypatch.setenv("GITHUB_API_BASE", "https://api.github.com")
    monkeypatch.setenv("GITHUB_TOKEN", "")
    monkeypatch.setenv("GITHUB_PER_PAGE", "2")
    monkeypatch.setenv("COLLECTION_MAX_ISSUES", "10")
    get_settings.cache_clear()
    try:
        yield create_app(), db_path
    finally:
        get_settings.cache_clear()


def _mock_github(app, pages):
    def handle(request):
        assert request.method == "GET"
        assert request.url.path == "/repos/o/r/issues"
        page = pages.get(int(request.url.params["page"]), [])
        if isinstance(page, int):
            return httpx.Response(page, json={})
        return httpx.Response(200, json=page)

    app.state.github_client_factory = factory_for(handle, app.state.settings)


def _analyze(client):
    response = client.post(
        "/api/repositories/analyze", json={"repository": "https://github.com/o/r.git"}
    )
    assert response.status_code == 202
    job = client.get(f"/api/repositories/jobs/{response.json()['job_id']}")
    assert job.status_code == 200
    return job.json()


def _search(client, **overrides):
    payload = {"repository": "o/r", "problem": "deadlock", "method": "bm25"}
    payload.update(overrides)
    return client.post("/api/search", json=payload)


def test_collected_issues_are_searchable_after_app_reopens(search_app):
    app, db_path = search_app
    _mock_github(app, {1: [GITHUB_ISSUE, pull_request(8)]})
    with TestClient(app) as client:
        job = _analyze(client)

    assert job["state"] == "completed"
    assert job["progress"]["indexed"] is True
    snapshot = job["collection"]
    assert snapshot["scope"]["pull_requests_excluded"] == 1
    with SQLiteRepository(db_path) as db:
        assert [item.number for item in db.list_issues(snapshot["snapshot_id"])] == [7]

    with TestClient(create_app()) as client:
        response = _search(client, repository="https://github.com/o/r")

    assert response.status_code == 200
    body = response.json()
    assert body["repository"] == "o/r"
    for field in ("snapshot_id", "collected_at", "scope", "partial_collection"):
        assert body[field] == snapshot[field]
    hit, = body["results"]
    assert hit["number"] == 7
    assert hit["title"] == "Database deadlock"
    assert hit["html_url"] == "https://github.com/o/r/issues/7"
    assert hit["state"] == "closed"
    assert hit["score_type"] == "bm25"
    assert hit["score"] > 0


def test_no_snapshot_and_no_matches_have_distinct_metadata(search_app):
    app, _ = search_app
    _mock_github(app, {1: [GITHUB_ISSUE]})
    with TestClient(app) as client:
        before = _search(client, method="hybrid")
        job = _analyze(client)
        after = _search(client, problem="unmatchedtoken")

    assert before.status_code == after.status_code == 200
    assert before.json()["results"] == after.json()["results"] == []
    assert before.json()["snapshot_id"] is None
    assert after.json()["snapshot_id"] == job["collection"]["snapshot_id"]


def test_partial_collection_remains_searchable(search_app):
    app, _ = search_app
    _mock_github(app, {1: [GITHUB_ISSUE, pull_request(8)], 2: 503})
    with TestClient(app) as client:
        job = _analyze(client)
        response = _search(client)

    assert job["state"] == "partial"
    assert job["progress"]["indexed"] is True
    assert job["collection"]["notes"]
    assert response.status_code == 200
    assert response.json()["partial_collection"] is True
    assert response.json()["results"][0]["number"] == 7


def test_repeat_collection_in_same_second_keeps_both_snapshots(search_app, monkeypatch):
    app, db_path = search_app
    monkeypatch.setattr(collection, "utc_now_iso", lambda: "2026-10-29T00:00:00+00:00")
    _mock_github(app, {1: [GITHUB_ISSUE]})
    with TestClient(app) as client:
        first = _analyze(client)
        second = _analyze(client)
        response = _search(client)

    assert first["state"] == second["state"] == "completed"
    first_id = first["collection"]["snapshot_id"]
    second_id = second["collection"]["snapshot_id"]
    assert first_id != second_id
    assert response.json()["snapshot_id"] == second_id
    with SQLiteRepository(db_path) as db:
        assert db.get_snapshot(first_id).issue_count == 1


@pytest.mark.parametrize(
    ("overrides", "status"),
    [
        ({"repository": "owner/.."}, 400),
        ({"repository": "https://[broken"}, 400),
        ({"problem": "   "}, 422),
    ],
)
def test_input_validation_before_search(search_app, overrides, status):
    app, _ = search_app
    with TestClient(app, raise_server_exceptions=False) as client:
        response = _search(client, **overrides)

    assert response.status_code == status
    if status == 400:
        assert response.json()["error"]["code"] == "invalid_repository"


def test_save_failure_rolls_back_and_records_failed_job(search_app):
    app, db_path = search_app
    _mock_github(app, {1: [GITHUB_ISSUE]})
    with TestClient(app) as client:
        initial = _analyze(client)
        assert initial["progress"]["indexed"] is True
        with closing(sqlite3.connect(db_path)) as connection:
            connection.execute(
                """CREATE TRIGGER fail_issue_insert BEFORE INSERT ON issues
                BEGIN SELECT RAISE(ABORT, 'fixed SQLite error'); END"""
            )
        failed = _analyze(client)
        response = _search(client)

    assert failed["state"] == "failed"
    assert failed["error"]["code"] == "internal_error"
    assert failed["progress"]["indexed"] is False
    assert response.status_code == 200
    assert response.json()["snapshot_id"] == initial["collection"]["snapshot_id"]


def test_lookup_failure_returns_structured_500(search_app):
    app, db_path = search_app
    with SQLiteRepository(db_path) as db:
        db.save_snapshot("o/r", [Issue(7, "Database deadlock")])
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute("UPDATE snapshots SET collection_scope = 'not-json'")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = _search(client)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"


def test_cli_snapshot_with_other_scope_is_searchable(search_app):
    app, db_path = search_app
    with SQLiteRepository(db_path) as db:
        snapshot = db.save_snapshot(
            "o/r", [Issue(7, "Database deadlock")],
            collection_scope={"state": "all", "pages": 2, "comments": "included"},
        )
    with TestClient(app) as client:
        response = _search(client)

    assert response.status_code == 200
    assert response.json()["snapshot_id"] == snapshot.snapshot_id
    assert response.json()["scope"] is None
    assert response.json()["results"][0]["number"] == 7


@pytest.mark.parametrize(("method", "score"), [("semantic", 1.0), ("hybrid", 2 / 61)])
def test_model_search_uses_http_score_types(search_app, monkeypatch, method, score):
    app, _ = search_app
    _mock_github(app, {1: [GITHUB_ISSUE]})
    monkeypatch.setattr(
        SentenceTransformerEmbedder, "encode", lambda _, texts: [[1.0, 0.0] for _ in texts]
    )
    with TestClient(app) as client:
        _analyze(client)
        response = _search(client, method=method)

    assert response.status_code == 200
    hit, = response.json()["results"]
    assert hit["number"] == 7
    assert hit["score_type"] == method
    assert hit["score"] == pytest.approx(score)


def test_model_unavailable_returns_503_without_fallback(search_app, monkeypatch):
    app, _ = search_app
    _mock_github(app, {1: [GITHUB_ISSUE]})

    def unavailable(_, texts):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(SentenceTransformerEmbedder, "encode", unavailable)
    with TestClient(app) as client:
        job = _analyze(client)
        response = client.post("/api/search", json={"repository": "o/r", "problem": "deadlock"})

    assert job["progress"]["indexed"] is True
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "search_unavailable"
