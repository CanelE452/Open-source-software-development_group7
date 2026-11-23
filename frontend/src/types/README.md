# API 타입

백엔드와 공유하는 입력·출력 타입은 이 폴더의 `api.ts`에 둡니다. API 변경 시 저장소 루트의 `docs/api-contract.md`와 타입을 함께 갱신하고 백엔드 담당자와 조율합니다.

이 폴더의 타입 정의는 `docs/api-contract.md`의 백엔드 API 입·출력 스키마와 일치합니다. 경로나 응답 필드를 변경할 때는 `docs/api-contract.md`, `api.ts`, `fixtures/mockData.ts`를 함께 수정합니다.