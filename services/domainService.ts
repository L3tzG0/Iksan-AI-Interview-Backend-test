import { API_BASE } from './apiBase';
import { getStoredToken } from './authService';

const authHeaders = () => {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const fetchDomains = async (search?: string): Promise<BackendDomain[]> => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  const response = await fetch(`${API_BASE}/api/v1/admin/domains?${params.toString()}`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch domains');
  }
  return response.json();
};

export const createDomain = async (data: { domain: string; organization_name: string }): Promise<BackendDomain> => {
  const response = await fetch(`${API_BASE}/api/v1/admin/domains`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create domain');
  }
  return response.json();
};

export const updateDomain = async (id: number, data: Partial<{ domain: string; organization_name: string; is_active: boolean }>): Promise<BackendDomain> => {
  const response = await fetch(`${API_BASE}/api/v1/admin/domains/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update domain');
  }
  return response.json();
};

export const deleteDomain = async (id: number): Promise<void> => {
  const response = await fetch(`${API_BASE}/api/v1/admin/domains/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to delete domain');
  }
};