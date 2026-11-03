"""
Does PCA tell us WHEN NOT TO TRADE pair relationships?

    python regime_analysis.py

1. Market concentration: each day, PCA on the previous 20 trading days of hourly returns (9 currencies +
   gold + silver, as value in USD). Share of variance explained by the first factor = how much
   "everything moves together". (Absorption ratio idea, Kritzman et al. 2011.)
2. Regimes: days split into thirds by that share -> low / medium / high concentration.
   (Low = currencies moving on their own stories; high = one force, mostly the dollar, moves them all.)
3. What happens to the 23 crosses in each regime, measured over the FOLLOWING days only:
     - when a pair stretches (|s| crosses 2), does it snap back (|s| <= 0.5) within 10 days,
       or break further (|s| >= 4 / model invalid)?
     - share of days where the pair's model shows mean reversion at all (0 < b < 1)
     - half-life of the pair's residual
     - volatility of the crosses over the next 20 days
4. Known market shocks: where was the concentration measure around them?
5. Live-style "no-trade" rule: a day is no-trade when concentration is in the bottom third of all
   PAST days (no hindsight). Share of tradable days per year.
6. Trades of the daily forex strategy (forex_analysis.py) and the gold/silver strategy
   (gold_silver_analysis.py), split by whether they were opened on a no-trade day.

Output: data/regime/*.csv, *.png
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
from fx_pca_strategy import CCYS, ROOT, Params, model_signals

OUT = ROOT / "data" / "regime"
WIN_H = 480          # hourly bars in the concentration window (~20 trading days)
FWD = 10             # days to wait for a stretched pair to snap back
EVENTS = {
    "2010-05-06": "Euro crisis / flash crash", "2011-08-08": "US downgrade",
    "2015-01-15": "SNB drops CHF floor", "2016-06-24": "Brexit vote",
    "2020-03-16": "COVID crash", "2022-09-26": "UK gilt crisis", "2025-04-03": "US tariff shock",
}


def pc1_share(z):
    vals = np.linalg.eigvalsh(np.corrcoef(z.T))
    return vals[-1] / vals.sum()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)

    # ---- daily candles + out-of-sample pair model (same settings as the D1 study)
    T.CROSSES = fx_pca_strategy.CROSSES_ALL
    cur, crs, *_ = T.load("D1")
    r = np.log(cur[CCYS]).diff().to_numpy()[1:]
    idx = cur.index[1:]
    names = list(T.CROSSES)
    pairs = [(CCYS.index(a), CCYS.index(b)) for a, b in T.CROSSES.values()]
    prm = replace(Params(), window=120, step=5, k=3)
    s, hl, resid, _ = model_signals(r, pairs, prm)

    # ---- concentration from hourly returns, known at each daily close
    h = pd.read_csv(ROOT / "data/histdata_fx/currencies_1h.csv", index_col=0, parse_dates=True)[CCYS]
    hr = np.log(h.ffill(limit=3)).diff().dropna()
    pos = hr.index.searchsorted(idx, side="right")       # hourly bars up to and including the daily close
    share = np.full(len(idx), np.nan)
    share9 = np.full(len(idx), np.nan)
    hv = hr.to_numpy()
    for i, p in enumerate(pos):
        if p >= WIN_H:
            w = hv[p - WIN_H:p]
            share[i] = pc1_share(w)
            share9[i] = pc1_share(w[:, :9])
    conc = pd.Series(share, index=idx, name="pc1_share")
    q1, q2 = conc.quantile([1 / 3, 2 / 3])
    regime = pd.Series(np.where(conc <= q1, "low", np.where(conc <= q2, "medium", "high")), index=idx)
    regime[conc.isna()] = None
    print(f"First-factor share (20-day hourly PCA): median {conc.median():.0%}, "
          f"low <= {q1:.0%} < medium <= {q2:.0%} < high, max {conc.max():.0%}")
    print(f"corr with FX-only (9 currencies, no metals) version: {np.corrcoef(share[~np.isnan(share)], share9[~np.isnan(share)])[0, 1]:.2f}")

    # ---- stretched pairs: snap back or break?
    ev = []
    T_, P = s.shape
    for j in range(P):
        for t in range(1, T_ - FWD):
            if regime.iloc[t] is None or np.isnan(s[t, j]) or abs(s[t, j]) < 2 or \
                    (not np.isnan(s[t - 1, j]) and abs(s[t - 1, j]) >= 2):
                continue
            out = "neither"
            for f in range(t + 1, t + FWD + 1):
                x = s[f, j]
                if np.isnan(x) or abs(x) >= 4:
                    out = "broke"
                    break
                if abs(x) <= 0.5:
                    out = "snapped back"
                    break
            ev.append({"date": idx[t], "pair": names[j], "s": s[t, j], "regime": regime.iloc[t], "outcome": out})
    ev = pd.DataFrame(ev)
    ev.to_csv(OUT / "stretch_events.csv", index=False)

    order = ["low", "medium", "high"]
    tab = pd.crosstab(ev["regime"], ev["outcome"], normalize="index").reindex(order) * 100
    tab["events"] = ev["regime"].value_counts().reindex(order)

    # ---- model health + forward volatility per regime
    valid = pd.Series((~np.isnan(s)).mean(1), index=idx)
    med_hl = pd.Series(np.nanmedian(np.where(np.isnan(s), np.nan, hl), axis=1), index=idx)
    lr = np.log(crs[names].reindex(idx)).diff()
    fwd_vol = lr.abs().mean(1).rolling(20).mean().shift(-20) * np.sqrt(260) * np.sqrt(np.pi / 2) * 100
    health = pd.DataFrame({"pairs with mean reversion %": valid * 100, "median half-life (days)": med_hl,
                           "next-20d cross vol %/yr": fwd_vol, "regime": regime}).groupby("regime").mean().reindex(order)

    res = pd.concat([tab[["snapped back", "broke", "neither", "events"]], health], axis=1)
    res.to_csv(OUT / "regime_summary.csv")
    print(f"\nStretched pairs (|s| crosses 2) — what happens in the next {FWD} days, by regime on that day:")
    print(res.round(1).to_string())

    # by year: is it consistent?
    ev["year"] = ev["date"].dt.year
    yr = ev.assign(snap=ev["outcome"] == "snapped back").pivot_table(index="year", columns="regime",
                                                                     values="snap", aggfunc="mean")[order] * 100
    yr.to_csv(OUT / "snapback_by_year.csv")
    print("\nsnap-back % by year and regime:")
    print(yr.round(0).to_string())

    # ---- shocks
    print("\nKnown shocks: highest first-factor share in the 20 days after, and its percentile in 2010-2026:")
    rows = []
    for d, name in EVENTS.items():
        w = conc[(conc.index >= pd.Timestamp(d, tz="UTC")) & (conc.index < pd.Timestamp(d, tz="UTC") + pd.Timedelta(days=28))]
        if len(w) and w.notna().any():
            pk = w.max()
            rows.append({"date": d, "event": name, "peak share %": pk * 100,
                         "percentile": (conc < pk).mean() * 100, "regime at peak": regime[w.idxmax()]})
    shocks = pd.DataFrame(rows)
    shocks.to_csv(OUT / "shocks.csv", index=False)
    print(shocks.round(0).to_string(index=False))

    pd.DataFrame({"pc1_share": conc, "pc1_share_fx_only": share9, "regime": regime}).to_csv(OUT / "concentration_daily.csv")

    # ---- 5. live-style no-trade rule: cut-off from past days only (needs 1 year of history)
    cut = conc.expanding(min_periods=260).quantile(1 / 3).shift(1)
    live = (conc > cut).where(cut.notna() & conc.notna()).dropna().astype(bool)
    tradable = live.groupby(live.index.year).agg(days="size", tradable_pct=lambda x: x.mean() * 100)
    tradable["avg share %"] = conc.groupby(conc.index.year).mean() * 100
    low = ~live
    runs = low.groupby((low != low.shift()).cumsum()).agg(["first", "size"])
    spells = runs[runs["first"]]["size"]
    print(f"\nLive no-trade rule (bottom third of past days): tradable {live.mean() * 100:.0f}% of days overall")
    print(tradable.round(0).to_string())
    print(f"no-trade spells: {len(spells)}, median {spells.median():.0f} days, longest {spells.max()} days")
    tradable.to_csv(OUT / "tradable_days_by_year.csv")

    # ---- 6. trades opened on no-trade vs trade days
    from forex_analysis import fx_trades
    from gold_silver_analysis import gs_trades
    flag = pd.Series(np.where(live, "trade", "no-trade"), index=live.index)
    rows = []
    for name, tr in [("forex D1, 13 crosses", fx_trades()[0]), ("gold/silver H1", gs_trades()[1])]:
        tr = tr.assign(day=flag.reindex(tr["entry"], method="ffill").to_numpy()).dropna(subset=["day"])
        for (per, day), g in tr.groupby([np.where(tr["entry"] < T.SPLIT, "2010-18", "2019-26"), "day"]):
            rows.append({"strategy": name, "period": per, "opened on": day, "trades": len(g),
                         "win %": (g["net"] > 0).mean() * 100, "stopped out %": (g["reason"] == "stop").mean() * 100,
                         "avg net per trade %": g["net"].mean() * 100})
        rows += [{"strategy": name, "period": "all", "opened on": day, "trades": len(g),
                  "win %": (g["net"] > 0).mean() * 100, "stopped out %": (g["reason"] == "stop").mean() * 100,
                  "avg net per trade %": g["net"].mean() * 100} for day, g in tr.groupby("day")]
    bt = pd.DataFrame(rows).set_index(["strategy", "period", "opened on"]).sort_index()
    print("\nTrades by the day they were opened (costs included):")
    print(bt.round(2).to_string())
    bt.to_csv(OUT / "trades_by_regime.csv")

    # ---- charts
    fig, ax = plt.subplots(figsize=(13, 4.5))
    ax.plot(conc.index, conc * 100, lw=0.8, color="#3b6ea5")
    ax.axhspan(q2 * 100, 100, color="#d9534f", alpha=0.08, label="high concentration (top third)")
    ax.axhspan(0, q1 * 100, color="#5cb85c", alpha=0.08, label="low concentration (bottom third)")
    for d, name in EVENTS.items():
        ax.axvline(pd.Timestamp(d, tz="UTC"), color="grey", lw=0.7, ls="--")
        ax.text(pd.Timestamp(d, tz="UTC"), conc.max() * 100, " " + name, rotation=90, va="top", fontsize=7, color="#444")
    ax.set_ylim(conc.min() * 100 - 3, conc.max() * 100 + 2)
    ax.set_ylabel("variance explained by 1st factor, %")
    ax.set_title("How much do currencies move together? Rolling 20-day PCA, 2010-2026")
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "concentration.png", dpi=150)

    fig, ax = plt.subplots(figsize=(7, 4))
    tab[["snapped back", "broke", "neither"]].plot.bar(ax=ax, color=["#5cb85c", "#d9534f", "#bbbbbb"], rot=0)
    ax.set_ylabel(f"% of stretched pairs, next {FWD} days")
    ax.set_title("Stretched pairs by market concentration")
    ax.set_xlabel("share of movement explained by the 1st PCA factor")
    for c in ax.containers:
        ax.bar_label(c, fmt="%.0f", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "snapback_by_regime.png", dpi=150)

    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.bar(tradable.index.astype(str), tradable["tradable_pct"], color="#3b6ea5")
    ax.axhline(live.mean() * 100, color="grey", ls="--", lw=1, label=f"average {live.mean() * 100:.0f}%")
    ax.set_ylim(0, 105); ax.set_ylabel("% of trading days")
    ax.set_title("Days PCA marks as safe for pair trading, per year (rule uses past data only)")
    for c in ax.containers:
        ax.bar_label(c, fmt="%.0f", fontsize=8)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "tradable_days_by_year.png", dpi=150)
    print(f"\ncharts in {OUT}")


if __name__ == "__main__":
    main()
