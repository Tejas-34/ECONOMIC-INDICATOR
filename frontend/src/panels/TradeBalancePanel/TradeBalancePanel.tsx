import React, { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import { echarts } from '../echartsSetup';
import { PanelShell } from '../../components/PanelShell/PanelShell';
import { useIndicatorData } from '../../hooks/useIndicatorData';
import { TradeBalanceValues, TradeBalanceSeries, PanelState, StatTileMetric } from '../../api/types';
import { buildTradeBalanceChartOption } from './chartOption';
import styles from './TradeBalancePanel.module.css';

interface TradeBalancePanelProps {
  initialStateOverride?: PanelState;
}

interface TradeSummaryCardProps {
  metric: StatTileMetric;
  variant: 'exports' | 'imports';
  illustrationSrc: string;
}

const TradeSummaryCard: React.FC<TradeSummaryCardProps> = ({
  metric,
  variant,
  illustrationSrc,
}) => {
  const displayValue =
    metric.value === null || metric.value === undefined
      ? '—'
      : metric.formattedValue || `$${metric.value} B`;

  const deltaText =
    metric.delta === null || metric.delta === undefined
      ? null
      : metric.formattedDelta ||
        `${metric.delta > 0 ? '+' : ''}${metric.delta}${metric.deltaUnit || 'pp'}`;

  return (
    <div
      className={`${styles.summaryCard} ${
        variant === 'exports' ? styles.exportsCard : styles.importsCard
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
          variant === 'exports' ? styles.exportsIllustration : styles.importsIllustration
        }`}
      />
    </div>
  );
};

export const TradeBalancePanel: React.FC<TradeBalancePanelProps> = ({
  initialStateOverride,
}) => {
  const { data, state, refetch } = useIndicatorData<TradeBalanceValues>(
    'trade-balance',
    initialStateOverride
  );

  const chartOption = useMemo(
    () => buildTradeBalanceChartOption((data?.series || []) as TradeBalanceSeries),
    [data?.series]
  );

  return (
    <PanelShell
      id="panel-trade-balance"
      title={data?.title || 'Imports, Exports & Trade Balance'}
      source={data?.source || 'Ministry of Commerce and Industry'}
      sourceType={data?.source_type || 'external'}
      asOf={data?.as_of || 'FY 2024-25'}
      state={state}
      onRetry={refetch}
    >
      {data?.values && (
        <div className={styles.tilesRow}>
          <TradeSummaryCard
            metric={data.values.exports}
            variant="exports"
            illustrationSrc="/exports-3d.png"
          />
          <TradeSummaryCard
            metric={data.values.imports}
            variant="imports"
            illustrationSrc="/imports-3d.png"
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
