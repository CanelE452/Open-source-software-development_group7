import React, { useState } from 'react';
import { SearchIssuesRequest } from '../../types/api';

interface SearchFormProps {
  onAnalyzeRepo: (repository: string) => void;
  onSearch: (params: SearchIssuesRequest) => void;
  isAnalyzing: boolean;
  isSearching: boolean;
}

export const SearchForm: React.FC<SearchFormProps> = ({
  onAnalyzeRepo,
  onSearch,
  isAnalyzing,
  isSearching,
}) => {
  const [repository, setRepository] = useState('huggingface/transformers');
  const [problem, setProblem] = useState('');
  const [errorText, setErrorText] = useState('');
  const [environment, setEnvironment] = useState('');
  const [method, setMethod] = useState<'bm25' | 'semantic' | 'hybrid'>('hybrid');
  const [topK, setTopK] = useState<number>(5);

  const handleAnalyzeClick = () => {
    if (!repository.trim()) return alert('저장소 경로를 입력하세요.');
    onAnalyzeRepo(repository.trim());
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repository.trim()) return alert('저장소 경로를 입력하세요.');
    if (!problem.trim()) return alert('문제 설명을 입력하세요.');

    onSearch({
      repository: repository.trim(),
      problem: problem.trim(),
      error: errorText.trim() || undefined,
      environment: environment.trim() || undefined,
      method,
      top_k: topK,
    });
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px', marginBottom: '20px' }}>
      <h2>1. 저장소 수집 & Issue 검색</h2>
      
      {/* 저장소 분석 요청 */}
      <div style={{ marginBottom: '16px', display: 'flex', gap: '8px' }}>
        <input
          type="text"
          placeholder="GitHub 저장소 (예: owner/repo)"
          value={repository}
          onChange={(e) => setRepository(e.target.value)}
          style={{ flex: 1, padding: '8px' }}
        />
        <button onClick={handleAnalyzeClick} disabled={isAnalyzing} style={{ padding: '8px 16px' }}>
          {isAnalyzing ? '수집/인덱싱 중...' : '저장소 분석 시작'}
        </button>
      </div>

      <hr style={{ margin: '16px 0' }} />

      {/* 검색 입력 폼 */}
      <form onSubmit={handleSearchSubmit}>
        <div style={{ marginBottom: '12px' }}>
          <label style={{ display: 'block', fontWeight: 'bold' }}>문제 설명 (필수)</label>
          <textarea
            rows={3}
            placeholder="발생한 문제나 관찰된 상황을 입력하세요"
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
            style={{ width: '100%', padding: '8px' }}
            required
          />
        </div>

        <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block' }}>오류 메시지 (선택)</label>
            <input
              type="text"
              placeholder="Error log 등"
              value={errorText}
              onChange={(e) => setErrorText(e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block' }}>환경 정보 (선택)</label>
            <input
              type="text"
              placeholder="PyTorch 2.1, Ubuntu 등"
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <label style={{ marginRight: '8px' }}>검색 방식:</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value as 'bm25' | 'semantic' | 'hybrid')}
              style={{ padding: '6px' }}
            >
              <option value="hybrid">Hybrid (BM25 + Semantic)</option>
              <option value="bm25">BM25 (키워드)</option>
              <option value="semantic">Semantic (임베딩)</option>
            </select>
          </div>

          <div>
            <label style={{ marginRight: '8px' }}>결과 개수 (top_k):</label>
            <input
              type="number"
              min={1}
              max={20}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={{ width: '60px', padding: '6px' }}
            />
          </div>

          <button type="submit" disabled={isSearching} style={{ marginLeft: 'auto', padding: '8px 24px', fontWeight: 'bold' }}>
            {isSearching ? '검색 중...' : '관련 Issue 검색'}
          </button>
        </div>
      </form>
    </div>
  );
};