import React from 'react';
import { SearchIssuesResponse, SearchIssueItem } from '../../types/api';

interface SearchResultsProps {
  searchResponse: SearchIssuesResponse | null;
  onSelectIssue: (issue: SearchIssueItem) => void;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  searchResponse,
  onSelectIssue,
}) => {
  if (!searchResponse) return null;

  if (searchResponse.results.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
        검색 조건과 일치하는 관련 Issue를 찾지 못했습니다.
      </div>
    );
  }

  return (
    <div>
      <h3>2. 검색 결과 ({searchResponse.results.length}건)</h3>
      {searchResponse.partial_collection && (
        <span style={{ fontSize: '12px', color: '#b45309', display: 'block', marginBottom: '12px' }}>
          * 부분 수집된 스냅샷 기준 검색 결과입니다.
        </span>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {searchResponse.results.map((item) => (
          <div
            key={item.number}
            style={{
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              padding: '12px 16px',
              backgroundColor: '#fff',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontWeight: 'bold', color: '#2563eb' }}>#{item.number}</span>
              <span style={{ fontSize: '12px', backgroundColor: '#f1f5f9', padding: '2px 8px', borderRadius: '4px' }}>
                점수: {item.score.toFixed(3)} ({item.score_type})
              </span>
            </div>

            <h4 style={{ margin: '8px 0' }}>{item.title}</h4>

            <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
              <button
                onClick={() => onSelectIssue(item)}
                style={{ padding: '6px 12px', backgroundColor: '#0f172a', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
              >
                상세 & AI 요약 보기
              </button>
              <a
                href={item.html_url}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: '14px', color: '#64748b', textDecoration: 'underline', alignSelf: 'center' }}
              >
                GitHub 원문 ↗
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};