PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS daily_returns;
DROP VIEW IF EXISTS rolling_vol;
DROP VIEW IF EXISTS drawdowns;
DROP VIEW IF EXISTS vix_regime;
DROP TABLE IF EXISTS fundamentals;
DROP TABLE IF EXISTS macro;
DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS meta;

CREATE TABLE companies (
    ticker  TEXT PRIMARY KEY,
    name    TEXT NOT NULL,
    sector  TEXT NOT NULL
);

CREATE TABLE prices (
    ticker     TEXT NOT NULL REFERENCES companies (ticker),
    date       TEXT NOT NULL,
    open       REAL,
    high       REAL,
    low        REAL,
    close      REAL NOT NULL,
    adj_close  REAL NOT NULL,
    volume     INTEGER,
    PRIMARY KEY (ticker, date)
);
CREATE INDEX idx_prices_date ON prices (date);

CREATE TABLE macro (
    series_id  TEXT NOT NULL,
    date       TEXT NOT NULL,
    value      REAL,
    PRIMARY KEY (series_id, date)
);

-- available_date = period_end + 90 days (reports aren't public on the year end date)
-- horizon_date   = available_date + 365 days, used to measure the forward return
CREATE TABLE fundamentals (
    ticker         TEXT NOT NULL REFERENCES companies (ticker),
    period_end     TEXT NOT NULL,
    revenue        REAL,
    net_income     REAL,
    total_debt     REAL,
    total_equity   REAL,
    available_date TEXT NOT NULL,
    horizon_date   TEXT NOT NULL,
    PRIMARY KEY (ticker, period_end)
);

CREATE TABLE meta (
    key    TEXT PRIMARY KEY,
    value  TEXT
);
