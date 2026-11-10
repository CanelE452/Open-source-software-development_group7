"""저장소 분석 작업(수집·인덱싱) 요청·상태 형식."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.collection import CollectionMetadata
from backend.app.schemas.errors import ErrorDetail


class JobState(str, Enum):
    """작업 진행 상태."""

    queued = "queued"
    collecting = "collecting"
    indexing = "indexing"
    completed = "completed"
    partial = "partial"  # 수집은 끝났으나 일부가 누락됨
    failed = "failed"


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository: str = Field(
        min_length=1,
        description="공개 GitHub 저장소. `owner/repo` 또는 전체 URL",
    )
    max_issues: int | None = Field(
        default=None, ge=1, le=2000, description="수집 상한(미지정 시 서버 기본값)"
    )


class AnalyzeResponse(BaseModel):
    """분석 시작 응답. 작업 ID로 상태를 조회한다."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    repository: str
    state: JobState


class JobProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collected_issues: int = 0
    collected_comments: int = 0
    indexed: bool = False


class JobStatus(BaseModel):
    """작업 상태 조회 응답. 실패 시 `error`에 사유를 담는다."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    repository: str
    state: JobState
    progress: JobProgress
    collection: CollectionMetadata | None = None
    error: ErrorDetail | None = None
    created_at: str
    updated_at: str
