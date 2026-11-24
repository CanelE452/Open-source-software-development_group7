# GitHub Issue 요약 근거 검증 보고서

- 실행 시각: 2026-11-23T13:04:20+09:00
- Issue: [[Feature] Issue 요약 기능 API 연결 및 근거 검증](https://github.com/CanelE452/Open-source-software-development_group7/issues/11)
- 요약 상태: `insufficient_evidence`
```json
{
  "problem": {
    "text": "Ollama 기반 Issue 요약 기능을 FastAPI의 요약 API에 연결해야 하며, 현재 `SummaryBackend`에는 실제 구현체가 연결되어 있지 않아 요약 API 요청 시 503 응답을 반환하고 있다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "그러나 FastAPI의 `SummaryBackend`에는 실제 구현체가 연결되어 있지 않아 요약 API 요청 시 503 응답을 반환한다.",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "conditions": {
    "text": "기존 요약 생성 기능과 근거 검증 로직을 재사용하여 사용자가 Issue 상세 화면에서 실제 요약 결과를 확인할 수 있도록 하며, `IssueDetailResponse`를 기존 요약 모듈의 `IssueInput` 형식으로 변환해야 한다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "기존 요약 생성 기능과 근거 검증 로직을 재사용하여 사용자가 Issue 상세 화면에서 실제 요약 결과를 확인할 수 있도록 한다.",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "solution": {
    "text": "기존 URL 입력 및 Issue 수집 과정과 요약 생성 과정을 분리하고, 전달받은 Issue 데이터로 요약할 수 있도록 수정하고, `SummaryBackend` 인터페이스에 맞는 요약 구현체를 작성하여 FastAPI의 요약 API에 연결해야 한다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "기존 URL 입력 및 Issue 수집 과정과 요약 생성 과정을 분리하고, 전달받은 Issue 데이터로 요약할 수 있도록 수정",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "SummaryBackend 인터페이스에 맞는 요약 구현체 작성",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "discussion": {
    "text": "기존 Ollama 기반 요약 생성 기능을 API에 연결하고, 요약 결과의 근거 URL, 발췌문 및 원문 일치 여부 검증, 근거 부족 및 요약 실패 상태 처리, Ollama 호출 실패 및 잘못된 JSON 응답 처리 등을 검증해야 한다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "요약 결과의 근거 URL, 발췌문 및 원문 일치 여부 검증",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "근거 부족 및 요약 실패 상태 처리",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "Ollama 호출 실패 및 잘못된 JSON 응답 처리",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "follow_up": {
    "text": "실제 공개 GitHub Issue를 이용한 요약 API 통합 확인 및 요약 API 실행 방법 및 검증 결과 문서화가 필요하다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "실제 공개 GitHub Issue를 이용한 요약 API 통합 확인",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "요약 API 실행 방법 및 검증 결과 문서화",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "unknowns": {
    "text": "요약 결과의 근거 URL, 발췌문 및 원문 일치 여부 검증, 근거 부족 및 요약 실패 상태 처리, Ollama 호출 실패 및 잘못된 JSON 응답 처리 등이 아직 검증되지 않았다.",
    "evidence": [
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "요약 결과의 근거 URL, 발췌문 및 원문 일치 여부 검증",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "근거 부족 및 요약 실패 상태 처리",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/CanelE452/Open-source-software-development_group7/issues/11",
        "excerpt": "Ollama 호출 실패 및 잘못된 JSON 응답 처리",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "status": "insufficient_evidence"
}
```

## 검증 결과

근거 불일치 또는 근거 누락 항목이 없습니다.