import React, { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import { echarts } from '../echartsSetup';
import { PanelShell } from '../../components/PanelShell/PanelShell';
import { useIndicatorData } from '../../hooks/useIndicatorData';
import {
  GovtExpenditureValues,
  GovtExpenditureSeries,
  PanelState,
  StatTileMetric,
} from '../../api/types';
import { buildGovtExpenditureChartOption } from './chartOption';
import styles from './GovtExpenditurePanel.module.css';

interface GovtExpenditurePanelProps {
  initialStateOverride?: PanelState;
}

interface GovtExpenditureSummaryCardProps {
  metric: StatTileMetric;
  variant: 'total' | 'capital';
  illustrationSrc: string;
}

const GovtExpenditureSummaryCard: React.FC<GovtExpenditureSummaryCardProps> = ({
  metric,
  variant,
  illustrationSrc,
}) => {
  const displayValue =
    metric.value === null || metric.value === undefined
      ? '—'
      : metric.formattedValue ||
        (typeof metric.value === 'number' ? `₹${metric.value}L Cr` : `${metric.value}`);

  const deltaText =
    metric.delta === null || metric.delta === undefined
      ? null
      : metric.formattedDelta ||
        `${metric.delta > 0 ? '+' : ''}${metric.delta}${metric.deltaUnit || 'pp'}`;

  return (
    <div
      className={`${styles.summaryCard} ${
        variant === 'total' ? styles.totalCard : styles.capitalCard
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
          variant === 'total' ? styles.totalIllustration : styles.capitalIllustration
        }`}
      />
    </div>
  );
};

export const GovtExpenditurePanel: React.FC<GovtExpenditurePanelProps> = ({
  initialStateOverride,
}) => {
  const { data, state, refetch } = useIndicatorData<GovtExpenditureValues>(
    'govt-expenditure',
    initialStateOverride
  );

  const chartOption = useMemo(
    () => buildGovtExpenditureChartOption((data?.series || []) as GovtExpenditureSeries),
    [data?.series]
  );

  return (
    <PanelShell
      id="panel-govt-expenditure"
      title={data?.title || 'Government Expenditure'}
      subtitle={data?.subtitle}
      source={data?.source || 'Union Budget (Ministry of Finance)'}
      sourceType={data?.source_type || 'external'}
      asOf={data?.as_of || 'FY 2025-26 RE'}
      isEstimate={Boolean(
        data?.as_of?.includes('RE') ||
        data?.as_of?.includes('BE') ||
        (Array.isArray(data?.series) && data.series.some((s: any) => s?.estimate))
      )}
      state={state}
      onRetry={refetch}
    >
      {data?.values && (
        <div className={styles.tilesRow}>
          <GovtExpenditureSummaryCard
            metric={data.values.totalExpenditure}
            variant="total"
            illustrationSrc="/total-expenditure-3d.png"
          />
          <GovtExpenditureSummaryCard
            metric={data.values.capitalExpenditure}
            variant="capital"
            illustrationSrc="/capital-expenditure-3d.png"
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
