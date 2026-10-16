import { describe, it, expect, beforeEach } from 'vitest';
import { fetchIndicator, fetchLatestTickerQuotes, apiLogin, setAuthToken, getAuthToken } from '../../src/api/client';
import { IndicatorResponse } from '../../src/api/types';

describe('API Client', () => {
  beforeEach(() => {
    setAuthToken(null);
  });

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

  it('authenticates analyst and stores in-memory token', async () => {
    const response = await apiLogin({
      email: 'analyst@adityabirla.com',
      password: 'AnyPassword',
    });
    expect(response.accessToken).toBeDefined();
    expect(getAuthToken()).toBe(response.accessToken);
    expect(response.user.role).toBe('analyst');
  });
});
