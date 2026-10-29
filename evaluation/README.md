# 검색·요약 평가

동일한 SQLite 스냅샷과 질의셋으로 BM25·Semantic·Hybrid 검색을 비교한다. 요약 평가는 별도 구현 예정이다.

- `datasets/`: 팀이 판정한 작은 질의·관련 Issue 목록과 요약 점검 사례. GitHub 토큰이나 개인 로그를 포함하지 않는다.
- `results/`: 실행 결과. Git에서 제외하며 공유할 때 재현 설정과 버전을 함께 제공한다.

검색에서는 동일 질의·동일 스냅샷으로 BM25/Semantic/Hybrid를 비교한다. 관련성은 사람이 판정하고 검색 결과를 자동 정답으로 쓰지 않는다. 요약에서는 원문 읽기·근거 발췌·요약을 비교해 근거 일치, 조건 누락, 후속 논의, 미확인 표현을 확인한다.

평가할 때 질의셋 버전, 스냅샷 해시, 수집 범위·시각, 모델 버전, 검색 설정, 평가 지표와 사례 수를 기록한다. 최종 평가에서는 두 저장소에서 기능을 시연하고 검색 방식별 결과를 비교한다.

## 실행

저장소 루트의 PowerShell에서 실행한다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-search.txt

$snapshot = .\.venv\Scripts\python.exe -m backend.app.search --db data/database/search-smoke.sqlite3 import --input evaluation/datasets/search-smoke.json | ConvertFrom-Json

.\.venv\Scripts\python.exe -m evaluation.compare --db data/database/search-smoke.sqlite3 --repository example/issue-search-fixture --snapshot-id $snapshot.snapshot_id --queries evaluation/datasets/smoke-queries.json --top-k 3 --output evaluation/results/search-smoke-run1.json
```

첫 실행에서 모델을 `data/models/`에 내려받는다. 다른 모델은 `--model-id ID --model-revision 40자리_SHA`로 지정한다. 기본 모델과 캐시 설정은 [검색 모듈](../backend/app/search/README.md)을 참고한다.

출력 파일이 있으면 덮어쓰지 않는다. 재실행 시 `search-smoke-run2.json`처럼 새 이름을 사용한다. 결과에는 스냅샷·질의셋 해시, 모델·패키지 버전, 검색 설정, 평균 지표와 질의별 순위·점수가 포함된다.

## 질의와 지표

질의셋은 다음 형식으로 작성한다. `relevant_issues`는 해당 스냅샷에서 사람이 판정한 번호다.

```json
{
  "version": "team-judgments-v1",
  "provenance": "판정자와 판정일",
  "queries": [
    {
      "id": "database-lock",
      "problem": "관찰한 문제 설명",
      "error": "선택적 오류 메시지",
      "environment": "선택적 환경",
      "relevant_issues": [12, 34]
    }
  ]
}
```

K는 1~20이다. 중복 질의 ID, 빈 문제·정답 목록, 스냅샷에 없는 정답은 거절한다. 검색 중 스냅샷이 바뀌어도 비교를 중단한다.

- P@K: 상위 K개 중 관련 Issue 수 / 요청한 K. 결과가 적어도 분모는 K다.
- Recall@K: 상위 K개 중 관련 Issue 수 / 전체 관련 Issue 수.
- MRR@K: K개 안에서 처음 관련 Issue가 나온 순위의 역수를 질의별로 평균한다. 관련 결과가 없으면 0이다.

## 예제와 테스트

`search-smoke.json`은 직접 작성한 가상 Issue 8개이며 `example.invalid` URL은 실제 원문이 아니다. 수집 시각과 `partial_collection`도 예제 메타데이터다. `smoke-queries.json`의 질의 4개와 판정은 검색 전에 작성했다. 이 예제는 동작 점검용이며 실제 GitHub 저장소의 검색 품질을 나타내지 않는다. 실제 평가는 수집 스냅샷과 독립적인 사람 판정을 사용한다. 정답이 없는 무관 질의는 별도로 점검한다.

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_evaluation.py -q
```

테스트는 고정 순위로 지표·입력 검증을 확인한다. 실제 모델 실행 결과는 [저장·검색 안내](../docs/sqlite-search.md)에 정리한다.
