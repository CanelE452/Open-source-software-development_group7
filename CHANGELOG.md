# Changelog

## Unreleased

### [#7](https://github.com/CanelE452/Open-source-software-development_group7/pull/7) 검색·상세 대시보드 — 김서현 (2026-11-10 병합)

Added

- 백엔드 API 명세 기준 프런트 타입(`types/api.ts`)과 API 통신 모듈(`api/issueApi.ts`).
- 검색·요약 API 503 응답에 대비한 Mock 데이터(`api/fixtures/mockData.ts`).
- 저장소 분석 요청, 분석 상태 확인, 검색 입력 폼, 결과 목록 화면(`features/search/`).
- Issue 상세 본문·댓글과 근거 기반 요약 대시보드(`features/issue-detail/`).

Changed

- `App.tsx`가 검색 화면과 Issue 상세 화면을 전환.

### [#5](https://github.com/CanelE452/Open-source-software-development_group7/pull/5) Issue 수집·API 연결 — 신은지 (2026-11-10 병합)

Added

- 공개 저장소 URL 검증(`collection/repository.py`), PR 제외·페이지네이션을 적용한 Issue 수집(`collection/issues.py`), Issue 상세·댓글 수집(`collection/issue_detail.py`).
- GitHub REST 클라이언트와 호출 제한·네트워크 실패·저장소 없음 예외 처리(`integrations/github.py`).
- 저장소 분석·작업 상태·검색·Issue 상세·요약 API(`api/routes/`)와 요청·응답 스키마(`schemas/`), 메모리 작업 저장소(`api/jobs.py`).
- 검색·요약 모듈 연결점(`api/backends.py`)과 미연결 시 503 응답, 공통 오류 응답 형식(`api/errors.py`).
- 서버 설정과 `.env` 로딩(`core/config.py`).
- 수집·API 테스트(`test_collection.py`, `test_api.py`, `test_repository.py`).

Changed

- `docs/api-contract.md`를 구현 기준으로 개정(요청·응답 예시, 오류 코드 표).
- `httpx`를 실행 의존성(`requirements.txt`)으로 이동하고 `main.py`에 라우터·오류 핸들러 연결.

### [#6](https://github.com/CanelE452/Open-source-software-development_group7/pull/6) Issue 요약 — 김민수 (2026-11-10 병합)

Added

- Ollama Cloud 클라이언트(`integrations/ollama.py`, 기본 모델 `gpt-oss:20b`).
- 문제·조건·해결·논의·후속·미확인 항목과 근거(`evidence`)를 담는 요약 스키마와 근거 검증 규칙(`schemas/summarization_schema.py`).
- Issue URL을 입력받는 요약 스크립트(`summarization/summarize.py`).
- 요약 근거 검증 테스트와 검증 보고서 생성(`test_summary_validation.py`, `backend/tests/reports/`).

Changed

- `NOTICE`에 서드파티 모델(gpt-oss-20b, Apache License 2.0) 고지 추가.
- 요약·Ollama 연동·테스트 안내 문서 작성(`summarization/`, `integrations/`, `backend/tests/` README).

### [#8](https://github.com/CanelE452/Open-source-software-development_group7/pull/8) SQLite 저장·검색 — 김민재 (2026-11-10 병합)

Added

- SQLite Issue·댓글 저장, 내용 해시를 가진 수집 스냅샷, 임베딩 캐시(`storage/`).
- BM25·Semantic·RRF Hybrid 검색(`search/engine.py`), 다국어 MiniLM 임베딩 어댑터(`search/embeddings.py`), JSON import·검색 CLI(`search/__main__.py`).
- 검색 비교 도구(`evaluation/compare.py`, P@K·Recall@K·MRR@K)와 가상 Issue 8개·질의 4개 예제(`evaluation/datasets/`).
- Semantic·Hybrid 선택 의존성(`backend/requirements-search.txt`).
- 저장·검색·CLI·평가 테스트.

Changed

- 저장·검색 실행 문서 추가(`docs/sqlite-search.md`, `docs/sqlite-search-plan.md`, `_docs/history/`)와 `NOTICE` 갱신.

### PR 없이 master에 반영

- 2026-10-13 `01bec19` 초기 구조: 역할별 백엔드 모듈·프런트엔드 폴더, FastAPI 상태 API와 React/Vite 시작 앱, 구조·API 계약 초안·설치·협업·개발 순서 문서, Issue/PR 템플릿·CODEOWNERS·CI, 비밀 정보 제외 규칙과 MIT 라이선스.
- 2026-11-10 `112f0e9` 요약 검증 보고서 1개의 줄바꿈을 LF로 정리.

검색·요약 모듈의 HTTP API 연결과 실제 저장소 대상 평가는 아직 구현하지 않았으며 릴리스는 없습니다.