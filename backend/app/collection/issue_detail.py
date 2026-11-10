"""선택한 Issue 하나의 본문·댓글·원문 링크 수집.

요약 담당에게 넘길 입력을 만든다. 댓글을 끝까지 받지 못하면 부분 수집으로 표시한다.
"""

from __future__ import annotations

from typing import Any

from backend.app.collection.issues import utc_now_iso
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.github import (
    GitHubClient,
    GitHubUnavailable,
    RateLimited,
    RepositoryNotFound,
)
from backend.app.schemas.collection import CollectedComment
from backend.app.schemas.issues import IssueDetailResponse


def _comment_from_raw(raw: dict[str, Any]) -> CollectedComment:
    user = raw.get("user") or {}
    return CollectedComment(
        id=raw.get("id"),
        html_url=raw.get("html_url"),
        body=raw.get("body"),
        author=user.get("login"),
        created_at=raw.get("created_at"),
    )


def collect_issue_detail(
    client: GitHubClient,
    owner: str,
    repo: str,
    number: int,
    *,
    settings: Settings | None = None,
) -> IssueDetailResponse:
    """Issue 본문과 댓글을 수집한다. PR 번호가 들어오면 404로 처리한다."""

    settings = settings or get_settings()
    slug = f"{owner}/{repo}"

    raw = client.get_issue(owner, repo, number)
    if "pull_request" in raw:
        # 이 서비스는 Issue만 다룬다. PR 번호는 없는 Issue로 취급한다.
        raise RepositoryNotFound(f"#{number}은(는) Issue가 아니라 Pull Request입니다.")

    user = raw.get("user") or {}
    expected_comments = raw.get("comments", 0) or 0

    comments: list[CollectedComment] = []
    partial = False
    notes: list[str] = []

    try:
        for item in client.iter_comments(
            owner,
            repo,
            number,
            per_page=settings.per_page,
            max_items=settings.max_comments,
        ):
            comments.append(_comment_from_raw(item))
    except (RateLimited, GitHubUnavailable) as exc:
        partial = True
        notes.append(f"댓글을 끝까지 받지 못했습니다: {exc}")

    if len(comments) >= settings.max_comments and expected_comments > len(comments):
        partial = True
        notes.append(
            f"댓글 수집 상한({settings.max_comments}개)에 도달했습니다."
        )
    elif expected_comments and len(comments) < expected_comments and not partial:
        partial = True
        notes.append(
            f"기대한 댓글 {expected_comments}개 중 {len(comments)}개만 수집했습니다."
        )

    return IssueDetailResponse(
        repository=slug,
        number=raw["number"],
        title=raw.get("title") or "",
        html_url=raw.get("html_url") or "",
        state=raw.get("state") or "open",
        body=raw.get("body"),
        author=user.get("login"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
        comments=comments,
        comment_count=len(comments),
        collected_at=utc_now_iso(),
        partial_collection=partial,
        notes=notes,
    )
