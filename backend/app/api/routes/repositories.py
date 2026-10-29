"""저장소 분석·작업 상태·Issue 상세·요약 API."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend.app.api.backends import SearchBackend, SummaryBackend
from backend.app.api.dependencies import (
    get_client_factory,
    get_job_store,
    get_search_backend,
    get_settings_dep,
    get_summary_backend,
)
from backend.app.api.jobs import GitHubClientFactory, JobStore, run_analysis
from backend.app.collection.issue_detail import collect_issue_detail
from backend.app.collection.repository import parse_repository
from backend.app.core.config import Settings
from backend.app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, JobStatus
from backend.app.schemas.issues import IssueDetailResponse
from backend.app.schemas.summary import SummaryRequest, SummaryResponse

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/analyze", response_model=AnalyzeResponse, status_code=202)
def analyze_repository(
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    job_store: JobStore = Depends(get_job_store),
    client_factory: GitHubClientFactory = Depends(get_client_factory),
    search_backend: SearchBackend = Depends(get_search_backend),
    settings: Settings = Depends(get_settings_dep),
) -> AnalyzeResponse:
    """수집·인덱싱을 시작하고 작업 ID를 돌려준다. 입력이 잘못되면 즉시 400."""

    owner, repo = parse_repository(payload.repository)  # 잘못된 입력은 400으로 변환됨
    job = job_store.create(f"{owner}/{repo}")
    background_tasks.add_task(
        run_analysis,
        job_store=job_store,
        job_id=job.job_id,
        client_factory=client_factory,
        search_backend=search_backend,
        max_issues=payload.max_issues,
        settings=settings,
    )
    return AnalyzeResponse(
        job_id=job.job_id, repository=job.repository, state=job.state
    )


@router.get("/jobs/{job_id}", response_model=JobStatus)
def get_job(
    job_id: str, job_store: JobStore = Depends(get_job_store)
) -> JobStatus:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return job


@router.get(
    "/{owner}/{repo}/issues/{number}", response_model=IssueDetailResponse
)
def get_issue_detail(
    owner: str,
    repo: str,
    number: int,
    client_factory: GitHubClientFactory = Depends(get_client_factory),
    settings: Settings = Depends(get_settings_dep),
) -> IssueDetailResponse:
    """선택한 Issue의 본문·댓글·원문 링크를 조회한다."""

    owner, repo = parse_repository(f"{owner}/{repo}")
    client = client_factory()
    try:
        return collect_issue_detail(client, owner, repo, number, settings=settings)
    finally:
        client.close()


@router.post(
    "/{owner}/{repo}/issues/{number}/summary", response_model=SummaryResponse
)
def summarize_issue(
    owner: str,
    repo: str,
    number: int,
    payload: SummaryRequest | None = None,
    client_factory: GitHubClientFactory = Depends(get_client_factory),
    summary_backend: SummaryBackend = Depends(get_summary_backend),
    settings: Settings = Depends(get_settings_dep),
) -> SummaryResponse:
    """수집한 원문으로 구조화 요약을 요청한다. 요약 모듈 미연결 시 503."""

    owner, repo = parse_repository(f"{owner}/{repo}")
    client = client_factory()
    try:
        detail = collect_issue_detail(client, owner, repo, number, settings=settings)
    finally:
        client.close()
    # 요약 생성은 요약 담당 모듈이 수행한다(미연결 시 BackendUnavailable → 503).
    return summary_backend.summarize(detail)
