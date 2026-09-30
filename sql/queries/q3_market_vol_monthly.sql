-- SPY 30 day vol sampled at each month end, next to the VIX
SELECT rv.date,
       ROUND(rv.vol_30d * 100, 2) AS spy_realised_vol_pct,
       m.value                    AS vix
FROM rolling_vol rv
LEFT JOIN macro m ON m.date = rv.date AND m.series_id = 'VIXCLS'
WHERE rv.ticker = 'SPY'
  AND rv.date IN (SELECT MAX(date) FROM rolling_vol WHERE ticker = 'SPY' GROUP BY SUBSTR(date, 1, 7))
ORDER BY rv.date;
