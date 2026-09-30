-- does ROE at fiscal year end say anything about the next 12 months of returns?
-- entry is the first trading day after the report would have been public (period_end + 90d),
-- exit is 365 days after that. stocks are bucketed into ROE quartiles within each fiscal year
WITH f AS (
    SELECT ticker, period_end, available_date, horizon_date,
           net_income * 1.0 / total_equity AS roe
    FROM fundamentals
    WHERE total_equity > 0
),
dates AS (
    SELECT f.*,
           (SELECT MIN(p.date) FROM prices p WHERE p.ticker = f.ticker AND p.date >= f.available_date) AS entry_date,
           (SELECT MIN(p.date) FROM prices p WHERE p.ticker = f.ticker AND p.date >= f.horizon_date)   AS exit_date
    FROM f
),
fwd AS (
    SELECT d.ticker, d.period_end, d.roe,
           p1.adj_close / p0.adj_close - 1 AS fwd_return
    FROM dates d
    JOIN prices p0 ON p0.ticker = d.ticker AND p0.date = d.entry_date
    JOIN prices p1 ON p1.ticker = d.ticker AND p1.date = d.exit_date
),
bucketed AS (
    SELECT *, NTILE(4) OVER (PARTITION BY SUBSTR(period_end, 1, 4) ORDER BY roe) AS roe_quartile
    FROM fwd
)
SELECT roe_quartile,
       COUNT(*)                          AS n_obs,
       ROUND(AVG(roe) * 100, 1)          AS avg_roe_pct,
       ROUND(AVG(fwd_return) * 100, 1)   AS avg_fwd_12m_return_pct
FROM bucketed
GROUP BY roe_quartile
ORDER BY roe_quartile;
