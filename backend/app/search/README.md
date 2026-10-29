# Search

기본 담당: 김민재 (`@CanelE452`).

SQLite 스냅샷에서 BM25·Semantic·Hybrid 검색을 수행한다. 실행 방법은 [저장·검색 안내](../../../docs/sqlite-search.md)를 참고한다.

## Python 인터페이스

```python
from backend.app.search import SearchEngine
from backend.app.storage import SQLiteRepository

with SQLiteRepository("data/database/issues.sqlite3") as repository:
    engine = SearchEngine(repository)
    result = engine.search(
        "owner/repository", "database locked",
        error="WinError 32", environment="Windows", method="bm25", top_k=5,
    )
    print(result.to_dict())
```

`problem`은 필수이며 `method`는 `bm25 | semantic | hybrid`, `top_k`는 정수 1~20이다. `snapshot_id`를 생략하면 수집 시각이 가장 최근인 스냅샷을 사용한다. 다른 저장소의 스냅샷을 지정하면 오류다.

응답에는 `repository`, `method`, `results`, `snapshot`, `model`이 들어간다. 결과는 Issue 번호·제목·URL·점수·점수 종류를, 스냅샷은 ID·내용 해시·수집 시각·범위·부분 수집 여부를 담는다. 스냅샷이 없으면 `snapshot: null`과 빈 결과를 반환한다.

## 검색 방식

- BM25: 제목·본문·댓글 전체를 Unicode 단어와 `casefold`로 검색한다. `k1=1.5`, `b=0.75`이며 한국어 형태소 분석은 하지 않는다. 일치 단어가 없으면 빈 결과를 반환한다.
- Semantic: 문서 임베딩의 코사인 유사도로 정렬한다. 관련성 임계값을 두지 않아 낮거나 음수인 점수도 포함될 수 있다.
- Hybrid: 전체 BM25·Semantic 순위를 RRF `sum(1 / (60 + rank))`로 결합한다.

동점이면 Issue 번호 오름차순으로 정렬한다. `score_type`은 각각 `bm25`, `cosine`, `rrf`이며 점수는 해결 확률이 아니다.

## 모델과 캐시

Semantic·Hybrid는 `backend/requirements-search.txt` 설치 후 `SentenceTransformerEmbedder`를 엔진에 전달한다.

```python
from backend.app.search import SentenceTransformerEmbedder

with SQLiteRepository("data/database/issues.sqlite3") as repository:
    engine = SearchEngine(repository, SentenceTransformerEmbedder())
    result = engine.search("owner/repository", "database locked", method="hybrid")
```

기본 모델은 [paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2), revision은 `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`다. CPU에서 384차원 정규화 벡터를 생성하며 `trust_remote_code=False`로 로드한다. 다른 모델은 ID와 40자리 commit SHA를 함께 지정한다.

첫 임베딩 요청에 모델을 내려받는다. 이후 `local_files_only=True`로 로컬 모델만 사용할 수 있다. 설치·모델 로드 실패는 오류로 반환한다. 기본 모델은 최대 128토큰까지만 읽으므로 긴 본문·댓글은 일부만 반영된다.

문서 캐시는 SQLite에 저장하며 키는 모델 ID·revision·`SHA256(issue-text-v1 + NUL + 정규화 텍스트)`다. 제목·본문·ID순 댓글을 NFKC와 공백 정리 후 합친다. URL·수집 시각은 제외한다. 원문·모델·전처리가 바뀌면 다시 계산하고, 같은 텍스트는 스냅샷이 달라도 재사용한다. 질의 벡터는 매번 계산한다.

벡터 개수·차원·유한값·0벡터를 검사한다. 모델 가중치 변경 시 revision을, 전처리나 임베딩 정책 변경 시 전처리 버전을 갱신한다.

## 테스트

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_search.py backend/tests/test_embeddings.py -q
```

단위 테스트는 고정 벡터로 검색·RRF·캐시를 확인한다. 실제 모델 비교와 평가 범위는 [평가 안내](../../../evaluation/README.md)에 정리한다.
