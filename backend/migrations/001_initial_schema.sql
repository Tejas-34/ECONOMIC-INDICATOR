-- 001_initial_schema.sql
-- Core users, sources provenance, seed tracking, and schema migrations tracking

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(64) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'viewer' CHECK (role IN ('viewer', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(32) NOT NULL CHECK (type IN ('nse', 'external', 'external-curated')),
    url TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS seed_files (
    path VARCHAR(255) PRIMARY KEY,
    checksum VARCHAR(64) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert baseline source registries
INSERT INTO sources (id, name, type, url, notes)
VALUES
    ('worldbank', 'World Bank Group Open Data', 'external', 'https://data.worldbank.org', 'Authoritative macro GDP, Inflation, and Trade data'),
    ('imf', 'International Monetary Fund DataMapper', 'external', 'https://www.imf.org/external/datamapper', 'Authoritative Debt-to-GDP historical and projected statistics'),
    ('nse', 'National Stock Exchange of India (NSE)', 'nse', 'https://www.nseindia.com', 'Live exchange market index feeds for NIFTY BANK and NIFTY IT'),
    ('bse', 'Bombay Stock Exchange (BSE)', 'external', 'https://www.bseindia.com', 'SENSEX quote feed (non-NSE exchange source)'),
    ('seed-budget', 'Union Budget Expenditure Document', 'external-curated', 'https://www.indiabudget.gov.in', 'Curated Central Government Revenue, Capital, and Total Expenditure'),
    ('seed-gst', 'Ministry of Finance GST Portal', 'external-curated', 'https://www.gst.gov.in', 'Monthly and annual gross GST revenue collections')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    url = EXCLUDED.url;
