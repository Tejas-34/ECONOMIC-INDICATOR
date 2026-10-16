import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from '../../src/auth/AuthContext';
import { LoginPage } from '../../src/auth/LoginPage';
import * as client from '../../src/api/client';

const TestAuthConsumer: React.FC = () => {
  const { user, isAuthenticated, login } = useAuth();
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'authenticated' : 'unauthenticated'}</div>
      <div data-testid="user-role">{user?.role}</div>
      <button
        onClick={() =>
          login({ email: 'analyst@adityabirla.com', password: 'password123' })
        }
      >
        Trigger Login
      </button>
    </div>
  );
};

describe('AuthContext and Session Expiry', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('authenticates with aligned role and terminates session when countdown timer expires', async () => {
    vi.spyOn(client, 'apiLogin').mockResolvedValueOnce({
      user: {
        id: 'usr_1',
        email: 'analyst@adityabirla.com',
        name: 'Analyst',
        role: 'admin',
      },
      accessToken: 'token_123',
      expiresInSeconds: 3600, // 60 minutes
    });

    render(
      <AuthProvider>
        <TestAuthConsumer />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');

    // Trigger login
    await act(async () => {
      screen.getByText('Trigger Login').click();
    });

    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    expect(screen.getByTestId('user-role')).toHaveTextContent('admin');

    // Fast-forward 59 minutes: should still be authenticated
    act(() => {
      vi.advanceTimersByTime(59 * 60 * 1000);
    });
    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');

    // Fast-forward past 60 minutes: session terminates automatically
    act(() => {
      vi.advanceTimersByTime(2 * 60 * 1000);
    });
    expect(screen.getByTestId('auth-status')).toHaveTextContent('unauthenticated');
  });

  it('LoginPage displays session expired alert when session_expired query param is present', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/login?session_expired=true']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    expect(
      screen.getByText('Your analyst session has expired. Please sign in again.')
    ).toBeInTheDocument();
  });
});
