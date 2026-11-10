"""백엔드 공통 설정.

환경변수와 선택적 `.env` 파일에서 서버 설정을 읽는다. GitHub 토큰은 서버에서만
사용하며 응답으로 노출하지 않는다. 외부 의존성 없이 동작하도록 `.env` 로딩은
간단한 파서로 직접 처리한다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# backend/app/core/config.py -> parents[3] == 저장소 루트
REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = REPO_ROOT / ".env"


def load_env_file(path: Path = ENV_PATH) -> None:
    """`.env` 파일이 있으면 `KEY=VALUE` 형식을 읽어 환경변수로 넣는다.

    이미 설정된 환경변수는 덮어쓰지 않는다(`setdefault`). 파일이 없으면 조용히
    넘어가 토큰 없이도 서버를 실행할 수 있게 한다.
    """

    if not path.is_file():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        # 따옴표로 감싼 값은 벗겨낸다.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """서버 실행에 필요한 값. 토큰이 없어도 공개 저장소는 수집할 수 있다."""

    github_token: str | None
    github_api_base: str
    github_api_version: str
    user_agent: str
    request_timeout: float
    per_page: int
    max_issues: int
    max_comments: int
    ollama_base_url: str
    ollama_model: str | None

    def github_headers(self) -> dict[str, str]:
        """GitHub REST API 요청 공통 헤더. 토큰이 있으면 인증을 추가한다."""

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": self.user_agent,
            "X-GitHub-Api-Version": self.github_api_version,
        }
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        return headers


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """설정을 한 번 읽어 캐시한다. 테스트에서는 `get_settings.cache_clear()`로 초기화한다."""

    load_env_file()
    token = os.getenv("GITHUB_TOKEN") or None
    return Settings(
        github_token=token,
        github_api_base=os.getenv("GITHUB_API_BASE", "https://api.github.com"),
        github_api_version=os.getenv("GITHUB_API_VERSION", "2022-11-28"),
        user_agent=os.getenv("GITHUB_USER_AGENT", "issue-finder"),
        request_timeout=_float_env("GITHUB_TIMEOUT", 30.0),
        per_page=min(_int_env("GITHUB_PER_PAGE", 100), 100),
        max_issues=_int_env("COLLECTION_MAX_ISSUES", 300),
        max_comments=_int_env("COLLECTION_MAX_COMMENTS", 300),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL") or None,
    )
