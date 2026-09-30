import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DATA_RAW, DB_PATH, ROOT


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())

    companies = pd.read_csv(DATA_RAW / "companies.csv")
    prices = pd.read_csv(DATA_RAW / "prices.csv")
    macro = pd.read_csv(DATA_RAW / "macro.csv")
    fund = pd.read_csv(DATA_RAW / "fundamentals.csv")

    # drop rows the schema would reject anyway, and say so
    bad = prices["adj_close"].isna() | prices["close"].isna()
    if bad.any():
        print(f"dropping {bad.sum()} price rows with missing close")
        prices = prices[~bad]
    prices = prices.drop_duplicates(["ticker", "date"])

    period = pd.to_datetime(fund["period_end"])
    fund["available_date"] = (period + pd.Timedelta(days=90)).dt.strftime("%Y-%m-%d")
    fund["horizon_date"] = (period + pd.Timedelta(days=90 + 365)).dt.strftime("%Y-%m-%d")

    for name, df in [("companies", companies), ("prices", prices), ("macro", macro), ("fundamentals", fund)]:
        df.to_sql(name, con, if_exists="append", index=False)

    source = (DATA_RAW / "SOURCE").read_text().strip() if (DATA_RAW / "SOURCE").exists() else "unknown"
    con.executemany("INSERT INTO meta VALUES (?, ?)",
                    [("source", source), ("loaded_at", datetime.now().isoformat(timespec="seconds"))])
    con.commit()

    for t in ["companies", "prices", "macro", "fundamentals"]:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: {n:,} rows")
    print(f"data source: {source}")
    con.close()


if __name__ == "__main__":
    main()
