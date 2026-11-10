import React from 'react';
import { IssueSummaryResponse, SummaryField, EvidenceItem } from '../../types/api';

interface SummaryDashboardProps {
  summary: IssueSummaryResponse | null;
  isLoading: boolean;
}

export const SummaryDashboard: React.FC<SummaryDashboardProps> = ({ summary, isLoading }) => {
  if (isLoading) {
    return (
      <div style={{ padding: '20px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        🤖 AI가 Issue 본문과 댓글을 분석하여 요약 중입니다...
      </div>
    );
  }

  if (!summary) return null;

  // 요약 실패 및 근거 부족 상태 처리
  if (summary.status === 'failed') {
    return (
      <div style={{ padding: '16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b' }}>
        ⚠️ AI 요약 생성에 실패했습니다. (원문 본문과 댓글을 직접 확인해 주세요)
      </div>
    );
  }

  const renderSection = (title: string, icon: string, field: SummaryField) => {
    if (!field || !field.text) return null;

    return (
      <div style={{ border: '1px solid #e2e8f0', borderRadius: '6px', padding: '12px 16px', backgroundColor: '#fff', marginBottom: '12px' }}>
        <h5 style={{ margin: '0 0 8px 0', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '6px', color: '#1e293b' }}>
          <span>{icon}</span> {title}
        </h5>
        <p style={{ margin: '0 0 8px 0', fontSize: '14px', lineHeight: '1.5', color: '#334155' }}>{field.text}</p>
        
        {/* 근거 링크(Evidence) 표시 */}
        {field.evidence && field.evidence.length > 0 && (
          <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px dashed #cbd5e1', fontSize: '12px' }}>
            <span style={{ fontWeight: 'bold', color: '#64748b' }}>근거 위치:</span>
            <ul style={{ margin: '4px 0 0 0', paddingLeft: '18px', color: '#475569' }}>
              {field.evidence.map((ev: EvidenceItem, idx: number) => (
                <li key={idx}>
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

  return (
    <div style={{ backgroundColor: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4 style={{ margin: 0, fontSize: '16px', color: '#0f172a' }}>✨ AI 근거 기반 요약 대시보드</h4>
        {summary.status === 'insufficient_evidence' && (
          <span style={{ backgroundColor: '#fef3c7', color: '#92400e', fontSize: '12px', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
            ⚠️ 근거 부족 (추측 지양 모드)
          </span>
        )}
      </div>

      {renderSection('문제 상황', '📌', summary.problem)}
      {renderSection('발생 조건', '⚙️', summary.conditions)}
      {renderSection('해결 방법', '💡', summary.solution)}
      {renderSection('논의 결과', '💬', summary.discussion)}
      {renderSection('후속 확인 사항', '🔍', summary.follow_up)}
      {renderSection('미확인 사항', '❓', summary.unknowns)}
    </div>
  );
};