"""Volatility targeting on SPY using the walk-forward forecasts.

Weight on day d is set from the forecast made on d-1, so nothing here uses future data.
Weight is capped at 1 (no leverage): de-risk when forecast vol is above target, park the rest in cash.
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DB_PATH, INDEX_TICKER, OUT

TARGET_VOL = 0.10
MAX_WEIGHT = 1.0
COST_BPS = 5         # per unit of turnover. ignores weight drift between rebalances


def load_inputs():
    con = sqlite3.connect(DB_PATH)
    px = pd.read_sql("SELECT date, adj_close FROM prices WHERE ticker = ? ORDER BY date", con,
                     params=(INDEX_TICKER,), parse_dates=["date"]).set_index("date")["adj_close"]
    ff = pd.read_sql("SELECT date, value FROM macro WHERE series_id = 'FEDFUNDS'", con,
                     parse_dates=["date"]).set_index("date")["value"]
    con.close()
    spy_ret = px.pct_change()
    # monthly series, forward filled and lagged a day so it's not used before it exists
    cash = (ff.reindex(spy_ret.index, method="ffill").shift(1) / 100 / 252).fillna(0.0)
    return spy_ret, cash


def run_strategy(spy_ret, cash, h=None):
    if h is None:
        w = pd.Series(1.0, index=spy_ret.index)
    else:
        vol = np.sqrt(h) / 100 * np.sqrt(252)      # h is daily variance in pct^2
        w = (TARGET_VOL / vol).clip(upper=MAX_WEIGHT)
    turnover = w.diff().abs().fillna(0.0)
    ret = w * spy_ret + (1 - w) * cash - turnover * COST_BPS / 1e4
    return ret, w, turnover


def metrics(ret, cash, turnover, w):
    n = len(ret)
    equity = (1 + ret).cumprod()
    excess = ret - cash
    dd = equity / equity.cummax() - 1
    cagr = equity.iloc[-1] ** (252 / n) - 1
    vol = ret.std() * np.sqrt(252)
    return {
        "CAGR": cagr,
        "Ann. vol": vol,
        "Sharpe": excess.mean() / ret.std() * np.sqrt(252),
        "Max drawdown": dd.min(),
        "Calmar": cagr / abs(dd.min()),
        "Avg SPY weight": w.mean(),
        "Turnover / yr": turnover.sum() / n * 252,
    }


def main():
    fc = pd.read_csv(OUT / "forecasts.csv", index_col=0, parse_dates=True)
    spy_ret, cash = load_inputs()
    idx = fc.index
    spy_ret, cash = spy_ret.reindex(idx), cash.reindex(idx)

    strategies = {"Buy & hold SPY": None, "Vol target: EWMA": "EWMA",
                  "Vol target: GARCH(1,1)-t": "GARCH(1,1)-t",
                  "Vol target: HMM 2-state": "HMM 2-state", "Vol target: HMM 3-state": "HMM 3-state"}
    curves, rows = {}, []
    for name, col in strategies.items():
        ret, w, to = run_strategy(spy_ret, cash, None if col is None else fc[col])
        curves[name] = (1 + ret).cumprod()
        rows.append({"strategy": name, **metrics(ret, cash, to, w)})

    table = pd.DataFrame(rows)
    table.to_csv(OUT / "backtest_metrics.csv", index=False)
    pd.DataFrame(curves).to_csv(OUT / "backtest_equity_curves.csv")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 5))
    for name, c in curves.items():
        ax.plot(c, lw=1.2, label=name, color="black" if "Buy" in name else None)
    ax.set_yscale("log")
    ax.set_title(f"Volatility targeting ({TARGET_VOL:.0%} target, no leverage, {COST_BPS}bp costs)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "figures" / "backtest_equity.png", dpi=130)
    plt.close(fig)
    print(table.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
