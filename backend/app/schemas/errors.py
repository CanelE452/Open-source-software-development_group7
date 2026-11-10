"""공통 오류 응답 형식.

모든 예외 응답은 `{"error": {"code", "message", "detail"}}` 구조를 따른다.
프런트엔드는 `code`로 분기하고 `message`(한국어)를 사용자에게 보여준다.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(description="기계가 분기할 오류 코드")
    message: str = Field(description="사람이 읽는 한국어 설명")
    detail: dict | None = Field(default=None, description="추가 정보(선택)")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
