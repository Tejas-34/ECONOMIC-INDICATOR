import React from 'react';
import { GdpGrowthPanel } from './GdpGrowthPanel/GdpGrowthPanel';
import { DebtToGdpPanel } from './DebtToGdpPanel/DebtToGdpPanel';
import { TradeBalancePanel } from './TradeBalancePanel/TradeBalancePanel';
import { GstCollectionPanel } from './GstCollectionPanel/GstCollectionPanel';
import { InflationPanel } from './InflationPanel/InflationPanel';
import { GovtExpenditurePanel } from './GovtExpenditurePanel/GovtExpenditurePanel';
import { PanelState } from '../api/types';
import styles from './DashboardGrid.module.css';

interface DashboardGridProps {
  stateOverrides?: Record<string, PanelState>;
}

export const DashboardGrid: React.FC<DashboardGridProps> = ({ stateOverrides = {} }) => {
  return (
    <main className={styles.gridContainer} role="main" aria-label="Macroeconomic Indicators">
      {/* Row 1 */}
      <GdpGrowthPanel initialStateOverride={stateOverrides['gdp-growth']} />
      <DebtToGdpPanel initialStateOverride={stateOverrides['debt-to-gdp']} />

      {/* Row 2 */}
      <TradeBalancePanel initialStateOverride={stateOverrides['trade-balance']} />
      <GstCollectionPanel initialStateOverride={stateOverrides['gst-collection']} />

      {/* Row 3 */}
      <InflationPanel initialStateOverride={stateOverrides['inflation']} />
      <GovtExpenditurePanel initialStateOverride={stateOverrides['govt-expenditure']} />
    </main>
  );
};
