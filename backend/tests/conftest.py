"""테스트 공용 도구.

실제 GitHub 대신 `httpx.MockTransport`로 응답을 주입한다. 네트워크 없이 수집·API를
검증한다.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx

from backend.app.core.config import Settings
from backend.app.integrations.github import GitHubClient

Handler = Callable[[httpx.Request], httpx.Response]


def make_settings(**overrides: object) -> Settings:
    """테스트용 설정. 페이지네이션을 쉽게 보려고 작은 값을 기본으로 둔다."""

    base: dict[str, object] = dict(
        github_token=None,
        github_api_base="https://api.github.com",
        github_api_version="2022-11-28",
        user_agent="issue-finder-test",
        request_timeout=5.0,
        per_page=2,
        max_issues=10,
        max_comments=10,
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model=None,
    )
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def make_client(handler: Handler, settings: Settings | None = None) -> GitHubClient:
    settings = settings or make_settings()
    return GitHubClient(settings, transport=httpx.MockTransport(handler))


def factory_for(handler: Handler, settings: Settings | None = None):
    """매 호출마다 MockTransport 클라이언트를 새로 만드는 팩토리."""

    settings = settings or make_settings()
    return lambda: GitHubClient(settings, transport=httpx.MockTransport(handler))


def issue(number: int, **overrides: object) -> dict:
    data: dict = {
        "number": number,
        "title": f"Issue {number}",
        "html_url": f"https://github.com/o/r/issues/{number}",
        "state": "open",
        "body": f"body {number}",
        "user": {"login": "alice"},
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "comments": 0,
        "labels": [{"name": "bug"}],
    }
    data.update(overrides)
    return data


def pull_request(number: int) -> dict:
    data = issue(number)
    data["pull_request"] = {"url": f"https://api.github.com/o/r/pulls/{number}"}
    return data


def comment(cid: int) -> dict:
    return {
        "id": cid,
        "html_url": f"https://github.com/o/r/issues/1#issuecomment-{cid}",
        "body": f"comment {cid}",
        "user": {"login": "bob"},
        "created_at": "2026-01-03T00:00:00Z",
    }
