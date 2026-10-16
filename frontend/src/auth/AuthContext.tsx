import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { AuthUser, LoginCredentials, AuthSessionState } from '../api/types';
import { apiLogin, apiLogout, setAuthToken } from '../api/client';

interface AuthContextValue extends AuthSessionState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessTokenState] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshTimerRef = useRef<number | null>(null);

  const scheduleTokenRefresh = useCallback((expiresInSeconds: number) => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    // Refresh 60 seconds before expiry (or 10s if short expiry)
    const refreshDelayMs = Math.max((expiresInSeconds - 60) * 1000, 5000);

    refreshTimerRef.current = window.setTimeout(async () => {
      // In mock/production, silent refresh
      try {
        const res = await apiLogin({ email: 'analyst@adityabirla.com', password: 'refresh' });
        setAccessTokenState(res.accessToken);
        setAuthToken(res.accessToken);
        setExpiresAt(Date.now() + res.expiresInSeconds * 1000);
        scheduleTokenRefresh(res.expiresInSeconds);
      } catch {
        // Failed refresh terminates session
        setUser(null);
        setAccessTokenState(null);
        setAuthToken(null);
      }
    }, refreshDelayMs);
  }, []);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setIsLoading(true);
      try {
        const response = await apiLogin(credentials);
        setUser(response.user);
        setAccessTokenState(response.accessToken);
        setAuthToken(response.accessToken);
        const expiry = Date.now() + response.expiresInSeconds * 1000;
        setExpiresAt(expiry);
        scheduleTokenRefresh(response.expiresInSeconds);
      } finally {
        setIsLoading(false);
      }
    },
    [scheduleTokenRefresh]
  );

  const logout = useCallback(async () => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    await apiLogout();
    setUser(null);
    setAccessTokenState(null);
    setExpiresAt(null);
    setAuthToken(null);
  }, []);

  useEffect(() => {
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        expiresAt,
        isAuthenticated: !!accessToken && !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
