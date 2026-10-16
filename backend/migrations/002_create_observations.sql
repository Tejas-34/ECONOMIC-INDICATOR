-- 002_create_observations.sql
-- Macroeconomic observations table and collector audit runs log

CREATE TABLE IF NOT EXISTS observations (
    id BIGSERIAL PRIMARY KEY,
    indicator VARCHAR(64) NOT NULL,
    series VARCHAR(64) NOT NULL,
    period VARCHAR(32) NOT NULL,
    value NUMERIC(18, 4),
    unit VARCHAR(32),
    basis VARCHAR(32) CHECK (basis IN ('actual', 'revised_estimate', 'budget_estimate', NULL)),
    source_id VARCHAR(64) REFERENCES sources(id) ON DELETE RESTRICT,
    as_of DATE NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_observations_indicator_series_period UNIQUE (indicator, series, period)
);

CREATE INDEX IF NOT EXISTS idx_observations_indicator_period ON observations (indicator, period);
CREATE INDEX IF NOT EXISTS idx_observations_fetched_at ON observations (fetched_at);

CREATE TABLE IF NOT EXISTS collector_runs (
    id BIGSERIAL PRIMARY KEY,
    job VARCHAR(64) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL CHECK (status IN ('success', 'failed', 'skipped_rate_limit', 'circuit_open')),
    rows INTEGER DEFAULT 0,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_collector_runs_job_started ON collector_runs (job, started_at DESC);
