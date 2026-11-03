"""
PCA residual mean reversion on FX "twin" crosses (AUDNZD, EURGBP, EURCHF, ...).

Model, re-fit every STEP bars on the previous WINDOW bars only (no look-ahead):
    1. Universe: 9 currencies + gold + silver, each as "value in USD". Hourly log returns, standardized.
    2. PCA. Keep the first K factors (USD, risk-on/off, metals...). Residual = what they don't explain.
    3. A cross A/B returns exactly r_A - r_B, so its residual is e_A - e_B.
    4. X = cumulative residual of the cross. Ornstein-Uhlenbeck fit -> s-score.
    5. s < -ENTRY: buy the cross (A cheap vs B). s > +ENTRY: sell it. Exit near 0, stop at |s| > STOP.

Usage
    python fx_pca_strategy.py              # diagnostics + backtest + prop challenge simulation
Input:  data/histdata_fx/currencies_1h.csv, crosses_1h.csv   (python fetch_fx_histdata.py)
Output: data/backtest_fx/trades.csv, equity.csv
"""
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

from pca_strategy import BARS_PER_YEAR, challenge, stats

ROOT = Path(__file__).resolve().parent.parent  # repository root; data lives in <repo>/data
CCYS = ["EUR", "GBP", "AUD", "NZD", "CAD", "CHF", "JPY", "NOK", "SEK", "XAU", "XAG"]
CROSSES = {  # symbol: (base, quote)
    "AUDNZD": ("AUD", "NZD"), "EURGBP": ("EUR", "GBP"), "EURCHF": ("EUR", "CHF"),
    "AUDCAD": ("AUD", "CAD"), "NZDCAD": ("NZD", "CAD"), "CADCHF": ("CAD", "CHF"),
    "EURNOK": ("EUR", "NOK"), "EURSEK": ("EUR", "SEK"),
}
# all 23 crosses downloaded (fetch_fx_histdata.py): the 8 above + the rest of the 28 pairs without USD
CROSSES_ALL = {**CROSSES, **{s: (s[:3], s[3:]) for s in [
    "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY", "EURAUD", "EURNZD",
    "EURCAD", "GBPAUD", "GBPNZD", "GBPCAD", "GBPCHF", "AUDCHF", "NZDCHF"]}}
# HistData has no spreads: assumed typical prop-firm raw spreads, as % of price (conservative)
SPREAD_PCT = {"AUDNZD": 0.018, "EURGBP": 0.012, "EURCHF": 0.016, "AUDCAD": 0.016,
              "NZDCAD": 0.024, "CADCHF": 0.025, "EURNOK": 0.035, "EURSEK": 0.036}
COMMISSION_PCT = 0.003  # per side, ~ $6 per 100k round turn


@dataclass(frozen=True)
class Params:
    window: int = 480
    step: int = 24
    k: int = 3                 # PCA factors removed
    entry: float = 2.0
    exit: float = 0.5
    stop: float = 4.0
    max_hl: float = 48.0
    max_hold: int = 96
    target_vol: float = 0.05   # annual vol per open position
    max_lev: float = 30.0
    spread_mult: float = 1.0
    real_spreads: bool = False  # True: per-bar spreads recorded by Vantage MT5 (data/mt5_fx)
    bars_per_year: float = BARS_PER_YEAR  # 5900 for H1; set for other timeframes
    vol_lookback: int = 480     # bars used to size positions


_MT5_SPREADS = None


def mt5_spreads(idx):
    """Per-bar spread as a fraction of price for each cross, from fetch_fx_mt5.py, aligned to idx.
    Bars missing in the MT5 history get that symbol's median spread."""
    global _MT5_SPREADS
    if _MT5_SPREADS is None:
        _MT5_SPREADS = pd.read_csv(ROOT / "data/mt5_fx/crosses_1h.csv", index_col=0, parse_dates=True)
    out = {}
    for sym in CROSSES:
        s = _MT5_SPREADS[f"{sym}_spread"]
        out[sym] = s.reindex(idx).fillna(s.median()).to_numpy()
    return out


# ----------------------------------------------------------------------------- model

def model_signals(r, pairs, prm):
    """Out-of-sample residuals and s-scores for each cross. r: (T, N) log returns of CCYS."""
    T = len(r)
    P = len(pairs)
    s = np.full((T, P), np.nan)
    hl = np.full((T, P), np.nan)
    resid = np.full((T, P), np.nan)
    explained = np.full(T, np.nan)
    for t0 in range(prm.window, T, prm.step):
        w = r[t0 - prm.window:t0]
        mu, sd = w.mean(0), w.std(0, ddof=1)
        z = (w - mu) / sd
        vals, vecs = np.linalg.eigh(np.corrcoef(z.T))
        o = vals.argsort()[::-1]
        V = vecs[:, o[:prm.k]]
        t1 = min(t0 + prm.step, T)
        explained[t0:t1] = vals[o[0]] / vals.sum()
        e_win = (z - z @ V @ V.T) * sd                         # residual returns, window
        zn = (r[t0:t1] - mu) / sd
        e_new = (zn - zn @ V @ V.T) * sd                       # residual returns, next bars (frozen model)
        for j, (a, b) in enumerate(pairs):
            p_win = e_win[:, a] - e_win[:, b]
            p_new = e_new[:, a] - e_new[:, b]
            resid[t0:t1, j] = p_new
            x = np.cumsum(p_win)
            bb, aa = np.polyfit(x[:-1], x[1:], 1)
            if not 0 < bb < 1:
                continue
            zeta = x[1:] - (aa + bb * x[:-1])
            m = aa / (1 - bb)
            sig = np.sqrt(zeta.var() / (1 - bb * bb))
            s[t0:t1, j] = (x[-1] + np.cumsum(p_new) - m) / sig
            hl[t0:t1, j] = np.log(2) / -np.log(bb)
    return s, hl, resid, explained


# ----------------------------------------------------------------------------- backtest

def backtest_one(px, s, hl, idx, cost_side, prm, carry=0.0):
    """One cross. px: closes, s/hl: signals at each bar close, cost_side: cost per side (scalar or per bar),
    carry: holding cost per bar while a position is open (swap), as a fraction of notional."""
    cost_side = np.broadcast_to(np.asarray(cost_side, dtype=float), (len(px),))
    carry = np.broadcast_to(np.asarray(carry, dtype=float), (len(px),))
    simple = np.r_[0.0, px[1:] / px[:-1] - 1]
    lr = np.r_[0.0, np.diff(np.log(px))]
    bar_target = prm.target_vol / np.sqrt(prm.bars_per_year)
    n = len(px)
    ret, gross = np.zeros(n), np.zeros(n)
    pos, lev, held, blocked, cur, trades = 0, 0.0, 0, 0, None, []
    for t in range(n):
        if pos != 0:
            g = pos * lev * simple[t]
            ret[t] += g - lev * carry[t]
            gross[t] += g
            cur["gross"] += g
            cur["cost"] += lev * carry[t]
            held += 1
        st = s[t]
        want, reason = pos, None
        if pos != 0:
            if np.isnan(st):
                want, reason = 0, "model invalid"
            elif (pos > 0 and st >= -prm.exit) or (pos < 0 and st <= prm.exit):
                want, reason = 0, "target"
            elif abs(st) >= prm.stop:
                want, reason = 0, "stop"
            elif held >= prm.max_hold:
                want, reason = 0, "time"
        if blocked and (np.isnan(st) or abs(st) < prm.entry):
            blocked = 0
        if want == 0 and pos == 0 and not blocked and not np.isnan(st) \
                and hl[t] <= prm.max_hl and prm.entry <= abs(st) < prm.stop:
            want = -1 if st > 0 else 1
        if want != pos:
            if pos != 0:
                ret[t] -= lev * cost_side[t]
                cur.update(cost=cur["cost"] + lev * cost_side[t], exit=idx[t], bars=held, reason=reason)
                trades.append(cur)
                blocked = 1 if reason in ("stop", "time") else 0
            if want != 0:
                vol = lr[max(0, t - prm.vol_lookback):t + 1].std()
                lev = min(bar_target / vol, prm.max_lev) if vol > 0 else 0.0
                ret[t] -= lev * cost_side[t]
                cur = {"entry": idx[t], "dir": want, "s_entry": st, "half_life": hl[t], "lev": lev,
                       "gross": 0.0, "cost": lev * cost_side[t]}
                held = 0
            pos = want
    tr = pd.DataFrame(trades)
    if len(tr):
        tr["net"] = tr["gross"] - tr["cost"]
    return ret, gross, tr


def run(cur, crs, prm, sig=None):
    r = np.log(cur[CCYS]).diff().to_numpy()[1:]
    idx = cur.index[1:]
    pairs = [(CCYS.index(a), CCYS.index(b)) for a, b in CROSSES.values()]
    if sig is None:
        sig = model_signals(r, pairs, prm)
    s, hl, resid, explained = sig
    px_all = crs.reindex(idx).ffill()
    real = mt5_spreads(idx) if prm.real_spreads else None
    per, trades = {}, []
    for j, sym in enumerate(CROSSES):
        if real is not None:
            cost = real[sym] / 2 * prm.spread_mult + COMMISSION_PCT / 100
        else:
            cost = (SPREAD_PCT[sym] / 2 * prm.spread_mult + COMMISSION_PCT) / 100
        ret, gross, tr = backtest_one(px_all[sym].to_numpy(), s[:, j], hl[:, j], idx, cost, prm)
        per[sym] = (ret, gross, tr)
        if len(tr):
            tr.insert(0, "symbol", sym)
            trades.append(tr)
    eq = pd.DataFrame({"ret": sum(v[0] for v in per.values()),
                       "gross": sum(v[1] for v in per.values())}, index=idx)
    tr = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()
    return eq, tr, per, sig, idx


def variance_ratio(x, k):
    x = pd.Series(x).dropna()
    agg = x.rolling(k).sum().iloc[k - 1::k]
    return agg.var() / (k * x.var())


def main():
    d = ROOT / "data/histdata_fx"
    cur = pd.read_csv(d / "currencies_1h.csv", index_col=0, parse_dates=True)[CCYS].dropna()
    crs = pd.read_csv(d / "crosses_1h.csv", index_col=0, parse_dates=True)
    out = ROOT / "data/backtest_fx"
    out.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)
    base = Params()
    print(f"Data: {cur.index[0]:%Y-%m-%d} -> {cur.index[-1]:%Y-%m-%d}, {len(cur):,} hourly bars, {len(CCYS)} assets")

    # --- factor structure
    r = np.log(cur).diff().dropna()
    z = (r - r.mean()) / r.std()
    vals, vecs = np.linalg.eigh(np.corrcoef(z.T))
    o = vals.argsort()[::-1]
    print("\nPCA loadings, full sample (first 4 factors):")
    L = pd.DataFrame(vecs[:, o[:4]], index=CCYS, columns=["PC1", "PC2", "PC3", "PC4"])
    L = L * np.sign(L.loc["EUR"])
    print(L.round(2).T.to_string())
    print("variance explained:", (vals[o] / vals.sum())[:6].round(3), "cumulative 3:", round(vals[o[:3]].sum() / vals.sum(), 3))

    eq, tr, per, sig, idx = run(cur, crs, base)
    s, hl, resid, explained = sig

    # --- does each cross's residual mean-revert?
    print("\nVariance ratio of each cross's PCA residual (out-of-sample), <1 = mean-reverting, >1 = trending")
    rows = {}
    raw = np.log(crs.reindex(idx).ffill()).diff()
    for j, sym in enumerate(CROSSES):
        rows[sym] = {f"resid {k}h": variance_ratio(resid[:, j], k) for k in (4, 24, 72, 120, 240)}
        rows[sym].update({f"raw {k}h": variance_ratio(raw[sym], k) for k in (24, 120)})
    print(pd.DataFrame(rows).T.round(2).to_string())

    eq.to_csv(out / "equity.csv")
    tr.to_csv(out / "trades.csv", index=False)
    print(f"\n=== Portfolio backtest, all {len(CROSSES)} crosses, {base} ===")
    print(pd.Series(stats(eq, tr)).drop("label").astype(float).round(3).to_string())

    print("\nper cross:")
    rows = {}
    for sym, (ret, gross, t) in per.items():
        rr = pd.Series(ret)
        rows[sym] = {"trades": len(t), "win %": (t["net"] > 0).mean() * 100 if len(t) else np.nan,
                     "net total %": rr.sum() * 100, "gross total %": np.sum(gross) * 100,
                     "Sharpe": rr.mean() / rr.std() * np.sqrt(BARS_PER_YEAR) if rr.std() > 0 else np.nan}
    print(pd.DataFrame(rows).T.round(2).to_string())

    print("\nper year (portfolio):")
    yr = eq.groupby(eq.index.year).agg(net=("ret", lambda x: x.sum() * 100), gross=("gross", lambda x: x.sum() * 100))
    yr["trades"] = tr.groupby(tr["entry"].dt.year).size()
    print(yr.round(2).to_string())

    print("\nexit reasons:")
    print(tr.groupby("reason").agg(n=("net", "size"), win_pct=("net", lambda x: (x > 0).mean() * 100),
                                   avg_net_pct=("net", lambda x: x.mean() * 100)).round(3).to_string())

    print("\nsensitivity (portfolio Sharpe after costs / trades):")
    for label, p in [("no costs", replace(base, spread_mult=0)), ("spreads x2", replace(base, spread_mult=2)),
                     ("k=2 factors", replace(base, k=2)), ("k=4 factors", replace(base, k=4)),
                     ("entry 1.5", replace(base, entry=1.5)), ("entry 2.5", replace(base, entry=2.5)),
                     ("window 240", replace(base, window=240)), ("window 960", replace(base, window=960)),
                     ("max half-life 24h", replace(base, max_hl=24))]:
        same_model = p.k == base.k and p.window == base.window and p.step == base.step
        e2, t2, *_ = run(cur, crs, p, sig if same_model else None)
        s2 = stats(e2, t2)
        print(f"  {label:20s} Sharpe {s2['Sharpe']:6.2f}  (before costs {s2['Sharpe before costs']:5.2f})  "
              f"CAGR {s2['CAGR %']:6.2f}%  maxDD {s2['max DD %']:6.2f}%  trades {s2['trades']}")

    print("\n=== Prop challenge (+8% target, 5% daily, 10% max loss, 120 days) ===")
    for scale in [1, 2, 4]:
        c = challenge(eq, scale=scale)
        vc = c["outcome"].value_counts(normalize=True) * 100
        passed = c[c["outcome"] == "pass"]["days"]
        print(f"  risk x{scale}: {len(c)} attempts | " + " | ".join(f"{k} {v:.0f}%" for k, v in vc.items())
              + (f" | median days to pass {passed.median():.0f}" if len(passed) else ""))


if __name__ == "__main__":
    main()
