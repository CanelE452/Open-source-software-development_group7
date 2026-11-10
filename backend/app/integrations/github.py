"""GitHub REST API 클라이언트.

수집 로직(`collection/`)이 사용한다. 여기서는 HTTP 요청·페이지네이션·오류 변환만
담당하고, PR 제외나 수집 범위 판단 같은 정책은 `collection/`에 둔다. 토큰은 서버
환경변수(`core.config`)로만 전달한다.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx

from backend.app.core.config import Settings, get_settings


class GitHubError(Exception):
    """GitHub 연동에서 발생하는 오류의 기반 클래스."""


class RepositoryNotFound(GitHubError):
    """저장소나 Issue가 없을 때(HTTP 404)."""


class RateLimited(GitHubError):
    """호출 제한에 걸렸을 때(HTTP 403/429, 남은 호출 0)."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class GitHubUnavailable(GitHubError):
    """네트워크 실패나 5xx 등 일시적 오류."""


def _raise_for_status(response: httpx.Response) -> None:
    """GitHub 응답 상태를 도메인 예외로 바꾼다."""

    status = response.status_code
    if status == 404:
        raise RepositoryNotFound("요청한 저장소 또는 Issue를 찾을 수 없습니다.")
    if status in (403, 429):
        remaining = response.headers.get("X-RateLimit-Remaining")
        retry_after = response.headers.get("Retry-After")
        reset = response.headers.get("X-RateLimit-Reset")
        if status == 429 or remaining == "0":
            after = None
            if retry_after and retry_after.isdigit():
                after = int(retry_after)
            elif reset and reset.isdigit():
                after = int(reset)
            raise RateLimited(
                "GitHub API 호출 제한에 걸렸습니다. 잠시 후 다시 시도하세요.",
                retry_after=after,
            )
        # 권한 문제 등 그 외 403.
        raise GitHubError(f"GitHub 요청이 거부되었습니다(HTTP {status}).")
    if status >= 500:
        raise GitHubUnavailable(f"GitHub 서버 오류(HTTP {status}).")
    if status >= 400:
        raise GitHubError(f"GitHub 요청 실패(HTTP {status}).")


class GitHubClient:
    """얇은 httpx 래퍼. 테스트에서는 `transport`로 가짜 응답을 주입한다."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.Client | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            self._client = httpx.Client(
                base_url=self.settings.github_api_base,
                headers=self.settings.github_headers(),
                timeout=self.settings.request_timeout,
                transport=transport,
            )
            self._owns_client = True

    def _get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        try:
            response = self._client.get(path, params=params)
        except httpx.RequestError as exc:  # 네트워크·타임아웃 등
            raise GitHubUnavailable(
                f"GitHub에 연결하지 못했습니다: {exc}"
            ) from exc
        _raise_for_status(response)
        return response

    def iter_issues(
        self, owner: str, repo: str, *, per_page: int, max_items: int
    ) -> Iterator[dict[str, Any]]:
        """저장소 Issue를 페이지 단위로 순회한다. PR 제외는 호출 측에서 처리한다.

        `max_items`는 안전장치다. 받은 원본(raw) Issue 수가 상한에 닿으면 멈춘다.
        """

        page = 1
        seen = 0
        while seen < max_items:
            response = self._get(
                f"/repos/{owner}/{repo}/issues",
                params={
                    "state": "all",
                    "per_page": per_page,
                    "page": page,
                    "sort": "created",
                    "direction": "desc",
                },
            )
            batch = response.json()
            if not batch:
                break
            for item in batch:
                yield item
                seen += 1
                if seen >= max_items:
                    break
            if len(batch) < per_page:
                break
            page += 1

    def get_issue(self, owner: str, repo: str, number: int) -> dict[str, Any]:
        return self._get(f"/repos/{owner}/{repo}/issues/{number}").json()

    def iter_comments(
        self, owner: str, repo: str, number: int, *, per_page: int, max_items: int
    ) -> Iterator[dict[str, Any]]:
        page = 1
        seen = 0
        while seen < max_items:
            response = self._get(
                f"/repos/{owner}/{repo}/issues/{number}/comments",
                params={"per_page": per_page, "page": page},
            )
            batch = response.json()
            if not batch:
                break
            for item in batch:
                yield item
                seen += 1
                if seen >= max_items:
                    break
            if len(batch) < per_page:
                break
            page += 1

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "GitHubClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
