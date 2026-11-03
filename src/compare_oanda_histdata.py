"""
Compare 1-minute XAUUSD bars: OANDA (via TradingView / tvdatafeed) vs HistData.com.

    python compare_oanda_histdata.py

Writes to ./data/compare:
    oanda_xauusd_1m.csv      OANDA bars from TradingView, UTC
    histdata_xauusd_1m.csv   HistData bars for the same window, UTC
    joined_xauusd_1m.csv     both side by side on the minutes they share
"""
import io
import re
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from tvDatafeed import Interval, TvDatafeed

from fetch_data import histdata_to_utc

OUT = Path(__file__).resolve().parent.parent / "data" / "compare"
N_BARS = 5000  # the most TradingView serves without a login


def fetch_oanda():
    tv = TvDatafeed()
    df = None
    for _ in range(5):  # the anonymous feed drops connections now and then
        df = tv.get_hist(symbol="XAUUSD", exchange="OANDA", interval=Interval.in_1_minute, n_bars=N_BARS)
        if df is not None and len(df):
            break
    if df is None or df.empty:
        raise RuntimeError("TradingView returned no data")
    # tvdatafeed stamps bars in this computer's local time -> convert to UTC
    local_tz = datetime.now().astimezone().tzinfo
    df.index = df.index.tz_localize(local_tz).tz_convert("UTC")
    df.index.name = "time_utc"
    return df[["open", "high", "low", "close", "volume"]]


def fetch_histdata_m1(year, month):
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    page = ("https://www.histdata.com/download-free-forex-historical-data/"
            f"?/ascii/1-minute-bar-quotes/xauusd/{year}/{month}")
    html = s.get(page, timeout=60).text
    fields = ["tk", "date", "datemonth", "platform", "timeframe", "fxpair"]
    found = {k: re.search(rf'id="{k}" value="([^"]*)"', html) for k in fields}
    if not all(found.values()):
        return pd.DataFrame()
    r = s.post("https://www.histdata.com/get.php", headers={"Referer": page}, timeout=600,
               data={k: m.group(1) for k, m in found.items()})
    try:
        z = zipfile.ZipFile(io.BytesIO(r.content))
    except zipfile.BadZipFile:
        return pd.DataFrame()
    name = next(n for n in z.namelist() if n.endswith(".csv"))
    df = pd.read_csv(io.BytesIO(z.read(name)), sep=";", header=None,
                     names=["t", "open", "high", "low", "close", "volume"])
    df.index = histdata_to_utc(pd.to_datetime(df["t"], format="%Y%m%d %H%M%S"))
    df = df[df.index.notna()]
    df.index.name = "time_utc"
    return df[["open", "high", "low", "close"]]


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    oa = fetch_oanda()
    oa.to_csv(OUT / "oanda_xauusd_1m.csv")
    print(f"OANDA (TradingView): {len(oa):,} bars  {oa.index[0]} -> {oa.index[-1]}")

    months = sorted({(t.year, t.month) for t in oa.index})
    hd = pd.concat([fetch_histdata_m1(y, m) for y, m in months])
    if hd.empty:
        print(f"HistData has not published {months} yet -> nothing to compare")
        return
    print(f"HistData month file(s) {months}: {len(hd):,} bars  {hd.index[0]} -> {hd.index[-1]}")
    hd = hd[(hd.index >= oa.index[0]) & (hd.index <= oa.index[-1])]
    hd.to_csv(OUT / "histdata_xauusd_1m.csv")

    j = oa.join(hd, lsuffix="_oanda", rsuffix="_hist", how="inner")
    j.to_csv(OUT / "joined_xauusd_1m.csv")
    if j.empty:
        print("No overlapping minutes: HistData's latest bar is older than the oldest OANDA bar available.")
        return

    lo, hi = j.index[0], j.index[-1]
    n_oa = len(oa[(oa.index >= lo) & (oa.index <= hi)])
    n_hd = len(hd[(hd.index >= lo) & (hd.index <= hi)])
    print(f"\nOverlap window: {lo} -> {hi}")
    print(f"  minutes in OANDA: {n_oa:,}   in HistData: {n_hd:,}   in both: {len(j):,}")

    print("\nPrice difference, OANDA minus HistData ($):")
    rows = {}
    for c in ["open", "high", "low", "close"]:
        d = j[f"{c}_oanda"] - j[f"{c}_hist"]
        rows[c] = {"mean": d.mean(), "median": d.median(), "mean abs": d.abs().mean(),
                   "95% abs": d.abs().quantile(0.95), "max abs": d.abs().max(),
                   "identical %": (d.abs() < 0.0005).mean() * 100, "within $0.10 %": (d.abs() <= 0.10).mean() * 100}
    print(pd.DataFrame(rows).T.round(3).to_string())

    d = j["close_oanda"] - j["close_hist"]
    print(f"\nclose diff as % of price: mean {(d / j['close_hist']).mean() * 100:+.4f}%")
    r = np.log(j[["close_oanda", "close_hist"]]).diff().dropna()
    print(f"1-minute return correlation: {r.corr().iloc[0, 1]:.4f}")
    r5 = np.log(j[["close_oanda", "close_hist"]].resample("5min").last().dropna()).diff().dropna()
    print(f"5-minute return correlation: {r5.corr().iloc[0, 1]:.4f}")
    rng = pd.DataFrame({"oanda": j["high_oanda"] - j["low_oanda"], "hist": j["high_hist"] - j["low_hist"]})
    print(f"average bar range (high-low): OANDA ${rng['oanda'].mean():.3f}   HistData ${rng['hist'].mean():.3f}")

    # time alignment sanity check: correlation should peak at zero shift
    base = np.log(j["close_hist"]).diff()
    shifts = {k: np.log(j["close_oanda"]).diff().shift(k).corr(base) for k in (-2, -1, 0, 1, 2)}
    print("alignment check (corr by minute shift):", "  ".join(f"{k:+d}:{v:.2f}" for k, v in shifts.items()))


if __name__ == "__main__":
    main()
