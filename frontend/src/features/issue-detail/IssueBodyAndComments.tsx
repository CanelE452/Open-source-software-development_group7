// frontend/src/features/issue-detail/IssueBodyAndComments.tsx
import React from 'react';
import { IssueDetailResponse } from '../../types/api';

interface IssueBodyAndCommentsProps {
  detail: IssueDetailResponse | null;
  isLoading: boolean;
}

export const IssueBodyAndComments: React.FC<IssueBodyAndCommentsProps> = ({ detail, isLoading }) => {
  if (isLoading) return <div style={{ padding: '12px' }}>상세 본문 및 댓글을 불러오는 중...</div>;
  if (!detail) return null;

  const hasNotes = Boolean(detail.notes && detail.notes.length > 0);
  const showPartialWarning = detail.partial_collection || hasNotes;

  return (
    <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', backgroundColor: '#fff' }}>
      <div style={{ marginBottom: '16px', borderBottom: '1px solid #f1f5f9', paddingBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', marginBottom: '8px' }}>
          <h3 style={{ margin: 0 }}>
            <span style={{ color: '#2563eb', marginRight: '6px' }}>#{detail.number}</span>
            {detail.title}
          </h3>
          <a
            href={detail.html_url}
            target="_blank"
            rel="noreferrer"
            style={{ fontSize: '13px', color: '#2563eb', textDecoration: 'underline', whiteSpace: 'nowrap' }}
          >
            GitHub 원문 ↗
          </a>
        </div>
        <div style={{ fontSize: '13px', color: '#64748b' }}>
          작성자: <strong>{detail.author}</strong> | 상태: <span>{detail.state}</span> | 댓글 {detail.comment_count}개
        </div>

        {showPartialWarning && (
          <div style={{ marginTop: '10px', padding: '8px 12px', backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: '6px', fontSize: '13px', color: '#b45309' }}>
            ⚠️ 일부 본문 또는 댓글만 수집되었습니다.
            {hasNotes && <span> ({detail.notes.join(', ')})</span>}
          </div>
        )}
      </div>

      {/* 본문 */}
      <div style={{ marginBottom: '24px' }}>
        <h5 style={{ margin: '0 0 8px 0', color: '#475569' }}>본문 내용</h5>
        <div style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px', fontSize: '14px', whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
          {detail.body || '(본문 내용이 없습니다)'}
        </div>
      </div>

      {/* 댓글 목록 */}
      <div>
        <h5 style={{ margin: '0 0 12px 0', color: '#475569' }}>댓글 목록 ({detail.comments.length})</h5>
        {detail.comments && detail.comments.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {detail.comments.map((comment) => (
              <div key={comment.id} id={`comment-${comment.id}`} style={{ border: '1px solid #f1f5f9', borderRadius: '6px', padding: '10px 12px', fontSize: '13px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', color: '#64748b' }}>
                  <strong>{comment.author}</strong>
                  <a
                    href={comment.html_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: '#64748b', textDecoration: 'underline' }}
                  >
                    {new Date(comment.created_at).toLocaleDateString()} ↗
                  </a>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>{comment.body}</div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8' }}>등록된 댓글이 없습니다.</p>
        )}
      </div>
    </div>
  );
};