"""라우터가 쓰는 의존성.

실제 구현(GitHub 클라이언트 팩토리, 검색·요약 백엔드, 작업 저장소)은 `app.state`에
둔다. 테스트나 팀원 모듈 합류 시 `app.state`만 교체하면 라우터는 그대로 둔다.
"""

from __future__ import annotations

import httpx
from fastapi import FastAPI, Request

from backend.app.api.backends import (
    SearchBackend,
    SummaryBackend,
    UnavailableSearchBackend,
    UnavailableSummaryBackend,
)
from backend.app.api.jobs import GitHubClientFactory, JobStore
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.github import GitHubClient


def default_client_factory(settings: Settings) -> GitHubClientFactory:
    """실제 GitHub에 붙는 클라이언트 팩토리."""

    def factory() -> GitHubClient:
        client = httpx.Client(
            base_url=settings.github_api_base,
            headers=settings.github_headers(),
            timeout=settings.request_timeout,
        )
        return GitHubClient(settings, client=client)

    return factory


def init_app_state(app: FastAPI, settings: Settings | None = None) -> None:
    """기본 상태를 설정한다. 이미 설정된 값은 덮어쓰지 않아 테스트 주입을 보존한다."""

    settings = settings or get_settings()
    state = app.state
    if not hasattr(state, "settings"):
        state.settings = settings
    if not hasattr(state, "job_store"):
        state.job_store = JobStore()
    if not hasattr(state, "github_client_factory"):
        state.github_client_factory = default_client_factory(state.settings)
    if not hasattr(state, "search_backend"):
        state.search_backend = UnavailableSearchBackend()
    if not hasattr(state, "summary_backend"):
        state.summary_backend = UnavailableSummaryBackend()


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_job_store(request: Request) -> JobStore:
    return request.app.state.job_store


def get_client_factory(request: Request) -> GitHubClientFactory:
    return request.app.state.github_client_factory


def get_search_backend(request: Request) -> SearchBackend:
    return request.app.state.search_backend


def get_summary_backend(request: Request) -> SummaryBackend:
    return request.app.state.summary_backend
