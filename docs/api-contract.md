# API 계약 초안

현재 구현한 API는 `GET /api/health`다. 나머지는 개발 예정인 API의 초안이다. 경로나 필드를 바꾸면 이 문서와 `frontend/src/types/`도 함께 수정한다.

## 현재 구현: 서버 상태

`GET /api/health` → HTTP 200

```json
{"status": "ok", "service": "issue-finder"}
```

프로세스가 HTTP 요청에 응답하는지만 확인한다. DB·GitHub·모델 준비 상태를 보장하지 않는다.

## 계획: 저장소 분석과 검색

- `POST /api/repositories/analyze`: 공개 GitHub 저장소의 Issue 수집·검색 인덱싱을 시작하고 작업 ID를 반환한다.
- `GET /api/repositories/jobs/{job_id}`: 수집 범위와 작업 상태·실패 정보를 조회한다.
- `POST /api/search`: 문제 설명과 오류·환경을 받아 관련 Issue 후보를 반환한다.

검색 요청 초안:

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

`problem`은 필수, `method`는 `bm25 | semantic | hybrid`, `top_k`는 1~20을 기준으로 한다. 결과에는 Issue 번호·제목·원문 URL·점수와 점수 종류를 넣는다. 검색 범위, 수집 시각, 부분 수집 여부, 스냅샷 식별자를 함께 제공한다. 검색 점수는 중복 확률이나 해결 성공률로 표현하지 않는다.

## 계획: Issue 상세와 요약

- `GET /api/repositories/{owner}/{repo}/issues/{number}`: 선택한 Issue의 본문과 댓글, 수집 범위·원문 링크를 조회한다.
- `POST /api/repositories/{owner}/{repo}/issues/{number}/summary`: 수집한 원문을 바탕으로 구조화 요약을 요청한다. 비동기 작업 여부는 요약 담당과 API 담당이 구현 PR에서 정한다.

요약은 `problem`, `conditions`, `solution`, `discussion`, `follow_up`, `unknowns` 항목을 사용한다. 각 항목은 `text`와 `evidence`를 가진다. 근거는 원문 `url`과 짧은 `excerpt`를 함께 보관하고, 본문/댓글 위치를 구분한다. 설명할 근거가 없으면 만들어 채우지 않는다.

항목 형식 예시:

```json
{
  "text": null,
  "evidence": []
}
```

`status`는 `completed | insufficient_evidence | failed`를 구분하고, 댓글 수집 누락 여부는 별도 `partial_collection`으로 표시한다. 요약 실패 시 원문과 확보한 근거를 계속 확인할 수 있어야 한다. 실제 예외 코드와 오류 응답 스키마는 API 구현에서 확정한다.

## 구현 순서

1. 수집·작업 상태·검색 요청/응답 스키마를 API 담당과 검색 담당이 확정한다.
2. 프런트는 확정된 타입과 비밀 정보 없는 fixture로 화면을 구현한다.
3. 요약 담당이 근거 위치·불확실성 표현을 정하고 상세/요약 API와 연결한다.
4. 성공·입력 오류·API 호출 제한·부분 수집·요약 실패를 통합 테스트한다.
