# SQLite 저장·검색

[이슈 #2](https://github.com/CanelE452/Open-source-software-development_group7/issues/2)의 김민재 담당 구현이다. SQLite에 Issue·댓글을 스냅샷으로 저장하고 BM25·Semantic·Hybrid 검색과 비교 CLI를 제공한다. GitHub 수집과 검색 HTTP API는 별도 모듈에서 연결한다.

## 실행

Python 3.12 이상을 사용한다. 저장소 루트의 PowerShell에서 실행하며, 기존 `.venv`가 있으면 생성 명령을 생략한다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt

$snapshot = .\.venv\Scripts\python.exe -m backend.app.search --db data/database/search-smoke.sqlite3 import --input evaluation/datasets/search-smoke.json | ConvertFrom-Json

.\.venv\Scripts\python.exe -m backend.app.search --db data/database/search-smoke.sqlite3 search --repository example/issue-search-fixture --problem 'sqlite database is locked' --method bm25 --top-k 3 --snapshot-id $snapshot.snapshot_id
```

BM25와 SQLite는 추가 검색 패키지 없이 실행된다. 위 fixture는 실제 수집 자료가 아닌 가상 Issue 8개다.

Semantic·Hybrid를 사용하려면 선택 의존성을 설치한다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-search.txt

.\.venv\Scripts\python.exe -m backend.app.search --db data/database/search-smoke.sqlite3 search --repository example/issue-search-fixture --problem '두 프로세스가 동시에 데이터베이스에 쓰면 잠금 오류가 납니다' --method semantic --top-k 3 --snapshot-id $snapshot.snapshot_id

.\.venv\Scripts\python.exe -m backend.app.search --db data/database/search-smoke.sqlite3 search --repository example/issue-search-fixture --problem 'database lock' --method hybrid --top-k 3 --snapshot-id $snapshot.snapshot_id
```

첫 검색에서 모델을 `data/models/`에 내려받고 로컬 CPU로 실행한다. 다운로드 후 `$env:HF_HUB_OFFLINE = '1'`로 로컬 파일만 사용할 수 있다. 다른 모델은 전역 인자 `--model-id ID --model-revision 40자리_SHA`를 함께 지정한다. 설치·모델 로드 오류는 그대로 반환한다.

기본 모델·고정 revision, RRF·캐시 설정과 128토큰 입력 제한은 [검색 모듈](../backend/app/search/README.md)에 정리한다. DB·모델·캐시·실행 결과는 Git에서 제외한다.

## 수집·API 연결

수집 모듈은 `SQLiteRepository.save_snapshot()`에 `Issue`·`Comment`와 수집 시각·범위·부분 수집 여부를 전달한다. [저장 모듈](../backend/app/storage/README.md)의 입력 형식을 사용하며, JSON import는 다음 형식이다.

```json
{
  "repository": "owner/repository",
  "collected_at": "2026-10-29T00:00:00Z",
  "collection_scope": {"state": "all", "pages": 2, "comments": "included"},
  "partial_collection": true,
  "issues": [
    {
      "number": 12,
      "title": "수집한 제목",
      "body": "수집한 본문",
      "url": "https://github.com/owner/repository/issues/12",
      "state": "open",
      "comments": [
        {"id": 42, "body": "수집한 댓글", "url": "https://github.com/owner/repository/issues/12#issuecomment-42"}
      ]
    }
  ]
}
```

API에서는 `SearchEngine.search(repository, problem, error=..., environment=..., method=..., top_k=..., snapshot_id=...)`를 호출한다. `to_dict()`는 검색 결과와 스냅샷 메타데이터, 모델 정보를 반환한다. 입력 조건은 [검색 모듈](../backend/app/search/README.md), HTTP 형식은 [API 계약](api-contract.md)을 따른다. 현재 HTTP API는 `GET /api/health`만 구현했다.

## 테스트와 평가

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

2026-10-29 Windows / Python 3.12.14에서 전체 테스트 83개와 하위 테스트 9개가 통과했다. 기존 Starlette TestClient의 httpx 사용 중단 경고가 1개 있다. 단위 테스트는 고정 벡터로 검색·RRF·캐시를 확인하며 실제 모델 품질을 평가하지 않는다. 상세 실행 기록은 [작업 이력](../_docs/history/2026-10-29.md)에 남긴다.

구현 당시 별도 작업 환경에서 고정 MiniLM 모델을 실행해 가상 Issue 8개·질의 4개를 K=3으로 비교했다. 실행 방법과 질의 형식은 [평가 안내](../evaluation/README.md)를 참고한다.

```text
Method       P@3       Recall@3   MRR@3
───────────────────────────────────────
BM25         0.2500    0.7500     0.7500
Semantic     0.3333    1.0000     1.0000
Hybrid       0.3333    1.0000     1.0000
```

가상 예제의 동작 점검 결과로, 실제 공개 저장소의 검색 성능이나 방식별 우열을 뜻하지 않는다. 실제 수집 자료와 독립적인 사람 판정 평가는 팀 통합 후 진행한다. 문서 벡터 캐시는 첫 실행에 8개를 계산했고 DB 재개방 후에는 질의 벡터 1개만 계산했으며 결과는 같았다.

- 스냅샷 ID: `00ddb185-16e9-4394-9a68-eaf399dc0ce9`
- 스냅샷 해시: `943d63e5e05fbbd6749f1cae4e4354e387e9e6cb13a7c85cd3cadcc376207b86`
- 질의셋 해시: `4be3d82d0c358df9c5329247c0f124b75db8fbbcc1a1b348cae8eb79c4212fc6`
- 모델 revision: `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`
- 패키지: sentence-transformers 5.1.2 / transformers 4.57.6 / torch 2.15.0

원본 작업 환경의 결과 파일은 `evaluation/results/search-smoke-run1.json`과 `real-cache-verification.json`이며 Git에서 제외했다. AI는 구현·문서 편집과 로컬 검증을 보조했고, stage·commit·push는 사용자가 직접 수행한다.
