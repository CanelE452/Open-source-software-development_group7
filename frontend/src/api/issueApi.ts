// frontend/src/api/issueApi.ts
import {
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

// 공통 응답 처리 함수
async function handleResponse<T>(response: Response, fallbackMock?: T): Promise<T> {
  if (response.status === 503 && fallbackMock) {
    console.warn(`[API 503 Fallback] Mock 데이터를 사용합니다: ${response.url}`);
    return fallbackMock;
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.error?.message || `HTTP 에러 발생: ${response.status}`
    );
  }

  return response.json();
}

// 1. POST /api/repositories/analyze (수집 시작)
export async function analyzeRepository(
  data: AnalyzeRepoRequest
): Promise<AnalyzeRepoResponse> {
  const response = await fetch(`${API_BASE}/repositories/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<AnalyzeRepoResponse>(response);
}

// 2. GET /api/repositories/jobs/{job_id} (분석 진행 상태)
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/repositories/jobs/${jobId}`);
  return handleResponse<JobStatusResponse>(response);
}

// 3. POST /api/search (검색) — 503 시 Mock Fallback
export async function searchIssues(
  data: SearchIssuesRequest
): Promise<SearchIssuesResponse> {
  try {
    const response = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return await handleResponse<SearchIssuesResponse>(response, mockSearchResponse);
  } catch {
    console.warn('[API Fetch Error] Mock 검색 데이터를 반환합니다.');
    return mockSearchResponse;
  }
}

// 4. GET /api/repositories/{owner}/{repo}/issues/{number} (상세)
export async function getIssueDetail(
  owner: string,
  repo: string,
  number: number
): Promise<IssueDetailResponse> {
  try {
    const response = await fetch(
      `${API_BASE}/repositories/${owner}/${repo}/issues/${number}`
    );
    return await handleResponse<IssueDetailResponse>(response, mockIssueDetailResponse);
  } catch {
    return mockIssueDetailResponse;
  }
}

// 5. POST /api/repositories/{owner}/{repo}/issues/{number}/summary (요약) — 503 시 Mock Fallback
export async function getIssueSummary(
  owner: string,
  repo: string,
  number: number
): Promise<IssueSummaryResponse> {
  try {
    const response = await fetch(
      `${API_BASE}/repositories/${owner}/${repo}/issues/${number}/summary`,
      { method: 'POST' }
    );
    return await handleResponse<IssueSummaryResponse>(response, mockIssueSummaryResponse);
  } catch {
    console.warn('[API Fetch Error] Mock 요약 데이터를 반환합니다.');
    return mockIssueSummaryResponse;
  }
}