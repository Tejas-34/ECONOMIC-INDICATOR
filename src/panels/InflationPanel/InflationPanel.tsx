import React, { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import { echarts } from '../echartsSetup';
import { PanelShell } from '../../components/PanelShell/PanelShell';
import { useIndicatorData } from '../../hooks/useIndicatorData';
import { InflationValues, InflationSeries, PanelState, StatTileMetric } from '../../api/types';
import { buildInflationChartOption } from './chartOption';
import styles from './InflationPanel.module.css';

interface InflationPanelProps {
  initialStateOverride?: PanelState;
}

interface InflationSummaryCardProps {
  metric: StatTileMetric;
  variant: 'rate' | 'target';
  illustrationSrc: string;
}

const InflationSummaryCard: React.FC<InflationSummaryCardProps> = ({
  metric,
  variant,
  illustrationSrc,
}) => {
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
    <div
      className={`${styles.summaryCard} ${
        variant === 'rate' ? styles.rateCard : styles.targetCard
      }`}
      data-testid="stat-tile"
    >
      <div className={styles.cardGlow} aria-hidden="true" />

      <div className={styles.cardContent}>
        <div className={styles.cardLabel}>{metric.label}</div>
        <div className={styles.cardValue}>{displayValue}</div>
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

      <img
        src={illustrationSrc}
        alt=""
        aria-hidden="true"
        className={`${styles.illustration} ${
          variant === 'rate' ? styles.rateIllustration : styles.targetIllustration
        }`}
      />
    </div>
  );
};

export const InflationPanel: React.FC<InflationPanelProps> = ({ initialStateOverride }) => {
  const { data, state, refetch } = useIndicatorData<InflationValues>(
    'inflation',
    initialStateOverride
  );

  const chartOption = useMemo(
    () => buildInflationChartOption((data?.series || []) as InflationSeries),
    [data?.series]
  );

  return (
    <PanelShell
      id="panel-inflation"
      title={data?.title || 'Inflation'}
      subtitle={data?.subtitle || '(IND)'}
      source={data?.source || 'Reserve Bank of India (RBI)'}
      sourceType={data?.source_type || 'external'}
      asOf={data?.as_of || 'August 2025'}
      state={state}
      onRetry={refetch}
    >
      {data?.values && (
        <div className={styles.tilesRow}>
          <InflationSummaryCard
            metric={data.values.inflationRate}
            variant="rate"
            illustrationSrc="/image-9590.png"
          />
          <InflationSummaryCard
            metric={data.values.rbiTarget}
            variant="target"
            illustrationSrc="/rbi-target-3d.png"
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
