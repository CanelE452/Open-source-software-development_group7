# Storage

기본 담당: 김민재 (`@CanelE452`).

`SQLiteRepository`가 Issue·댓글과 수집 스냅샷을 저장한다. 로컬 DB는 `data/database/`에 두며 Git에서 제외한다.

## 사용법

```python
from backend.app.storage import Issue, SQLiteRepository

with SQLiteRepository("data/database/issues.sqlite3") as storage:
    snapshot = storage.save_snapshot(
        "owner/repository",
        [Issue(number=1, title="SQLite 잠금 오류", body="수집한 본문")],
        collected_at="2026-10-29T10:00:00Z",
        collection_scope={"state": "all", "pages": 1},
        partial_collection=False,
    )
    issues = storage.list_issues(snapshot.snapshot_id)
    issue = storage.get_issue(snapshot.snapshot_id, 1)
```

위 코드는 입력 형식 예시다. 수집 모듈에서 GitHub 응답을 `Issue`·`Comment`로 변환하고, nullable 본문은 빈 문자열로 넘긴다. 원문 URL을 그대로 보관하며 수집 누락은 `collection_scope`와 `partial_collection`에 표시한다.

## 저장 규칙

- `snapshots`, `issues`, `comments`, `embedding_cache` 테이블을 사용한다. 스키마 버전은 SQLite `user_version=1`이다.
- 저장소 이름은 `owner/name`을 소문자로 정규화한다. 스냅샷에는 UUID·UTC 수집 시각·수집 범위·부분 수집 여부·Issue 수·내용 해시를 보관한다. 입력 시각에는 시간대가 필요하다.
- 새 수집은 새 스냅샷으로 저장한다. 기존 ID 재사용, 중복 Issue, 잘못된 입력이나 쓰기 실패 시 트랜잭션 전체를 취소한다.
- 내용 해시는 저장소·수집 범위·부분 수집 여부·번호순 Issue·ID순 댓글의 JSON으로 계산한다. 스냅샷 ID와 수집 시각은 제외한다.
- `latest_snapshot(repository)`는 수집 시각이 가장 최근인 스냅샷을 반환하며, 없으면 `None`이다. 없는 ID 조회는 `KeyError`다.
- 인스턴스는 SQLite 연결과 잠금을 공유한다. 사용 후 `with` 또는 `close()`로 닫는다.

`get_embedding(model_id, model_revision, text_hash)`·`put_embedding(...)`으로 문서 벡터를 저장·조회한다. DB를 다시 열어도 캐시는 유지되며 빈 벡터와 비정상 값은 거절한다. 키 생성과 갱신 기준은 [검색 모듈](../search/README.md)에 정리한다.

## 테스트

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_storage.py -q
```
