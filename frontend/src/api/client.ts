import type { HealthResponse } from '../types/api';

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch('/api/health', { signal });

  if (!response.ok) {
    throw new Error(`서버 상태 확인 실패 (${response.status})`);
  }

  return response.json() as Promise<HealthResponse>;
}
