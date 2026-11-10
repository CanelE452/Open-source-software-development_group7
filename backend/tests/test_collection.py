import httpx
import pytest

from backend.app.collection.issue_detail import collect_issue_detail
from backend.app.collection.issues import collect_issues
from backend.app.integrations.github import (
    GitHubUnavailable,
    RateLimited,
    RepositoryNotFound,
)
from backend.tests.conftest import (
    comment,
    issue,
    make_client,
    make_settings,
    pull_request,
)


def _issue_pages(pages: dict[int, list[dict]]):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/o/r/issues"
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(200, json=pages.get(page, []))

    return handler


def test_collect_issues_excludes_prs_and_paginates():
    # per_page=2: 1페이지는 Issue+PR, 2페이지는 Issue 하나(마지막).
    handler = _issue_pages({1: [issue(1), pull_request(2)], 2: [issue(3)]})
    settings = make_settings(per_page=2, max_issues=10)

    result = collect_issues(make_client(handler, settings), "o", "r", settings=settings)

    assert [i.number for i in result.issues] == [1, 3]
    assert result.metadata.scope.pull_requests_excluded == 1
    assert result.metadata.scope.issue_count == 2
    assert result.metadata.partial_collection is False
    assert result.metadata.snapshot_id
    assert result.metadata.repository == "o/r"


def test_collect_issues_marks_partial_when_capped():
    handler = _issue_pages({1: [issue(1), issue(2), issue(3)]})
    settings = make_settings(per_page=10, max_issues=2)

    result = collect_issues(make_client(handler, settings), "o", "r", settings=settings)

    assert [i.number for i in result.issues] == [1, 2]
    assert result.metadata.partial_collection is True
    assert any("상한" in note for note in result.metadata.notes)


def test_collect_issues_keeps_partial_on_rate_limit():
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        if page == 1:
            return httpx.Response(200, json=[issue(1), issue(2)])
        return httpx.Response(403, headers={"X-RateLimit-Remaining": "0"}, json={})

    settings = make_settings(per_page=2, max_issues=10)
    result = collect_issues(make_client(handler, settings), "o", "r", settings=settings)

    assert [i.number for i in result.issues] == [1, 2]
    assert result.metadata.partial_collection is True


def test_collect_issues_keeps_partial_on_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        if page == 1:
            return httpx.Response(200, json=[issue(1), issue(2)])
        raise httpx.ConnectError("boom", request=request)

    settings = make_settings(per_page=2, max_issues=10)
    result = collect_issues(make_client(handler, settings), "o", "r", settings=settings)

    assert [i.number for i in result.issues] == [1, 2]
    assert result.metadata.partial_collection is True


def test_collect_issues_raises_on_missing_repository():
    handler = _issue_pages({})

    def not_found(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    with pytest.raises(RepositoryNotFound):
        collect_issues(make_client(not_found), "o", "r")


def test_collect_issues_raises_rate_limit_with_no_data():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "30"}, json={})

    with pytest.raises(RateLimited) as excinfo:
        collect_issues(make_client(handler), "o", "r")
    assert excinfo.value.retry_after == 30


def _detail_handler(issue_json: dict, comment_pages: dict[int, list[dict]]):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/o/r/issues/1":
            return httpx.Response(200, json=issue_json)
        if path == "/repos/o/r/issues/1/comments":
            page = int(request.url.params.get("page", "1"))
            return httpx.Response(200, json=comment_pages.get(page, []))
        return httpx.Response(404, json={})

    return handler


def test_collect_issue_detail_gathers_body_and_comments():
    settings = make_settings(per_page=2, max_comments=10)
    handler = _detail_handler(
        issue(1, comments=3),
        {1: [comment(10), comment(11)], 2: [comment(12)]},
    )

    detail = collect_issue_detail(make_client(handler, settings), "o", "r", 1, settings=settings)

    assert detail.number == 1
    assert detail.comment_count == 3
    assert [c.id for c in detail.comments] == [10, 11, 12]
    assert detail.partial_collection is False


def test_collect_issue_detail_marks_partial_when_comments_missing():
    settings = make_settings(per_page=2, max_comments=10)
    # Issue는 댓글 5개라고 하지만 2개만 반환된다.
    handler = _detail_handler(issue(1, comments=5), {1: [comment(10), comment(11)]})

    detail = collect_issue_detail(make_client(handler, settings), "o", "r", 1, settings=settings)

    assert detail.comment_count == 2
    assert detail.partial_collection is True


def test_collect_issue_detail_rejects_pull_request():
    settings = make_settings()
    pr_json = issue(1)
    pr_json["pull_request"] = {"url": "https://api.github.com/o/r/pulls/1"}
    handler = _detail_handler(pr_json, {})

    with pytest.raises(RepositoryNotFound):
        collect_issue_detail(make_client(handler, settings), "o", "r", 1, settings=settings)
