import React, { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import { echarts } from '../echartsSetup';
import { PanelShell } from '../../components/PanelShell/PanelShell';
import { useIndicatorData } from '../../hooks/useIndicatorData';
import { GstCollectionValues, GstCollectionSeries, PanelState, StatTileMetric } from '../../api/types';
import { buildGstChartOption } from './chartOption';
import styles from './GstCollectionPanel.module.css';

interface GstCollectionPanelProps {
  initialStateOverride?: PanelState;
}

interface GstSummaryCardProps {
  metric: StatTileMetric;
  variant: 'collections' | 'monthly';
  illustrationSrc: string;
}

const GstSummaryCard: React.FC<GstSummaryCardProps> = ({
  metric,
  variant,
  illustrationSrc,
}) => {
  const displayValue =
    metric.value === null || metric.value === undefined
      ? '—'
      : metric.formattedValue || (typeof metric.value === 'number' ? `₹${metric.value}L Cr` : `${metric.value}`);

  const deltaText =
    metric.delta === null || metric.delta === undefined
      ? null
      : metric.formattedDelta ||
        `${metric.delta > 0 ? '+' : ''}${metric.delta}${metric.deltaUnit || 'pp'}`;

  return (
    <div
      className={`${styles.summaryCard} ${
        variant === 'collections' ? styles.collectionsCard : styles.monthlyCard
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
          variant === 'collections'
            ? styles.collectionsIllustration
            : styles.monthlyIllustration
        }`}
      />
    </div>
  );
};

export const GstCollectionPanel: React.FC<GstCollectionPanelProps> = ({
  initialStateOverride,
}) => {
  const { data, state, refetch } = useIndicatorData<GstCollectionValues>(
    'gst-collection',
    initialStateOverride
  );

  const chartOption = useMemo(
    () => buildGstChartOption((data?.series || []) as GstCollectionSeries),
    [data?.series]
  );

  return (
    <PanelShell
      id="panel-gst-collection"
      title={data?.title || 'GST Tax Collection'}
      subtitle={data?.subtitle || '(₹ Lakh Cr)'}
      source={data?.source || 'data.gov.in (Rajya Sabha)'}
      sourceType={data?.source_type || 'external'}
      asOf={data?.as_of || '2024-25'}
      state={state}
      onRetry={refetch}
    >
      {data?.values && (
        <div className={styles.tilesRow}>
          <GstSummaryCard
            metric={data.values.collections}
            variant="collections"
            illustrationSrc="/image-9600.png"
          />
          <GstSummaryCard
            metric={data.values.monthlyAverage}
            variant="monthly"
            illustrationSrc="/image-9580.png"
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
