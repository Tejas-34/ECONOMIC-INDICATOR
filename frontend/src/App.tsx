import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { LoginPage } from './auth/LoginPage';
import { Header } from './components/Header/Header';
import { Ticker } from './components/Ticker/Ticker';
import { DashboardGrid } from './panels/DashboardGrid';
import { isMockMode } from './api/client';
import styles from './App.module.css';

const DashboardView: React.FC = () => {
  return (
    <div className={styles.appCanvas}>
      {isMockMode() && (
        <div
          data-testid="mock-data-ribbon"
          style={{
            position: 'fixed',
            top: 12,
            right: 12,
            backgroundColor: '#d97706',
            color: '#ffffff',
            fontWeight: 700,
            fontSize: '11px',
            letterSpacing: '0.08em',
            padding: '4px 10px',
            borderRadius: '4px',
            zIndex: 9999,
            boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
            textTransform: 'uppercase',
            pointerEvents: 'none',
          }}
        >
          MOCK DATA
        </div>
      )}

      {/* 1. Header Banner */}
      <Header />

      {/* 2. Live Market Ticker */}
      <Ticker />

      {/* 3. Six Analytical Panels in 2x3 Grid */}
      <DashboardGrid />
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
