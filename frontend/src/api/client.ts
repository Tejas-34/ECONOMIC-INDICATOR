import { TickerStreamPayload, LoginCredentials, LoginResponse } from './types';

let inMemoryToken: string | null = null;

export const setAuthToken = (token: string | null): void => {
  inMemoryToken = token;
};

export const getAuthToken = (): string | null => inMemoryToken;


export function normalizeApiBaseUrl(raw?: string): string {
  const url = (raw || '/api').trim();
  if (url === '/api' || url === '/api/') return '/api';
  const stripped = url.replace(/\/+$/, '');
  if (stripped.endsWith('/api')) {
    return stripped;
  }
  return `${stripped}/api`;
}

export function getApiOrigin(): string {
  const base = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
  if (base.startsWith('http://') || base.startsWith('https://')) {
    try {
      return new URL(base).origin;
    } catch {
      // fallback
    }
  }
  if (typeof window !== 'undefined' && window.location) {
    return window.location.origin;
  }
  return 'http://localhost:8000';
}

export class ApiError extends Error {
  public status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

// In-memory ETag cache
interface ETagCacheEntry {
  etag: string;
  data: unknown;
}
const etagCache = new Map<string, ETagCacheEntry>();

export function clearEtagCache(): void {
  etagCache.clear();
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
  retries?: number;
}

export async function request<T = unknown>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const baseUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
  const isFullUrl = path.startsWith('http://') || path.startsWith('https://');
  const url = isFullUrl
    ? path
    : `${baseUrl}${path.startsWith('/') ? '' : '/'}${path}`;

  const method = (options.method || 'GET').toUpperCase();
  const maxRetries = method === 'GET' ? (options.retries ?? 2) : 0;
  const timeoutMs = options.timeoutMs ?? 10000;

  let lastError: unknown = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    if (options.signal) {
      options.signal.addEventListener('abort', () => controller.abort());
    }

    const headers = new Headers(options.headers || {});
    if (inMemoryToken && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${inMemoryToken}`);
    }
    if (!headers.has('Content-Type') && method !== 'GET') {
      headers.set('Content-Type', 'application/json');
    }

    if (method === 'GET') {
      const cached = etagCache.get(url);
      if (cached?.etag) {
        headers.set('If-None-Match', cached.etag);
      }
    }

    try {
      const response = await fetch(url, {
        ...options,
        method,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Global 401 Handler (I3)
      if (response.status === 401) {
        setAuthToken(null);
        if (typeof window !== 'undefined' && window.location) {
          if (!window.location.pathname.startsWith('/login')) {
            window.location.href = '/login?session_expired=true';
          }
        }
        throw new ApiError('Session expired. Please log in again.', 401);
      }

      // 304 Not Modified ETag Cache Hit
      if (response.status === 304 && method === 'GET') {
        const cached = etagCache.get(url);
        if (cached) {
          return cached.data as T;
        }
      }

      if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        let detail = response.statusText;
        try {
          const parsed = JSON.parse(errorText);
          if (parsed.detail) {
            detail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
          }
        } catch {
          if (errorText) detail = errorText;
        }
        throw new ApiError(detail || `Request failed with status ${response.status}`, response.status);
      }

      if (response.status === 204) {
        return undefined as T;
      }

      const data = await response.json();
      if (method === 'GET') {
        const etag = response.headers.get('ETag');
        if (etag) {
          etagCache.set(url, { etag, data });
        }
      }
      return data as T;
    } catch (err: any) {
      clearTimeout(timeoutId);
      lastError = err;

      // Do NOT retry 4xx errors
      if (err instanceof ApiError && err.status < 500 && err.status !== 0 && err.status !== 408) {
        throw err;
      }

      if (attempt < maxRetries) {
        const delay = 300 * Math.pow(2, attempt);
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }
    }
  }

  if (lastError instanceof Error && lastError.name === 'AbortError') {
    throw new ApiError('Request timed out after 10 seconds', 408);
  }
  if (lastError instanceof ApiError) {
    throw lastError;
  }
  throw new ApiError((lastError as Error)?.message || 'Network request failed', 0);
}

// -------------------------------------------------------------
// High-Level Domain API Methods (Strictly Live Endpoints)
// -------------------------------------------------------------
export async function fetchIndicator<T = unknown>(id: string): Promise<T> {
  return request<T>(`/indicators/${id}`);
}

export async function fetchDashboard<T = unknown>(): Promise<T> {
  return request<T>('/dashboard');
}

export async function fetchLatestTickerQuotes(): Promise<TickerStreamPayload> {
  return request<TickerStreamPayload>('/ticker');
}

export async function fetchStreamTicket(): Promise<{ ticket: string; expires_in_seconds: number }> {
  return request<{ ticket: string; expires_in_seconds: number }>('/auth/stream-ticket', {
    method: 'POST',
  });
}

export async function apiLogin(credentials: LoginCredentials): Promise<LoginResponse> {
  const data = await request<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
  setAuthToken(data.accessToken);
  return data;
}

export async function apiLogout(): Promise<void> {
  setAuthToken(null);
  clearEtagCache();
  try {
    await request('/auth/logout', { method: 'POST', retries: 0 });
  } catch {
    // Ignore network errors during sign-out cleanup
  }
}
