// frontend/src/features/issue-detail/SummaryDashboard.tsx
import React from 'react';
import { IssueSummaryResponse, SummaryField, EvidenceItem } from '../../types/api';

interface SummaryDashboardProps {
  summary: IssueSummaryResponse | null;
  isLoading: boolean;
}

export const SummaryDashboard: React.FC<SummaryDashboardProps> = ({ summary, isLoading }) => {
  if (isLoading) {
    return (
      <div style={{ padding: '20px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '24px' }}>
        🤖 AI가 Issue 본문과 댓글을 분석하여 요약 중입니다...
      </div>
    );
  }

  if (!summary) return null;

  const formatSourceLabel = (ev: EvidenceItem) => {
    if (ev.source_type === 'issue_body') return '본문';
    if (ev.source_type === 'comment') {
      return ev.comment_id ? `댓글 #${ev.comment_id}` : '댓글';
    }
    return ev.source_type;
  };

  const renderSection = (title: string, icon: string, field: SummaryField) => {
    const hasText = Boolean(field?.text && field.text.trim().length > 0);
    const hasEvidence = Boolean(field?.evidence && field.evidence.length > 0);

    return (
      <div style={{ border: '1px solid #e2e8f0', borderRadius: '6px', padding: '12px 16px', backgroundColor: '#fff', marginBottom: '12px' }}>
        <h5 style={{ margin: '0 0 8px 0', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '6px', color: '#1e293b' }}>
          <span>{icon}</span> {title}
        </h5>

        {hasText ? (
          <p style={{ margin: '0 0 8px 0', fontSize: '14px', lineHeight: '1.5', color: '#334155' }}>
            {field.text}
          </p>
        ) : (
          <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8' }}>
            확인된 근거가 없습니다.
          </p>
        )}

        {/* 근거 링크(Evidence) 표시 */}
        {hasEvidence && (
          <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px dashed #cbd5e1', fontSize: '12px' }}>
            <span style={{ fontWeight: 'bold', color: '#64748b' }}>근거 위치:</span>
            <ul style={{ margin: '4px 0 0 0', paddingLeft: '18px', color: '#475569' }}>
              {field.evidence.map((ev: EvidenceItem, idx: number) => (
                <li key={idx} style={{ marginBottom: '2px' }}>
                  <span style={{ fontWeight: 600, color: '#334155', marginRight: '6px' }}>
                    [{formatSourceLabel(ev)}]
                  </span>
                  <a href={ev.url} target="_blank" rel="noreferrer" style={{ color: '#2563eb', textDecoration: 'underline' }}>
                    원문 발췌 ↗
                  </a>
                  {ev.excerpt && <span style={{ color: '#64748b' }}> — "{ev.excerpt}"</span>}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const sections: Array<{ title: string; icon: string; field: SummaryField }> = [
    { title: '문제 상황', icon: '📌', field: summary.problem },
    { title: '발생 조건', icon: '⚙️', field: summary.conditions },
    { title: '해결 방법', icon: '💡', field: summary.solution },
    { title: '논의 결과', icon: '💬', field: summary.discussion },
    { title: '후속 확인 사항', icon: '🔍', field: summary.follow_up },
    { title: '미확인 사항', icon: '❓', field: summary.unknowns },
  ];

  const hasAnyContent = sections.some(
    ({ field }) => Boolean(field?.text?.trim()) || Boolean(field?.evidence?.length)
  );

  return (
    <div style={{ backgroundColor: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ margin: 0, fontSize: '16px', color: '#0f172a' }}>✨ AI 근거 기반 요약 대시보드</h4>
        {summary.status === 'insufficient_evidence' && (
          <span style={{ backgroundColor: '#fef3c7', color: '#92400e', fontSize: '12px', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
            ⚠️ 근거 부족 (추측 지양 모드)
          </span>
        )}
        {summary.status === 'failed' && (
          <span style={{ backgroundColor: '#fee2e2', color: '#991b1b', fontSize: '12px', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
            ❌ 요약 실패
          </span>
        )}
      </div>

      {summary.status === 'failed' && (
        <div style={{ padding: '10px 12px', marginBottom: '12px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', fontSize: '13px', color: '#991b1b' }}>
          ⚠️ AI 요약 생성 중 오류가 발생했습니다. 아래 확보된 근거 또는 원문 본문과 댓글을 직접 확인해 주세요.
        </div>
      )}

      {summary.partial_collection && (
        <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#b45309' }}>
          * 부분 수집된 본문/댓글을 기준으로 생성된 요약입니다.
        </p>
      )}

      {summary.status === 'failed' && !hasAnyContent ? null : (
        sections.map(({ title, icon, field }) => (
          <React.Fragment key={title}>
            {renderSection(title, icon, field)}
          </React.Fragment>
        ))
      )}
    </div>
  );
};