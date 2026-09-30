import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DB_PATH, OUT, ROOT


def main():
    (OUT / "sql").mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript((ROOT / "sql" / "views.sql").read_text())

    for f in sorted((ROOT / "sql" / "queries").glob("q*.sql")):
        df = pd.read_sql(f.read_text(), con)
        df.to_csv(OUT / "sql" / f"{f.stem}.csv", index=False)
        print(f"{f.stem}: {len(df)} rows")
    con.close()


if __name__ == "__main__":
    main()
