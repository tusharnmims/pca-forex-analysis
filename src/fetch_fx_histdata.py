"""
Pull hourly FX majors, tradable crosses and metals from HistData.com (free, bid prices, no spreads).

    python fetch_fx_histdata.py                  # 2019-01-01 -> latest published
    python fetch_fx_histdata.py --start 2021-01-01

Output (data/histdata_fx):
    <SYMBOL>_1h.csv       hourly OHLC per symbol (UTC)
    currencies_1h.csv     value of 1 unit of each currency in USD + XAU, XAG -> the PCA universe
    crosses_1h.csv        hourly closes of the tradable crosses
Downloads are cached in data/cache, so re-running only fetches what is missing.
"""
import argparse
from datetime import date, timedelta

import pandas as pd
import requests

import fetch_data
from fetch_data import ROOT, histdata_symbol

OUT = ROOT / "data" / "histdata_fx"

# currency -> (symbol, True if quoted USDxxx and must be inverted)
MAJORS = {
    "EUR": ("EURUSD", False), "GBP": ("GBPUSD", False), "AUD": ("AUDUSD", False),
    "NZD": ("NZDUSD", False), "CAD": ("USDCAD", True), "CHF": ("USDCHF", True),
    "JPY": ("USDJPY", True), "NOK": ("USDNOK", True), "SEK": ("USDSEK", True),
    "XAU": ("XAUUSD", False), "XAG": ("XAGUSD", False),
}
CROSSES = ["AUDNZD", "EURGBP", "EURCHF", "AUDCAD", "NZDCAD", "CADCHF", "EURNOK", "EURSEK",
           # rest of the 28 pairs between EUR, GBP, AUD, NZD, CAD, CHF, JPY, USD
           "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY", "EURAUD", "EURNZD",
           "EURCAD", "GBPAUD", "GBPNZD", "GBPCAD", "GBPCHF", "AUDCHF", "NZDCHF"]

# loose price ranges to catch bad files
fetch_data.SANE.update({
    "AUDUSD": (0.5, 1.0), "NZDUSD": (0.45, 0.9), "USDNOK": (7, 13),
    "AUDNZD": (0.95, 1.2), "EURGBP": (0.75, 0.95), "EURCHF": (0.85, 1.25), "AUDCAD": (0.8, 1.05),
    "NZDCAD": (0.75, 0.95), "CADCHF": (0.55, 0.85), "EURNOK": (9, 13), "EURSEK": (9.5, 12.5),
    "EURJPY": (90, 200), "GBPJPY": (110, 230), "AUDJPY": (50, 125), "NZDJPY": (40, 110), "CADJPY": (65, 130),
    "CHFJPY": (70, 210), "EURAUD": (1.0, 2.0), "EURNZD": (1.3, 2.2), "EURCAD": (1.15, 1.75),
    "GBPAUD": (1.3, 2.4), "GBPNZD": (1.6, 2.7), "GBPCAD": (1.35, 2.2), "GBPCHF": (1.0, 1.9),
    "AUDCHF": (0.5, 1.05), "NZDCHF": (0.45, 0.95),
})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2019-01-01")
    ap.add_argument("--end", default=str(date.today() - timedelta(days=1)))
    a = ap.parse_args()
    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
    OUT.mkdir(parents=True, exist_ok=True)

    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    data = {}
    for sym in [x for x, _ in MAJORS.values()] + CROSSES:
        df = histdata_symbol(s, sym, start, end)
        df.to_csv(OUT / f"{sym}_1h.csv")
        data[sym] = df
        print(f"  saved {sym}: {len(df):,} bars  {df.index[0]} -> {df.index[-1]}", flush=True)

    cur = pd.DataFrame({c: (1 / data[sym]["close"] if inv else data[sym]["close"])
                        for c, (sym, inv) in MAJORS.items()})
    cur.index.name = "time_utc"
    cur.to_csv(OUT / "currencies_1h.csv")
    crs = pd.DataFrame({sym: data[sym]["close"] for sym in CROSSES})
    crs.index.name = "time_utc"
    crs.to_csv(OUT / "crosses_1h.csv")

    full = cur.dropna()
    print(f"\ncurrencies_1h.csv: {len(cur):,} rows, {len(full):,} with all 11 present "
          f"({full.index[0]} -> {full.index[-1]})")
    print("rows with all present, per year:")
    print(full.groupby(full.index.year).size().to_string())


if __name__ == "__main__":
    main()
