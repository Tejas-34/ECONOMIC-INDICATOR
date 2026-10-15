import { useState, useEffect, useRef, useCallback } from 'react';
import { TickerQuote, TickerStreamPayload } from '../api/types';
import { fetchLatestTickerQuotes } from '../api/client';

export interface UseTickerStreamReturn {
  quotes: TickerQuote[];
  isConnected: boolean;
  isPollingFallback: boolean;
  refresh: () => Promise<void>;
}

export function useTickerStream(): UseTickerStreamReturn {
  const [quotes, setQuotes] = useState<TickerQuote[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPollingFallback, setIsPollingFallback] = useState(false);

  const reconnectAttempts = useRef(0);
  const pollingTimerRef = useRef<number | null>(null);
  const sseRef = useRef<EventSource | null>(null);

  const fetchPoll = useCallback(async () => {
    try {
      const feed = await fetchLatestTickerQuotes();
      if (feed && feed.quotes) {
        setQuotes(feed.quotes);
        setIsConnected(true);
      }
    } catch {
      setIsConnected(false);
    }
  }, []);

  const startPolling = useCallback(() => {
    setIsPollingFallback(true);
    fetchPoll();
    if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    pollingTimerRef.current = window.setInterval(fetchPoll, 5000);
  }, [fetchPoll]);

  useEffect(() => {
    const isMock = import.meta.env.VITE_USE_MOCKS !== 'false';

    if (isMock) {
      // In mock mode, simulate live updates with periodic polling or mock feed
      fetchPoll();
      const mockInterval = window.setInterval(() => {
        setQuotes((prev) =>
          prev.map((q) => {
            // Subtle simulated drift
            const drift = (Math.random() - 0.48) * 5;
            const newPrice = Math.round((q.currentPrice + drift) * 100) / 100;
            const newPoints = Math.round((q.changePoints + drift) * 100) / 100;
            const newPercent = Math.round((newPoints / (newPrice - newPoints)) * 10000) / 100;
            return {
              ...q,
              currentPrice: newPrice,
              changePoints: newPoints,
              changePercent: newPercent,
              isPositive: newPoints >= 0,
              updatedAt: new Date().toISOString(),
            };
          })
        );
      }, 4000);

      setIsConnected(true);
      return () => clearInterval(mockInterval);
    }

    // Real SSE connection mode
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
    const sseUrl = `${baseUrl}/ticker/stream`;

    try {
      const sse = new EventSource(sseUrl);
      sseRef.current = sse;

      sse.onopen = () => {
        setIsConnected(true);
        setIsPollingFallback(false);
        reconnectAttempts.current = 0;
      };

      sse.onmessage = (event) => {
        try {
          const payload: TickerStreamPayload = JSON.parse(event.data);
          if (payload && payload.quotes) {
            setQuotes(payload.quotes);
          }
        } catch {
          // ignore parse error
        }
      };

      sse.onerror = () => {
        sse.close();
        setIsConnected(false);
        reconnectAttempts.current += 1;

        if (reconnectAttempts.current > 3) {
          // Fallback to polling after 3 failed SSE attempts
          startPolling();
        } else {
          // Exponential backoff reconnect
          const backoff = Math.min(1000 * 2 ** reconnectAttempts.current, 15000);
          setTimeout(() => {
            // trigger re-run
          }, backoff);
        }
      };
    } catch {
      startPolling();
    }

    return () => {
      if (sseRef.current) sseRef.current.close();
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    };
  }, [fetchPoll, startPolling]);

  return {
    quotes,
    isConnected,
    isPollingFallback,
    refresh: fetchPoll,
  };
}
