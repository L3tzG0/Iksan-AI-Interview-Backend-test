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
  const role = profile.role === 'teacher' ? 'teacher' : 'student';
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

export const signIn = async (email: string, password: string): Promise<User> => {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Login failed');
  }
  const data = await response.json();
  const user = buildUserFromResponse(data, email);
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
  role: 'student' | 'teacher',
  schoolName: string,
  grade: number,
  major: string,
  password: string
): Promise<User> => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, role, schoolName, grade, major }),
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
