import React from 'react';
import styles from './Header.module.css';

interface HeaderProps {
  title?: string;
}

export const Header: React.FC<HeaderProps> = ({ title = 'ECONOMIC INDICATOR' }) => {
  return (
    <header className={styles.headerContainer} role="banner">
      <div className={styles.candlestickOverlay} aria-hidden="true" />
      <h1 className={styles.title}>{title}</h1>
    </header>
  );
};
