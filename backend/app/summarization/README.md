# Summarization

기본 담당: 김민수 (`@mins-oo`).

Issue 본문과 댓글을 분석하고 요약하는 코드를 추가한다. 프롬프트, 요약 항목, 원문 근거 연결을 담당한다. Ollama 통신은 `integrations/`에 둔다.

## 처리 과정

1. GitHub Issue URL 입력
2. URL에서 owner, repo, issue number 추출
3. GitHub API를 통해 Issue 본문과 댓글 수집
4. Pydantic 모델에서 JSON Schema 생성
5. Issue 데이터와 JSON Schema를 프롬프트에 포함
6. Ollama LLM을 이용한 요약 생성
7. JSON 파싱 및 Pydantic 스키마 검증

## 요약 항목

| 필드 | 설명 |
|---|---|
| problem | Issue에서 보고한 문제와 증상 |
| conditions | 문제 발생 환경 및 조건 |
| solution | 제안되거나 확인된 해결 방법 |
| discussion | 댓글에서 논의한 내용과 결론 |
| follow_up | 후속 작업 및 추가 확인 사항 |
| unknowns | 원문만으로 확인할 수 없는 정보 |

각 항목은 `text`와 `evidence`로 구성된다.

`evidence`에는 다음 정보가 포함된다.

- `url`: 근거가 되는 Issue 또는 댓글 URL
- `excerpt`: 원문에서 발췌한 문장
- `source_type`: `issue_body` 또는 `comment`
- `comment_id`: 댓글 근거의 댓글 ID

## 요약 상태

- `completed`: 요약 생성 완료
- `insufficient_evidence`: 요약에 필요한 정보나 근거 부족
- `failed`: 요약 처리 실패

## 연결 상태

현재는 Issue URL을 입력하는 스크립트로 실행하며, HTTP API의 `SummaryBackend`에는 아직 연결하지 않았다. 요약 생성에는 `OLLAMA_API_KEY`가 필요하다. 스크립트는 GitHub 토큰 없이 Issue를 조회하므로 호출 제한에 걸릴 수 있다.

## 실행 방법

프로젝트 루트에서 다음 명령어를 실행한다.

```powershell
python .\backend\app\summarization\summarize.py
```

실행 후 GitHub Issue URL을 입력한다.

```text
https://github.com/owner/repo/issues/123
```

## 주요 파일

| 파일 | 역할 |
|---|---|
| `summarize.py` | GitHub Issue 수집 및 요약 생성 |
| `schemas/summarization_schema.py` | 요약 결과 및 근거 데이터 구조 정의 |
| `integrations/ollama.py` | Ollama Cloud API 호출 |

근거 검증과 검증 보고서 생성은 `backend/tests/test_summary_validation.py`에서 별도로 수행한다.
