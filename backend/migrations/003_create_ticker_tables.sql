-- 003_create_ticker_tables.sql
-- Live market index latest state and historical quotes

CREATE TABLE IF NOT EXISTS ticker_latest (
    symbol VARCHAR(32) PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    last NUMERIC(12, 2) NOT NULL,
    change NUMERIC(10, 2) NOT NULL,
    pct_change NUMERIC(6, 2) NOT NULL,
    market_status VARCHAR(16) NOT NULL CHECK (market_status IN ('open', 'closed', 'stale')),
    source_id VARCHAR(64) REFERENCES sources(id) ON DELETE RESTRICT,
    as_of TIMESTAMPTZ NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ticker_history (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    last NUMERIC(12, 2) NOT NULL,
    pct_change NUMERIC(6, 2) NOT NULL,
    as_of TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ticker_history_symbol_as_of ON ticker_history (symbol, as_of DESC);
