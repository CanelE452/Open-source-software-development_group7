# GitHub Issue 요약 근거 검증 보고서

- 실행 시각: 2026-10-29T20:10:35+09:00
- Issue: [[Feature] GitHub Issue·댓글 수집 및 API 연결](https://github.com/CanelE452/Open-source-software-development_group7/issues/4)
- 요약 상태: `completed`
```json
{
  "problem": {
    "text": "공개 GitHub 저장소의 Issue와 댓글을 수집해 분석 진행 상태를 확인하고, 이를 API로 제공하는 기능을 구현하는 것이 목표입니다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/4",
        "excerpt": "사용자가 입력한 공개 GitHub 저장소의 Issue를 수집하고 분석 진행 상태를 확인할 수 있도록 한다.",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "conditions": {
    "text": "수집 단계에서는 공개 저장소 URL 검증, 페이지네이션, PR 제외, 본문·댓글 수집, 수집 범위·누락 여부 기록이 필요합니다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/4",
        "excerpt": "공개 저장소 URL 검증, 페이지네이션 및 PR 제외를 적용한 Issue 수집",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "solution": {
    "text": "API 및 모듈 동작을 연결하고 예외 처리를 포함한 핵심 기능을 완료했습니다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/4",
        "excerpt": "- [x] 공개 저장소 URL 검증, 페이지네이션 및 PR 제외를 적용한 Issue 수집\n- [x] 선택한 Issue의 본문·댓글·원문 링크 수집과 수집 범위·누락 여부 기록\n- [x] 분석·작업 상태 API 구현 및 수집·인덱싱 진행 상태 연결\n- [x] 검색·상세·요약 API를 각 담당 모듈과 연결 (연결점 정의, 미연결 시 503)\n- [x] 잘못된 입력, 호출 제한, 네트워크 실패, 부분 수집에 대한 예외 처리\n- [x] 토큰의 서버 환경변수 관리",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "discussion": {
    "text": "정상·예외 응답 테스트, 실제 저장소 동작 확인, 네트워크 장애 대비, 문서화 및 데이터 제외 검증을 수행했습니다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/4",
        "excerpt": "- [x] 정상·예외 응답 자동 테스트: python -m pytest -q → 38 passed\n- [x] 실제 공개 저장소 라이브 동작 확인: octocat/Hello-World 수집(Issue 10건, PR 15건 제외), huggingface/transformers #876 상세(본문 + 댓글 163건)\n- [x] 네트워크 실패가 기존 스냅샷을 손상시키지 않음 테스트\n- [x] 실행 방법 문서화 (README, docs/api-contract.md)",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "follow_up": {
    "text": "팀원 1명 이상 리뷰와 CI 통과 후 병합 작업이 남아 있습니다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/4",
        "excerpt": "- [ ] 팀원 1명 이상 리뷰 + CI 통과 후 병합 (PR feat/issue-collection에서 처리)",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "unknowns": {
    "text": null,
    "evidence": []
  },
  "status": "completed"
}
```

## 검증 결과

근거 불일치 또는 근거 누락 항목이 없습니다.