import { getStoredToken } from './authService';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://iksan-ai-interview-backend-production.up.railway.app';

const buildWsUrl = (path: string) => {
  try {
    const url = new URL(API_BASE);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.pathname = path.startsWith('/') ? path : `/${path}`;
    url.search = '';
    url.hash = '';
    return url.toString();
  } catch {
    const stripped = API_BASE.replace(/^https?:\/\//, '');
    const protocol = API_BASE.startsWith('https') ? 'wss' : 'ws';
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${protocol}://${stripped}${normalizedPath}`;
  }
};

const STT_WS_URL = buildWsUrl('/api/v1/stt/live');
export const createLiveSttSocket = () => {
  const token = getStoredToken();
  const url = new URL(STT_WS_URL);
  if (token) {
    url.searchParams.set('token', token);
  }
  const ws = new WebSocket(url.toString());
  ws.binaryType = 'arraybuffer';
  return ws;
};

export interface KoreanSttResponse {
  answer_text?: string;
  text?: string;
  [key: string]: any;
}

export const transcribeKorean = async (file: File): Promise<KoreanSttResponse> => {
  const token = getStoredToken();
  const url = new URL(STT_WS_URL);
  if (token) {
    url.searchParams.set('token', token);
  }

  return new Promise<KoreanSttResponse>((resolve, reject) => {
    let settled = false;
    const ws = new WebSocket(url.toString());
    ws.binaryType = 'arraybuffer';

    const closeWithError = (message: string) => {
      if (settled) return;
      settled = true;
      try {
        ws.close();
      } catch {
        // ignore close errors
      }
      reject(new Error(message));
    };

    const timeoutId = setTimeout(() => {
      closeWithError('?? ??? ??????. ?? ? ?? ??? ???.');
    }, 20000);

    ws.onopen = async () => {
      try {
        const buffer = await file.arrayBuffer();
        ws.send(buffer);
      } catch (err) {
        closeWithError((err as Error)?.message || '?? ??? ????.');
      }
    };

    ws.onmessage = (event) => {
      if (settled) return;
      let payload: KoreanSttResponse | null = null;
      if (typeof event.data === 'string') {
        try {
          payload = JSON.parse(event.data);
        } catch {
          payload = { text: event.data };
        }
      }
      if (!payload) return;
      if (payload.text || payload.answer_text) {
        settled = true;
        clearTimeout(timeoutId);
        ws.close();
        resolve(payload);
      }
    };

    ws.onerror = () => {
      closeWithError('?? ??? ????. ?? ? ?? ??? ???.');
    };

    ws.onclose = () => {
      if (!settled) {
        closeWithError('?? ??? ?? ??? ????.');
      }
      clearTimeout(timeoutId);
    };
  });
};
