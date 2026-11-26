// frontend/src/features/search/SearchForm.tsx
import React, { useState, useEffect } from 'react';
import { SearchIssuesRequest } from '../../types/api';

interface SearchFormProps {
  defaultRepository?: string;
  onAnalyzeRepo: (repository: string) => void;
  onSearch: (params: SearchIssuesRequest) => void;
  isAnalyzing: boolean;
  isSearching: boolean;
}

function clampTopK(value: number): number {
  if (!Number.isFinite(value)) return 5;
  return Math.min(20, Math.max(1, Math.floor(value)));
}

export const SearchForm: React.FC<SearchFormProps> = ({
  defaultRepository = 'huggingface/transformers',
  onAnalyzeRepo,
  onSearch,
  isAnalyzing,
  isSearching,
}) => {
  const [repository, setRepository] = useState(defaultRepository);
  const [problem, setProblem] = useState('');
  const [errorText, setErrorText] = useState('');
  const [environment, setEnvironment] = useState('');
  const [method, setMethod] = useState<'bm25' | 'semantic' | 'hybrid'>('hybrid');
  const [topK, setTopK] = useState<number>(5);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    setRepository(defaultRepository);
  }, [defaultRepository]);

  const handleAnalyzeClick = () => {
    const trimmedRepo = repository.trim();
    if (!trimmedRepo) {
      setValidationError('저장소 경로(예: owner/repo)를 입력하세요.');
      return;
    }
    setValidationError(null);
    onAnalyzeRepo(trimmedRepo);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedRepo = repository.trim();
    const trimmedProblem = problem.trim();

    if (!trimmedRepo) {
      setValidationError('저장소 경로(예: owner/repo)를 입력하세요.');
      return;
    }
    if (!trimmedProblem) {
      setValidationError('문제 설명을 입력하세요.');
      return;
    }

    const safeTopK = clampTopK(topK);
    setTopK(safeTopK);
    setValidationError(null);

    onSearch({
      repository: trimmedRepo,
      problem: trimmedProblem,
      error: errorText.trim() || undefined,
      environment: environment.trim() || undefined,
      method,
      top_k: safeTopK,
    });
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px', marginBottom: '20px' }}>
      <h2>1. 저장소 수집 & Issue 검색</h2>

      {validationError && (
        <div
          role="alert"
          style={{
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            color: '#92400e',
            padding: '8px 12px',
            borderRadius: '6px',
            marginBottom: '12px',
            fontSize: '13px',
          }}
        >
          ⚠️ {validationError}
        </div>
      )}

      {/* 저장소 분석 요청 */}
      <div style={{ marginBottom: '16px', display: 'flex', gap: '8px' }}>
        <input
          type="text"
          placeholder="GitHub 저장소 (예: owner/repo 또는 전체 URL)"
          value={repository}
          onChange={(e) => {
            setRepository(e.target.value);
            if (validationError) setValidationError(null);
          }}
          style={{ flex: 1, padding: '8px' }}
        />
        <button
          type="button"
          onClick={handleAnalyzeClick}
          disabled={isAnalyzing}
          style={{ padding: '8px 16px' }}
        >
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
            onChange={(e) => {
              setProblem(e.target.value);
              if (validationError) setValidationError(null);
            }}
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
              onBlur={() => setTopK(clampTopK(topK))}
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