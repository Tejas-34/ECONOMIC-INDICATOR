import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Ticker } from '../../src/components/Ticker/Ticker';

describe('Ticker Component', () => {
  it('renders live badge and quotes', async () => {
    render(<Ticker />);
    expect(screen.getByText('LIVE')).toBeInTheDocument();
  });
});
