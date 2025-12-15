import { getStoredToken } from './authService';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://iksan-ai-interview-backend-production.up.railway.app';

const authHeaders = () => {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export interface CreateStudentPayload {
  full_name: string;
  school_id?: string;
  school_name?: string;
  major_id?: string;
  major_name?: string;
  class_id?: string;
  class_name?: string;
  grade_level?: number;
}

export const createStudent = async (payload: CreateStudentPayload) => {
  const response = await fetch(`${API_BASE}/api/v1/students/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const msg = await response.text();
    throw new Error(msg || '학생을 추가할 수 없어요');
  }
  return response.json();
};

export interface BulkRowError {
  row: number;
  message: string;
  raw?: string | string[];
}

export interface BulkCreateResult {
  total: number;
  created: number;
  failed: number;
  errors?: BulkRowError[];
}

const parseBulkErrorMessage = (data: any, fallback: string) => {
  if (!data) return fallback;
  if (typeof data === 'string') return data;
  return data.message || data.error || data.detail || fallback;
};

export const bulkCreateStudents = async (file: File): Promise<BulkCreateResult> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE}/api/v1/student/bulk-create`, {
    method: 'POST',
    headers: {
      ...authHeaders(),
    },
    body: formData,
  });

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // ignore JSON parse error; fallback to text
  }

  if (!response.ok) {
    if (data) {
      throw new Error(parseBulkErrorMessage(data, 'CSV 업로드에 실패했어요'));
    }
    const msg = await response.text();
    throw new Error(msg || 'CSV 업로드에 실패했어요');
  }

  const total = data?.total ?? data?.total_count ?? data?.count ?? data?.summary?.total ?? 0;
  const created = data?.created ?? data?.created_count ?? data?.summary?.created ?? data?.data?.created ?? 0;
  const failed = data?.failed ?? data?.failed_count ?? data?.summary?.failed ?? Math.max((total || 0) - (created || 0), 0);

  const errorsSource = data?.errors || data?.errorRows || data?.error_rows || data?.failed_rows || [];
  const errors: BulkRowError[] = Array.isArray(errorsSource)
    ? errorsSource.map((err: any) => ({
        row: Number(err?.row ?? err?.line ?? err?.index ?? err?.lineNumber ?? 0),
        message: err?.message || err?.error || err?.detail || JSON.stringify(err),
        raw: err?.raw || err?.rowData || err?.data,
      }))
    : [];

  return {
    total: total || created + failed,
    created,
    failed,
    errors,
  };
};
