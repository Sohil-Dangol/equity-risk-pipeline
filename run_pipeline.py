"""Runs everything: python run_pipeline.py --source synthetic|real"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STEPS = [
    ("load into database", "src/load_db.py"),
    ("run SQL analysis", "src/run_sql.py"),
    ("forecast models (takes a minute or two)", "src/models.py"),
    ("volatility-target backtest", "src/backtest.py"),
    ("excel dashboard", "src/build_excel.py"),
    ("findings report", "src/report.py"),
]


def run(script):
    subprocess.run([sys.executable, str(ROOT / script)], check=True, cwd=ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["synthetic", "real"], default="synthetic")
    args = ap.parse_args()

    first = "src/generate_sample_data.py" if args.source == "synthetic" else "src/fetch_data.py"
    print(f"\n== get data ({args.source})")
    run(first)
    for label, script in STEPS:
        print(f"\n== {label}")
        run(script)
    print("\nDone. Open outputs/risk_dashboard.xlsx and outputs/findings.md")
    print("Excel calculates the workbook formulas when you open it.")


if __name__ == "__main__":
    main()
