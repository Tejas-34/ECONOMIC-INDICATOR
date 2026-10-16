import React from 'react';
import { StatTileMetric } from '../../api/types';
import { TileIcon } from './TileIcon';
import styles from './StatTile.module.css';

interface StatTileProps {
  metric: StatTileMetric;
}

export const StatTile: React.FC<StatTileProps> = ({ metric }) => {
  const displayValue =
    metric.value === null || metric.value === undefined
      ? '—'
      : metric.formattedValue || `${metric.value}${metric.unit || ''}`;

  const deltaText =
    metric.delta === null || metric.delta === undefined
      ? null
      : metric.formattedDelta ||
        `${metric.delta > 0 ? '+' : ''}${metric.delta}${metric.deltaUnit || 'pp'}`;

  const isFlag =
    metric.iconKey === 'india' || metric.iconKey === 'us' || metric.iconKey === 'world';

  return (
    <div className={styles.tile} data-testid="stat-tile">
      <div className={styles.contentCol}>
        <div className={styles.labelRow}>
          {isFlag && (
            <div className={styles.iconSlot}>
              <TileIcon iconKey={metric.iconKey} className={styles.flagImg} />
            </div>
          )}
          <span className={styles.label}>{metric.label}</span>
          {metric.sublabel && <span className={styles.sublabel}>{metric.sublabel}</span>}
        </div>

        <div className={styles.valueRow}>
          <span className={styles.value}>{displayValue}</span>
          {deltaText && (
            <span
              className={`${styles.deltaBadge} ${
                metric.deltaDirection === 'negative' ? styles.deltaNegative : styles.deltaPositive
              }`}
            >
              <span aria-hidden="true">▲</span>
              <span>{deltaText}</span>
            </span>
          )}
        </div>
      </div>

      {!isFlag && metric.iconKey && (
        <div className={styles.artSlot}>
          <TileIcon iconKey={metric.iconKey} className={styles.artImg} />
        </div>
      )}
    </div>
  );
};
