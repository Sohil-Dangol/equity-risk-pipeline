-- beta = cov(stock, market) / var(market), computed from averages
WITH m AS (
    SELECT date, ret AS mret FROM daily_returns WHERE ticker = 'SPY'
),
j AS (
    SELECT r.ticker, r.ret, m.mret
    FROM daily_returns r
    JOIN m USING (date)
    WHERE r.ticker <> 'SPY'
),
b AS (
    SELECT ticker,
           (AVG(ret * mret) - AVG(ret) * AVG(mret)) / (AVG(mret * mret) - AVG(mret) * AVG(mret)) AS beta,
           SQRT(AVG(ret * ret) - AVG(ret) * AVG(ret)) * SQRT(252.0) AS ann_vol
    FROM j
    GROUP BY ticker
)
SELECT b.ticker, c.sector,
       ROUND(b.beta, 3)          AS beta,
       ROUND(b.ann_vol * 100, 1) AS ann_vol_pct,
       RANK() OVER (ORDER BY b.beta DESC) AS beta_rank
FROM b
JOIN companies c USING (ticker)
ORDER BY beta_rank;
