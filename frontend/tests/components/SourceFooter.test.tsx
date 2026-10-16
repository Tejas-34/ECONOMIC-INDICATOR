import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SourceFooter } from '../../src/components/SourceFooter/SourceFooter';

describe('SourceFooter Component', () => {
  it('renders source string, external Non-NSE badge, and as-of date', () => {
    render(
      <SourceFooter
        source="Ministry of Statistics and Programme Implementation"
        sourceType="external"
        asOf="Q1 2025"
      />
    );

    expect(screen.getByText('Source:')).toBeInTheDocument();
    expect(screen.getByText('Ministry of Statistics and Programme Implementation')).toBeInTheDocument();
    expect(screen.getByText('Non-NSE')).toBeInTheDocument();
    expect(screen.getByText('Q1 2025')).toBeInTheDocument();
    expect(screen.queryByText(/Estimate/i)).toBeNull();
  });

  it('does not display Non-NSE badge for NSE source type', () => {
    render(
      <SourceFooter
        source="National Stock Exchange"
        sourceType="NSE"
        asOf="Today"
      />
    );

    expect(screen.getByText('National Stock Exchange')).toBeInTheDocument();
    expect(screen.queryByText('Non-NSE')).toBeNull();
  });

  it('renders estimate badge when isEstimate is true', () => {
    render(
      <SourceFooter
        source="Ministry of Finance, Budget Division"
        sourceType="external"
        asOf="FY 2024-25"
        isEstimate={true}
      />
    );

    expect(screen.getByText(/Estimate/i)).toBeInTheDocument();
  });

  it('renders estimate badge when asOf contains RE or BE', () => {
    render(
      <SourceFooter
        source="Ministry of Finance"
        sourceType="external"
        asOf="FY 2024-25 RE"
      />
    );

    expect(screen.getByText(/Estimate/i)).toBeInTheDocument();
  });
});
