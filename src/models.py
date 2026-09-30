"""Walk-forward 1-day-ahead variance forecasts for SPY.

Models: rolling 21d, EWMA, GARCH(1,1)-t, VIX bucket, 2 and 3 state HMM.
Everything is refit on an expanding window every REFIT_EVERY days, and the hidden state
probabilities are filtered forward only (hmmlearn's predict_proba is smoothed, which would
peek at the future, so the filter is written by hand below).
"""
import sqlite3
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model
from hmmlearn.hmm import GaussianHMM
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DB_PATH, INDEX_TICKER, OUT

MIN_TRAIN = 756      # about 3 years before the first forecast
REFIT_EVERY = 63     # about a quarter
EWMA_LAMBDA = 0.94
VIX_EDGES = [15, 25]

MODELS = ["Rolling 21d", "EWMA", "GARCH(1,1)-t", "VIX bucket", "HMM 2-state", "HMM 3-state"]


def load_market():
    con = sqlite3.connect(DB_PATH)
    px = pd.read_sql("SELECT date, adj_close FROM prices WHERE ticker = ? ORDER BY date", con,
                     params=(INDEX_TICKER,), parse_dates=["date"]).set_index("date")["adj_close"]
    vix = pd.read_sql("SELECT date, value FROM macro WHERE series_id = 'VIXCLS'", con,
                      parse_dates=["date"]).set_index("date")["value"]
    con.close()
    df = pd.DataFrame({"r": 100 * np.log(px).diff()}).dropna()   # log return in percent
    df["vix"] = vix.reindex(df.index).ffill()
    return df.dropna()


def normal_pdf(x, mu, var):
    return np.exp(-0.5 * (x - mu) ** 2 / var) / np.sqrt(2 * np.pi * var)


def filter_probs(r, pi, A, mu, var):
    """forward algorithm. row t is P(state_t | r_0..r_t)"""
    T, k = len(r), len(pi)
    out = np.empty((T, k))
    a = pi * normal_pdf(r[0], mu, var)
    out[0] = a / a.sum()
    for t in range(1, T):
        a = (out[t - 1] @ A) * normal_pdf(r[t], mu, var)
        s = a.sum()
        out[t] = a / s if s > 0 else out[t - 1] @ A
    return out


def fit_hmm(x, k, n_init=3):
    best, best_ll = None, -np.inf
    for seed in range(n_init):
        m = GaussianHMM(n_components=k, covariance_type="diag", n_iter=200, tol=1e-4, random_state=seed)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m.fit(x)
                ll = m.score(x)
        except Exception:
            continue
        if ll > best_ll:
            best, best_ll = m, ll
    if best is None:
        raise RuntimeError("hmm fit failed on every init")
    mu = best.means_.reshape(k)
    var = np.maximum(np.asarray(best.covars_).reshape(k), 1e-6)
    return best.startprob_, best.transmat_, mu, var


def fit_garch(r_train):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = arch_model(r_train, mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
    p = res.params
    sigma2_last = float(res.conditional_volatility[-1] ** 2)
    return p["mu"], p["omega"], p["alpha[1]"], p["beta[1]"], sigma2_last


def ewma_series(r):
    s2 = np.var(r[:30])
    out = np.empty(len(r))
    for t, x in enumerate(r):
        s2 = EWMA_LAMBDA * s2 + (1 - EWMA_LAMBDA) * x * x
        out[t] = s2          # forecast for t+1 using data up to t
    return out


def walk_forward(df):
    r = df["r"].to_numpy()
    vix = df["vix"].to_numpy()
    n = len(r)
    ew = ewma_series(r)
    rows = []

    garch = None
    hmm = {}      # k -> dict(params, alpha)
    bucket_means = None

    for t in range(MIN_TRAIN - 1, n - 1):
        if (t - (MIN_TRAIN - 1)) % REFIT_EVERY == 0:
            mu, omega, a, b, s2 = fit_garch(r[: t + 1])
            garch = dict(mu=mu, omega=omega, alpha=a, beta=b, h=omega + a * (r[t] - mu) ** 2 + b * s2)

            for k in (2, 3):
                pi, A, m, v = fit_hmm(r[: t + 1].reshape(-1, 1), k)
                alpha_t = filter_probs(r[: t + 1], pi, A, m, v)[-1]
                hmm[k] = dict(A=A, mu=m, var=v, alpha=alpha_t)

            # mean squared next-day return for each yesterday-vix bucket, training data only
            b_idx = np.digitize(vix[:t], VIX_EDGES)
            nxt = r[1 : t + 1] ** 2
            overall = nxt.mean()
            bucket_means = np.array([nxt[b_idx == i].mean() if (b_idx == i).sum() > 20 else overall
                                     for i in range(len(VIX_EDGES) + 1)])
        else:
            g = garch
            s2 = g["h"]
            g["h"] = g["omega"] + g["alpha"] * (r[t] - g["mu"]) ** 2 + g["beta"] * s2
            for k, h in hmm.items():
                a = (h["alpha"] @ h["A"]) * normal_pdf(r[t], h["mu"], h["var"])
                s = a.sum()
                h["alpha"] = a / s if s > 0 else h["alpha"] @ h["A"]

        row = {"date": df.index[t + 1], "r": r[t + 1], "vix_prev": vix[t]}
        row["Rolling 21d"] = np.mean(r[t - 20 : t + 1] ** 2)
        row["EWMA"] = ew[t]
        row["GARCH(1,1)-t"] = garch["h"]
        row["VIX bucket"] = bucket_means[np.digitize(vix[t], VIX_EDGES)]
        for k, name in [(2, "HMM 2-state"), (3, "HMM 3-state")]:
            h = hmm[k]
            p_next = h["alpha"] @ h["A"]
            row[name] = float(p_next @ (h["var"] + h["mu"] ** 2))
            if k == 2:
                row["p_high_vol"] = float(p_next[np.argmax(h["var"])])
        rows.append(row)

    return pd.DataFrame(rows).set_index("date")


def qlike(y, h):
    return np.mean(np.log(h) + y / h)


def dm_test(loss_a, loss_b):
    """diebold-mariano on the loss differential with newey-west variance. negative stat = a is better"""
    d = np.asarray(loss_a) - np.asarray(loss_b)
    T = len(d)
    lag = int(T ** (1 / 3))
    dc = d - d.mean()
    lrv = dc @ dc / T
    for L in range(1, lag + 1):
        lrv += 2 * (1 - L / (lag + 1)) * (dc[L:] @ dc[:-L]) / T
    stat = d.mean() / np.sqrt(lrv / T)
    return stat, 2 * (1 - stats.norm.cdf(abs(stat)))


def qlike_loss(y, h):
    return np.log(h) + y / h


def evaluate(fc):
    y = fc["r"].to_numpy() ** 2      # squared return is a noisy but unbiased proxy for variance
    rows = []
    for m in MODELS:
        h = fc[m].to_numpy()
        slope, intercept, rval, _, _ = stats.linregress(h, y)
        if m == "GARCH(1,1)-t":
            stat, p = np.nan, np.nan
        else:
            stat, p = dm_test(qlike_loss(y, h), qlike_loss(y, fc["GARCH(1,1)-t"].to_numpy()))
        rows.append({"model": m, "QLIKE": qlike(y, h), "MSE": np.mean((y - h) ** 2),
                     "MZ_R2": rval ** 2, "DM_stat_vs_GARCH": stat, "DM_pvalue": p})
    metrics = pd.DataFrame(rows).sort_values("QLIKE").reset_index(drop=True)

    bucket = np.digitize(fc["vix_prev"], VIX_EDGES)
    names = ["VIX<15", "VIX 15-25", "VIX 25+"]
    rr = []
    for i, nm in enumerate(names):
        mask = bucket == i
        if mask.sum() < 20:
            continue
        for m in MODELS:
            rr.append({"vix_bucket": nm, "n_days": int(mask.sum()), "model": m,
                       "QLIKE": qlike(y[mask], fc[m].to_numpy()[mask])})
    by_regime = pd.DataFrame(rr)
    return metrics, by_regime


def make_figures(fc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = OUT / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    ann = lambda h: np.sqrt(h * 252)
    realised = np.sqrt((fc["r"] ** 2).rolling(21).mean() * 252)

    fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    ax[0].plot(realised, color="0.6", lw=1, label="realised vol (21d)")
    for m in ["EWMA", "GARCH(1,1)-t", "HMM 2-state"]:
        ax[0].plot(ann(fc[m]), lw=1, label=m)
    ax[0].set_ylabel("annualised vol, %")
    ax[0].set_title("SPY one-day-ahead volatility forecasts (out of sample)")
    ax[0].legend(loc="upper right", fontsize=8)
    ax[1].fill_between(fc.index, fc["p_high_vol"], color="tab:red", alpha=0.5)
    ax[1].set_ylabel("P(high-vol state)")
    ax[1].set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(fig_dir / "vol_forecasts.png", dpi=130)
    plt.close(fig)


def main():
    df = load_market()
    print(f"{len(df)} daily returns, first forecast after {MIN_TRAIN} days")
    fc = walk_forward(df)
    metrics, by_regime = evaluate(fc)
    OUT.mkdir(exist_ok=True)
    fc.to_csv(OUT / "forecasts.csv")
    metrics.to_csv(OUT / "model_metrics.csv", index=False)
    by_regime.to_csv(OUT / "model_metrics_by_regime.csv", index=False)
    make_figures(fc)
    print(metrics.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
