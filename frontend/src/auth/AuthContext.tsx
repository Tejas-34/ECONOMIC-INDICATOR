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

  const expiryTimerRef = useRef<number | null>(null);

  // 60-minute countdown session expiry timer (I3 - no refresh token)
  const startSessionExpiryTimer = useCallback((expiresInSeconds: number) => {
    if (expiryTimerRef.current) clearTimeout(expiryTimerRef.current);
    const delayMs = Math.max(expiresInSeconds * 1000, 1000);

    expiryTimerRef.current = window.setTimeout(() => {
      setUser(null);
      setAccessTokenState(null);
      setExpiresAt(null);
      setAuthToken(null);
      if (typeof window !== 'undefined' && window.location) {
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login?session_expired=true';
        }
      }
    }, delayMs);
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
        startSessionExpiryTimer(response.expiresInSeconds);
      } finally {
        setIsLoading(false);
      }
    },
    [startSessionExpiryTimer]
  );

  const logout = useCallback(async () => {
    if (expiryTimerRef.current) {
      clearTimeout(expiryTimerRef.current);
      expiryTimerRef.current = null;
    }
    await apiLogout();
    setUser(null);
    setAccessTokenState(null);
    setExpiresAt(null);
    setAuthToken(null);
  }, []);

  useEffect(() => {
    return () => {
      if (expiryTimerRef.current) clearTimeout(expiryTimerRef.current);
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
