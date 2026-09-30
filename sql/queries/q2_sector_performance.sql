-- equal weighted sector portfolios, rebalanced daily
WITH sector_daily AS (
    SELECT c.sector, r.date, AVG(r.ret) AS ret
    FROM daily_returns r
    JOIN companies c USING (ticker)
    WHERE c.sector <> 'Index'
    GROUP BY c.sector, r.date
),
stats AS (
    SELECT sector,
           AVG(ret) * 252 AS ann_ret,
           SQRT(AVG(ret * ret) - AVG(ret) * AVG(ret)) * SQRT(252.0) AS ann_vol,
           MIN(ret) AS worst_day
    FROM sector_daily
    GROUP BY sector
)
SELECT sector,
       ROUND(ann_ret * 100, 2)          AS ann_return_pct,
       ROUND(ann_vol * 100, 2)          AS ann_vol_pct,
       ROUND(ann_ret / ann_vol, 2)      AS return_to_risk,
       ROUND(worst_day * 100, 2)        AS worst_day_pct,
       RANK() OVER (ORDER BY ann_ret / ann_vol DESC) AS rank_by_return_to_risk
FROM stats
ORDER BY rank_by_return_to_risk;
