# Integrations

기본 담당: GitHub 연동은 신은지 (`@eunji8319`), Ollama 연동은 김민수 (`@mins-oo`).

GitHub와 Ollama 클라이언트를 추가한다. API 요청과 응답 처리는 이곳에 두고 수집 로직은 `collection/`, 요약 로직은 `summarization/`에서 관리한다. 토큰은 서버 환경변수로 전달한다.

## Ollama

루트에 아래와 같은 형식의 `.env` 파일을 생성해 OLLAMA_API_KEY를 입력한다.

```
# GitHub API token (server only)
GITHUB_TOKEN=
# Ollama server and model
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_API_KEY=\
```

기본 모델은 gpt-oss:20b로 ollama에서 제공하는 무료 클라우드 모델을 사용한다.
라이선스 추후 추가 필요 [model license link](https://huggingface.co/openai/gpt-oss-20b/blob/main/LICENSE)