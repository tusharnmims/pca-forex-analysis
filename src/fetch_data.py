"""
Download hourly Gold (XAU/USD), Silver (XAG/USD) and a USD index for PCA research.

Sources
-------
histdata (default)   HistData.com free 1-minute spot bars (bid), 2000s -> ~last week,
                     resampled to 1h UTC. Synthetic DXY from 6 FX pairs (ICE formula).
mt5                  Your broker's own history via the MetaTrader 5 terminal (must be open and
                     logged in). Spot bars with the recorded spread and the broker's USD index.
                     Read-only: no orders are sent.
dukascopy            Free bid/ask hourly candles, spot metals + spreads. Blocks fast clients,
                     so requests are paced; cached per month, re-run to resume.
yahoo                Gold futures (GC=F), Silver futures (SI=F), DXY (DX-Y.NYB).
                     No bid/ask, and Yahoo only serves the last ~730 days of hourly data.

Downloads are cached in ./data/cache, so re-running only fetches what is missing.

Usage
-----
    python fetch_data.py                          # histdata, 2019-01-01 -> today
    python fetch_data.py --start 2021-01-01
    python fetch_data.py --source dukascopy       # adds real bid/ask spreads
    python fetch_data.py --source yahoo           # quick, last 2 years only

Output (in ./data/<source>)
---------------------------
    XAUUSD_1h.csv   OHLC, volume (+ bid/ask and spread for dukascopy)
    XAGUSD_1h.csv   same
    USDX_1h.csv     dollar index (close)
    panel_1h.csv    aligned closes: xau, xag, usdx (+ spreads) -> input for PCA
"""
import io
import re
import zipfile
import argparse
import lzma
import struct
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent  # repository root; data lives in <repo>/data
DATA = ROOT / "data"          # repointed to data/<source> in main()
CACHE = ROOT / "data" / "cache"

BASE_URL = "https://datafeed.dukascopy.com/datafeed"

# Price scaling used by Dukascopy (raw integer / factor = price)
POINT = {
    "XAUUSD": 1_000, "XAGUSD": 1_000,
    "EURUSD": 100_000, "GBPUSD": 100_000, "USDCAD": 100_000,
    "USDCHF": 100_000, "USDSEK": 100_000, "USDJPY": 1_000,
}
# Rough sanity ranges to catch a wrong scaling factor
SANE = {
    "XAUUSD": (800, 10_000), "XAGUSD": (8, 200),
    "EURUSD": (0.8, 1.6), "GBPUSD": (0.9, 2.0), "USDCAD": (1.0, 1.8),
    "USDCHF": (0.6, 1.3), "USDSEK": (6, 14), "USDJPY": (80, 200),
}
METALS = ["XAUUSD", "XAGUSD"]
# ICE US Dollar Index: 50.14348112 * EURUSD^-0.576 * USDJPY^0.136 * GBPUSD^-0.119
#                      * USDCAD^0.091 * USDSEK^0.042 * USDCHF^0.036
DXY_WEIGHTS = {
    "EURUSD": -0.576, "USDJPY": 0.136, "GBPUSD": -0.119,
    "USDCAD": 0.091, "USDSEK": 0.042, "USDCHF": 0.036,
}
DXY_CONST = 50.14348112

REQUEST_PAUSE = 1.0  # seconds between requests; Dukascopy blocks aggressive clients


# ----------------------------------------------------------------------------- dukascopy

class Fetcher:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Mozilla/5.0"
        self.last = 0.0

    def get(self, url, max_tries=8):
        """Return bytes, b'' for a missing file (404), or raise after max_tries."""
        for attempt in range(max_tries):
            wait = self.last + REQUEST_PAUSE - time.time()
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            try:
                r = self.s.get(url, timeout=30)
                if r.status_code == 200:
                    return r.content
                if r.status_code == 404:
                    return b""
                reason = f"HTTP {r.status_code}"
            except requests.RequestException as e:
                reason = type(e).__name__
            backoff = min(5 * 2 ** attempt, 120)
            print(f"    {reason}, retry in {backoff}s ({attempt + 1}/{max_tries})", flush=True)
            time.sleep(backoff)
        raise RuntimeError(f"giving up on {url}")


def decode_candles(raw, t0, point):
    """bi5 candle file -> DataFrame. Record = offset_sec, open, close, low, high (int32), volume (float32)."""
    if not raw:
        return pd.DataFrame()
    buf = lzma.decompress(raw)
    arr = np.frombuffer(buf, dtype=np.dtype([
        ("t", ">i4"), ("o", ">i4"), ("c", ">i4"), ("l", ">i4"), ("h", ">i4"), ("v", ">f4")]))
    df = pd.DataFrame({
        "open": arr["o"] / point, "high": arr["h"] / point,
        "low": arr["l"] / point, "close": arr["c"] / point,
        "volume": arr["v"].astype(float),
    }, index=pd.to_datetime(t0, utc=True) + pd.to_timedelta(arr["t"].astype(np.int64), unit="s"))
    return df[df["volume"] > 0]  # drop flat filler bars (weekends, holidays, daily breaks)


def synthetic_usdx(closes):
    """ICE dollar index from a dict of FX close series."""
    fx = pd.DataFrame(closes).dropna()
    usdx = DXY_CONST * np.exp(sum(w * np.log(fx[s]) for s, w in DXY_WEIGHTS.items()))
    usdx = usdx.rename("close").to_frame()
    usdx.index.name = "time_utc"
    return usdx


def month_range(start, end):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def fetch_month(f, sym, side, y, m, today):
    """Hourly candles for one month, cached as CSV."""
    cache = CACHE / sym / f"{y}-{m:02d}_{side}.csv"
    is_recent = (today.year, today.month) <= (y, m + 1) or (today.year == y + 1 and m == 12 and today.month == 1)
    if cache.exists() and not is_recent:
        return pd.read_csv(cache, index_col=0, parse_dates=True)

    t0 = datetime(y, m, 1, tzinfo=timezone.utc)
    raw = f.get(f"{BASE_URL}/{sym}/{y}/{m - 1:02d}/{side}_candles_hour_1.bi5")  # month is 0-based
    df = decode_candles(raw, t0, POINT[sym])

    if df.empty and is_recent:
        # Monthly file isn't published until the month is complete -> build from daily 1-minute files
        parts = []
        d = date(y, m, 1)
        while d.month == m and d < today:
            if d.weekday() != 5:  # markets closed all Saturday
                raw = f.get(f"{BASE_URL}/{sym}/{y}/{m - 1:02d}/{d.day:02d}/{side}_candles_min_1.bi5")
                parts.append(decode_candles(raw, datetime(y, m, d.day, tzinfo=timezone.utc), POINT[sym]))
            d += timedelta(days=1)
        parts = [p for p in parts if not p.empty]
        if parts:
            mins = pd.concat(parts)
            df = mins.resample("1h").agg({"open": "first", "high": "max", "low": "min",
                                          "close": "last", "volume": "sum"}).dropna()

    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache)
    return df


def fetch_symbol(f, sym, side, start, end):
    today = date.today()
    frames = []
    months = list(month_range(start, end))
    for i, (y, m) in enumerate(months, 1):
        print(f"  {sym} {side} {y}-{m:02d} ({i}/{len(months)})", flush=True)
        frames.append(fetch_month(f, sym, side, y, m, today))
    df = pd.concat([x for x in frames if not x.empty]).sort_index()
    df = df[~df.index.duplicated()]
    df = df[(df.index >= pd.Timestamp(start, tz="UTC")) & (df.index < pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1))]
    lo, hi = SANE[sym]
    med = df["close"].median()
    if not lo <= med <= hi:
        print(f"  WARNING: {sym} median price {med:.4f} outside {lo}-{hi}; check POINT scaling", flush=True)
    return df


def run_dukascopy(start, end):
    f = Fetcher()
    out = {}

    for sym in METALS:
        bid = fetch_symbol(f, sym, "BID", start, end)
        ask = fetch_symbol(f, sym, "ASK", start, end)
        df = bid.add_prefix("bid_").join(ask.drop(columns="volume").add_prefix("ask_"), how="inner")
        for c in ["open", "high", "low", "close"]:
            df[c] = (df[f"bid_{c}"] + df[f"ask_{c}"]) / 2
        df["spread"] = df["ask_close"] - df["bid_close"]
        df = df.rename(columns={"bid_volume": "volume"})
        df.index.name = "time_utc"
        df.to_csv(DATA / f"{sym}_1h.csv")
        out[sym] = df
        print(f"  saved {sym}_1h.csv: {len(df):,} bars", flush=True)

    # Synthetic dollar index from bid closes of the 6 ICE components
    closes = {}
    for sym in DXY_WEIGHTS:
        closes[sym] = fetch_symbol(f, sym, "BID", start, end)["close"]
    usdx = synthetic_usdx(closes)
    usdx.to_csv(DATA / "USDX_1h.csv")
    print(f"  saved USDX_1h.csv: {len(usdx):,} bars", flush=True)

    panel = pd.DataFrame({
        "xau": out["XAUUSD"]["close"], "xag": out["XAGUSD"]["close"], "usdx": usdx["close"],
        "xau_spread": out["XAUUSD"]["spread"], "xag_spread": out["XAGUSD"]["spread"],
    }).dropna()
    return panel


# ----------------------------------------------------------------------------- histdata

HISTDATA_PAGE = "https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes"
HISTDATA_GET = "https://www.histdata.com/get.php"


def ny_to_utc(ts):
    """Naive New York local timestamps (EST/EDT) -> UTC."""
    local = pd.DatetimeIndex(ts).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    return local.tz_convert("UTC")


def histdata_to_utc(ts):
    """HistData timestamps are UTC-5 in winter and UTC-4 in summer, but the switch happens on the
    EUROPEAN daylight-saving dates (= Central European time minus 6h), not the US ones.
    Verified against Yahoo UTC bars and MT5: using New York rules is 1h off for the
    1-3 weeks each spring/autumn when US and EU clocks disagree."""
    cet = (pd.DatetimeIndex(ts) + pd.Timedelta(hours=6)).tz_localize(
        "Europe/Berlin", ambiguous="NaT", nonexistent="NaT")
    return cet.tz_convert("UTC")


def histdata_period(s, pair, year, month=None):
    """1-minute bid bars for a full year (or one month) -> hourly UTC DataFrame, cached."""
    tag = f"{year}" if month is None else f"{year}-{month:02d}"
    cache = CACHE / "histdata_v3" / f"{pair}_{tag}.csv"
    today = date.today()
    is_current = month is not None and (year, month) == (today.year, today.month)
    if cache.exists() and not is_current:
        return pd.read_csv(cache, index_col=0, parse_dates=True)

    page = f"{HISTDATA_PAGE}/{pair.lower()}/{year}" + (f"/{month}" if month else "")
    time.sleep(REQUEST_PAUSE)
    html = s.get(page, timeout=60).text
    tk = re.search(r'id="tk" value="([0-9a-f]+)"', html)
    if not tk:
        print(f"    no data page for {pair} {tag}", flush=True)
        return pd.DataFrame()
    datemonth = re.search(r'id="datemonth" value="(\d+)"', html).group(1)
    r = s.post(HISTDATA_GET, headers={"Referer": page}, timeout=300, data={
        "tk": tk.group(1), "date": str(year), "datemonth": datemonth,
        "platform": "ASCII", "timeframe": "M1", "fxpair": pair})
    try:
        z = zipfile.ZipFile(io.BytesIO(r.content))
    except zipfile.BadZipFile:
        print(f"    no file for {pair} {tag}", flush=True)
        return pd.DataFrame()
    name = next(n for n in z.namelist() if n.endswith(".csv"))
    m1 = pd.read_csv(io.BytesIO(z.read(name)), sep=";", header=None,
                     names=["t", "open", "high", "low", "close", "volume"])
    m1.index = histdata_to_utc(pd.to_datetime(m1["t"], format="%Y%m%d %H%M%S"))
    m1 = m1[m1.index.notna()]  # drops the one ambiguous DST-change hour per year
    h1 = m1.resample("1h").agg({"open": "first", "high": "max", "low": "min",
                                "close": "last", "volume": "count"}).dropna()
    h1 = h1.rename(columns={"volume": "minutes"})  # HistData has no volume; keep bar count instead
    h1.index.name = "time_utc"
    cache.parent.mkdir(parents=True, exist_ok=True)
    h1.to_csv(cache)
    return h1


def histdata_symbol(s, pair, start, end):
    today = date.today()
    frames = []
    for year in range(start.year, end.year + 1):
        if year < today.year:
            print(f"  {pair} {year}", flush=True)
            frames.append(histdata_period(s, pair, year))
        else:  # current year is only published month by month
            for month in range(1, today.month + 1):
                print(f"  {pair} {year}-{month:02d}", flush=True)
                frames.append(histdata_period(s, pair, year, month))
    df = pd.concat([x for x in frames if not x.empty]).sort_index()
    df = df[~df.index.duplicated()]
    df = df[(df.index >= pd.Timestamp(start, tz="UTC")) & (df.index < pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1))]
    lo, hi = SANE[pair]
    med = df["close"].median()
    if not lo <= med <= hi:
        print(f"  WARNING: {pair} median price {med:.4f} outside {lo}-{hi}", flush=True)
    return df


def run_histdata(start, end):
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    out = {}
    for sym in METALS:
        df = histdata_symbol(s, sym, start, end)
        df.to_csv(DATA / f"{sym}_1h.csv")
        out[sym] = df
        print(f"  saved {sym}_1h.csv: {len(df):,} bars", flush=True)

    closes = {sym: histdata_symbol(s, sym, start, end)["close"] for sym in DXY_WEIGHTS}
    usdx = synthetic_usdx(closes)
    usdx.to_csv(DATA / "USDX_1h.csv")
    print(f"  saved USDX_1h.csv: {len(usdx):,} bars", flush=True)

    return pd.DataFrame({
        "xau": out["XAUUSD"]["close"], "xag": out["XAGUSD"]["close"], "usdx": usdx["close"],
    }).dropna()


# ----------------------------------------------------------------------------- mt5

MT5_USDX = "USDX.r"  # broker's own dollar index symbol (Vantage); synthetic index is used if absent
MT5_PATH = Path(r"G:\MT5\terminal64.exe")  # portable install: program, login and history all on G:


def mt5_connect(mt5):
    """Attach to the logged-in terminal (portable G: install if present). Never sends credentials."""
    kw = {"path": str(MT5_PATH), "portable": True} if MT5_PATH.exists() else {}
    if not mt5.initialize(timeout=60000, **kw):
        raise RuntimeError(f"MT5 not available: {mt5.last_error()} (open the terminal and log in first)")


def mt5_symbol(mt5, sym, start, end):
    """Hourly bars from the logged-in MT5 terminal (read-only), index converted to UTC."""
    info = mt5.symbol_info(sym)
    if info is None:
        return pd.DataFrame()
    mt5.symbol_select(sym, True)
    # +2 days so the request covers "now" in server time, which runs ahead of UTC
    r = mt5.copy_rates_range(sym, mt5.TIMEFRAME_H1,
                             datetime(start.year, start.month, start.day, tzinfo=timezone.utc),
                             datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=2))
    if r is None or len(r) == 0:
        print(f"  {sym}: no data {mt5.last_error()}", flush=True)
        return pd.DataFrame()
    df = pd.DataFrame(r)
    # MT5 bar times are broker server time. Vantage (like most FX brokers) runs New York + 7h,
    # so the trading day starts at 00:00 server time = 17:00 New York, summer and winter.
    server = pd.to_datetime(df["time"], unit="s")
    df.index = ny_to_utc(server - pd.Timedelta(hours=7))
    df = df[df.index.notna()]
    df.index.name = "time_utc"
    df["spread_points"] = df["spread"]
    df["spread"] = df["spread_points"] * info.point  # spread recorded for the bar, in price units
    df = df[["open", "high", "low", "close", "tick_volume", "spread", "spread_points"]]
    df = df[(df.index >= pd.Timestamp(start, tz="UTC")) & (df.index < pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1))]
    print(f"  {sym}: {len(df):,} bars  {df.index[0]} -> {df.index[-1]}", flush=True)
    return df


def run_mt5(start, end):
    import MetaTrader5 as mt5

    mt5_connect(mt5)
    try:
        acc = mt5.account_info()
        print(f"  connected to {acc.server}", flush=True)
        out = {}
        for sym in METALS:
            df = mt5_symbol(mt5, sym, start, end)
            df.to_csv(DATA / f"{sym}_1h.csv")
            out[sym] = df

        usdx = mt5_symbol(mt5, MT5_USDX, start, end)
        if usdx.empty or usdx.index[0] > pd.Timestamp(start, tz="UTC") + pd.Timedelta(days=30):
            print("  broker dollar index missing or too short -> building synthetic index", flush=True)
            closes = {sym: mt5_symbol(mt5, sym, start, end)["close"] for sym in DXY_WEIGHTS}
            usdx = synthetic_usdx(closes)
        usdx.to_csv(DATA / "USDX_1h.csv")
    finally:
        mt5.shutdown()

    return pd.DataFrame({
        "xau": out["XAUUSD"]["close"], "xag": out["XAGUSD"]["close"], "usdx": usdx["close"],
        "xau_spread": out["XAUUSD"]["spread"], "xag_spread": out["XAGUSD"]["spread"],
    }).dropna()


# ----------------------------------------------------------------------------- yahoo

def run_yahoo(start, end):
    import yfinance as yf

    earliest = date.today() - timedelta(days=725)
    if start < earliest:
        print(f"  Yahoo keeps only ~730 days of hourly data; starting at {earliest}", flush=True)
        start = earliest
    tickers = {"xau": "GC=F", "xag": "SI=F", "usdx": "DX-Y.NYB"}
    series = {}
    for name, tk in tickers.items():
        df = yf.download(tk, start=start, end=end + timedelta(days=1), interval="1h",
                         auto_adjust=False, progress=False, multi_level_index=False)
        if df.empty:
            raise RuntimeError(f"no data returned for {tk}")
        df.index = df.index.tz_convert("UTC")
        df.index.name = "time_utc"
        df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
        fname = {"xau": "XAUUSD", "xag": "XAGUSD", "usdx": "USDX"}[name]
        df.to_csv(DATA / f"{fname}_1h.csv")
        print(f"  saved {fname}_1h.csv ({tk}): {len(df):,} bars", flush=True)
        series[name] = df["close"]
    return pd.DataFrame(series).dropna()


# ----------------------------------------------------------------------------- summary

def summarize(panel):
    print("\n=== panel_1h.csv ===")
    print(f"bars: {len(panel):,}   from {panel.index[0]}   to {panel.index[-1]}")
    print(panel[["xau", "xag", "usdx"]].describe().loc[["min", "50%", "max"]].round(3).to_string())
    if "xau_spread" in panel:
        print(f"\nmedian spread: gold ${panel['xau_spread'].median():.3f}   silver ${panel['xag_spread'].median():.4f}")

    r = np.log(panel[["xau", "xag", "usdx"]]).diff().dropna()
    gap = r.index.to_series().diff() > pd.Timedelta(hours=1)
    r = r[~gap]  # skip returns spanning weekends / breaks
    print("\ncorrelation of hourly returns:")
    print(r.corr().round(2).to_string())
    print("\nannualized volatility (hourly returns, ~6000 trading hours/yr):")
    print((r.std() * np.sqrt(6000) * 100).round(1).astype(str).add("%").to_string())

    daily = np.log(panel[["xau", "xag", "usdx"]].resample("1D").last().dropna()).diff().dropna()
    roll = daily["xau"].rolling(60).corr(daily["usdx"])
    print(f"\n60-day rolling corr gold vs USD index: min {roll.min():.2f}  median {roll.median():.2f}  max {roll.max():.2f}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", choices=["histdata", "mt5", "dukascopy", "yahoo"], default="histdata")
    p.add_argument("--start", default="2019-01-01")
    p.add_argument("--end", default=str(date.today() - timedelta(days=1)))
    a = p.parse_args()
    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
    global DATA
    DATA = ROOT / "data" / a.source
    DATA.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {a.source}: {start} -> {end}", flush=True)
    runner = {"histdata": run_histdata, "mt5": run_mt5, "dukascopy": run_dukascopy, "yahoo": run_yahoo}[a.source]
    panel = runner(start, end)
    panel.index.name = "time_utc"
    panel.to_csv(DATA / "panel_1h.csv")
    summarize(panel)


if __name__ == "__main__":
    sys.exit(main())
