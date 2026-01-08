const DEFAULT_API_BASE = 'https://iksan-ai-interview-backend-production.up.railway.app';

const normalizeApiBase = (raw: string | undefined): string => {
  const trimmed = (raw || '').trim();
  const candidate = trimmed || DEFAULT_API_BASE;

  // Already absolute
  if (/^https?:\/\//i.test(candidate)) {
    return candidate.replace(/\/+$/, '');
  }

  // Support protocol-relative URLs
  if (candidate.startsWith('//')) {
    return `https:${candidate}`.replace(/\/+$/, '');
  }

  // If user provided a host without scheme, default based on whether it's local.
  const looksLocal =
    candidate.startsWith('localhost') ||
    candidate.startsWith('127.') ||
    candidate.startsWith('0.0.0.0') ||
    candidate.endsWith('.local');

  const protocol = looksLocal ? 'http' : 'https';
  return `${protocol}://${candidate}`.replace(/\/+$/, '');
};

export const API_BASE = normalizeApiBase(import.meta.env.VITE_API_BASE);
