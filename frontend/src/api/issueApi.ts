// frontend/src/api/issueApi.ts
import {
  ApiDomainError,
  AnalyzeRepoRequest,
  AnalyzeRepoResponse,
  JobStatusResponse,
  SearchIssuesRequest,
  SearchIssuesResponse,
  IssueDetailResponse,
  IssueSummaryResponse,
} from '../types/api';
import {
  mockSearchResponse,
  mockIssueDetailResponse,
  mockIssueSummaryResponse,
} from './fixtures/mockData';

const API_BASE = '/api';

// 명시적으로 VITE_USE_MOCK=true를 설정한 경우에만 Mock 데이터 반환 (기본값: 실제 API 모드)
const USE_MOCK =
  (import.meta as { env?: Record<string, string | undefined> }).env?.VITE_USE_MOCK === 'true';

function formatErrorMessage(status: number, errorData: unknown): string {
  const domainError = (errorData as Partial<ApiDomainError> | null)?.error;

  if (domainError?.code) {
    switch (domainError.code) {
      case 'search_unavailable':
        return `검색 모듈이 연결되지 않았습니다. (${domainError.message || '503 search_unavailable'})`;
      case 'summary_unavailable':
        return `요약 서버가 연결되지 않았습니다. (${domainError.message || '503 summary_unavailable'})`;
      case 'upstream_unavailable':
        return `GitHub API 또는 외부 서버에 연결할 수 없습니다. (${domainError.message || '503 upstream_unavailable'})`;
      default:
        return domainError.message
          ? `[${domainError.code}] ${domainError.message}`
          : `API 오류 발생 (${domainError.code})`;
    }
  }

  if (status === 503) {
    return '백엔드 기능 모듈이 아직 연결되지 않았습니다. (HTTP 503)';
  }

  // FastAPI 기본 422 검증 오류 등 detail 필드 처리
  const detail = (errorData as { detail?: unknown } | null)?.detail;
  if (typeof detail === 'string') {
    return detail;
  }

  return `HTTP 오류가 발생했습니다. (상태 코드: ${status})`;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(formatErrorMessage(response.status, errorData));
  }

  return response.json() as Promise<T>;
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(url, init);
  } catch {
    throw new Error(
      '백엔드 서버에 연결할 수 없습니다. 서버 실행 상태와 네트워크 연결을 확인해 주세요.'
    );
  }

  return handleResponse<T>(response);
}

// 1. POST /api/repositories/analyze (수집 시작)
export async function analyzeRepository(
  data: AnalyzeRepoRequest
): Promise<AnalyzeRepoResponse> {
  if (USE_MOCK) {
    return {
      job_id: 'mock-job-001',
      repository: data.repository,
      state: 'completed',
    };
  }

  return requestJson<AnalyzeRepoResponse>(`${API_BASE}/repositories/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

// 2. GET /api/repositories/jobs/{job_id} (분석 진행 상태)
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  if (USE_MOCK) {
    return {
      job_id: jobId,
      state: 'completed',
      progress: {
        collected_issues: 42,
        collected_comments: 128,
        indexed: true,
      },
      collection: {
        snapshot_id: mockSearchResponse.snapshot_id,
        collected_at: mockSearchResponse.collected_at,
        scope: mockSearchResponse.scope,
        partial_collection: false,
        notes: [],
      },
      error: null,
    };
  }

  return requestJson<JobStatusResponse>(`${API_BASE}/repositories/jobs/${jobId}`);
}

// 3. POST /api/search (검색)
export async function searchIssues(
  data: SearchIssuesRequest
): Promise<SearchIssuesResponse> {
  if (USE_MOCK) {
    return mockSearchResponse;
  }

  return requestJson<SearchIssuesResponse>(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

// 4. GET /api/repositories/{owner}/{repo}/issues/{number} (상세)
export async function getIssueDetail(
  owner: string,
  repo: string,
  number: number
): Promise<IssueDetailResponse> {
  if (USE_MOCK) {
    return mockIssueDetailResponse;
  }

  return requestJson<IssueDetailResponse>(
    `${API_BASE}/repositories/${owner}/${repo}/issues/${number}`
  );
}

// 5. POST /api/repositories/{owner}/{repo}/issues/{number}/summary (요약)
export async function getIssueSummary(
  owner: string,
  repo: string,
  number: number
): Promise<IssueSummaryResponse> {
  if (USE_MOCK) {
    return mockIssueSummaryResponse;
  }

  return requestJson<IssueSummaryResponse>(
    `${API_BASE}/repositories/${owner}/${repo}/issues/${number}/summary`,
    { method: 'POST' }
  );
}