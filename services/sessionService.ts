import { InterviewStartPayload, Question } from '../types';
import { getStoredToken } from './authService';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://iksan-ai-interview-backend-production.up.railway.app';

export interface InitiateSessionResponse {
  sessionId?: string;
  questions: Question[];
  timeLimitSeconds?: number;
}

export const initiateSession = async (input: InterviewStartPayload): Promise<InitiateSessionResponse> => {
  const token = getStoredToken();
  const payload = {
    intent: input.intent,
    resumeText: input.resumeText,
    resumeFile: input.fileData?.data,
    resumeMimeType: input.fileData?.mimeType,
    favoriteUniversities: input.favoriteUniversities,
    major: input.major,
    workField: input.workField,
  };

  const response = await fetch(`${API_BASE}/api/v1/sessions/initiate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Failed to initiate interview session');
  }

  const data = await response.json();
  return {
    sessionId: data?.sessionId || data?.session_id,
    questions: data?.questions || [],
    timeLimitSeconds: data?.timeLimitSeconds ?? data?.perQuestionSeconds,
  };
};
