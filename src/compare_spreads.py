"""Re-run the FX PCA backtest with Vantage's recorded per-bar spreads vs the assumed spreads (same parameters)."""
from dataclasses import replace

import numpy as np
import pandas as pd

from fx_pca_strategy import CCYS, CROSSES, ROOT, Params, mt5_spreads, run
from pca_strategy import BARS_PER_YEAR, challenge, stats

d = ROOT / "data/histdata_fx"
cur = pd.read_csv(d / "currencies_1h.csv", index_col=0, parse_dates=True)[CCYS].dropna()
crs = pd.read_csv(d / "crosses_1h.csv", index_col=0, parse_dates=True)
pd.set_option("display.width", 200)

base = Params()
eq_a, tr_a, per_a, sig, idx = run(cur, crs, base)
real = replace(base, real_spreads=True)
eq_r, tr_r, per_r, *_ = run(cur, crs, real, sig)

sp = mt5_spreads(idx)
# spread actually paid: at the bars where trades opened/closed
paid = {}
for sym in CROSSES:
    t = tr_r[tr_r["symbol"] == sym]
    at = pd.Series(sp[sym], index=idx)
    paid[sym] = pd.concat([at.reindex(t["entry"]), at.reindex(t["exit"])]).median() * 100
print("spread paid at trade times vs typical (median, % of price):")
print(pd.DataFrame({"typical": {s: np.median(sp[s]) * 100 for s in CROSSES}, "at trades": paid}).round(4).T.to_string())

print("\n                         assumed spreads    Vantage spreads")
sa, sr = stats(eq_a, tr_a), stats(eq_r, tr_r)
for k in ["Sharpe", "Sharpe before costs", "CAGR %", "max DD %", "trades", "win %", "avg gross/trade %", "avg cost/trade %"]:
    print(f"  {k:22s} {sa[k]:15.3f}    {sr[k]:15.3f}")

print("\nper cross with Vantage spreads:")
rows = {}
for sym, (ret, gross, t) in per_r.items():
    rr = pd.Series(ret)
    rows[sym] = {"trades": len(t), "win %": (t["net"] > 0).mean() * 100, "net total %": rr.sum() * 100,
                 "gross total %": np.sum(gross) * 100, "cost total %": t["cost"].sum() * 100,
                 "Sharpe": rr.mean() / rr.std() * np.sqrt(BARS_PER_YEAR)}
print(pd.DataFrame(rows).T.round(2).to_string())

print("\nper year (Vantage spreads):")
yr = eq_r.groupby(eq_r.index.year).agg(net=("ret", lambda x: x.sum() * 100), gross=("gross", lambda x: x.sum() * 100))
print(yr.round(2).to_string())

print("\nprop challenge with Vantage spreads (+8%, 5% daily, 10% max, 120 days):")
for scale in [1, 2, 4]:
    c = challenge(eq_r, scale=scale)
    vc = c["outcome"].value_counts(normalize=True) * 100
    print(f"  risk x{scale}: " + " | ".join(f"{k} {v:.0f}%" for k, v in vc.items()))
eq_r.to_csv(ROOT / "data/backtest_fx/equity_real_spreads.csv")
tr_r.to_csv(ROOT / "data/backtest_fx/trades_real_spreads.csv", index=False)
