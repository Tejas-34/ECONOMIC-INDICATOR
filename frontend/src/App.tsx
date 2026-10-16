import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { LoginPage } from './auth/LoginPage';
import { Header } from './components/Header/Header';
import { Ticker } from './components/Ticker/Ticker';
import { DashboardGrid } from './panels/DashboardGrid';
import styles from './App.module.css';

const DashboardView: React.FC = () => {
  return (
    <div className={styles.appCanvas}>
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
