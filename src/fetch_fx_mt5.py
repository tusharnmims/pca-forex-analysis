"""
Pull hourly FX majors, tradable crosses and metals from the logged-in MT5 terminal (read-only).

    python fetch_fx_mt5.py                  # 2019-01-01 -> yesterday
    python fetch_fx_mt5.py --start 2021-01-01

Output (data/mt5_fx):
    <SYMBOL>_1h.csv           OHLC, tick volume, spread, per symbol
    currencies_1h.csv         value of 1 unit of each currency in USD (EUR, GBP, AUD, NZD, CAD,
                              CHF, JPY, NOK, SEK) + XAU, XAG  -> the PCA universe
    crosses_1h.csv            close + spread (as fraction of price) of each tradable symbol
"""
import argparse
import sys
from datetime import date, timedelta

import pandas as pd

from fetch_data import ROOT, mt5_connect, mt5_symbol

OUT = ROOT / "data" / "mt5_fx"

# currency -> (MT5 symbol, True if quoted as USDxxx and must be inverted)
MAJORS = {
    "EUR": ("EURUSD", False), "GBP": ("GBPUSD", False), "AUD": ("AUDUSD", False),
    "NZD": ("NZDUSD", False), "CAD": ("USDCAD", True), "CHF": ("USDCHF", True),
    "JPY": ("USDJPY", True), "NOK": ("USDNOK", True), "SEK": ("USDSEK", True),
    "XAU": ("XAUUSD", False), "XAG": ("XAGUSD", False),
}
CROSSES = ["AUDNZD", "EURGBP", "EURCHF", "AUDCAD", "NZDCAD", "CADCHF", "EURNOK", "EURSEK",
           "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY", "EURAUD", "EURNZD",
           "EURCAD", "GBPAUD", "GBPNZD", "GBPCAD", "GBPCHF", "AUDCHF", "NZDCHF"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2019-01-01")
    ap.add_argument("--end", default=str(date.today() - timedelta(days=1)))
    a = ap.parse_args()
    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
    OUT.mkdir(parents=True, exist_ok=True)

    import MetaTrader5 as mt5
    try:
        mt5_connect(mt5)
    except RuntimeError as e:
        sys.exit(str(e))
    try:
        print(f"connected to {mt5.account_info().server}", flush=True)
        data = {}
        for sym in [s for s, _ in MAJORS.values()] + CROSSES:
            df = mt5_symbol(mt5, sym, start, end)
            if df.empty:
                print(f"  {sym}: not available at this broker, skipped", flush=True)
                continue
            df.to_csv(OUT / f"{sym}_1h.csv")
            data[sym] = df
    finally:
        mt5.shutdown()

    cur = {}
    for ccy, (sym, invert) in MAJORS.items():
        if sym in data:
            cur[ccy] = 1 / data[sym]["close"] if invert else data[sym]["close"]
    cur = pd.DataFrame(cur)
    cur.index.name = "time_utc"
    cur.to_csv(OUT / "currencies_1h.csv")

    trad = {}
    for sym, df in data.items():
        trad[f"{sym}"] = df["close"]
        trad[f"{sym}_spread"] = df["spread"] / df["close"]
    trad = pd.DataFrame(trad)
    trad.index.name = "time_utc"
    trad.to_csv(OUT / "crosses_1h.csv")

    full = cur.dropna()
    print(f"\ncurrencies_1h.csv: {len(cur):,} rows, {len(full):,} with every currency present "
          f"({full.index[0]} -> {full.index[-1]})")
    print("\nmedian spread (% of price) and bars:")
    rows = {s: {"spread %": (d["spread"] / d["close"]).median() * 100, "bars": len(d),
                "first": d.index[0].date(), "last": d.index[-1].date()} for s, d in data.items()}
    print(pd.DataFrame(rows).T.to_string())


if __name__ == "__main__":
    main()
