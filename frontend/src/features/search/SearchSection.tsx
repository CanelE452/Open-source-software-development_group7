// frontend/src/features/search/SearchSection.tsx
import React, { useState, useEffect } from 'react';
import { SearchForm } from './SearchForm';
import { JobProgress } from './JobProgress';
import { SearchResults } from './SearchResults';
import {
  SearchIssuesRequest,
  SearchIssuesResponse,
  JobStatusResponse,
  SearchIssueItem,
} from '../../types/api';
import { analyzeRepository, getJobStatus, searchIssues } from '../../api/issueApi';

interface SearchSectionProps {
  defaultRepository?: string;
  onRepositoryChange?: (repository: string) => void;
  onSelectIssue: (issue: SearchIssueItem, repository?: string) => void;
}

function normalizeRepoPath(input: string): string {
  const trimmed = input.trim().replace(/\/+$/, '');
  const match = trimmed.match(/github\.com\/([^/]+\/[^/]+)/i);
  return match ? match[1].replace(/\.git$/, '') : trimmed;
}

export const SearchSection: React.FC<SearchSectionProps> = ({
  defaultRepository = 'huggingface/transformers',
  onRepositoryChange,
  onSelectIssue,
}) => {
  const [activeRepository, setActiveRepository] = useState<string>(defaultRepository);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [searchResponse, setSearchResponse] = useState<SearchIssuesResponse | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Issue 번호 직접 조회용 상태
  const [directIssueInput, setDirectIssueInput] = useState<string>('');
  const [directIssueError, setDirectIssueError] = useState<string | null>(null);

  useEffect(() => {
    setActiveRepository(defaultRepository);
  }, [defaultRepository]);

  const syncRepository = (repo: string) => {
    setActiveRepository(repo);
    onRepositoryChange?.(repo);
  };

  // 저장소 분석 요청
  const handleAnalyzeRepo = async (repository: string) => {
    try {
      setIsAnalyzing(true);
      setAnalyzeError(null);
      setJobStatus(null);
      syncRepository(repository);

      const res = await analyzeRepository({ repository });
      setJobId(res.job_id);
      setJobStatus({
        job_id: res.job_id,
        repository: res.repository,
        state: res.state,
        progress: {
          collected_issues: 0,
          collected_comments: 0,
          indexed: false,
        },
        collection: null,
        error: null,
      });
    } catch (err: unknown) {
      setAnalyzeError(err instanceof Error ? err.message : '분석 요청 중 오류가 발생했습니다.');
      setIsAnalyzing(false);
    }
  };

  // Job Status Polling (1.5초 간격)
  useEffect(() => {
    if (!jobId) return;
    let isCancelled = false;

    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId);
        if (isCancelled) return;

        setJobStatus(status);

        if (['completed', 'partial', 'failed'].includes(status.state)) {
          setIsAnalyzing(false);
          clearInterval(interval);
        }
      } catch (err: unknown) {
        if (isCancelled) return;
        setAnalyzeError(
          err instanceof Error ? err.message : '분석 진행 상태를 조회하는 중 오류가 발생했습니다.'
        );
        setIsAnalyzing(false);
        clearInterval(interval);
      }
    }, 1500);

    return () => {
      isCancelled = true;
      clearInterval(interval);
    };
  }, [jobId]);

  // 이슈 검색 요청
  const handleSearch = async (params: SearchIssuesRequest) => {
    try {
      setIsSearching(true);
      setSearchError(null);
      setSearchResponse(null);
      syncRepository(params.repository);

      const res = await searchIssues(params);
      setSearchResponse(res);
    } catch (err: unknown) {
      setSearchError(err instanceof Error ? err.message : '검색 중 오류가 발생했습니다.');
    } finally {
      setIsSearching(false);
    }
  };

  // Issue 번호로 상세 & AI 요약 화면 바로 이동
  const handleDirectIssueSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const issueNumber = Number(directIssueInput.trim());

    if (!Number.isInteger(issueNumber) || issueNumber <= 0) {
      setDirectIssueError('1 이상의 올바른 Issue 번호를 입력하세요.');
      return;
    }

    const normalizedRepo = normalizeRepoPath(activeRepository);
    if (!normalizedRepo.includes('/')) {
      setDirectIssueError('상단에서 유효한 저장소(owner/repo)를 먼저 설정해 주세요.');
      return;
    }

    setDirectIssueError(null);
    const directItem: SearchIssueItem = {
      number: issueNumber,
      title: `Issue #${issueNumber}`,
      state: 'open',
      html_url: `https://github.com/${normalizedRepo}/issues/${issueNumber}`,
      score: 0,
      score_type: 'hybrid',
    };

    onSelectIssue(directItem, normalizedRepo);
  };

  return (
    <section>
      <SearchForm
        defaultRepository={activeRepository}
        onAnalyzeRepo={handleAnalyzeRepo}
        onSearch={handleSearch}
        isAnalyzing={isAnalyzing}
        isSearching={isSearching}
      />

      {analyzeError && (
        <div
          role="alert"
          style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#991b1b',
            padding: '12px 16px',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '14px',
          }}
        >
          ❌ <strong>저장소 분석 오류:</strong> {analyzeError}
        </div>
      )}

      <JobProgress jobStatus={jobStatus} />

      {/* Issue 번호로 직접 상세 & AI 요약 조회 */}
      <div
        style={{
          border: '1px solid #e2e8f0',
          backgroundColor: '#f8fafc',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '20px',
        }}
      >
        <form
          onSubmit={handleDirectIssueSubmit}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}
        >
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#1e293b' }}>
            Issue 번호로 바로 보기
          </span>
          <span style={{ fontSize: '12px', color: '#64748b' }}>
            (대상: <code>{normalizeRepoPath(activeRepository)}</code>)
          </span>
          <input
            type="number"
            min={1}
            placeholder="예: 1"
            value={directIssueInput}
            onChange={(e) => {
              setDirectIssueInput(e.target.value);
              if (directIssueError) setDirectIssueError(null);
            }}
            style={{ width: '110px', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1' }}
          />
          <button
            type="submit"
            style={{
              padding: '6px 14px',
              backgroundColor: '#0f172a',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            상세 & AI 요약 조회
          </button>
        </form>
        {directIssueError && (
          <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#b91c1c' }}>
            ⚠️ {directIssueError}
          </p>
        )}
      </div>

      {searchError && (
        <div
          role="alert"
          style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#991b1b',
            padding: '12px 16px',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '14px',
          }}
        >
          ❌ <strong>검색 오류:</strong> {searchError}
        </div>
      )}

      {isSearching ? (
        <div
          style={{
            padding: '24px',
            textAlign: 'center',
            color: '#475569',
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '6px',
          }}
        >
          🔍 관련 Issue를 검색 중입니다...
        </div>
      ) : (
        <SearchResults
          searchResponse={searchResponse}
          onSelectIssue={(issue) => onSelectIssue(issue, activeRepository)}
        />
      )}
    </section>
  );
};