# Changelog

## Unreleased

### Added

- 역할별 백엔드 모듈과 프런트엔드 폴더.
- FastAPI 상태 API와 React/Vite 최소 시작 앱.
- 구조·API 계약 초안·설치·협업·개발 순서 문서.
- Issue/PR 템플릿, CODEOWNERS, 백엔드 테스트·프런트 빌드 CI 구성.
- 비밀 정보·로컬 데이터 제외 규칙과 MIT 라이선스.

- 공개 저장소 URL 검증·PR 제외·페이지네이션을 적용한 Issue·댓글 수집(`collection/`)과 GitHub 연동(`integrations/github.py`).
- 분석·작업 상태, 검색, Issue 상세, 요약 API와 요청·응답 스키마(`schemas/`), 서버 설정(`core/config.py`).
- 검색·요약 모듈 연결점(포트)과 미연결 시 503 응답, 공통 오류 응답 형식.
- 호출 제한·네트워크 실패·부분 수집 예외 처리와 수집·API 테스트.

- SQLite Issue·댓글 저장과 수집 스냅샷, 임베딩 캐시 (#2).
- BM25·Semantic·Hybrid 검색과 JSON import·검색 CLI.
- 검색 비교 도구, 저장·검색·CLI 테스트와 실행 문서.

- Ollama Cloud 클라이언트(`integrations/ollama.py`), 요약 스키마와 Issue URL 입력 요약 스크립트(`summarization/`).
- 요약 근거 검증 테스트와 검증 보고서(`backend/tests/reports/`).

- API 통신 모듈, 검색 입력·분석 상태 확인·결과 목록 화면, Issue 상세·근거 기반 요약 대시보드.
- 검색·요약 API 503 응답에 대비한 Mock 데이터.

검색·요약 모듈의 HTTP API 연결과 실제 저장소 대상 평가는 아직 구현하지 않았으며 릴리스는 없습니다.