import { describe, it, expect } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useIndicatorData } from '../../src/hooks/useIndicatorData';

describe('useIndicatorData Hook', () => {
  it('loads indicator data and resolves to ok state', async () => {
    const { result } = renderHook(() => useIndicatorData('gdp-growth'));
    
    expect(result.current.state).toBe('loading');

    await waitFor(() => {
      expect(result.current.state).toBe('ok');
    });

    expect(result.current.data?.id).toBe('gdp-growth');
    expect(result.current.error).toBeNull();
  });

  it('allows manual override of panel state', async () => {
    const { result } = renderHook(() => useIndicatorData('gdp-growth'));

    await waitFor(() => {
      expect(result.current.state).toBe('ok');
    });

    act(() => {
      result.current.setPanelState('stale');
    });

    expect(result.current.state).toBe('stale');
  });
});
