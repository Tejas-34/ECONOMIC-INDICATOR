import React from 'react';
import styles from './StatusBadge.module.css';

export type BadgeType = 'live' | 'stale' | 'unavailable';

interface StatusBadgeProps {
  type: BadgeType;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, label }) => {
  if (type === 'live') {
    return (
      <span className={`${styles.badge} ${styles.live}`} aria-label="Live updates active">
        <span className={styles.liveDot} aria-hidden="true" />
        {label || 'LIVE'}
      </span>
    );
  }

  if (type === 'stale') {
    return (
      <span
        className={`${styles.badge} ${styles.stale}`}
        title="Data is older than standard threshold"
      >
        {label || 'STALE'}
      </span>
    );
  }

  return <span className={`${styles.badge} ${styles.unavailable}`}>{label || 'UNAVAILABLE'}</span>;
};
