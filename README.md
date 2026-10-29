# Issue Finder · 7조

공개 GitHub 저장소에서 문제 상황과 관련된 Issue를 검색하고, 선택한 Issue의 본문·댓글을 근거와 함께 요약하는 팀 프로젝트입니다.

현재 상태 확인 API와 기본 화면, SQLite 저장·검색 CLI를 구성했습니다. 실행 방법은 [저장·검색 안내](docs/sqlite-search.md)를 참고해주세요. GitHub 수집·검색 API·요약·화면 연동은 개발 예정입니다.

## 저장소 구조

```text
backend/
  app/
    api/routes/       HTTP endpoint
    schemas/          요청·응답 형식
    collection/       GitHub Issue·댓글 수집
    storage/          SQLite·스냅샷
    search/           BM25·Semantic·Hybrid
    summarization/    구조화 요약·근거 검증
    integrations/     GitHub·Ollama 외부 연동
    core/             서버 공통 설정
  tests/              백엔드 테스트
frontend/
  src/
    api/              API 호출
    types/            서버와 공유하는 타입
    components/       공통 UI
    features/         검색·Issue 상세 화면
evaluation/           질의·판정 자료, 검색·요약 평가
data/                 로컬 DB·원문·임베딩·모델 (Git 제외)
docs/                 구조·API 계약·작업 계획·회의
.github/              CI·Issue/PR 템플릿·리뷰 담당
```

폴더별 역할은 [구조 문서](docs/architecture.md), API 형식은 [API 문서](docs/api-contract.md)에 정리했습니다. 협업 방법은 [CONTRIBUTING.md](CONTRIBUTING.md), 개발 순서는 [roadmap](docs/roadmap.md)을 참고해주세요.

## 개발 환경

- Python 3.12, Node.js 20.19+ 또는 22.12+.
- FastAPI, React 19, TypeScript 5.7, Vite 6.
- 현재는 GitHub 토큰·Ollama·검색 모델 없이 실행할 수 있습니다.

### Windows PowerShell

프로젝트 루트에서 실행합니다. 먼저 Python 버전을 확인하세요.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
npm.cmd --prefix frontend ci
```

Python 실행기가 있다면 `py -3.12 -m venv .venv`로 3.12를 선택할 수 있습니다. 이미 `.venv`가 있으면 다시 만들 필요가 없습니다.

터미널 두 개를 열어 각각 실행합니다.

```powershell
# 터미널 1: 백엔드
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
# 터미널 2: 프런트엔드
npm.cmd --prefix frontend run dev
```

### Ubuntu / macOS

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm --prefix frontend ci
# 터미널 1
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
# 터미널 2
npm --prefix frontend run dev
```

- 프런트: http://127.0.0.1:5173
- API 문서: http://127.0.0.1:8000/docs
- 상태 확인: http://127.0.0.1:8000/api/health

개발 중 `/api` 요청은 Vite 프록시를 통해 백엔드로 전달됩니다. 백엔드와 프런트엔드는 각각 실행합니다.

## 검증

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
```

Ubuntu/macOS에서는 Python 경로를 `.venv/bin/python`, `npm.cmd`를 `npm`으로 바꿉니다. PR과 `main` push에서는 GitHub Actions로 테스트와 빌드를 실행합니다.

## 비밀 정보와 실행 데이터

서버 연동에 사용할 환경변수는 `.env.example`에 정리했습니다. `.env` 로딩은 수집·요약 기능 개발 시 연결할 예정입니다. 토큰은 서버에서만 사용합니다. `.env`, 가상환경, DB, 모델, 수집 데이터, 평가 결과는 Git에서 제외합니다.

## 라이선스

[MIT](LICENSE) 라이선스를 사용합니다. 사용 라이브러리는 [NOTICE](NOTICE)에 정리했습니다.
