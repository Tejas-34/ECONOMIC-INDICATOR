export type SourceType = 'NSE' | 'external';
export type IndicatorStatus = 'ok' | 'stale' | 'unavailable';
export type PanelState = 'loading' | 'ok' | 'stale' | 'empty' | 'unavailable' | 'error';
export type DeltaDirection = 'positive' | 'negative' | 'neutral';

export interface StatTileMetric {
  label: string;
  value: number | string | null;
  formattedValue?: string;
  unit?: string;
  delta?: number | null;
  formattedDelta?: string;
  deltaUnit?: string;
  deltaDirection: DeltaDirection;
  sublabel?: string;
  iconKey?: string;
}

export interface IndicatorResponse<TValues = Record<string, StatTileMetric>, TSeries = unknown[]> {
  id: string;
  title: string;
  subtitle?: string;
  source: string;
  source_type: SourceType;
  as_of: string;
  status: IndicatorStatus;
  values: TValues;
  series: TSeries;
}

/* Panel 1: GDP Growth */
export interface GdpGrowthValues {
  india: StatTileMetric;
  world: StatTileMetric;
}

export interface GdpGrowthPoint {
  year: string;
  indiaRate: number | null;
  worldRate: number | null;
}
export type GdpGrowthSeries = GdpGrowthPoint[];

/* Panel 2: Debt to GDP */
export interface DebtToGdpValues {
  indiaFy25: StatTileMetric;
  indVsUs: StatTileMetric;
}

export interface DebtToGdpPoint {
  date: string;
  ratio: number | null;
  isHighlighted?: boolean;
  highlightLabel?: string;
}
export type DebtToGdpSeries = DebtToGdpPoint[];

/* Panel 3: Imports, Exports & Trade Balance */
export interface TradeBalanceValues {
  exports: StatTileMetric;
  imports: StatTileMetric;
}

export interface TradeBalancePoint {
  year: string;
  importsValue: number | null;
  exportsValue: number | null;
  tradeBalance: number | null;
  tradeBalanceLabel?: string;
}
export type TradeBalanceSeries = TradeBalancePoint[];

/* Panel 4: GST Tax Collection */
export interface GstCollectionValues {
  collections: StatTileMetric;
  monthlyAverage: StatTileMetric;
}

export interface GstCollectionPoint {
  year: string;
  collectionRate: number | null;
  averageRate: number | null;
  highlightLabel?: string;
}
export type GstCollectionSeries = GstCollectionPoint[];

/* Panel 5: Inflation */
export interface InflationValues {
  inflationRate: StatTileMetric;
  rbiTarget: StatTileMetric;
}

export interface InflationPoint {
  year: string;
  cpiRate: number | null;
  isHighlighted?: boolean;
  highlightLabel?: string;
}
export type InflationSeries = InflationPoint[];

/* Panel 6: Government Expenditure */
export interface GovtExpenditureValues {
  totalExpenditure: StatTileMetric;
  capitalExpenditure: StatTileMetric;
}

export interface GovtExpenditurePoint {
  year: string;
  revenueExpenditure: number | null;
  capitalExpenditure: number | null;
  totalExpenditure: number | null;
}
export type GovtExpenditureSeries = GovtExpenditurePoint[];

/* Live Ticker Quotes */
export interface TickerQuote {
  symbol: string;
  currentPrice: number;
  changePoints: number;
  changePercent: number;
  isPositive: boolean;
  updatedAt: string;
}

export interface TickerStreamPayload {
  timestamp: string;
  quotes: TickerQuote[];
}

/* Authentication */
export interface AuthUser {
  id: string;
  username?: string;
  email: string;
  name?: string;
  role: 'viewer' | 'admin';
}

export interface LoginCredentials {
  username?: string;
  email?: string;
  password?: string;
}

export interface LoginResponse {
  user: AuthUser;
  accessToken: string;
  expiresInSeconds: number;
}

export interface AuthSessionState {
  user: AuthUser | null;
  accessToken: string | null;
  expiresAt: number | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
