# Issue #2 구현 범위

[이슈 #2](https://github.com/CanelE452/Open-source-software-development_group7/issues/2): 수집한 Issue를 SQLite 스냅샷으로 저장하고 동일 입력에서 세 검색 방식을 비교한다.

- `storage/`: Issue·댓글, 수집 시각·범위·부분 수집 여부와 내용 해시를 저장한다. 스냅샷 보존과 트랜잭션을 검증한다.
- `search/`: BM25·Semantic·RRF Hybrid와 모델·revision·텍스트별 임베딩 캐시를 구현한다.
- `search/__main__.py`: 수집 JSON import와 검색 CLI를 제공한다.
- `evaluation/`: 고정 스냅샷·질의·관련성 판정으로 검색 방식별 지표를 비교한다.

빈 입력·쓰기 실패·스냅샷 격리·캐시 갱신·비정상 벡터·CLI를 테스트한다. 가상 예제 결과와 실제 수집 자료의 품질 평가는 구분한다. 실행법과 검증 결과는 [저장·검색 안내](sqlite-search.md)에 정리한다. HTTP 수집·검색 API, 요약과 프런트엔드는 각 담당 모듈에서 연결한다.
