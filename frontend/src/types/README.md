# API 타입

백엔드와 공유하는 입력·출력 타입은 이 폴더의 `api.ts`에 둡니다. API 변경 시 저장소 루트의 `docs/api-contract.md`와 타입을 함께 갱신하고 백엔드 담당자와 조율합니다.

현재 일부 타입(`scope`, `notes`, `progress.indexed`, 요약 항목의 `text`)은 `docs/api-contract.md`·백엔드 스키마와 형식이 다르므로 API를 연결할 때 맞춥니다.