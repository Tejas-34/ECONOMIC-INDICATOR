import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  fetchIndicator,
  fetchLatestTickerQuotes,
  apiLogin,
  setAuthToken,
  getAuthToken,
  normalizeApiBaseUrl,
  getApiOrigin,
  request,
  clearEtagCache,
  ApiError,
} from '../../src/api/client';
import { IndicatorResponse } from '../../src/api/types';

describe('API Client', () => {
  beforeEach(() => {
    setAuthToken(null);
    clearEtagCache();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Mock Mode Domain Methods', () => {
    it('fetches mock GDP indicator data matching contract', async () => {
      const data = await fetchIndicator<IndicatorResponse>('gdp-growth');
      expect(data.id).toBe('gdp-growth');
      expect(data.title).toBe('GDP Growth - India vs World');
      expect(data.source_type).toBe('external');
      expect(data.values.india.value).toBe(4.82);
      expect(data.values.world.value).toBe(3.82);
    });

    it('fetches mock ticker quotes with SENSEX and NIFTY', async () => {
      const feed = await fetchLatestTickerQuotes();
      expect(feed.quotes.length).toBeGreaterThan(0);
      const symbols = feed.quotes.map((q) => q.symbol);
      expect(symbols).toContain('SENSEX');
      expect(symbols).toContain('NIFTY BANK');
    });

    it('authenticates analyst and stores in-memory token with aligned role', async () => {
      const response = await apiLogin({
        email: 'analyst@adityabirla.com',
        password: 'AnyPassword',
      });
      expect(response.accessToken).toBeDefined();
      expect(getAuthToken()).toBe(response.accessToken);
      expect(response.user.role).toBe('admin');
    });
  });

  describe('URL Normalization', () => {
    it('normalizes various base URL formats correctly', () => {
      expect(normalizeApiBaseUrl(undefined)).toBe('/api');
      expect(normalizeApiBaseUrl('')).toBe('/api');
      expect(normalizeApiBaseUrl('/api')).toBe('/api');
      expect(normalizeApiBaseUrl('/api/')).toBe('/api');
      expect(normalizeApiBaseUrl('http://localhost:8000')).toBe('http://localhost:8000/api');
      expect(normalizeApiBaseUrl('http://localhost:8000/')).toBe('http://localhost:8000/api');
      expect(normalizeApiBaseUrl('http://localhost:8000/api')).toBe('http://localhost:8000/api');
      expect(normalizeApiBaseUrl('http://localhost:8000/api/')).toBe('http://localhost:8000/api');
    });

    it('extracts API origin cleanly', () => {
      const origin = getApiOrigin();
      expect(origin).toBeDefined();
    });
  });

  describe('request() Wrapper Features', () => {
    it('handles global 401 interception: clears token and redirects to login', async () => {
      setAuthToken('valid_token_123');
      expect(getAuthToken()).toBe('valid_token_123');

      // Mock window.location
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = {
        href: 'http://localhost:5173/',
        pathname: '/',
        origin: 'http://localhost:5173',
      } as any;

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Token expired' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      await expect(request('/indicators/gdp-growth')).rejects.toThrow(ApiError);
      expect(getAuthToken()).toBeNull();
      expect(window.location.href).toBe('/login?session_expired=true');

      window.location = originalLocation as any;
    });

    it('implements ETag caching: returns cached data on 304 Not Modified', async () => {
      const testData = { id: 'gdp-growth', value: 4.82 };

      // 1st request: returns 200 with ETag header
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify(testData), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            ETag: '"gdp-etag-123"',
          },
        })
      );

      const firstResult = await request('/indicators/gdp-growth');
      expect(firstResult).toEqual(testData);

      // 2nd request: returns 304 Not Modified
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(null, {
          status: 304,
          headers: {
            ETag: '"gdp-etag-123"',
          },
        })
      );

      const secondResult = await request('/indicators/gdp-growth');
      expect(secondResult).toEqual(testData);

      // Verify that If-None-Match header was passed on the 2nd request
      const callHeaders = fetchSpy.mock.calls[0][1]?.headers as Headers;
      expect(callHeaders.get('If-None-Match')).toBe('"gdp-etag-123"');
    });

    it('retries up to 2 times on 500 server error and succeeds if next attempt succeeds', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch')
        // 1st attempt: 500
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ detail: 'Server Error 1' }), { status: 500 })
        )
        // 2nd attempt: 500
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ detail: 'Server Error 2' }), { status: 500 })
        )
        // 3rd attempt: 200 OK
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ success: true }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        );

      const result = await request<{ success: boolean }>('/test-retry');
      expect(result).toEqual({ success: true });
      expect(fetchSpy).toHaveBeenCalledTimes(3);
    });

    it('does not retry 4xx errors like 404', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Not Found' }), { status: 404 })
      );

      await expect(request('/indicators/unknown')).rejects.toThrow(ApiError);
      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    it('times out and throws ApiError with status 408 when request exceeds timeoutMs', async () => {
      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(
        (_url, options) =>
          new Promise((_, reject) => {
            if (options?.signal) {
              options.signal.addEventListener('abort', () => {
                const abortErr = new Error('The operation was aborted');
                abortErr.name = 'AbortError';
                reject(abortErr);
              });
            }
          })
      );

      await expect(
        request('/slow-endpoint', { timeoutMs: 50, retries: 0 })
      ).rejects.toThrow('Request timed out after 10 seconds');
    });
  });
});
