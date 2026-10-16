import React, { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import { echarts } from '../echartsSetup';
import { PanelShell } from '../../components/PanelShell/PanelShell';
import { useIndicatorData } from '../../hooks/useIndicatorData';
import { DebtToGdpValues, DebtToGdpSeries, PanelState, StatTileMetric } from '../../api/types';
import { buildDebtChartOption } from './chartOption';
import styles from './DebtToGdpPanel.module.css';

interface DebtToGdpPanelProps {
  initialStateOverride?: PanelState;
}

interface DebtSummaryCardProps {
  metric: StatTileMetric;
  iconSrc: string;
}

const DebtSummaryCard: React.FC<DebtSummaryCardProps> = ({ metric, iconSrc }) => {
  const displayValue =
    metric.value === null || metric.value === undefined
      ? '—'
      : metric.formattedValue || `${metric.value}%`;

  const deltaText =
    metric.delta === null || metric.delta === undefined
      ? null
      : metric.formattedDelta ||
        `${metric.delta > 0 ? '+' : ''}${metric.delta}${metric.deltaUnit || 'pp'}`;

  return (
    <div className={styles.summaryCard} data-testid="stat-tile">
      <div className={styles.cardTopRow}>
        <img src={iconSrc} alt={metric.label} className={styles.cardIcon} />
        <span className={styles.cardLabel}>{metric.label}</span>
      </div>

      <div className={styles.cardBottomRow}>
        <span className={styles.cardValue}>{displayValue}</span>
        {deltaText && (
          <div className={styles.deltaPill}>
            <svg
              className={styles.deltaTriangle}
              viewBox="0 0 14 15"
              fill="none"
              aria-hidden="true"
            >
              <path d="M7 1L13.5 13.5H0.5L7 1Z" fill="#45FF5B" />
            </svg>
            <span className={styles.deltaText}>{deltaText}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export const DebtToGdpPanel: React.FC<DebtToGdpPanelProps> = ({ initialStateOverride }) => {
  const { data, state, refetch } = useIndicatorData<DebtToGdpValues>(
    'debt-to-gdp',
    initialStateOverride
  );

  const chartOption = useMemo(
    () => buildDebtChartOption((data?.series || []) as DebtToGdpSeries),
    [data?.series]
  );

  return (
    <PanelShell
      id="panel-debt-to-gdp"
      title={data?.title || 'Debt to GDP Ratio'}
      subtitle={data?.subtitle || '(IND)'}
      source={data?.source || 'Reserve Bank of India (RBI)'}
      sourceType={data?.source_type || 'external'}
      asOf={data?.as_of || '22 Aug 2025'}
      state={state}
      onRetry={refetch}
    >
      {data?.values && (
        <div className={styles.tilesRow}>
          <DebtSummaryCard
            metric={data.values.indiaFy25}
            iconSrc="/india-flag-clean.png"
          />
          <DebtSummaryCard
            metric={data.values.indVsUs}
            iconSrc="/us-flag-clean.png"
          />
        </div>
      )}

      <div className={styles.chartContainer}>
        <ReactEChartsCore
          echarts={echarts}
          option={chartOption}
          notMerge={true}
          lazyUpdate={true}
          style={{ height: '100%', width: '100%' }}
        />
      </div>
    </PanelShell>
  );
};
