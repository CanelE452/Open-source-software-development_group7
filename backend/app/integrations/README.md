# Integrations

기본 담당: GitHub 연동은 신은지 (`@eunji8319`), Ollama 연동은 김민수 (`@mins-oo`).

GitHub와 Ollama 클라이언트를 추가한다. API 요청과 응답 처리는 이곳에 두고 수집 로직은 `collection/`, 요약 로직은 `summarization/`에서 관리한다. 토큰은 서버 환경변수로 전달한다.

## Ollama

Ollama Cloud API를 이용하여 LLM 모델을 호출한다.

현재 기본 모델은 `gpt-oss:20b`이며, `ollama.py`의 `OllamaClient`를 통해 프롬프트를 전달하고 생성된 응답을 반환한다.

### 환경 설정

프로젝트 루트에 `.env` 파일을 직접 생성하고 Ollama API Key를 입력한다.

```dotenv
OLLAMA_API_KEY=YOUR_API_KEY
OLLAMA_MODEL=gpt-oss:20b
```

`.env` 파일은 개인별로 생성해야 하며 실제 API Key는 GitHub에 업로드하지 않는다.

### 사용 방법

```python
from app.integrations.ollama import OllamaClient

ollama = OllamaClient()

try:
    response = ollama.chat("Hello World!")
    print(response)
finally:
    ollama.close()
```

`chat(prompt)`는 입력된 프롬프트에 대한 모델의 응답 텍스트를 반환한다.
