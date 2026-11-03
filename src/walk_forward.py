"""
Walk-forward test of the FX PCA strategy with Vantage's real per-bar spreads.

    python walk_forward.py

1. TRAIN 2019-2022: try every parameter combination in GRID, keep only crosses that made money
   before costs in TRAIN, pick the combination with the best after-cost Sharpe in TRAIN.
2. TEST 2023 -> latest: run that single choice once, untouched. This is the honest result.
Signals are rolling and use only past data, so the TEST years never influence the choice.
"""
from dataclasses import replace
from itertools import product

import numpy as np
import pandas as pd

from fx_pca_strategy import CCYS, CROSSES, ROOT, Params, run
from pca_strategy import BARS_PER_YEAR, challenge

SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
GRID = {
    "window": [480, 960],
    "entry": [1.5, 2.0, 2.5],
    "exit": [0.0, 0.5],
    "max_hl": [24.0, 48.0, 96.0],
}


def perf(ret):
    ret = pd.Series(ret)
    if ret.std() == 0 or len(ret) == 0:
        return {"Sharpe": np.nan, "return %/yr": 0.0, "max DD %": 0.0}
    eq = (1 + ret).cumprod()
    return {"Sharpe": ret.mean() / ret.std() * np.sqrt(BARS_PER_YEAR),
            "return %/yr": ret.mean() * BARS_PER_YEAR * 100,
            "max DD %": (eq / eq.cummax() - 1).min() * 100}


def portfolio(per, symbols, idx, mask):
    ret = sum(per[s][0] for s in symbols) if symbols else np.zeros(len(idx))
    gross = sum(per[s][1] for s in symbols) if symbols else np.zeros(len(idx))
    return pd.Series(ret[mask], index=idx[mask]), pd.Series(gross[mask], index=idx[mask])


def trades_in(per, symbols, lo, hi):
    t = [per[s][2].assign(symbol=s) for s in symbols if len(per[s][2])]
    t = pd.concat(t, ignore_index=True) if t else pd.DataFrame(columns=["entry", "net", "gross", "cost"])
    return t[(t["entry"] >= lo) & (t["entry"] < hi)]


def main():
    d = ROOT / "data/histdata_fx"
    cur = pd.read_csv(d / "currencies_1h.csv", index_col=0, parse_dates=True)[CCYS].dropna()
    crs = pd.read_csv(d / "crosses_1h.csv", index_col=0, parse_dates=True)
    pd.set_option("display.width", 220)

    sig_cache, rows, keep = {}, [], {}
    for window, entry, exit_, max_hl in product(*GRID.values()):
        prm = replace(Params(), window=window, entry=entry, exit=exit_, max_hl=max_hl, real_spreads=True)
        eq, tr, per, sig, idx = run(cur, crs, prm, sig_cache.get(window))
        sig_cache[window] = sig
        train, test = idx < SPLIT, idx >= SPLIT
        # cross selection uses TRAIN only: keep crosses with positive gross P&L before costs
        chosen = [s for s in CROSSES if per[s][1][train].sum() > 0]
        r_tr, _ = portfolio(per, chosen, idx, train)
        r_te, _ = portfolio(per, chosen, idx, test)
        key = (window, entry, exit_, max_hl)
        keep[key] = (per, chosen, idx)
        p_tr, p_te = perf(r_tr), perf(r_te)
        rows.append({"window": window, "entry": entry, "exit": exit_, "max_hl": max_hl,
                     "crosses": len(chosen),
                     "train trades": len(trades_in(per, chosen, idx[0], SPLIT)),
                     "TRAIN Sharpe": p_tr["Sharpe"], "TRAIN %/yr": p_tr["return %/yr"],
                     "test Sharpe": p_te["Sharpe"], "test %/yr": p_te["return %/yr"]})
        print(f"  {key}: train Sharpe {p_tr['Sharpe']:5.2f} | test Sharpe {p_te['Sharpe']:5.2f}", flush=True)

    res = pd.DataFrame(rows).sort_values("TRAIN Sharpe", ascending=False)
    res.to_csv(ROOT / "data/backtest_fx/walk_forward_grid.csv", index=False)
    print("\nTop 10 by TRAIN Sharpe (the test columns are shown for transparency, not used to choose):")
    print(res.head(10).round(2).to_string(index=False))

    best = res.iloc[0]
    key = (int(best["window"]), best["entry"], best["exit"], best["max_hl"])
    per, chosen, idx = keep[key]
    print(f"\n=== CHOSEN on 2019-2022: window {key[0]}, entry {key[1]}, exit {key[2]}, max half-life {key[3]}h ===")
    print(f"crosses kept (positive before costs in train): {chosen}")

    for label, mask, lo, hi in [("TRAIN 2019-2022", idx < SPLIT, idx[0], SPLIT),
                                ("TEST 2023-latest (untouched)", idx >= SPLIT, SPLIT, idx[-1] + pd.Timedelta(hours=1))]:
        r, g = portfolio(per, chosen, idx, mask)
        t = trades_in(per, chosen, lo, hi)
        p = perf(r)
        print(f"\n{label}:  Sharpe {p['Sharpe']:.2f} (before costs {perf(g)['Sharpe']:.2f})  "
              f"return {p['return %/yr']:.2f}%/yr  maxDD {p['max DD %']:.2f}%  trades {len(t)}  "
              f"win {(t['net'] > 0).mean() * 100:.0f}%  avg gross {t['gross'].mean() * 100:.4f}%  avg cost {t['cost'].mean() * 100:.4f}%")
        by_year = r.groupby(r.index.year).sum() * 100
        print("  by year %: " + "  ".join(f"{y}: {v:+.2f}" for y, v in by_year.items()))
        if mask[-1]:
            per_cross = {s: per[s][0][mask].sum() * 100 for s in chosen}
            print("  by cross %: " + "  ".join(f"{s}: {v:+.2f}" for s, v in per_cross.items()))
            eq = pd.DataFrame({"ret": r})
            print("  prop challenge in TEST period (+8%, 5% daily, 10% max, 120 days):")
            for scale in [1, 2, 4]:
                c = challenge(eq, scale=scale)
                vc = c["outcome"].value_counts(normalize=True) * 100
                print(f"    risk x{scale}: {len(c)} attempts | " + " | ".join(f"{k} {v:.0f}%" for k, v in vc.items()))

    print("\nRobustness: how all 36 combinations did in TEST")
    print(f"  positive test Sharpe: {(res['test Sharpe'] > 0).sum()} of {len(res)}   "
          f"median test Sharpe {res['test Sharpe'].median():.2f}   "
          f"corr(train Sharpe, test Sharpe) {res['TRAIN Sharpe'].corr(res['test Sharpe']):.2f}")


if __name__ == "__main__":
    main()
