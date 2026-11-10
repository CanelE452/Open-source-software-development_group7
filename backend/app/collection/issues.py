"""저장소 Issue 목록 수집.

GitHub Issue 목록에는 Pull Request가 섞여 오므로 PR을 제외한다. 수집 범위와 시각,
부분 수집 여부를 메타데이터로 남긴다. 네트워크 실패나 호출 제한이 이미 받은 데이터를
버리지 않도록, 일부라도 받았으면 부분 수집으로 표시하고 멈춘다.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from math import ceil
from typing import Any

from backend.app.core.config import Settings, get_settings
from backend.app.integrations.github import (
    GitHubClient,
    GitHubUnavailable,
    RateLimited,
)
from backend.app.schemas.collection import (
    CollectedIssue,
    CollectionMetadata,
    CollectionScope,
)


@dataclass
class CollectionResult:
    issues: list[CollectedIssue]
    metadata: CollectionMetadata


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_snapshot_id(slug: str, collected_at: str, numbers: list[int]) -> str:
    """저장소·시각·Issue 번호로 재현 가능한 짧은 스냅샷 식별자를 만든다."""

    joined = ",".join(str(n) for n in numbers)
    digest = hashlib.sha256(f"{slug}|{collected_at}|{joined}".encode()).hexdigest()
    return digest[:16]


def _issue_from_raw(raw: dict[str, Any]) -> CollectedIssue:
    user = raw.get("user") or {}
    labels = [
        label.get("name", "")
        for label in raw.get("labels", [])
        if isinstance(label, dict)
    ]
    return CollectedIssue(
        number=raw["number"],
        title=raw.get("title") or "",
        html_url=raw.get("html_url") or "",
        state=raw.get("state") or "open",
        body=raw.get("body"),
        author=user.get("login"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
        comment_count=raw.get("comments", 0) or 0,
        labels=[name for name in labels if name],
    )


def collect_issues(
    client: GitHubClient,
    owner: str,
    repo: str,
    *,
    settings: Settings | None = None,
    max_issues: int | None = None,
) -> CollectionResult:
    """PR을 제외한 Issue를 수집하고 메타데이터와 함께 돌려준다."""

    settings = settings or get_settings()
    limit = max_issues or settings.max_issues
    per_page = settings.per_page
    slug = f"{owner}/{repo}"

    issues: list[CollectedIssue] = []
    raw_count = 0
    pr_excluded = 0
    partial = False
    notes: list[str] = []

    # PR이 섞여 오므로, Issue가 상한에 닿을 때까지 넉넉히 읽는다(안전 상한 포함).
    raw_cap = max(limit * 5, limit + per_page)

    try:
        for raw in client.iter_issues(
            owner, repo, per_page=per_page, max_items=raw_cap
        ):
            raw_count += 1
            if "pull_request" in raw:  # PR 제외
                pr_excluded += 1
                continue
            issues.append(_issue_from_raw(raw))
            if len(issues) >= limit:
                # 상한에 닿았다. 더 있을 수 있으므로 부분 수집으로 표시한다.
                partial = True
                notes.append(f"수집 상한({limit}개)에 도달하여 이후 Issue는 제외했습니다.")
                break
    except RateLimited as exc:
        if not issues:
            raise
        partial = True
        notes.append(f"호출 제한으로 수집을 중단했습니다: {exc}")
    except GitHubUnavailable as exc:
        if not issues:
            raise
        partial = True
        notes.append(f"네트워크 문제로 수집을 중단했습니다: {exc}")

    collected_at = utc_now_iso()
    numbers = [issue.number for issue in issues]
    scope = CollectionScope(
        state="all",
        per_page=per_page,
        max_issues=limit,
        pages_fetched=ceil(raw_count / per_page) if raw_count else 0,
        issue_count=len(issues),
        pull_requests_excluded=pr_excluded,
    )
    metadata = CollectionMetadata(
        repository=slug,
        collected_at=collected_at,
        snapshot_id=make_snapshot_id(slug, collected_at, numbers),
        scope=scope,
        partial_collection=partial,
        notes=notes,
    )
    return CollectionResult(issues=issues, metadata=metadata)
