"""
Read current overnight swap rates for the traded crosses from the logged-in MT5 terminal (read-only).

    python fetch_swaps_mt5.py

Writes data/mt5_fx/swaps.csv: swap long/short as % of position value per night.
These are TODAY's rates; historical swaps followed interest-rate differentials and changed over time.
"""
import pandas as pd

from fetch_data import ROOT, mt5_connect
from fetch_fx_mt5 import CROSSES


def main():
    import MetaTrader5 as mt5
    mt5_connect(mt5)
    rows = {}
    try:
        for sym in CROSSES:
            mt5.symbol_select(sym, True)
            i = mt5.symbol_info(sym)
            tick = mt5.symbol_info_tick(sym)
            if i is None or tick is None:
                continue
            px = (tick.bid + tick.ask) / 2
            # swap_mode 1 = points; value in points of price per night
            if i.swap_mode == 1:
                long_pct = i.swap_long * i.point / px * 100
                short_pct = i.swap_short * i.point / px * 100
            else:
                long_pct = short_pct = float("nan")
            rows[sym] = {"swap_mode": i.swap_mode, "swap_long_raw": i.swap_long, "swap_short_raw": i.swap_short,
                         "long %/night": long_pct, "short %/night": short_pct,
                         "triple day": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][i.swap_rollover3days]}
    finally:
        mt5.shutdown()
    df = pd.DataFrame(rows).T
    df.to_csv(ROOT / "data/mt5_fx/swaps.csv")
    pd.set_option("display.width", 200)
    print(df.to_string())


if __name__ == "__main__":
    main()
