# Integrations

기본 담당: GitHub 연동은 신은지 (`@eunji8319`), Ollama 연동은 김민수 (`@mins-oo`).

GitHub와 Ollama 클라이언트를 둔다. API 요청과 응답 처리는 이곳에 두고 수집 로직은 `collection/`, 요약 로직은 `summarization/`에서 관리한다. 토큰과 API Key는 서버 환경변수로 전달한다.

## GitHub

`github.py`의 `GitHubClient`가 GitHub REST API를 호출한다. `GITHUB_TOKEN`이 없어도 공개 저장소를 조회할 수 있으며, 토큰이 있으면 호출 제한이 완화된다. 저장소 없음·호출 제한·네트워크 오류는 `RepositoryNotFound`·`RateLimited`·`GitHubUnavailable`로 구분한다.

## Ollama

Ollama Cloud API(`https://ollama.com`)를 이용하여 LLM 모델을 호출한다.

현재 기본 모델은 `gpt-oss:20b`이며, `ollama.py`의 `OllamaClient`를 통해 프롬프트를 전달하고 생성된 응답을 반환한다.

### 환경 설정

프로젝트 루트에 `.env` 파일을 직접 생성하고 Ollama API Key를 입력한다. `.env` 파일이 없거나 `OLLAMA_API_KEY`가 비어 있으면 오류가 발생한다.

```dotenv
OLLAMA_API_KEY=YOUR_API_KEY
OLLAMA_MODEL=gpt-oss:20b
```

`.env` 파일은 개인별로 생성해야 하며 실제 API Key는 GitHub에 업로드하지 않는다.

### 사용 방법

```python
from backend.app.integrations.ollama import OllamaClient

ollama = OllamaClient()

try:
    response = ollama.chat("Hello World!")
    print(response)
finally:
    ollama.close()
```

`chat(prompt)`는 입력된 프롬프트에 대한 모델의 응답 텍스트를 반환한다.