export interface HealthResponse {
  status: 'ok';
  service: 'issue-finder';
}

// 1. 공통 에러 응답 타입
export interface ApiDomainError {
  error: {
    code:
      | 'invalid_repository'
      | 'not_found'
      | 'rate_limited'
      | 'upstream_unavailable'
      | 'search_unavailable'
      | 'summary_unavailable'
      | string;
    message: string;
    detail?: unknown;
  };
}

// 2. 수집 시작 (POST /api/repositories/analyze)
export interface AnalyzeRepoRequest {
  repository: string;
  max_issues?: number;
}

export interface AnalyzeRepoResponse {
  job_id: string;
  repository: string;
  state: 'queued' | 'collecting' | 'indexing' | 'completed' | 'partial' | 'failed';
}

// 3. 분석 진행 상태 (GET /api/repositories/jobs/{job_id})
export interface JobStatusResponse {
  state: 'queued' | 'collecting' | 'indexing' | 'completed' | 'partial' | 'failed';
  progress: {
    collected_issues: number;
    collected_comments: number;
    indexed: number;
  };
  collection: {
    snapshot_id: string;
    collected_at: string;
    scope: string;
    partial_collection: boolean;
    notes?: string;
  } | null;
  error: {
    code: string;
    message: string;
  } | null;
}

// 4. 이슈 검색 (POST /api/search)
export interface SearchIssuesRequest {
  repository: string;
  problem: string; // 필수
  error?: string;
  environment?: string;
  method: 'bm25' | 'semantic' | 'hybrid';
  top_k: number; // 1~20
}

export interface SearchIssueItem {
  number: number;
  title: string;
  html_url: string;
  score: number;
  score_type: string;
  state: string;
}

export interface SearchIssuesResponse {
  results: SearchIssueItem[];
  snapshot_id: string;
  collected_at: string;
  partial_collection: boolean;
  scope: string;
}

// 5. 이슈 상세 (GET /api/repositories/{owner}/{repo}/issues/{number})
export interface IssueComment {
  id: number;
  html_url: string;
  body: string;
  author: string;
  created_at: string;
}

export interface IssueDetailResponse {
  number: number;
  title: string;
  html_url: string;
  state: string;
  body: string;
  author: string;
  comments: IssueComment[];
  comment_count: number;
  partial_collection: boolean;
  notes?: string;
}

// 6. 이슈 요약 (POST /api/repositories/{owner}/{repo}/issues/{number}/summary)
export interface EvidenceItem {
  url: string;
  excerpt: string;
  source_type: string;
  comment_id?: number;
}

export interface SummaryField {
  text: string;
  evidence: EvidenceItem[];
}

export interface IssueSummaryResponse {
  problem: SummaryField;
  conditions: SummaryField;
  solution: SummaryField;
  discussion: SummaryField;
  follow_up: SummaryField;
  unknowns: SummaryField;
  status: 'completed' | 'insufficient_evidence' | 'failed';
  partial_collection: boolean;
}