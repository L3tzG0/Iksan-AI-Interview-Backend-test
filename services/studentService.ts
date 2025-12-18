import { getStoredToken } from './authService';
import type { School, Major, User, ClassRoom } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://iksan-ai-interview-backend-production.up.railway.app';

const authHeaders = () => {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export interface CreateStudentPayload {
  full_name: string;
  school_name?: string;
  major_name?: string;
  class_id?: string;
  class_name?: string;
  grade_level?: number;
}

export interface CreatedStudentAccount {
  id?: string;
  userId?: string;
  fullName?: string;
  studentId: string;
  password?: string;
  currentClassId?: string;
  raw?: any;
}

export const createStudent = async (payload: CreateStudentPayload): Promise<CreatedStudentAccount> => {
  const response = await fetch(`${API_BASE}/api/v1/students/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(payload),
  });

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // ignore parse errors; handled below
  }

  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.message || data?.error || data?.detail;
    throw new Error(msg || '학생을 추가할 수 없어요');
  }

  const studentId = data?.student_id ?? data?.studentId;
  if (!studentId) {
    throw new Error('생성된 학생 ID가 응답에 없습니다.');
  }

  const password = data?.password ?? data?.temp_password ?? data?.tempPassword;
  const fullName = data?.full_name ?? data?.fullName;
  const userId = data?.user_id ?? data?.userId;
  const id = data?.id ?? userId;
  const currentClassId = data?.current_class_id ?? data?.currentClassId;

  return {
    id: id !== undefined ? String(id) : undefined,
    userId: userId !== undefined ? String(userId) : undefined,
    fullName,
    studentId: String(studentId),
    password,
    currentClassId: currentClassId !== undefined ? String(currentClassId) : undefined,
    raw: data,
  };
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

export type BulkCreateStudentInput = CreateStudentPayload;

export const bulkCreateStudents = async (students: BulkCreateStudentInput[]): Promise<BulkCreateResult> => {
  const response = await fetch(`${API_BASE}/api/v1/students/bulk-create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ students }),
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

export interface StudentSessionResponse {
  id: string;
  started_at?: string;
  startedAt?: string;
  completed_at?: string;
  completedAt?: string;
  total_score?: number;
  totalScore?: number;
  status?: string;
  intent?: string;
  student_id?: string;
  studentId?: string;
}

export const fetchStudentSessions = async () => {
  const response = await fetch(`${API_BASE}/api/v1/sessions/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
  });

  let data: StudentSessionResponse[] = [];
  try {
    data = await response.json();
  } catch {
    // keep data empty
  }

  if (!response.ok) {
    const msg = typeof data === 'string' ? data : (data as any)?.message || (data as any)?.error;
    throw new Error(msg || '학생 세션 내역을 불러오지 못했습니다.');
  }

  return Array.isArray(data) ? data : [];
};

export const fetchAllSessions = async () => {
  const response = await fetch(`${API_BASE}/api/v1/sessions/all`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
  });

  let data: StudentSessionResponse[] = [];
  try {
    data = await response.json();
  } catch {
    // keep data empty
  }

  if (!response.ok) {
    const msg = typeof data === 'string' ? data : (data as any)?.message || (data as any)?.error;
    throw new Error(msg || '세션 내역을 불러오지 못했습니다.');
  }

  return Array.isArray(data) ? data : [];
};

export const fetchStudentSessionDetail = async (sessionId: string) => {
  const response = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
  });

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // ignore JSON parse issues; fall back to null
  }

  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.message || data?.error;
    throw new Error(msg || '세션 상세를 불러오지 못했습니다.');
  }

  return data;
};

export interface PaginatedSchools {
  data: School[];
  total?: number;
  page?: number;
  pageSize?: number;
}

export const fetchSchools = async (page = 1, pageSize = 20): Promise<PaginatedSchools> => {
  const response = await fetch(`${API_BASE}/api/v1/schools?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
  });

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // ignore parsing errors
  }

  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.message || data?.error;
    throw new Error(msg || '학교 목록을 불러오지 못했습니다.');
  }

  const schools = data?.data || data?.schools || data || [];
  const total = data?.total ?? data?.total_count ?? data?.count;
  const normalized: School[] = Array.isArray(schools)
    ? schools.map((s: any) => ({
        id: String(s.id ?? s.school_id ?? s.uuid ?? s.code ?? ''),
        name: s.name ?? s.school_name ?? s.title ?? '',
      }))
    : [];

  return {
    data: normalized,
    total,
    page: data?.page ?? page,
    pageSize: data?.page_size ?? pageSize,
  };
};

export interface PaginatedMajors {
  data: Major[];
  total?: number;
  page?: number;
  pageSize?: number;
}

export const fetchMajors = async (page = 1, pageSize = 20): Promise<PaginatedMajors> => {
  const response = await fetch(`${API_BASE}/api/v1/majors?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
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
    throw new Error(msg || '전공 목록을 불러오지 못했습니다.');
  }

  const majors = data?.data || data?.majors || data || [];
  const total = data?.total ?? data?.total_count ?? data?.count;
  const normalized: Major[] = Array.isArray(majors)
    ? majors.map((m: any) => ({
        id: String(m.id ?? m.major_id ?? m.uuid ?? m.code ?? ''),
        name: m.name ?? m.major_name ?? m.title ?? '',
        schoolId: m.school_id || m.schoolId,
        schoolName: m.school_name || m.schoolName,
      }))
    : [];

  return {
    data: normalized,
    total,
    page: data?.page ?? page,
    pageSize: data?.page_size ?? pageSize,
  };
};

export interface PaginatedUsers {
  data: User[];
  total?: number;
  page?: number;
  pageSize?: number;
}

export const fetchUsers = async ({
  page = 1,
  pageSize = 20,
  role,
  schoolId,
  search,
}: {
  page?: number;
  pageSize?: number;
  role?: User['role'] | 'all';
  schoolId?: string;
  search?: string;
} = {}): Promise<PaginatedUsers> => {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('page_size', String(pageSize));
  if (role && role !== 'all') params.set('role', role);
  if (schoolId) params.set('school_id', schoolId);
  if (search) params.set('search', search);

  const response = await fetch(`${API_BASE}/api/v1/users?${params.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
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
    throw new Error(msg || '사용자 목록을 불러오지 못했습니다.');
  }
  const users = data?.data || data?.users || data?.items || data || [];
  const total = data?.total ?? data?.total_count ?? data?.count ?? (Array.isArray(users) ? users.length : undefined);
  const normalized: User[] = Array.isArray(users)
    ? users.map((u: any) => ({
        id: u.student_id || u.id || u.user_id || u.uuid || '',
        name: u.name || u.full_name || u.display_name || '',
        email: u.email || '',
        role: (u.role || u.role_name || u.user_role || 'student').toLowerCase(),
        schoolName: u.school_name || u.school || '',
        grade: u.grade_level ?? u.grade,
        major: u.major_name || u.major || '',
        authToken: undefined,
        studentId: u.student_id || u.id || u.user_id,
        tempPassword: u.password || u.temp_password || u.tempPassword,
      })) as User[]
    : [];

  const derivedPageSize = data?.page_size ?? data?.limit ?? pageSize;
  const derivedPage =
    data?.page ?? (typeof data?.skip === 'number' && derivedPageSize ? Math.floor(data.skip / derivedPageSize) + 1 : page);

  return {
    data: normalized,
    total,
    page: derivedPage,
    pageSize: derivedPageSize,
  };
};

export interface PaginatedClasses {
  data: ClassRoom[];
  total?: number;
  page?: number;
  pageSize?: number;
}

export interface CreateClassPayload {
  name: string;
  grade_level?: number;
  school_id?: string;
  school_name?: string;
}

export const fetchClasses = async ({
  page = 1,
  pageSize = 20,
  schoolId,
  gradeLevel,
  search,
}: {
  page?: number;
  pageSize?: number;
  schoolId?: string;
  gradeLevel?: number;
  search?: string;
} = {}): Promise<PaginatedClasses> => {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('page_size', String(pageSize));
  if (schoolId) params.set('school_id', schoolId);
  if (typeof gradeLevel === 'number') params.set('grade_level', String(gradeLevel));
  if (search) params.set('search', search);

  const response = await fetch(`${API_BASE}/api/v1/classes?${params.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
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
    throw new Error(msg || '학급 목록을 불러오지 못했습니다.');
  }

  const classes = data?.data || data?.classes || data || [];
  const total = data?.total ?? data?.total_count ?? data?.count;
  const normalized: ClassRoom[] = Array.isArray(classes)
    ? classes.map((c: any) => ({
        id: String(c.id ?? c.class_id ?? c.uuid ?? ''),
        name: c.name ?? c.class_name ?? '',
        gradeLevel: c.grade_level ?? c.grade,
        schoolId: c.school_id || c.schoolId,
        schoolName: c.school_name || c.schoolName,
      }))
    : [];

  return {
    data: normalized,
    total,
    page: data?.page ?? page,
    pageSize: data?.page_size ?? pageSize,
  };
};

export const createClass = async (payload: CreateClassPayload): Promise<ClassRoom> => {
  const response = await fetch(`${API_BASE}/api/v1/classes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(payload),
  });

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // ignore parse errors
  }

  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.message || data?.error;
    throw new Error(msg || '학급을 생성하지 못했습니다.');
  }

  return {
    id: String(data?.id ?? data?.class_id ?? ''),
    name: data?.name ?? data?.class_name ?? '',
    gradeLevel: data?.grade_level ?? data?.grade,
    schoolId: data?.school_id,
    schoolName: data?.school_name,
  };
};
