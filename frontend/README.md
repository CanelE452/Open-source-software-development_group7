# 프런트엔드

담당: 김서현 (`@narnia0302-cloud`). React, TypeScript, Vite를 사용하는 화면 모듈입니다. 저장소 분석 요청과 진행 상태, Issue 검색, 결과 목록, Issue 상세와 근거 기반 요약 화면을 구현했습니다. 검색·요약 API가 503을 반환하면 `src/api/fixtures/`의 Mock 데이터로 대체해 표시하므로, 화면에 보이는 검색·요약 결과가 실제 값인지 백엔드 연결 상태와 함께 확인해야 합니다.

## 설치와 개발

저장소 루트에서 Node.js 24 LTS를 사용합니다. 백엔드는 별도 터미널에서 `127.0.0.1:8000`으로 실행합니다.

Windows PowerShell:

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run dev
```

Ubuntu:

```bash
npm --prefix frontend ci
npm --prefix frontend run dev
```

개발 화면: `http://127.0.0.1:5173`. Vite가 `/api` 요청을 백엔드로 전달합니다. 프런트엔드에 GitHub 토큰 등 비밀 정보를 넣지 않습니다. 특히 `VITE_` 환경 변수는 브라우저에 공개됩니다.

## 확인 명령

Windows PowerShell에서 저장소 루트 기준:

```powershell
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
```

Ubuntu에서 저장소 루트 기준:

```bash
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

빌드 결과는 `frontend/dist/`에 생성됩니다. 루트에서 `npm --prefix frontend run preview`를 실행하면 이 정적 빌드를 확인할 수 있습니다. API 통합 확인에는 `/api` 프록시가 있는 개발 서버를 사용합니다.

## 폴더 경계

```text
src/
  api/                   서버 호출
  types/                 API 입력·출력 타입
  components/            재사용 UI
  features/
    search/              입력, 검색 상태, 결과 목록
    issue-detail/        Issue·댓글, 요약, 근거 링크
  App.tsx                앱 진입 화면
  main.tsx               React 시작점
```

작업 전 루트의 `CONTRIBUTING.md`, `docs/architecture.md`, `docs/api-contract.md`를 확인합니다. API 변경은 백엔드 담당자와 조율하고 타입·문서를 함께 수정합니다.

## 실제 API 연동 테스트 및 확인 절차

프론트엔드 대시보드와 FastAPI 백엔드(`/api`) 간의 전체 워크플로우(수집 → 저장·색인 → 검색/직접 조회 → 상세·요약 조회) 및 예외 상태 처리를 검증하는 절차입니다.

### 1. 사전 준비 및 서버 실행 (프로젝트 루트 기준)

1. **정적 타입 및 프로덕션 빌드 검증**
   ```powershell
   npm.cmd --prefix frontend run typecheck
   npm.cmd --prefix frontend run build
   ```
   * 타입 오류 및 번들링 에러가 0건인지 확인합니다.

2. **백엔드 및 프론트엔드 개발 서버 실행**
   * **터미널 1 (백엔드)**:
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
     * 신규 의존성이 추가된 경우 실행 전 `.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt`를 실행합니다.
     * `.env` 파일이 없어도 서버 기동 및 수집·상세 조회 테스트가 가능하며, AI 요약 기능의 실제 LLM 호출까지 검증할 때만 `.env.example`을 참고해 API 키를 설정합니다.
   * **터미널 2 (프론트엔드)**:
```powershell
npm.cmd --prefix frontend run dev
```
   * 기본값은 **실제 API 연동 모드**이며, 백엔드 없이 UI만 단독으로 점검할 때만 `frontend/.env`에 `VITE_USE_MOCK=true`를 설정합니다.

---

### 2. 전체 흐름(E2E) 단계별 확인

GitHub API 비인증 호출 제한(시간당 60회)과 수집 시간을 고려해, **열린 이슈와 닫힌 이슈(`open` + `closed`) 및 댓글을 모두 합쳐도 규모가 작은 현재 과제 저장소나 소규모 공개 저장소**로 먼저 확인합니다.

1. **저장소 수집 및 색인 상태 폴링 (`POST /api/repositories/analyze` → `GET /api/repositories/jobs/{job_id}`)**
   * 저장소 경로(`owner/repo` 또는 전체 GitHub URL)를 입력하고 **[저장소 분석 시작]**을 클릭합니다.
   * 상태 배지가 `queued → collecting → indexing → completed` 순으로 자동 갱신되는지 확인합니다.
   * 수집된 Issue 수, 댓글 수, `인덱싱: 완료` 여부(`progress.indexed`), 스냅샷 ID 및 수집 범위(`collection.scope`)가 화면에 정상 표시되는지 확인합니다.

2. **이슈 검색 (`POST /api/search`) 또는 Issue 번호 직접 조회**
   * **검색 모듈 연결 시**: 문제 설명(필수)과 오류 메시지·환경 정보(선택)를 입력하고 `hybrid` / `bm25` / `semantic` 방식별로 **[관련 Issue 검색]**을 실행해 대상 스냅샷 정보(`snapshot_id`, `scope.issue_count`)와 결과 카드(`score`, `score_type`, 상태 뱃지)를 확인합니다.
   * **검색 모듈 미연결 시(`503 search_unavailable`)**: 하단의 **[Issue 번호로 바로 보기]** 입력칸에 실제 존재하는 Issue 번호를 입력하고 **[상세 & AI 요약 조회]**를 클릭해 다음 단계로 진입합니다.

3. **이슈 상세 조회 (`GET /api/repositories/{owner}/{repo}/issues/{number}`)**
   * 직전에 분석·검색한 저장소 경로(`currentRepository`)가 상세 화면 상단 및 API 요청 경로에 정확히 반영되는지 확인합니다.
   * 이슈 번호, 제목, 작성자, 상태, 본문 내용, 댓글 목록 및 각 댓글의 GitHub 원문 링크가 정상 렌더링되는지 확인합니다.

4. **근거 기반 AI 요약 (`POST /api/repositories/{owner}/{repo}/issues/{number}/summary`)**
   * LLM 설정이 연결된 경우 상단 대시보드에 6개 항목(**문제 상황**, **발생 조건**, **해결 방법**, **논의 결과**, **후속 확인 사항**, **미확인 사항**)과 `[본문]`/`[댓글]` 출처 뱃지, 원문 발췌 링크가 표시되는지 확인합니다.
   * LLM 설정이 없는 환경에서는 상단에 요약 조회 불가(`503`) 안내 배너가 표시되고, 하단 원문 본문과 댓글은 정상 유지되는지 확인합니다.

---

### 3. 예외 및 오류 상태 확인 (Mock 자동 대체 차단 검증)

실제 API 모드에서 백엔드 오류 발생 시 Mock 데이터로 대체되지 않고 실제 상태를 안내하는지 확인합니다.

* **잘못된 저장소 형식 (`400 invalid_repository`)**: 슬래시가 없는 경로(예: `invalid-repo`) 요청 시 상단 오류 배너에 백엔드 오류 메시지가 출력되는지 확인합니다.
* **검색 결과 없음 (`results: []`)**: 무관한 키워드 검색 시 에러 대신 `'검색 조건과 일치하는 관련 Issue를 찾지 못했습니다.'` 안내와 대상 스냅샷 정보가 표시되는지 확인합니다.
* **부분 수집 상태 (`state: "partial"`, `partial_collection: true`)**: 수집 제한 등으로 일부만 수집된 경우 `collection.notes` 배열의 제한 사유가 안내 배너에 출력되는지 확인합니다.
* **요약 근거 부족 (`status: "insufficient_evidence"`)**: 정보가 부족한 이슈 조회 시 `⚠️ 근거 부족 (추측 지양 모드)` 뱃지가 표시되고 `text`가 `null`인 항목이 `'확인된 근거가 없습니다.'` 문구로 안전하게 표시되는지 확인합니다.
* **기능 모듈 미연결 (`503`) 및 백엔드 서버 중단**: `503 search_unavailable`, `503 summary_unavailable` 응답이나 백엔드 서버 중지 상태에서 요청 시 Mock 데이터 대신 실제 오류 안내 배너가 표시되는지 확인합니다.