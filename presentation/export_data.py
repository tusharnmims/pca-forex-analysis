"""Collect the numbers saved by gold_silver_analysis.py, forex_analysis.py and regime_analysis.py into deck_data.json."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

D = Path(__file__).resolve().parent.parent / "data"
out = {}
r = lambda s, n=2: [round(float(x), n) for x in s]

g = pd.read_csv(D / "gold_silver/pca_share.csv", index_col=0).iloc[:, 0]
out["gs_share"] = {"labels": list(g.index), "values": r(g, 1)}
v = pd.read_csv(D / "gold_silver/variance_ratio.csv", index_col=0).iloc[:, 0]
out["gs_vr"] = {"labels": list(v.index), "values": r(v)}
t = pd.read_csv(D / "gold_silver/trades_by_year.csv", index_col=0)
out["gs_trades"] = [[int(i), int(a), round(b), round(c, 1)] for i, (a, b, c) in t.iterrows()]
h = pd.read_csv(D / "histdata_fx/currencies_1h.csv", index_col=0, parse_dates=True)[["XAU", "XAG"]].dropna()
ratio = (h["XAU"] / h["XAG"]).resample("W").last().dropna()
out["gs_ratio"] = {"labels": [d.strftime("%Y-%m") for d in ratio.index], "values": r(ratio, 1)}

s = pd.read_csv(D / "forex/pca_share.csv", index_col=0).iloc[:, 0]
out["fx_share"] = {"labels": list(s.index), "values": r(s, 1)}
L = pd.read_csv(D / "forex/pca_loadings.csv", index_col=0)
out["fx_load"] = {"labels": list(L.index), **{c: r(L[c]) for c in L.columns}}
vr = pd.read_csv(D / "forex/variance_ratio.csv", index_col=0)["10 days"].sort_values()
out["fx_vr"] = {"labels": list(vr.index), "values": r(vr)}
t = pd.read_csv(D / "forex/trades_by_year.csv", index_col=0)
out["fx_trades"] = [[int(i), int(a["trades"]), round(a["win_pct"]), round(a["return %"], 1), a["period"]] for i, a in t.iterrows()]

c = pd.read_csv(D / "regime/concentration_daily.csv", index_col=0, parse_dates=True)["pc1_share"].dropna()
w = c.resample("W").mean().dropna() * 100
out["conc"] = {"labels": [d.strftime("%Y-%m") for d in w.index], "values": r(w, 1),
               "q1": round(float(c.quantile(1 / 3) * 100), 1), "q2": round(float(c.quantile(2 / 3) * 100), 1)}
rs = pd.read_csv(D / "regime/regime_summary.csv", index_col=0)
out["regime"] = {k: r(rs[k], 1) for k in ["snapped back", "broke", "neither"]} | {"events": [int(x) for x in rs["events"]]}
e = pd.read_csv(D / "regime/stretch_events.csv", parse_dates=["date"])
e["broke"] = e.outcome == "broke"
e["per"] = pd.cut(e.date.dt.year, [2009, 2014, 2018, 2022, 2026], labels=["2010-14", "2015-18", "2019-22", "2023-26"])
p = e.pivot_table(index="per", columns="regime", values="broke", aggfunc="mean", observed=True) * 100
out["break_period"] = [[str(i), round(a["low"], 1), round(a["high"], 1)] for i, a in p.iterrows()]
pp = e.pivot_table(index="pair", columns="regime", values="broke", aggfunc="mean") * 100
out["pairs_low_gt_high"] = int((pp["low"] > pp["high"]).sum())
td = pd.read_csv(D / "regime/tradable_days_by_year.csv", index_col=0)
td = td[td.index > 2010]
out["tradable"] = {"labels": [str(i) for i in td.index], "values": r(td["tradable_pct"], 0)}
bt = pd.read_csv(D / "regime/trades_by_regime.csv")
out["trades_regime"] = bt.round(2).to_dict(orient="records")
json.dump(out, open(Path(__file__).parent / "deck_data.json", "w"), indent=1)
print({k: (len(v) if hasattr(v, "__len__") else v) for k, v in out.items()})

# raw volatility before scaling, and the gauge on shock dates
hh = pd.read_csv(D / "histdata_fx/currencies_1h.csv", index_col=0, parse_dates=True)
dr = np.log(hh.resample("D").last().dropna()).diff().dropna()
vol = (dr.std() * np.sqrt(260) * 100).sort_values()
out["raw_vol"] = {"labels": list(vol.index), "values": r(vol, 1)}
ev = {"2011-08-08": "US downgrade", "2015-01-15": "SNB drops CHF floor", "2016-06-24": "Brexit vote",
      "2020-03-09": "COVID crash", "2022-09-26": "UK gilt crisis", "2025-04-07": "US tariff shock"}
cut = c.expanding(min_periods=260).quantile(1 / 3).shift(1)
rows = []
for d, n in ev.items():
    i = c.index.searchsorted(pd.Timestamp(d, tz="UTC") + pd.Timedelta(days=5))
    rows.append([d[:7], n, round(float(c.iloc[i] * 100), 1), round(float(cut.iloc[i] * 100), 1),
                 "no-trade" if c.iloc[i] <= cut.iloc[i] else "trade"])
out["events"] = rows
json.dump(out, open(Path(__file__).parent / "deck_data.json", "w"), indent=1)
print(out["raw_vol"], out["events"], sep="\n")
