"""Makes fake but realistic-ish market data so the whole pipeline runs offline.

The market has three hidden regimes (calm / normal / stress) that switch as a markov chain.
Because the regimes are built in, a regime model will look good on this data. That says
nothing about real markets, so rerun with fetch_data.py before drawing any conclusions.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DATA_RAW, END, INDEX_ROW, START, UNIVERSE

SECTOR_BETA = {
    "Technology": 1.25, "Communication": 1.0, "Financials": 1.15, "Health Care": 0.8,
    "Consumer Discretionary": 1.2, "Consumer Staples": 0.6, "Energy": 1.1,
    "Industrials": 1.1, "Utilities": 0.55, "Materials": 0.95, "Real Estate": 0.85,
}


def t_noise(rng, size, df=6):
    # student-t scaled to unit variance, gives fat tails
    return rng.standard_t(df, size) / np.sqrt(df / (df - 2))


def make_market(rng, n):
    P = np.array([[0.985, 0.014, 0.001],
                  [0.010, 0.982, 0.008],
                  [0.004, 0.040, 0.956]])
    ann_vol = np.array([0.07, 0.13, 0.32])
    ann_mu = np.array([0.14, 0.08, -0.30])
    state = np.zeros(n, dtype=int)
    state[0] = 1
    for i in range(1, n):
        state[i] = rng.choice(3, p=P[state[i - 1]])
    m = ann_mu[state] / 252 + ann_vol[state] / np.sqrt(252) * t_noise(rng, n)
    return state, m, ann_vol


def make_vix(rng, state, m, ann_vol):
    n = len(m)
    level = ann_vol[state] * 100
    smooth = np.zeros(n)
    ew = np.zeros(n)
    smooth[0], ew[0] = level[0], level[0]
    s2 = (level[0] / 100) ** 2 / 252
    for i in range(1, n):
        smooth[i] = 0.9 * smooth[i - 1] + 0.1 * level[i]
        s2 = 0.94 * s2 + 0.06 * m[i] ** 2
        ew[i] = np.sqrt(s2 * 252) * 100
    noise = np.zeros(n)
    for i in range(1, n):
        noise[i] = 0.9 * noise[i - 1] + rng.normal(0, 0.8)
    return np.clip(3 + 1.05 * (0.6 * smooth + 0.4 * ew) + noise, 9, 85)


def to_prices(ticker, dates, log_ret, p0, div_yield, rng):
    n = len(dates)
    close = p0 * np.exp(np.cumsum(log_ret))
    adj = close * np.exp(-div_yield * (n - 1 - np.arange(n)) / 252)
    prev = np.r_[p0, close[:-1]]
    open_ = prev * np.exp(rng.normal(0, 0.002, n))
    spread = np.abs(rng.normal(0, 0.006, n))
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * (1 - spread)
    vol = rng.lognormal(15.5, 0.4, n).astype(int)
    return pd.DataFrame({
        "ticker": ticker, "date": dates.strftime("%Y-%m-%d"),
        "open": open_.round(4), "high": high.round(4), "low": low.round(4),
        "close": close.round(4), "adj_close": adj.round(4), "volume": vol,
    })


def main(seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(START, END)  # no holiday calendar, fine for a demo
    n = len(dates)
    state, m, ann_vol = make_market(rng, n)
    vol_mult = np.array([0.8, 1.0, 1.8])[state]

    sector_factor = {s: rng.normal(0, 0.006, n) * vol_mult for s in SECTOR_BETA}
    price_frames = [to_prices("SPY", dates, m, 200.0, 0.015, rng)]
    fundamentals = []

    for t, (name, sector) in UNIVERSE.items():
        beta = SECTOR_BETA[sector] * rng.uniform(0.85, 1.15)
        idio = rng.normal(0, 1, n) * 0.008 * vol_mult
        alpha = rng.normal(0.03, 0.05) / 252
        r = alpha + beta * m + sector_factor[sector] + idio
        price_frames.append(to_prices(t, dates, r, rng.uniform(30, 300),
                                      rng.uniform(0, 0.03), rng))

        rev = rng.lognormal(23, 1.0)
        equity = rev * rng.uniform(0.3, 1.0)
        for y in range(2014, 2025):
            rev *= 1 + rng.normal(0.06, 0.06)
            margin = np.clip(rng.normal(0.12, 0.06), -0.05, 0.35)
            equity *= 1 + rng.normal(0.05, 0.05)
            fundamentals.append({
                "ticker": t, "period_end": f"{y}-12-31", "revenue": round(rev),
                "net_income": round(rev * margin), "total_debt": round(equity * rng.uniform(0.1, 1.5)),
                "total_equity": round(equity),
            })

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    pd.concat(price_frames).to_csv(DATA_RAW / "prices.csv", index=False)

    vix = make_vix(rng, state, m, ann_vol)
    ten = np.clip(2.5 + np.cumsum(rng.normal(0, 0.03, n)), 0.5, 5.5)
    ds = pd.Series(dates)
    month_start = (ds.groupby(dates.to_period("M")).transform("min") == ds).values
    ff = np.clip(1.5 + np.cumsum(rng.normal(0, 0.05, n)), 0.1, 5.5)
    macro = pd.concat([
        pd.DataFrame({"series_id": "VIXCLS", "date": dates.strftime("%Y-%m-%d"), "value": vix.round(2)}),
        pd.DataFrame({"series_id": "DGS10", "date": dates.strftime("%Y-%m-%d"), "value": ten.round(2)}),
        pd.DataFrame({"series_id": "FEDFUNDS", "date": dates[month_start].strftime("%Y-%m-%d"),
                      "value": ff[month_start].round(2)}),
    ])
    macro.to_csv(DATA_RAW / "macro.csv", index=False)

    pd.DataFrame(fundamentals).to_csv(DATA_RAW / "fundamentals.csv", index=False)
    comp = pd.DataFrame([(t, nm, s) for t, (nm, s) in {**UNIVERSE, **INDEX_ROW}.items()],
                        columns=["ticker", "name", "sector"])
    comp.to_csv(DATA_RAW / "companies.csv", index=False)
    (DATA_RAW / "SOURCE").write_text("synthetic")
    print(f"synthetic data written: {n} days, {len(UNIVERSE) + 1} tickers")


if __name__ == "__main__":
    main()
