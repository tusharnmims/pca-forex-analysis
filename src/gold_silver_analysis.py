"""
Why PCA pair trading FAILS on gold vs silver.

    python gold_silver_analysis.py

1. PCA on hourly returns of gold, silver and the US dollar index (Vantage MT5, 2019-2026):
   how much each factor explains and what it is made of. The 3rd factor = silver vs gold.
2. Does that silver-vs-gold leftover come back (mean-revert)? Variance ratio of its out-of-sample
   returns over 1 to 20 days. Below 1 = comes back, about 1 or above = drifts / trends.
3. The gold/silver ratio 2010-2026 (HistData): it trends for years instead of oscillating.
4. Backtest of the residual strategy (pca_strategy.py): trades and return per year.

Output: data/gold_silver/*.csv, *.png
"""
import sys

import matplotlib
if "ipykernel" not in sys.modules:  # scripts save PNGs without a window; notebooks show charts inline
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fx_pca_strategy import variance_ratio
from pca_strategy import ASSETS, ROOT, Params, backtest, signals

OUT = ROOT / "data" / "gold_silver"
HORIZONS_H = {"1 day": 24, "5 days": 120, "10 days": 240, "20 days": 480}


def load_panel():
    return pd.read_csv(ROOT / "data/mt5/panel_1h.csv", index_col=0, parse_dates=True)


def residual_returns(panel, prm=Params()):
    """Out-of-sample returns of the silver-vs-gold (PC3) portfolio, model re-fit on past data only."""
    r = np.log(panel[ASSETS]).diff().to_numpy()[1:]
    s, hl, W, vol = signals(r, prm)
    return pd.Series((r[:, :2] * W).sum(1), index=panel.index[1:]).where(~np.isnan(W[:, 0])).dropna()


def gs_trades(panel=None):
    """Trades of the gold/silver residual strategy with its default settings."""
    eq, tr = backtest(load_panel() if panel is None else panel, Params())
    return eq, tr


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)
    panel = load_panel()
    print(f"Data: Vantage MT5 hourly, {panel.index[0]:%Y-%m-%d} -> {panel.index[-1]:%Y-%m-%d}, {len(panel):,} bars")

    # ---- 1. PCA structure
    r = np.log(panel[ASSETS]).diff().dropna()
    z = (r - r.mean()) / r.std()
    vals, vecs = np.linalg.eigh(np.corrcoef(z.T))
    o = vals.argsort()[::-1]
    load = pd.DataFrame(vecs[:, o], index=["gold", "silver", "USD index"], columns=["PC1", "PC2", "PC3"])
    load = load * np.sign(load.loc["gold"])
    share = pd.Series(vals[o] / vals.sum() * 100, index=load.columns)
    print("\n1. PCA on gold, silver, USD index (hourly, full sample)")
    print("variance explained %:  " + "  ".join(f"{k} {v:.0f}%" for k, v in share.items()))
    print("loadings:"); print(load.round(2).to_string())
    print("   PC1 = all three together (metals priced in dollars), PC2 = the dollar on its own,"
          " PC3 = silver vs gold (the only thing left to trade)")
    print("correlations:"); print(r.corr().round(2).to_string())

    # ---- 2. does the leftover come back?
    res = residual_returns(panel)
    vr = pd.Series({k: variance_ratio(res, h) for k, h in HORIZONS_H.items()})
    print("\n2. Variance ratio of the silver-vs-gold leftover (out-of-sample).  <1 comes back,  >=1 drifts/trends")
    print("   " + "  ".join(f"{k}: {v:.2f}" for k, v in vr.items()))

    # ---- 3. the ratio itself, 2010-2026
    h = pd.read_csv(ROOT / "data/histdata_fx/currencies_1h.csv", index_col=0, parse_dates=True)[["XAU", "XAG"]].dropna()
    ratio = (h["XAU"] / h["XAG"]).resample("D").last().dropna()
    lr = np.log(ratio)
    dev = (lr - lr.rolling(260).mean()).abs().dropna() * 100
    yr = ratio.groupby(ratio.index.year).agg(["first", "min", "max", "last"])
    print("\n3. Gold/silver ratio by year (HistData daily):")
    print(yr.round(1).to_string())
    print(f"   typical distance from its own 1-year average: {dev.median():.1f}% (median), "
          f"{dev.quantile(.9):.1f}% (90th pct)")

    # ---- 4. backtest result per year
    eq, tr = gs_trades(panel)
    y = tr.groupby(tr["entry"].dt.year).agg(trades=("net", "size"), win_pct=("net", lambda x: (x > 0).mean() * 100))
    y["return %"] = eq["ret"].groupby(eq.index.year).sum() * 100
    print("\n4. Residual strategy backtest (pca_strategy.py, costs included):")
    print(y.round(1).to_string())
    print(f"   total {len(tr)} trades, Sharpe {eq['ret'].mean() / eq['ret'].std() * np.sqrt(5900):.2f}, "
          f"{(y['return %'] < 0).sum()} of {len(y)} years negative")

    share.to_csv(OUT / "pca_share.csv"); load.to_csv(OUT / "pca_loadings.csv")
    vr.to_csv(OUT / "variance_ratio.csv"); yr.to_csv(OUT / "ratio_by_year.csv"); y.to_csv(OUT / "trades_by_year.csv")

    # ---- charts
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    share.plot.bar(ax=axes[0], color="#3b6ea5", rot=0)
    axes[0].set_title("Variance explained by each factor (%)")
    for c in axes[0].containers:
        axes[0].bar_label(c, fmt="%.0f%%", fontsize=9)
    load.T.plot.bar(ax=axes[1], rot=0, color=["#d4a017", "#9aa5b1", "#2e7d32"])
    axes[1].axhline(0, color="black", lw=0.6)
    axes[1].set_title("What each factor is made of (loadings)")
    fig.tight_layout(); fig.savefig(OUT / "pca_gold_silver.png", dpi=150)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(ratio.index, ratio, lw=0.8, color="#7a5c00")
    ax.set_title("Gold / silver ratio 2010-2026: long trends, not a stable band")
    ax.set_ylabel("ounces of silver per ounce of gold")
    fig.tight_layout(); fig.savefig(OUT / "gold_silver_ratio.png", dpi=150)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    vr.plot.bar(ax=ax, color="#7a5c00", rot=0)
    ax.axhline(1, color="red", ls="--", lw=1, label="1 = random walk")
    ax.set_title("Silver-vs-gold leftover: variance ratio")
    ax.legend(fontsize=8)
    for c in ax.containers:
        ax.bar_label(c, fmt="%.2f", fontsize=9)
    fig.tight_layout(); fig.savefig(OUT / "variance_ratio.png", dpi=150)
    print(f"\ncharts in {OUT}")


if __name__ == "__main__":
    main()
