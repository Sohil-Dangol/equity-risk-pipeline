import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import DB_PATH  # noqa: E402
import models  # noqa: E402

needs_db = pytest.mark.skipif(not DB_PATH.exists(), reason="run the pipeline first")


@needs_db
def test_sql_returns_match_pandas():
    con = sqlite3.connect(DB_PATH)
    sql = pd.read_sql("SELECT date, ret FROM daily_returns WHERE ticker = 'AAPL' ORDER BY date", con)
    px = pd.read_sql("SELECT date, adj_close FROM prices WHERE ticker = 'AAPL' ORDER BY date", con)
    con.close()
    expected = px["adj_close"].pct_change().dropna().to_numpy()
    assert np.allclose(sql["ret"].to_numpy(), expected)


@needs_db
def test_sql_beta_matches_regression():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""SELECT a.ret AS x, b.ret AS y FROM daily_returns a
                        JOIN daily_returns b USING (date)
                        WHERE a.ticker = 'SPY' AND b.ticker = 'MSFT'""", con)
    sql_beta = pd.read_csv(ROOT / "outputs" / "sql" / "q5_beta_vs_spy.csv").set_index("ticker").loc["MSFT", "beta"]
    con.close()
    slope = np.polyfit(df["x"], df["y"], 1)[0]
    assert abs(slope - sql_beta) < 1e-3


@needs_db
def test_no_missing_or_bad_prices():
    con = sqlite3.connect(DB_PATH)
    bad = con.execute("SELECT COUNT(*) FROM prices WHERE adj_close IS NULL OR adj_close <= 0").fetchone()[0]
    con.close()
    assert bad == 0


def test_hmm_filter_is_a_probability_and_causal():
    rng = np.random.default_rng(0)
    r = np.r_[rng.normal(0, 0.5, 200), rng.normal(0, 3, 100)]
    pi, A = np.array([0.5, 0.5]), np.array([[0.95, 0.05], [0.1, 0.9]])
    mu, var = np.array([0.0, 0.0]), np.array([0.25, 9.0])
    full = models.filter_probs(r, pi, A, mu, var)
    assert np.allclose(full.sum(axis=1), 1)
    # filtering on a truncated series must give identical early rows (no lookahead)
    part = models.filter_probs(r[:150], pi, A, mu, var)
    assert np.allclose(full[:150], part)
    assert full[-1, 1] > 0.9      # ends deep in the high vol block


def test_qlike_prefers_the_true_variance():
    rng = np.random.default_rng(1)
    y = rng.normal(0, 2, 20000) ** 2
    assert models.qlike(y, np.full_like(y, 4.0)) < models.qlike(y, np.full_like(y, 2.0))
    assert models.qlike(y, np.full_like(y, 4.0)) < models.qlike(y, np.full_like(y, 8.0))


def test_dm_test_detects_a_better_forecast():
    rng = np.random.default_rng(2)
    y = rng.normal(0, 2, 3000) ** 2
    good, bad = np.full_like(y, 4.0), np.full_like(y, 12.0)
    stat, p = models.dm_test(models.qlike_loss(y, good), models.qlike_loss(y, bad))
    assert stat < 0 and p < 0.01
