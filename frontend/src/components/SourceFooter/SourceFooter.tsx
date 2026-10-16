import React from 'react';
import { SourceType } from '../../api/types';
import styles from './SourceFooter.module.css';

interface SourceFooterProps {
  source: string;
  sourceType: SourceType;
  asOf: string;
}

export const SourceFooter: React.FC<SourceFooterProps> = ({ source, sourceType, asOf }) => {
  return (
    <footer className={styles.footer} aria-label="Data provenance and reporting date">
      <div className={styles.sourceInfo}>
        <span>Source:</span>
        <span className={styles.sourceLabel} title={source}>
          {source}
        </span>
        {sourceType === 'external' && (
          <span className={styles.externalBadge} title="Non-NSE data provider">
            Non-NSE
          </span>
        )}
      </div>
      <div className={styles.asOfDate}>
        <span>As of: </span>
        <span>{asOf}</span>
      </div>
    </footer>
  );
};
