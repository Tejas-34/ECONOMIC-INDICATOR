import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { fetchIndicator } from '../../api/client';
import { IndicatorResponse, PanelState } from '../../api/types';

interface IndicatorEntry {
  data: IndicatorResponse<any> | null;
  state: PanelState;
  error?: string;
  lastUpdated?: string;
}

interface IndicatorsState {
  byIndicator: Record<string, IndicatorEntry>;
}

const initialState: IndicatorsState = {
  byIndicator: {},
};

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
    builder
      .addCase(fetchIndicatorThunk.pending, (state, action) => {
        const id = action.meta.arg;
        if (!state.byIndicator[id]) {
          state.byIndicator[id] = { data: null, state: 'loading' };
        } else {
          state.byIndicator[id].state = 'loading';
        }
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

        state.byIndicator[indicatorId] = {
          data: payload,
          state: mappedState,
          lastUpdated: new Date().toISOString(),
        };
      })
      .addCase(fetchIndicatorThunk.rejected, (state, action) => {
        const id = action.meta.arg;
        state.byIndicator[id] = {
          data: null,
          state: 'unavailable',
          error: (action.payload as any)?.message || 'Failed to load indicator',
        };
      });
  },
});

export const { setIndicatorStateOverride } = indicatorsSlice.actions;
export default indicatorsSlice.reducer;
