"""Pulls real data: prices from Yahoo (yfinance), macro from FRED, fundamentals from yfinance.

Needs internet. Writes the same four csv files that generate_sample_data.py writes.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DATA_RAW, END, FRED_SERIES, INDEX_ROW, START, UNIVERSE


def fetch_prices(tickers):
    import yfinance as yf

    raw = yf.download(tickers, start=START, end=END, auto_adjust=False,
                      group_by="ticker", progress=False, threads=True)
    frames = []
    for t in tickers:
        if t not in raw.columns.get_level_values(0):
            print(f"  no price data for {t}, skipping")
            continue
        df = raw[t].dropna(how="all").reset_index()
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        df["ticker"] = t
        frames.append(df[["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]])
    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    return out


def fetch_fred(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url)
    df.columns = ["date", "value"]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")  # FRED uses "." for missing
    df = df.dropna()
    df = df[(df["date"] >= START) & (df["date"] <= END)]
    df.insert(0, "series_id", series_id)
    return df


def fetch_fundamentals(tickers):
    import yfinance as yf

    def pick(frame, names):
        for n in names:
            if n in frame.index:
                return frame.loc[n]
        return pd.Series(dtype=float)

    rows = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            fin, bs = tk.financials, tk.balance_sheet
            rev = pick(fin, ["Total Revenue", "Operating Revenue"])
            ni = pick(fin, ["Net Income", "Net Income Common Stockholders"])
            debt = pick(bs, ["Total Debt"])
            eq = pick(bs, ["Stockholders Equity", "Common Stock Equity"])
            for d in rev.index:
                rows.append({
                    "ticker": t,
                    "period_end": pd.Timestamp(d).strftime("%Y-%m-%d"),
                    "revenue": rev.get(d),
                    "net_income": ni.get(d),
                    "total_debt": debt.get(d),
                    "total_equity": eq.get(d),
                })
        except Exception as e:
            print(f"  fundamentals failed for {t}: {e}")
    return pd.DataFrame(rows).dropna(subset=["revenue", "net_income", "total_equity"])


def main():
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    tickers = list(UNIVERSE) + list(INDEX_ROW)

    print("prices...")
    fetch_prices(tickers).to_csv(DATA_RAW / "prices.csv", index=False)

    print("macro...")
    pd.concat([fetch_fred(s) for s in FRED_SERIES]).to_csv(DATA_RAW / "macro.csv", index=False)

    print("fundamentals (yfinance only gives the last few years)...")
    fetch_fundamentals(list(UNIVERSE)).to_csv(DATA_RAW / "fundamentals.csv", index=False)

    comp = pd.DataFrame([(t, n, s) for t, (n, s) in {**UNIVERSE, **INDEX_ROW}.items()],
                        columns=["ticker", "name", "sector"])
    comp.to_csv(DATA_RAW / "companies.csv", index=False)
    (DATA_RAW / "SOURCE").write_text("yfinance+fred")
    print("done")


if __name__ == "__main__":
    main()
