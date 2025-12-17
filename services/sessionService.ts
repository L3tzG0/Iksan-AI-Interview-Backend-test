import { InterviewStartPayload, Answer } from '../types';
import { getStoredToken } from './authService';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://iksan-ai-interview-backend-production.up.railway.app';

export interface InitiateSessionResponse {
  sessionId?: string;
  message?: string;
  status?: string;
}

const base64ToBlob = (base64: string, mimeType: string) => {
  const byteCharacters = atob(base64);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: mimeType });
};

export const initiateSession = async (input: InterviewStartPayload): Promise<InitiateSessionResponse> => {
  const token = getStoredToken();
  const formData = new FormData();

  const field = input.workField || input.major || input.workIndustry || 'General';
  const role = input.workField || input.major || 'Candidate';
  formData.append('field', field);
  formData.append('role', role);

  if (input.fileData?.data && input.fileData?.mimeType) {
    try {
      const blob = base64ToBlob(input.fileData.data, input.fileData.mimeType);
      formData.append('file', blob, 'resume');
    } catch {
      if (input.resumeText) {
        formData.append('raw_text', input.resumeText);
      }
    }
  } else if (input.resumeText) {
    formData.append('raw_text', input.resumeText);
  }

  const endpoint =
    input.intent === 'university'
      ? '/api/v1/sessions/initiate_university_prep'
      : '/api/v1/sessions/initiate';

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.message || data?.error;
    throw new Error(msg || 'Failed to initiate interview session');
  }

  return {
    sessionId: data?.session_id || data?.sessionId,
    message: data?.message,
    status: data?.status,
  };
};

export interface SessionStatusResponse {
  status?: string;
  isReady?: boolean;
  message?: string;
}

export const fetchSessionStatus = async (sessionId: string): Promise<SessionStatusResponse> => {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE}/api/v1/sessions/status/${sessionId}`, {
    method: 'GET',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.message || data?.error;
    throw new Error(msg || 'Failed to fetch session status');
  }
  return {
    status: data?.status,
    isReady: data?.is_ready ?? data?.isReady,
    message: data?.message,
  };
};

export const fetchSessionDetail = async (sessionId: string) => {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`, {
    method: 'GET',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.message || data?.error;
    throw new Error(msg || 'Failed to fetch session detail');
  }
  return data;
};

export interface SubmitSessionResponse {
  status?: string;
  message?: string;
  sessionId?: string;
}

export const submitSessionAnswers = async (sessionId: string, qaPairs: Answer[]): Promise<SubmitSessionResponse> => {
  const token = getStoredToken();
  const payload = {
    session_id: sessionId,
    qa_pairs: qaPairs.map((a, idx) => ({
      question_order: a.questionOrder ?? idx + 1,
      question_text: a.questionText || '',
      answer_text: a.text,
      audio_duration_seconds: a.audioDurationSeconds,
      word_count: a.wordCount,
      total_pause_duration_seconds: a.totalPauseDurationSeconds,
      total_pause_count: a.totalPauseCount,
    })),
  };

  const response = await fetch(`${API_BASE}/api/v1/sessions/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.message || data?.error;
    throw new Error(msg || 'Failed to submit interview session');
  }

  return {
    status: data?.status,
    message: data?.message,
    sessionId: data?.session_id || sessionId,
  };
};
