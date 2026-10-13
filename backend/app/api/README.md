# API

기본 담당: 신은지 (`@eunji8319`).

HTTP 요청 검증, 응답, 오류 처리를 담당한다. 엔드포인트는 `routes/`에 나누고 `app/main.py`에서 라우터를 연결한다. 수집·검색·요약 처리는 해당 모듈에 둔다.

현재 라우터는 `GET /api/health`뿐이다. 검색과 요약 API를 구현할 때 먼저 [`docs/api-contract.md`](../../../docs/api-contract.md)와 프런트엔드 타입을 확인한다.
