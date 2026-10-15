import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import styles from './LoginPage.module.css';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const { login, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const searchParams = new URLSearchParams(location.search);
  const sessionExpired = searchParams.get('session_expired') === 'true';
  const from = (location.state as any)?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Invalid analyst credentials');
    }
  };

  const handleFillDemo = () => {
    setEmail('analyst@adityabirla.com');
    setPassword('Analyst@2026');
  };

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginCard}>
        <h1 className={styles.title}>Economic Indicator</h1>
        <p className={styles.subtitle}>Macroeconomic Intelligence Terminal</p>

        {sessionExpired && (
          <div className={styles.sessionExpiredAlert} role="alert">
            Your analyst session has expired. Please sign in again.
          </div>
        )}

        {error && (
          <div className={styles.alertBox} role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.fieldGroup}>
            <label htmlFor="email" className={styles.label}>
              Analyst Email
            </label>
            <input
              id="email"
              type="email"
              required
              className={styles.input}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@adityabirla.com"
            />
          </div>

          <div className={styles.fieldGroup}>
            <label htmlFor="password" className={styles.label}>
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              className={styles.input}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          <button type="submit" disabled={isLoading} className={styles.submitBtn}>
            {isLoading ? 'Verifying...' : 'Sign In'}
          </button>
        </form>

        <div className={styles.demoHelper}>
          <p>Demo analyst credentials:</p>
          <button type="button" className={styles.demoBtn} onClick={handleFillDemo}>
            Fill analyst@adityabirla.com / Analyst@2026
          </button>
        </div>
      </div>
    </div>
  );
};
