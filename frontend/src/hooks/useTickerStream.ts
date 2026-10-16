import { useState, useEffect, useRef, useCallback } from 'react';
import { TickerQuote } from '../api/types';
import { fetchLatestTickerQuotes, fetchStreamTicket, getApiOrigin, isMockMode } from '../api/client';

export type MarketBadgeStatus = 'LIVE' | 'CLOSED' | 'STALE';

export interface UseTickerStreamReturn {
  quotes: TickerQuote[];
  isConnected: boolean;
  isPollingFallback: boolean;
  marketStatus: MarketBadgeStatus;
  lastUpdated: string | null;
  refresh: () => Promise<void>;
}

export function useTickerStream(): UseTickerStreamReturn {
  const [quotes, setQuotes] = useState<TickerQuote[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPollingFallback, setIsPollingFallback] = useState(false);
  const [marketStatus, setMarketStatus] = useState<MarketBadgeStatus>('LIVE');
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const lastUpdateEpochRef = useRef<number>(Date.now());
  const consecutiveFailures = useRef(0);
  const pollingTimerRef = useRef<number | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const sseRef = useRef<EventSource | null>(null);
  const isUnmountedRef = useRef(false);

  // Synchronize quotes and update timestamps
  const handleIncomingQuotes = useCallback((newQuotes: TickerQuote[]) => {
    if (!newQuotes || newQuotes.length === 0) return;
    setQuotes(newQuotes);
    lastUpdateEpochRef.current = Date.now();
    const dateStr = new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    setLastUpdated(dateStr);
  }, []);

  // Polling fallback mechanism
  const fetchPoll = useCallback(async () => {
    try {
      const feed = await fetchLatestTickerQuotes();
      if (feed && feed.quotes) {
        handleIncomingQuotes(feed.quotes);
      }
    } catch {
      // Ignore poll error
    }
  }, [handleIncomingQuotes]);

  const startPollingFallback = useCallback(() => {
    setIsPollingFallback(true);
    fetchPoll();
    if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    // Poll every 10 seconds during fallback (I4)
    pollingTimerRef.current = window.setInterval(fetchPoll, 10000);
  }, [fetchPoll]);

  const stopPollingFallback = useCallback(() => {
    setIsPollingFallback(false);
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  }, []);

  // Connect to SSE stream with fresh ticket and backoff
  const connectSSE = useCallback(async () => {
    if (isUnmountedRef.current) return;
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }

    try {
      // 1. Acquire single-use stream ticket (I3/I4)
      const ticketRes = await fetchStreamTicket();
      if (isUnmountedRef.current) return;

      const origin = getApiOrigin();
      const sseUrl = `${origin}/api/stream/ticker?ticket=${encodeURIComponent(ticketRes.ticket)}`;

      const eventSource = new EventSource(sseUrl);
      sseRef.current = eventSource;

      eventSource.onopen = () => {
        if (isUnmountedRef.current) return;
        setIsConnected(true);
        consecutiveFailures.current = 0;
        stopPollingFallback();
      };

      // 2. Listen for named 'snapshot' event (I4)
      eventSource.addEventListener('snapshot', (event: MessageEvent) => {
        if (isUnmountedRef.current) return;
        try {
          const payload = JSON.parse(event.data);
          if (payload && payload.quotes) {
            handleIncomingQuotes(payload.quotes);
          }
        } catch {
          // Ignore JSON parse error
        }
      });

      // Also listen to default onmessage in case of legacy payload
      eventSource.onmessage = (event: MessageEvent) => {
        if (isUnmountedRef.current) return;
        try {
          const payload = JSON.parse(event.data);
          if (payload && payload.quotes) {
            handleIncomingQuotes(payload.quotes);
          }
        } catch {
          // Ignore
        }
      };

      eventSource.onerror = () => {
        if (isUnmountedRef.current) return;
        eventSource.close();
        sseRef.current = null;
        setIsConnected(false);
        consecutiveFailures.current += 1;

        // Fall back to 10s polling after 3 consecutive failures (I4)
        if (consecutiveFailures.current >= 3) {
          startPollingFallback();
        }

        // Exponential backoff 1s to 30s with jitter (I4)
        const baseDelay = Math.min(
          1000 * Math.pow(1.5, consecutiveFailures.current - 1),
          30000
        );
        const jitter = Math.random() * 1000;
        const totalDelay = Math.round(baseDelay + jitter);

        if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = window.setTimeout(() => {
          connectSSE();
        }, totalDelay);
      };
    } catch {
      consecutiveFailures.current += 1;
      if (consecutiveFailures.current >= 3) {
        startPollingFallback();
      }
      const retryDelay = Math.min(1000 * Math.pow(1.5, consecutiveFailures.current - 1), 30000);
      reconnectTimerRef.current = window.setTimeout(connectSSE, retryDelay);
    }
  }, [handleIncomingQuotes, startPollingFallback, stopPollingFallback]);

  // Periodic evaluation of badge status: LIVE / CLOSED / STALE (I5)
  useEffect(() => {
    const statusInterval = window.setInterval(() => {
      const now = Date.now();
      const elapsedSinceUpdate = (now - lastUpdateEpochRef.current) / 1000;

      // Check if backend reports market as closed
      const anyClosed = quotes.some(
        (q) => (q as any).market_status === 'closed'
      );
      if (anyClosed) {
        setMarketStatus('CLOSED');
        return;
      }

      // If SSE down for > 60s or no update for > 40s (2x 20s interval) -> STALE
      if ((!isConnected && elapsedSinceUpdate > 60) || elapsedSinceUpdate > 40) {
        setMarketStatus('STALE');
        return;
      }

      setMarketStatus('LIVE');
    }, 2000);

    return () => clearInterval(statusInterval);
  }, [isConnected, quotes]);

  // Main lifecycle effect
  useEffect(() => {
    isUnmountedRef.current = false;

    // 1. Initial snapshot on mount (I4)
    fetchPoll();

    if (isMockMode()) {
      setIsConnected(true);
      // In mock mode, update every 4 seconds with mock data
      const mockInterval = window.setInterval(fetchPoll, 4000);
      return () => {
        isUnmountedRef.current = true;
        clearInterval(mockInterval);
      };
    }

    // 2. Connect to SSE stream
    connectSSE();

    return () => {
      isUnmountedRef.current = true;
      if (sseRef.current) {
        sseRef.current.close();
        sseRef.current = null;
      }
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    };
  }, [fetchPoll, connectSSE]);

  return {
    quotes,
    isConnected,
    isPollingFallback,
    marketStatus,
    lastUpdated,
    refresh: fetchPoll,
  };
}
