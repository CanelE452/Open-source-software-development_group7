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
  onSelectIssue: (issue: SearchIssueItem) => void;
}

export const SearchSection: React.FC<SearchSectionProps> = ({ onSelectIssue }) => {
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [searchResponse, setSearchResponse] = useState<SearchIssuesResponse | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  // 저장소 분석 요청
  const handleAnalyzeRepo = async (repository: string) => {
    try {
      setIsAnalyzing(true);
      const res = await analyzeRepository({ repository });
      setJobId(res.job_id);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '분석 요청 중 오류가 발생했습니다.');
      setIsAnalyzing(false);
    }
  };

  // Job Status Polling (1.5초 간격)
  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId);
        setJobStatus(status);

        if (['completed', 'partial', 'failed'].includes(status.state)) {
          setIsAnalyzing(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Job Status Polling Error:', err);
        setIsAnalyzing(false);
        clearInterval(interval);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [jobId]);

  // 이슈 검색 요청
  const handleSearch = async (params: SearchIssuesRequest) => {
    try {
      setIsSearching(true);
      const res = await searchIssues(params);
      setSearchResponse(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '검색 중 오류가 발생했습니다.');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <section>
      <SearchForm
        onAnalyzeRepo={handleAnalyzeRepo}
        onSearch={handleSearch}
        isAnalyzing={isAnalyzing}
        isSearching={isSearching}
      />
      <JobProgress jobStatus={jobStatus} />
      <SearchResults searchResponse={searchResponse} onSelectIssue={onSelectIssue} />
    </section>
  );
};