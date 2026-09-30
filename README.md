# Equity Risk & Volatility Analytics Pipeline

An end-to-end **finance data-science project** combining Python, SQL, statistical modelling, machine learning and Excel.

The pipeline analyses daily market data for **48 US large-cap equities plus SPY**, combines it with VIX and macroeconomic data, stores the data in a relational database, performs financial analysis in SQL, builds an interactive Excel risk dashboard, and evaluates whether regime-aware models can improve one-day-ahead volatility forecasts and volatility-targeting performance.

## Research Question

> **How do risk and return behave across market regimes, and does a regime-aware model forecast volatility better than a standard GARCH model?**

The project evaluates several forecasting approaches using a walk-forward, out-of-sample framework:

* Rolling historical volatility
* EWMA
* GARCH(1,1)-t
* VIX-based regime buckets
* 2-state Hidden Markov Model
* 3-state Hidden Markov Model

Forecasts are evaluated using **QLIKE**, **Mincer-Zarnowitz regression**, and **Diebold-Mariano tests**.

The resulting volatility forecasts are then used in a **10% volatility-targeting strategy** to investigate whether better risk forecasts translate into better portfolio risk management.

---

## Key Findings

### 1. Risk varies substantially across market regimes

Using the previous day's VIX close as a causal regime indicator, average annualised sector volatility was:

* **14.4%** when VIX was below 15
* **40.6%** when VIX was 25 or above

This indicates a substantial increase in realised risk during high-volatility market conditions.

The sector analysis also demonstrates how return, volatility and drawdown characteristics vary across the equity universe.

### 2. GARCH(1,1)-t performed best for volatility forecasting

For SPY one-day-ahead volatility forecasts over the out-of-sample period **4 January 2018 to 30 December 2025** (2,008 trading days):

| Model            |    QLIKE ↓ | Mincer-Zarnowitz R² | DM p-value vs GARCH |
| ---------------- | ---------: | ------------------: | ------------------: |
| **GARCH(1,1)-t** | **0.9453** |          **0.2716** |                   — |
| VIX bucket       |     1.0301 |              0.0266 |              0.1308 |
| EWMA             |     1.0306 |              0.1635 |              0.0012 |
| Rolling 21-day   |     1.0788 |              0.1367 |              <0.001 |
| HMM 3-state      |     1.0874 |              0.0242 |              0.1621 |
| HMM 2-state      |     1.1598 |              0.0173 |              0.1071 |

GARCH(1,1)-t produced the lowest QLIKE and highest Mincer-Zarnowitz \(R^2\).

EWMA and rolling volatility were significantly worse than GARCH according to the Diebold-Mariano tests.

The HMM models also produced higher average QLIKE than GARCH, but the differences were **not statistically significant at the 5% level** over the full out-of-sample period.

This suggests that, for this dataset and modelling specification, introducing latent volatility regimes did not provide statistically significant forecasting improvements over a well-specified GARCH model.

### 3. Volatility targeting substantially reduced drawdowns

A simple volatility-targeting strategy was constructed with:

* 10% target volatility
* SPY exposure capped at 100%
* remaining capital held as cash
* position determined using the previous day's volatility forecast
* 5 basis points of transaction cost per unit of turnover

| Strategy                     |     CAGR | Annualised Vol. |    Sharpe | Max Drawdown | Avg. SPY Weight |
| ---------------------------- | -------: | --------------: | --------: | -----------: | --------------: |
| Buy & hold SPY               |    14.2% |           19.5% |     0.648 |       -33.7% |          100.0% |
| Vol target: EWMA             |     8.9% |           10.2% |     0.635 |       -12.8% |           69.6% |
| **Vol target: GARCH(1,1)-t** | **9.4%** |       **10.0%** | **0.690** |   **-12.2%** |           70.5% |
| Vol target: HMM 2-state      |     9.0% |           10.8% |     0.613 |       -19.5% |           68.5% |
| Vol target: HMM 3-state      |     8.9% |           10.8% |     0.610 |       -17.6% |           69.9% |

Volatility targeting reduced maximum drawdown substantially and kept realised volatility close to the 10% target.

However, lower portfolio exposure also reduced CAGR relative to buy-and-hold SPY. The observed Sharpe differences are small enough that the sample does not provide strong evidence that one strategy has a materially different risk-adjusted return from another.

---

## Data

### Market data

* **Yahoo Finance**
* Daily adjusted prices
* 48 US large-cap equities
* SPY benchmark
* 2015–2025

### Macro data

* **FRED**
* VIX
* 10-year Treasury yield
* Federal funds rate

### Fundamentals

Selected annual company fundamentals retrieved through Yahoo Finance.

The project treats reported fundamentals as point-in-time information using an availability-date assumption to reduce lookahead bias.

### Synthetic data

The pipeline also contains a synthetic data generator with built-in volatility regimes.

Synthetic mode is intended for:

* offline demonstrations
* testing
* reproducibility when internet access is unavailable

Synthetic results are clearly separated from the real-data findings above.

---

## Pipeline Architecture

```text
Yahoo Finance + FRED
        │
        ▼
Data ingestion and cleaning
        │
        ▼
Relational database
        │
        ├───────────────┐
        ▼               ▼
     SQL analysis     Python analysis
        │               │
        │         ┌─────┼─────────────┐
        │         ▼     ▼             ▼
        │       GARCH  HMM       Other forecasts
        │         │     │             │
        │         └─────┼─────────────┘
        │               ▼
        │        Out-of-sample
        │        model evaluation
        │               │
        └───────┬───────┘
                ▼
        Volatility-targeting
             backtest
                │
        ┌───────┴────────┐
        ▼                ▼
   Excel dashboard    Findings/report
```

---

# SQL Analysis

The database contains relational tables for:

* companies
* prices
* fundamentals
* macroeconomic data

The SQL layer uses a range of analytical techniques rather than simple filtering and aggregation.

### Queries

| Query                        | Analysis                                                          |
| ---------------------------- | ----------------------------------------------------------------- |
| `q1_data_quality`            | Row counts, date ranges, invalid prices and extreme returns       |
| `q2_sector_performance`      | Equal-weight sector returns and risk using `RANK()`               |
| `q3_market_vol_monthly`      | Rolling 30-day volatility and monthly VIX observations            |
| `q4_max_drawdown`            | Running highs, drawdowns and worst periods using window functions |
| `q5_beta_vs_spy`             | Beta calculated directly in SQL                                   |
| `q6_regime_performance`      | Sector return and volatility across VIX regimes                   |
| `q7_fundamentals_vs_returns` | Point-in-time fundamentals joined to subsequent returns           |
| `q8_worst_market_days`       | Worst SPY trading days alongside VIX                              |

The SQL implementation demonstrates:

* CTEs
* joins
* window functions
* `LAG()`
* rolling calculations
* `ROW_NUMBER()`
* `RANK()`
* `NTILE()`
* financial-statistical calculations directly in SQL

---

# Volatility Modelling

The modelling pipeline uses **walk-forward forecasting** rather than randomly splitting the time series.

Models are refitted on an expanding window every 63 trading days, and each forecast only uses information available before the forecast date.

### Models

**Rolling volatility**

A simple historical benchmark using recent realised returns.

**EWMA**

Exponentially weighted volatility, giving more weight to recent observations.

**GARCH(1,1)-t**

A conditional-volatility model with Student-t innovations designed to better accommodate heavy-tailed financial returns.

**VIX bucket model**

Forecasts volatility based on the previous day's VIX regime.

**Hidden Markov Models**

Two- and three-state models are used to identify latent volatility regimes.

---

# Avoiding Lookahead Bias

A major focus of the project is ensuring that the forecasting and backtesting framework is causal.

### VIX regimes

Regime classification uses the **previous day's VIX close**, not the contemporaneous value.

### HMM filtering

Standard HMM smoothing can use future observations.

To avoid this, the project uses a **forward-only filtering implementation** for live-style regime probabilities.

A dedicated test checks that adding future observations does not change earlier filtered probabilities.

### Walk-forward evaluation

Models are refitted periodically using only historical observations available at that point in time.

### Fundamentals

Fundamental information is treated as becoming available after a reporting delay rather than being assumed to have been known immediately at fiscal year-end.

### Backtest timing

The position for day \(t\) is determined using the volatility forecast generated from information available through day \(t-1\).

---

# Model Evaluation

Squared returns are a noisy proxy for realised variance, so model performance is not judged using MSE alone.

### QLIKE

QLIKE is used as the primary volatility forecast loss function because it is designed for variance forecasts and penalises under-forecasting strongly.

### Mincer-Zarnowitz regression

Used to examine the explanatory power and calibration of volatility forecasts.

### Diebold-Mariano test

Used to test whether the forecast loss of each alternative model differs significantly from GARCH.

This provides a statistical comparison rather than simply choosing the model with the lowest point estimate.

---

# Volatility-Targeting Backtest

The backtest translates volatility forecasts into a simple risk-management strategy.

The target is:

$$
\sigma_{target}=10\%
$$

The approximate portfolio weight is determined by the relationship between target and forecast volatility, subject to a maximum SPY exposure of 100%.

Transaction costs are included at **5 basis points per unit of turnover**.

The backtest reports:

* CAGR
* annualised volatility
* Sharpe ratio
* maximum drawdown
* Calmar ratio
* average SPY weight
* turnover

The purpose is not to claim a trading edge, but to examine whether volatility forecasting can improve **risk control**.

---

# Excel Risk Dashboard

`outputs/risk_dashboard.xlsx` contains a formula-driven portfolio risk dashboard.

The workbook includes:

### Portfolio analytics

* annualised return
* annualised volatility
* Sharpe ratio
* maximum drawdown
* beta
* correlation matrix

### Risk measures

* historical VaR
* parametric VaR
* CVaR / Expected Shortfall
* dollar VaR
* stress scenarios

### Interactive inputs

Portfolio weights and selected risk parameters can be changed on the Inputs sheet, with the downstream risk calculations updating through Excel formulas.

The workbook was independently cross-checked against pandas calculations for the headline risk metrics.

---

# Project Structure

```text
equity-risk-pipeline/
│
├── config.py
├── run_pipeline.py
├── requirements.txt
├── README.md
│
├── sql/
│   ├── schema.sql
│   ├── views.sql
│   └── queries/
│       ├── q1_data_quality.sql
│       ├── q2_sector_performance.sql
│       ├── q3_market_vol_monthly.sql
│       ├── q4_max_drawdown.sql
│       ├── q5_beta_vs_spy.sql
│       ├── q6_regime_performance.sql
│       ├── q7_fundamentals_vs_returns.sql
│       └── q8_worst_market_days.sql
│
├── src/
│   ├── fetch_data.py
│   ├── generate_sample_data.py
│   ├── load_db.py
│   ├── run_sql.py
│   ├── models.py
│   ├── backtest.py
│   ├── build_excel.py
│   └── report.py
│
├── tests/
│   └── test_pipeline.py
│
└── outputs/
    ├── forecasts.csv
    ├── model_metrics.csv
    ├── model_metrics_by_regime.csv
    ├── backtest_metrics.csv
    ├── backtest_equity_curves.csv
    ├── risk_dashboard.xlsx
    ├── findings.md
    ├── figures/
    └── sql/
```

---

# Testing

The project includes automated tests covering both numerical correctness and methodological issues.

Tests include:

* SQL calculations compared with pandas
* beta calculations
* data-quality checks
* HMM probability behaviour
* HMM causality / no-future-information checks
* QLIKE behaviour
* Diebold-Mariano test behaviour

Run:

```bash
pytest tests
```

---

# Running the Project

Install dependencies:

```bash
pip install -r requirements.txt
```

### Real data

```bash
python run_pipeline.py --source real
```

This requires internet access and downloads Yahoo Finance and FRED data.

### Synthetic data

```bash
python run_pipeline.py --source synthetic
```

Synthetic mode generates a reproducible regime-switching dat
