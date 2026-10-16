import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DebtToGdpPanel } from '../../src/panels/DebtToGdpPanel/DebtToGdpPanel';
import * as indicatorHook from '../../src/hooks/useIndicatorData';
import { buildDebtChartOption } from '../../src/panels/DebtToGdpPanel/chartOption';

describe('DebtToGdpPanel Component', () => {
  const mockDebtData = {
    id: 'debt-to-gdp',
    title: 'Debt to GDP Ratio',
    subtitle: '(IND)',
    source: 'International Monetary Fund DataMapper',
    source_type: 'external' as const,
    as_of: '2025',
    status: 'ok' as const,
    values: {
      indiaFy25: {
        label: 'India (FY25)',
        value: 84.3,
        formattedValue: '84.3%',
        unit: '%',
        delta: -0.5,
        change: -0.5,
        formattedDelta: '-0.5pp',
        deltaUnit: 'pp',
        deltaDirection: 'negative' as const,
        iconKey: 'india',
      },
      indVsUs: {
        label: 'Ind vs US',
        value: -40.1,
        formattedValue: '-40.1%',
        unit: 'pp',
        delta: -2.6,
        change: -2.6,
        formattedDelta: '-2.6pp',
        deltaUnit: 'pp',
        deltaDirection: 'negative' as const,
        iconKey: 'us',
      },
    },
    series: [
      { date: '2021', ratio: 85.5 },
      { date: '2022', ratio: 84.4 },
      { date: '2023', ratio: 84.7, isHighlighted: true, highlightLabel: '84.7%' },
      { date: '2024', ratio: 84.8 },
      { date: '2025', ratio: 84.3, isHighlighted: true, highlightLabel: '84.3%' },
    ],
  };

  it('renders the two summary cards with India 84.3% (-0.5pp) and Ind vs US -40.1% (-2.6pp)', () => {
    vi.spyOn(indicatorHook, 'useIndicatorData').mockReturnValue({
      data: mockDebtData as any,
      state: 'ok',
      error: null,
      refetch: vi.fn(),
      setPanelState: vi.fn(),
    });

    render(<DebtToGdpPanel />);

    // Header & provenance
    expect(screen.getByText('Debt to GDP Ratio')).toBeInTheDocument();
    expect(screen.getByText('International Monetary Fund DataMapper')).toBeInTheDocument();
    expect(screen.getByText('2025')).toBeInTheDocument();

    // Summary Card 1: India (FY25)
    expect(screen.getByText('India (FY25)')).toBeInTheDocument();
    expect(screen.getByText('84.3%')).toBeInTheDocument();
    expect(screen.getByText('-0.5pp')).toBeInTheDocument();

    // Summary Card 2: Ind vs US
    expect(screen.getByText('Ind vs US')).toBeInTheDocument();
    expect(screen.getByText('-40.1%')).toBeInTheDocument();
    expect(screen.getByText('-2.6pp')).toBeInTheDocument();
  });

  it('buildDebtChartOption configures annual line chart for 2021-2025 with Figma specs', () => {
    const option = buildDebtChartOption(mockDebtData.series);

    // X-axis has all 5 annual categories
    expect((option.xAxis as any).data).toEqual(['2021', '2022', '2023', '2024', '2025']);

    // Y-axis conforms to Figma 50-100% scale
    expect((option.yAxis as any).min).toBe(50);
    expect((option.yAxis as any).max).toBe(100);
    expect((option.yAxis as any).interval).toBe(10);

    // Series line configuration
    const series = (option.series as any[])[0];
    expect(series.type).toBe('line');
    expect(series.data).toEqual([85.5, 84.4, 84.7, 84.8, 84.3]);
    expect(series.lineStyle.color).toBe('#00D2FF');
    expect(series.showSymbol).toBe(true);

    // Mark lines for all 5 years
    expect(series.markLine.data).toEqual([
      { xAxis: '2021' },
      { xAxis: '2022' },
      { xAxis: '2023' },
      { xAxis: '2024' },
      { xAxis: '2025' },
    ]);
  });
});
