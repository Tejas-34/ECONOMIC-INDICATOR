import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Ticker } from '../../src/components/Ticker/Ticker';
import * as tickerHook from '../../src/hooks/useTickerStream';

describe('Ticker Component', () => {
  it('renders LIVE badge and the live blinking dot when market is open', () => {
    vi.spyOn(tickerHook, 'useTickerStream').mockReturnValue({
      quotes: [
        {
          symbol: 'SENSEX',
          currentPrice: 74729.27,
          changePoints: 413.66,
          changePercent: 0.56,
          isPositive: true,
          updatedAt: '2026-10-16T12:00:00Z',
        },
      ],
      marketStatus: 'LIVE',
      lastUpdated: '12:00:00 PM',
      isConnected: true,
      isPollingFallback: false,
      refresh: vi.fn(),
    });

    render(<Ticker />);
    expect(screen.getByText('LIVE')).toBeInTheDocument();
    expect(screen.getByTestId('ticker-live-dot')).toBeInTheDocument();
    expect(screen.getAllByText('SENSEX').length).toBeGreaterThan(0);
    expect(screen.getAllByText('74,729.27 (+0.56%)').length).toBeGreaterThan(0);
  });

  it('renders CLOSED badge and does NOT render the circle dot when market is closed', () => {
    vi.spyOn(tickerHook, 'useTickerStream').mockReturnValue({
      quotes: [
        {
          symbol: 'SENSEX',
          currentPrice: 74729.27,
          changePoints: 413.66,
          changePercent: 0.56,
          isPositive: true,
          updatedAt: '2026-10-16T12:00:00Z',
        },
      ],
      marketStatus: 'CLOSED',
      lastUpdated: '12:00:00 PM',
      isConnected: true,
      isPollingFallback: false,
      refresh: vi.fn(),
    });

    render(<Ticker />);
    expect(screen.getByText('CLOSED')).toBeInTheDocument();
    expect(screen.queryByTestId('ticker-live-dot')).not.toBeInTheDocument();
  });
});
