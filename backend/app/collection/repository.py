"""저장소 식별자 검증·정규화.

`owner/repo` 또는 GitHub URL을 받아 `(owner, repo)`로 바꾼다. 형식이 맞지 않으면
`InvalidRepository`를 던진다.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

# GitHub 사용자/저장소 이름 규칙에 맞춘 느슨한 검증.
_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


class InvalidRepository(ValueError):
    """저장소 식별자 형식이 잘못되었을 때."""


def parse_repository(value: str) -> tuple[str, str]:
    """입력을 `(owner, repo)`로 정규화한다.

    허용 형식:
    - `owner/repo`
    - `https://github.com/owner/repo`(뒤에 `.git`이나 추가 경로가 있어도 됨)
    """

    if value is None:
        raise InvalidRepository("저장소를 입력하세요.")

    text = value.strip()
    if not text:
        raise InvalidRepository("저장소를 입력하세요.")

    owner: str
    repo: str

    if "://" in text or text.lower().startswith("github.com/"):
        parsed = urlparse(text if "://" in text else f"https://{text}")
        host = (parsed.netloc or "").lower()
        if host and host not in ("github.com", "www.github.com"):
            raise InvalidRepository("github.com 공개 저장소 주소만 지원합니다.")
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            raise InvalidRepository("주소에서 owner/repo를 찾지 못했습니다.")
        owner, repo = parts[0], parts[1]
    else:
        parts = [p for p in text.split("/") if p]
        if len(parts) != 2:
            raise InvalidRepository("`owner/repo` 형식으로 입력하세요.")
        owner, repo = parts[0], parts[1]

    if repo.endswith(".git"):
        repo = repo[: -len(".git")]

    if not _NAME.match(owner) or not _NAME.match(repo):
        raise InvalidRepository("owner/repo에 허용되지 않는 문자가 있습니다.")

    return owner, repo


def repository_slug(owner: str, repo: str) -> str:
    """`owner/repo` 문자열로 되돌린다."""

    return f"{owner}/{repo}"
