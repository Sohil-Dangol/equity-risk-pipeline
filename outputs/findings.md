# Findings (30 Sep 2026)

Data source: yfinance+fred

Out-of-sample forecast window: 2018-01-04 to 2025-12-30 (2,008 days).

## 1. Risk and return across VIX regimes (SQL)
Average sector volatility was 14.4% when the prior-day VIX was below 15 and 40.6% when it was 25 or above.

| sector | ann_return_pct | ann_vol_pct | return_to_risk | worst_day_pct | rank_by_return_to_risk |
|---|---|---|---|---|---|
| Technology | 36.32 | 27.68 | 1.31 | -15.37 | 1 |
| Consumer Discretionary | 23.66 | 23.48 | 1.01 | -14.25 | 2 |
| Health Care | 15.75 | 17.65 | 0.89 | -9.90 | 3 |
| Communication | 16.94 | 19.09 | 0.89 | -9.39 | 4 |
| Consumer Staples | 12.86 | 15.30 | 0.84 | -8.90 | 5 |
| Materials | 15.79 | 21.21 | 0.74 | -14.48 | 6 |
| Financials | 17.61 | 25.59 | 0.69 | -13.73 | 7 |
| Industrials | 14.38 | 23.38 | 0.62 | -12.47 | 8 |
| Utilities | 12.27 | 20.11 | 0.61 | -11.74 | 9 |
| Real Estate | 13.65 | 23.39 | 0.58 | -16.22 | 10 |
| Energy | 9.59 | 30.59 | 0.31 | -19.96 | 11 |

## 2. Volatility forecast accuracy (SPY, walk-forward)
Best model by QLIKE: **GARCH(1,1)-t** (0.9453). DM stat is against GARCH; negative means better, and p-values below 0.05 are conventional significance.

| model | QLIKE | MSE | MZ_R2 | DM_stat_vs_GARCH | DM_pvalue |
|---|---|---|---|---|---|
| GARCH(1,1)-t | 0.9453 | 25.7839 | 0.2716 | nan | nan |
| VIX bucket | 1.0301 | 37.2075 | 0.0266 | 1.5108 | 0.1308 |
| EWMA | 1.0306 | 29.4084 | 0.1635 | 3.2303 | 0.0012 |
| Rolling 21d | 1.0788 | 31.4409 | 0.1367 | 4.2168 | 0.0000 |
| HMM 3-state | 1.0874 | 34.7789 | 0.0242 | 1.3979 | 0.1621 |
| HMM 2-state | 1.1598 | 34.5865 | 0.0173 | 1.6112 | 0.1071 |

QLIKE by prior-day VIX bucket:

| model | VIX 15-25 | VIX 25+ | VIX<15 |
|---|---|---|---|
| EWMA | 1.0625 | 2.5105 | -0.0174 |
| GARCH(1,1)-t | 0.9802 | 2.3653 | -0.0694 |
| HMM 2-state | 1.0097 | 3.4784 | -0.0566 |
| HMM 3-state | 0.9626 | 3.2034 | -0.0485 |
| Rolling 21d | 1.1292 | 2.5686 | -0.0150 |
| VIX bucket | 0.9635 | 2.9308 | -0.0869 |

## 3. Volatility-targeting backtest
Buy and hold: Sharpe 0.65, max drawdown -33.7%. Best Sharpe among strategies: Vol target: GARCH(1,1)-t at 0.69.

| strategy | CAGR | Ann. vol | Sharpe | Max drawdown | Calmar | Avg SPY weight | Turnover / yr |
|---|---|---|---|---|---|---|---|
| Buy & hold SPY | 0.142 | 0.195 | 0.648 | -0.337 | 0.421 | 1.000 | 0.000 |
| Vol target: EWMA | 0.089 | 0.102 | 0.635 | -0.128 | 0.697 | 0.696 | 4.437 |
| Vol target: GARCH(1,1)-t | 0.094 | 0.100 | 0.690 | -0.122 | 0.766 | 0.705 | 11.585 |
| Vol target: HMM 2-state | 0.090 | 0.108 | 0.613 | -0.195 | 0.459 | 0.685 | 13.497 |
| Vol target: HMM 3-state | 0.089 | 0.108 | 0.610 | -0.176 | 0.508 | 0.699 | 12.933 |

## 4. ROE quartile vs next-12-month return (SQL)

| roe_quartile | n_obs | avg_roe_pct | avg_fwd_12m_return_pct |
|---|---|---|---|
| 1 | 25 | 6.9 | 22.7 |
| 2 | 25 | 19.3 | 23.8 |
| 3 | 23 | 36.4 | 17.7 |
| 4 | 22 | 213.8 | 27.1 |

## Caveats
- The universe is today's large caps, so there is survivorship bias.
- Squared daily returns are a noisy proxy for true variance; QLIKE is used because it copes with that.
- Backtest costs are a flat 5bp of turnover and ignore weight drift, borrowing and taxes.
- Fundamentals from yfinance cover only the last few years.

## My interpretation

_Write this yourself: what do the numbers say, and what would you test next?_
