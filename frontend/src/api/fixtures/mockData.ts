// frontend/src/api/fixtures/mockData.ts
import {
  SearchIssuesResponse,
  IssueDetailResponse,
  IssueSummaryResponse,
} from '../../types/api';

// 1. Mock 검색 결과
export const mockSearchResponse: SearchIssuesResponse = {
  results: [
    {
      number: 47752,
      title: 'incorrect precedence of generation_config values in pipeline',
      html_url: 'https://github.com/huggingface/transformers/issues/47752',
      score: 0.892,
      score_type: 'hybrid',
      state: 'open',
    },
    {
      number: 41200,
      title: 'CUDA out of memory error during text generation with long context',
      html_url: 'https://github.com/huggingface/transformers/issues/41200',
      score: 0.745,
      score_type: 'hybrid',
      state: 'closed',
    },
  ],
  snapshot_id: 'snap-20261029-01',
  collected_at: '2026-10-29T12:00:00Z',
  partial_collection: false,
  scope: 'full',
};

// 2. Mock 이슈 상세 데이터
export const mockIssueDetailResponse: IssueDetailResponse = {
  number: 47752,
  title: 'incorrect precedence of generation_config values in pipeline',
  html_url: 'https://github.com/huggingface/transformers/issues/47752',
  state: 'open',
  body: 'When calling pipeline("text-generation"), setting max_new_tokens in generation_config gets overridden by default parameters.',
  author: 'dev-user',
  comments: [
    {
      id: 1001,
      html_url: 'https://github.com/huggingface/transformers/issues/47752#issuecomment-1001',
      body: 'Confirmed. Setting max_new_tokens inside generation_config is ignored if kwargs are passed.',
      author: 'maintainer-a',
      created_at: '2026-10-20T10:15:00Z',
    },
    {
      id: 1002,
      html_url: 'https://github.com/huggingface/transformers/issues/47752#issuecomment-1002',
      body: 'Workaround: Pass max_new_tokens directly as a keyword argument to pipeline() instead of inside generation_config.',
      author: 'contributor-b',
      created_at: '2026-10-21T14:20:00Z',
    },
  ],
  comment_count: 2,
  partial_collection: false,
};

// 3. Mock 이슈 AI 요약 데이터
export const mockIssueSummaryResponse: IssueSummaryResponse = {
  problem: {
    text: '파이프라인 호출 시 generation_config 내부의 생성 길이 설정이 기본 파라미터보다 낮은 우선순위를 가져 반영되지 않는 현상이 발생합니다.',
    evidence: [
      {
        url: 'https://github.com/huggingface/transformers/issues/47752',
        excerpt: 'setting max_new_tokens in generation_config gets overridden',
        source_type: 'issue_body',
      },
    ],
  },
  conditions: {
    text: 'text-generation 파이프라인에서 generation_config 객체와 일반 kwargs를 함께 전달할 때 발생합니다.',
    evidence: [
      {
        url: 'https://github.com/huggingface/transformers/issues/47752#issuecomment-1001',
        excerpt: 'inside generation_config is ignored if kwargs are passed',
        source_type: 'issue_comment',
        comment_id: 1001,
      },
    ],
  },
  solution: {
    text: 'generation_config 내부에 넣는 대신 pipeline() 호출 시 max_new_tokens를 직접 인자로 전달하여 회피할 수 있습니다.',
    evidence: [
      {
        url: 'https://github.com/huggingface/transformers/issues/47752#issuecomment-1002',
        excerpt: 'Pass max_new_tokens directly as a keyword argument to pipeline()',
        source_type: 'issue_comment',
        comment_id: 1002,
      },
    ],
  },
  discussion: {
    text: '메인테이너가 문제 원인을 파악했으며, 파라미터 병합 방식 수정 작업이 공유되었습니다.',
    evidence: [],
  },
  follow_up: {
    text: '다음 패치 버전 릴리스에서 관련 병합 우선순위 픽스 PR이 포함될 예정입니다.',
    evidence: [],
  },
  unknowns: {
    text: 'v4.x 이전 버전에서의 동일 작동 여부는 확인되지 않았습니다.',
    evidence: [],
  },
  status: 'completed',
  partial_collection: false,
};