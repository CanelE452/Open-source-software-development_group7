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

DB 저장·검색 점수·AI 요약 생성은 담당 모듈에서 개발 중이며 릴리스는 없습니다.
