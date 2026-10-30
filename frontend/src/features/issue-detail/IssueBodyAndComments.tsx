import React from 'react';
import { IssueDetailResponse } from '../../types/api';

interface IssueBodyAndCommentsProps {
  detail: IssueDetailResponse | null;
  isLoading: boolean;
}

export const IssueBodyAndComments: React.FC<IssueBodyAndCommentsProps> = ({ detail, isLoading }) => {
  if (isLoading) return <div style={{ padding: '12px' }}>상세 본문 및 댓글을 불러오는 중...</div>;
  if (!detail) return null;

  return (
    <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', backgroundColor: '#fff' }}>
      <div style={{ marginBottom: '16px', borderBottom: '1px solid #f1f5f9', paddingBottom: '12px' }}>
        <h3 style={{ margin: '0 0 8px 0' }}>{detail.title}</h3>
        <div style={{ fontSize: '13px', color: '#64748b' }}>
          작성자: <strong>{detail.author}</strong> | 상태: <span>{detail.state}</span> | 댓글 {detail.comment_count}개
        </div>
      </div>

      {/* 본문 */}
      <div style={{ marginBottom: '24px' }}>
        <h5 style={{ margin: '0 0 8px 0', color: '#475569' }}>본문 내용</h5>
        <div style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px', fontSize: '14px', whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
          {detail.body || '(본문 내용이 없습니다)'}
        </div>
      </div>

      {/* 댓글 목록 */}
      {detail.comments && detail.comments.length > 0 && (
        <div>
          <h5 style={{ margin: '0 0 12px 0', color: '#475569' }}>댓글 목록 ({detail.comments.length})</h5>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {detail.comments.map((comment) => (
              <div key={comment.id} id={`comment-${comment.id}`} style={{ border: '1px solid #f1f5f9', borderRadius: '6px', padding: '10px 12px', fontSize: '13px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', color: '#64748b' }}>
                  <strong>{comment.author}</strong>
                  <span>{new Date(comment.created_at).toLocaleDateString()}</span>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>{comment.body}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};