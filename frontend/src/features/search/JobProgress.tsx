import React from 'react';
import { JobStatusResponse } from '../../types/api';

interface JobProgressProps {
  jobStatus: JobStatusResponse | null;
}

export const JobProgress: React.FC<JobProgressProps> = ({ jobStatus }) => {
  if (!jobStatus) return null;

  const { state, progress, collection, error } = jobStatus;

  const getStateBadge = () => {
    switch (state) {
      case 'queued':
      case 'collecting':
      case 'indexing':
        return <span style={{ color: '#d97706', fontWeight: 'bold' }}>⏳ 분석 진행 중 ({state})</span>;
      case 'completed':
        return <span style={{ color: '#059669', fontWeight: 'bold' }}>✅ 수집/인덱싱 완료</span>;
      case 'partial':
        return <span style={{ color: '#2563eb', fontWeight: 'bold' }}>⚠️ 부분 수집 완료</span>;
      case 'failed':
        return <span style={{ color: '#dc2626', fontWeight: 'bold' }}>❌ 분석 실패</span>;
      default:
        return <span>{state}</span>;
    }
  };

  return (
    <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', padding: '12px 16px', borderRadius: '6px', marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <strong>저장소 분석 상태:</strong>
        {getStateBadge()}
      </div>

      <div style={{ fontSize: '14px', color: '#475569' }}>
        <span>수집된 Issue: {progress.collected_issues}개</span> |{' '}
        <span>수집된 댓글: {progress.collected_comments}개</span> |{' '}
        <span>인덱싱 완료: {progress.indexed}개</span>
      </div>

      {collection?.partial_collection && (
        <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#b45309' }}>
          💡 제한사항으로 인해 저장소의 일부 Issue만 수집되었습니다. ({collection.notes || '부분 수집 모드'})
        </p>
      )}

      {error && (
        <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#dc2626' }}>
          오류 발생: [{error.code}] {error.message}
        </p>
      )}
    </div>
  );
};