# PCA Forex Analysis

Using Principal Component Analysis (PCA) to understand how currencies move together, test which pair relationships pull back to normal, and build a daily gauge that tells us **when not to trade** them.

Hourly data, 9 currencies + gold + silver, 2010 – 2026.

## Main findings

| | Result |
|---|---|
| **One common force** | The first PCA factor (the US dollar against everything) explains **49%** of all currency movement; three factors explain 72% |
| **Forex crosses pull back** | After removing the common factors, **15 of 23** cross-pair leftovers have a variance ratio below 1 (EURSEK 0.79) |
| **Gold/silver fails** | Its leftover trends instead (variance ratio 1.20 at 10 days, 1.48 at 20); the residual strategy lost money in 7 of 8 years |
| **When not to trade** | When the first factor's share falls into its lowest third, stretched pairs **break ≈ 3× more often** (7.7% vs 2.3%), in 22 of 23 pairs |
| **How often** | A live rule (past data only) marks ≈ **69%** of trading days as safe; 31 – 33% in 2013 – 14, 87 – 100% in 2021 – 26 |

Conclusion: **PCA tells us when not to trust relationships between currency pairs.** It is a risk warning, not a profit rule.

## Repository layout

```
pca/                     analysis notebooks (charts and outputs saved inside)
  01_gold_silver_pca.ipynb       why the PCA pullback fails for gold vs silver
  02_forex_pca.ipynb             correlations, PCA factors, variance ratio of 23 crosses vs gold/silver
  03_when_not_to_trade.ipynb     daily PCA concentration gauge, breakdowns by regime, tradable days
backtesting/             strategy backtests (charts and outputs saved inside)
  01_gold_silver_backtest.ipynb  gold/silver residual strategy, hourly
  02_forex_h1_backtest.ipynb     forex residual strategy, hourly, assumed vs Vantage spreads
  03_forex_h1_walk_forward.ipynb hourly walk-forward (train 2019-22, test 2023+)
  04_forex_daily_walk_forward.ipynb  D1 / H4 walk-forward (train 2010-18, test 2019+), 8 and 23 crosses
  05_swap_sensitivity.ipynb      effect of swap assumptions on the daily setup
src/                     shared Python code used by the notebooks
  fetch_*.py, compare_oanda_histdata.py    data download and validation
  fx_pca_strategy.py, pca_strategy.py      PCA residual model, s-score, backtest engine
  tf_strategy.py, walk_forward.py, ...     walk-forward tests
  gold_silver_analysis.py, forex_analysis.py, regime_analysis.py   analysis behind pca/
presentation/
  PCA_Forex_Analysis.pptx        26-slide deck of the study
  export_data.py, build_deck.js  rebuild the deck from the analysis outputs
chat/
  conversation.md                readable record of the working session with Claude
  claude_session_sanitized.zip   full session transcript (images, account details and private strategy removed)
```

## Method in short

1. **Scale:** prices → hourly log returns → standardised with the mean and std of the past window only (same as `StandardScaler`, without look-ahead). PCA on this = PCA on the correlation matrix.
2. **PCA:** eigenvectors are the shared movement patterns (dollar, currencies vs metals, risk-on vs safe havens); eigenvalues say how much each explains and add up to 11.
3. **Leftover:** remove the first 3 factors. A cross A/B returns exactly r_A − r_B, so its leftover is e_A − e_B.
4. **s-score:** Ornstein–Uhlenbeck fit on the cumulative leftover X (X tomorrow = a + b·X today + noise, 0 < b < 1); s = (X − m) / σ_eq. Beyond ±2.5 a pair is stretched and expected to pull back; beyond ±4 the relationship is treated as broken (Avellaneda & Lee, 2010).
5. **Variance ratio:** VR(k) = Var(k-day moves) / (k · Var(1-day moves)); below 1 = pulls back (Lo & MacKinlay, 1988). Model-free check of step 4.
6. **Gauge:** each day, share of the first factor over the last 480 hours = largest eigenvalue / 11. No-trade when it is at or below the 33rd percentile of all previous days.

## Running it

Market data is **not** included (size and data licences). Download it into `data/`:

```bash
pip install -r requirements.txt
python src/fetch_fx_histdata.py --start 2010-01-01      # HistData hourly: 11 majors/metals + 23 crosses
python src/fetch_data.py --source mt5                   # gold/silver/USD panel from a logged-in MT5 terminal
python src/fetch_fx_mt5.py                              # per-bar spreads from MT5 (2019+)
python src/fetch_swaps_mt5.py                           # current swap rates from MT5
```

The MT5 scripts need the `MetaTrader5` package and a running, logged-in MetaTrader 5 terminal (Windows); they only read data. Set `MT5_PATH` in `src/fetch_data.py` to your terminal. Then open the notebooks in `pca/` and `backtesting/` (they add `../src` to the path) or run the scripts directly, e.g. `python src/regime_analysis.py`.

To rebuild the deck: `python presentation/export_data.py`, then `npm install` and `node build_deck.js` inside `presentation/`.

## Limits

* Trading results on daily candles are **swap-free**; with worst-side swap the 2019 – 26 test is about flat. Hourly and 4-hour versions fail after costs.
* Not every cross pulls back (8 of 23 have a variance ratio above 1).
* Regime thirds in the analysis tables use the full sample; the live rule uses past data only.
* Tested on 23 cross pairs; USD pairs themselves, exotics, indices and crypto were not tested.

*Research and education only, not investment advice.*
