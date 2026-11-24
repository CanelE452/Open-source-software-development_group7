# GitHub Issue 요약 근거 검증 보고서

- 실행 시각: 2026-10-29T20:14:34+09:00
- Issue: [security-guidance: NotebookEdit still bypasses immediate pattern checks — #5337 was closed as completed without a fix landing](https://github.com/anthropics/claude-plugins-official/issues/6718)
- 요약 상태: `completed`
```json
{
  "problem": {
    "text": "NotebookEdit 도구 호출 시 코드를 추출하지 않아 보안 패턴 검사가 수행되지 않아 악성 코드 실행 위험이 존재합니다.",
    "evidence": [
      {
        "url": "https://github.com/anthropics/claude-plugins-official/issues/6718",
        "excerpt": "NotebookEdit content bypasses the PostToolUse pattern checks",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/anthropics/claude-plugins-official/issues/6718",
        "excerpt": "the bypass still reproduces on current `main`",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "conditions": {
    "text": "extract_content_from_input 함수가 NotebookEdit에 대한 처리 없으므로 빈 문자열을 반환해 패턴 검사가 실행되지 않습니다.",
    "evidence": [
      {
        "url": "https://github.com/anthropics/claude-plugins-official/issues/6718",
        "excerpt": "extract_content_from_input has branches for `Write` / `Edit` / `MultiEdit` and nothing for `NotebookEdit`, so it returns `\"\"`.",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/anthropics/claude-plugins-official/issues/6718",
        "excerpt": ">>> extract_content_from_input(\"NotebookEdit\", { ... })\n''\n>>> check_patterns(\"/repo/analysis.ipynb\", \"\")\n[]",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "solution": {
    "text": "2.0.15 버전에서 NotebookEdit의 new_source를 읽어 패턴 검사를 수행하도록 수정되었으며, 제안된 패치는 extract_content_from_input에 NotebookEdit 분기문을 추가하는 것입니다.",
    "evidence": [
      {
        "url": "https://github.com/anthropics/claude-plugins-official/issues/6718",
        "excerpt": "Add a `NotebookEdit` branch to `extract_content_from_input`:\n\n```python\nelif tool_name == \"NotebookEdit\":\n    return tool_input.get(\"new_source\", \"\")\n```",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/anthropics/claude-plugins-official/issues/6718#issuecomment-6302878987",
        "excerpt": "This is fixed in security‑guidance 2.0.15.",
        "source_type": "comment",
        "comment_id": 6302878987
      }
    ]
  },
  "discussion": {
    "text": "NotebookEdit를 통해 삽입된 pickle.loads, os.system 등 악성 코드는 경고 없이 실행될 수 있어 보안상 큰 위험이 있습니다.",
    "evidence": [
      {
        "url": "https://github.com/anthropics/claude-plugins-official/issues/6718",
        "excerpt": "A cell edit that introduces `pickle.loads(...)`, `yaml.load(...)`, `os.system(...)`, etc. via the `NotebookEdit` tool produces no warning, no `pattern_hits` metric, and no pending-warning record",
        "source_type": "issue_body",
        "comment_id": null
      }
    ]
  },
  "follow_up": {
    "text": "버전 2.0.15 이상에서 재시도해보고 여전히 문제가 발생하면 다시 이슈를 열어 주세요.",
    "evidence": [
      {
        "url": "https://github.com/anthropics/claude-plugins-official/issues/6718#issuecomment-6302878987",
        "excerpt": "Please reopen with the plugin version if you still see it on 2.0.15 or later.",
        "source_type": "comment",
        "comment_id": 6302878987
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


## 불일치 1: `conditions`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
extract_content_from_input 함수가 NotebookEdit에 대한 처리 없으므로 빈 문자열을 반환해 패턴 검사가 실행되지 않습니다.
````

- 근거 순번: 1
- 모델이 제시한 URL: https://github.com/anthropics/claude-plugins-official/issues/6718
- 모델이 제시한 출처 유형: `issue_body`
- 모델이 제시한 댓글 ID: `None`

### 모델이 제시한 발췌문

````text
extract_content_from_input has branches for `Write` / `Edit` / `MultiEdit` and nothing for `NotebookEdit`, so it returns `""`.
````

- 실제 출처 유형: `issue_body`
- 실제 댓글 ID: `None`

### 해당 URL의 실제 원문

````text
#5337 reported that `NotebookEdit` content bypasses the PostToolUse pattern checks, and it was closed as `completed` on Sep 25 — but no fix ever landed. I can't find any commit touching `NotebookEdit` handling in `security_reminder_hook.py`, and the bypass still reproduces on current `main` (ea10b21, checked today).

## Repro on current main

The PostToolUse hook is registered for `NotebookEdit` ([hooks.json#L33](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/hooks.json#L33)), the handler dispatches it ([security_reminder_hook.py#L2612](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/security_reminder_hook.py#L2612)), and it even reads `notebook_path` from the tool input — but `extract_content_from_input` ([#L518-L529](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/security_reminder_hook.py#L518)) has branches for `Write` / `Edit` / `MultiEdit` and nothing for `NotebookEdit`, so it returns `""`.

Running the real module:

```python
new_source = (
    "import pickle\n"
    "data = pickle.loads(open('model.pkl','rb').read())\n"
    "import os\n"
    "os.system(f'convert {user_input}')"
)

>>> extract_content_from_input("NotebookEdit", {
...     "notebook_path": "/repo/analysis.ipynb",
...     "cell_id": "cell-1", "cell_type": "code", "edit_mode": "replace",
...     "new_source": new_source})
''
>>> check_patterns("/repo/analysis.ipynb", "")
[]
```

The identical code through `Edit` on a `.py` file fires both `pickle_deserialization` and `os_system_injection`; feeding the same `new_source` to `check_patterns` with the `.ipynb` path also fires both — so the only gap is content extraction, not the patterns or path gates. Note `patterns.py` deliberately includes `.ipynb` in `_PY_EXTS` for the pickle rules, so notebook coverage is clearly intended.

## Impact

A cell edit that introduces `pickle.loads(...)`, `yaml.load(...)`, `os
````
(원문이 길어 앞부분 2,000자만 기록했습니다.)

## 불일치 2: `conditions`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
extract_content_from_input 함수가 NotebookEdit에 대한 처리 없으므로 빈 문자열을 반환해 패턴 검사가 실행되지 않습니다.
````

- 근거 순번: 2
- 모델이 제시한 URL: https://github.com/anthropics/claude-plugins-official/issues/6718
- 모델이 제시한 출처 유형: `issue_body`
- 모델이 제시한 댓글 ID: `None`

### 모델이 제시한 발췌문

````text
>>> extract_content_from_input("NotebookEdit", { ... })
''
>>> check_patterns("/repo/analysis.ipynb", "")
[]
````

- 실제 출처 유형: `issue_body`
- 실제 댓글 ID: `None`

### 해당 URL의 실제 원문

````text
#5337 reported that `NotebookEdit` content bypasses the PostToolUse pattern checks, and it was closed as `completed` on Sep 25 — but no fix ever landed. I can't find any commit touching `NotebookEdit` handling in `security_reminder_hook.py`, and the bypass still reproduces on current `main` (ea10b21, checked today).

## Repro on current main

The PostToolUse hook is registered for `NotebookEdit` ([hooks.json#L33](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/hooks.json#L33)), the handler dispatches it ([security_reminder_hook.py#L2612](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/security_reminder_hook.py#L2612)), and it even reads `notebook_path` from the tool input — but `extract_content_from_input` ([#L518-L529](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/security_reminder_hook.py#L518)) has branches for `Write` / `Edit` / `MultiEdit` and nothing for `NotebookEdit`, so it returns `""`.

Running the real module:

```python
new_source = (
    "import pickle\n"
    "data = pickle.loads(open('model.pkl','rb').read())\n"
    "import os\n"
    "os.system(f'convert {user_input}')"
)

>>> extract_content_from_input("NotebookEdit", {
...     "notebook_path": "/repo/analysis.ipynb",
...     "cell_id": "cell-1", "cell_type": "code", "edit_mode": "replace",
...     "new_source": new_source})
''
>>> check_patterns("/repo/analysis.ipynb", "")
[]
```

The identical code through `Edit` on a `.py` file fires both `pickle_deserialization` and `os_system_injection`; feeding the same `new_source` to `check_patterns` with the `.ipynb` path also fires both — so the only gap is content extraction, not the patterns or path gates. Note `patterns.py` deliberately includes `.ipynb` in `_PY_EXTS` for the pickle rules, so notebook coverage is clearly intended.

## Impact

A cell edit that introduces `pickle.loads(...)`, `yaml.load(...)`, `os
````
(원문이 길어 앞부분 2,000자만 기록했습니다.)