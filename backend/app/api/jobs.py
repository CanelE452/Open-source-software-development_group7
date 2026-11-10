"""분석 작업(수집·인덱싱) 상태 관리.

작업 상태는 메모리에 둔다. 영속 저장은 저장 담당(`storage/`)과 연결할 때 교체한다.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from threading import Lock

from backend.app.api.backends import BackendUnavailable, SearchBackend
from backend.app.api.errors import error_detail_for
from backend.app.collection.issues import collect_issues, utc_now_iso
from backend.app.collection.repository import parse_repository
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.github import GitHubClient
from backend.app.schemas.analysis import JobProgress, JobState, JobStatus

# 매 호출마다 새 GitHub 클라이언트를 만드는 팩토리. 테스트는 가짜 전송을 주입한다.
GitHubClientFactory = Callable[[], GitHubClient]


class JobStore:
    """작업 ID로 상태를 보관·조회한다(스레드 안전)."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobStatus] = {}
        self._lock = Lock()

    def create(self, repository: str) -> JobStatus:
        job_id = uuid.uuid4().hex
        now = utc_now_iso()
        job = JobStatus(
            job_id=job_id,
            repository=repository,
            state=JobState.queued,
            progress=JobProgress(),
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> JobStatus | None:
        with self._lock:
            return self._jobs.get(job_id)

    def save(self, job: JobStatus) -> None:
        job.updated_at = utc_now_iso()
        with self._lock:
            self._jobs[job.job_id] = job


def run_analysis(
    *,
    job_store: JobStore,
    job_id: str,
    client_factory: GitHubClientFactory,
    search_backend: SearchBackend,
    max_issues: int | None = None,
    settings: Settings | None = None,
) -> None:
    """수집하고, 검색 모듈이 있으면 색인한 뒤 작업 상태를 갱신한다.

    백그라운드에서 실행된다. 예외는 작업을 `failed`로 기록하고 삼킨다(요청은 이미 응답됨).
    """

    settings = settings or get_settings()
    job = job_store.get(job_id)
    if job is None:
        return

    client: GitHubClient | None = None
    try:
        owner, repo = parse_repository(job.repository)
        job.repository = f"{owner}/{repo}"
        job.state = JobState.collecting
        job_store.save(job)

        client = client_factory()
        result = collect_issues(
            client, owner, repo, settings=settings, max_issues=max_issues
        )
        job.collection = result.metadata
        job.progress.collected_issues = len(result.issues)

        # 검색 모듈이 연결돼 있으면 색인한다. 아니면 수집만 하고 넘어간다.
        if getattr(search_backend, "available", False):
            job.state = JobState.indexing
            job_store.save(job)
            try:
                search_backend.index(job.repository, result.issues, result.metadata)
                job.progress.indexed = True
            except BackendUnavailable as exc:
                job.collection.notes.append(f"색인을 건너뛰었습니다: {exc}")
        else:
            job.collection.notes.append(
                "검색 모듈 미연결로 색인을 건너뛰었습니다."
            )

        job.state = (
            JobState.partial if result.metadata.partial_collection else JobState.completed
        )
        job_store.save(job)
    except Exception as exc:  # noqa: BLE001 - 상태로 기록하고 요청과 분리한다.
        job.state = JobState.failed
        job.error = error_detail_for(exc)
        job_store.save(job)
    finally:
        if client is not None:
            client.close()
