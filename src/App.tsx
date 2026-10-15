import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { LoginPage } from './auth/LoginPage';
import { Header } from './components/Header/Header';
import { Ticker } from './components/Ticker/Ticker';
import { DashboardGrid } from './panels/DashboardGrid';
import { PanelState } from './api/types';
import styles from './App.module.css';

const DashboardView: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeSimulation, setActiveSimulation] = useState<PanelState | 'normal'>('normal');

  const stateOverrides: Record<string, PanelState> = {};
  if (activeSimulation !== 'normal') {
    stateOverrides['gdp-growth'] = activeSimulation;
    stateOverrides['debt-to-gdp'] = activeSimulation;
    stateOverrides['trade-balance'] = activeSimulation;
    stateOverrides['gst-collection'] = activeSimulation;
    stateOverrides['inflation'] = activeSimulation;
    stateOverrides['govt-expenditure'] = activeSimulation;
  }

  return (
    <div className={styles.appCanvas}>
      {/* 1. Header Banner */}
      <Header />

      {/* 2. Live Market Ticker */}
      <Ticker />

      {/* 3. Six Analytical Panels in 2x3 Grid */}
      <DashboardGrid stateOverrides={stateOverrides} />

      {/* Floating Analyst & Demonstration Controls Bar */}
      <aside className={styles.floatingToolbar} aria-label="Analyst and Evaluation Controls">
        <div className={styles.analystInfo}>
          <span>
            Analyst: <b>{user?.name || 'Macro Analyst'}</b>
          </span>
        </div>
        <div className={styles.simulatorButtonGroup}>
          {(['normal', 'loading', 'stale', 'empty', 'unavailable', 'error'] as const).map((st) => (
            <button
              key={st}
              type="button"
              className={`${styles.simBtn} ${activeSimulation === st ? styles.simBtnActive : ''}`}
              onClick={() => setActiveSimulation(st)}
            >
              {st.toUpperCase()}
            </button>
          ))}
        </div>
        <button type="button" className={styles.signOutBtn} onClick={logout}>
          Sign Out
        </button>
      </aside>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardView />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
