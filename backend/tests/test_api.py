import httpx
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas.search import SearchResponse, SearchResultItem
from backend.app.schemas.summary import SummaryResponse, SummaryStatus
from backend.tests.conftest import comment, factory_for, issue, make_settings, pull_request


class FakeSearch:
    available = True

    def __init__(self) -> None:
        self.indexed: list[tuple[str, int]] = []

    def index(self, repository, issues, metadata) -> None:
        self.indexed.append((repository, len(issues)))

    def search(self, request) -> SearchResponse:
        return SearchResponse(
            repository=request.repository,
            method=request.method,
            results=[
                SearchResultItem(
                    number=1,
                    title="관련 Issue",
                    html_url="https://github.com/o/r/issues/1",
                    score=0.9,
                    score_type=request.method.value,
                    state="open",
                )
            ],
        )


class FakeSummary:
    available = True

    def summarize(self, detail) -> SummaryResponse:
        return SummaryResponse(
            repository=detail.repository,
            number=detail.number,
            html_url=detail.html_url,
            status=SummaryStatus.completed,
        )


def _issue_pages(pages):
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(200, json=pages.get(page, []))

    return handler


def _detail_handler(issue_json, comment_pages, *, issue_status=200):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/o/r/issues/1":
            return httpx.Response(issue_status, json=issue_json)
        if path == "/repos/o/r/issues/1/comments":
            page = int(request.url.params.get("page", "1"))
            return httpx.Response(200, json=comment_pages.get(page, []))
        return httpx.Response(404, json={})

    return handler


def _dummy_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(404, json={})


def build_app(handler, *, settings=None, search=None, summary=None):
    settings = settings or make_settings()
    app = create_app()
    app.state.settings = settings
    app.state.github_client_factory = factory_for(handler, settings)
    if search is not None:
        app.state.search_backend = search
    if summary is not None:
        app.state.summary_backend = summary
    return app


# --- analyze / job status ---------------------------------------------------


def test_analyze_then_job_status_completes():
    handler = _issue_pages({1: [issue(1), pull_request(2)], 2: [issue(3)]})
    app = build_app(handler, settings=make_settings(per_page=2, max_issues=10))

    with TestClient(app) as client:
        start = client.post("/api/repositories/analyze", json={"repository": "o/r"})
        assert start.status_code == 202
        job_id = start.json()["job_id"]

        status = client.get(f"/api/repositories/jobs/{job_id}")

    assert status.status_code == 200
    body = status.json()
    assert body["state"] == "completed"
    assert body["progress"]["collected_issues"] == 2
    assert body["progress"]["indexed"] is False
    assert body["collection"]["partial_collection"] is False
    assert body["collection"]["scope"]["pull_requests_excluded"] == 1


def test_analyze_indexes_when_search_available():
    handler = _issue_pages({1: [issue(1)]})
    search = FakeSearch()
    app = build_app(
        handler, settings=make_settings(per_page=2, max_issues=10), search=search
    )

    with TestClient(app) as client:
        start = client.post("/api/repositories/analyze", json={"repository": "o/r"})
        job_id = start.json()["job_id"]
        status = client.get(f"/api/repositories/jobs/{job_id}").json()

    assert status["state"] == "completed"
    assert status["progress"]["indexed"] is True
    assert search.indexed == [("o/r", 1)]


def test_analyze_rejects_invalid_repository():
    app = build_app(_dummy_handler)
    with TestClient(app) as client:
        response = client.post("/api/repositories/analyze", json={"repository": "bad"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_repository"


def test_job_not_found_returns_404():
    app = build_app(_dummy_handler)
    with TestClient(app) as client:
        response = client.get("/api/repositories/jobs/does-not-exist")
    assert response.status_code == 404


# --- issue detail -----------------------------------------------------------


def test_issue_detail_endpoint():
    handler = _detail_handler(issue(1, comments=1), {1: [comment(10)]})
    app = build_app(handler, settings=make_settings(per_page=2))
    with TestClient(app) as client:
        response = client.get("/api/repositories/o/r/issues/1")
    assert response.status_code == 200
    body = response.json()
    assert body["number"] == 1
    assert body["comment_count"] == 1
    assert body["comments"][0]["id"] == 10


def test_issue_detail_not_found():
    handler = _detail_handler({}, {}, issue_status=404)
    app = build_app(handler)
    with TestClient(app) as client:
        response = client.get("/api/repositories/o/r/issues/1")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


# --- summary ----------------------------------------------------------------


def test_summary_without_backend_returns_503():
    handler = _detail_handler(issue(1, comments=0), {})
    app = build_app(handler)
    with TestClient(app) as client:
        response = client.post("/api/repositories/o/r/issues/1/summary")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "summary_unavailable"


def test_summary_with_backend_returns_result():
    handler = _detail_handler(issue(1, comments=0), {})
    app = build_app(handler, summary=FakeSummary())
    with TestClient(app) as client:
        response = client.post("/api/repositories/o/r/issues/1/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["repository"] == "o/r"
    assert body["number"] == 1
    assert body["status"] == "completed"


# --- search -----------------------------------------------------------------


def test_search_missing_problem_is_422():
    app = build_app(_dummy_handler)
    with TestClient(app) as client:
        response = client.post("/api/search", json={"repository": "o/r"})
    assert response.status_code == 422


def test_search_bad_method_is_422():
    app = build_app(_dummy_handler)
    with TestClient(app) as client:
        response = client.post(
            "/api/search",
            json={"repository": "o/r", "problem": "x", "method": "weird"},
        )
    assert response.status_code == 422


def test_search_top_k_out_of_range_is_422():
    app = build_app(_dummy_handler)
    with TestClient(app) as client:
        low = client.post(
            "/api/search", json={"repository": "o/r", "problem": "x", "top_k": 0}
        )
        high = client.post(
            "/api/search", json={"repository": "o/r", "problem": "x", "top_k": 99}
        )
    assert low.status_code == 422
    assert high.status_code == 422


def test_search_invalid_repository_is_400():
    app = build_app(_dummy_handler)
    with TestClient(app) as client:
        response = client.post("/api/search", json={"repository": "bad", "problem": "x"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_repository"


def test_search_without_backend_returns_503():
    app = build_app(_dummy_handler)
    with TestClient(app) as client:
        response = client.post(
            "/api/search", json={"repository": "o/r", "problem": "로그인 실패"}
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "search_unavailable"


def test_search_with_backend_returns_results():
    app = build_app(_dummy_handler, search=FakeSearch())
    with TestClient(app) as client:
        response = client.post(
            "/api/search",
            json={"repository": "o/r", "problem": "로그인 실패", "method": "bm25"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["method"] == "bm25"
    assert len(body["results"]) == 1
    assert body["results"][0]["score_type"] == "bm25"
