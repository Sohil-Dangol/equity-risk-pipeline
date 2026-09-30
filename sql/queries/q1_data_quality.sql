-- row counts, date range and obvious problems per ticker
SELECT p.ticker, c.sector,
       COUNT(*)        AS n_rows,
       MIN(p.date)     AS first_date,
       MAX(p.date)     AS last_date,
       SUM(CASE WHEN p.adj_close <= 0 THEN 1 ELSE 0 END) AS non_positive_prices,
       (SELECT COUNT(*) FROM daily_returns r
         WHERE r.ticker = p.ticker AND ABS(r.ret) > 0.25) AS moves_over_25pct
FROM prices p
JOIN companies c USING (ticker)
GROUP BY p.ticker, c.sector
ORDER BY n_rows, p.ticker;
