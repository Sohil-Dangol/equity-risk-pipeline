"""Writes outputs/findings.md from the csv results. Numbers only, the interpretation is yours to write."""
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DB_PATH, OUT


def md(df, floatfmt="{:.3f}"):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.itertuples(index=False):
        cells = [floatfmt.format(v) if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    con = sqlite3.connect(DB_PATH)
    source = con.execute("SELECT value FROM meta WHERE key = 'source'").fetchone()[0]
    con.close()

    mm = pd.read_csv(OUT / "model_metrics.csv")
    bt = pd.read_csv(OUT / "backtest_metrics.csv")
    br = pd.read_csv(OUT / "model_metrics_by_regime.csv").pivot(index="model", columns="vix_bucket", values="QLIKE")
    sec = pd.read_csv(OUT / "sql" / "q2_sector_performance.csv")
    reg = pd.read_csv(OUT / "sql" / "q6_regime_performance.csv")
    fq = pd.read_csv(OUT / "sql" / "q7_fundamentals_vs_returns.csv")
    fc = pd.read_csv(OUT / "forecasts.csv", parse_dates=["date"])

    high = reg[reg["regime"].str.startswith("3")]["ann_vol_pct"].mean()
    low = reg[reg["regime"].str.startswith("1")]["ann_vol_pct"].mean()
    best_model = mm.iloc[0]
    buy = bt[bt["strategy"].str.startswith("Buy")].iloc[0]
    best_bt = bt.sort_values("Sharpe", ascending=False).iloc[0]

    out = [f"# Findings ({date.today():%d %b %Y})", ""]
    if source == "synthetic":
        out += ["> **These results come from synthetic data with regimes built in. They demonstrate that the pipeline works, "
                "not anything about real markets. Rerun with real data before quoting a number.**", ""]
    else:
        out += [f"Data source: {source}", ""]

    out += [f"Out-of-sample forecast window: {fc['date'].min():%Y-%m-%d} to {fc['date'].max():%Y-%m-%d} "
            f"({len(fc):,} days).", "",
            "## 1. Risk and return across VIX regimes (SQL)",
            f"Average sector volatility was {low:.1f}% when the prior-day VIX was below 15 and {high:.1f}% when it was 25 or above.",
            "", md(sec, "{:.2f}"), "",
            "## 2. Volatility forecast accuracy (SPY, walk-forward)",
            f"Best model by QLIKE: **{best_model['model']}** ({best_model['QLIKE']:.4f}). "
            "DM stat is against GARCH; negative means better, and p-values below 0.05 are conventional significance.",
            "", md(mm, "{:.4f}"), "", "QLIKE by prior-day VIX bucket:", "", md(br.reset_index(), "{:.4f}"), "",
            "## 3. Volatility-targeting backtest",
            f"Buy and hold: Sharpe {buy['Sharpe']:.2f}, max drawdown {buy['Max drawdown']:.1%}. "
            f"Best Sharpe among strategies: {best_bt['strategy']} at {best_bt['Sharpe']:.2f}.",
            "", md(bt, "{:.3f}"), "",
            "## 4. ROE quartile vs next-12-month return (SQL)", "", md(fq, "{:.1f}"), "",
            "## Caveats",
            "- The universe is today's large caps, so there is survivorship bias.",
            "- Squared daily returns are a noisy proxy for true variance; QLIKE is used because it copes with that.",
            "- Backtest costs are a flat 5bp of turnover and ignore weight drift, borrowing and taxes.",
            "- Fundamentals from yfinance cover only the last few years.", "",
            "## My interpretation", "", "_Write this yourself: what do the numbers say, and what would you test next?_", ""]
    (OUT / "findings.md").write_text("\n".join(out))
    print("wrote outputs/findings.md")


if __name__ == "__main__":
    main()
