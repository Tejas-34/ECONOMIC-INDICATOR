import React, { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import { echarts } from '../echartsSetup';
import { PanelShell } from '../../components/PanelShell/PanelShell';
import { StatTile } from '../../components/StatTile/StatTile';
import { useIndicatorData } from '../../hooks/useIndicatorData';
import { GovtExpenditureValues, GovtExpenditureSeries, PanelState } from '../../api/types';
import { buildGovtExpenditureChartOption } from './chartOption';
import styles from '../../components/PanelShell/PanelShell.module.css';

interface GovtExpenditurePanelProps {
  initialStateOverride?: PanelState;
}

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
      source={data?.source || 'Ministry of Finance'}
      sourceType={data?.source_type || 'external'}
      asOf={data?.as_of || 'FY 2024-25 RE'}
      state={state}
      onRetry={refetch}
    >
      {data?.values && (
        <div className={styles.tilesRow}>
          <StatTile metric={data.values.totalExpenditure} />
          <StatTile metric={data.values.capitalExpenditure} />
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
