# API 계약

모든 경로에 `/api` 접두사가 붙는다. 경로나 필드를 바꾸면 이 문서와 `frontend/src/types/`도
함께 수정한다. 검색 점수와 요약 생성 로직은 각 담당 모듈에서 구현하며, 아래는 API 입·출력
형식이다.

## 구현: 서버 상태

`GET /api/health` → HTTP 200

```json
{"status": "ok", "service": "issue-finder"}
```

프로세스가 HTTP 요청에 응답하는지만 확인한다. DB·GitHub·모델 준비 상태를 보장하지 않는다.

## 구현: 저장소 분석과 작업 상태

`POST /api/repositories/analyze` → HTTP 202. 공개 저장소의 Issue 수집을 시작하고(검색 모듈이
연결돼 있으면 색인까지) 작업 ID를 돌려준다.

요청:

```json
{"repository": "owner/repo", "max_issues": 300}
```

`repository`는 `owner/repo` 또는 전체 URL. `max_issues`는 선택(1~2000). 형식이 잘못되면 400.

응답:

```json
{"job_id": "…", "repository": "owner/repo", "state": "queued"}
```

`GET /api/repositories/jobs/{job_id}` → HTTP 200. 없는 작업이면 404.

```json
{
  "job_id": "…",
  "repository": "owner/repo",
  "state": "completed",
  "progress": {"collected_issues": 42, "collected_comments": 0, "indexed": false},
  "collection": {
    "repository": "owner/repo",
    "collected_at": "2026-10-29T00:00:00+00:00",
    "snapshot_id": "a1b2c3d4e5f60718",
    "scope": {
      "state": "all", "per_page": 100, "max_issues": 300,
      "pages_fetched": 1, "issue_count": 42, "pull_requests_excluded": 8
    },
    "partial_collection": false,
    "notes": []
  },
  "error": null,
  "created_at": "…",
  "updated_at": "…"
}
```

`state`는 `queued | collecting | indexing | completed | partial | failed`. 부분 수집이면
`partial`이며 `collection.notes`에 사유를 남긴다. 실패하면 `failed`이며 `error`에 사유를 담는다.
수집 시각·범위·스냅샷 식별자는 항상 `collection`에 기록한다.

## 구현: 검색

`POST /api/search` → HTTP 200. 검색 모듈 미연결 시 503(`search_unavailable`).

```json
{
  "repository": "owner/repository",
  "problem": "관찰한 문제 상황",
  "error": "선택적 오류 메시지",
  "environment": "선택적 버전·환경",
  "method": "hybrid",
  "top_k": 5
}
```

`problem`은 필수, `method`는 `bm25 | semantic | hybrid`, `top_k`는 1~20. 응답에는 Issue
번호·제목·원문 URL·점수와 점수 종류를 넣고, 검색한 스냅샷 정보를 함께 제공한다. 검색 점수는
중복 확률이나 해결 성공률로 표현하지 않는다.

```json
{
  "repository": "owner/repository",
  "method": "hybrid",
  "results": [
    {"number": 47752, "title": "…", "html_url": "https://github.com/…",
     "score": 0.87, "score_type": "hybrid", "state": "closed"}
  ],
  "snapshot_id": "a1b2c3d4e5f60718",
  "collected_at": "2026-10-29T00:00:00+00:00",
  "partial_collection": false,
  "scope": {"state": "all", "per_page": 100, "max_issues": 300,
            "pages_fetched": 1, "issue_count": 42, "pull_requests_excluded": 8}
}
```

## 구현: Issue 상세

`GET /api/repositories/{owner}/{repo}/issues/{number}` → HTTP 200. 선택한 Issue의 본문·댓글·
원문 링크를 수집해 돌려준다. PR 번호나 없는 Issue는 404.

```json
{
  "repository": "owner/repo",
  "number": 47752,
  "title": "…",
  "html_url": "https://github.com/…",
  "state": "closed",
  "body": "…",
  "author": "alice",
  "created_at": "…",
  "updated_at": "…",
  "comments": [
    {"id": 1, "html_url": "https://github.com/…#issuecomment-1",
     "body": "…", "author": "bob", "created_at": "…"}
  ],
  "comment_count": 1,
  "collected_at": "2026-10-29T00:00:00+00:00",
  "partial_collection": false,
  "notes": []
}
```

## 구현: 요약

`POST /api/repositories/{owner}/{repo}/issues/{number}/summary` → HTTP 200. 원문을 수집한 뒤
요약 모듈에 넘긴다. 요약 모듈 미연결 시 503(`summary_unavailable`).

요약은 `problem`, `conditions`, `solution`, `discussion`, `follow_up`, `unknowns` 항목을
사용한다. 각 항목에는 `text`와 `evidence`가 있다. 근거는 원문 `url`과 짧은 `excerpt`를 함께
보관하고, `source_type`으로 본문(`issue_body`)·댓글(`comment`)을 구분한다. 설명할 근거가
없으면 만들어 채우지 않는다.

```json
{
  "repository": "owner/repo",
  "number": 47752,
  "html_url": "https://github.com/…",
  "problem": {"text": null, "evidence": []},
  "conditions": {"text": null, "evidence": []},
  "solution": {"text": null, "evidence": []},
  "discussion": {"text": null, "evidence": []},
  "follow_up": {"text": null, "evidence": []},
  "unknowns": {"text": null, "evidence": []},
  "status": "insufficient_evidence",
  "partial_collection": false
}
```

`status`는 `completed | insufficient_evidence | failed`를 구분한다. 요약 실패 시에도 원문과
확보한 근거를 계속 확인할 수 있어야 한다. 이 형식은 요약 담당의 `IssueSummary`와 같다.

## 공통 오류 응답

요청 본문 검증 실패는 FastAPI 기본 422를 사용한다. 그 밖의 도메인 오류는 아래 형식이다.

```json
{"error": {"code": "invalid_repository", "message": "…", "detail": null}}
```

| code | HTTP | 상황 |
| --- | --- | --- |
| `invalid_repository` | 400 | 저장소 형식 오류 |
| `not_found` | 404 | 저장소·Issue 없음 또는 PR 번호 |
| `rate_limited` | 429 | GitHub 호출 제한(`detail.retry_after` 초) |
| `upstream_unavailable` | 502 | GitHub 네트워크·서버 오류 |
| `search_unavailable` | 503 | 검색 모듈 미연결 |
| `summary_unavailable` | 503 | 요약 모듈 미연결 |

## 모듈 연결점

API는 검색·요약을 직접 구현하지 않고 연결점(포트, `backend/app/api/backends.py`)에만
의존한다. 담당 모듈이 `SearchBackend`·`SummaryBackend`를 구현해 `app.state`에 주입하면
해당 API가 동작한다. 그 전에는 503을 돌려주므로 수집·상세 API는 독립적으로 쓸 수 있다.
