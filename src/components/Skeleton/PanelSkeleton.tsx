import React from 'react';
import styles from './PanelSkeleton.module.css';

export const PanelSkeleton: React.FC = () => {
  return (
    <div className={styles.skeletonWrapper} aria-busy="true" aria-label="Loading indicator data">
      <div className={`${styles.pulse} ${styles.titleSkeleton}`} />
      <div className={styles.tilesRowSkeleton}>
        <div className={`${styles.pulse} ${styles.tileSkeleton}`} />
        <div className={`${styles.pulse} ${styles.tileSkeleton}`} />
      </div>
      <div className={`${styles.pulse} ${styles.chartSkeleton}`} />
      <div className={`${styles.pulse} ${styles.footerSkeleton}`} />
    </div>
  );
};
