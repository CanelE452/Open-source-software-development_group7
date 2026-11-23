// frontend/src/features/issue-detail/IssueDetailSection.tsx
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
  const [detailError, setDetailError] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedIssue || !repository) return;

    let isCancelled = false;
    setDetail(null);
    setSummary(null);
    setDetailError(null);
    setSummaryError(null);

    const [owner, repo] = repository.split('/');
    if (!owner || !repo) {
      setDetailError(`유효하지 않은 저장소 경로입니다: "${repository}" (owner/repo 형식 필요)`);
      return;
    }

    // 1. Issue 상세 조회
    const fetchDetail = async () => {
      try {
        setIsDetailLoading(true);
        const res = await getIssueDetail(owner, repo, selectedIssue.number);
        if (!isCancelled) {
          setDetail(res);
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          setDetailError(
            err instanceof Error ? err.message : 'Issue 상세 내용을 불러오는 중 오류가 발생했습니다.'
          );
        }
      } finally {
        if (!isCancelled) {
          setIsDetailLoading(false);
        }
      }
    };

    // 2. Issue AI 요약 조회
    const fetchSummary = async () => {
      try {
        setIsSummaryLoading(true);
        const res = await getIssueSummary(owner, repo, selectedIssue.number);
        if (!isCancelled) {
          setSummary(res);
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          setSummaryError(
            err instanceof Error ? err.message : 'Issue AI 요약을 불러오는 중 오류가 발생했습니다.'
          );
        }
      } finally {
        if (!isCancelled) {
          setIsSummaryLoading(false);
        }
      }
    };

    fetchDetail();
    fetchSummary();

    return () => {
      isCancelled = true;
    };
  }, [selectedIssue, repository]);

  if (!selectedIssue) return null;

  return (
    <section style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <button
          onClick={onBack}
          style={{ padding: '6px 12px', cursor: 'pointer', backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '4px' }}
        >
          ← 검색 결과 목록으로 돌아가기
        </button>
        <span style={{ fontSize: '13px', color: '#64748b' }}>
          저장소: <code>{repository}</code> · <strong>#{selectedIssue.number}</strong>
        </span>
      </div>

      {/* 요약 오류 / 요약 서버 미연결(503) 안내 */}
      {summaryError && (
        <div
          role="alert"
          style={{
            padding: '12px 16px',
            marginBottom: '16px',
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: '8px',
            color: '#92400e',
            fontSize: '14px',
          }}
        >
          ⚠️ <strong>AI 요약 조회 불가:</strong> {summaryError}
          <div style={{ fontSize: '12px', marginTop: '4px', color: '#b45309' }}>
            아래 원문 본문과 댓글은 계속 확인할 수 있습니다.
          </div>
        </div>
      )}

      {/* AI 요약 대시보드 */}
      <SummaryDashboard summary={summary} isLoading={isSummaryLoading} />

      {/* 원문 상세 조회 오류 안내 */}
      {detailError ? (
        <div
          role="alert"
          style={{
            padding: '16px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#991b1b',
            fontSize: '14px',
          }}
        >
          ❌ <strong>Issue 상세 조회 오류:</strong> {detailError}
        </div>
      ) : (
        /* 원문 본문 및 댓글 */
        <IssueBodyAndComments detail={detail} isLoading={isDetailLoading} />
      )}
    </section>
  );
};