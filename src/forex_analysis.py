"""
Why PCA pair analysis WORKS on forex crosses (and how it compares with gold/silver).

    python forex_analysis.py

1. Correlation heatmap: 9 currencies + gold + silver, each as value in USD, daily returns 2010-2026.
2. PCA (hourly, full sample): how much each factor explains (scree) and what it is made of (loadings).
   PC1 = the dollar against everything, PC2 = currencies vs metals, PC3 = risk-on (AUD, NZD, CAD)
   vs safe havens (JPY, CHF).
3. Does each cross's leftover come back? Out-of-sample PCA residual of the 23 crosses (daily model:
   window 120 days, re-fit every 5, 3 factors removed), variance ratio over 5 / 10 / 20 days,
   next to gold/silver's leftover (gold_silver_analysis.py). <1 = comes back.
4. Typical distance of each cross from its own 1-year average vs the gold/silver ratio.
5. Daily residual strategy (tf_strategy.py walk-forward choice, swap-free): trades and return per year.

Output: data/forex/*.csv, *.png
"""
from dataclasses import replace

import sys

import matplotlib
if "ipykernel" not in sys.modules:  # scripts save PNGs without a window; notebooks show charts inline
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import fx_pca_strategy
import tf_strategy as T
from fx_pca_strategy import CCYS, ROOT, Params, model_signals, variance_ratio
from gold_silver_analysis import load_panel, residual_returns

OUT = ROOT / "data" / "forex"
SPLIT = T.SPLIT
# chosen on 2010-2018 only by: python tf_strategy.py --tf D1 --universe all --swap none
CHOSEN = dict(window=120, entry=2.5, exit=0.5, max_hl=10)
KEPT = ["AUDNZD", "EURGBP", "AUDCAD", "NZDCAD", "EURNOK", "EURSEK", "EURJPY", "GBPJPY", "AUDJPY",
        "EURAUD", "EURNZD", "GBPCAD", "NZDCHF"]


def load_d1():
    T.CROSSES = fx_pca_strategy.CROSSES_ALL
    T.SWAP = "none"
    return T.load("D1")


def fx_trades(data=None):
    """Trades and daily returns of the chosen D1 setup on the kept crosses (swap-free)."""
    cur, crs, sp, sw = load_d1() if data is None else data
    cfg = T.TF["D1"]
    prm = replace(Params(), step=cfg["step"], max_hold=int(3 * CHOSEN["max_hl"]), bars_per_year=cfg["per_year"],
                  vol_lookback=CHOSEN["window"], **CHOSEN)
    per, sig, idx = T.run_tf(cur, crs, sp, sw, prm)
    tr = pd.concat([per[s][2].assign(symbol=s) for s in KEPT if len(per[s][2])], ignore_index=True)
    return tr, pd.Series(sum(per[s][0] for s in KEPT), index=idx)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)
    data = load_d1()
    cur, crs = data[0], data[1]
    names = list(T.CROSSES)
    labels = CCYS
    print(f"Data: HistData daily candles (17:00 New York close), {cur.index[0]:%Y-%m-%d} -> {cur.index[-1]:%Y-%m-%d}")

    # ---- 1. correlations
    dr = np.log(cur[CCYS]).diff().dropna()
    corr = dr.corr()
    corr.to_csv(OUT / "correlation.csv")
    print("\n1. Correlation of daily returns (each currency in USD):")
    print(corr.round(2).to_string())

    # ---- 2. PCA structure (hourly, as in the model)
    h = pd.read_csv(ROOT / "data/histdata_fx/currencies_1h.csv", index_col=0, parse_dates=True)[CCYS].dropna()
    r = np.log(h).diff().dropna()
    z = (r - r.mean()) / r.std()
    vals, vecs = np.linalg.eigh(np.corrcoef(z.T))
    o = vals.argsort()[::-1]
    share = pd.Series(vals[o] / vals.sum() * 100, index=[f"PC{i + 1}" for i in range(len(CCYS))])
    load = pd.DataFrame(vecs[:, o[:3]], index=CCYS, columns=["PC1", "PC2", "PC3"])
    load = load * np.sign(load.loc["EUR"])
    load["PC2"] *= -np.sign(load.loc["XAU", "PC2"])         # orient PC2: currencies positive, metals negative
    load["PC3"] *= np.sign(load.loc["AUD", "PC3"])          # orient PC3: risk-on currencies positive
    print("\n2. PCA, hourly 2010-2026: variance explained %")
    print("   " + "  ".join(f"{k} {v:.0f}" for k, v in share.items()) + f"   (first 3 together: {share.iloc[:3].sum():.0f}%)")
    print("loadings of the first 3 factors:"); print(load.round(2).T.to_string())
    share.to_csv(OUT / "pca_share.csv"); load.to_csv(OUT / "pca_loadings.csv")

    # ---- 3. does the leftover come back?
    rd = np.log(cur[CCYS]).diff().to_numpy()[1:]
    idx = cur.index[1:]
    pairs = [(CCYS.index(a), CCYS.index(b)) for a, b in T.CROSSES.values()]
    _, _, resid, _ = model_signals(rd, pairs, replace(Params(), window=CHOSEN["window"], step=5, k=3))
    hz = {"5 days": 5, "10 days": 10, "20 days": 20}
    vr = pd.DataFrame({n: {k: variance_ratio(resid[:, j], d) for k, d in hz.items()} for j, n in enumerate(names)}).T
    gs = residual_returns(load_panel())
    vr.loc["GOLD/SILVER"] = {k: variance_ratio(gs, d * 24) for k, d in hz.items()}
    vr = vr.sort_values("10 days")
    print("\n3. Variance ratio of the PCA leftover, out-of-sample.  <1 comes back,  >=1 drifts/trends")
    print(vr.round(2).to_string())
    fx = vr.drop("GOLD/SILVER")
    print(f"   forex crosses below 1 at 10 days: {(fx['10 days'] < 1).sum()} of {len(fx)} "
          f"(median {fx['10 days'].median():.2f});  gold/silver: {vr.loc['GOLD/SILVER', '10 days']:.2f}")
    vr.to_csv(OUT / "variance_ratio.csv")

    # ---- 4. distance from 1-year average
    lp = np.log(crs[names])
    dev = (lp - lp.rolling(260).mean()).abs().median() * 100
    hx = pd.read_csv(ROOT / "data/histdata_fx/currencies_1h.csv", index_col=0, parse_dates=True)[["XAU", "XAG"]].dropna()
    g = np.log((hx["XAU"] / hx["XAG"]).resample("D").last().dropna())
    dev["GOLD/SILVER"] = (g - g.rolling(260).mean()).abs().median() * 100
    dev = dev.sort_values()
    print("\n4. Typical distance from its own 1-year average (median, %):")
    print("   " + "  ".join(f"{k} {v:.1f}" for k, v in dev.items()))
    dev.to_csv(OUT / "distance_from_1y_avg.csv")

    # ---- 5. strategy per year
    tr, ret = fx_trades(data)
    y = tr.groupby(tr["entry"].dt.year).agg(trades=("net", "size"), win_pct=("net", lambda x: (x > 0).mean() * 100),
                                            hold_days=("bars", "mean"))
    y["return %"] = ret.groupby(ret.index.year).sum() * 100
    y["period"] = np.where(y.index < SPLIT.year, "train", "test")
    print(f"\n5. Daily residual strategy, {len(KEPT)} crosses, swap-free, costs = Vantage spreads + commission:")
    print(y.round(1).to_string())
    for p, m in [("train 2010-2018", ret.index < SPLIT), ("test 2019-latest", ret.index >= SPLIT)]:
        rr = ret[m]
        n = ((tr["entry"] < SPLIT) if p.startswith("train") else (tr["entry"] >= SPLIT)).sum()
        print(f"   {p}: {n} trades, Sharpe {rr.mean() / rr.std() * np.sqrt(260):.2f}, {rr.mean() * 260 * 100:.1f}%/yr")
    y.to_csv(OUT / "trades_by_year.csv")

    # ---- charts
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(labels)), labels); ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(corr.iloc[i, j]) > 0.6 else "black")
    fig.colorbar(im, fraction=0.046)
    ax.set_title("Daily return correlation, each currency in USD, 2010-2026")
    fig.tight_layout(); fig.savefig(OUT / "correlation_heatmap.png", dpi=150)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    share.plot.bar(ax=axes[0], color="#3b6ea5", rot=0)
    axes[0].plot(range(len(share)), share.cumsum(), color="#d9534f", marker="o", lw=1, label="cumulative")
    axes[0].set_title("Variance explained by each factor (%)"); axes[0].legend(fontsize=8)
    for c in axes[0].containers:
        axes[0].bar_label(c, fmt="%.0f", fontsize=8)
    load.plot.bar(ax=axes[1], rot=0, color=["#3b6ea5", "#5cb85c", "#d4a017"])
    axes[1].axhline(0, color="black", lw=0.6)
    axes[1].set_title("Loadings\nPC1 = the dollar, PC2 = currencies vs metals, PC3 = risk-on vs safe havens", fontsize=10)
    fig.tight_layout(); fig.savefig(OUT / "pca_forex.png", dpi=150)

    fig, ax = plt.subplots(figsize=(12, 4))
    col = ["#7a5c00" if n == "GOLD/SILVER" else "#3b6ea5" for n in vr.index]
    ax.bar(vr.index, vr["10 days"], color=col)
    ax.axhline(1, color="red", ls="--", lw=1, label="1 = random walk (no coming back)")
    ax.set_title("Does the PCA leftover come back? Variance ratio over 10 days (below 1 = yes)")
    ax.tick_params(axis="x", rotation=60); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "variance_ratio_vs_gold.png", dpi=150)
    print(f"\ncharts in {OUT}")


if __name__ == "__main__":
    main()
