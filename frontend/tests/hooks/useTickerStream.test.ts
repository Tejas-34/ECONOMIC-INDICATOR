import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTickerStream } from '../../src/hooks/useTickerStream';
import * as client from '../../src/api/client';

class MockEventSource {
  static instances: MockEventSource[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  listeners: Record<string, ((event: MessageEvent) => void)[]> = {};
  closed = false;

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (event: MessageEvent) => void) {
    if (!this.listeners[type]) this.listeners[type] = [];
    this.listeners[type].push(listener);
  }

  emit(type: string, data: any) {
    const event = { data: JSON.stringify(data) } as MessageEvent;
    if (this.listeners[type]) {
      this.listeners[type].forEach((l) => l(event));
    }
    if (type === 'message' && this.onmessage) {
      this.onmessage(event);
    }
  }

  triggerOpen() {
    if (this.onopen) this.onopen();
  }

  triggerError() {
    if (this.onerror) this.onerror();
  }

  close() {
    this.closed = true;
  }
}

describe('useTickerStream Hook', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    MockEventSource.instances = [];
    (globalThis as any).EventSource = MockEventSource;
    vi.spyOn(client, 'isMockMode').mockReturnValue(false);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('fetches initial snapshot on mount and connects to SSE with stream ticket', async () => {
    vi.spyOn(client, 'fetchLatestTickerQuotes').mockResolvedValueOnce({
      timestamp: '2026-10-16T12:00:00Z',
      quotes: [
        {
          symbol: 'SENSEX',
          currentPrice: 73500.0,
          changePoints: 200.0,
          changePercent: 0.27,
          isPositive: true,
          updatedAt: '2026-10-16T12:00:00Z',
        },
      ],
    });

    vi.spyOn(client, 'fetchStreamTicket').mockResolvedValueOnce({
      ticket: 'test_stream_ticket_123',
      expires_in_seconds: 30,
    });

    const { result } = renderHook(() => useTickerStream());

    // Allow mount promises to resolve
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.quotes.length).toBe(1);
    expect(result.current.quotes[0].symbol).toBe('SENSEX');

    // Verify EventSource connected with ticket
    expect(MockEventSource.instances.length).toBe(1);
    expect(MockEventSource.instances[0].url).toContain('ticket=test_stream_ticket_123');

    // Simulate SSE connection open
    act(() => {
      MockEventSource.instances[0].triggerOpen();
    });
    expect(result.current.isConnected).toBe(true);
    expect(result.current.isPollingFallback).toBe(false);
  });

  it('updates quotes when named snapshot event is received', async () => {
    vi.spyOn(client, 'fetchLatestTickerQuotes').mockResolvedValueOnce({
      timestamp: '2026-10-16T12:00:00Z',
      quotes: [],
    });
    vi.spyOn(client, 'fetchStreamTicket').mockResolvedValueOnce({
      ticket: 'ticket_abc',
      expires_in_seconds: 30,
    });

    const { result } = renderHook(() => useTickerStream());
    await act(async () => {
      await Promise.resolve();
    });

    const sse = MockEventSource.instances[0];
    act(() => {
      sse.triggerOpen();
    });

    // Emit named 'snapshot' event with 2 quotes
    act(() => {
      sse.emit('snapshot', {
        timestamp: '2026-10-16T12:00:05Z',
        quotes: [
          {
            symbol: 'NIFTY BANK',
            currentPrice: 48500.0,
            changePoints: 150.0,
            changePercent: 0.31,
            isPositive: true,
            updatedAt: '2026-10-16T12:00:05Z',
          },
          {
            symbol: 'NIFTY IT',
            currentPrice: 36000.0,
            changePoints: -50.0,
            changePercent: -0.14,
            isPositive: false,
            updatedAt: '2026-10-16T12:00:05Z',
          },
        ],
      });
    });

    expect(result.current.quotes.length).toBe(2);
    expect(result.current.quotes[0].symbol).toBe('NIFTY BANK');
    expect(result.current.quotes[1].symbol).toBe('NIFTY IT');
    expect(result.current.marketStatus).toBe('LIVE');
    expect(result.current.lastUpdated).toBeDefined();
  });

  it('initiates polling fallback after 3 consecutive connection failures', async () => {
    const pollSpy = vi.spyOn(client, 'fetchLatestTickerQuotes').mockResolvedValue({
      timestamp: '2026-10-16T12:00:00Z',
      quotes: [
        {
          symbol: 'SENSEX',
          currentPrice: 73500.0,
          changePoints: 100.0,
          changePercent: 0.15,
          isPositive: true,
          updatedAt: '2026-10-16T12:00:00Z',
        },
      ],
    });

    vi.spyOn(client, 'fetchStreamTicket').mockResolvedValue({
      ticket: 'ticket_fail',
      expires_in_seconds: 30,
    });

    const { result } = renderHook(() => useTickerStream());
    await act(async () => {
      await Promise.resolve();
    });

    // 1st error
    act(() => {
      MockEventSource.instances[0].triggerError();
    });
    expect(result.current.isConnected).toBe(false);
    expect(result.current.isPollingFallback).toBe(false);

    // Fast-forward backoff for 2nd attempt
    act(() => {
      vi.advanceTimersByTime(3000);
    });
    await act(async () => {
      await Promise.resolve();
    });

    // 2nd error
    if (MockEventSource.instances[1]) {
      act(() => {
        MockEventSource.instances[1].triggerError();
      });
    }

    // Fast-forward backoff for 3rd attempt
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {
      await Promise.resolve();
    });

    // 3rd error -> trips fallback
    if (MockEventSource.instances[2]) {
      act(() => {
        MockEventSource.instances[2].triggerError();
      });
    }

    expect(result.current.isPollingFallback).toBe(true);
    expect(pollSpy).toHaveBeenCalled();
  });

  it('cleans up EventSource and timers on unmount', async () => {
    vi.spyOn(client, 'fetchLatestTickerQuotes').mockResolvedValueOnce({
      timestamp: '2026-10-16T12:00:00Z',
      quotes: [],
    });
    vi.spyOn(client, 'fetchStreamTicket').mockResolvedValueOnce({
      ticket: 'ticket_cleanup',
      expires_in_seconds: 30,
    });

    const { unmount } = renderHook(() => useTickerStream());
    await act(async () => {
      await Promise.resolve();
    });

    const sse = MockEventSource.instances[0];
    unmount();
    expect(sse.closed).toBe(true);
  });
});
