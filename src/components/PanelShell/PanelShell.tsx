import React from 'react';
import { PanelState, SourceType } from '../../api/types';
import { SourceFooter } from '../SourceFooter/SourceFooter';
import { StatusBadge } from '../StatusBadge/StatusBadge';
import { PanelSkeleton } from '../Skeleton/PanelSkeleton';
import styles from './PanelShell.module.css';

export interface PanelShellProps {
  id?: string;
  title: string;
  subtitle?: string;
  source: string;
  sourceType: SourceType;
  asOf: string;
  state: PanelState;
  onRetry?: () => void;
  children: React.ReactNode;
}

export const PanelShell: React.FC<PanelShellProps> = ({
  id,
  title,
  subtitle,
  source,
  sourceType,
  asOf,
  state,
  onRetry,
  children,
}) => {
  if (state === 'loading') {
    return (
      <article className={styles.panelCard} id={id} data-testid="panel-loading">
        <div className={styles.glowBlob} aria-hidden="true" />
        <PanelSkeleton />
      </article>
    );
  }

  return (
    <article className={styles.panelCard} id={id} data-testid={`panel-${state}`}>
      {/* Figma Ambient Glow Blobs */}
      <div className={styles.glowTopLeft} aria-hidden="true" />
      <div className={styles.glowBottomRight} aria-hidden="true" />

      {/* Chrome Corner Highlight from Figma */}
      <img
        src="/vector-16250.svg"
        className={styles.chromeCorner}
        alt=""
        aria-hidden="true"
      />

      {/* Frosted Header Bar */}
      <header className={styles.headerBar}>
        <div className={styles.titleArea}>
          <h2 className={styles.title}>{title}</h2>
          {subtitle && <span className={styles.subtitle}>{subtitle}</span>}
        </div>
        <div className={styles.statusContainer}>
          {state === 'stale' && <StatusBadge type="stale" />}
          {state === 'unavailable' && <StatusBadge type="unavailable" />}
        </div>
      </header>

      {/* Content depending on state */}
      <div className={styles.panelBody}>
        {state === 'error' ? (
          <div className={styles.stateOverlay}>
            <p className={styles.errorTitle}>Failed to load indicator data</p>
            <p className={styles.errorMessage}>An unexpected network or service error occurred.</p>
            {onRetry && (
              <button type="button" className={styles.retryButton} onClick={onRetry}>
                Retry Data
              </button>
            )}
          </div>
        ) : state === 'empty' ? (
          <div className={styles.stateOverlay}>
            <p className={styles.infoNotice}>No indicator figures reported for this period.</p>
          </div>
        ) : state === 'unavailable' ? (
          <div className={styles.stateOverlay}>
            <p className={styles.infoNotice}>Upstream data feed is temporarily unavailable.</p>
          </div>
        ) : (
          /* Active or Stale */
          children
        )}
      </div>

      {/* Subtle compact footer */}
      <div className={styles.footerContainer}>
        <SourceFooter source={source} sourceType={sourceType} asOf={asOf} />
      </div>
    </article>
  );
};
