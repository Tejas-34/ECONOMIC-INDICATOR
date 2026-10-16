import { useState, useEffect, useCallback, useContext, useSyncExternalStore } from 'react';
import { ReactReduxContext } from 'react-redux';
import { IndicatorResponse, PanelState } from '../api/types';
import { fetchIndicator } from '../api/client';
import {
  fetchDashboardThunk,
  fetchIndicatorThunk,
  setIndicatorStateOverride,
  IndicatorEntry,
} from '../store/slices/indicatorsSlice';
import { AppDispatch, RootState } from '../store';

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
  const reduxContext = useContext(ReactReduxContext);
  const store = reduxContext?.store;

  // Local fallback state (used when outside Redux Provider)
  const [localData, setLocalData] = useState<IndicatorResponse<T> | null>(null);
  const [localState, setLocalState] = useState<PanelState>(initialStateOverride || 'loading');
  const [localError, setLocalError] = useState<Error | null>(null);

  // Redux subscriptions via useSyncExternalStore
  const reduxEntry: IndicatorEntry | undefined = useSyncExternalStore(
    store ? store.subscribe : () => () => {},
    store ? () => (store.getState() as RootState).indicators.byIndicator[indicatorId] : () => undefined,
    store ? () => (store.getState() as RootState).indicators.byIndicator[indicatorId] : () => undefined
  );

  // Fallback loadData for non-Redux test environments
  const loadLocalData = useCallback(async () => {
    setLocalState('loading');
    setLocalError(null);
    try {
      const response = await fetchIndicator<IndicatorResponse<T>>(indicatorId);
      setLocalData(response);

      if (initialStateOverride) {
        setLocalState(initialStateOverride);
        return;
      }

      if (response.status === 'stale') {
        setLocalState('stale');
      } else if (response.status === 'unavailable') {
        setLocalState('unavailable');
      } else if (!response.series || (Array.isArray(response.series) && response.series.length === 0)) {
        setLocalState('empty');
      } else {
        setLocalState('ok');
      }
    } catch (err) {
      setLocalError(err instanceof Error ? err : new Error(String(err)));
      setLocalState('error');
    }
  }, [indicatorId, initialStateOverride]);

  // Initial load
  useEffect(() => {
    if (!store) {
      loadLocalData();
      return;
    }

    const dispatch = store.dispatch as AppDispatch;
    const currentState = store.getState() as RootState;

    if (!currentState.indicators.dashboardLastUpdated && !currentState.indicators.dashboardLoading) {
      // First paint: trigger consolidated dashboard fetch
      dispatch(fetchDashboardThunk());
    } else if (currentState.indicators.dashboardLastUpdated && !currentState.indicators.byIndicator[indicatorId]?.data) {
      // Individual panel fetch if missing from dashboard
      dispatch(fetchIndicatorThunk(indicatorId));
    }
  }, [store, indicatorId, loadLocalData]);

  // Isolated panel refetch
  const refetch = useCallback(async () => {
    if (!store) {
      await loadLocalData();
      return;
    }
    const dispatch = store.dispatch as AppDispatch;
    await dispatch(fetchIndicatorThunk(indicatorId));
  }, [store, indicatorId, loadLocalData]);

  // 5-minute periodic refresh
  useEffect(() => {
    const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
    const interval = setInterval(() => {
      refetch();
    }, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refetch]);

  if (!store) {
    return {
      data: localData,
      state: initialStateOverride || localState,
      error: localError,
      refetch,
      setPanelState: setLocalState,
    };
  }

  const effectiveData = (reduxEntry?.data as IndicatorResponse<T>) || null;
  const effectiveState: PanelState = initialStateOverride || reduxEntry?.state || 'loading';
  const effectiveError = reduxEntry?.error ? new Error(reduxEntry.error) : null;

  const setPanelState = (newState: PanelState) => {
    const dispatch = store.dispatch as AppDispatch;
    dispatch(setIndicatorStateOverride({ indicatorId, panelState: newState }));
  };

  return {
    data: effectiveData,
    state: effectiveState,
    error: effectiveError,
    refetch,
    setPanelState,
  };
}
