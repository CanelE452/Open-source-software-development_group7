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

## API 연결

형식은 [API 문서](api-contract.md)가 기준이다. 백엔드 경로는 `backend/app/`, 프런트 경로는 `frontend/src/` 기준이다.

### 백엔드

| ID | 엔드포인트 | 라우터 | 요청·응답 스키마 | 하위 호출 |
|---|---|---|---|---|
| A1 | `GET /api/health` | `api/routes/health.py` `health` | 없음 | 없음 |
| A2 | `POST /api/repositories/analyze` | `api/routes/repositories.py` `analyze_repository` | `schemas/analysis.py` `AnalyzeRequest`·`AnalyzeResponse` | `collection/repository.py` `parse_repository` → `api/jobs.py` `JobStore.create` → (백그라운드) `run_analysis` → `collection/issues.py` `collect_issues` → `integrations/github.py` `GitHubClient.iter_issues` → `SearchBackend.index` (연결 시) |
| A3 | `GET /api/repositories/jobs/{job_id}` | `api/routes/repositories.py` `get_job` | `schemas/analysis.py` `JobStatus`·`JobProgress`·`JobState`, `schemas/collection.py` `CollectionMetadata`·`CollectionScope` | `api/jobs.py` `JobStore.get` |
| A4 | `POST /api/search` | `api/routes/search.py` `search_issues` | `schemas/search.py` `SearchRequest`·`SearchResponse`·`SearchResultItem` | `parse_repository` → `api/backends.py` `SearchBackend.search` (기본값 `UnavailableSearchBackend` → 503) |
| A5 | `GET /api/repositories/{owner}/{repo}/issues/{number}` | `api/routes/repositories.py` `get_issue_detail` | `schemas/issues.py` `IssueDetailResponse`, `schemas/collection.py` `CollectedComment` | `parse_repository` → `collection/issue_detail.py` `collect_issue_detail` → `GitHubClient.get_issue`·`iter_comments` |
| A6 | `POST /api/repositories/{owner}/{repo}/issues/{number}/summary` | `api/routes/repositories.py` `summarize_issue` | `schemas/summary.py` `SummaryRequest`·`SummaryResponse`·`SummarySection`·`Evidence` | `collect_issue_detail` → `api/backends.py` `SummaryBackend.summarize` (기본값 `UnavailableSummaryBackend` → 503) |

라우터 등록은 `main.py` `create_app`, 의존성 주입은 `api/dependencies.py` `init_app_state`에서 한다.

### 프런트엔드

| ID | API 함수 (`api/issueApi.ts`) | 호출 위치 | 표시 컴포넌트 | 타입 (`types/api.ts`) |
|---|---|---|---|---|
| A1 | `api/client.ts` `getHealth` | 호출 없음 | 없음 | `HealthResponse` |
| A2 | `analyzeRepository` | `features/search/SearchSection.tsx` `handleAnalyzeRepo` (버튼: `SearchForm.tsx` `handleAnalyzeClick`) | 없음 | `AnalyzeRepoRequest`·`AnalyzeRepoResponse` |
| A3 | `getJobStatus` | `SearchSection.tsx` 폴링 `useEffect` (1.5초) | `features/search/JobProgress.tsx` | `JobStatusResponse` |
| A4 | `searchIssues` | `SearchSection.tsx` `handleSearch` (폼: `SearchForm.tsx` `handleSearchSubmit`) | `features/search/SearchResults.tsx` | `SearchIssuesRequest`·`SearchIssuesResponse`·`SearchIssueItem` |
| A5 | `getIssueDetail` | `features/issue-detail/IssueDetailSection.tsx` `fetchDetail` | `features/issue-detail/IssueBodyAndComments.tsx` | `IssueDetailResponse`·`IssueComment` |
| A6 | `getIssueSummary` | `IssueDetailSection.tsx` `fetchSummary` | `features/issue-detail/SummaryDashboard.tsx` | `IssueSummaryResponse`·`SummaryField`·`EvidenceItem` |

오류 응답은 `api/issueApi.ts` `handleResponse` 한 곳에서 처리한다. 응답 형식을 바꾸면 `api/fixtures/mockData.ts`의 `mockSearchResponse`·`mockIssueDetailResponse`·`mockIssueSummaryResponse`도 함께 고친다. 검색에 쓴 저장소는 `App.tsx`의 `currentRepository`로 상세 화면에 전달한다.

### 테스트

| ID | 파일과 테스트 |
|---|---|
| A1 | `test_health.py` `test_health_reports_service_status` |
| A2 | `test_api.py` `test_analyze_then_job_status_completes`·`test_analyze_indexes_when_search_available`·`test_analyze_rejects_invalid_repository`, `test_collection.py` `test_collect_issues_*` |
| A3 | `test_api.py` `test_job_not_found_returns_404` |
| A4 | `test_api.py` `test_search_*` 6개 (422·400·503·정상) |
| A5 | `test_api.py` `test_issue_detail_endpoint`·`test_issue_detail_not_found`, `test_collection.py` `test_collect_issue_detail_*` |
| A6 | `test_api.py` `test_summary_without_backend_returns_503`·`test_summary_with_backend_returns_result` |

프런트엔드 테스트는 아직 없고 `typecheck`와 `build`로만 확인한다.

### 스키마 대응

같은 데이터가 이름이 다른 타입으로 여러 곳에 정의되어 있다. 하나를 바꾸면 같은 행의 나머지도 확인한다.

| 데이터 | 백엔드 API 스키마 | 모듈 내부 타입 | 프런트 타입 | API 문서 절 |
|---|---|---|---|---|
| Issue 상세 | `schemas/issues.py` `IssueDetailResponse` | 요약 `schemas/summarization_schema.py` `IssueInput`·`IssueComment`, 저장 `storage/models.py` `Issue`·`Comment` | `IssueDetailResponse`·`IssueComment` | 구현: Issue 상세 |
| 요약 | `schemas/summary.py` `SummaryResponse`·`SummarySection`·`Evidence` | `schemas/summarization_schema.py` `IssueSummary`·`SummarySection`·`Evidence` (근거 검증 validator 포함) | `IssueSummaryResponse`·`SummaryField`·`EvidenceItem` | 구현: 요약 |
| 검색 | `schemas/search.py` `SearchRequest`·`SearchResponse`·`SearchResultItem` | `search/engine.py` `SearchResponse`·`SearchHit` (`to_dict()`) | `SearchIssuesRequest`·`SearchIssuesResponse`·`SearchIssueItem` | 구현: 검색 |
| 수집 범위·스냅샷 | `schemas/collection.py` `CollectionMetadata`·`CollectionScope` | 저장 `storage/models.py` `Snapshot`, 수집 `collection/issues.py` `make_snapshot_id` | `CollectionScope`, `JobStatusResponse.collection` | 구현: 저장소 분석과 작업 상태 |

`SearchResponse`, `Evidence`, `SummarySection`은 서로 다른 모듈에 같은 이름의 다른 클래스로 있으므로 import 경로를 확인한다.

## 개발 현황

- 상태·저장소 분석·검색·Issue 상세·요약 API, SQLite 저장·검색 CLI, Ollama 요약 스크립트, 검색·상세 화면을 구성했다.

- 수집(`collection/`)과 Issue 상세 API는 GitHub와 연동해 동작한다.

- 검색(`search/`)과 요약(`summarization/`)은 `api/backends.py`의 연결점에 아직 주입하지 않아 `POST /api/search`와 요약 API는 503을 반환하고, 화면은 이때 Mock 데이터를 보여준다.

- 분석 작업 상태는 메모리에만 있고 수집 결과는 아직 `storage/`에 저장하지 않는다.

- 실행 방법은 [저장·검색 안내](sqlite-search.md), 남은 연결 작업은 [개발 순서](roadmap.md)를 따른다. API 형식은 [API 문서](api-contract.md)에서 맞춘다. 요약 모델은 Ollama Cloud의 `gpt-oss:20b`를 사용한다.