import { TickerStreamPayload, LoginCredentials, LoginResponse } from './types';

let inMemoryToken: string | null = null;

export const setAuthToken = (token: string | null): void => {
  inMemoryToken = token;
};

export const getAuthToken = (): string | null => inMemoryToken;

export const isMockMode = (): boolean => {
  return import.meta.env.VITE_USE_MOCKS === 'true';
};

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
// Dynamic Mock Loaders (Tree-shaken out of production bundle)
// -------------------------------------------------------------
async function loadMockIndicator(id: string): Promise<unknown> {
  switch (id) {
    case 'gdp-growth':
      return (await import('../mocks/gdpGrowth.json')).default;
    case 'debt-to-gdp':
      return (await import('../mocks/debtToGdp.json')).default;
    case 'trade-balance':
    case 'trade':
      return (await import('../mocks/tradeBalance.json')).default;
    case 'gst-collection':
    case 'gst':
      return (await import('../mocks/gstCollection.json')).default;
    case 'inflation':
      return (await import('../mocks/inflation.json')).default;
    case 'govt-expenditure':
    case 'government-expenditure':
      return (await import('../mocks/govtExpenditure.json')).default;
    default:
      throw new ApiError(`Indicator '${id}' not found in mock fixtures`, 404);
  }
}

async function loadMockTicker(): Promise<TickerStreamPayload> {
  const mod = await import('../mocks/tickerFeed.json');
  return mod.default as unknown as TickerStreamPayload;
}

// -------------------------------------------------------------
// High-Level Domain API Methods
// -------------------------------------------------------------
export async function fetchIndicator<T = unknown>(id: string): Promise<T> {
  if (isMockMode()) {
    await new Promise((resolve) => setTimeout(resolve, 50));
    return (await loadMockIndicator(id)) as T;
  }
  return request<T>(`/indicators/${id}`);
}

export async function fetchDashboard<T = unknown>(): Promise<T> {
  if (isMockMode()) {
    await new Promise((resolve) => setTimeout(resolve, 60));
    const slugs = [
      'gdp-growth',
      'debt-to-gdp',
      'trade-balance',
      'gst-collection',
      'inflation',
      'govt-expenditure',
    ];
    const indicators = await Promise.all(slugs.map((s) => loadMockIndicator(s)));
    return {
      indicators,
      as_of: '2026',
      fetched_at: new Date().toISOString(),
    } as T;
  }
  return request<T>('/dashboard');
}

export async function fetchLatestTickerQuotes(): Promise<TickerStreamPayload> {
  if (isMockMode()) {
    await new Promise((resolve) => setTimeout(resolve, 40));
    return loadMockTicker();
  }
  return request<TickerStreamPayload>('/ticker');
}

export async function fetchStreamTicket(): Promise<{ ticket: string; expires_in_seconds: number }> {
  if (isMockMode()) {
    return {
      ticket: `mock_ticket_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
      expires_in_seconds: 30,
    };
  }
  return request<{ ticket: string; expires_in_seconds: number }>('/auth/stream-ticket', {
    method: 'POST',
  });
}

export async function apiLogin(credentials: LoginCredentials): Promise<LoginResponse> {
  if (isMockMode()) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const identity = credentials.username || credentials.email;
    if (identity && credentials.password) {
      const mockResponse: LoginResponse = {
        user: {
          id: 'usr_mock_001',
          username: identity,
          email: identity,
          name: 'Lead Macro Analyst',
          role: 'admin',
        },
        accessToken: 'mock_jwt_token_analyst_2026',
        expiresInSeconds: 3600,
      };
      setAuthToken(mockResponse.accessToken);
      return mockResponse;
    }
    throw new ApiError('Invalid email or password', 401);
  }

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
  if (!isMockMode()) {
    try {
      await request('/auth/logout', { method: 'POST', retries: 0 });
    } catch {
      // Ignore network errors during sign-out cleanup
    }
  }
}
