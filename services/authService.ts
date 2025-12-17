import { User, School } from '../types';
import { fetchSchools as fetchSchoolsApi } from './studentService';
import { jwtDecode } from 'jwt-decode';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://iksan-ai-interview-backend-production.up.railway.app';
const TOKEN_KEY = 'auth_token';

const saveToken = (token: string) => {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
  } catch {
    // ignore storage errors
  }
};

export const getStoredToken = () => {
  try {
    return sessionStorage.getItem(TOKEN_KEY) || undefined;
  } catch {
    return undefined;
  }
};

export const clearStoredToken = () => {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore
  }
};

export const apiLogout = async () => {
  const token = getStoredToken();
  if (!token) return;
  await fetch(`${API_BASE}/api/v1/auth/logout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  }).catch(() => {
    // ignore network/logout errors
  });
  clearStoredToken();
};

export const getSchools = async (page = 1, pageSize = 20): Promise<School[]> => {
  const res = await fetchSchoolsApi(page, pageSize);
  return res.data;
};

const buildUserFromResponse = (data: any, fallbackEmail: string): User => {
  const token = data?.token || data?.access_token || data?.accessToken;
  const profile = data?.user || data?.profile || data?.data || data || {};

  let decoded: any = {};
  try {
    if (token) decoded = jwtDecode(token);
  } catch {
    decoded = {};
  }
  const metadata = decoded?.user_metadata || decoded?.app_metadata || profile?.user_metadata || {};

  const roleId = data?.role_id ?? profile?.role_id ?? metadata.role_id ?? decoded.role_id;
  const rawRole =
    data?.role_name ||
    profile?.role_name ||
    metadata.role ||
    decoded?.role ||
    decoded?.user_role ||
    decoded?.data?.role ||
    profile.role ||
    profile?.data?.role ||
    profile?.user_metadata?.role;

  let normalizedRole = typeof rawRole === 'string' ? rawRole.toLowerCase() : '';
  if (!normalizedRole) {
    if (roleId === 1) normalizedRole = 'admin';
    else if (roleId === 2) normalizedRole = 'teacher';
    else if (roleId === 3) normalizedRole = 'student';
  }
  const role: User['role'] =
    normalizedRole.includes('admin')
      ? 'admin'
      : normalizedRole.includes('teacher')
      ? 'teacher'
      : 'student';

  const name = data?.full_name || profile?.full_name || metadata.full_name || profile.name || fallbackEmail.split('@')[0];
  const email = profile.email || data?.email || fallbackEmail;
  const studentId = data?.student_id || profile?.student_id || metadata.student_id;

  const schoolName = data?.school_name ?? profile.schoolName ?? profile.school ?? metadata.schoolName ?? '';
  const grade = data?.grade_level ?? profile.grade ?? metadata.grade;
  const major = data?.major_name ?? profile.major ?? metadata.major ?? '';

  return {
    id: studentId || data?.user_id || profile.id || profile.userId || `temp-${Date.now()}`,
    name,
    email,
    role,
    schoolName,
    grade,
    major,
    authToken: token,
  };
};

export const signIn = async (loginId: string, password: string, mode: 'student' | 'staff' = 'student'): Promise<User> => {
  const attemptLogin = async (url: string, body: Record<string, string>) => {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || 'Login failed');
    }
    return response.json();
  };

  let data: any;
  if (mode === 'student') {
    // Dedicated student login endpoint
    data = await attemptLogin(`${API_BASE}/api/v1/auth/student-login`, { student_id: loginId, password });
  } else {
    // Staff/admin/teacher login (email only)
    data = await attemptLogin(`${API_BASE}/api/v1/auth/login`, { email: loginId, password });
  }

  const user = buildUserFromResponse(data, loginId);
  if (user.authToken) {
    saveToken(user.authToken);
  }
  return user;
};

export const fetchProfile = async (): Promise<User | null> => {
  const token = getStoredToken();
  if (!token) return null;
  const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) return null;
  const data = await response.json();
  const user = buildUserFromResponse(data, data?.email || '');
  user.authToken = token;
  return user;
};

export const signUp = async (
  name: string,
  email: string,
  role: 'teacher' | 'admin',
  options: { schoolName?: string; organization?: string; grade?: number; major?: string },
  password: string
): Promise<User> => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        email,
        password,
        role,
        schoolName: options.schoolName,
        organization: options.organization,
        grade: options.grade,
        major: options.major,
      }),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Sign up failed');
    }
    const data = await response.json();
    const user = buildUserFromResponse(data, email);
    if (user.authToken) saveToken(user.authToken);
    return user;
  } catch (e) {
    // fallback to login attempt
    return signIn(email, password);
  }
};
