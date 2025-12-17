const API_BASE = import.meta.env.VITE_API_BASE || 'https://iksan-ai-interview-backend-production.up.railway.app';

export interface RedisStatusResponse {
  status: string;
  ping?: string;
  set?: string;
  get?: string;
  [key: string]: any;
}

export const fetchRedisStatus = async (): Promise<RedisStatusResponse> => {
  const response = await fetch(`${API_BASE}/api/v1/redis/redis/status`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // ignore parse errors
  }

  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.message || data?.error;
    throw new Error(msg || 'Redis 상태 확인에 실패했습니다.');
  }

  return data as RedisStatusResponse;
};
