# Backend Tests

요약 결과의 구조와 원문 근거를 검증하기 위한 테스트 및 실행 스크립트를 관리한다.

## 요약 근거 검증

`test_summary_validation.py`를 실행하면 GitHub Issue 요약 결과에 포함된 근거가 실제 원문과 일치하는지 확인한다.

### 검증 항목

- 근거 URL이 수집된 Issue 또는 댓글 URL과 일치하는지 확인
- `source_type`이 실제 출처 유형과 일치하는지 확인
- 댓글 근거의 `comment_id`가 실제 댓글 ID와 일치하는지 확인
- 모델이 발췌한 문장이 원문에 존재하는지 확인
- 요약 텍스트가 있지만 근거가 없는 항목 확인

### 실행 방법

프로젝트 루트에서 실행한다.

```powershell
python .\backend\tests\test_summary_validation.py
```

실행하면 GitHub Issue URL을 입력받아 요약 생성 및 근거 검증을 수행한다.

### 검증 보고서

검증 결과는 `backend/tests/reports/`에 Markdown 파일로 저장된다.

파일명 형식:

```text
summary_validation_YYYYMMDD_HHMMSS.md
```

보고서에는 다음 내용이 포함된다.

- 검증 실행 시각 및 대상 Issue 정보
- LLM이 생성한 전체 요약 JSON
- 불일치가 발생한 요약 항목
- 불일치 유형 및 발생 사유
- 모델이 제시한 근거 URL과 발췌문
- 실제 원문의 내용과 출처 정보

검증 결과를 실행별로 보존하여 요약 근거의 문제를 확인하고 비교할 수 있다.

### 기존 검증 보고서

- [검증 보고서 1](reports/summary_validation_20261029_200702.md)
- [검증 보고서 2](reports/summary_validation_20261029_201035.md)
- [검증 보고서 3](reports/summary_validation_20261029_201434.md)