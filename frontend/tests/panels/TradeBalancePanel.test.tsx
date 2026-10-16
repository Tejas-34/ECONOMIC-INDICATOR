import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TradeBalancePanel } from '../../src/panels/TradeBalancePanel/TradeBalancePanel';
import * as indicatorHook from '../../src/hooks/useIndicatorData';
import { buildTradeBalanceChartOption } from '../../src/panels/TradeBalancePanel/chartOption';

describe('TradeBalancePanel Component', () => {
  const mockTradeData = {
    id: 'trade-balance',
    title: 'Imports, Exports & Trade Balance',
    source: 'Ministry of Commerce and Industry',
    source_type: 'external' as const,
    as_of: 'FY 2024-25',
    status: 'ok' as const,
    values: {
      exports: {
        label: 'Exports',
        value: 382.9,
        formattedValue: '$382.9 B',
        unit: 'US$ B',
        delta: -0.81,
        change: -0.81,
        formattedDelta: '-0.81pp',
        deltaUnit: 'pp',
        deltaDirection: 'negative' as const,
        iconKey: 'exports',
      },
      imports: {
        label: 'Imports',
        value: 382.9,
        formattedValue: '$382.9 B',
        unit: 'US$ B',
        delta: -0.81,
        change: -0.81,
        formattedDelta: '-0.81pp',
        deltaUnit: 'pp',
        deltaDirection: 'negative' as const,
        iconKey: 'imports',
      },
    },
    series: [
      { year: '2021', importsValue: 8.7, exportsValue: 6.3, tradeBalance: 2.8, tradeBalanceLabel: '2.8' },
      { year: '2022', importsValue: 6.3, exportsValue: 4.5, tradeBalance: 2.2, tradeBalanceLabel: '2.2' },
      { year: '2023', importsValue: 8.7, exportsValue: 4.5, tradeBalance: 1.7, tradeBalanceLabel: '1.7' },
      { year: '2024', importsValue: 8.7, exportsValue: 6.3, tradeBalance: 1.1, tradeBalanceLabel: '1.1' },
      { year: '2025', importsValue: 6.8, exportsValue: 4.5, tradeBalance: 0.8, tradeBalanceLabel: '0.8' },
    ],
  };

  it('renders top summary cards for Exports and Imports in billions of USD with pp delta', () => {
    vi.spyOn(indicatorHook, 'useIndicatorData').mockReturnValue({
      data: mockTradeData as any,
      state: 'ok',
      error: null,
      refetch: vi.fn(),
      setPanelState: vi.fn(),
    });

    render(<TradeBalancePanel />);

    expect(screen.getByText('Imports, Exports & Trade Balance')).toBeInTheDocument();
    expect(screen.getByText('Exports')).toBeInTheDocument();
    expect(screen.getByText('Imports')).toBeInTheDocument();
    expect(screen.getAllByText('$382.9 B').length).toBe(2);
    expect(screen.getAllByText('-0.81pp').length).toBe(2);
  });

  it('buildTradeBalanceChartOption scales bars within 0-10% and overlays Trade Balance line', () => {
    // Test with raw billions to ensure proper scaling
    const rawSeries = [
      { year: '2021', importsValue: 760.9, exportsValue: 677.77, tradeBalance: -2.62, tradeBalanceLabel: '-2.62' },
      { year: '2022', importsValue: 866.36, exportsValue: 781.29, tradeBalance: -2.62, tradeBalanceLabel: '-2.62' },
      { year: '2023', importsValue: 839.1, exportsValue: 782.62, tradeBalance: -1.61, tradeBalanceLabel: '-1.61' },
      { year: '2024', importsValue: 897.06, exportsValue: 829.79, tradeBalance: -1.79, tradeBalanceLabel: '-1.79' },
      { year: '2025', importsValue: 949.66, exportsValue: 880.74, tradeBalance: -1.74, tradeBalanceLabel: '-1.74' },
    ];

    const option = buildTradeBalanceChartOption(rawSeries);

    // Y-axis conforms strictly to 0-10% scale
    expect((option.yAxis as any).min).toBe(0);
    expect((option.yAxis as any).max).toBe(10);
    expect((option.yAxis as any).interval).toBe(2);

    const series = option.series as any[];
    const importsBar = series.find((s) => s.name === 'Imports');
    const exportsBar = series.find((s) => s.name === 'Exports');
    const tbLine = series.find((s) => s.name === 'Trade Balance');

    // Values scaled to 0-10%
    expect(importsBar.data).toEqual([7.6, 8.7, 8.4, 9.0, 9.5]);
    expect(exportsBar.data).toEqual([6.8, 7.8, 7.8, 8.3, 8.8]);

    // Trade Balance line overlay
    expect(tbLine.type).toBe('line');
    expect(tbLine.z).toBe(10);
    expect(tbLine.lineStyle.color).toBe('#22D700');
    expect(tbLine.symbolSize).toBe(9);
    // Maps to positive magnitude within 0-10%
    expect(tbLine.data[0].value).toBe(2.6);
    expect(tbLine.data[4].value).toBe(1.7);
  });
});
