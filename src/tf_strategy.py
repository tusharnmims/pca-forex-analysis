"""
FX PCA residual mean reversion on H4 and D1 candles, walk-forward tested.

    python tf_strategy.py            # both timeframes
    python tf_strategy.py --tf D1
    python tf_strategy.py --tf D1 --universe all --swap none   # all 23 crosses, swap-free account

Candles are built from the hourly HistData files and close at the New York 17:00 rollover, like MT5 brokers
(D1 = one candle per trading day; H4 = six candles per day starting 17:00 NY).

Costs
    spread      Vantage's recorded spread (median of the hours inside each candle, 2019+);
                before 2019, each cross's median Vantage spread
    commission  0.003% per side (~$6 per 100k round turn)
    swap        current Vantage swap rates, ALWAYS charging the more expensive side (conservative),
                7 nights per 5 trading days (--swap none: swap-free account)

Price gaps in a cross's HistData file (e.g. AUDJPY 2012) are filled from its two USD majors (AUDJPY = AUDUSD x USDJPY).

Walk-forward
    TRAIN 2010-2018: pick parameters + crosses (positive before costs) by best after-cost Sharpe
    TEST  2019-latest: run that one choice untouched
"""
import argparse
from dataclasses import replace
from itertools import product

import numpy as np
import pandas as pd

import fx_pca_strategy
from fx_pca_strategy import CCYS, COMMISSION_PCT, ROOT, Params, backtest_one, model_signals
from pca_strategy import challenge

CROSSES = fx_pca_strategy.CROSSES  # set by --universe
SWAP = "worst"                     # set by --swap
SPLIT = pd.Timestamp("2019-01-01", tz="UTC")
TF = {
    # bars per trading day, bars per year, model re-fit step, grid
    "D1": {"per_day": 1, "per_year": 260, "step": 5,
           "grid": {"window": [60, 120, 250], "entry": [1.5, 2.0, 2.5], "exit": [0.0, 0.5], "max_hl": [5, 10, 20]}},
    "H4": {"per_day": 6, "per_year": 1560, "step": 6,
           "grid": {"window": [180, 360, 720], "entry": [1.5, 2.0, 2.5], "exit": [0.0, 0.5], "max_hl": [12, 30, 60]}},
}


# ----------------------------------------------------------------------------- data

def candle_key(idx, tf):
    """Group hourly UTC timestamps into candles that start at 17:00 New York (MT5 broker convention)."""
    shifted = idx.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)
    return shifted.floor("D" if tf == "D1" else "4h")


def to_candles(hourly, tf, how="last"):
    key = candle_key(hourly.index, tf)
    g = hourly.groupby(key)
    out = g.last() if how == "last" else g.median()
    stamps = hourly.index.to_series().groupby(key).last()  # stamp = last hour in the candle (UTC)
    out.index = pd.DatetimeIndex(stamps.reindex(out.index).to_list(), name="time_utc")
    return out


def load(tf):
    d = ROOT / "data/histdata_fx"
    cur_h = pd.read_csv(d / "currencies_1h.csv", index_col=0, parse_dates=True)[CCYS]
    crs_h = pd.read_csv(d / "crosses_1h.csv", index_col=0, parse_dates=True)[list(CROSSES)]
    for sym, (a, b) in CROSSES.items():  # gaps in a cross's own file -> rebuild from the majors
        crs_h[sym] = crs_h[sym].fillna(cur_h[a] / cur_h[b])
    cur = to_candles(cur_h.ffill(limit=3), tf).dropna()
    crs = to_candles(crs_h.ffill(limit=3), tf).reindex(cur.index).ffill()

    # spreads: Vantage hourly spreads -> median per candle; earlier years -> each cross's overall median
    sp_h = pd.read_csv(ROOT / "data/mt5_fx/crosses_1h.csv", index_col=0, parse_dates=True)
    sp_h = sp_h[[f"{s}_spread" for s in CROSSES]]
    sp_h.columns = list(CROSSES)
    sp = to_candles(sp_h, tf, how="median").reindex(cur.index)
    sp = sp.fillna(sp_h.median())

    swaps = pd.read_csv(ROOT / "data/mt5_fx/swaps.csv", index_col=0)
    worst = (-swaps[["long %/night", "short %/night"]].astype(float)).max(axis=1).clip(lower=0) / 100
    per_bar_swap = worst.reindex(list(CROSSES)) * 7 / 5 / TF[tf]["per_day"] * (SWAP == "worst")  # 7 nights paid over 5 trading days
    return cur, crs, sp, per_bar_swap


# ----------------------------------------------------------------------------- run

def run_tf(cur, crs, sp, swap, prm, sig=None):
    r = np.log(cur[CCYS]).diff().to_numpy()[1:]
    idx = cur.index[1:]
    pairs = [(CCYS.index(a), CCYS.index(b)) for a, b in CROSSES.values()]
    if sig is None:
        sig = model_signals(r, pairs, prm)
    s, hl, *_ = sig
    per = {}
    for j, sym in enumerate(CROSSES):
        cost = sp[sym].reindex(idx).to_numpy() / 2 * prm.spread_mult + COMMISSION_PCT / 100
        ret, gross, tr = backtest_one(crs[sym].reindex(idx).to_numpy(), s[:, j], hl[:, j], idx, cost, prm,
                                      carry=swap[sym])
        per[sym] = (ret, gross, tr)
    return per, sig, idx


def perf(ret, per_year):
    ret = pd.Series(ret)
    if len(ret) == 0 or ret.std() == 0:
        return {"Sharpe": np.nan, "%/yr": 0.0, "maxDD %": 0.0}
    eq = (1 + ret).cumprod()
    return {"Sharpe": ret.mean() / ret.std() * np.sqrt(per_year), "%/yr": ret.mean() * per_year * 100,
            "maxDD %": (eq / eq.cummax() - 1).min() * 100}


def combine(per, syms, idx, mask, k=0):
    arr = sum(per[s][k] for s in syms) if syms else np.zeros(len(idx))
    return pd.Series(arr[mask], index=idx[mask])


def trades(per, syms, lo, hi):
    t = [per[s][2].assign(symbol=s) for s in syms if len(per[s][2])]
    t = pd.concat(t, ignore_index=True) if t else pd.DataFrame(columns=["entry", "net", "gross", "cost", "bars"])
    return t[(t["entry"] >= lo) & (t["entry"] < hi)]


def walk_forward(tf):
    cfg = TF[tf]
    cur, crs, sp, swap = load(tf)
    py = cfg["per_year"]
    print(f"\n{'=' * 100}\n{tf}, {len(CROSSES)} crosses, swap: {SWAP}: {len(cur):,} candles, {cur.index[0]:%Y-%m-%d} -> {cur.index[-1]:%Y-%m-%d}   "
          f"train < {SPLIT:%Y-%m-%d} <= test")
    print("swap charged per night (% of position, worst side): "
          + "  ".join(f"{s} {v * 100 * cfg['per_day'] * 5 / 7:.4f}" for s, v in swap.items()))

    cache, rows, keep = {}, [], {}
    for window, entry, exit_, max_hl in product(*cfg["grid"].values()):
        prm = replace(Params(), window=window, step=cfg["step"], entry=entry, exit=exit_, max_hl=max_hl,
                      max_hold=int(3 * max_hl), bars_per_year=py, vol_lookback=window)
        per, sig, idx = run_tf(cur, crs, sp, swap, prm, cache.get(window))
        cache[window] = sig
        train, test = idx < SPLIT, idx >= SPLIT
        chosen = [s for s in CROSSES if per[s][1][train].sum() > 0]
        p_tr, p_te = perf(combine(per, chosen, idx, train), py), perf(combine(per, chosen, idx, test), py)
        key = (window, entry, exit_, max_hl)
        keep[key] = (per, chosen, idx, prm)
        rows.append({"window": window, "entry": entry, "exit": exit_, "max_hl": max_hl, "crosses": len(chosen),
                     "train trades": len(trades(per, chosen, idx[0], SPLIT)),
                     "TRAIN Sharpe": p_tr["Sharpe"], "TRAIN %/yr": p_tr["%/yr"],
                     "test Sharpe": p_te["Sharpe"], "test %/yr": p_te["%/yr"]})

    res = pd.DataFrame(rows).sort_values("TRAIN Sharpe", ascending=False)
    res.to_csv(ROOT / f"data/backtest_fx/walk_forward_{tf}_{len(CROSSES)}x_swap-{SWAP}.csv", index=False)
    print("\nTop 8 by TRAIN Sharpe (test columns shown for transparency, never used to choose):")
    print(res.head(8).round(2).to_string(index=False))

    best = res.iloc[0]
    key = (int(best["window"]), best["entry"], best["exit"], best["max_hl"])
    per, chosen, idx, prm = keep[key]
    days = {"D1": 1, "H4": 1 / 6}[tf]
    print(f"\nCHOSEN on train: window {key[0]} candles, entry {key[1]}, exit {key[2]}, max half-life {key[3]} candles")
    print(f"crosses kept: {chosen}")

    for label, mask, lo, hi in [("TRAIN 2010-2018", idx < SPLIT, idx[0], SPLIT),
                                ("TEST 2019-latest (untouched)", idx >= SPLIT, SPLIT, idx[-1] + pd.Timedelta(days=1))]:
        r, g = combine(per, chosen, idx, mask), combine(per, chosen, idx, mask, k=1)
        t = trades(per, chosen, lo, hi)
        p = perf(r, py)
        years = mask.sum() / py
        print(f"\n{label}: Sharpe {p['Sharpe']:.2f} (before costs {perf(g, py)['Sharpe']:.2f})  "
              f"{p['%/yr']:.2f}%/yr  maxDD {p['maxDD %']:.2f}%  trades {len(t)} ({len(t) / years / 12:.1f}/month)  "
              f"win {(t['net'] > 0).mean() * 100:.0f}%  hold {t['bars'].mean() * days:.1f} days  "
              f"avg gross {t['gross'].mean() * 100:.3f}%  avg cost incl. swap {t['cost'].mean() * 100:.3f}%")
        by_year = r.groupby(r.index.year).sum() * 100
        print("  by year %: " + "  ".join(f"{y}:{v:+.1f}" for y, v in by_year.items()))
        if label.startswith("TEST"):
            print("  by cross %: " + "  ".join(f"{s}:{per[s][0][mask].sum() * 100:+.1f}" for s in chosen))
            print("  prop challenge in TEST (+8%, 5% daily, 10% max, 120 days; end-of-candle equity only):")
            for scale in [1, 2, 4]:
                c = challenge(pd.DataFrame({"ret": r}), scale=scale)
                vc = c["outcome"].value_counts(normalize=True) * 100
                print(f"    risk x{scale}: {len(c)} attempts | " + " | ".join(f"{k} {v:.0f}%" for k, v in vc.items()))

    print(f"\nRobustness across all {len(res)} combinations in TEST: positive {(res['test Sharpe'] > 0).sum()}, "
          f"median test Sharpe {res['test Sharpe'].median():.2f}, "
          f"corr(train, test Sharpe) {res['TRAIN Sharpe'].corr(res['test Sharpe']):.2f}")
    print(f"spreads x2 on the chosen setup, TEST Sharpe: "
          f"{perf(combine(run_tf(cur, crs, sp, swap, replace(prm, spread_mult=2), cache[key[0]])[0], chosen, idx, idx >= SPLIT), py)['Sharpe']:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tf", choices=list(TF), nargs="*", default=list(TF))
    ap.add_argument("--universe", choices=["8", "all"], default="8")
    ap.add_argument("--swap", choices=["worst", "none"], default="worst")
    a = ap.parse_args()
    global CROSSES, SWAP
    CROSSES = fx_pca_strategy.CROSSES_ALL if a.universe == "all" else fx_pca_strategy.CROSSES
    SWAP = a.swap
    pd.set_option("display.width", 220)
    for tf in a.tf:
        walk_forward(tf)


if __name__ == "__main__":
    main()
