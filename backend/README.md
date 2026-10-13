# Backend

Python 3.12 이상을 사용한다. FastAPI 앱의 시작점은 `backend.app.main:app`이며 모든 명령은 **저장소 루트**에서 실행한다.

현재 동작하는 API는 `GET /api/health`뿐이다. 이 응답은 API 프로세스 상태를 나타내며 GitHub·DB·모델의 연결 상태는 확인하지 않는다. 검색·수집·저장·요약은 팀원별로 다음 모듈에 구현한다.

```text
backend/
├── app/
│   ├── main.py           # 앱 생성과 라우터 연결
│   ├── api/routes/       # HTTP 엔드포인트
│   ├── schemas/          # 요청·응답 및 공유 데이터 형식
│   ├── collection/       # Issue·댓글 수집
│   ├── storage/          # SQLite·스냅샷
│   ├── search/           # BM25·Semantic·Hybrid 검색
│   ├── summarization/    # 요약·근거 검증
│   ├── integrations/     # GitHub·Ollama 클라이언트
│   └── core/             # 공통 실행 설정
├── tests/                # 백엔드 검증
├── requirements.txt      # 최소 API 실행 의존성
└── requirements-dev.txt  # 실행 의존성 + 테스트 도구
```

담당자와 경계는 각 모듈의 README와 [`docs/architecture.md`](../docs/architecture.md)를 확인한다. 기능 개발 전 [`docs/api-contract.md`](../docs/api-contract.md), [`CONTRIBUTING.md`](../CONTRIBUTING.md)를 읽는다.

## Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

이미 `.venv`가 있으면 생성 명령을 생략한다. 가상환경 Python을 직접 실행하므로 PowerShell 활성화 스크립트는 필요하지 않다.

서버가 켜진 동안 다른 터미널에서 확인한다.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
.\.venv\Scripts\python.exe -m pytest backend/tests
```

## Ubuntu

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

이미 `.venv`가 있으면 생성 명령을 생략한다. 서버가 켜진 동안 다른 터미널에서 확인한다.

```bash
curl http://127.0.0.1:8000/api/health
.venv/bin/python -m pytest backend/tests
```

상태 응답은 `{"status":"ok","service":"issue-finder"}`이며 API 문서는 <http://127.0.0.1:8000/docs>에서 확인한다. 서버는 `Ctrl+C`로 종료한다. 초기 상태 확인에는 GitHub 토큰과 Ollama 설치가 필요하지 않다.

## 의존성 기준

API 실행에는 FastAPI와 Uvicorn만 직접 선언한다. `requirements-dev.txt`는 테스트에 필요한 pytest와 HTTPX를 추가한다. 검색용 ML 패키지는 검색 방식과 모델이 결정된 뒤 별도로 관리한다.

패키지 버전은 `requirements.txt`와 `requirements-dev.txt`에서 관리한다.
