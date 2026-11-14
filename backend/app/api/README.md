# API

기본 담당: 신은지 (`@eunji8319`).

HTTP 요청 검증, 응답, 오류 처리를 담당한다. 엔드포인트는 `routes/`에 나누고 `app/main.py`에서 라우터를 연결한다. 수집·검색·요약 처리는 해당 모듈에 둔다.

## 라우터

- `routes/health.py`: `GET /api/health`
- `routes/repositories.py`: 저장소 분석(`POST /api/repositories/analyze`), 작업 상태, Issue 상세, 요약
- `routes/search.py`: `POST /api/search`

## 모듈 연결

검색·요약은 `backends.py`의 `SearchBackend`·`SummaryBackend`에만 의존한다. 구현을 `app.state`에 주입하기 전에는 `Unavailable*Backend`가 503을 반환하며, 수집·Issue 상세 API는 독립적으로 동작한다. 분석 작업 상태는 `jobs.py`의 메모리 저장소에 두므로 서버를 다시 시작하면 사라진다. 도메인 예외는 `errors.py`에서 공통 오류 응답으로 바꾼다.

API를 변경할 때는 [`docs/api-contract.md`](../../../docs/api-contract.md)와 프런트엔드 타입을 함께 수정한다.