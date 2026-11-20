"""저장소 식별자 검증·정규화.

`owner/repo` 또는 GitHub URL을 받아 `(owner, repo)`로 바꾼다. 형식이 맞지 않으면
`InvalidRepository`를 던진다.
"""

from __future__ import annotations

from urllib.parse import urlparse

from backend.app.storage import normalize_repository


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
        try:
            parsed = urlparse(text if "://" in text else f"https://{text}")
        except ValueError as exc:
            raise InvalidRepository("GitHub 저장소 주소 형식이 올바르지 않습니다.") from exc
        if parsed.scheme not in ("http", "https") or parsed.netloc.lower() not in (
            "github.com", "www.github.com",
        ):
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

    try:
        normalize_repository(f"{owner}/{repo}")
    except ValueError as exc:
        raise InvalidRepository("owner/repo에 허용되지 않는 문자가 있습니다.") from exc

    return owner, repo


def repository_slug(owner: str, repo: str) -> str:
    """`owner/repo` 문자열로 되돌린다."""

    return f"{owner}/{repo}"
