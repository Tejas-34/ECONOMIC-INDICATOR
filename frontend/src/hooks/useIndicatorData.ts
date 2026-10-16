import { useState, useEffect, useCallback } from 'react';
import { IndicatorResponse, PanelState } from '../api/types';
import { fetchIndicator } from '../api/client';

export interface UseIndicatorDataReturn<T = unknown> {
  data: IndicatorResponse<T> | null;
  state: PanelState;
  error: Error | null;
  refetch: () => Promise<void>;
  setPanelState: (state: PanelState) => void;
}

export function useIndicatorData<T = Record<string, unknown>>(
  indicatorId: string,
  initialStateOverride?: PanelState
): UseIndicatorDataReturn<T> {
  const [data, setData] = useState<IndicatorResponse<T> | null>(null);
  const [state, setState] = useState<PanelState>(initialStateOverride || 'loading');
  const [error, setError] = useState<Error | null>(null);

  const loadData = useCallback(async () => {
    setState('loading');
    setError(null);
    try {
      const response = await fetchIndicator<IndicatorResponse<T>>(indicatorId);
      setData(response);

      if (initialStateOverride) {
        setState(initialStateOverride);
        return;
      }

      // Map indicator status
      if (response.status === 'stale') {
        setState('stale');
      } else if (response.status === 'unavailable') {
        setState('unavailable');
      } else if (
        !response.series ||
        (Array.isArray(response.series) && response.series.length === 0)
      ) {
        setState('empty');
      } else {
        setState('ok');
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      setState('error');
    }
  }, [indicatorId, initialStateOverride]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return {
    data,
    state,
    error,
    refetch: loadData,
    setPanelState: setState,
  };
}
