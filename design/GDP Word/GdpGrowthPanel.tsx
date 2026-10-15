import React, { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import { echarts } from '../echartsSetup';
import { PanelShell } from '../../components/PanelShell/PanelShell';
import { useIndicatorData } from '../../hooks/useIndicatorData';
import { GdpGrowthValues, GdpGrowthSeries, PanelState, StatTileMetric } from '../../api/types';
import { buildGdpChartOption } from './chartOption';
import styles from './GdpGrowthPanel.module.css';

interface GdpGrowthPanelProps {
  initialStateOverride?: PanelState;
}

interface GdpSummaryCardProps {
  metric: StatTileMetric;
  variant: 'india' | 'world';
  iconSrc: string;
}

const GdpSummaryCard: React.FC<GdpSummaryCardProps> = ({ metric, variant, iconSrc }) => {
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
        variant === 'india' ? styles.indiaCard : styles.worldCard
      }`}
      data-testid="stat-tile"
    >
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

export const GdpGrowthPanel: React.FC<GdpGrowthPanelProps> = ({ initialStateOverride }) => {
  const { data, state, refetch } = useIndicatorData<GdpGrowthValues>(
    'gdp-growth',
    initialStateOverride
  );

  const chartOption = useMemo(
    () => buildGdpChartOption((data?.series || []) as GdpGrowthSeries),
    [data?.series]
  );

  return (
    <PanelShell
      id="panel-gdp-growth"
      title={data?.title || 'GDP Growth - India vs World'}
      subtitle={data?.subtitle || '(YOY%)'}
      source={data?.source || 'MoSPI'}
      sourceType={data?.source_type || 'external'}
      asOf={data?.as_of || 'Q1 2025'}
      state={state}
      onRetry={refetch}
    >
      {data?.values && (
        <div className={styles.tilesRow}>
          <GdpSummaryCard
            metric={data.values.india}
            variant="india"
            iconSrc="/image-9450.png"
          />
          <GdpSummaryCard
            metric={data.values.world}
            variant="world"
            iconSrc="/image-9510.png"
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
