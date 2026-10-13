# 프런트엔드

담당: 김서현 (`@narnia0302-cloud`). React, TypeScript, Vite를 사용하는 화면 모듈입니다. 현재 화면은 프로젝트 준비 안내만 표시하며 검색·상세 요약 기능은 아직 구현하지 않았습니다.

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
