# Core

공동 담당: 백엔드 담당자.

환경변수와 로깅 등 백엔드 공통 설정을 둔다. `config.py`의 `get_settings()`가 저장소 루트의 `.env`와 환경변수를 읽는다. 이미 설정된 환경변수는 `.env`보다 우선한다.

| 환경변수 | 기본값 | 설명 |
|---|---|---|
| `GITHUB_TOKEN` | 없음 | GitHub API 토큰. 없어도 공개 저장소를 수집할 수 있다 |
| `GITHUB_API_BASE` | `https://api.github.com` | GitHub API 주소 |
| `GITHUB_API_VERSION` | `2022-11-28` | GitHub API 버전 헤더 |
| `GITHUB_USER_AGENT` | `issue-finder` | 요청 User-Agent |
| `GITHUB_TIMEOUT` | `30` | 요청 제한 시간(초) |
| `GITHUB_PER_PAGE` | `100` | 페이지당 수집 개수(최대 100) |
| `COLLECTION_MAX_ISSUES` | `300` | Issue 수집 상한 |
| `COLLECTION_MAX_COMMENTS` | `300` | Issue당 댓글 수집 상한 |

Ollama 연동(`OLLAMA_API_KEY`, `OLLAMA_MODEL`)은 [`integrations/`](../integrations/README.md)에서 읽는다.