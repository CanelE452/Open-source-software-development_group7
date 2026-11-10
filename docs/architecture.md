# 프로젝트 구조

백엔드, 프런트엔드, 평가 코드를 한 저장소에서 관리한다. 백엔드는 수집·저장·검색·요약으로 나누고 API를 통해 화면과 연결한다.

## 처리 흐름

```text
GitHub API → collection → storage → search → API → frontend
                 선택한 Issue + 댓글 → summarization → API → frontend
evaluation → 고정한 입력·스냅샷으로 검색/요약 품질 확인
```

API 라우터는 HTTP 입력·출력과 오류를 담당한다. `collection/`은 Issue·댓글 수집, `storage/`는 SQLite와 스냅샷, `search/`는 BM25·Semantic·Hybrid, `summarization/`은 Ollama 연동·구조화 요약·근거 검증을 담당한다. 모듈에서 FastAPI에 직접 의존하는 코드는 줄여 독립적으로 테스트한다.

프런트엔드는 `api/`에 서버 호출, `types/`에 API 타입, `components/`에 공통 UI, `features/`에 검색·상세 화면을 둔다.

## 역할 분담

- 김민재 (`@CanelE452`): `storage/`, `search/`, 메인 파이프라인과 저장소 관리.
- 신은지 (`@eunji8319`): `api/`, `collection/`, GitHub 연동, 백엔드 실행 설정.
- 김민수 (`@mins-oo`): `summarization/`, Ollama 연동, 요약 스키마와 근거 검증.
- 김서현 (`@narnia0302-cloud`): `frontend/`, 문제 입력과 상세 요약 대시보드.
- API 형식과 공통 설정은 관련 담당자가 함께 리뷰한다. 리뷰 담당은 `.github/CODEOWNERS`에 정리한다.

## 데이터와 모델

`data/`에는 로컬 SQLite, 수집 스냅샷, 임베딩, 모델 캐시를 둔다. 실제 파일은 Git에서 제외한다. 작은 비밀 정보 없는 테스트 fixture만 테스트 폴더에 넣는다. 평가 질의와 사람의 관련성 판정은 `evaluation/datasets/`, 재현 설정은 `evaluation/`, 실행 결과는 Git에서 제외하는 `evaluation/results/`에 둔다. 평가 결과를 제출할 때는 데이터·모델 버전과 스냅샷 해시를 기록한다.

## 개발 현황

상태 API와 기본 화면, SQLite 저장·검색 CLI를 구성했다. 실행 방법은 [저장·검색 안내](sqlite-search.md), 수집·검색 HTTP API와 요약 연동은 [개발 순서](roadmap.md)를 따른다. API 형식은 [API 문서](api-contract.md)에서 맞춘다. Ollama 요약 모델은 선정 예정이다.
