DROP VIEW IF EXISTS daily_returns;
DROP VIEW IF EXISTS rolling_vol;
DROP VIEW IF EXISTS drawdowns;
DROP VIEW IF EXISTS vix_regime;

-- simple daily return on adjusted close
CREATE VIEW daily_returns AS
SELECT ticker, date, ret
FROM (
    SELECT ticker, date,
           adj_close / LAG(adj_close) OVER (PARTITION BY ticker ORDER BY date) - 1 AS ret
    FROM prices
)
WHERE ret IS NOT NULL;

-- 30 day annualised vol. sqlite has no stddev window function so this is
-- sqrt(E[r^2] - E[r]^2), i.e. population std. in postgres you could use STDDEV_SAMP
CREATE VIEW rolling_vol AS
SELECT ticker, date, vol_30d
FROM (
    SELECT ticker, date,
           COUNT(*) OVER w AS n,
           SQRT(AVG(ret * ret) OVER w - AVG(ret) OVER w * AVG(ret) OVER w) * SQRT(252.0) AS vol_30d
    FROM daily_returns
    WINDOW w AS (PARTITION BY ticker ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)
)
WHERE n = 30;

CREATE VIEW drawdowns AS
SELECT ticker, date,
       adj_close / MAX(adj_close) OVER (
           PARTITION BY ticker ORDER BY date
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) - 1 AS drawdown
FROM prices;

-- regime is based on the PREVIOUS day's VIX so it's something you could know
-- before the return happens (no lookahead)
CREATE VIEW vix_regime AS
WITH v AS (
    SELECT date, value AS vix, LAG(value) OVER (ORDER BY date) AS prev_vix
    FROM macro
    WHERE series_id = 'VIXCLS'
)
SELECT date, vix,
       CASE WHEN prev_vix IS NULL THEN NULL
            WHEN prev_vix < 15 THEN '1 Low (<15)'
            WHEN prev_vix < 25 THEN '2 Mid (15-25)'
            ELSE '3 High (25+)' END AS regime
FROM v;
