"""도메인 예외를 HTTP 상태·오류 응답으로 변환한다.

라우터와 작업 실행기가 같은 매핑을 쓰도록 한 곳에 모은다.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.api.backends import BackendUnavailable
from backend.app.collection.repository import InvalidRepository
from backend.app.integrations.github import (
    GitHubError,
    GitHubUnavailable,
    RateLimited,
    RepositoryNotFound,
)
from backend.app.schemas.errors import ErrorDetail, ErrorResponse


def status_for(exc: Exception) -> int:
    if isinstance(exc, InvalidRepository):
        return 400
    if isinstance(exc, RepositoryNotFound):
        return 404
    if isinstance(exc, RateLimited):
        return 429
    if isinstance(exc, GitHubUnavailable):
        return 502
    if isinstance(exc, BackendUnavailable):
        return 503
    if isinstance(exc, GitHubError):
        return 502
    return 500


def error_detail_for(exc: Exception) -> ErrorDetail:
    """예외를 오류 코드·메시지로 변환한다."""

    if isinstance(exc, InvalidRepository):
        return ErrorDetail(code="invalid_repository", message=str(exc))
    if isinstance(exc, RepositoryNotFound):
        return ErrorDetail(code="not_found", message=str(exc))
    if isinstance(exc, RateLimited):
        detail = {"retry_after": exc.retry_after} if exc.retry_after else None
        return ErrorDetail(code="rate_limited", message=str(exc), detail=detail)
    if isinstance(exc, GitHubUnavailable):
        return ErrorDetail(code="upstream_unavailable", message=str(exc))
    if isinstance(exc, BackendUnavailable):
        return ErrorDetail(
            code=f"{exc.backend}_unavailable",
            message=exc.message,
        )
    if isinstance(exc, GitHubError):
        return ErrorDetail(code="github_error", message=str(exc))
    return ErrorDetail(code="internal_error", message="서버 내부 오류가 발생했습니다.")


def _handler(exc: Exception) -> JSONResponse:
    detail = error_detail_for(exc)
    status = status_for(exc)
    body = ErrorResponse(error=detail).model_dump()
    headers = {}
    if isinstance(exc, RateLimited) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(status_code=status, content=body, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    """도메인 예외가 일관된 JSON 오류로 나가도록 핸들러를 등록한다."""

    domain_errors = (
        InvalidRepository,
        GitHubError,  # RepositoryNotFound/RateLimited/GitHubUnavailable 포함
        BackendUnavailable,
    )

    for exc_type in domain_errors:

        async def handle(_: Request, exc: Exception) -> JSONResponse:
            return _handler(exc)

        app.add_exception_handler(exc_type, handle)
