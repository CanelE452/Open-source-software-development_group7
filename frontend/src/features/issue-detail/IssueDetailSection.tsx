import React, { useState, useEffect } from 'react';
import { SummaryDashboard } from './SummaryDashboard';
import { IssueBodyAndComments } from './IssueBodyAndComments';
import { SearchIssueItem, IssueDetailResponse, IssueSummaryResponse } from '../../types/api';
import { getIssueDetail, getIssueSummary } from '../../api/issueApi';

interface IssueDetailSectionProps {
  selectedIssue: SearchIssueItem | null;
  repository: string;
  onBack: () => void;
}

export const IssueDetailSection: React.FC<IssueDetailSectionProps> = ({
  selectedIssue,
  repository,
  onBack,
}) => {
  const [detail, setDetail] = useState<IssueDetailResponse | null>(null);
  const [summary, setSummary] = useState<IssueSummaryResponse | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);

  useEffect(() => {
    if (!selectedIssue || !repository) return;

    const [owner, repo] = repository.split('/');
    if (!owner || !repo) return;

    // 1. Issue 상세 조회
    const fetchDetail = async () => {
      try {
        setIsDetailLoading(true);
        const res = await getIssueDetail(owner, repo, selectedIssue.number);
        setDetail(res);
      } catch (err) {
        console.error('Issue 상세 조회 오류:', err);
      } finally {
        setIsDetailLoading(false);
      }
    };

    // 2. Issue AI 요약 조회
    const fetchSummary = async () => {
      try {
        setIsSummaryLoading(true);
        const res = await getIssueSummary(owner, repo, selectedIssue.number);
        setSummary(res);
      } catch (err) {
        console.error('Issue 요약 조회 오류:', err);
      } finally {
        setIsSummaryLoading(false);
      }
    };

    fetchDetail();
    fetchSummary();
  }, [selectedIssue, repository]);

  if (!selectedIssue) return null;

  return (
    <section style={{ marginTop: '24px' }}>
      <button
        onClick={onBack}
        style={{ marginBottom: '16px', padding: '6px 12px', cursor: 'pointer', backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '4px' }}
      >
        ← 검색 결과 목록으로 돌아가기
      </button>

      {/* AI 요약 대시보드 */}
      <SummaryDashboard summary={summary} isLoading={isSummaryLoading} />

      {/* 원문 본문 및 댓글 */}
      <IssueBodyAndComments detail={detail} isLoading={isDetailLoading} />
    </section>
  );
};