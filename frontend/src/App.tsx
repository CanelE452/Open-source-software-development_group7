// frontend/src/App.tsx
import { useState } from 'react';
import { SearchSection } from './features/search/SearchSection';
import { IssueDetailSection } from './features/issue-detail/IssueDetailSection';
import { SearchIssueItem } from './types/api';

function extractOwnerRepo(input: string): string {
  const trimmed = input.trim().replace(/\/+$/, '');
  const match = trimmed.match(/github\.com\/([^/]+\/[^/]+)/i);
  return match ? match[1].replace(/\.git$/, '') : trimmed;
}

export default function App() {
  const [selectedIssue, setSelectedIssue] = useState<SearchIssueItem | null>(null);
  const [currentRepository, setCurrentRepository] = useState<string>('huggingface/transformers');

  const handleRepositoryChange = (repo: string) => {
    const normalized = extractOwnerRepo(repo);
    if (normalized) {
      setCurrentRepository(normalized);
    }
  };

  const handleSelectIssue = (issue: SearchIssueItem, repository?: string) => {
    if (repository) {
      handleRepositoryChange(repository);
    }
    setSelectedIssue(issue);
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '24px', fontFamily: 'sans-serif' }}>
      <header style={{ marginBottom: '32px', borderBottom: '2px solid #0f172a', paddingBottom: '16px' }}>
        <h1 style={{ margin: 0, color: '#0f172a' }}>🔍 Issue Finder</h1>
        <p style={{ margin: '8px 0 0 0', color: '#64748b' }}>
          GitHub 오픈소스 관련 Issue 검색 및 근거 기반 AI 요약 대시보드
        </p>
      </header>

      <main>
        {!selectedIssue ? (
          <SearchSection
            defaultRepository={currentRepository}
            onRepositoryChange={handleRepositoryChange}
            onSelectIssue={handleSelectIssue}
          />
        ) : (
          <IssueDetailSection
            selectedIssue={selectedIssue}
            repository={currentRepository}
            onBack={() => setSelectedIssue(null)}
          />
        )}
      </main>
    </div>
  );
}