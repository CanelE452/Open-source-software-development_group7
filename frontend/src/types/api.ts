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

// 공통 수집 범위 객체 (docs/api-contract.md 기준)
export interface CollectionScope {
  state: string;
  per_page: number;
  max_issues: number;
  pages_fetched: number;
  issue_count: number;
  pull_requests_excluded: number;
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
  job_id?: string;
  repository?: string;
  state: 'queued' | 'collecting' | 'indexing' | 'completed' | 'partial' | 'failed';
  progress: {
    collected_issues: number;
    collected_comments: number;
    indexed: boolean; // [수정] number -> boolean
  };
  collection: {
    repository?: string;
    snapshot_id: string;
    collected_at: string;
    scope: CollectionScope; // [수정] string -> CollectionScope 객체
    partial_collection: boolean;
    notes: string[]; // [수정] string -> string[]
  } | null;
  error: {
    code: string;
    message: string;
  } | null;
  created_at?: string;
  updated_at?: string;
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
  repository?: string;
  method?: 'bm25' | 'semantic' | 'hybrid';
  results: SearchIssueItem[];
  snapshot_id: string;
  collected_at: string;
  partial_collection: boolean;
  scope: CollectionScope; // [수정] string -> CollectionScope 객체
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
  repository?: string;
  number: number;
  title: string;
  html_url: string;
  state: string;
  body: string;
  author: string;
  created_at?: string;
  updated_at?: string;
  comments: IssueComment[];
  comment_count: number;
  collected_at?: string;
  partial_collection: boolean;
  notes: string[]; // [수정] string -> string[]
}

// 6. 이슈 요약 (POST /api/repositories/{owner}/{repo}/issues/{number}/summary)
export interface EvidenceItem {
  url: string;
  excerpt: string;
  source_type: 'issue_body' | 'comment' | string;
  comment_id?: number;
}

export interface SummaryField {
  text: string | null; // [수정] string -> string | null
  evidence: EvidenceItem[];
}

export interface IssueSummaryResponse {
  repository?: string;
  number?: number;
  html_url?: string;
  problem: SummaryField;
  conditions: SummaryField;
  solution: SummaryField;
  discussion: SummaryField;
  follow_up: SummaryField;
  unknowns: SummaryField;
  status: 'completed' | 'insufficient_evidence' | 'failed';
  partial_collection: boolean;
}