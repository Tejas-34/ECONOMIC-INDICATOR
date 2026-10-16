import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GstCollectionPanel } from '../../src/panels/GstCollectionPanel/GstCollectionPanel';
import * as indicatorHook from '../../src/hooks/useIndicatorData';
import { buildGstChartOption } from '../../src/panels/GstCollectionPanel/chartOption';

describe('GstCollectionPanel Component', () => {
  const mockGstData = {
    id: 'gst-collection',
    title: 'GST Tax Collection',
    subtitle: '(₹ Lakh Cr)',
    source: 'data.gov.in (Rajya Sabha)',
    source_type: 'external' as const,
    as_of: '2024-25',
    status: 'ok' as const,
    values: {
      collections: {
        label: 'GST Collections',
        value: 16.34,
        formattedValue: '₹16.34L Cr',
        unit: 'Rs lakh crore',
        delta: 11.65,
        change: 11.65,
        formattedDelta: '+11.6%',
        deltaUnit: '%',
        deltaDirection: 'positive' as const,
        iconKey: 'gst',
      },
      monthlyAverage: {
        label: 'Monthly Average',
        value: 1.63,
        formattedValue: '₹1.63L Cr',
        unit: 'Rs lakh crore',
        delta: 0.17,
        change: 0.17,
        formattedDelta: '+11.6%',
        deltaUnit: '%',
        deltaDirection: 'positive' as const,
        iconKey: 'coins',
      },
    },
    series: [
      { year: '2021', collectionRate: 8.66, averageRate: 2.71, domestic: 8.66, imports: 2.71, totalCollection: 11.37, highlightLabel: '₹2.71L Cr' },
      { year: '2022', collectionRate: 10.98, averageRate: 3.86, domestic: 10.98, imports: 3.86, totalCollection: 14.83, highlightLabel: '₹3.86L Cr' },
      { year: '2023', collectionRate: 13.25, averageRate: 4.83, domestic: 13.25, imports: 4.83, totalCollection: 18.08, highlightLabel: '₹4.83L Cr' },
      { year: '2024', collectionRate: 15.23, averageRate: 4.95, domestic: 15.23, imports: 4.95, totalCollection: 20.18, highlightLabel: '₹4.95L Cr' },
      { year: '2025', collectionRate: 12.37, averageRate: 3.96, domestic: 12.37, imports: 3.96, totalCollection: 16.34, highlightLabel: '₹3.96L Cr' },
    ],
  };

  it('renders summary cards with accurate data.gov.in Lakh Cr numbers and proper labels', () => {
    vi.spyOn(indicatorHook, 'useIndicatorData').mockReturnValue({
      data: mockGstData as any,
      state: 'ok',
      error: null,
      refetch: vi.fn(),
      setPanelState: vi.fn(),
    });

    render(<GstCollectionPanel />);

    expect(screen.getByText('GST Tax Collection')).toBeInTheDocument();
    expect(screen.getByText('(₹ Lakh Cr)')).toBeInTheDocument();
    expect(screen.getByText('data.gov.in (Rajya Sabha)')).toBeInTheDocument();
    expect(screen.getByText('2024-25')).toBeInTheDocument();

    expect(screen.getByText('GST Collections')).toBeInTheDocument();
    expect(screen.getByText('₹16.34L Cr')).toBeInTheDocument();

    expect(screen.getByText('Monthly Average')).toBeInTheDocument();
    expect(screen.getByText('₹1.63L Cr')).toBeInTheDocument();
  });

  it('buildGstChartOption configures Domestic bars and Imports line with data.gov.in specifications', () => {
    const option = buildGstChartOption(mockGstData.series);

    expect((option.xAxis as any).data).toEqual(['2021', '2022', '2023', '2024', '2025']);

    // Check legend specifies Domestic and Imports (NO "Trade Balance")
    const legendData = (option.legend as any).data;
    expect(legendData).toEqual([
      { name: 'Domestic', icon: 'roundRect' },
      { name: 'Imports' },
    ]);

    // Check series
    const series = option.series as any[];
    const domBar = series.find((s) => s.name === 'Domestic');
    const impLine = series.find((s) => s.name === 'Imports');

    expect(domBar).toBeDefined();
    expect(domBar.type).toBe('bar');
    expect(domBar.data).toEqual([8.66, 10.98, 13.25, 15.23, 12.37]);

    expect(impLine).toBeDefined();
    expect(impLine.type).toBe('line');
    expect(impLine.data).toEqual([2.71, 3.86, 4.83, 4.95, 3.96]);

    // Check Y-axis
    expect((option.yAxis as any).min).toBe(0);
    expect((option.yAxis as any).max).toBe(18);
  });
});
