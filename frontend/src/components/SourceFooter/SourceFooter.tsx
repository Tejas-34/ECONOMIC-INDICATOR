import React from 'react';
import { SourceType } from '../../api/types';
import styles from './SourceFooter.module.css';

export interface SourceFooterProps {
  source: string;
  sourceType: SourceType;
  asOf: string;
  isEstimate?: boolean;
}

export const SourceFooter: React.FC<SourceFooterProps> = ({
  source,
  sourceType,
  asOf,
  isEstimate = false,
}) => {
  const isEstimated =
    isEstimate ||
    (asOf && (asOf.includes('RE') || asOf.includes('BE') || asOf.toLowerCase().includes('estimate')));

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
        {isEstimated && (
          <span className={styles.estimateBadge} title="Budget / Revised Estimate">
            Estimate
          </span>
        )}
        <span>As of: </span>
        <span>{asOf}</span>
      </div>
    </footer>
  );
};

