import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { TickerQuote } from '../../api/types';

interface TickerState {
  quotes: TickerQuote[];
  lastUpdated: string | null;
}

const initialState: TickerState = {
  quotes: [],
  lastUpdated: null,
};

export const tickerSlice = createSlice({
  name: 'ticker',
  initialState,
  reducers: {
    updateQuotes: (state, action: PayloadAction<TickerQuote[]>) => {
      state.quotes = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
  },
});

export const { updateQuotes } = tickerSlice.actions;
export default tickerSlice.reducer;
