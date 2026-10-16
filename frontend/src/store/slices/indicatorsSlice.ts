import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { fetchIndicator, fetchDashboard } from '../../api/client';
import { IndicatorResponse, PanelState } from '../../api/types';

export interface IndicatorEntry {
  data: IndicatorResponse<any> | null;
  state: PanelState;
  error?: string;
  lastUpdated?: string;
}

export interface IndicatorsState {
  byIndicator: Record<string, IndicatorEntry>;
  dashboardLoading: boolean;
  dashboardLastUpdated?: string;
  dashboardError?: string;
}

const initialState: IndicatorsState = {
  byIndicator: {},
  dashboardLoading: false,
  dashboardLastUpdated: undefined,
  dashboardError: undefined,
};

export const fetchDashboardThunk = createAsyncThunk<
  { indicators: IndicatorResponse<any>[] },
  void
>('indicators/fetchDashboard', async (_, { rejectWithValue }) => {
  try {
    const payload = await fetchDashboard<{ indicators: IndicatorResponse<any>[] }>();
    return { indicators: payload.indicators };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to fetch dashboard';
    return rejectWithValue({ message });
  }
});

export const fetchIndicatorThunk = createAsyncThunk<
  { indicatorId: string; payload: IndicatorResponse<any> },
  string
>('indicators/fetchById', async (indicatorId: string, { rejectWithValue }) => {
  try {
    const payload = await fetchIndicator<IndicatorResponse<any>>(indicatorId);
    return { indicatorId, payload };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to fetch indicator';
    return rejectWithValue({ indicatorId, message });
  }
});

export const indicatorsSlice = createSlice({
  name: 'indicators',
  initialState,
  reducers: {
    setIndicatorStateOverride: (
      state,
      action: PayloadAction<{ indicatorId: string; panelState: PanelState }>
    ) => {
      const { indicatorId, panelState } = action.payload;
      if (!state.byIndicator[indicatorId]) {
        state.byIndicator[indicatorId] = {
          data: null,
          state: panelState,
        };
      } else {
        state.byIndicator[indicatorId].state = panelState;
      }
    },
  },
  extraReducers: (builder) => {
    // -------------------------------------------------------------
    // Consolidated Dashboard First Paint & Refresh
    // -------------------------------------------------------------
    builder
      .addCase(fetchDashboardThunk.pending, (state) => {
        state.dashboardLoading = true;
        state.dashboardError = undefined;
        const canonicalSlugs = [
          'gdp-growth',
          'debt-to-gdp',
          'trade-balance',
          'gst-collection',
          'inflation',
          'govt-expenditure',
        ];
        for (const slug of canonicalSlugs) {
          if (!state.byIndicator[slug]) {
            state.byIndicator[slug] = { data: null, state: 'loading' };
          }
        }
      })
      .addCase(fetchDashboardThunk.fulfilled, (state, action) => {
        state.dashboardLoading = false;
        state.dashboardLastUpdated = new Date().toISOString();
        state.dashboardError = undefined;

        for (const item of action.payload.indicators) {
          let mappedState: PanelState = 'ok';
          if (item.status === 'stale') {
            mappedState = 'stale';
          } else if (item.status === 'unavailable') {
            mappedState = 'unavailable';
          } else if (!item.series || (Array.isArray(item.series) && item.series.length === 0)) {
            mappedState = 'empty';
          }

          const entry = {
            data: item,
            state: mappedState,
            lastUpdated: new Date().toISOString(),
            error: undefined,
          };

          state.byIndicator[item.id] = entry;
          if (item.id === 'trade') state.byIndicator['trade-balance'] = entry;
          if (item.id === 'gst') state.byIndicator['gst-collection'] = entry;
          if (item.id === 'government-expenditure') state.byIndicator['govt-expenditure'] = entry;
        }
      })
      .addCase(fetchDashboardThunk.rejected, (state, action) => {
        state.dashboardLoading = false;
        const errorMsg = (action.payload as any)?.message || 'Failed to fetch dashboard';
        state.dashboardError = errorMsg;

        // Stale-while-revalidate across all indicators
        for (const key of Object.keys(state.byIndicator)) {
          const entry = state.byIndicator[key];
          if (entry?.data) {
            state.byIndicator[key] = {
              ...entry,
              state: 'stale',
              error: errorMsg,
            };
          } else {
            state.byIndicator[key] = {
              data: null,
              state: 'unavailable',
              error: errorMsg,
            };
          }
        }
      });

    // -------------------------------------------------------------
    // Individual Indicator Panel Refetch
    // -------------------------------------------------------------
    builder
      .addCase(fetchIndicatorThunk.pending, (state, action) => {
        const id = action.meta.arg;
        if (!state.byIndicator[id]) {
          state.byIndicator[id] = { data: null, state: 'loading' };
        }
        // If data exists, keep existing data active during revalidation
      })
      .addCase(fetchIndicatorThunk.fulfilled, (state, action) => {
        const { indicatorId, payload } = action.payload;
        let mappedState: PanelState = 'ok';
        if (payload.status === 'stale') {
          mappedState = 'stale';
        } else if (payload.status === 'unavailable') {
          mappedState = 'unavailable';
        } else if (!payload.series || (Array.isArray(payload.series) && payload.series.length === 0)) {
          mappedState = 'empty';
        }

        const entry = {
          data: payload,
          state: mappedState,
          lastUpdated: new Date().toISOString(),
          error: undefined,
        };

        state.byIndicator[indicatorId] = entry;
        if (indicatorId === 'trade') state.byIndicator['trade-balance'] = entry;
        if (indicatorId === 'gst') state.byIndicator['gst-collection'] = entry;
        if (indicatorId === 'government-expenditure') state.byIndicator['govt-expenditure'] = entry;
      })
      .addCase(fetchIndicatorThunk.rejected, (state, action) => {
        const id = action.meta.arg;
        const existing = state.byIndicator[id];
        const errorMsg = (action.payload as any)?.message || 'Failed to load indicator';

        // Stale-while-revalidate: retain existing data, never blank out
        if (existing?.data) {
          state.byIndicator[id] = {
            ...existing,
            state: 'stale',
            error: errorMsg,
          };
        } else {
          state.byIndicator[id] = {
            data: null,
            state: 'unavailable',
            error: errorMsg,
          };
        }
      });
  },
});

export const { setIndicatorStateOverride } = indicatorsSlice.actions;
export default indicatorsSlice.reducer;
