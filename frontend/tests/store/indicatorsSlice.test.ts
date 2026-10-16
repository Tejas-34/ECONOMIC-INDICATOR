import { describe, it, expect } from 'vitest';
import indicatorsReducer, {
  fetchDashboardThunk,
  fetchIndicatorThunk,
  setIndicatorStateOverride,
  IndicatorsState,
} from '../../src/store/slices/indicatorsSlice';

describe('indicatorsSlice Reducer', () => {
  const initial: IndicatorsState = {
    byIndicator: {},
    dashboardLoading: false,
    dashboardLastUpdated: undefined,
    dashboardError: undefined,
  };

  it('handles fetchDashboardThunk.fulfilled by populating indicators', () => {
    const mockIndicators = [
      {
        id: 'gdp-growth',
        title: 'GDP Growth',
        as_of: 'Q1 2025',
        status: 'ok',
        source: 'MoSPI',
        source_type: 'external' as const,
        values: {},
        series: [{ period: '2024', value: 7.2 }],
      },
      {
        id: 'debt-to-gdp',
        title: 'Debt to GDP',
        as_of: '2024',
        status: 'stale',
        source: 'IMF',
        source_type: 'external' as const,
        values: {},
        series: [{ period: '2024', value: 82.5 }],
      },
    ];

    const state = indicatorsReducer(
      initial,
      fetchDashboardThunk.fulfilled({ indicators: mockIndicators as any }, 'request-id')
    );

    expect(state.dashboardLoading).toBe(false);
    expect(state.dashboardLastUpdated).toBeDefined();
    expect(state.byIndicator['gdp-growth'].state).toBe('ok');
    expect(state.byIndicator['gdp-growth'].data?.id).toBe('gdp-growth');
    expect(state.byIndicator['debt-to-gdp'].state).toBe('stale');
  });

  it('preserves existing data as stale when fetchIndicatorThunk fails (stale-while-revalidate)', () => {
    const stateWithData: IndicatorsState = {
      byIndicator: {
        'gdp-growth': {
          data: {
            id: 'gdp-growth',
            title: 'GDP Growth',
            as_of: 'Q1 2025',
            status: 'ok',
            source: 'MoSPI',
            source_type: 'external' as const,
            values: {} as any,
            series: [{ period: '2024', value: 7.2 }],
          },
          state: 'ok',
          lastUpdated: '2026-10-16T00:00:00Z',
        },
      },
      dashboardLoading: false,
      dashboardLastUpdated: '2026-10-16T00:00:00Z',
    };

    const action = fetchIndicatorThunk.rejected(
      new Error('500 Server Error'),
      'req-1',
      'gdp-growth',
      { indicatorId: 'gdp-growth', message: 'Network Failure' }
    );

    const nextState = indicatorsReducer(stateWithData, action);

    // Stale-while-revalidate expectation:
    // Existing data is NOT null, state is marked stale, never blanking the panel
    expect(nextState.byIndicator['gdp-growth'].data).not.toBeNull();
    expect(nextState.byIndicator['gdp-growth'].data?.id).toBe('gdp-growth');
    expect(nextState.byIndicator['gdp-growth'].state).toBe('stale');
    expect(nextState.byIndicator['gdp-growth'].error).toBe('Network Failure');
  });

  it('marks panel as unavailable when initial fetch fails with no prior data', () => {
    const action = fetchIndicatorThunk.rejected(
      new Error('500 Server Error'),
      'req-1',
      'inflation',
      { indicatorId: 'inflation', message: 'Backend unreachable' }
    );

    const nextState = indicatorsReducer(initial, action);

    expect(nextState.byIndicator['inflation'].data).toBeNull();
    expect(nextState.byIndicator['inflation'].state).toBe('unavailable');
    expect(nextState.byIndicator['inflation'].error).toBe('Backend unreachable');
  });

  it('allows manual override of indicator state', () => {
    const state = indicatorsReducer(
      initial,
      setIndicatorStateOverride({ indicatorId: 'trade-balance', panelState: 'stale' })
    );

    expect(state.byIndicator['trade-balance'].state).toBe('stale');
  });
});
