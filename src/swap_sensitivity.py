"""D1 chosen setup (from tf_strategy walk-forward): how much do swap assumptions matter?"""
from dataclasses import replace

import pandas as pd

from fx_pca_strategy import ROOT, Params
from tf_strategy import SPLIT, TF, combine, load, perf, run_tf, trades

CHOSEN = dict(window=120, entry=2.5, exit=0.5, max_hl=10)
CROSSES_KEPT = ["AUDNZD", "EURGBP", "AUDCAD", "NZDCAD", "EURNOK", "EURSEK"]

cur, crs, sp, worst = load("D1")
swaps = pd.read_csv(ROOT / "data/mt5_fx/swaps.csv", index_col=0)
avg = (-(swaps["long %/night"].astype(float) + swaps["short %/night"].astype(float)) / 2).clip(lower=0) / 100 * 7 / 5
cfg = TF["D1"]
prm = replace(Params(), step=cfg["step"], max_hold=30, bars_per_year=cfg["per_year"],
              vol_lookback=CHOSEN["window"], **CHOSEN)

sig = None
print("D1 chosen setup, TEST 2019-latest:")
for label, sw in [("worst-side swap (used in walk-forward)", worst), ("average of long/short swap", avg),
                  ("swap-free account", worst * 0)]:
    per, sig, idx = run_tf(cur, crs, sp, sw, prm, sig)
    test = idx >= SPLIT
    p = perf(combine(per, CROSSES_KEPT, idx, test), cfg["per_year"])
    t = trades(per, CROSSES_KEPT, SPLIT, idx[-1] + pd.Timedelta(days=1))
    print(f"  {label:40s} Sharpe {p['Sharpe']:5.2f}  {p['%/yr']:5.2f}%/yr  maxDD {p['maxDD %']:6.2f}%  "
          f"avg cost/trade {t['cost'].mean() * 100:.3f}%  (avg gross {t['gross'].mean() * 100:.3f}%)")
