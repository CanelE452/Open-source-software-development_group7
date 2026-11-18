# Collection

기본 담당: 신은지 (`@eunji8319`).

GitHub Issue와 댓글을 수집한다. 페이지네이션, API 호출 제한, 수집 범위, 부분 수집 표시를 함께 처리한다. GitHub 클라이언트는 `integrations/github.py`에 둔다.

| 파일 | 역할 |
|---|---|
| `repository.py` | `owner/repo` 또는 URL 검증 (`parse_repository`) |
| `issues.py` | 저장소 Issue 목록 수집, PR 제외, 수집 범위·스냅샷 식별자 기록 (`collect_issues`) |
| `issue_detail.py` | 선택한 Issue의 본문·댓글 수집 (`collect_issue_detail`) |

수집 결과는 아직 `storage/`의 SQLite 스냅샷에 저장하지 않는다. API가 반환하는 `snapshot_id`는 수집 모듈이 만든 식별자이며, 저장 모듈의 스냅샷 ID와는 연결 전이다.