-- how do sectors behave depending on where the VIX closed the day before?
WITH sector_daily AS (
    SELECT c.sector, r.date, AVG(r.ret) AS ret
    FROM daily_returns r
    JOIN companies c USING (ticker)
    WHERE c.sector <> 'Index'
    GROUP BY c.sector, r.date
)
SELECT s.sector, v.regime,
       COUNT(*) AS n_days,
       ROUND(AVG(s.ret) * 252 * 100, 1) AS ann_return_pct,
       ROUND(SQRT(AVG(s.ret * s.ret) - AVG(s.ret) * AVG(s.ret)) * SQRT(252.0) * 100, 1) AS ann_vol_pct
FROM sector_daily s
JOIN vix_regime v USING (date)
WHERE v.regime IS NOT NULL
GROUP BY s.sector, v.regime
ORDER BY s.sector, v.regime;
