import { User, School } from '../types';

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

export const getSchools = async (): Promise<School[]> => {
  // Placeholder until backend exposes schools
  return [];
};

const buildUserFromResponse = (data: any, fallbackEmail: string): User => {
  const token = data?.token || data?.access_token || data?.accessToken;
  const profile = data?.user || data?.profile || data?.data || data || {};
  const rawRole = profile.role || profile?.data?.role || profile?.user_metadata?.role;
  const normalizedRole = typeof rawRole === 'string' ? rawRole.toLowerCase() : '';
  const role: User['role'] =
    normalizedRole.includes('admin')
      ? 'admin'
      : normalizedRole.includes('teacher')
      ? 'teacher'
      : normalizedRole
      ? 'student'
      : 'student';
  return {
    id: profile.id || profile.userId || `temp-${Date.now()}`,
    name: profile.name || fallbackEmail.split('@')[0],
    email: profile.email || fallbackEmail,
    role,
    schoolName: profile.schoolName || profile.school || '',
    grade: profile.grade,
    major: profile.major,
    authToken: token,
  };
};

export const signIn = async (loginId: string, password: string): Promise<User> => {
  const attemptLogin = async (body: Record<string, string>) => {
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
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
  try {
    // Default: treat as email login
    data = await attemptLogin({ email: loginId, password });
  } catch (err) {
    // Fallback: student ID login (if backend supports student_id)
    if (loginId.includes('@')) throw err;
    data = await attemptLogin({ student_id: loginId, password });
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
