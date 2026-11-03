"""
PCA gold/silver residual mean-reversion strategy + backtest + prop-firm challenge simulator.

Model (re-fit every STEP bars on the previous WINDOW bars only -> no look-ahead)
    1. Hourly log returns of gold, silver, USD index; standardize.
    2. PCA. PC1 = all together (USD/metals), PC2 = USD on its own, PC3 = silver vs gold.
    3. Remove PC1 + PC2. What is left is the PC3 portfolio: long silver / short gold
       (USD loading ~0, so it is traded with XAUUSD and XAGUSD only).
    4. X = cumulative return of that portfolio. Fit Ornstein-Uhlenbeck (AR(1)) -> s-score.
    5. s < -ENTRY: buy the spread (silver cheap vs gold). s > +ENTRY: sell it.
       Exit near equilibrium, stop if |s| > STOP, time-stop after MAX_HOLD bars.

Usage
    python pca_strategy.py              # backtest + challenge simulation + sensitivity grid
    python pca_strategy.py --no-grid

Input:  data/mt5/panel_1h.csv  (from: python fetch_data.py --source mt5)
Output: data/backtest/trades.csv, equity.csv
"""
import argparse
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # repository root; data lives in <repo>/data
ASSETS = ["xau", "xag", "usdx"]
LOT_OZ = {"xau": 100, "xag": 5000}  # standard MT5 lot sizes
BARS_PER_YEAR = 5900  # hourly bars actually present per year in the data


@dataclass(frozen=True)
class Params:
    window: int = 480          # bars used to fit PCA + OU (~4 weeks)
    step: int = 24             # re-fit every N bars
    entry: float = 2.0         # |s| to open
    exit: float = 0.5          # |s| to close at equilibrium
    stop: float = 4.0          # |s| stop-loss (model broken)
    max_hl: float = 48.0       # only trade if OU half-life <= this many bars
    max_hold: int = 96         # time stop, bars
    target_vol: float = 0.10   # annual volatility target while in a trade
    max_lev: float = 10.0      # cap on gross notional / equity
    spread_mult: float = 1.5   # demo spreads are optimistic; prop spreads are wider
    commission: float = 6.0    # $ per lot round turn (typical prop firm)
    flat_weekend: bool = False  # close before the Friday close


# ----------------------------------------------------------------------------- model

def fit(r_win):
    """PCA + OU on one window of returns. Returns dict or None if not mean-reverting."""
    mu, sd = r_win.mean(0), r_win.std(0, ddof=1)
    z = (r_win - mu) / sd
    vals, vecs = np.linalg.eigh(np.corrcoef(z.T))
    v3 = vecs[:, vals.argsort()[0]]           # smallest-variance component = PC3
    v3 = v3 * np.sign(v3[1])                  # orient: long silver
    w = v3[:2] / sd[:2]                       # dollar weights, gold & silver legs only
    w = w / np.abs(w).sum()                   # $1 gross
    spread = r_win[:, :2] @ w
    x = np.cumsum(spread)
    b, a = np.polyfit(x[:-1], x[1:], 1)
    if not 0 < b < 1:
        return None
    zeta = x[1:] - (a + b * x[:-1])
    return {
        "w": w, "x_last": x[-1], "m": a / (1 - b),
        "sigma_eq": np.sqrt(zeta.var() / (1 - b * b)),
        "hl": np.log(2) / -np.log(b),
        "lev": None if spread.std() == 0 else spread.std(),
        "usdx_loading": v3[2],
    }


def signals(r, prm):
    """s-score, half-life, weights and spread vol for every bar (using only past data)."""
    n = len(r)
    s = np.full(n, np.nan)
    hl = np.full(n, np.nan)
    W = np.full((n, 2), np.nan)
    vol = np.full(n, np.nan)
    for t0 in range(prm.window, n, prm.step):
        f = fit(r[t0 - prm.window:t0])
        if f is None:
            continue
        t1 = min(t0 + prm.step, n)
        # extend the cumulative spread with new bars, model frozen until next re-fit
        x = f["x_last"] + np.cumsum(r[t0:t1, :2] @ f["w"])
        s[t0:t1] = (x - f["m"]) / f["sigma_eq"]
        hl[t0:t1] = f["hl"]
        W[t0:t1] = f["w"]
        vol[t0:t1] = f["lev"]
    return s, hl, W, vol


# ----------------------------------------------------------------------------- backtest

def backtest(panel, prm):
    px = panel[["xau", "xag"]].to_numpy()
    r = np.log(panel[ASSETS]).diff().to_numpy()[1:]
    idx = panel.index[1:]
    simple = px[1:] / px[:-1] - 1
    half_spread = 0.5 * prm.spread_mult * (panel[["xau_spread", "xag_spread"]].to_numpy()[1:] / px[1:])
    comm = np.column_stack([(prm.commission / 2) / (LOT_OZ[a] * px[1:, i]) for i, a in enumerate(["xau", "xag"])])
    s, hl, W, vol = signals(r, prm)

    hourly_target = prm.target_vol / np.sqrt(BARS_PER_YEAR)
    weekday, hour = idx.weekday, idx.hour
    n = len(r)
    ret = np.zeros(n)          # strategy return per bar (net of costs)
    gross = np.zeros(n)
    pos, w_e, lev_e, held, blocked = 0, None, 0.0, 0, 0
    trades, cur = [], None

    for t in range(n):
        # 1) P&L of the position held over bar t
        if pos != 0:
            g = pos * lev_e * (w_e @ simple[t])
            ret[t] += g
            gross[t] += g
            cur["gross"] += g
            held += 1

        # 2) decide at the close of bar t
        st = s[t]
        want = pos
        reason = None
        friday_close = prm.flat_weekend and weekday[t] == 4 and hour[t] >= 19
        if pos != 0:
            if np.isnan(st):
                want, reason = 0, "model invalid"
            elif (pos > 0 and st >= -prm.exit) or (pos < 0 and st <= prm.exit):
                want, reason = 0, "target"
            elif abs(st) >= prm.stop:
                want, reason = 0, "stop"
            elif held >= prm.max_hold:
                want, reason = 0, "time"
            elif friday_close:
                want, reason = 0, "weekend"
        if blocked and (np.isnan(st) or abs(st) < prm.entry):
            blocked = 0
        if want == 0 and pos == 0 and not blocked and not friday_close and not np.isnan(st) \
                and hl[t] <= prm.max_hl and prm.entry <= abs(st) < prm.stop:
            want = -1 if st > 0 else 1   # s high -> silver rich vs gold -> sell spread

        # 3) trade + costs
        if want != pos:
            if pos != 0:  # close
                c = lev_e * np.abs(w_e) @ (half_spread[t] + comm[t])
                ret[t] -= c
                cur.update(cost=cur["cost"] + c, exit=idx[t], bars=held, reason=reason, s_exit=st)
                trades.append(cur)
                if reason in ("stop", "time"):
                    blocked = 1
            if want != 0:  # open
                w_e = W[t]
                lev_e = min(hourly_target / vol[t], prm.max_lev) if vol[t] > 0 else 0.0
                c = lev_e * np.abs(w_e) @ (half_spread[t] + comm[t])
                ret[t] -= c
                cur = {"entry": idx[t], "dir": "long spread" if want > 0 else "short spread",
                       "s_entry": st, "half_life": hl[t], "lev": lev_e,
                       "w_gold": w_e[0], "w_silver": w_e[1], "gross": 0.0, "cost": c}
                held = 0
            pos = want

    eq = pd.DataFrame({"ret": ret, "gross": gross, "s": s, "in_trade": 0}, index=idx)
    tr = pd.DataFrame(trades)
    if len(tr):
        tr["net"] = tr["gross"] - tr["cost"]
    return eq, tr


def stats(eq, tr, label=""):
    r = eq["ret"]
    equity = (1 + r).cumprod()
    years = len(r) / BARS_PER_YEAR
    dd = equity / equity.cummax() - 1
    sharpe = r.mean() / r.std() * np.sqrt(BARS_PER_YEAR) if r.std() > 0 else np.nan
    gross_sharpe = eq["gross"].mean() / eq["gross"].std() * np.sqrt(BARS_PER_YEAR)
    out = {
        "label": label,
        "CAGR %": (equity.iloc[-1] ** (1 / years) - 1) * 100,
        "Sharpe": sharpe,
        "Sharpe before costs": gross_sharpe,
        "max DD %": dd.min() * 100,
        "trades": len(tr),
        "trades/month": len(tr) / (years * 12),
        "win %": (tr["net"] > 0).mean() * 100 if len(tr) else np.nan,
        "avg hold (h)": tr["bars"].mean() if len(tr) else np.nan,
        "avg gross/trade %": tr["gross"].mean() * 100 if len(tr) else np.nan,
        "avg cost/trade %": tr["cost"].mean() * 100 if len(tr) else np.nan,
    }
    return out


# ----------------------------------------------------------------------------- prop challenge

def challenge(eq, scale=1.0, target=0.08, daily_loss=0.05, max_loss=0.10, max_days=120, every_days=5):
    """Replay the strategy from many start dates under prop-firm rules.
    scale multiplies risk (2.0 = twice the position size). Daily loss uses equity at the 22:00 UTC rollover."""
    r = eq["ret"].to_numpy() * scale
    day = (eq.index + pd.Timedelta(hours=2)).normalize()  # trading day rolls at 22:00 UTC
    day_codes, day_start = pd.factorize(day)[0], None
    starts = np.flatnonzero(np.r_[True, np.diff(day_codes) != 0])[::every_days]
    results = []
    for st in starts:
        e, peak_day_eq, d0, days, outcome, t = 1.0, 1.0, day_codes[st], 0, "unfinished", st
        day_start = 1.0
        while t < len(r):
            if day_codes[t] != d0:
                d0 = day_codes[t]
                day_start = e
                days += 1
                if days >= max_days:
                    break
            e *= 1 + r[t]
            if e <= day_start * (1 - daily_loss):
                outcome = "fail: daily loss"
                break
            if e <= 1 - max_loss:
                outcome = "fail: max loss"
                break
            if e >= 1 + target:
                outcome = "pass"
                break
            t += 1
        if t >= len(r) and outcome == "unfinished" and days < max_days:
            continue  # ran out of data, not a fair attempt
        results.append({"start": eq.index[st], "outcome": outcome, "days": days})
    return pd.DataFrame(results)


# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-grid", action="store_true")
    a = ap.parse_args()

    panel = pd.read_csv(ROOT / "data/mt5/panel_1h.csv", index_col=0, parse_dates=True)
    out = ROOT / "data/backtest"
    out.mkdir(parents=True, exist_ok=True)

    base = Params()
    eq, tr = backtest(panel, base)
    eq.to_csv(out / "equity.csv")
    tr.to_csv(out / "trades.csv", index=False)

    pd.set_option("display.width", 200)
    print(f"Data: {panel.index[0]:%Y-%m-%d} -> {panel.index[-1]:%Y-%m-%d}, {len(panel):,} hourly bars")
    print(f"Params: {base}\n")
    print("=== Backtest (base parameters, costs = demo spread x1.5 + $6/lot) ===")
    print(pd.Series(stats(eq, tr)).drop("label").astype(float).round(3).to_string())

    print("\nper year:")
    yr = eq.groupby(eq.index.year).agg(ret=("ret", lambda x: ((1 + x).prod() - 1) * 100),
                                         gross=("gross", lambda x: x.sum() * 100))
    yr["trades"] = tr.groupby(tr["entry"].dt.year).size() if len(tr) else 0
    yr.columns = ["net return %", "gross (no costs) %", "trades"]
    print(yr.round(2).to_string())

    if len(tr):
        print("\nexit reasons:")
        g = tr.groupby("reason").agg(n=("net", "size"), win_pct=("net", lambda x: (x > 0).mean() * 100),
                                     avg_net_pct=("net", lambda x: x.mean() * 100))
        print(g.round(3).to_string())

    print("\ncost sensitivity (Sharpe / CAGR %):")
    for label, p in [("no costs", replace(base, spread_mult=0, commission=0)),
                     ("demo spread, no commission", replace(base, spread_mult=1, commission=0)),
                     ("base: spread x1.5 + $6", base),
                     ("harsh: spread x3 + $7", replace(base, spread_mult=3, commission=7))]:
        e2, t2 = backtest(panel, p)
        s2 = stats(e2, t2)
        print(f"  {label:30s} Sharpe {s2['Sharpe']:6.2f}   CAGR {s2['CAGR %']:6.2f}%   maxDD {s2['max DD %']:6.2f}%")

    print("\n=== Prop challenge simulation (target +8%, daily loss 5%, max loss 10%, 120 trading days) ===")
    for scale in [1, 2, 3, 4]:
        c = challenge(eq, scale=scale)
        vc = c["outcome"].value_counts(normalize=True) * 100
        passed = c[c["outcome"] == "pass"]["days"]
        print(f"  risk x{scale} (vol target {base.target_vol * scale:.0%}): {len(c)} attempts | "
              + " | ".join(f"{k} {v:.0f}%" for k, v in vc.items())
              + (f" | median days to pass {passed.median():.0f}" if len(passed) else ""))

    if not a.no_grid:
        print("\n=== Sensitivity grid: Sharpe after costs (window x entry) ===")
        print("    (for robustness only: picking the best cell would be curve-fitting)")
        rows = {}
        for win in [240, 480, 960]:
            rows[win] = {}
            for ent in [1.5, 2.0, 2.5]:
                e2, t2 = backtest(panel, replace(base, window=win, entry=ent))
                s2 = stats(e2, t2)
                rows[win][ent] = f"{s2['Sharpe']:.2f} ({s2['trades']})"
        print(pd.DataFrame(rows).T.rename_axis("window \\ entry").to_string())


if __name__ == "__main__":
    main()
