SELECT r.date,
       ROUND(r.ret * 100, 2) AS spy_return_pct,
       m.value               AS vix_close
FROM daily_returns r
LEFT JOIN macro m ON m.date = r.date AND m.series_id = 'VIXCLS'
WHERE r.ticker = 'SPY'
ORDER BY r.ret
LIMIT 10;
