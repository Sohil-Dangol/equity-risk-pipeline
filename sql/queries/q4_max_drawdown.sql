WITH ranked AS (
    SELECT ticker, date, drawdown,
           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY drawdown) AS rn
    FROM drawdowns
)
SELECT r.ticker, c.sector,
       ROUND(r.drawdown * 100, 1) AS max_drawdown_pct,
       r.date                     AS trough_date
FROM ranked r
JOIN companies c USING (ticker)
WHERE r.rn = 1
ORDER BY r.drawdown;
