# Data Model & Schema Specification: Economic Indicator Dashboard

**Feature**: [001-economic-indicator-dashboard](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md)  
**Date**: 2026-10-16  
**Status**: Approved

This document specifies the PostgreSQL 16 relational database schema, SQL constraints, Pydantic v2 schemas, and domain state machines for the Economic Indicator backend and frontend integration.

---

## 1. Relational Database Schema (PostgreSQL 16)

The database schema is managed via numbered raw SQL migrations (`migrations/*.sql`) executed transactionally.

### 1.1 `users` Table
Stores authenticated analyst and administrative accounts.

```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'viewer' CHECK (role IN ('viewer', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
```

### 1.2 `sources` Table
Authoritative registry of external and internal data sources.

```sql
CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(32) NOT NULL CHECK (type IN ('nse', 'external', 'external-curated')),
    url TEXT NOT NULL,
    notes TEXT
);

-- Seed initial sources
INSERT INTO sources (id, name, type, url, notes) VALUES
('worldbank-gdp', 'World Bank', 'external', 'https://api.worldbank.org/v2/country/{country}/indicator/NY.GDP.MKTP.KD.ZG', 'Annual GDP growth %'),
('imf-debt', 'IMF DataMapper', 'external', 'https://www.imf.org/external/datamapper/api/v1/GGXWDG_NGDP', 'Central government debt % of GDP'),
('worldbank-trade', 'World Bank', 'external', 'https://api.worldbank.org/v2/country/IND/indicator/NE.EXP.GNFS.CD', 'Imports, Exports, and Trade Balance'),
('seed-gst', 'Ministry of Finance / data.gov.in', 'external-curated', 'https://data.gov.in', 'Curated monthly GST collections'),
('worldbank-inflation', 'World Bank', 'external', 'https://api.worldbank.org/v2/country/IND/indicator/FP.CPI.TOTL.ZG', 'Consumer price index inflation %'),
('seed-budget', 'Union Budget (Expenditure Profile)', 'external-curated', 'https://www.indiabudget.gov.in', 'Capital, revenue, and total central expenditure'),
('nse', 'National Stock Exchange of India', 'nse', 'https://www.nseindia.com/api/allIndices', 'NIFTY indices live quotes'),
('bse', 'Bombay Stock Exchange', 'external', 'https://query1.finance.yahoo.com', 'SENSEX real-time quote')
ON CONFLICT (id) DO NOTHING;
```

### 1.3 `observations` Table
Granular time-series and level metrics across the six macroeconomic indicator cards.

```sql
CREATE TABLE IF NOT EXISTS observations (
    id BIGSERIAL PRIMARY KEY,
    indicator VARCHAR(64) NOT NULL CHECK (indicator IN (
        'gdp-growth',
        'debt-to-gdp',
        'trade-balance',
        'gst-collection',
        'inflation',
        'govt-expenditure'
    )),
    series VARCHAR(64) NOT NULL,             -- e.g. 'india', 'world', 'exports', 'imports', 'capex'
    period VARCHAR(32) NOT NULL,             -- e.g. '2021', '2022', 'FY2024-25', 'FY2025-26'
    value NUMERIC(18, 4),                    -- NULL allowed for missing historical figures
    unit VARCHAR(32),                        -- '%', 'US$ B', 'Rs lakh crore'
    basis VARCHAR(32) CHECK (basis IN ('actual', 'revised_estimate', 'budget_estimate') OR basis IS NULL),
    source_id VARCHAR(64) NOT NULL REFERENCES sources(id),
    as_of DATE NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_indicator_series_period UNIQUE (indicator, series, period)
);

CREATE INDEX IF NOT EXISTS idx_observations_indicator_period ON observations(indicator, period);
```

### 1.4 `ticker_latest` Table
Holds the most recent snapshot of market index quotes for the header ticker.

```sql
CREATE TABLE IF NOT EXISTS ticker_latest (
    symbol VARCHAR(32) PRIMARY KEY,          -- 'SENSEX', 'NIFTY BANK', 'NIFTY IT'
    name VARCHAR(64) NOT NULL,
    last NUMERIC(12, 2) NOT NULL,
    change NUMERIC(10, 2) NOT NULL,
    pct_change NUMERIC(6, 2) NOT NULL,
    market_status VARCHAR(16) NOT NULL CHECK (market_status IN ('open', 'closed', 'stale')),
    source_id VARCHAR(64) NOT NULL REFERENCES sources(id),
    as_of TIMESTAMPTZ NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 1.5 `ticker_history` Table
Stores rolling snapshots for auditability and chart trend analysis; auto-pruned to retain 7 days.

```sql
CREATE TABLE IF NOT EXISTS ticker_history (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    last NUMERIC(12, 2) NOT NULL,
    pct_change NUMERIC(6, 2) NOT NULL,
    as_of TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ticker_history_symbol_asof ON ticker_history(symbol, as_of DESC);
```

### 1.6 `collector_runs` Table
Audit ledger tracking execution, health, and error states of background collectors.

```sql
CREATE TABLE IF NOT EXISTS collector_runs (
    id BIGSERIAL PRIMARY KEY,
    job VARCHAR(64) NOT NULL,                -- 'ticker', 'gdp', 'debt', 'trade', 'gst', 'inflation', 'expenditure'
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL CHECK (status IN ('success', 'failed', 'circuit_open', 'skipped')),
    rows INTEGER DEFAULT 0,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_collector_runs_job_started ON collector_runs(job, started_at DESC);
```

### 1.7 `seed_files` Table
Tracks loaded seed CSV checksums to guarantee idempotent execution.

```sql
CREATE TABLE IF NOT EXISTS seed_files (
    path VARCHAR(255) PRIMARY KEY,
    checksum VARCHAR(64) NOT NULL,           -- SHA-256
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 2. Pydantic v2 Domain Models

### 2.1 Standard Indicator Response Envelope

```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import date, datetime

SourceType = Literal['nse', 'external', 'external-curated']
IndicatorStatus = Literal['ok', 'stale', 'unavailable']
DeltaDirection = Literal['positive', 'negative', 'neutral']
EstimateBasis = Literal['actual', 'revised_estimate', 'budget_estimate']

class SourceInfo(BaseModel):
    name: str
    type: SourceType
    url: str

class StatTile(BaseModel):
    label: str
    value: Optional[float] = None
    unit: Optional[str] = None
    change: Optional[float] = None
    change_unit: Optional[str] = "pp"
    formatted_value: Optional[str] = None
    formatted_change: Optional[str] = None
    delta_direction: DeltaDirection = "neutral"

class SeriesPoint(BaseModel):
    period: str
    value: Optional[float] = None
    basis: Optional[EstimateBasis] = None

class SeriesItem(BaseModel):
    name: str
    points: List[SeriesPoint]

class IndicatorEnvelope(BaseModel):
    indicator: str
    title: str
    subtitle: Optional[str] = None
    tiles: List[StatTile]
    series: List[SeriesItem]
    source: SourceInfo
    as_of: str
    fetched_at: datetime
    status: IndicatorStatus
```

### 2.2 Market Ticker Models

```python
MarketStatus = Literal['open', 'closed', 'stale']

class TickerQuote(BaseModel):
    symbol: str
    name: str
    last: float
    change: float
    pct_change: float
    market_status: MarketStatus
    source: str
    as_of: datetime

class TickerSnapshotResponse(BaseModel):
    timestamp: datetime
    quotes: List[TickerQuote]

class TickerStreamEvent(BaseModel):
    id: int
    data: TickerSnapshotResponse
```

### 2.3 Authentication Models

```python
UserRole = Literal['viewer', 'admin']

class LoginRequest(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    id: int
    username: str
    role: UserRole

class LoginResponse(BaseModel):
    user: UserProfile
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 3600

class StreamTicketResponse(BaseModel):
    ticket: str
    expires_in_seconds: int = 30
```

---

## 3. Business Logic & Calculation Rules

### 3.1 Stat Tile Change Rules (Decision D3)
1. **Rate Series (GDP Growth, Inflation, Debt to GDP)**:
   $$\text{change} = \text{latest rate} - \text{previous rate} \quad (\text{in percentage points, pp})$$
2. **Level Series (Exports, Imports, GST Collections, Total/Capital Expenditure)**:
   $$\text{YoY growth}(t) = \frac{\text{value}(t) - \text{value}(t-1)}{\text{value}(t-1)} \times 100$$
   $$\text{change} = \text{YoY growth}(\text{latest}) - \text{YoY growth}(\text{previous}) \quad (\text{in pp})$$
3. **Missing Data**:
   If either $\text{latest}$ or $\text{previous}$ is `null` or missing, $\text{change} = \text{null}$.

### 3.2 Indicator Staleness State Machine (Decision D15)
- Given expected refresh interval $R$:
  - If $\text{now} - \text{fetched\_at} > 2 \times R \implies \text{status} = \text{"stale"}$.
  - If the last collector run failed but historical data exists $\implies \text{status} = \text{"stale"}$.
  - If no data has ever been collected $\implies \text{status} = \text{"unavailable"}$.
  - Otherwise $\implies \text{status} = \text{"ok"}$.

### 3.3 Market Status State Machine (Decision D11)
- Evaluated against `Asia/Kolkata` time:
  - If Monday–Friday, `09:15 <= current_time <= 15:30`:
    - If `now - as_of <= 120s` $\implies \text{"open"}$.
    - If `now - as_of > 120s` (upstream quote timestamp stopped updating during market hours) $\implies \text{"closed"}$ (Exchange Holiday detected).
  - Outside these hours or weekends $\implies \text{"closed"}$.
