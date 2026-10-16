import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatTile } from '../../src/components/StatTile/StatTile';
import { StatTileMetric } from '../../src/api/types';

describe('StatTile Component', () => {
  it('renders metric label, formatted value and delta', () => {
    const metric: StatTileMetric = {
      label: 'India',
      value: 4.82,
      formattedValue: '4.82%',
      delta: -0.2,
      formattedDelta: '-0.2pp',
      deltaDirection: 'negative',
      iconKey: 'india',
    };

    render(<StatTile metric={metric} />);
    expect(screen.getByText('India')).toBeInTheDocument();
    expect(screen.getByText('4.82%')).toBeInTheDocument();
    expect(screen.getByText('-0.2pp')).toBeInTheDocument();
  });

  it('renders em-dash "—" when value is null or missing', () => {
    const metric: StatTileMetric = {
      label: 'World',
      value: null,
      delta: null,
      deltaDirection: 'neutral',
    };

    render(<StatTile metric={metric} />);
    expect(screen.getByText('World')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();
  });
});
