import { API_BASE } from './apiBase';
import { getStoredToken } from './authService';
import type { SchoolsResponse } from '../types';

const authHeaders = () => {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const getSchools = async (params?: { q?: string; limit?: number; skip?: number }): Promise<SchoolsResponse> => {
  const searchParams = new URLSearchParams();
  if (params?.q) searchParams.append('q', params.q);
  if (params?.limit != null) searchParams.append('limit', String(params.limit));
  if (params?.skip != null) searchParams.append('skip', String(params.skip));

  const url = `${API_BASE}/api/v1/schools/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) {
    throw new Error('Failed to fetch schools');
  }
  return res.json();
};
