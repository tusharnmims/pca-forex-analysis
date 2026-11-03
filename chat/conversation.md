# Project conversation with Claude

Readable copy of the working session behind this repository. Images, account numbers and email removed; tool calls and their raw output omitted.

### You

I want to use PCA and built a trading strategy tell me what can I build?

### Claude

PCA works well in trading because asset returns are driven by a few hidden common factors. Once you pull those factors out, what's left over (the residual) is often the part you can trade. Here are the main strategies you can build, starting with the most practical.

## 1. Statistical arbitrage on PCA residuals (Avellaneda–Lee style)
**Best starting point.**
- Take a universe of about 50–500 stocks (for example, S&P 500 members) and run PCA on rolling 252-day returns.
- Keep the top k components (roughly 10–15, or however many explain about 50% of variance). These act as "market / sector / style" factors.
- Regress each stock's returns on those factors. The residual is that stock's idiosyncratic move.
- Model the cumulative residual as mean-reverting (Ornstein–Uhlenbeck) and compute an s-score:
  - s < −1.25 → buy the stock and hedge its factor exposure
  - s > +1.25 → short it and hedge
  - Exit when |s| < 0.5
- The result is market-neutral and factor-neutral. It's a classic, well-documented approach with real papers to benchmark against.

## 2. Yield curve trading (rates / futures)
- PCA on daily changes in Treasury yields (2y, 5y, 10y, 30y) almost always gives three components: **level, slope, curvature**.
- You can trade:
  - **Butterfly mean reversion:** when the PC3 (curvature) score is extreme, trade a 2s5s10s fly weighted so it's neutral to level and slope.
  - **Hedging:** isolate your slope view by neutralizing PC1.
- The results are very clean and easy to interpret. A good fit if you trade futures or ETFs (SHY/IEF/TLT).

## 3. Eigenportfolio / factor momentum
- Treat each principal component as a tradable portfolio (its eigenvector weights).
- Apply time-series momentum or trend rules to the PC returns themselves, for example going long any PC whose 3-month return is positive.
- Lower-order PCs often behave like hidden sector or style rotations.

## 4. Regime detection / risk filter
- Track the **variance explained by PC1** over a rolling window.
- When PC1 explains a lot (for example >40%), correlations are spiking and the market is in "risk-off / everything moves together" mode.
- Use this as a filter: cut leverage, pause mean-reversion strategies, or switch to trend-following. It works well as an add-on to any other strategy.

## 5. Pairs / basket trading generalized
- Instead of hand-picking pairs, apply PCA within a sector (for example the 20 largest banks). The smallest-eigenvalue components are the most stationary, mean-reverting combinations.
- Trade those baskets with z-score entries. This works much like cointegration but scales to many assets.

## 6. Crypto / FX versions
- **Crypto:** PC1 is essentially "BTC beta". Residual stat arb on altcoins works like #1, and you can trade 24/7.
- **FX:** PCA on G10 crosses pulls out the "USD factor" and "risk-on/off (carry)" factor, and you trade currencies' deviations from them.

## Pitfalls to avoid
- **Look-ahead bias:** fit PCA only on past data (rolling or expanding window), never on the full sample.
- **Sign flipping:** eigenvectors can flip sign between windows, so align them to the previous window.
- **Standardize first:** run PCA on the correlation matrix (z-scored returns), not raw prices.
- **Survivorship bias:** use point-in-time index membership.
- **Transaction costs:** residual stat arb trades often, so model slippage and borrow costs.
- **Instability:** the lower PCs are noisy, so don't over-interpret anything past about PC10.

## Recommended path
1. Start with **#2 (yield curve)** to build intuition. It's small, visual, and PCA behaves perfectly there.
2. Then build **#1 (residual stat arb)** as your real strategy.
3. Add **#4 (regime filter)** on top to control risk.

I can build any of these as a Python project: data download with `yfinance`, rolling PCA, signal generation, a vectorized backtest with costs, and performance charts (Sharpe, drawdown, equity curve). Which one do you want, and which market (US stocks, crypto, FX, rates)?

### You

I want to a build a strategy which can be used in forex or crypto propfirms

### You

[Request interrupted by user for tool use]

### You

I want to a build a strategy using pca which can be used in forex or crypto propfirms, tell me

### Claude

Below is a PCA strategy built around prop firm rules. Passing a prop firm challenge depends less on a high return than on keeping drawdown small and steady. PCA helps with that because it lets you trade assets relative to each other and hedge out the big market move, which is what usually blows accounts.

# The strategy: PCA residual mean reversion

**The idea:** most of a currency's or coin's movement comes from one or two shared factors. In FX that's mainly the US dollar and risk-on/risk-off sentiment; in crypto it's the overall market. PCA separates out those shared factors. What's left for each asset is a short-term deviation that tends to snap back. You trade that snap-back while staying hedged against the big move.

## Forex version

**1. Universe.** Express 7 currencies against USD: EUR, GBP, AUD, NZD, CAD, CHF, JPY. Flip USDCAD, USDCHF and USDJPY so every series is "currency vs USD".

**2. PCA.** Use 1-hour log returns over a rolling window of about 20 trading days, and z-score them before running PCA. You'll typically get:
- **PC1 ≈ the USD factor** (about 50–60% of variance)
- **PC2 ≈ risk-on/off** (AUD/NZD/CAD vs JPY/CHF)

Keep those 2 components. Whatever PCA doesn't explain is the **residual**, the currency's own move.

**3. Signal.** For each currency, add up its residual over the last N bars (for example 48) and z-score it. This is the **s-score**.

**4. Execution: trade crosses, not USD pairs.** Pick two currencies with similar PC loadings, one stretched up and one stretched down, and trade the cross between them. Because both currencies react alike to the shared factors, the cross is close to factor-neutral. Good candidates:
- **AUDNZD, EURCHF, EURGBP, AUDCAD, NZDCAD, CADCHF**
- Example: AUD s-score = +2.3 and NZD s-score = −1.8 → **short AUDNZD**
- Each trade is one position, which is easy on MT5 or cTrader.

**5. Rules**
- **Entry:** spread of s-scores > 2.0
- **Take profit:** spread returns below 0.5
- **Hard stop:** about 1.5× ATR, or the s-score spread widens past 4 (the relationship has broken)
- **Time stop:** close after about 2× the estimated half-life (roughly 1–3 days)

## Crypto version

**1. Universe.** 10–15 liquid perpetual futures: BTC, ETH, SOL, XRP, BNB, DOGE, ADA, AVAX, LINK, LTC, and so on.

**2. PCA.** Use 1h or 4h returns over a 30-day window. PC1 is the crypto market factor and often explains 60–75% of variance.

**3. Signal.** Compute an s-score from each alt's residual, as in the FX version.

**4. Execution.**
- Go long the most oversold alt and short BTC (or BTC+ETH), sized by the alt's beta to PC1. The hedge removes most market risk.
- If the firm only allows one position or has low alt leverage, trade only the extreme signals, unhedged, with tight stops. This carries more risk.

**5. Important caveat.** In crypto, residuals often **mean-revert on intraday horizons** but can **trend over several days** (narrative pumps). Backtest both "fade" and "follow" before choosing.

## Regime filter (both markets)

Trade only when conditions are normal:
- **Stand aside** when PC1's share of variance jumps, for example 15+ percentage points above its 60-day average. That means correlation is spiking, which usually signals panic or a macro event, and relative-value trades fail then.
- **Stand aside** when residual volatility is above its 90th percentile.
- **FX:** no new entries 30 minutes before or after high-impact news (NFP, CPI, FOMC, central bank decisions). Many firms ban news trading anyway.

# Fitting prop firm rules

| Prop rule (typical) | How the strategy handles it |
|---|---|
| Daily loss limit of 4–5% | Your own daily stop at **2%** stops trading for the day |
| Max drawdown of 8–10% (static or trailing) | Risk **0.25–0.5% per trade**; halve position size once drawdown passes 4% |
| Profit target of 8% / 5% | About 1–2 trades a day at a 0.4% average win gets there in 4–8 weeks without forcing it |
| Consistency rule | Cap daily profit at about 2%, then stop for the day |
| No martingale or grid | Never average down. One entry, hard stop |
| Weekend holding (FX) | Close all FX positions Friday evening |
| Correlated exposure | At most 3 open trades, and no currency in more than 2 of them |

**Phase management:** in the challenge phase use normal size. Once funded, cut risk to about 0.25% per trade, since keeping the account matters more than growing it.

# How to validate before paying for a challenge

1. **Data.** FX: Dukascopy (free, hourly/tick). Crypto: Binance/Bybit history via `ccxt`.
2. **Walk-forward backtest.** Fit PCA only on past data (no look-ahead), and align eigenvector signs between windows because they can flip.
3. **Realistic costs.** Crosses like AUDNZD cost about 1.5–3 pips. Crypto costs fees plus funding. Costs decide whether this strategy works.
4. **Prop firm simulator.** Replay the equity curve against the actual rules (daily limit, max drawdown, target). Then run a Monte Carlo of about 1,000 challenge attempts to estimate the **pass rate**. This is a better guide than Sharpe ratio.
5. **Deploy.** Use MT5 through the Python `MetaTrader5` package, or port the strategy to an MQL5 expert advisor (EA). First check the firm's rules on EAs, copy trading and HFT.

# Honest expectations
- This is a **low-volatility, high-win-rate, small-edge** strategy. Spreads can erase the edge, especially at small timeframes.
- It suits prop firms because of drawdown control, not explosive returns.
- The regime filter and hard stops are not optional. Unstopped mean reversion is the #1 way prop accounts get blown.

I can build it in Python: data loader, rolling PCA, signals, a backtest with costs, and the prop firm Monte Carlo pass-rate simulator. Should I start with **FX (AUDNZD/EURGBP-style crosses)** or **crypto (alt vs BTC)**, and which prop firm's rules should I model?

### You

tell me how pca is importance here like how signal is decided give me an exmaple of forex version and tell

### Claude

# Why PCA matters here

When AUD/USD drops 1.3%, the chart alone doesn't tell you why. There are three possible reasons:

1. **The USD got stronger.** Every currency falls against it, so AUD isn't special.
2. **Markets went risk-off.** AUD always falls when that happens, so again AUD isn't special.
3. **Something specific to AUD.** This is the only part that is a real mispricing that might snap back.

Price shows you all three mixed together. PCA pulls them apart:

```
AUD's move = (USD factor part) + (risk-on/off factor part) + RESIDUAL
               └────────── explained by PCA ─────────┘      └ what you trade ┘
```

Without PCA, you might buy AUD/USD because "it fell a lot" and lose money as the USD keeps rallying. With PCA, you trade only the unexplained part and hedge away the rest.

---

# How the signal is calculated (5 steps)

**Step 1. Returns matrix.** Take hourly returns of 7 currencies vs USD over the last 20 days, about 480 rows × 7 columns. Flip USDJPY, USDCAD and USDCHF so every column reads "currency strength vs USD".

**Step 2. Run PCA.** PCA finds the hidden common drivers:
- **PC1 (USD factor):** all 7 currencies move together, about 55% of variance
- **PC2 (risk factor):** AUD/NZD/CAD move one way, JPY/CHF the other, about 15% of variance

**Step 3. Measure each currency's sensitivity (beta) to each factor.** Regress each currency's returns on PC1 and PC2:

| Currency | β to PC1 (USD) | β to PC2 (risk) |
|---|---|---|
| EUR | 1.00 | 0.10 |
| GBP | 0.90 | 0.20 |
| **AUD** | **1.10** | **0.80** |
| **NZD** | **1.05** | **0.75** |
| CAD | 0.70 | 0.50 |
| CHF | 0.95 | −0.40 |
| JPY | 0.80 | −0.70 |

AUD and NZD have almost identical betas, so they're "twins". Hold that thought.

**Step 4. Residual = actual move − expected move.**

**Step 5. s-score = residual ÷ its normal size (standard deviation).** An s-score beyond ±2 means the move is unusually large.

---

# Worked example (illustrative numbers)

**Situation:** over the last 48 hours, US CPI came in hot. The USD rallied and markets turned slightly risk-off. PCA measures the factor moves:
- **PC1 (USD factor) = −0.60%** (all currencies weakened vs USD)
- **PC2 (risk factor) = −0.20%** (mild risk-off)

**Expected move for each currency = β1 × (−0.60) + β2 × (−0.20)**

| Currency | Actual 48h move | Expected (from factors) | **Residual** | Residual std | **s-score** |
|---|---|---|---|---|---|
| EUR | −0.55% | −0.62% | +0.07% | 0.15% | +0.5 |
| GBP | −0.60% | −0.58% | −0.02% | 0.16% | −0.1 |
| **AUD** | **−1.30%** | **−0.82%** | **−0.48%** | 0.20% | **−2.4** |
| **NZD** | **−0.70%** | **−0.78%** | **+0.08%** | 0.18% | **+0.4** |
| CAD | −0.50% | −0.52% | +0.02% | 0.14% | +0.1 |
| CHF | −0.45% | −0.49% | +0.04% | 0.15% | +0.3 |
| JPY | −0.35% | −0.34% | −0.01% | 0.17% | −0.1 |

**What the table shows:**
- Every currency fell, and PCA explains nearly all of it: EUR, GBP, CAD, CHF and JPY have tiny residuals, so they are fairly priced.
- **AUD fell 0.48% more than the USD and risk factors can explain**, an s-score of −2.4. AUD is oversold on its own.
- NZD, its twin, behaved normally.

**Signal:** buy AUD, sell NZD → **long AUD/NZD**
- s-score spread = (+0.4) − (−2.4) = **2.8**, above the 2.0 entry threshold ✅
- **Hedge check:** long AUD/NZD carries net exposure of 1.10 − 1.05 = **0.05** to the USD factor and 0.80 − 0.75 = **0.05** to the risk factor. That is almost zero, so if the USD keeps rallying or risk-off deepens, both legs move together and cancel out.

**Regime check:** PC1's share of variance is 55% against a 60-day average of 52%, which is normal, so trading is allowed. If CPI had pushed it to 80%, meaning everything moving in lockstep, you would skip.

---

# The trade (on a $100k prop account)

| Item | Value |
|---|---|
| Entry | Long AUD/NZD at 1.0850 |
| Risk | 0.5% = $500 |
| Stop | 35 pips (1.0815), roughly where the s-spread would hit 4 and the relationship is broken |
| Size | $500 ÷ (35 pips × ~$6 per pip per lot) ≈ **2.4 lots** |
| Exit | When the s-spread falls back below 0.5, about +50 pips (~$720) |
| Time stop | Close after 3 days if nothing happens |

**Scenario A (reversion, the usual case):** the AUD-specific selling fades and AUD/NZD recovers about 50 pips. The USD's direction didn't matter, because the hedge removed it.

**Scenario B (a real regime change):** AUD fell because the RBA surprised with a dovish cut. That is new information, so the residual keeps widening and you're stopped out for −$500 (0.5%). This is why you always check the news calendar and always use a hard stop.

---

# Why not just watch the AUD/NZD chart?

You could z-score the AUD/NZD price directly, but PCA gives you three things that approach can't:

1. **It picks the pair.** PCA ranks all 7 currencies at once and shows AUD as the outlier. Across 21 possible crosses, it tells you which one to trade.
2. **It proves the hedge.** The betas show AUD/NZD is factor-neutral. A cross like AUD/JPY is not: its betas differ by 1.5 on the risk factor, so you'd be making a hidden risk-on bet.
3. **It filters out false signals.** If AUD and NZD both fell because of risk-off, a naive approach might misread it. PCA knows how much of the move risk-off explains.

---

# Core code (the essence)

```python
import numpy as np
from sklearn.decomposition import PCA

# R: 480 x 7 hourly returns (EUR, GBP, AUD, NZD, CAD, CHF, JPY vs USD)
Z = (R - R.mean()) / R.std()                     # standardize
pca = PCA(n_components=2).fit(Z)
F = pca.transform(Z)                             # factor returns (PC1, PC2)

betas = np.linalg.lstsq(F, R, rcond=None)[0]     # each currency's sensitivity
resid = R - F @ betas                            # unexplained part

cum = resid[-48:].sum(axis=0)                    # last 48h residual
roll = resid.rolling(48).sum()                   # history of 48h residuals
s = (cum - roll.mean()) / roll.std()             # s-score per currency

explained_pc1 = pca.explained_variance_ratio_[0] # regime filter input
```

Then choose the most positive and most negative s-scores among twin pairs (AUD/NZD, EUR/CHF, EUR/GBP, AUD/CAD), check that the spread is above 2 and the regime is normal, and trade the cross.

These numbers only show the mechanics; they aren't real market data. I can build a full backtest on real hourly FX data with spreads included, to see whether this edge survives costs and prop firm rules.

### You

why vairance is important here

### Claude

In this strategy, variance simply means **how much something moves around**. It shows up in five places, and each one does a different job.

---

## 1. PCA itself works by hunting for variance

PCA asks one question: **which combination of currencies explains the most movement?**

- **PC1** is the single direction that captures the most variance. In FX that's "everything moves against the USD together".
- **PC2** captures the most of what's left, which is risk-on/off.
- And so on.

So variance is literally how PCA ranks what matters. A factor that explains a lot of variance is a real market driver. A factor that explains little is mostly noise.

---

## 2. Explained variance tells you how many PCs to keep

Typical FX output:

| Component | Variance explained | Cumulative |
|---|---|---|
| PC1 (USD) | 55% | 55% |
| PC2 (risk) | 15% | 70% |
| PC3 | 9% | 79% |
| PC4–PC7 | ~5% each | 100% |

- **Keep too few (only PC1):** risk-off moves stay in your residuals. AUD falling in a risk-off market then looks like a signal when it isn't, so you get **false signals**.
- **Keep too many (PC1–PC5):** you strip out the currency-specific moves you actually want to trade, and the residuals become tiny, so you get **no signals**.

Keep the components that explain real, stable variance (usually 2 for 7 currencies) and treat the rest as tradable residual.

---

## 3. Standardizing so no currency dominates

Currencies have different natural variance: AUD might move 0.8% a day and CHF 0.4%. If you run PCA on raw returns, PC1 bends toward the volatile currencies just because they move more, not because they matter more.

That's why the code does `Z = (R - mean) / std`. It puts every currency on the same scale, so PCA finds **shared behaviour (correlation)**, not just "who is loudest".

---

## 4. Residual variance turns moves into s-scores

This is the most important one for the signal. Two residuals from the example:
- AUD residual = −0.48%
- EUR residual = +0.07%

Whether −0.48% is big depends on how much AUD's residual normally moves:

| | Residual | Normal residual std | s-score | Meaning |
|---|---|---|---|---|
| AUD | −0.48% | 0.20% | **−2.4** | Rare, a signal |
| Same −0.48% for a currency with std 0.60% | −0.48% | 0.60% | −0.8 | Normal noise, no signal |

The same move can be a signal or noise. Dividing by the residual standard deviation (the square root of its variance) makes all 7 currencies comparable, so one threshold (±2) works for all of them.

---

## 5. PC1's variance share is your regime filter

PC1's share of variance measures **how much all currencies move together** (correlation):

| PC1 share | Market state | Action |
|---|---|---|
| ~50–55% | Normal: currencies have their own stories | ✅ Trade. Residuals are meaningful and tend to revert |
| ~75–85% | Panic or macro shock (CPI, FOMC, crisis): everything moves in lockstep | ❌ Stand aside |

When PC1 dominates, the residuals are tiny and unreliable, and "mispricings" usually mean the factor structure itself is shifting. Mean reversion fails in exactly these moments. For a prop account, this filter keeps you out of the days that break the daily loss limit.

---

## Bonus: variance drives position sizing

A trade's risk equals its volatility (standard deviation, the square root of variance) times position size. Low-variance crosses like AUD/NZD allow larger sizes for the same dollar risk. When volatility rises, you cut size so each trade still risks only 0.5%, which keeps you inside the prop firm's drawdown rules.

---

## Summary

| Where | What variance does |
|---|---|
| PCA | Finds the main market drivers (directions of maximum movement) |
| Explained variance | Decides how many factors to remove: signal vs noise |
| Standardization | Stops volatile currencies from dominating |
| Residual variance | Turns raw moves into comparable s-scores, so it decides the signal |
| PC1 variance share | Regime filter: when to trade and when to stay out |
| Volatility | Position sizing to respect prop firm drawdown limits |

In short, variance tells you what's normal. The strategy trades only when a currency's own movement is abnormally large while the market overall is behaving normally.

### You

like a 5 year old explain me a signal like when to take trade and which long or short?

### Claude

# The twins and the dog walk 🐕

Picture **two twin dogs, AUD and NZD**, on leashes, walking with their owner. The owner is the market (the US dollar).

- When the owner walks forward, **both dogs walk forward**.
- When the owner walks backward, **both dogs walk backward**.
- The twins almost always stay **side by side**, because they're twins.

That's what PCA tells us: AUD and NZD react to the owner the same way.

---

## One day...

The owner steps back, and both dogs step back. That's normal, so we ignore it.

But **AUD steps back a lot more than NZD**. Now AUD is **way behind** its twin.

```
Normal:      🐕AUD  🐕NZD      (side by side)

Today:  🐕AUD ........ 🐕NZD   (AUD fell behind!)
```

Twins don't stay apart for long. **AUD will probably run to catch up with NZD.**

---

## So what do we do?

- AUD is **behind**, and we expect it to come back up → **BUY AUD**
- NZD is **ahead**, and we expect it to come back down or stay put → **SELL NZD**

Buying AUD and selling NZD is one single trade:

## 👉 **BUY (long) AUD/NZD**

We don't care where the owner walks next. Both dogs move with the owner anyway, so that cancels out. We only care about **the gap between the twins closing**.

---

## The simple rules

| What you see | What it means | What you do |
|---|---|---|
| AUD fell **behind** NZD (AUD score very negative, like −2) | AUD is "too cheap" | **BUY AUD/NZD** 🟢 |
| AUD ran **ahead** of NZD (AUD score very positive, like +2) | AUD is "too expensive" | **SELL AUD/NZD** 🔴 |
| Twins are side by side (scores near 0) | Nothing unusual | **Do nothing** 😴 |
| Twins are back together after your trade | The gap closed | **Take profit** 💰 |
| The gap keeps getting **bigger** | Maybe AUD isn't coming back | **Stop loss**, get out ❌ |
| The owner is running wild (big news, panic) | Dogs are being dragged everywhere | **Don't trade** 🚫 |

---

## One-line version

> **Find two twin currencies. When one runs away from the other, bet that it comes back: buy the one that fell behind and sell the one that ran ahead.**

The **s-score** is just a ruler that measures **how far apart the twins are**:
- **0** = side by side
- **−2 or +2** = unusually far apart → **trade**
- **−4 or +4** = something broke → **get out**

### You

what is the role of s explain me as a 5 year old

### Claude

# The s-score is a "weirdness meter" 📏

In the dog story, the **s-score tells you how weird the gap between the twins is**. It's not how far AUD fell. It's how **unusual** that fall is **for AUD**.

---

## Why not just measure the distance?

Imagine two kids on a playground:

- 🧒 **Calm Tom** always stays close to his mom, about **1 step away**.
- 🏃 **Wild Max** always runs around, often **5 steps away**.

Today **both are 5 steps from their moms.**

- Tom 5 steps away? **That's weird!** Tom never does that. 😮
- Max 5 steps away? **That's normal.** Max always does that. 😴

**Same distance, different meaning.** So we don't just ask "how far?" We ask:

> **"How far is this compared to how far this kid USUALLY goes?"**

That answer is the **s-score**.

---

## How it's counted

```
s-score = how far away today ÷ how far away normally
```

- Tom: 5 steps ÷ 1 normal = **s = 5** → super weird! 🚨
- Max: 5 steps ÷ 5 normal = **s = 1** → nothing special 😴

---

## The weirdness meter

| s-score | What it means | What you do |
|---|---|---|
| **0** | Right where they normally are | Nothing 😴 |
| **±1** | A little off, happens all the time | Nothing 😴 |
| **±2** | Weird, doesn't happen often | **Take the trade** 🎯 |
| **back to ±0.5** | Almost back to normal | **Take profit** 💰 |
| **±4** | Way too weird, something broke | **Get out (stop loss)** ❌ |

---

## Plus or minus tells you the direction

- **s = −2** → the currency fell **too far down** → it's "too cheap" → **BUY it** 🟢
- **s = +2** → the currency went **too far up** → it's "too expensive" → **SELL it** 🔴

---

## Why it matters

Without the s-score, you'd have to guess separately for every currency whether a move was big. Some currencies move a lot, some a little.

**With the s-score, every currency uses the same ruler.** One simple rule works for all of them:

> **When the weirdness meter hits 2, trade. When it goes back near 0, take profit. If it hits 4, run away.**

### You

what is s in technical now?

### Claude

# The s-score, technically

The s-score is a **z-score of the cumulative residual** from the PCA factor model. It measures how many standard deviations the residual currently sits from its equilibrium level. It's calculated in four steps.

---

## Step 1: Residual returns from the PCA factor model

For each currency *i* at each hourly bar *t*:

```
r_i,t = β_i1 · F1_t + β_i2 · F2_t + ε_i,t
```

- `r_i,t` = currency return vs USD
- `F1, F2` = PC1 and PC2 factor returns (PC scores)
- `β` = factor loadings from regressing r_i on F over the lookback window
- `ε_i,t` = **residual return**, the idiosyncratic part not explained by the common factors

---

## Step 2: Cumulative residual (the "spread level")

Returns are noisy increments. Mean reversion shows up in **levels**, so sum the residuals into a path:

```
X_i,t = Σ ε_i,k   (k = t−L+1 … t),   L = lookback window, e.g. 480 hourly bars
```

`X_i` behaves like a synthetic price of "currency *i* with the USD and risk factors hedged out". This is the series you expect to mean-revert.

---

## Step 3: Two ways to turn X into s

### Version A: simple rolling z-score (easy, good for a first version)

```
s_i,t = ( X_i,t − mean(X_i) ) / std(X_i)
```

The mean and standard deviation are taken over the lookback window. This is quick, but it assumes the residual always reverts and says nothing about **how fast** it does.

### Version B: Ornstein–Uhlenbeck s-score (Avellaneda & Lee, 2010), the proper version

Model X as a mean-reverting Ornstein–Uhlenbeck (OU) process:

```
dX_t = κ (m − X_t) dt + σ dW_t
```

- `κ` = speed of mean reversion
- `m` = equilibrium level
- `σ` = volatility of the residual

You estimate it with a discrete AR(1) regression on X:

```
X_t+1 = a + b · X_t + ζ_t+1
```

From the fitted `a`, `b` and `Var(ζ)`:

| Parameter | Formula | Meaning |
|---|---|---|
| Reversion speed | `κ = −ln(b)` (per bar) | How fast the gap closes |
| Half-life | `h = ln(2) / κ` bars | Time to close half the gap |
| Equilibrium | `m = a / (1 − b)` | Where X "wants" to be |
| Equilibrium std | `σ_eq = √( Var(ζ) / (1 − b²) )` | Normal size of deviations |

**The s-score:**

```
s_i,t = ( X_i,t − m ) / σ_eq
```

Why Version B is better:
- `σ_eq` is the **stationary** standard deviation of a mean-reverting process, not just the sample std of a path that may be trending.
- You get a **validity test**: if `b ≥ 1` (no mean reversion) or the half-life is too long, **there's no signal**, whatever s says.

**Tradability filter** (Avellaneda–Lee use about half the window):

```
Trade only if:  0 < b < 1   AND   half-life < L / 2
                e.g. with L = 480 bars, require h < 240 bars (~10 trading days)
```

For prop firms you'd want something much tighter, like **h < 48–72 bars**, so trades resolve in 2–3 days.

---

## Step 4: Apply it to the cross (AUD/NZD)

You could compute `s_AUD − s_NZD`, but that ignores the correlation between the two residuals. It's better to **build the pair residual directly**:

```
ε_pair,t = ε_AUD,t − ε_NZD,t
X_pair,t = Σ ε_pair
```

Then fit the OU model on `X_pair` and compute **one s-score for the pair**.

---

## Trading rules in terms of s

Using the Avellaneda–Lee thresholds, adjusted:

| Condition | Action |
|---|---|
| `s < −2.0` (and the OU fit is valid) | **Open long** (pair is below equilibrium) |
| `s > +2.0` | **Open short** |
| Long open and `s > −0.5` | **Close long** (take profit) |
| Short open and `s < +0.5` | **Close short** |
| `|s| > 4.0` | **Stop out** (model broken) |
| Open longer than 2–3 × half-life | **Time stop** |
| `b ≥ 1` or half-life too long | **No trade** (not mean-reverting right now) |

The entry/exit thresholds should be optimized **walk-forward**. Treat 1.25–2.0 for entry and 0.5–0.75 for exit as starting ranges, not fixed truths.

---

## Code (Version B)

```python
import numpy as np

def ou_sscore(X):
    """X: 1-D array of cumulative residuals (the spread level)."""
    x_t, x_next = X[:-1], X[1:]
    b, a = np.polyfit(x_t, x_next, 1)          # AR(1): x_next = a + b*x_t
    if not (0 < b < 1):
        return None                             # no mean reversion -> no signal
    zeta = x_next - (a + b * x_t)
    m = a / (1 - b)
    sigma_eq = np.sqrt(zeta.var() / (1 - b**2))
    half_life = np.log(2) / -np.log(b)
    s = (X[-1] - m) / sigma_eq
    return {"s": s, "half_life": half_life, "m": m, "sigma_eq": sigma_eq}

# eps_aud, eps_nzd: residual return series from the PCA step
X_pair = np.cumsum(eps_aud[-480:] - eps_nzd[-480:])
sig = ou_sscore(X_pair)
# long AUDNZD if sig and sig["s"] < -2 and sig["half_life"] < 72
```

---

## One-sentence definition

> **The s-score is the number of equilibrium standard deviations that the cumulative factor-neutral residual currently sits from its OU mean. It is valid only when the residual is actually mean-reverting (0 < b < 1 with a short enough half-life).**

### You

so research paper on this is done or is this new like for forex crypto propfirm using pca?

### Claude

Short answer: **the building blocks are well researched, but the exact combination (PCA residual stat arb on FX crosses or crypto, designed around prop firm rules) is not a standard published strategy.** This is a new *application* of known ideas, not new theory.

These references are from memory, so check the exact details before citing them anywhere.

---

## ✅ Already well researched (solid foundations)

### 1. PCA statistical arbitrage (the core method)
- **Avellaneda & Lee (2010), "Statistical Arbitrage in the U.S. Equities Market"**, *Quantitative Finance*. This is **the** paper: PCA factors → residuals → OU model → s-score with ±1.25 / 0.5 thresholds. Everything in the s-score explanation comes from here. **It was done on US stocks, not FX or crypto.**
- **Krauss (2017), "Statistical Arbitrage Pairs Trading Strategies: Review and Outlook"**, *Journal of Economic Surveys*. A good survey of the whole field.
- **Gatev, Goetzmann & Rouwenhorst (2006), "Pairs Trading"**, *Review of Financial Studies*. The classic pairs-trading study.
- More recent work extends this with machine learning on PCA residuals, for example Guijarro-Ordóñez, Pelger & Zanotti, "Deep Learning Statistical Arbitrage".

### 2. PCA and factors in forex
- **Lustig, Roussanov & Verdelhan (2011), "Common Risk Factors in Currency Markets"**, *Review of Financial Studies*. Applies PCA to currency portfolios and finds a **dollar factor** (PC1) and a **carry / risk factor** (PC2). This is exactly the PC1/PC2 structure used in the example.
- **Verdelhan (2018), "The Share of Systematic Variation in Bilateral Exchange Rates"**, *Journal of Finance*. Shows the dollar and carry factors explain a large share of currency moves.

⚠️ These papers are about **explaining** currency returns (asset pricing), **not** about trading residual mean reversion on crosses like AUD/NZD.

### 3. PCA as a regime or risk filter
- **Kritzman, Li, Page & Rigobon (2011), "Principal Components as a Measure of Systemic Risk"**, *Journal of Portfolio Management*. Introduces the **"absorption ratio"**, essentially the "PC1 variance share" regime filter. When it spikes, markets are fragile.

### 4. Crypto
- **Liu, Tsyvinski & Wu (2022), "Common Risk Factors in Cryptocurrency"**, *Journal of Finance*. Crypto has a strong market factor, like PC1.
- PCA stat arb in crypto: there are **some smaller studies and working papers** (arXiv, SSRN), but nothing as definitive as Avellaneda & Lee for equities.

### 5. Trading under drawdown limits (the prop firm constraint)
- **Grossman & Zhou (1993), "Optimal Investment Strategies for Controlling Drawdowns"**, *Mathematical Finance*.
- **Chekhlov, Uryasev & Zabarankin (2005), "Drawdown Measure in Portfolio Optimization"**.

These cover the maths of max-drawdown limits, but **not prop firm rules** like daily loss limits, profit targets and pass probability.

---

## 🆕 What's not really covered (your gap)

| Piece | Status |
|---|---|
| PCA residual → OU → s-score | ✅ Established (equities) |
| PCA dollar / carry factors in FX | ✅ Established (asset pricing) |
| Using that for **residual mean reversion on factor-neutral FX crosses** (AUD/NZD, EUR/CHF…) | 🟡 Little formal research, mostly practitioner work |
| Same on **crypto perps (alt vs BTC hedge)** | 🟡 Some small or working papers |
| Absorption ratio as a **trade on/off filter** for stat arb | 🟡 Partly covered |
| Designing and evaluating a strategy around **prop firm rules** (daily loss, trailing drawdown, profit target, pass-rate Monte Carlo) | 🔴 **Essentially no academic literature** |

**The novel angle:** *"What is the probability of passing a prop firm challenge with a PCA stat arb strategy, and how should thresholds and sizing be tuned to maximize it?"*

Academic papers optimize **Sharpe ratio**. Prop traders need to optimize **P(hit +8% before −5% daily or −10% total)**. That's a different objective, and it could be written up as a research paper or blog post.

---

## ⚠️ Caution: "new" doesn't mean "profitable"

- Published edges tend to **shrink after publication** as more people trade them.
- Equity stat arb returns in Avellaneda & Lee were **much weaker after about 2003** than before.
- In FX, **spreads on crosses** and prop firm commissions can eat a small edge.
- The fact that nobody published it **could mean an opportunity, or that it doesn't survive costs**. Only a backtest will tell.

---

## Suggested next step

1. **Replicate** Avellaneda & Lee's method on FX crosses (hourly data, real spreads).
2. **Add** the absorption-ratio regime filter.
3. **Build** a prop firm simulator and measure the **pass rate**, not just Sharpe.
4. If the results are interesting, **that's your paper or edge**.

I can do a web search for recent (2023–2026) papers on PCA stat arb in FX or crypto to confirm nobody has published this exact angle, or start building the backtest.

### You

so I have heard gold and silver with usd moves together so tell me should i use metals with currencies? and others also like euro etc with these metals and main usd?

### Claude

Yes, you can add gold (XAU) and silver (XAG). They fit the PCA model naturally, but they need a few adjustments.

---

## Why gold, silver, EUR etc. all seem to move with the USD

Everything you look at is **priced in USD**: XAU/USD, XAG/USD, EUR/USD, AUD/USD. When the dollar weakens, all of them rise together, and when it strengthens, all of them fall.

That shared move is **PC1, the USD factor**. So a lot of the time, gold and the euro aren't really linked to each other. They are both reacting to the dollar. That's exactly what PCA separates:

```
Gold's move = USD factor + risk/safe-haven factor + METALS factor + gold's own residual
```

Gold is already treated like a currency; its code "XAU" is an official currency code. So adding it to the universe is natural.

---

## What changes when you add metals

**Universe: 7 currencies + gold + silver = 9 assets.**

Typical factor structure (illustrative):

| Asset | PC1 (USD) | PC2 (risk-on/off) | PC3 (metals) |
|---|---|---|---|
| EUR | high | low | ~0 |
| GBP | high | low+ | ~0 |
| AUD | high | **high +** | small + |
| NZD | high | **high +** | ~0 |
| CAD | medium | medium + | ~0 |
| CHF | high | **negative** (safe haven) | small + |
| JPY | medium | **negative** (safe haven) | ~0 |
| **Gold** | high | **negative** (safe haven) | **high** |
| **Silver** | high | **positive** (industrial) | **high** |

**Key point:** metals bring **their own factor (PC3)**. So:
- **FX only:** keep **2 PCs**
- **FX + metals:** keep **3 PCs**

If you keep only 2 PCs, the gold/silver residuals will contain the whole metals move. You'd get false signals on every metals rally.

---

## New "twin" pairs metals give you

| Pair | Why they're twins | How to trade | Quality |
|---|---|---|---|
| **Gold vs Silver** | Same metals factor, same USD factor | Long one, short the other, sized by beta (**gold/silver ratio**) | ⭐⭐⭐ Best |
| **Gold vs CHF / JPY** | All safe havens (negative risk loading) | XAU/CHF, or long XAU/USD + long USD/CHF | ⭐⭐ OK |
| **Silver vs AUD** | Both risk-on / commodity linked | Long XAG/USD + short AUD/USD | ⭐ Weaker |
| **Gold vs AUD** | Australia is a major gold producer | Two legs | ⭐ Weaker |

**Gold vs silver is the natural one.** It's the famous **gold/silver ratio** trade: when silver falls much more than gold "should" allow, buy silver and sell gold (and the reverse).

---

## ⚠️ Metals problems to know about

| Issue | Why it matters | Fix |
|---|---|---|
| **Much more volatile** (gold ≈ 2× EUR, silver ≈ 3–4× EUR) | Without standardizing, PCA gets dominated by metals | Always z-score returns before PCA ✅ |
| **Strong trends** (central bank buying, geopolitics, real yields) | Gold's residual can keep trending for months instead of reverting | Use the OU half-life filter strictly; trade only short half-lives |
| **Wider spreads and commissions** | Eats the small edge | Trade only strong signals (s > 2.5) |
| **Lower leverage at prop firms** (often 1:20–1:30 on metals vs 1:100 on FX) | Smaller positions | Size with this in mind |
| **Silver is thin and jumpy** | Big spikes, slippage | Smaller size, wider stops |
| **Two-leg trades** (gold/silver needs XAU/USD + XAG/USD) | Must enter both legs together; the hedge is only as good as the ratio | Size legs by beta, and check the firm allows it |
| **Some crosses don't exist** (XAU/CHF, XAU/XAG) at many prop firms | Can't trade them as one symbol | Build them from two legs |

---

## My recommendation: 3 separate "books"

Instead of one big 9-asset model at first:

**Book 1: FX only (7 currencies, 2 PCs)**
- Trades: AUD/NZD, EUR/CHF, EUR/GBP, AUD/CAD, NZD/CAD
- Cleanest structure; start here

**Book 2: Metals (gold vs silver)**
- Hedge out the USD factor, trade the ratio residual
- Two legs: XAU/USD and XAG/USD, beta-weighted
- OU s-score on the ratio residual, same rules as before

**Book 3 (later): Combined universe (9 assets, 3 PCs)**
- Only after Books 1 and 2 work
- Use it to find cross-asset twins (gold vs CHF/JPY)
- Check that PC3 really is a "metals factor" by looking at the loadings

**Also: gold as an extra regime signal.** When gold spikes along with CHF and JPY together, that's a **risk-off / panic** signal. Combine it with the PC1 variance filter and stand aside.

---

## Prop firm angle
- ✅ XAU/USD is available at nearly every FX prop firm, and XAG/USD at most of them.
- ✅ Gold and FX trades don't overlap much, so running both books **spreads risk** and gives more trade opportunities, which helps reach the profit target.
- ⚠️ But **correlated losses** on a USD shock day can hit both books at once. Keep one combined **daily stop** (for example 2%) across everything.
- ⚠️ Keep the risk per trade **lower on metals** (for example 0.25% vs 0.5% on FX), because gaps and spikes are bigger.

---

## Bottom line

> **Yes, add gold and silver, but as their own group with their own factor.** They move with EUR and the others mostly because of the **USD**, which PCA removes. The best metals trade is **gold vs silver**, and the best FX trades stay the **twin crosses**. Start with FX alone, add metals second, and combine them only once each works on its own.

I can build the backtest with both books (FX crosses + gold/silver) and a shared prop firm risk layer, so you can compare which one passes challenges more reliably.

### You

so tell me what data I will be needing for this and tell me the comodities also

### Claude

The core need is **hourly price data (with bid/ask spreads) for about 15–20 instruments over 5+ years**, plus some supporting data for costs, news and prop firm rules.

---

# 1. Instruments

## 🟦 Forex: the PCA universe (7 currencies)
**Core (required):**
| Symbol | Why |
|---|---|
| EUR/USD | Largest currency, heavy USD factor loading |
| GBP/USD | Twin to EUR |
| AUD/USD | Risk-on, commodity currency |
| NZD/USD | Twin to AUD |
| USD/CAD | Oil-linked currency |
| USD/CHF | Safe haven |
| USD/JPY | Safe haven |

**Optional (more twins, wider spreads):**
| Symbol | Why |
|---|---|
| USD/NOK | Oil currency, twin to CAD |
| USD/SEK | Twin to EUR / NOK |

## 🟩 Forex: crosses you actually trade (needed for real cost data)
AUD/NZD, EUR/GBP, EUR/CHF, AUD/CAD, NZD/CAD, CAD/CHF

You need these separately because their **real spreads** are wider than two USD pairs combined would suggest.

## 🟨 Commodities

### Metals ⭐ (best fit)
| Symbol | Priority | Notes |
|---|---|---|
| **XAU/USD (Gold)** | ✅ Must-have | Safe haven, available at every prop firm |
| **XAG/USD (Silver)** | ✅ Must-have | Twin to gold, more industrial and risk-on |
| XPT/USD (Platinum) | 🟡 Optional | Twin to palladium; thinner market |
| XPD/USD (Palladium) | 🟡 Optional | Very jumpy, wide spreads |
| Copper | 🟡 Optional | Tracks economic growth; links to AUD and silver |

### Energy
| Symbol | Priority | Notes |
|---|---|---|
| **WTI crude (USOIL)** | ✅ Good | Twin to Brent |
| **Brent crude (UKOIL)** | ✅ Good | WTI vs Brent is a classic spread trade |
| Natural gas | ❌ Skip | Weather-driven and very volatile. Bad for prop firm drawdown rules |

### Twin trades these unlock
| Twin pair | Relationship |
|---|---|
| Gold ↔ Silver | Same metals factor (gold/silver ratio) |
| WTI ↔ Brent | Same oil, different location |
| Platinum ↔ Palladium | Same car-industry metals |
| Oil ↔ CAD / NOK | Oil exporters' currencies |
| Gold ↔ CHF / JPY | All safe havens |
| Copper / Silver ↔ AUD | Risk-on commodities |

### ❌ Skip at first
Agricultural commodities (wheat, corn, coffee, and so on). Most prop firms don't offer them, their spreads are wide, and they're driven by weather and seasons.

## 🟥 Crypto (only for a crypto prop firm)
BTC, ETH, SOL, XRP, BNB, DOGE, ADA, AVAX, LINK, LTC (perpetual futures), plus **funding rates**, which are a real cost of holding perps.

## ⬜ Regime-filter data (not traded, only for context)
| Data | Used for |
|---|---|
| US 10-year yield / real yields (TIPS) | Explains gold trends |
| VIX | Risk-off detection |
| S&P 500 | Risk-on/off confirmation |
| DXY (dollar index) | Checking that PC1 really is the USD factor |

---

# 2. Data specs

| Item | Requirement | Why |
|---|---|---|
| **Timeframe** | **1-hour bars** for signals, **1-minute bars** for simulating trades | Signals are hourly; stops and take-profits need finer data to test realistically |
| **History** | **5+ years** (2019 → now) | Must include COVID 2020, the 2022 rate hikes, the 2023 banking stress and the 2024–25 gold rally |
| **Fields** | Open, High, Low, Close, **plus bid and ask** (or the spread) | Costs make or break this strategy |
| **Time zone** | Everything in **UTC**, aligned | PCA needs all assets at the same timestamps |
| **Trading hours** | Handle FX weekend gaps and the daily 1-hour break in metals and oil | Avoid fake returns across gaps |
| **Oil contracts** | **Continuous, roll-adjusted** prices | Contract rollovers create fake price jumps |

**Size:** 1h × 5 years × 20 instruments is about 600k rows, which is small. 1-minute data is about 30M rows, still fine on a laptop.

---

# 3. Where to get it

| Source | Covers | Cost | Notes |
|---|---|---|---|
| **Dukascopy** | FX, metals, some energy CFDs | Free | Tick or 1m data with **bid/ask**. The best free option |
| **HistData.com** | FX 1m, some gold | Free | No bid/ask spread |
| **Your prop firm's MT5 history** | Exactly what you'll trade | Free | **Most realistic.** Same feed, spreads and symbols. Limited history depth |
| **OANDA API** | FX, metals, CFDs | Free (practice account) | Good bid/ask data |
| **ccxt → Binance / Bybit** | Crypto + funding rates | Free | Full crypto history |
| **FRED** | Yields, VIX, macro | Free | For regime filters |
| **ForexFactory / Investing.com** | Economic calendar | Free | For the news filter |
| Databento / Norgate / Polygon | Clean futures, tick data | Paid | Only if you want institutional quality |

**Suggested combo:** Dukascopy for research and backtests, then your prop firm's **MT5 data** for final validation.

---

# 4. Supporting data (often forgotten)

| Data | Why | Where |
|---|---|---|
| **Spread history per symbol** | Cost per trade, especially at night and around news | Dukascopy bid/ask, or log it from MT5 |
| **Commission per lot** | Prop firms often charge $3–7 per lot round turn | Prop firm FAQ |
| **Swap / overnight fees** | Trades last 1–3 days | MT5 symbol specification |
| **Contract specs** (lot size, pip value, minimum lot) | Correct position sizing | MT5 symbol specification |
| **Leverage limits** (FX 1:100, metals 1:20–30, crypto 1:2–5) | Caps position size | Prop firm rules |
| **Economic calendar** (NFP, CPI, FOMC, central bank decisions) | News blackout filter | ForexFactory |
| **Prop firm rules** (daily loss, max drawdown type, target, minimum days, consistency, news rules) | For the pass-rate simulator | Prop firm website |

---

# 5. Recommended rollout

| Phase | Instruments | PCs |
|---|---|---|
| **1** | 7 FX majors + 6 crosses | 2 |
| **2** | + Gold, Silver | Separate metals model |
| **3** | + WTI, Brent (+ CAD/NOK link) | Separate energy model |
| **4** | Combined universe | 3–4, check the loadings |
| **Crypto** | Separate project entirely | 1–2 |

---

## Minimum checklist to start (phase 1 + 2)
- ✅ 7 FX majors, 1h + 1m, bid/ask, 2019 → now
- ✅ 6 FX crosses, 1h + 1m, bid/ask
- ✅ XAU/USD and XAG/USD, 1h + 1m, bid/ask
- ✅ Economic calendar (high-impact events)
- ✅ Your prop firm's rules, commissions and leverage

That's **15 instruments**, all free from Dukascopy. I can write a Python script that downloads all of it from Dukascopy, aligns it to UTC hourly bars and saves it ready for the PCA backtest. Which prop firm are you planning to use, so I can model its exact rules?

### You

can you write code and extract the data for gold silver with usd?

### Claude

Connection works (gold Jan 2024 = $2062.69 ✓). The 503s look like rate-limiting; testing with retries and pauses:

### Claude

Dukascopy is now refusing connections, most likely a temporary block from the rapid test requests. Checking whether it recovers:

### Claude

Running the Yahoo fallback first to get data right away:

### Claude

The Yahoo data works. Now checking whether Dukascopy has unblocked, for the full 2019+ history with spreads:

### Claude

I wrote the downloader and pulled about 2 years of hourly gold, silver and USD index data. The full 2019+ download with real spreads is written but hasn't run yet: Dukascopy (the free source) is blocking this machine, probably because my first test requests came too fast.

## What was downloaded
The data came from Yahoo Finance, from 29 Sep 2024 to 23 Sep 2026, about 11,300 hourly bars:

| File | What's in it |
|---|---|
| [XAUUSD_1h.csv](gold_silver_data/data/XAUUSD_1h.csv) | Gold, hourly open/high/low/close and volume |
| [XAGUSD_1h.csv](gold_silver_data/data/XAGUSD_1h.csv) | Silver, same fields |
| [USDX_1h.csv](gold_silver_data/data/USDX_1h.csv) | US Dollar Index (DXY) |
| [panel_1h.csv](gold_silver_data/data/panel_1h.csv) | All three closes lined up by UTC time, ready for PCA |

The code is in [fetch_data.py](gold_silver_data/fetch_data.py).

## What the data shows
| Hourly return correlation | Gold | Silver | USD |
|---|---|---|---|
| **Gold** | 1.00 | **0.77** | **−0.36** |
| **Silver** | 0.77 | 1.00 | −0.29 |

- **Gold and silver move together strongly (0.77).** That supports gold vs silver as a pair trade.
- **Gold does move against the USD, but only moderately (−0.36).** Over rolling 60-day windows the link ranged from −0.79 to almost 0. Most of gold's hourly movement comes from metals-specific drivers, not the dollar. That's why you need the USD index as a separate input: with only gold and silver, PCA can't tell a dollar move from a metals move.
- **Silver is about twice as volatile as gold** (48% vs 23% a year). In a gold vs silver trade, the silver position has to be roughly half the size in dollar terms.

## Limits of the Yahoo data
- These are **futures prices** (GC=F and SI=F), not the spot XAU/USD you'd trade at a prop firm.
- There are **no bid/ask spreads**, so trading costs can't be tested.
- It covers **only 2 years**, because Yahoo keeps only 730 days of hourly data.

## The full version (Dukascopy)
When you run the script without options, it downloads spot gold and silver with **bid, ask and spread** from 2019 onward. It also builds the USD index from 6 currency pairs using the official ICE formula. It waits about a second between requests so it doesn't get blocked, saves each month as it goes, and picks up where it stopped if you run it again. The first run takes about 20–30 minutes. Try it in an hour or two, once the block has cleared:

```bash
python fetch_data.py
```

The file-decoding step was checked on real gold data (January 2024 gold read correctly as $2062.69). Silver and the currency pairs couldn't be tested before the block, but the script prints a warning if any price looks wrongly scaled.

Next I can build the PCA model on this data: take the USD factor out of gold and silver, then compute the s-score for the gold/silver spread and backtest it.

If you want to keep this work, I can move this session to a folder you choose.

### You

try different ways to fetch the data of remaing years if possible.

### Claude

HistData.com is reachable, and the MetaTrader5 Python package is installed. Checking both:

### Claude

HistData's download form is standard (token + POST). Testing one year of gold:

### Claude

HistData works: silver 2020 went from $17.86 to $26.37, which matches the real market. Checking the monthly files for the current year and the USD index currencies:

### Claude

Moving the earlier Yahoo files into their own folder, then starting the full HistData download:

### Claude

Wrong folder; rerunning with the full path:

### Claude

While that runs, I'll check the MT5 terminal installed on this machine. It could be another data source:

### Claude

The download is running (it has reached gold 2019). It needs about 130 files, so it will take a few minutes. I'll report the results as soon as it finishes.

### Claude

The data covers 2019 to 18 Sep 2026. Checking it against the Yahoo data where they overlap, and looking for missing chunks:

### Claude

Two problems: the hourly moves match Yahoo only about 50% (they should be above 90%), and 2023 is missing about a quarter of its bars. The first one looks like a time-zone misalignment. Testing:

### Claude

Cleaning up that last edit properly:

### Claude

Converting the saved downloads to the corrected times, then checking which symbol has the 2023 gap:

### Claude

From late February to July 2023, HistData has only about 16 of every 24 hours. Checking which hours are missing:

### Claude

The missing hours are scattered at random (not one fixed block) between 20 Feb and 28 Jul 2023. Checking whether Dukascopy has unblocked, since it could fill those months:

### Claude

Validating against Yahoo again:

### Claude

I now have hourly spot gold, silver and a USD index from **1 Jan 2019 to 18 Sep 2026**, about 44,000 bars. They came from HistData.com, a free site of forex and metals price history. One stretch is patchy: from 20 Feb to 28 Jul 2023, a few random hours per day are missing.

## What I tried
| Source | Result |
|---|---|
| Dukascopy | ❌ Still blocking this machine (my fault: my first test requests came too fast) |
| Dukascopy's second server | ❌ Refuses automated requests |
| Stooq | ❌ Has a bot check, which I won't try to get around |
| **HistData.com** | ✅ **Worked: 2019 → 18 Sep 2026**, spot prices, 1-minute bars turned into hourly |
| Yahoo (earlier) | ✅ Last 2 years only, futures prices |

## The files, in `data/histdata/`
| File | Contents |
|---|---|
| [XAUUSD_1h.csv](gold_silver_data/data/histdata/XAUUSD_1h.csv) | Spot gold hourly OHLC, 44,839 bars |
| [XAGUSD_1h.csv](gold_silver_data/data/histdata/XAGUSD_1h.csv) | Spot silver hourly OHLC, 44,823 bars |
| [USDX_1h.csv](gold_silver_data/data/histdata/USDX_1h.csv) | USD index built from 6 currency pairs with the official ICE formula |
| [panel_1h.csv](gold_silver_data/data/histdata/panel_1h.csv) | All three lined up by UTC time: **43,940 bars, ready for PCA** |

## Checks
- **Price levels are right.** Gold went from $1,268 to $5,562 and silver bottomed at $11.79 in the March 2020 crash, both matching the real market.
- **I found and fixed a time-zone bug.** HistData's times follow New York time including daylight saving; I first assumed a fixed UTC−5, which put every summer bar 1 hour off. The fix is in [fetch_data.py](gold_silver_data/fetch_data.py).
- **It now matches the Yahoo data where they overlap.** Daily moves agree at 0.98–0.99 and hourly moves at 0.87–0.91. Hourly can't be perfect because Yahoo has futures and this is spot.

## Limits
- **2023 gap:** between 20 Feb and 28 Jul 2023, HistData is missing a few random hours per day, so the aligned panel has about half the normal bars for those months. I left them missing rather than inventing prices. The PCA code will need to skip returns that span a gap.
- **No bid/ask spreads.** HistData only has one price per bar, so trading costs still need another source.

## Two ways to fill those gaps
1. **Dukascopy, once it unblocks** (usually within hours). This fills 2023 and adds real spreads. In a terminal in the `gold_silver_data` folder, run:
   ```bash
   python fetch_data.py --source dukascopy
   ```
2. **Your MetaTrader 5.** I noticed an MT5 terminal on this computer with a Vantage demo account. The MT5 Python package can pull years of gold and silver history with real spreads straight from the broker, which is the same kind of data you'd trade on. It would open your MT5 terminal, and it only reads price history (no trades). Should I try that?

If you want to keep this work, I can move this session to a folder you choose.

### You

yes try mt5

### Claude

You've hit your session limit · resets 4pm (Asia/Kolkata)

### You

I hit my usage limit while you were working, but it has reset now. Please continue from where you left off.

### Claude

Found the MT5 terminal. Connecting through the Python package. This only reads data and uses whatever account the terminal is already logged into:

### Claude

MT5 opened with your Vantage demo account, but the login was refused. Trying once more in case the terminal just needed time to connect:

### Claude

I couldn't get the MT5 data. The terminal opened with your Vantage demo account (#[account]), but it refused the login: "Authorization failed". Most likely the password isn't saved in MT5, or the demo account has expired, as Vantage demo accounts often do after about 30 days of inactivity. I'm not allowed to type passwords for you, so this part needs you.

**To fix it (about 1 minute):**
1. In the MT5 window I opened, go to **File → Login to Trade Account**.
2. Enter your demo password and **tick "Save password"**.
3. If it says the account is invalid or expired, open a new demo with **File → Open an Account → Vantage**, and save the password.
4. Tell me when you're done.

The script will then pull from your broker:
- **XAUUSD and XAGUSD hourly bars with the real spread**, for as many years as Vantage keeps (usually back to 2015 or earlier). That fills the 2023 gaps and gives the trading costs HistData is missing.
- **The currency pairs for the USD index**, from the same feed.

It only reads price history; it won't place any trades.

Until then, the HistData files from last time (2019 → 18 Sep 2026) are ready in `data/histdata/`.

### You

vantage is logged in now extract the data now

### Claude

Connected. Vantage has the full history from 2019 to yesterday for gold and silver, each bar with its spread, plus a real USD index symbol (`USDX.r`). Adding MT5 as a source in the script:

### Claude

Still waiting on MT5 for GBPUSD. I'll continue as soon as that step finishes.

### Claude

All downloaded. Validating the time conversion, the 2023 gap, and the spreads:

### Claude

The MT5 extraction worked. You now have hourly gold, silver and a USD index from your Vantage terminal, from **1 Jan 2019 to 29 Sep 2026**, with the spread on every bar. This is now the best dataset of the three.

## The files, in `data/mt5/`
| File | Contents |
|---|---|
| [XAUUSD_1h.csv](gold_silver_data/data/mt5/XAUUSD_1h.csv) | Gold: 45,760 hourly bars, OHLC, tick volume, spread |
| [XAGUSD_1h.csv](gold_silver_data/data/mt5/XAGUSD_1h.csv) | Silver: 45,772 hourly bars, same fields |
| [USDX_1h.csv](gold_silver_data/data/mt5/USDX_1h.csv) | USD index built from Vantage's six currency pairs |
| [panel_1h.csv](gold_silver_data/data/mt5/panel_1h.csv) | All three lined up by UTC time, plus spreads: 45,421 bars, ready for PCA |

Vantage's own USD index symbol (`USDX.r`) only goes back to March 2022. So the script built the index from the six currency pairs with the ICE formula instead.

## Checks
- **The 2023 gap is filled.** 2023 has 5,893 bars, against 4,377 from HistData.
- **Times are correct.** MT5 bars match Yahoo (true UTC) in summer, winter, and the weeks around the clock changes.
- **It agrees with HistData.** Hourly moves match at 0.99 or better, and prices differ by less than 0.005%.
- **I fixed a second HistData time bug.** HistData changes its clocks on the European dates, not the US ones, so it was an hour off for 1–3 weeks each spring and autumn. The HistData files are rebuilt with the fix.

## Spreads

| | Typical spread | As % of price |
|---|---|---|
| Gold | $0.18–0.23 | about 0.005% |
| Silver | $0.02–0.035 | about 0.04% |

**Silver costs roughly 9 times more to trade than gold, relative to its price.** In a gold vs silver trade, the silver leg will carry most of the cost, so the strategy needs moves big enough to cover it.

## Caveats
- **The spreads are from a demo server.** They are the spread MT5 records for each bar, which is usually close to the best case. A prop firm's real spreads will be wider, especially around news and the daily market open.
- **About 240 hours of the USD index are missing in May–June 2020.** One of the six currency pairs has a hole in Vantage's history there. Gold and silver themselves are complete.
- **MT5 is still open** on your computer; I left it running.

To refresh the data later, with MT5 open and logged in, run this in the `gold_silver_data` folder:

```bash
python fetch_data.py --source mt5
```

The next step is the PCA model on this data: take the USD factor out of gold and silver, compute the s-score for the gold/silver spread, and backtest it with these spreads.

### You

canwe download second wise full historical data of xauusd?

### Claude

I'm testing how far back your Vantage terminal keeps tick-by-tick gold prices; second-level data is built from ticks. MT5 is fetching tick history from the broker's server, which is slow. I'll give you the answer once the test returns.

### Claude

Every tick request timed out, even for last week. Checking whether the terminal is still connected:

### Claude

The test is downloading two sample months of gold ticks from HistData (August 2026 and June 2019). These files are much larger than the hourly data. I'll report sizes and feasibility when it finishes.

### Claude

Yes, second-by-second gold data can be downloaded, but only from HistData, and it is a big job: about 10 hours of downloading for 2019 to now. I tested two sample months and they worked; I haven't started the full download.

## What I tested
| Source | Result |
|---|---|
| **Your MT5 (Vantage demo)** | ❌ It only returned ticks from the last 4 minutes. Requests for a day or more timed out. |
| **Dukascopy** | ❌ Still refusing requests from this machine (now "503 busy" rather than a hard block). |
| **HistData.com** | ✅ Has gold tick files for every month from 2009 to 2026. |

Nobody stores ready-made 1-second bars. You download every price update (ticks) and build the 1-second bars from them.

## What the HistData ticks look like
| | June 2019 | August 2026 |
|---|---|---|
| Ticks in the month | 3.5 million | 5.2 million |
| Seconds that have a price update | 1.0 million (49%) | 1.4 million (65%) |
| Download size (zipped) | 22 MB | 26 MB |
| Download time | 5 min | 9 min |
| Median spread | $0.29 | $0.61 |

- Each tick has a bid and an ask price with a millisecond timestamp, so you get the spread too.
- About a third to a half of all seconds have no price update. A 1-second bar file either skips those seconds or repeats the last price.
- The spreads here are about 3 times wider than Vantage's ($0.61 vs $0.21). HistData's prices come from a different liquidity provider, so treat its spread as a rough guide, not your trading cost.

## What the full download would involve
| Range | Months | Download | Time (at the speed I measured) | Final size as 1-second bars |
|---|---|---|---|---|
| 2019 → now | 93 | about 2.3 GB | about 10 hours | about 1.5 GB compressed |
| 2009 → now | 213 | about 5 GB | about 24 hours | about 3 GB compressed |

The server is slow (about 50 KB per second), and that's what sets the time. The script would save each month as it goes, so it can be stopped and resumed.

## Do you need it?
For the PCA strategy, the signals are hourly and 1-minute bars are enough to test stops and targets. I already have 1-minute gold from HistData for 2019–2026. Second-level data only matters if you want to study scalping, exact fills during news spikes, or how the spread behaves second by second.

## Before I start
- **Which range:** 2019 → now (about 10 hours) or 2009 → now (about 24 hours)?
- **What to keep:** 1-second bars only (my recommendation, about 1.5 GB), or the raw ticks as well (about 3 times larger)?

The computer needs to stay on with this session open for the whole download.

### You

<pasted_content id="d732">[private strategy code removed]</pasted_content id="d732">

use this and pull data of oanda and compare it with hist data and tell wether they are same or not so first extract 1minute data from this code of same time of xauusd and then 1 minute data of hist of xauusd on same timeline. and tell if both are same or no.

### Claude

Installed. Pulling the OANDA 1-minute gold bars from TradingView first, to see what time range it gives:

### Claude

The pasted code has two small mistakes: the real method is `get_hist` (not `get_history`), and the module is `tvDatafeed`. Fixing and rerunning:

### Claude

**No, they are not the same, but they track each other very closely.** The OANDA and HistData gold prices move together almost perfectly, but OANDA is consistently about $0.33 higher, and no bar matches exactly.

## What I could compare
TradingView's free feed gives at most 5,000 bars, so 1-minute OANDA data only reaches back about 3.5 trading days. HistData's newest file stops at 24 Sep. That left only a **204-minute overlap** at 1-minute level (24 Sep, 19:31–23:58 UTC), which is the quietest part of the day. So I added a larger check with 5-minute bars, which overlap for 3 weeks.

| | 1-minute bars | 5-minute bars |
|---|---|---|
| Overlap | 24 Sep, 204 bars | 4–24 Sep, 4,038 bars |
| Bars with identical close | 0% | 0% |
| Average gap (OANDA minus HistData) | +$0.46 | +$0.35 |
| Gap in 95% of bars | under $1.52 | under $0.56 |
| Largest gap | $1.86 | $4.50 |
| How closely the moves match (correlation) | 0.957 | 0.998 |

## What the difference looks like
- **OANDA is always the higher one.** The gap is about $0.31 during London and New York hours and about $0.46 around the daily market close (20:00–01:00 UTC), when spreads widen.
- **The likely reason is bid versus mid price.** HistData's bars are bid prices. A gap of about $0.31 is half of HistData's own spread (about $0.61), which is what you'd see if OANDA's bars are mid prices. I haven't confirmed how TradingView builds the OANDA bars, so treat this as the probable explanation.
- **The timestamps line up.** Shifting either series by a minute drops the correlation to about zero, so there is no time offset between them.
- **No missing bars** on either side in the 5-minute window.

In practice the two sources are interchangeable for hourly signals. As a share of price the gap is about 0.01%, and because it is nearly constant it cancels out of returns. They are not interchangeable for anything that depends on exact price levels, such as stop-loss fills or scalping a few cents.

## About the code you pasted
It needed two fixes to run: the method is `get_hist`, not `get_history`, and the module name is `tvDatafeed`. I installed the library from its GitHub repo (rongardF/tvdatafeed). It is an unofficial tool that reads TradingView's feed without a login, so the 5,000-bar limit applies.

To rerun the 1-minute comparison later (when HistData has published more days, the overlap will still be limited to the last 5,000 minutes):

```bash
python compare_oanda_histdata.py
```

Files are in `gold_silver_data/data/compare/`:
- [oanda_xauusd_1m.csv](gold_silver_data/data/compare/oanda_xauusd_1m.csv)
- [histdata_xauusd_1m.csv](gold_silver_data/data/compare/histdata_xauusd_1m.csv)
- [joined_xauusd_1m.csv](gold_silver_data/data/compare/joined_xauusd_1m.csv)
- [compare_oanda_histdata.py](gold_silver_data/compare_oanda_histdata.py)

### You

so using hist data instead of oanda assuming that data will be same , so I will be wrong if we make japenese candles from both of them, then candles will be slight different?

### Claude

Yes, the candles come out slightly different, but you would not be meaningfully wrong for this strategy. I measured it on the same overlap data:

| Candle size | Candles compared | Same colour (up/down) in both | Body size differs by | Typical body size |
|---|---|---|---|---|
| 1-minute | 204 | 91% | $0.15 | $0.61 |
| 5-minute | 4,037 | 98% | $0.15 | $2.51 |
| 1-hour | 408 | 97% | $0.40 | $9.31 |

- **The whole candle is shifted, and the shape barely changes.** OANDA sits about $0.33 above HistData, and the open, high, low and close all move up together.
- **Only tiny candles flip colour.** The candles that are green in one source and red in the other have very small bodies, around $0.17 on 1-minute and $1.63 on 1-hour. These are near-doji candles where a few cents decide the colour.
- **Bigger candles almost always agree.** Among candles with a body over $1, the colour matches 100% of the time on 1-minute bars and about 99% on the 5-minute and 1-hour bars.
- **The smaller the timeframe, the more it matters.** The difference is a quarter of a typical 1-minute body but only about 4% of a typical 1-hour body.

**For the PCA strategy:** it uses hourly returns (close-to-close changes), not candle patterns. A near-constant $0.33 offset cancels out of returns, which is why the two sources' moves agree at 0.998. HistData is fine for research and backtesting here.

**Where the difference would matter:**
- **Candlestick-pattern rules** (doji, engulfing, pin bars) on 1-minute or 5-minute charts would occasionally fire on one source and not the other.
- **Exact stop-loss and take-profit fills** can differ, because highs and lows are off by a few tens of cents, more around the daily close.
- **The final test** should use the feed you will actually trade on. No two brokers' candles match exactly, so your prop firm's candles will differ slightly from both OANDA and HistData.

### You

now continue again with pca

### You

[Request interrupted by user for tool use]

I want to a build a strategy using pca which can be used in forex or crypto propfirms, tell me

### You

yes try mt5

I hit my usage limit while you were working, but it has reset now. Please continue from where you left off.

### Claude

Picking up the PCA work with the MT5 data (gold, silver and the USD index, 2019 to 2026, with spreads). First step: see what PCA finds in these three markets before building any signal.

### Claude

I built the full PCA strategy and backtested it on 2019–2026. **As designed, it loses money, even before trading costs.** The diagnostics show why, and point to what to try next.

## What PCA found (this part works)
Over the full 2019–2026 data, the three markets split into three factors, and the split looks almost the same in every individual year:

| Factor | Share of movement | Meaning |
|---|---|---|
| PC1 | 68% | Gold and silver up, USD down, all together |
| PC2 | 24% | USD moving on its own |
| **PC3** | **8%** | **Silver vs gold** (+0.69 silver, −0.72 gold, about 0 USD) |

Because PC3 has almost no USD in it, the trade needs only two legs, XAUUSD and XAGUSD. The model is refitted every day using only past data, so there is no look-ahead.

## Backtest results (costs = demo spread × 1.5 + $6 per lot)
| | Result |
|---|---|
| Yearly return (compounded) | **−2.3%** |
| Sharpe ratio | −0.61 (−0.28 before costs) |
| Max drawdown | −18.8% |
| Trades | 104 (about 1 per month), 53% winners |
| Average hold | 52 hours |

- **6 of 8 years lose money**; only 2021 made money after costs.
- **Every one of the 9 parameter combinations I tried loses money**, so this isn't a case of bad settings.
- **Prop challenge** (+8% target, 5% daily loss, 10% max loss): at normal risk no attempt hits the target. Doubling or quadrupling the risk mostly adds failures; the best case passes 22% of attempts.

The entry and exit logic does what it should: trades that reach the target win 83% of the time (+0.41% each). But the stop-losses (−1.37% each) and time-outs eat all of it.

## Why it fails
I measured whether the gold/silver spread snaps back or keeps running, at different holding periods. A **variance ratio** below 1 means it snaps back; above 1 means it keeps trending:

| Holding period | 2h | 8h | 24h | 72h | 120h | 240h |
|---|---|---|---|---|---|---|
| Variance ratio | 0.95 | 0.91 | 1.00 | 1.05 | 0.96 | **1.14** |

- **Within a few hours there is a weak snap-back.**
- **Over days, the spread behaves like a random walk or trends.** Silver's big runs, such as the 2020 squeeze and the 2025 rally to $119, kept going instead of reverting.
- **The strategy holds about 2 days, which is exactly where there is no snap-back to capture.** Only 2021 and 2022 reverted, matching the one profitable year after costs (2021) and the year that came closest to breaking even (2022).

## What to try next (in the order I'd test them)
1. **Add the forex currencies** (the original plan). With only 3 markets there is just one leftover factor to trade. With 7 currencies plus metals you get many twin pairs (AUD/NZD, EUR/CHF…) where snap-back is better documented.
2. **Trade the spread as a trend instead.** Over 1–2 weeks the gold/silver spread tends to keep going. The edge is small (+0.28 Sharpe before costs if the current signal is reversed), so it needs a proper test.
3. **Very short-term snap-back (1–8 hours).** It exists, but it's so small that silver's spread (0.04% per side) probably eats it. Worth a quick check, but I'm not optimistic.
4. **Use PCA as a risk filter, not a signal.** PC1's share jumping from about 65% to 85% flags panic periods to stay out of, for any strategy.

Files:
- [pca_strategy.py](gold_silver_data/pca_strategy.py): the model, backtest and prop challenge simulator
- [trades.csv](gold_silver_data/data/backtest/trades.csv): every trade
- [equity.csv](gold_silver_data/data/backtest/equity.csv): hourly returns and s-score

My suggestion is option 1. I'd pull the 7 forex majors and the crosses from your MT5 and run the same PCA framework on the full universe. Should I go ahead?

### You

yes pull

### Claude

I'm pulling 11 markets and 9 crosses from your MT5:
- **Markets for the PCA model:** 9 currencies (EUR, GBP, AUD, NZD, CAD, CHF, JPY, NOK, SEK), plus gold and silver.
- **Crosses you would actually trade:** AUDNZD, EURGBP, EURCHF, AUDCAD, NZDCAD, CADCHF, EURNOK, EURSEK, NOKSEK, each with its spread.

MT5 loads each symbol's history from the server, which took a few minutes per symbol last time. I'll report when it finishes.

### Claude

The pull didn't start. MT5 had been closed since last time, so my script reopened it (it's on your screen now as demo account [account]), but the login was refused again with "Authorization failed". The password probably isn't saved in MT5. I'm not allowed to type it for you.

**To fix it:**
1. In the MT5 window, go to **File → Login to Trade Account**.
2. Enter the password and **tick "Save password"**, so future pulls work even after MT5 restarts.
3. Tell me when you're logged in, and I'll rerun the pull.

If you'd rather not wait, I can pull the same currencies from HistData instead. It covers all of them for 2019–2026, but it has no spreads, so the cost side of the backtest would rely on the gold/silver spreads we already have plus estimates for the crosses.

### You

yes histdata

### Claude

The strategy code is ready; it will run as soon as the download finishes.

### Claude

All 19 symbols downloaded for 2019 to 16 Oct 2026, and every price passed the sanity checks. Running the strategy:

### Claude

The forex version is a clear step forward: **the forex crosses really do snap back, and before costs the strategy makes money (Sharpe +0.59).** But with my assumed spreads, **trading costs eat the edge and it ends slightly negative (Sharpe −0.18).**

## Data
HistData gave me 9 currencies, gold, silver and 8 crosses from 2019 to 16 Oct 2026, with about 44,300 hourly bars where every market has a price. HistData has no spreads, so costs use **assumed typical prop-firm spreads** (for example AUD/NZD 0.018% of price, EUR/GBP 0.012%), plus $6 per lot commission.

## What PCA found
| Factor | Share | What it is |
|---|---|---|
| PC1 | 55% | USD: every currency moves together against the dollar |
| PC2 | 12% | Metals: gold and silver moving on their own |
| PC3 | 10% | Safe havens vs risk: JPY and CHF on one side, AUD, NZD and CAD on the other |

Together these three explain 77%; the remaining 23% is the leftover the strategy trades.

## Do the crosses snap back? Yes, unlike gold/silver
Variance ratio of each cross's leftover move (below 1 = snaps back):

| Cross | 24h | 72h | 120h | 240h |
|---|---|---|---|---|
| **EUR/SEK** | 0.73 | **0.62** | 0.65 | 0.63 |
| **AUD/CAD** | 0.88 | **0.72** | 0.66 | 0.65 |
| EUR/CHF | 0.88 | 0.78 | 0.75 | 0.77 |
| AUD/NZD | 0.86 | 0.82 | 0.86 | 0.78 |
| EUR/GBP | 1.05 | 0.99 | 0.90 | 0.91 |

Every cross is below 1 at 72 hours and beyond. For gold vs silver the equivalent figure was 1.05 to 1.14. So the idea works in forex, as the research suggested.

## Backtest (all 8 crosses, settings fixed before testing)
| | Result |
|---|---|
| Sharpe | **+0.59 before costs → −0.18 after costs** |
| Yearly return (compounded) | −1.4% |
| Max drawdown | −21% |
| Trades | 1,708 (about 19 per month), 56% winners, average hold 37h |
| **Average profit per trade vs cost** | **0.018% vs 0.023%**: costs are larger than the profit |

- **By cross (after costs):** AUD/CAD is the best (+9.4% total, Sharpe 0.57), followed by AUD/NZD and EUR/SEK. CAD/CHF and EUR/GBP are the worst.
- **Before costs, 6 of 8 years were profitable.** After costs, only 3 were.
- **Every settings variation I tried was profitable before costs (Sharpe +0.42 to +1.10).** That makes the edge look real rather than luck.
- **The result depends heavily on spreads.** With zero costs the Sharpe is +0.43; with double my assumed spreads it falls to −0.78.

**Prop challenge:** at 4× risk, 41% of attempts pass and 59% fail. That's not good enough to pay for challenges.

## Why it's close but not there yet
The strategy closes trades at s = 0.5, which grabs small snap-backs, and makes many trades, each paying the spread. The edge per trade is about the size of the spread. To fix that, each trade needs to capture a bigger move, or the strategy needs fewer, better trades. Two variations already point that way:
- **Longer 960-hour window:** Sharpe +0.31 after costs, max drawdown −10%, 517 trades.
- **Entry at s = 1.5:** Sharpe +1.10 before costs, but more trades.

**Caution:** I ran these variations on the same data I'm reporting, so picking the best one now would be curve-fitting.

## Next step I recommend
1. **Proper walk-forward test:** choose settings using 2019–2022 only, then test them untouched on 2023–2026.
2. **Changes aimed at costs:** trade only the crosses that snap back most (EUR/SEK, AUD/CAD, EUR/CHF, AUD/NZD), use the longer window, and exit at 0 instead of 0.5 to capture more per trade.
3. **Real spreads:** once your MT5 password is saved, I'll pull Vantage's actual spreads for these crosses. The verdict depends on them.

Files:
- [fx_pca_strategy.py](gold_silver_data/fx_pca_strategy.py)
- [fetch_fx_histdata.py](gold_silver_data/fetch_fx_histdata.py)
- [trades.csv](gold_silver_data/data/backtest_fx/trades.csv)
- [equity.csv](gold_silver_data/data/backtest_fx/equity.csv)

Should I run the walk-forward test with those cost-focused changes?

### You

download spreads now

### You

download spreads now

[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\C--Users-Admin-AppData-Roaming-Claude-scratch-workspaces-17196538-0cb6-4756-b882-7680761b6be5-bc07d694-d57d-4fc0-8ffa-59c6e6ea6fc6-scratch-2026-09-23-33ce44\0ce3e559-fdf8-4b30-9840-f1f2a4be8aed\images\1.png]

### Claude

I can't use that password. Logging in with credentials is something you need to do yourself, even for a demo account and even when you give it to me. What I can do is connect to MT5 once you're logged in. Checking whether the terminal is already logged in:

### Claude

MT5 is already logged in to account [account], so no password is needed from me. Pulling the forex data with spreads now:

### Claude

The download is running: 11 markets and 9 crosses, each with Vantage's recorded spread. MT5 loads each symbol's history from the server, so it takes a few minutes per symbol.

A security note: that password is now in this chat. It's only a demo account, so the risk is low, but change it if you use that password anywhere else. In future, just log in to MT5 yourself; I only need the terminal to be open and logged in.

### You

and for xauusd and silver if we use ifvg and fvg as entry modules then will it work and probability  increases?

### Claude

Possibly, but it can't be assumed. It needs to be tested, and how you combine the two matters a lot. Here's my view based on what we've already measured.

## What each tool does
| | PCA s-score | FVG / iFVG |
|---|---|---|
| Answers | **What** is mispriced, and which way | **When and where** to enter |
| Based on | Statistics across several markets | The candle pattern on one chart |
| Horizon | Days | Minutes to hours |

So FVG is a **timing filter**, not a new edge. A timing filter can improve a real edge by getting a better entry price, a tighter stop and better reward-to-risk. **It cannot create an edge that isn't there.**

## The problem specific to gold and silver
Our test showed that **the gold/silver spread does not snap back over days** (variance ratio about 1.0–1.14). There was only a weak snap-back within 1–8 hours. That means:

1. **FVG on top of the current gold/silver PCA signal:** the PCA bias itself has no edge at the 2–3 day horizon, so better timing won't fix it. ❌ Unlikely to help.
2. **FVG on the gold/silver ratio chart** (the spread itself): FVGs are a short-term retracement idea, and the 1–8 hour window is where we did see some snap-back. 🟡 This is the version worth testing, but silver's spread (about 0.04% per side) is a real hurdle.
3. **PCA as a bias, then FVG entries on gold or silver alone:** for example, "silver is cheap vs gold, so take only bullish FVG entries on XAGUSD". 🟡 Testable, but it **drops the hedge**. You're then exposed to the USD/metals factor, which is 68% of the movement, so the PCA advantage mostly disappears and it becomes a silver trend trade with a filter.

## Will the probability increase?
Be careful about which "probability" you mean:
- **Win rate** often **rises** with FVG pullback entries, because you enter at better prices.
- **But what matters is expectancy after costs** (average profit per trade, including losses and spreads), and for prop firms the **challenge pass rate**. A strategy can win 65% of the time and still lose money.

## Risks specific to FVG
- **Small FVGs depend on the data feed.** We measured that 1-minute candles differ between OANDA and HistData by $0.10–0.40, and 2–9% of small candles even flip colour. A small FVG on HistData may not exist at your prop firm. **Only count gaps larger than some fraction of ATR** (for example 0.3× ATR).
- **Lots of ways to define it:** minimum gap size, timeframe, how deep into the gap you enter, when an FVG becomes an iFVG, and when it expires. Each choice is a parameter, so the more you try, the higher the risk of curve-fitting.
- **Little independent evidence:** FVG and iFVG come from ICT trading education. I'm not aware of peer-reviewed studies showing they add an edge, so treat it as an idea to test, not a fact.

## How I'd test it fairly
Same data, same costs, settings chosen on 2019–2022 and tested on 2023–2026:

| Version | Entry rule |
|---|---|
| A | PCA alone (what we have) |
| B | FVG / iFVG alone, no PCA |
| C | **PCA bias + FVG / iFVG trigger** in that direction |
| D | PCA bias + **random** entry with the same stop and target (control) |

**C only counts as an improvement if it beats both A and D after costs.** If C beats A but not D, the gain comes from the stop/target structure, not from the FVG.

This should also run on the **forex crosses**, where the PCA edge actually exists (Sharpe +0.59 before costs). There, a timing filter that reduces trades and improves entry prices is exactly what's needed to get past the spread.

The MT5 download with real spreads is still running. Once it's done, I can build this four-way test. I'd also need to re-download gold and silver 1-minute data from HistData, since only the hourly bars were kept, for FVGs on 5–15 minute charts. Should I do it?

### You

why pca edge is not there in gold and silver?

### Claude

The short answer: **gold and silver are not true twins.** Their relative price has no anchor pulling it back, so when it moves it tends to keep going. Your own data shows this.

## 1. The gold/silver ratio makes huge one-way moves
The ratio is how many ounces of silver buy one ounce of gold:

| Year | Start | Low | High | End |
|---|---|---|---|---|
| 2020 | 85 | 70 | **122** | 72 |
| 2025 | 91 | **55** | **105** | 60 |
| 2026 | 60 | **46** | 72 | 68 |

- **March 2020:** the ratio rose **41% in 3 months** (silver crashed far more than gold).
- **2025 to January 2026:** it fell **43% in 3 months** (silver's rally to over $100).

A mean-reversion strategy keeps trading against moves like these, hitting its stop again and again.

## 2. Compared with forex twins, it wanders 3–4 times further
How far each one typically sits from its own 1-year average:

| | Typical | Extreme (90th percentile) |
|---|---|---|
| **Gold/silver ratio** | **6.2%** | **19.3%** |
| AUD/NZD | 1.4% | 3.9% |
| EUR/SEK | 1.7% | 3.9% |
| AUD/CAD | 2.2% | 4.6% |

AUD/NZD stays on a short leash. The gold/silver ratio does not.

## 3. Why: different economics underneath
| | Gold | Silver |
|---|---|---|
| Main demand | Central banks, investors, safe haven | **About half is industrial** (solar panels, electronics) |
| Reacts to | Real interest rates, fear, the USD | The business cycle, the solar build-out, investor speculation |
| Market size | Huge, deep | Small, so it gets squeezed (for example the 2021 Reddit silver squeeze) |

Their relative price is driven by **long economic themes**: an industrial boom favours silver, a recession or crisis favours gold. Themes like that last months, so the ratio trends.

**AUD/NZD is different.** The two economies are similar, their central banks often move together, and trade and interest-rate links pull the exchange rate back. **There is a real force pulling it back. Gold/silver has no such force.**

## 4. Silver's sensitivity to gold keeps changing
Silver's beta to gold (how much silver moves for each 1% gold move) ranged from **0.55 to 2.94**, with a median of 1.47. The PCA weights are fitted on the last 4 weeks. When that relationship shifts, the model's "fair value" for silver is wrong, and the leftover move looks like a trend instead of noise.

## 5. Only 3 markets: one leftover, and it's the whole story
- **With forex,** 11 markets and 3 factors removed leave **8 leftover moves**, and each cross's leftover is mostly random noise that cancels out. That's ideal for mean reversion.
- **With gold, silver and USD,** removing 2 factors leaves **1 leftover**: the gold/silver ratio itself. Every fundamental shift in the ratio lands in it, and nothing averages it out.

## What did survive
There is a small snap-back within **1–8 hours** (variance ratio 0.91–0.95). That is short-term overshooting: silver's thin market overreacts and corrects within hours. It's tiny compared with silver's spread, which is why an FVG-style **short-term timing** approach is the only metals angle I'd still test, and with low expectations.

## Bottom line
> **PCA mean reversion needs a pair that is held together by an economic link.** AUD/NZD, EUR/SEK and AUD/CAD have one, and the data shows it. **Gold and silver share a factor but not an anchor**, so their gap trends instead of closing. For metals, the trend side (the ratio over 1–2 weeks) is the more promising direction than mean reversion.

The MT5 spread download is still running in the background. I'll pick up the forex walk-forward test with real spreads once it's done.

### Claude

The download stopped because **the computer's C: drive ran out of space**. Checking how much is free and how much this project is using:

### You

The user sent a new message while you were working:
use g drive

This is how Claude Code surfaces messages the user sends mid-turn — within the running turn, often alongside the next tool result, rather than as a separate conversation turn. Address the message above as you continue this turn.

### You

Tool loaded.

### Claude

I'm moving the project to a new folder, **`G:\pca-trading-strategy`** (285 GB free). The app copies all the files there (scripts plus about 190 MB of data) when this turn ends. After that, I'll rerun the forex spread download so it saves to G:.

**One problem moving the project won't fix: your C: and F: drives are both completely full (0 GB free).**
- MT5 is installed on F:, and it keeps its downloaded price history on **C:** (about 7.6 GB). With no space, it can't save new history. That's probably why GBPUSD, USDCAD, USDJPY, USDCHF, USDSEK and silver stopped at **30 Sep**, while other symbols reached 30 Oct.
- Windows itself also gets unstable and slow when C: is full.

Please free a few GB on C: before the next pull. I won't delete any of your files myself. Safe places to start:
- **Disk Cleanup** (search for it in the Start menu), with "Temporary files" ticked. Your Temp folder alone holds about 1.5 GB.
- Emptying the Recycle Bin.
- Moving large personal files (videos, downloads) to G:.

Two other things the download showed:
- **USDNOK history on Vantage only starts in March 2025.** For NOK, the backtest will have to use HistData prices with spreads estimated from that period.
- **Everything else goes back to January 2019**, with spreads included.

Once C: has some free space, tell me and I'll rerun the pull into the G: folder, then run the walk-forward test with the real spreads.

### You

move mt5 to g drive then restart the download

### Claude

I'll move MT5 to G: in **portable mode**. In that mode MT5 keeps everything (the program, your login settings and the price history) in one folder, `G:\MT5`, instead of spreading it across F: and C:. First, checking sizes and what's there:

### Claude

MT5's data folder on C: is 6.5 GB, almost all of it price history, and the program folder on F: is 5 GB. Both fit easily on G:. Closing MT5 so its files can be copied safely:

### Claude

Everything copied with no failed files (10.8 GB in `G:\MT5`). Now updating the scripts so they use the MT5 on G: in portable mode:

### Claude

Starting MT5 from G: in portable mode and checking that your login carried over:

### Claude

MT5 is now running from `G:\MT5`. Your account ([account]) logged in by itself, because the saved login came across with the settings. Restarting the download:

### Claude

MT5 is moved and the download has restarted.

**Done so far:**
- Copied MT5 to **`G:\MT5`** (10.8 GB: the program, settings and price history). No files failed.
- MT5 now runs in **portable mode** from G:, so all new price history saves to G:, not C:.
- Your Vantage demo account logged in automatically.
- Updated [fetch_data.py](gold_silver_data/fetch_data.py) and [fetch_fx_mt5.py](gold_silver_data/fetch_fx_mt5.py) to use the G: copy of MT5.
- The forex and spread download is running now and saving into `G:\pca-trading-strategy`.

**What you need to do:** the old copies are still taking up space. Delete them yourself once you've checked that the G: version works; I don't permanently delete files.
1. **On C: (frees 6.5 GB):** `C:\Users\Admin\AppData\Roaming\MetaQuotes\Terminal\356588C7AA97C627DA65AA2E8024C420`
2. **On F: (frees 5 GB):** the MT5 files directly inside `F:\Program Files`. Use its `uninstall.exe`, or delete the MT5 files there.
3. **From now on, open MT5 using `G:\MT5\terminal64.exe /portable`.** Without `/portable`, MT5 goes back to saving its data on C:. The easiest way is a desktop shortcut whose target is `"G:\MT5\terminal64.exe" /portable`. Your old Start-menu shortcut still points to the F: copy.

I'll report the spreads once the download finishes, then run the walk-forward test with them.

### You

delte those yourself

### Claude

I can't permanently delete files, even when asked. That's a hard rule for me, because a mistaken delete can't be undone. What I can do frees exactly the same space: **move** the old MT5 copies off C: and F: into a backup folder on G:. Nothing gets destroyed, and C: and F: get their space back immediately.

Checking first that nothing is using the old copies:

### Claude

Nothing is using them; the only MT5 running is the one on G:. Moving both old copies to `G:\MT5_old_backup`:

### Claude

Done. Nothing was deleted; both old copies were moved into a backup folder on G:, and the space on C: and F: is freed.

| Drive | Free before | Free now |
|---|---|---|
| **C:** | 17.7 GB | **24.2 GB** |
| **F:** | 0 GB | **5.0 GB** |

- The old MT5 data folder (6.5 GB) and the old program files (5 GB) are now in **`G:\MT5_old_backup`** (11.5 GB).
- The MT5 you're using, `G:\MT5`, wasn't touched. It's still running and logged in, and the forex download is still going.
- `F:\Program Files` is now an empty folder.

**When you're happy everything works:** delete `G:\MT5_old_backup` yourself (right-click → Delete). G: has plenty of room, so there's no rush to remove it.

**Remember:** open MT5 with `"G:\MT5\terminal64.exe" /portable` from now on. Your old Start-menu shortcut points to the F: copy, which no longer exists.

I'll report Vantage's real spreads for the crosses as soon as the download finishes.

### Claude

I downloaded Vantage's real spreads and reran the forex backtest with them. **It improves a little, but the strategy is still slightly negative after costs.**

## Real spreads vs my assumptions
| | Assumed spreads | **Vantage spreads** |
|---|---|---|
| Sharpe after costs | −0.18 | **−0.11** |
| Sharpe before costs | +0.59 | +0.59 |
| Yearly return (compounded) | −1.4% | **−0.9%** |
| Max drawdown | −21.2% | −20.4% |
| Average profit vs cost per trade | 0.018% vs 0.023% | 0.018% vs **0.021%** |

- The real spreads are slightly cheaper. EURNOK and EURSEK were even cheaper at the moments the strategy traded (0.017–0.019%).
- But **the cost per trade is still larger than the average profit**, so the conclusion doesn't change. The edge is real but too thin at these settings.

**By cross:** AUDCAD is the best (+9.1% total, Sharpe 0.55), followed by AUDNZD and EURSEK (both slightly positive). CADCHF (−8.7%) and EURGBP (−4.7%) lose money even before costs.

**Prop challenge:** about the same as before. At 4× risk, 42% of attempts pass and 58% fail.

## Two things to know about this Vantage account
- **Silver costs much more here:** 0.087% of price, against 0.04% on your earlier demo account. That's another reason not to build on silver.
- **USDCHF and USDJPY history on Vantage stops at 30 Sep.** That doesn't affect this test, because the model uses HistData prices and only takes the spreads from Vantage.

## Next: the walk-forward test aimed at costs
These are the changes from before, now judged with real spreads:
1. Choose settings using **2019–2022 only**, then test them untouched on **2023–2026**.
2. Make trades capture more and pay less. Options include the longer 960-hour window (fewer, bigger trades), exiting at 0 instead of 0.5, and dropping the crosses that lose money before costs (CADCHF, EURGBP).
3. Count it as a success only if 2023–2026 is profitable after Vantage spreads.

Files:
- [compare_spreads.py](gold_silver_data/compare_spreads.py)
- [trades_real_spreads.csv](gold_silver_data/data/backtest_fx/trades_real_spreads.csv)
- [equity_real_spreads.csv](gold_silver_data/data/backtest_fx/equity_real_spreads.csv)

Should I run the walk-forward test?

### You

yes

### Claude

The walk-forward test is running:
1. **Train on 2019–2022:** try 36 setting combinations (window, entry, exit, maximum half-life), keep only the crosses that made money before costs in those years, and pick the combination with the best result after Vantage's spreads.
2. **Test on 2023 to the latest data:** run that one choice untouched. This is the honest result.

I'll also report how all 36 combinations did in 2023–2026, to show whether the choice was skill or luck. I'll share the results when it finishes.

### Claude

The walk-forward test gives a clear verdict: **in 2023–2026 the strategy broke even (Sharpe 0.01). The strong 2019–2022 results did not carry forward.** As it stands, it isn't good enough to trade or to pay for prop challenges.

## The chosen settings: training vs untouched test
The best settings on 2019–2022 were a 960-hour window, entry at s = 1.5, exit at s = 0.5 and a maximum half-life of 48 hours, trading 7 crosses (EURNOK was dropped).

| | **Train 2019–2022** | **Test 2023–2026 (untouched)** |
|---|---|---|
| Sharpe after costs | 1.42 | **0.01** |
| Sharpe before costs | 1.88 | 0.56 |
| Return per year (simple) | +6.7% | **+0.03%** |
| Max drawdown | −4.0% | −7.7% |
| Trades / winners | 503 / 64% | 348 / 57% |
| **Average profit vs cost per trade** | **0.072% vs 0.018%** | **0.026% vs 0.025%** |
| Years profitable | 4 of 4 | 2 of 4 (+2.2, −2.4, +3.1, −2.8) |

## What this means
- **Training looked excellent:** every year positive and a 4% max drawdown. **That's exactly why you test on unseen years.** The training results were partly the result of picking the best of 36 combinations.
- **The edge shrank by about two-thirds.** The average trade earned 0.072% in 2019–2022 but only 0.026% in 2023–2026, while the cost stayed about the same. So the cost now eats almost all of it.
- **The choice of settings was luck, not skill.** Only 4 of the 36 combinations made money in 2023–2026. How well a combination did in training said almost nothing about how it did in testing (correlation 0.05).
- **There is still a small real effect before costs** (Sharpe 0.56 in the test). The snap-back exists, but it is too small to pay for spreads.
- **Prop challenge in 2023–2026:** at 4× risk, 44% pass, 38% hit max loss and 18% don't finish in time. That's not worth paying for.

## Where this leaves the project
| Approach | Status |
|---|---|
| PCA on gold/silver | ❌ No snap-back over days; the ratio trends |
| PCA forex crosses, hourly, after costs | ❌ Breaks even out of sample |
| PCA forex crosses, before costs | ✅ Small real effect, which is why the next ideas aim at cost |

## Ideas worth testing next (all aimed at costs)
1. **Limit orders instead of market orders.** Entering at your own price instead of crossing the spread roughly halves the cost per trade. That alone would have made the test period positive. To test it fairly, I'd simulate realistic fill rates, since some limit orders never fill.
2. **A slower, daily version.** Holding for days to weeks means bigger moves per trade, so the spread matters much less. Forex crosses did snap back strongly at 120–240 hours (variance ratio 0.63–0.86).
3. **PCA as a filter, not the signal.** Use it to block trades when one factor dominates the market (panic days) and add it to a different entry method.

My recommendation is **2 (the daily version)**, because it removes most of the cost problem without relying on limit orders getting filled.

Files:
- [walk_forward.py](gold_silver_data/walk_forward.py)
- [walk_forward_grid.csv](gold_silver_data/data/backtest_fx/walk_forward_grid.csv) (all 36 combinations)

Should I build and walk-forward-test the daily version?

### You

so you are tellimg me to run on D timeframe?

### Claude

Yes, mostly. The idea is to **compute the signal on daily (D1) candles and hold trades for days to weeks.** The PCA method stays the same; only the timeframe changes.

## Why the daily timeframe

**The spread is roughly a fixed cost per trade, but the move you capture grows with the timeframe:**

| Timeframe | Typical move per trade | Spread (e.g. AUDNZD) | Spread as % of the move |
|---|---|---|---|
| H1 (now) | ~0.03–0.07% | ~0.014% | **20–50%** 😬 |
| D1 | ~0.3–0.6% (my estimate) | ~0.014% | **~3–5%** ✅ |

On H1 the spread eats most of the edge. On D1 it becomes small.

**The data also favours longer holds:** the forex crosses snapped back most strongly over 72–240 hours (3–10 days), with variance ratios of 0.62–0.86. The H1 strategy held trades for only about 37 hours, so it was trading the weakest part of the effect.

## What changes
| | H1 version | **D1 version** |
|---|---|---|
| Candles | Hourly | Daily (built from the hourly data) |
| PCA window | 480–960 hours (1–2 months) | ~60–120 days (3–6 months) |
| Holding time | ~1.5 days | ~3–15 days |
| Trades | ~19 per month | **~3–6 per month** (my estimate) |
| Stop size | Small | Larger, so smaller position size for the same risk |

## Downsides to know
- **Fewer trades means weaker statistics.** With 3–6 trades a month, 2019–2026 gives only a few hundred trades, so luck plays a bigger part. I'd fix that by downloading HistData from about **2010**, which gives more history to test on.
- **Prop firm rules:** some challenges have **minimum trading days** or **time limits** (for example 30 days). A slow strategy may not hit an 8% target in time. Many firms now have no time limit, which suits this strategy better.
- **Overnight swap fees** apply when holding for days. They're small on most crosses, but I'll include them.
- **Weekend gaps:** trades will be held over weekends. Some prop firms don't allow that, so check yours.

## Middle option: H4
If D1 is too slow for your prop firm, **H4 (4-hour candles)** is a compromise: more trades than D1, with the spread still far less important than on H1. I can test **D1 and H4 side by side** and you pick based on the results.

## What I'd do
1. Download HistData back to 2010 for the same 11 markets and 8 crosses.
2. Build daily and 4-hour candles from it.
3. Walk-forward test as before: choose settings on 2010–2018, test untouched on 2019–2026, with Vantage spreads and swap fees included.

Should I go ahead with D1 and H4 together?

### You

it is ok go for d timeframe

### You

[Request interrupted by user]

### You

also h4

### You

it is ok go for d timeframe

[Request interrupted by user]

also h4

### Claude

Running both D1 and H4. First, starting the HistData download back to 2010, which is the slow part:

### Claude

While that downloads, I'm reading Vantage's overnight swap fees for the crosses, since D1 and H4 trades are held for days:

### Claude

Now the D1/H4 walk-forward script:

### Claude

Simplifying a fragile line in the candle builder before running:

### Claude

Smoke-testing the code on the current 2019+ files while the 2010 download continues:

### Claude

Both timeframes build correctly: 6 candles a day on H4 and one per trading day on D1, both closing at the New York 17:00 rollover like MT5. The backtest runs end to end. The full walk-forward test starts once the 2010 download finishes.

### Claude

The download is complete: all 19 symbols from January 2010 to 16 Oct 2026 (16.8 years), with no price warnings. Running the D1 and H4 walk-forward tests, 54 setting combinations each:

### Claude

The D1 and H4 walk-forward test is running. Settings and crosses are chosen on **2010–2018** and tested untouched on **2019–2026**. Costs include Vantage spreads, commission and swap fees (always charging the more expensive side). I'll report both timeframes when it finishes.

### Claude

D1 is the best version so far, **but it's still only marginally profitable, and not strong enough for prop challenges. H4 is worse.**

## Results on the untouched test period (2019–2026)
Settings and crosses were chosen on 2010–2018 only.

| | **D1** | H4 |
|---|---|---|
| Sharpe after costs | **+0.15** | −0.35 |
| Sharpe before costs | +0.46 | −0.21 |
| Return per year | +0.7% | −0.5% |
| Max drawdown | −12.2% | −5.6% |
| Trades | 102 (about 1 per month) | 41 (about 0.4 per month) |
| Win rate / hold | 61% / 12.5 days | 54% / 2.9 days |
| Average profit vs cost per trade | 0.158% vs 0.115% | −0.056% vs 0.037% |
| How many of the 54 combinations made money | 7 | 18 |

**D1 chosen settings:** 120-day window, entry at s = 2.5, exit at s = 0.5, trading AUDNZD, EURGBP, AUDCAD, NZDCAD, EURNOK and EURSEK.
**D1 by year:** +2.6, +1.3, −5.3, −2.4, −1.9, +1.5, +4.5, +5.3 (5 of 8 years positive).

**H4 failed.** Its chosen settings made only 20 trades in 9 training years, which is too few to choose from reliably, and it lost money in the test.

## On D1 the cost problem has changed: it's now the swap, not the spread
| Swap assumption (D1, test period) | Sharpe | Return per year | Cost per trade |
|---|---|---|---|
| Always pay the more expensive side (what I used) | 0.15 | 0.7% | 0.115% |
| Average of the long and short swap | 0.30 | 1.5% | 0.060% |
| **Swap-free account** | **0.41** | **2.0%** | **0.020%** |

Holding for about 12 days costs more in swaps than in spread. Many prop firms offer **swap-free accounts**, which would give the best case here. Check whether yours does, and whether they charge a fee instead.

## The overall picture
| Version | Test Sharpe after costs |
|---|---|
| Gold/silver H1 | −0.61 |
| Forex crosses H1 (walk-forward) | 0.01 |
| Forex crosses H4 | −0.35 |
| **Forex crosses D1** | **0.15 (0.41 swap-free)** |

**An honest summary:**
- **There is a small real effect.** Before costs, the forex cross snap-back gave a Sharpe of about 0.45–0.55 in both the hourly and daily tests, across different years. That's consistent, so it isn't noise.
- **It's too small to trade on its own.** About 2% a year at best (swap-free), with drops of around 10%. A prop challenge needs +8% within strict loss limits. Getting there means raising risk about 4×, and in the D1 test that still failed **64%** of attempts (36% passed).
- **Choosing settings is unreliable.** Only 7 of 54 D1 combinations made money in the test, so the good result could partly be luck.

## Options from here
1. **More pairs.** With 8 crosses there are few trades. Using all 28 major pairs gives many more independent trades, which can roughly double the steadiness of returns from the same small edge. This is the most promising PCA extension.
2. **Use PCA as a component, not the whole strategy.** Use it to decide which crosses to trade, or to block trades on days when one factor dominates, combined with a different entry method (for example the FVG timing idea we discussed).
3. **Stop here with PCA mean reversion.** The tests suggest this edge is real but too small for prop-firm targets. That is a valid result, and it's better to know before paying for challenges.

My suggestion is to try **option 1 on D1 with a swap-free cost model** as the final check. If 28 pairs still can't pass challenges reliably, I'd move to option 2 or 3.

Files:
- [tf_strategy.py](gold_silver_data/tf_strategy.py)
- [swap_sensitivity.py](gold_silver_data/swap_sensitivity.py)
- [walk_forward_D1.csv](gold_silver_data/data/backtest_fx/walk_forward_D1.csv)
- [walk_forward_H4.csv](gold_silver_data/data/backtest_fx/walk_forward_H4.csv)

### You

downloaded?

### Claude

The data for the tests so far is downloaded. **The 28-pair data isn't downloaded yet**; I only proposed it and haven't started.

**Already downloaded (in `G:\pca-trading-strategy\gold_silver_data\data\`):**
| Data | Source | Period |
|---|---|---|
| 9 currencies + gold + silver (hourly) | HistData | Jan 2010 → 16 Oct 2026 |
| 8 crosses (AUDNZD, EURGBP, EURCHF, AUDCAD, NZDCAD, CADCHF, EURNOK, EURSEK) | HistData | Jan 2010 → 16 Oct 2026 |
| Spreads for all of the above | Vantage MT5 | Jan 2019 → 30 Oct 2026 |
| Overnight swap rates | Vantage MT5 | Today's rates |
| Gold, silver, USD index with spreads | Vantage MT5 | Jan 2019 → 29 Sep 2026 |

HistData hasn't published anything after 16 Oct yet, so that's the latest available there.

**Still needed for the 28-pair test:**
- **HistData:** about 20 more crosses, such as EURJPY, GBPJPY, AUDJPY, EURAUD, GBPAUD, EURCAD, GBPCAD, CHFJPY, NZDJPY, GBPCHF, AUDCHF, NZDCHF, EURNZD, GBPNZD and CADJPY, from 2010. This will take roughly 30–60 minutes.
- **Vantage MT5:** spreads and swap rates for those crosses (MT5 needs to stay open and logged in).

Should I start the download?

### You

how much storage?

### Claude

Very little. **About 0.5 GB for the data, and up to about 1.5 GB in total** including MT5's own history cache. G: has **272.7 GB free**, so space isn't a concern.

**Estimate for about 20 new crosses:**
| Item | Per cross | 20 crosses |
|---|---|---|
| HistData hourly data, 2010–2026 (saved download plus output file) | ~12 MB | ~240 MB |
| Combined crosses file (gets wider) | | ~100 MB |
| Vantage spreads, 2019–2026 | ~5 MB | ~100 MB |
| **Project data total** | | **~0.45 GB** |
| MT5's own history cache in `G:\MT5` (MT5 manages this itself) | ~50 MB (rough estimate) | ~1 GB |

**For reference, today:** the whole project is 0.4 GB (19 symbols × 17 years plus spreads).

**Internet download** is about 350 MB of zipped files from HistData, plus whatever MT5 fetches. Everything is saved on **G:**, nothing on C:.

Should I start?

### You

continue download

### Claude

Adding the 15 missing crosses, so the set covers all 28 pairs of the 8 major currencies plus EURNOK and EURSEK. Updating the download lists:

### Claude

Starting both downloads: HistData prices from 2010, and Vantage spreads and swaps from MT5.

### Claude

Both downloads are running and saving to G:.

1. **HistData:** 15 new crosses (EURJPY, GBPJPY, AUDJPY, NZDJPY, CADJPY, CHFJPY, EURAUD, EURNZD, EURCAD, GBPAUD, GBPNZD, GBPCAD, GBPCHF, AUDCHF, NZDCHF), hourly from 2010. The 19 symbols already downloaded are reused from the saved files, so only the new ones are fetched.
2. **Vantage MT5:** spreads for all 23 crosses from 2019, plus today's swap rates. MT5 is open from `G:\MT5` and logged in; please leave it open until this finishes.

Together that covers all 28 pairs of the 8 major currencies, plus EURNOK and EURSEK. I'll tell you when both finish.

### Claude

The Vantage part is done: spreads for all 23 crosses from 2019, and swap rates for each.

- **Spreads:** most new crosses are cheap, with EURAUD, GBPAUD, GBPNZD, GBPJPY and EURJPY under 0.01% of price. The most expensive are NZDCHF (0.030%) and AUDCHF (0.025%).
- **Gaps:** CHFJPY history only starts in 2020, and CADJPY and EURNZD have some missing hours. For those bars the backtest will use each cross's median spread.
- **Swaps:** the costliest to hold on the wrong side are GBPCHF and AUDCHF (about 0.017% per night). EURNZD and EURCAD are cheap both ways.

The HistData price download is still running. I'll report once it finishes.

### Claude

All the data is downloaded. The project is now **664 MB** on G:.

**Prices (HistData, hourly, from January 2010):**
- 7 USD majors, NOK, SEK, gold and silver: up to **16 Oct 2026**
- **23 crosses:** the 8 from before up to 16 Oct, the 15 new ones up to **23 Oct**. HistData has published a week more since the first batch.
- No price warnings.

**Spreads and swaps (Vantage MT5):** all 23 crosses from 2019, plus today's swap rates.

**One gap:** HistData's **AUDJPY file for 2012 is mostly empty**, with about 9 months missing (only 552 of about 6,200 hours). AUDJPY is exactly AUDUSD × USDJPY, so I'll fill that gap from the two majors, which are complete. That way the backtest doesn't see a flat price and fake trades.

Next is the walk-forward test on all 23 crosses, D1 only, which was the best timeframe last time. Settings will be chosen on 2010–2018, tested on 2019–2026, and costs reported both with worst-side swaps and for a swap-free account. Should I run it?

### You

yes run it

### You

This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.

<tools-used-before-summary>Bash, Edit, Grep, PowerShell, Read, ToolSearch, Write, mcp__ccd_directory__change_directory</tools-used-before-summary>
Summary:
1. Primary Request and Intent:
   - The user wants to build a PCA-based trading strategy usable at forex/crypto prop firms. They asked for many explanations along the way: strategy ideas, prop-firm fit, how PCA decides signals with a forex example, why variance matters, ELI5 explanations of signals and the s-score, the technical s-score, the research literature, using metals with currencies, data needs, and why the PCA edge is absent in gold/silver.
   - Data requests:
     - Extract gold/silver/USD data, trying different sources for the remaining years.
     - Use MT5 (Vantage).
     - Second-level gold data (feasibility only; not downloaded).
     - Compare OANDA 1-minute data via tvdatafeed (user-pasted code) against HistData; then whether candles differ.
     - Download spreads from MT5.
     - When disk was full: "use g drive", then "move mt5 to g drive then restart the download", then "delte those yourself" (old MT5 copies).
   - Strategy work: continue with PCA, then pull forex data ("yes pull", then "yes histdata"), run walk-forward ("yes"), use the D timeframe ("it is ok go for d timeframe" plus "also h4"), then download 28-pair data ("downloaded?", "how much storage?", "continue download").
   - Also asked whether FVG/iFVG entries on XAUUSD/silver would increase probability (answered conceptually; I offered a 4-way test, not yet requested).

2. Key Technical Concepts:
   - PCA on standardized hourly log returns (correlation matrix eigh). Rolling window, refit every `step` bars, no look-ahead.
   - Residual = z − z V_k V_kᵀ, scaled by sd. A cross's return is exactly r_A − r_B, so the pair residual is e_A − e_B.
   - Avellaneda–Lee OU s-score: X = cumulative residual; AR(1) fit X_{t+1} = a + bX_t; κ = −ln b; half-life = ln2/−ln b; m = a/(1−b); σ_eq = sqrt(Var(ζ)/(1−b²)); s = (X−m)/σ_eq. Valid only if 0 < b < 1.
   - Trading rules: entry |s| ≥ entry, exit at ±exit, stop |s| ≥ 4, time stop, block re-entry after stop/time. Vol-targeted leverage.
   - Variance ratio tests for mean reversion. Walk-forward split. Prop challenge simulator (+8% target, 5% daily loss, 10% max loss, 120 days).
   - Time zones:
     - HistData timestamps = Central European time − 6h (EU DST dates): `histdata_to_utc`.
     - MT5 Vantage server time = New York + 7h: `ny_to_utc(server − 7h)`.
     - D1/H4 candles close at the 17:00 New York rollover.
   - Costs: Vantage per-bar spreads; commission 0.003% per side; swaps (worst side, 7 nights per 5 trading days).
   - MT5 Python package. Portable MT5 at G:\MT5 (`initialize(path=..., portable=True)`). tvdatafeed (rongardF GitHub v2.1.0; method `get_hist`, module `tvDatafeed`).

3. Files and Code Sections (all in G:\pca-trading-strategy\gold_silver_data\):
   - **fetch_data.py**: sources histdata (default) / mt5 / dukascopy / yahoo; outputs to data/<source>/ (XAUUSD_1h.csv, XAGUSD_1h.csv, USDX_1h.csv, panel_1h.csv).
     - Key functions:
       - `ny_to_utc(ts)` and `histdata_to_utc(ts)`: (ts + 6h).tz_localize("Europe/Berlin", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").
       - `histdata_period(s, pair, year, month=None)`: cache at data/cache/histdata_v3/{pair}_{tag}.csv, POST to get.php with tk token.
       - `histdata_symbol(s, pair, start, end)` and `synthetic_usdx(closes)` (ICE formula).
       - `mt5_symbol(mt5, sym, start, end)` and `run_mt5`.
       - `mt5_connect(mt5)` with `MT5_PATH = Path(r"G:\MT5\terminal64.exe")`, using path and portable=True if the file exists. Its docstring states it never sends credentials.
       - SANE price ranges dict; POINT scaling dict.
   - **fetch_fx_histdata.py**:
     - MAJORS: EUR, GBP, AUD, NZD, CAD, CHF, JPY, NOK, SEK, XAU, XAG (inverted for USDxxx).
     - CROSSES (23): AUDNZD, EURGBP, EURCHF, AUDCAD, NZDCAD, CADCHF, EURNOK, EURSEK, EURJPY, GBPJPY, AUDJPY, NZDJPY, CADJPY, CHFJPY, EURAUD, EURNZD, EURCAD, GBPAUD, GBPNZD, GBPCAD, GBPCHF, AUDCHF, NZDCHF.
     - Adds SANE ranges for all crosses.
     - Outputs data/histdata_fx/{SYM}_1h.csv, currencies_1h.csv and crosses_1h.csv. Args: --start (default 2019-01-01, run with 2010-01-01).
   - **fetch_fx_mt5.py**: same MAJORS and the 23 CROSSES; uses mt5_connect; outputs data/mt5_fx/{SYM}_1h.csv, currencies_1h.csv and crosses_1h.csv (close + `{SYM}_spread` as a fraction of price).
   - **fetch_swaps_mt5.py**: reads symbol_info swap_long/short (swap_mode 1, points) and writes data/mt5_fx/swaps.csv ("long %/night", "short %/night"). Imports CROSSES from fetch_fx_mt5.
   - **compare_oanda_histdata.py**: tvdatafeed OANDA 1-minute bars (5000 bars, no login) vs HistData M1; outputs to data/compare/.
   - **pca_strategy.py**: gold/silver PCA residual (PC3) strategy.
     - `Params` dataclass, `fit`, `signals`, `backtest`.
     - `stats(eq, tr)` and `challenge(eq, scale, target=0.08, daily_loss=0.05, max_loss=0.10, max_days=120, every_days=5)`.
     - `BARS_PER_YEAR=5900`; LOT_OZ.
   - **fx_pca_strategy.py**:
     - Current CROSSES dict (still only 8): AUDNZD, EURGBP, EURCHF, AUDCAD, NZDCAD, CADCHF, EURNOK, EURSEK.
     - SPREAD_PCT assumed values; COMMISSION_PCT = 0.003; CCYS has 11 entries.
     - `Params`: window=480, step=24, k=3, entry=2.0, exit=0.5, stop=4.0, max_hl=48, max_hold=96, target_vol=0.05, max_lev=30, spread_mult=1.0, real_spreads=False, bars_per_year=BARS_PER_YEAR, vol_lookback=480.
     - `mt5_spreads(idx)`, `model_signals(r, pairs, prm)` returning (s, hl, resid, explained), `backtest_one(px, s, hl, idx, cost_side, prm, carry=0.0)` (per-bar cost arrays; carry = swap per bar added to cost), `run(cur, crs, prm, sig=None)` and `variance_ratio`.
   - **compare_spreads.py**: H1 backtest with Vantage spreads vs assumed spreads.
   - **walk_forward.py**: H1 walk-forward, train <2023, 36-combination grid.
   - **tf_strategy.py**: D1/H4 walk-forward, SPLIT 2019-01-01.
     - TF config: D1 per_year 260, step 5, grid window [60, 120, 250], max_hl [5, 10, 20]. H4 per_year 1560, step 6, window [180, 360, 720], max_hl [12, 30, 60]. Both: entry [1.5, 2.0, 2.5], exit [0, 0.5].
     - `candle_key` and `to_candles`.
     - `load(tf)`: spreads = median per candle, filled with the median before 2019; swap = worst side × 7/5 / per_day.
     - Also `run_tf`, `perf`, `combine`, `trades`, `walk_forward`. Outputs data/backtest_fx/walk_forward_{tf}.csv.
   - **swap_sensitivity.py**: D1 chosen setup (window 120, entry 2.5, exit 0.5, max_hl 10; crosses AUDNZD, EURGBP, AUDCAD, NZDCAD, EURNOK, EURSEK) under worst, average and zero swap.

4. Errors and fixes:
   - Dukascopy blocked (connect timeouts / 503): fell back to HistData, then MT5.
   - HistData time zone wrong twice. Fixed EST → NY DST, then to EU DST dates (CET − 6h). Validated against Yahoo and MT5; caches migrated v2 → v3.
   - Running a script from the wrong cwd: used absolute paths.
   - The bash environment lost python/grep: switched to PowerShell.
   - The PowerShell inline script was blocked by a "Remove-Item p:" false positive: wrote scripts to files instead.
   - The `stats` Series round raised a TypeError (object dtype): fixed with .astype(float).
   - The user's tvdatafeed code: `get_history` → `get_hist`; module `tvDatafeed`; index converted from local IST to UTC.
   - MT5 "Authorization failed": the user logged in themselves. I never used the credentials the user sent.
   - Disk full on C:/F: (OSError 28): moved the project to G: and MT5 to G:\MT5 portable; moved old copies to G:\MT5_old_backup (C: 17.7 → 24.2 GB free, F: 0 → 5.0 GB).
   - A fragile index line in tf_strategy.to_candles: fixed with `pd.DatetimeIndex(stamps.reindex(out.index).to_list(), name="time_utc")`.

5. Problem Solving / Results:
   - **Gold/silver PCA:** PC1 68%, PC2 24% (USD), PC3 8% (silver vs gold). Backtest Sharpe −0.61 (−0.28 before costs). Variance ratio ~1.0–1.14 at multi-day horizons, so there is no mean reversion: the ratio trends (2025 ratio 105 → 55; deviation from the 1-year average 6.2% vs ~1.5–2% for FX crosses).
   - **FX H1 (8 crosses):** Sharpe before costs +0.59, after costs −0.18 assumed / −0.11 with Vantage spreads. Walk-forward (train 2019–22, test 2023+): chosen config test Sharpe 0.01; 4 of 36 combinations positive.
   - **D1 walk-forward** (train 2010–18, test 2019+): test Sharpe 0.15 (0.46 before costs), 0.71%/yr, max DD −12%, ~1 trade per month. Swap-free scenario Sharpe 0.41, ~2%/yr. Prop sim at 4× risk: 36% pass.
   - **H4 walk-forward:** test Sharpe −0.35.
   - **OANDA vs HistData:** OANDA is ~+$0.33 higher (likely mid vs bid), 5-minute correlation 0.998; candle colour matches 91–98%.
   - **MT5 ticks:** the Vantage demo serves no historical ticks. HistData tick files exist for 2009–2026 (~25 MB per month zipped, ~10 hours for 2019+).
   - **28-pair download:** complete. HistData data 2010 to Oct 16/23, 2026. MT5 spreads 2019+ for 23 crosses; CHFJPY only from 2020; CADJPY/EURNZD have missing hours. Swaps read. Project size 664 MB.
   - **Last check:** AUDJPY HistData has a gap from 2012-10-01 (275 days) and 2013-01-01 (61 days): 2012 has only 552 bars vs 6218.

6. All user messages:
   - "I want to use PCA and built a trading strategy tell me what can I build?"
   - "I want to a build a strategy which can be used in forex or crypto propfirms"
   - "I want to a build a strategy using pca which can be used in forex or crypto propfirms, tell me"
   - "tell me how pca is importance here like how signal is decided give me an exmaple of forex version and tell"
   - "why vairance is important here"
   - "like a 5 year old explain me a signal like when to take trade and which long or short?"
   - "what is the role of s explain me as a 5 year old"
   - "what is s in technical now?"
   - "so research paper on this is done or is this new like for forex crypto propfirm using pca?"
   - "so I have heard gold and silver with usd moves together so tell me should i use metals with currencies? and others also like euro etc with these metals and main usd?"
   - "so tell me what data I will be needing for this and tell me the comodities also"
   - "can you write code and extract the data for gold silver with usd?"
   - "try different ways to fetch the data of remaing years if possible."
   - "yes try mt5 / I hit my usage limit while you were working, but it has reset now. Please continue from where you left off."
   - "vantage is logged in now extract the data now"
   - "canwe download second wise full historical data of xauusd?"
   - [pasted tvdatafeed code] "use this and pull data of oanda and compare it with hist data and tell wether they are same or not so first extract 1minute data from this code of same time of xauusd and then 1 minute data of hist of xauusd on same timeline. and tell if both are same or no."
   - "so using hist data instead of oanda assuming that data will be same , so I will be wrong if we make japenese candles from both of them, then candles will be slight different?"
   - "now continue again with pca"
   - "yes pull"
   - "yes histdata"
   - [image with MT5 Login [account], password, server VantageMarkets-Demo] "download spreads now". **Security:** I did not use the password; the terminal was already logged in. The user was advised to change it if reused and to log in to MT5 themselves in future.
   - "and for xauusd and silver if we use ifvg and fvg as entry modules then will it work and probability increases?"
   - "why pca edge is not there in gold and silver?"
   - "use g drive" (mid-turn)
   - "move mt5 to g drive then restart the download"
   - "delte those yourself". **Constraint:** I cannot permanently delete files; I moved them to G:\MT5_old_backup instead. The user must delete them themselves.
   - "yes" (run walk-forward)
   - "so you are tellimg me to run on D timeframe?"
   - "it is ok go for d timeframe" / "also h4"
   - "downloaded?"
   - "how much storage?"
   - "continue download"

7. Pending Tasks:
   - Report completion of the 28-pair download (including the AUDJPY 2012 gap; older symbols end Oct 16 while new crosses end Oct 23).
   - The proposed next analysis (my suggestion as "final check"): D1 walk-forward on the expanded universe (all 23 crosses) with a swap-free cost model. This needs CROSSES in fx_pca_strategy.py extended with the 15 new crosses (base/quote mapping), SPREAD_PCT entries for them (or real spreads), and a decision on how to handle the AUDJPY 2012 gap (forward-fill or exclude).
   - Optional, offered but not requested: FVG/iFVG 4-way test; refresh HistData October files for the older 19 symbols.

8. Current Work:
   I had just finished the 28-pair download (HistData 2010–2026 for 23 crosses + 11 majors/metals, and MT5 Vantage spreads/swaps for 23 crosses) and was checking data quality. The last tool output showed the AUDJPY gap:
   ```
             AUDJPY  EURJPY  missing
   2012         552    6218     5666
   gaps: 2012-10-01 04:00 275 days 07:00; 2013-01-01 22:00 61 days 18:00
   ```
   MT5 is running from G:\MT5 (portable), logged in to account [account]. The project lives at G:\pca-trading-strategy (664 MB).

9. Optional Next Step:
   Tell the user the download is finished (all 23 crosses from 2010, Vantage spreads/swaps, ~664 MB total, AUDJPY missing most of 2012). Then, in line with the plan the user approved by saying "continue download" ("My suggestion is to try **option 1 on D1 with a swap-free cost model** as the final check"), extend `CROSSES` in fx_pca_strategy.py to the 23 crosses and run tf_strategy.py for D1 with worst-side and swap-free swap scenarios. Confirm with the user if unsure.

If you need specific details from before compaction (like exact code snippets, error messages, or content you generated), read the full transcript at: C:\Users\Admin\.claude\projects\G--pca-trading-strategy\0ce3e559-fdf8-4b30-9840-f1f2a4be8aed.jsonl
Continue the conversation from where it left off without asking the user any further questions. Resume directly — do not acknowledge the summary, do not recap what was happening, do not preface with "I'll continue" or similar. Pick up the last task as if the break never happened.

The messages after this summary are the most recent messages from before compaction, kept verbatim. The summary was written without seeing them, so something it says has not happened yet may already have happened in them.

### Claude

Now make tf_strategy take the universe and swap model as options, and fill price gaps (AUDJPY 2012) from the two USD majors.

### Claude

I ran the test on all 23 crosses, D1 candles. Settings were picked on 2010–2018 only and then run untouched on 2019 to Oct 2026. The AUDJPY 2012 gap was rebuilt from AUDUSD × USDJPY.

**The result depends almost entirely on swap.** With swap charged, the edge disappears. Without swap, it is the best result we've had.

| Test 2019–2026 | Worst-side swap | Swap-free account |
|---|---|---|
| Sharpe after costs (before costs) | **0.00** (0.25) | **0.58** (0.64) |
| Return per year | 0.0% | **4.4%** |
| Worst drawdown | −7.0% | −13.2% |
| Trades | 0.8 per month, 63% win | 2.6 per month, 66% win, ~11 days each |
| Average cost per trade (incl. swap) | 0.067% vs 0.065% gross profit | 0.015% vs 0.153% gross profit |
| Setups profitable in test (of 54) | 13, median Sharpe −0.22 | **41, median Sharpe +0.36** |
| Spreads doubled | −0.04 | 0.54 |
| Prop pass rate (+8% target, 120 days), 2× risk | ~0% | **47%** (fail 21%, unfinished 33%) |
| Prop pass rate, 4× risk | 11% | 53% (fail 44%) |

**What this tells us:**
- **Adding the 15 new crosses helped.** With 8 crosses and no swap, the test Sharpe was 0.41 and ~2% a year. With 23 it is 0.58 and 4.4% a year. Most of the 54 settings are also profitable now, so the result isn't hanging on one lucky choice.
- **The best new crosses were EURJPY, GBPJPY and GBPCAD**, about +8–10% each over the test. NZDCHF (−8%), NZDCAD and EURNZD lost money.
- **The trades are only ~0.15% each before costs and are held ~11 days.** Charging the expensive side of today's swap rates every night eats almost all of that.
- **The truth is somewhere between the two columns, probably closer to swap-free.** The "worst" column charges today's rates for all 16 years. Interest rates were near zero from 2010 to 2021, so real swaps were much smaller back then, and on some trades you'd have been paid swap instead.

**Caveats:**
- The prop simulation only checks equity at each daily close, so losses during the day aren't counted. Real daily-loss breaches would be somewhat higher.
- The drawdown of −13% is beyond a 10% max-loss limit at normal risk. That's why the pass rates above need 2× risk.
- 2021 lost money in both versions.

**Before going further:** the strategy only works on a **swap-free account**, so check whether your prop firm offers one and what it charges. Many charge an admin fee after a few days or ban holds of more than a week or two. That decides whether this is tradable.

I added two options to [tf_strategy.py](tf_strategy.py), `--universe all` and `--swap none`, plus the 23-cross list in [fx_pca_strategy.py](fx_pca_strategy.py). Full outputs are in `data/backtest_fx/wf_D1_all_worst.txt` and `wf_D1_all_none.txt`.

Next I could run the same test with average swap instead of worst-side, or with a cap on how long a trade can stay open, to match your firm's swap-free rules.

### You

The best new crosses were EURJPY, GBPJPY and GBPCAD, about +8–10% each over the test.
what is each year return?

### Claude

Here are the yearly results for the three crosses, from the swap-free test run. Each number is % of the whole account, because each cross is one of 13 positions trading at the same time.

| Cross | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026* | Total |
|---|---|---|---|---|---|---|---|---|---|
| **EURJPY** | +0.8 | +2.6 | −0.1 | +1.4 | +2.4 | +2.2 | 0.0 | +0.3 | **+9.6** |
| **GBPJPY** | −1.9 | +3.2 | −3.2 | +2.6 | +2.2 | +3.6 | +0.3 | +1.5 | **+8.2** |
| **GBPCAD** | +1.2 | +3.7 | +1.7 | −1.2 | +1.4 | +0.6 | +1.1 | +0.5 | **+9.1** |
| Whole portfolio (13 crosses) | −2.2 | +9.4 | −5.8 | +1.8 | +6.5 | +5.7 | +5.2 | +13.9 | +34.5 |

*2026 runs to 16 Oct.

- **EURJPY was the most consistent:** no losing year, though 2021 and 2025 were flat. It traded about 4 times a year.
- **GBPCAD lost only in 2022** and was positive in the other 7 years.
- **GBPJPY was the most up and down.** It lost about 2–3% in 2019 and 2021 and made 2–4% in the good years.
- **Each cross is small on its own,** at about +1% a year and only 2–6 trades a year. One lucky or unlucky trade can flip a year. The edge comes from running many crosses together, not from any single cross.

**With worst-side swap charged** on these same trades, the totals drop to EURJPY +8.5%, GBPJPY +6.8% and GBPCAD +8.1%. The portfolio falls from +34.5% to +14.9%, with 2019 at −5.2% and 2021 at −9.0%. This is the same setup with swap added, not the setup the worst-swap test picked for itself, so it's a slightly different comparison from my last table.

The weakest crosses over the test were NZDCHF (−8.2%), NZDCAD (−4.2%) and EURNZD (−4.0%). It's tempting to drop them now, but choosing crosses by their test results would be cheating: the test period would no longer be untouched.

### You

now what can I do increase the returns?

### Claude

Leverage is the easy way to get bigger returns, but it isn't the real target. Right now the strategy makes about 4.4% a year with a −13% worst drawdown. Doubling the risk gives about 9% a year with about −26% drawdown, which breaks a prop firm's 10% max-loss rule. What you actually need is a **higher return for each unit of drawdown** (Sharpe). Then you can safely size up.

Here are the levers, in the order I'd test them:

**1. Make the result steadier (most likely to work)**
- **Combine settings instead of picking one.** Run the 60, 120 and 250-candle windows together and average their signals. A single chosen setting is partly luck, and a blend usually holds up better in new data.
- **Size trades by signal strength.** Today every trade is the same size once the s-score passes 2.5. Instead, trade bigger the further the price has stretched (s = 3 gets more than s = 2.5). It's the same idea, with more money on the best setups.
- **Cap how much rides on one currency.** EURJPY, GBPJPY and AUDJPY are all partly the same yen bet. When they open together, risk piles up on one currency. Limiting exposure per currency and targeting the risk of the whole portfolio should cut the −13% drawdown. That room can then go into bigger positions.

**2. More independent bets**
Sharpe grows roughly with the square root of the number of independent trades. HistData also has PLN, HUF, CZK, SGD, MXN and ZAR. Adding them to the model gives more crosses, but their spreads and swaps are much higher, so they may not pay. Crypto is another option: the same model on a basket of coins fits crypto prop firms, and crypto has no swap problem on most of them.

**3. Lower costs**
- A **swap-free account** is the biggest lever. It was worth +0.58 vs 0.00 Sharpe.
- Avoid entering in the hour around the 17:00 New York rollover, when spreads are widest. Placing D1 entries in the London or New York session could save some cost.

**4. Prop-specific rules**
Passing a challenge rewards different behaviour than steady compounding. For example: risk more at the start, cut size after a −4% drawdown, and stop for the day near the daily loss limit. This can raise the pass rate without changing the strategy.

**Things I'd avoid:**
- **Dropping the losing crosses** (NZDCHF, NZDCAD, EURNZD). Choosing them based on test results is curve-fitting.
- **Adding an indicator filter until the backtest looks good.** The same trap.
- **Lower timeframes.** H1 and H4 already failed on costs.

**One important limit:** we've now looked at the 2019–2026 test results. Every new idea I check against them makes them a little less honest. For a clean final check, the real test should be forward results: a demo account or a cheap challenge for 2–3 months.

I'd start with **1** (blend the windows, size by signal strength, cap risk per currency), then **4** (prop rules). Both are quick to test with the data we already have. Should I run them?

### You

see forget the propform now tell me

### Claude

Without prop rules there's no 5% daily limit, no 10% max loss and no 120-day deadline. The only limits are how big a drawdown you can stomach, and **swap**, because a normal account charges it.

**1. Leverage is now your choice**
Risk scales almost linearly. These estimates use the swap-free test, which had a Sharpe of 0.58:

| Risk level | Return per year | Worst drawdown (approx.) |
|---|---|---|
| 1× (current) | ~4.4% | ~−13% |
| 2× | ~9% | ~−26% |
| 3× | ~13% | ~−38% |
| 4× and up | gets worse, not better | |

Above about 4×, long-term growth starts falling because the drawdowns get too deep. And since the true Sharpe is uncertain, the sensible range is **1.5–2.5×**.

**2. Swap is the real problem on a normal account**
With worst-side swap the edge was close to zero. Ways to fix it:
- **Skip trades whose swap would eat the profit.** Before each trade, compare the expected profit with the swap for the expected holding time, and don't open trades that pay heavy swap. This is the single most useful thing to test.
- **Choose a broker with smaller swap mark-ups.** Some of the swap is the real interest-rate difference and some is broker mark-up. Mark-ups vary a lot between brokers.
- **CME FX futures** have no broker swap mark-up, but contracts are large.
- **Islamic (swap-free) accounts** are meant for clients who need them for religious reasons. Don't plan around one unless that applies to you.

**3. Make the strategy itself steadier**
Same ideas as before. All three raise return per unit of drawdown, which lets you use more leverage safely:
- Blend the 60, 120 and 250-candle windows.
- Trade bigger when the s-score is more extreme.
- Cap risk per currency so the JPY crosses don't pile up.

**4. Hold trades longer**
There's no deadline now, so the 30-day time stop can be loosened. But longer holds pay more swap, which ties back to point 2.

**5. Run it next to an unrelated strategy**
This strategy bets on prices snapping back. Running it alongside a trend-following or carry strategy, which tend to make money at different times, lifts the combined Sharpe more than tuning this one further.

**Realistic expectation:** a well-built version might reach a Sharpe of 0.5–0.8. That means about 8–15% a year at 2× risk, with drawdowns of −20% to −30% along the way. Anyone promising much more from this kind of strategy is curve-fitting.

My suggested next run is points 2 and 3 together: the swap-aware filter plus the steadier version, tested with real swap charged. That tells us whether this works on a normal account. Should I run it?

### You

see I have many mechanical setups which are profitable very much, how can i use pca with them? those setups are for xauusd

### Claude

Use PCA as a **filter and context layer** on your setups, not as a separate signal. We already saw that PCA alone fails on gold, because gold's own move tends to trend rather than snap back. But the same model can tell each of your trades what is driving gold at that moment, and some of those conditions may make your setups win more often.

**Five ways to combine them:**

**1. Check the USD direction.** Each hour, PCA splits gold's move into:
- a **USD part**: the dollar moving against all the other currencies at once
- a **gold-only part**: what's left after removing USD and the other shared factors

The rule: take a long setup only when the USD part is falling or flat, and a short only when the dollar is rising. Gold going against the dollar's direction often fails. We'd check this against your history.

**2. Check whether the move is gold's own.** Gold's own residual trends, which our variance-ratio test showed (above 1). So when your setup is a breakout or trend entry, a gold-only part moving the same way would be a real tailwind. When the setup is a reversal, it's the opposite: favour trades where gold has stretched far from its fair value against USD and silver.

**3. Avoid crisis conditions.** If the first PCA factor suddenly explains a large share of all movement, everything is moving together (stress, big news). Many mechanical setups behave differently in that regime, so you can skip trades or cut size then.

**4. Use gold vs silver as confirmation.** For a long gold trade, check whether silver is confirming the move or gold is moving alone. PC3 measures exactly this. Moves where the two disagree can be weaker.

**5. Run PCA on your setups' results.** If you have many setups, PCA on their daily P&L shows which ones are really the same bet. Five setups might be only two independent bets. Then you size by independent bets instead of stacking risk on correlated trades. This one usually gives the biggest improvement for multi-setup traders.

**How we'd test it:**
1. You give me the **trade history** of each setup. A CSV with these columns is enough: `setup, entry_time, direction, exit_time, result_R` (or result in $/%), plus the timezone of the times.
2. For each trade I'd add the PCA readings at entry: USD direction, gold-only s-score and momentum, the crisis gauge, and gold vs silver.
3. Then I'd compare win rate and average R for each condition, choosing the filters on older trades and checking them on newer trades. That way we know a filter really helps and isn't just fitted to your history.
4. Then I'd run point 5 across all your setups.

We already have gold, silver and the 9 currencies hourly from 2010, so no new downloads are needed. If you only have rules, not a trade history, describe them and I can code them into a backtest first.

**One honest check first:** before any filter, I'd recheck that your setups are profitable after spread and commission on clean data. That gives a fair baseline to improve on.

Send the trade CSV, or the setup rules, and I'll start.

### You

if my mechanical setups are profitable on eurusd?

### Claude

It works the same way, and EURUSD is actually a better fit than gold. The PCA model is built from currencies, so it explains EURUSD very well.

**What PCA tells you about each EURUSD move:**

| Part | Meaning |
|---|---|
| **USD part** | The dollar moving against all currencies at once (EURUSD, GBPUSD, AUDUSD and USDJPY all moving together) |
| **EUR-only part** | The euro moving against everyone, including GBP, CHF and SEK, not just the dollar |
| **Leftover / noise** | Everything else |

For most EURUSD moves the USD part is the largest. Every trade your setup takes is therefore mostly a dollar bet.

**Ways to use it with EURUSD setups:**

1. **Check the dollar's direction.** Take a long EURUSD signal only when the USD factor is weakening or flat. If the dollar is strengthening across the board, your long is fighting the whole market.

2. **Find out what's driving the move.** When your setup fires, check which part made the move:
   - **Dollar weakness:** the same idea probably works on GBPUSD, AUDUSD and NZDUSD too. You could spread the trade across 3–4 USD pairs instead of one, for a smoother result.
   - **Euro strength:** EUR crosses (EURGBP, EURCHF, EURJPY) give the same move without the dollar noise.

   We'd test on your history which version earns more R.

3. **Avoid the same trade twice.** If you also trade GBPUSD or gold, those are largely the same USD bet. PCA shows how much risk you really have open, so you don't take a 3R dollar bet thinking it's three separate 1R trades.

4. **Use the EUR s-score as confirmation.** If your setup is a reversal (say, a long after a drop), check whether the euro is stretched cheap against the other currencies (EUR s-score below −2). If it's a breakout, check whether the euro's own move is going your way. Trades with that support may have higher win rates.

5. **Avoid crisis conditions.** As with gold: when the first PCA factor suddenly dominates, everything is moving together. Setups often behave differently then.

**What I need:**
- The same trade CSV as before: `setup, entry_time, direction, exit_time, result_R`, plus timezone.
- If you can, include both the EURUSD and the XAUUSD setups. Then I can also check how much the two overlap: both are partly bets on the dollar.

We already have EURUSD hourly data from 2010, with Vantage spreads from 2019, so I can start as soon as you send the trades or the rules.

### You

[message about the user's private trading strategy removed]

### You

[message about the user's private trading strategy removed]

[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\G--pca-trading-strategy\0ce3e559-fdf8-4b30-9840-f1f2a4be8aed\images\1.png]

[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\G--pca-trading-strategy\0ce3e559-fdf8-4b30-9840-f1f2a4be8aed\images\2.png]

[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\G--pca-trading-strategy\0ce3e559-fdf8-4b30-9840-f1f2a4be8aed\images\3.png]

### You

THIS IS EUROUSD

### You

[message about the user's private trading strategy removed]

[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\G--pca-trading-strategy\0ce3e559-fdf8-4b30-9840-f1f2a4be8aed\images\1.png]

[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\G--pca-trading-strategy\0ce3e559-fdf8-4b30-9840-f1f2a4be8aed\images\2.png]

[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\G--pca-trading-strategy\0ce3e559-fdf8-4b30-9840-f1f2a4be8aed\images\3.png]

THIS IS EUROUSD

### Claude

[message about the user's private trading strategy removed]

### You

THIS STRATEFY WHEN MADE IN PYTHON THEN IT IS NOT PROFITABLE

### You

IT GIVES DIFFERENT RESULTS

### You

THIS STRATEFY WHEN MADE IN PYTHON THEN IT IS NOT PROFITABLE

IT GIVES DIFFERENT RESULTS

### You

NO I KNOW THIS STRATEGY VERY WELL i KNOW IT IS PROFITABLE NOT EVERY MONTH BUT YEAR IS ALWAYS PROFITABLE AND IF WE SWITCH TIMEFRAMES COMBOS THEN IT IS A PROFIT BLASTER

### Claude

Okay. You know this strategy far better than I do, so let's take it as profitable over a year and build on that. The goal is then to make it stronger with PCA, using your TradingView results directly rather than a Python copy.

**Two things that matter for the PCA work:**
- **Combining timeframe combos is a good idea, if they're different bets.** If D1/4H, 4H/1H and 12H/2H all win and lose on the same days, running them together just multiplies risk. If they win on different days, combining them smooths the equity curve. Measuring that is exactly what PCA does well.
- **Pick combos on one period and confirm on another.** If the "best" combos are chosen after seeing all the results, part of the blast is selection luck. Choosing on earlier years and checking on later ones tells us which combos really hold up.

## What I need from you
For **each timeframe combo** you trade (e.g. D/240, D/60, 240/60…):
1. Run it in TradingView over the **longest history you can**. Deep Backtesting goes back years if your plan has it.
2. Download "List of trades" as CSV. That's the download button you showed above.
3. Name each file by its combo, e.g. `EURUSD_D_240.csv`, and put them in `G:\pca-trading-strategy\tv_trades\`.
4. Tell me the exact symbol (e.g. `OANDA:EURUSD`) and the risk % used.

XAUUSD trade lists are welcome too; same format.

## What I'll do with them
1. **Combo map:** PCA on each combo's daily P&L, to show which combos are separate bets and which are copies of each other.
2. **Combined portfolio:** risk split across the independent bets, with return, drawdown and worst month compared against each combo alone.
3. **PCA market filter:** for every trade, check the conditions at entry (dollar or euro driving the move, the dollar's direction, how stretched the euro is, crisis regime). Then see which conditions give higher win rates. Filters are chosen on early years and confirmed on later ones.
4. **Overlap between EURUSD and gold:** both are partly dollar bets, so we'd check how often they're the same trade.

We already have the market data (9 currencies, gold, silver, 2010–2026), so this can start as soon as the CSVs are in the folder.

### You

now tell me I want to show project of this to my hod using pca we are analyzing market, so this is enough to tell the relation which we have found between forex pairs?

### Claude

Mostly yes. The work already shows real relationships between forex pairs, backed by 16 years of data and an honest test. But for a presentation to your HOD, two pieces are missing: **charts** and **one clear storyline**. Right now the findings are scattered across script outputs.

## What we have found

| Finding | Evidence |
|---|---|
| **1. Most currency movement comes from a few shared forces.** The biggest is the US dollar moving against everything; the next ones split "risky" currencies from "safe" ones. | PCA on 9 currencies + gold + silver, hourly, 2010–2026 |
| **2. Each cross pair = difference of two currencies' "own" moves.** E.g. EURGBP = euro's own move − pound's own move. This connects the pairs mathematically. | Residual model, exact identity |
| **3. Pairs that share the same drivers (AUDNZD, EURGBP, EURJPY…) drift apart and come back** on a daily scale. | Variance-ratio test, D1 walk-forward: Sharpe 0.46 before costs, 0.58 with 23 pairs (no swap) |
| **4. The relation is weak hour-to-hour** and costs swallow it. | H1 and H4 tests failed after spreads |
| **5. Gold vs silver does not come back together.** Their ratio trends (105 → 55 in 2025). | Gold/silver PCA: 3rd factor only 8%, backtest negative |
| **6. Data checked carefully.** Time zones fixed, two sources compared. | OANDA vs HistData correlation 0.998 |

The strongest point to present is that **we tested honestly**. Settings were chosen on 2010–2018 and tested only on 2019–2026, and we report what didn't work too (H1, H4, gold/silver, swap). A HOD will value that more than a big profit number.

## What's missing for a good presentation

1. **Correlation heatmap** of all pairs, the simple "which pairs move together" picture.
2. **Scree chart:** how much each PCA factor explains.
3. **Loadings chart:** which currencies sit on which factor. This is what shows "the dollar factor" and "risk-on / risk-off".
4. **Rolling PCA:** how the dollar factor's share changes over time, e.g. a spike in the 2020 COVID crash. This shows the relationships aren't fixed.
5. **One worked example:** the EURGBP price, its residual and its s-score, with entry and exit points marked.
6. **Walk-forward equity curve** with the train/test split marked.
7. **Limitations slide:** costs, swap, the weak H1 results, and gold/silver.

I'll compute items 1–4 fresh from our data so every number on the slides is exact. I haven't printed the full FX factor loadings in a form ready for slides yet.

## Suggested flow (about 10 slides)
1. Problem: do forex pairs move independently?
2. Data: sources, 2010–2026, cleaning.
3. Method: what PCA is, in one picture.
4. Results: heatmap → factors → loadings → rolling stability.
5. Application: the residual / s-score idea, with the EURGBP example.
6. Testing: walk-forward results, honest numbers.
7. What failed and why.
8. Conclusion and next steps (e.g. your setups combined with PCA filters).

Should I make it? I can build the charts from our data and put them into a slide deck you can download as PowerPoint or PDF.

### You

i will not include the trade part I will conclude that using pca we can know when not to trade.

### Claude

That conclusion fits the project well, and a HOD will accept it more easily than profit numbers. But right now it's a **claim we haven't tested yet**. To say "PCA tells us when not to trade", you need one chart that proves it.

## What PCA can say about "when not to trade"

**1. When everything moves together (crisis / stress).** PCA measures how much of all currency movement the first factor explains. When that share jumps, pairs stop behaving independently, and normal relationships between them break. This idea is published: the **Absorption Ratio** (Kritzman et al., 2011) showed that a high share of the first factor came before market turmoil. Your project can show the same thing for forex.

**2. When a pair's relation isn't holding.** For each pair, the model checks whether the leftover move is snapping back (0 < b < 1, a short half-life). If not, there's no relationship to rely on, so don't trade it. We already saw this:
- **Gold/silver:** the ratio kept trending (105 → 55), so the model said "no".
- **Hourly timeframe:** the moves were too small to beat costs.

**3. When a move is just the dollar.** If EURUSD moves mostly because of the dollar factor, the move says nothing about the euro itself, so euro-specific signals don't apply.

## The test you need (no trading involved)
1. Compute the first factor's share over time with rolling PCA, 2010–2026.
2. Split the history into **calm periods** (low share) and **stress periods** (high share).
3. Compare the pair relationships in the two regimes:
   - Do pair residuals snap back less in stress periods (variance ratio, half-life)?
   - Are pairs more volatile?
   - Do correlations between pairs change?
4. Mark known events on the chart (2011 euro crisis, 2015 CHF unpeg, 2020 COVID, 2022 rate hikes) to check whether the share rose around them.

If stress periods clearly show broken relationships, your conclusion is proven with data. If they don't, we'll know before the HOD asks, and you can phrase the conclusion more carefully.

**Slide flow then becomes:**

data → correlation heatmap → PCA factors (dollar, risk) → rolling factor share with crisis events → "relations break in stress periods" → conclusion: PCA tells us when not to trade.

Should I run this test now? It uses only the data we already have.

### Claude

The result went the opposite way from what I expected, so let me check that it's consistent across years before I tell you.

### Claude

The result holds in all four periods. The labels "calm" and "stress" turned out to be misleading, so I'll rename the regimes to low, medium and high concentration and regenerate the charts.

### Claude

The test supports your conclusion, but **the warning sign is the opposite of what I expected**. Pair relationships break when currencies **stop** moving together.

## What I tested
- **Concentration:** every day from 2010 to 2026, PCA on the previous 20 days of hourly moves (9 currencies plus gold and silver). It measures what share of all movement the first factor explains, from 28% to 76% (typically 52%).
- **Regimes:** I split the days into thirds: low, medium and high concentration.
- **Stretched pairs:** each time one of the 23 crosses stretched (s-score past ±2), I checked the next 10 days. Did it snap back, break further, or neither?
- **No trading or profit is involved.** It's purely how the relationships behave.

## Results (3,345 stretch events)

| Concentration | Snapped back | **Broke further** | Neither |
|---|---|---|---|
| Low (≤48%) | 41% | **7.7%** | 51% |
| Medium | 39% | 6.0% | 55% |
| High (>57%) | 45% | **2.3%** | 53% |

**Pairs break about 3 times more often when concentration is low.** This held in every period I checked:

| Period | Break rate, low concentration | Break rate, high concentration |
|---|---|---|
| 2010–14 | 9.0% | 3.4% |
| 2015–18 | 6.1% | 2.6% |
| 2019–22 | 7.5% | 3.1% |
| 2023–26 | 8.2% | 1.3% |

## Why it works this way
- **High concentration** means one force, mostly the dollar, moves every currency together. The cross pairs just ride along, so their relationships stay stable.
- **Low concentration** means each currency follows its own story: rate decisions, a central bank shock, safe-haven flows into JPY and CHF. That's when pair relationships snap.

The market shocks show this. In the **COVID crash** (Mar 2020), the **SNB CHF shock** (Jan 2015) and the **US downgrade** (Aug 2011), concentration **fell** to the low zone, because currencies split into safe and risky groups. The UK gilt crisis was a high-concentration event because it was a strong-dollar episode.

## Your conclusion, worded so the data supports it
> "Using rolling PCA, we measure how much of the forex market is driven by one common factor. When this share falls into its lowest third, currencies are moving on their own news, and stretched pair relationships break about 3 times more often (7.7% vs 2.3%), consistently across 2010–2026. PCA therefore tells us **when not to trust pair relationships**: in low-concentration regimes, avoid pair trades."

**Two honest limits to mention if asked:**
- The effect is on **breakdowns** (the dangerous tail). The chance of snapping back barely changes (39–45%).
- The thirds were set using the full 2010–2026 history. Live use would need thresholds from past data only.

## Files for your slides (in `data/regime/`)
- [concentration.png](data/regime/concentration.png): concentration over 16 years with shocks marked. This is your main chart.
- [snapback_by_regime.png](data/regime/snapback_by_regime.png): the bar chart above.
- `regime_summary.csv`, `shocks.csv` and `stretch_events.csv` hold the numbers behind them.

The script is [regime_analysis.py](regime_analysis.py). Next I can make the remaining charts (correlation heatmap, factor shares, which currencies sit on which factor) and put everything into a slide deck.

### You

so how much time in every year we can trade according to pca?

### Claude

On average **about two-thirds of the trading days each year** are tradable. That means roughly 170 of 260 days, with the low-concentration third ruled out. But it swings a lot from year to year.

"Past-only rule" below means the no-trade cut-off is set each day using only the history before that day, the way it would work live. I'd show that version to your HOD.

| Year | Tradable days (past-only rule) | Approx. days | Average concentration |
|---|---|---|---|
| 2010* | ~90% | — | 54% |
| 2011 | 51% | ~140 | 50% |
| 2012 | 79% | ~210 | 55% |
| 2013 | **33%** | ~85 | 45% |
| 2014 | **31%** | ~80 | 42% |
| 2015 | 54% | ~140 | 48% |
| 2016 | 63% | ~165 | 47% |
| 2017 | 70% | ~185 | 50% |
| 2018 | 82% | ~215 | 52% |
| 2019 | **47%** | ~120 | 43% |
| 2020 | 74% | ~190 | 50% |
| 2021 | 97% | ~250 | 56% |
| 2022 | 93% | ~240 | 60% |
| 2023 | 62% | ~160 | 54% |
| 2024 | 93% | ~240 | 58% |
| 2025 | 87% | ~225 | 55% |
| 2026 (to Oct) | 100% | ~205 | 61% |
| **Overall** | **~69%** | **~180 per year** | |

\*2010 has no earlier history to set the cut-off from, so that row is unreliable.

**What this shows:**
- **2013, 2014 and 2019 were mostly no-trade years** (about a third of days tradable). Currencies moved on their own stories then: Abenomics weakened the yen, and central banks went their separate ways.
- **2021–2026 have been mostly tradable** (87–100%). The dollar has been the dominant driver, so pairs stayed connected.
- **No-trade periods come in blocks, not single days:** 57 of them since 2010, each typically lasting about **2 weeks** (median 10 trading days). The longest ran **241 trading days**, about a year, during 2013–2014. That's useful for a trader: when the warning turns on, it usually stays on for a while.

For your slide, one sentence covers it: *"On average PCA flags about one-third of trading days as unsafe for pair trading, but this varies from about 30% tradable in 2013–14 to almost 100% in 2021–26."* I can add this year-by-year table as a bar chart in the slides too.

### You

this all conclusion is based on which pairs?

### Claude

The analysis has two layers, and they use different instruments.

## 1. The concentration measure (the "when not to trade" gauge)
The PCA runs on **11 instruments, each priced in US dollars:**

| Currencies (9) | Metals (2) |
|---|---|
| EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF, USDJPY, USDNOK, USDSEK | XAUUSD (gold), XAGUSD (silver) |

The USDxxx pairs are flipped, so every series is "1 unit of that currency in dollars". I also ran it **without gold and silver** (the 9 currencies only). The two gauges move almost identically (correlation 0.97), so the result doesn't depend on the metals.

## 2. The pairs whose behaviour was tested (stretch → snap back or break)
**23 cross pairs**, all combinations of EUR, GBP, AUD, NZD, CAD, CHF, JPY plus EURNOK and EURSEK:

AUDNZD, EURGBP, EURCHF, AUDCAD, NZDCAD, CADCHF, EURNOK, EURSEK, EURJPY, GBPJPY, AUDJPY, NZDJPY, CADJPY, CHFJPY, EURAUD, EURNZD, EURCAD, GBPAUD, GBPNZD, GBPCAD, GBPCHF, AUDCHF, NZDCHF

**Break rate when a pair stretched, low vs high concentration (each pair has 118–181 events):**

| Pair | Low | High | | Pair | Low | High |
|---|---|---|---|---|---|---|
| GBPCHF | 18.2% | 5.0% | | GBPNZD | 8.2% | 2.7% |
| CHFJPY | 14.8% | 4.4% | | EURCAD | 8.0% | 5.1% |
| EURNOK | 10.9% | 0.0% | | EURGBP | 7.7% | 0.0% |
| GBPJPY | 10.4% | 0.0% | | AUDCAD | 6.9% | 0.0% |
| GBPAUD | 10.3% | 5.6% | | EURAUD | 6.7% | 0.0% |
| NZDJPY | 10.3% | 0.0% | | CADCHF | 6.4% | 6.2% |
| EURCHF | 10.3% | 5.6% | | CADJPY | 6.2% | 0.0% |
| AUDCHF | 9.6% | 2.0% | | EURSEK | 6.2% | 0.0% |
| GBPCAD | 9.3% | 5.3% | | AUDJPY | 5.5% | 4.3% |
| EURJPY | 4.9% | 2.9% | | EURNZD | 3.4% | 0.0% |
| NZDCAD | 3.3% | 0.0% | | NZDCHF | 3.1% | 2.3% |
| **AUDNZD** | **2.1%** | **2.6%** | | | | |

- **22 of 23 pairs break more often in low concentration.** The only exception is AUDNZD. Australia and New Zealand move almost as one economy, so that pair stays stable whatever the regime.
- **The clearest effect is in pairs involving CHF, JPY and GBP**, the safe-haven and news-driven currencies.
- **Per pair the numbers are small** (only about 2–15 breaks each). The strong evidence is the **pattern across all 23 together**, not any single pair.

## What the conclusion does NOT cover
- **The USD pairs themselves** (EURUSD, GBPUSD…). They were used to build the gauge but weren't tested as tradable relationships.
- **Gold vs silver**, which we already showed doesn't snap back at all.
- **Exotics, crypto and indices**, which weren't included.

For your slide: *"Gauge built from 9 USD currency pairs + gold and silver; tested on 23 cross pairs, 2010–2026; the effect appears in 22 of 23 pairs."*

### You

if audnzd is very stable then trading on it is best right?

### Claude

No. AUDNZD is the **safest** pair, but not the most **profitable** one. It rarely breaks, but it also rarely snaps back.

**What happens after a pair stretches (s-score past ±2), next 10 days, 2010–2026:**

| Pair | Snapped back | Broke | Neither (drifted) | Volatility per year |
|---|---|---|---|---|
| GBPCAD | **54%** | 5% | 41% | 6.7% |
| GBPJPY | **51%** | 5% | 45% | 8.9% |
| EURJPY | 48% | 7% | 45% | 7.7% |
| EURGBP | 46% | 3% | 51% | 5.7% |
| … | | | | |
| **AUDNZD** | **32% (lowest of 23)** | **1.5% (lowest)** | **67% (highest)** | **4.5% (lowest)** |

**Why AUDNZD isn't the best trade:**
1. **It mostly just drifts.** Two times out of three, a stretched AUDNZD neither returns nor breaks within 10 days. Your money sits in the trade doing nothing, and you pay swap while it waits.
2. **The moves are tiny.** It has the lowest volatility of all 23 pairs, so each winning trade makes little. Spread and swap then eat a bigger share of the profit.
3. **The actual results agree.** In the 2019–2026 test (swap-free), AUDNZD made only **+3.4% over 8 years**, from 13 trades, with losing years in 2019, 2021 and 2022. EURJPY made +9.6%, GBPCAD +9.1% and GBPJPY +8.2%.

**Safe and profitable aren't the same thing.** What makes money is a pair that **snaps back often, rarely breaks, and moves enough to beat costs.** GBPCAD, GBPJPY, EURJPY and EURGBP fit that best.

**One caution:** don't keep only those 4 based on this table. Picking the winners after looking at the full history is the same hindsight trap as before. It's safer to trade a broad group of pairs and let the PCA gauge switch trading off in low-concentration periods.

For your HOD, AUDNZD is a nice example: *"AUDNZD is the most stable relationship (it almost never breaks), but because it moves so little and so slowly, stability alone does not make a pair worth trading."*

### You

no not of snapping like ingeneral trading strategies

### Claude

For trading strategies in general, AUDNZD is one of the **weaker** choices, not the best. "Stable" here means it moves slowly and steadily, and for most strategies that's a drawback. The two things that matter most are **how much the pair moves in a day** and **how much of that move the spread takes.**

**Vantage data, 2019–2026, daily candles closing 17:00 New York:**

| Pair | Typical daily range | Spread as % of daily range | Volatility per year |
|---|---|---|---|
| **EURUSD** | 0.58% | **~0%** (raw spread, commission charged separately) | 7.1% |
| **XAUUSD** | **1.31%** | **0.5%** | **17.6%** |
| GBPJPY | 0.77% | 1.1% | 9.6% |
| GBPAUD / GBPNZD | 0.68% | 1.2% | 7.7% |
| EURJPY | 0.66% | 1.4% | 8.3% |
| GBPUSD | 0.68% | 1.4% | 8.7% |
| USDJPY | 0.64% | 1.6% | 9.2% |
| … | | | |
| **AUDNZD** | **0.46% (one of the smallest)** | **2.9%** | **4.9% (2nd lowest)** |
| EURCHF / CADCHF / EURSEK | 0.43–0.67% | 3.5–3.6% (worst) | 5–7.7% |

**Why AUDNZD is weak for most strategies:**
1. **Small moves.** It moves about 0.46% a day, roughly a third of gold's range. Each trade has less room to make money.
2. **Expensive relative to its moves.** The spread eats about 3% of the daily range. On GBPJPY it's about 1%, on gold 0.5%, and on EURUSD almost nothing. With the same rules, AUDNZD keeps less of each trade.
3. **Slow, grinding behaviour.** Over 20-day periods it tends to drift slowly in one direction (variance ratio 1.3). It rarely gives sharp moves for breakouts, and it rarely swings back fast enough for quick reversals.
4. **Low volatility** means you need much bigger position sizes to make the same money, and that raises spread and swap costs too.

AUDNZD can suit very slow, low-risk strategies, such as long-term range or grid trading with wide targets. It also works as a calm "test" pair. For most active strategies (breakouts, intraday setups, your fib strategy), the pairs at the top of the table are better.

**This also supports your own choice of EURUSD and XAUUSD.** Your strategy's entry, stop and target are all based on the size of the daily candle. The bigger the range compared to the spread, the less cost eats into each 1:1 trade. EURUSD (cheapest) and gold (biggest range, low relative cost) are exactly the two best pairs in this table.

A caveat on the numbers: the spread figures are Vantage's typical recorded spread per hour. Real spreads widen at rollover and around news, but the ranking between pairs stays about the same.

### You

so now tell me what python files I should be having with me to show sir, I need to first show that how gold and silver failed. then how this forex pairs passed

### Claude

Here are the files to bring, in the order you'd present them. They're all in `G:\pca-trading-strategy\gold_silver_data\`. One gap: the gold/silver failure checks we ran (variance ratio, ratio trend) were quick one-off commands and were never saved as a file. Right now the only gold/silver file is a trading backtest, which you said you'll leave out.

## Part 1: Data (show briefly)
| File | What it shows |
|---|---|
| [fetch_data.py](fetch_data.py) | Downloads gold, silver and USD data, with time-zone fixes |
| [fetch_fx_histdata.py](fetch_fx_histdata.py) | Downloads 9 currencies + 23 cross pairs, 2010–2026 |
| [compare_oanda_histdata.py](compare_oanda_histdata.py) | Data validation: two sources compared (correlation 0.998) |

## Part 2: Gold and silver fail
| File | What it shows |
|---|---|
| [pca_strategy.py](pca_strategy.py) | The PCA model on gold, silver and USD, but it's mainly a backtest (trading) |
| **Missing:** `gold_silver_analysis.py` | Should show the no-trade evidence: PCA factor shares (68% / 24% / 8%), variance ratio of about 1.0–1.14 (no snap-back), and the gold/silver ratio chart trending 105 → 55 |

## Part 3: Forex pairs pass
| File | What it shows |
|---|---|
| [fx_pca_strategy.py](fx_pca_strategy.py) | The core model: PCA on currencies, the residual of each pair, the s-score, and the variance-ratio test. It also contains backtest code, so show only the model part |
| [regime_analysis.py](regime_analysis.py) | **Main result:** the rolling PCA concentration gauge, pairs breaking 3× more often in low concentration, 22 of 23 pairs, the shock dates. Charts are in `data/regime/` |
| **Missing:** `forex_analysis.py` | Should hold the slide charts: correlation heatmap, factor shares (scree), which currencies sit on which factor (loadings), and how far each pair's leftover snaps back vs gold/silver |

## Leave out (trading part)
`tf_strategy.py`, `walk_forward.py`, `swap_sensitivity.py`, `compare_spreads.py`, `fetch_fx_mt5.py`, `fetch_swaps_mt5.py`

## What I suggest
I can write the two missing files with no trading code in them, so each one runs on its own and saves its charts:

1. **`gold_silver_analysis.py`:** factor shares, variance ratio, ratio chart. Conclusion: *"gold and silver share drivers but their relationship trends, so it doesn't come back."*
2. **`forex_analysis.py`:** heatmap, scree, loadings, and variance ratios of the cross residuals next to gold/silver's. Conclusion: *"forex cross residuals come back, gold/silver's doesn't."*

With those, you'd show your sir four files: the 2 new analysis files, `regime_analysis.py`, and `fetch_fx_histdata.py` for the data. That way there's no trading code to explain. Should I write them?

### You

first tell me how much trades it took every year

### Claude

These are trade counts from the two backtests: gold/silver failed, the forex pairs passed. If your presentation leaves out the trading part, treat these as background in case your sir asks.

## Gold / silver (hourly, 2019 – Oct 2026): failed

| Year | Trades | Win % | Return % |
|---|---|---|---|
| 2019 | 9 | 56 | −0.2 |
| 2020 | 17 | 41 | −5.3 |
| 2021 | 16 | 56 | +1.5 |
| 2022 | 22 | 68 | −2.0 |
| 2023 | 9 | 33 | −2.1 |
| 2024 | 10 | 60 | −0.3 |
| 2025 | 12 | 50 | −5.0 |
| 2026 | 9 | 44 | −4.1 |
| **Total** | **104** (~13 a year) | | **7 of 8 years negative** |

Even in 2022, with a 68% win rate, it lost money. The few losing trades were big ones, where the ratio kept trending away.

## Forex, 13 cross pairs, daily candles (2010 – Oct 2026), swap-free: passed

| Year | Trades | Win % | Avg hold (days) | Return % | Period |
|---|---|---|---|---|---|
| 2010 | 16 | 56 | 13.6 | +6.2 | train |
| 2011 | 32 | 63 | 12.8 | +7.6 | train |
| 2012 | 14 | 50 | 13.8 | +1.6 | train |
| 2013 | 37 | 62 | 7.6 | +4.6 | train |
| 2014 | 34 | 79 | 9.4 | +14.2 | train |
| 2015 | 29 | 69 | 9.6 | +16.5 | train |
| 2016 | 31 | 65 | 11.4 | +9.4 | train |
| 2017 | 32 | 78 | 10.8 | +18.3 | train |
| 2018 | 24 | 50 | 16.3 | −3.5 | train |
| 2019 | 25 | 56 | 16.1 | −2.2 | **test** |
| 2020 | 33 | 61 | 9.0 | +9.4 | **test** |
| 2021 | 34 | 56 | 15.5 | −5.8 | **test** |
| 2022 | 33 | 64 | 7.9 | +1.8 | **test** |
| 2023 | 27 | 74 | 7.2 | +6.5 | **test** |
| 2024 | 22 | 73 | 9.9 | +5.7 | **test** |
| 2025 | 37 | 70 | 9.6 | +5.2 | **test** |
| 2026 | 28 | 79 | 14.4 | +13.9 | **test** |
| **Total** | **488** (~29 a year, ~2.4 a month) | | | | |

- Train 2010–2018: 249 trades, used to choose the settings.
- Test 2019–2026: 239 trades, never touched while choosing. 6 of 8 test years were profitable.

**Notes if your sir asks:**
- The forex numbers are **swap-free**. With worst-case swap charged, the test period was roughly flat.
- The gold/silver test covers only 2019–2026, while forex runs from 2010.
- A trade count of 488 is enough to take the result seriously. The 104 gold/silver trades are fewer, but all the evidence points the same way: the ratio trends, so it doesn't come back.
- These are daily trades held about 7–16 days. That's slow and steady, not frequent trading.

### You

keep this also but we will still conclude only that we now know when not to trade

### Claude

To connect the trades to your conclusion, the useful check is whether the trades made in "don't trade" periods actually did worse. Let me check that.

### Claude

I checked whether trades taken in PCA's "don't trade" periods actually did worse. **Partly yes, but not as cleanly as the break test.** You need to know this before your sir asks.

## Forex trades split by the PCA gauge at entry
"Don't trade" means low concentration, set with the past-only rule as it would work live. Results include costs, swap-free.

| | Trades | Win % | **Hit stop loss** | Avg profit per trade |
|---|---|---|---|---|
| In "don't trade" periods | 186 | 66% | **13.4%** | 0.26% |
| In "trade" periods | 286 | 66% | **8.0%** | 0.19% |

| Avg profit per trade | "Don't trade" periods | "Trade" periods |
|---|---|---|
| 2011–2018 | 0.38% | 0.22% |
| 2019–2026 | **0.04%** | **0.17%** |

**What it shows:**
- **Supports your conclusion:** trades in flagged periods hit the stop loss **about 1.7× more often** (13% vs 8%). That's the same "relationships break" effect, now seen in real trades.
- **Supports it in recent years:** in 2019–2026, flagged-period trades made almost nothing (0.04% per trade vs 0.17%).
- **Doesn't support it in 2011–2018:** flagged-period trades actually earned more. Currencies move more in those periods, so the winners were bigger too, which made up for the extra stop-outs.

**Gold/silver:** it loses in both kinds of period, and the gauge can't fix that. Only 12 gold/silver trades fell in flagged periods, too few to judge.

## Conclusion wording that matches all the evidence
> "PCA shows us **when pair relationships become unreliable**. When the first factor's share falls into its lowest third, stretched pairs break about 3× more often (7.7% vs 2.3%, 22 of 23 pairs). In our trades, stop-losses were hit 1.7× more often (13% vs 8%). So PCA tells us when **not to rely** on pair relationships. It's a risk warning, and it doesn't guarantee profit outside those periods."

Avoid saying *"trades in flagged periods lose money"*. That held in 2019–2026 but not in 2011–2018, and a careful HOD might check it.

## Files to show, in order
1. **Data:** `fetch_data.py`, `fetch_fx_histdata.py`, `compare_oanda_histdata.py`
2. **Gold/silver fail:** `pca_strategy.py` (yearly trades table), plus the missing `gold_silver_analysis.py`
3. **Forex pass:** `fx_pca_strategy.py` (model) and `tf_strategy.py` (yearly trades table, train/test), plus the missing `forex_analysis.py`
4. **Main conclusion:** `regime_analysis.py` (gauge, breaks 3×), extended with this trades-by-regime check

Should I write the two missing analysis files now and add the trades-by-regime table to `regime_analysis.py`, so everything above comes from files you can run?

### Claude

Now the forex file.

### Claude

Two fixes are needed in the forex file. The factor labels I wrote in advance don't match the data: PC2 is metals vs currencies, and PC3 is risk-on vs safe havens.

### Claude

Now I'll add the trades-by-regime check and the tradable-days table to the regime file.

### Claude

All three files run. Let me check the new charts.

### Claude

The loadings chart title is cut off. I'll fix it.

### Claude

I wrote the two new files and extended the regime file. All three run on their own and save their charts.

## What to show, in order

| # | Run this | Shows | Charts |
|---|---|---|---|
| 1 | [gold_silver_analysis.py](gold_silver_analysis.py) | **Gold/silver fails** | `data/gold_silver/` |
| 2 | [forex_analysis.py](forex_analysis.py) | **Forex pairs pass** | `data/forex/` |
| 3 | [regime_analysis.py](regime_analysis.py) | **Conclusion: when not to trade** | `data/regime/` |

Show [fetch_fx_histdata.py](fetch_fx_histdata.py) too, for where the data comes from.

## 1. Gold/silver: why it fails
- **PCA:** the first factor (gold, silver and the dollar moving together) explains 68%. The second (the dollar on its own) explains 24%. That leaves only **8%** for silver vs gold.
- **The leftover doesn't come back.** Its variance ratio is 1.01 at 1 day, 1.04 at 5 days, **1.20 at 10 days and 1.48 at 20 days**. That means it trends instead of returning.
- **The ratio trends for years:** from 32 up to 122, then from 105 down to 46 in 2025–26. It typically sits 5.2% away from its 1-year average.
- **Trading result:** 104 trades, Sharpe −0.61, 7 of 8 years negative.
- **Charts:** `pca_gold_silver.png`, `gold_silver_ratio.png`, `variance_ratio.png`

## 2. Forex: why it passes
- **PCA, 2010–2026:** the first 3 factors explain 72% of all movement:

  | Factor | Share | What it is |
  |---|---|---|
  | PC1 | 49% | the dollar against everything |
  | PC2 | 13% | currencies vs gold/silver |
  | PC3 | 10% | risk-on currencies (AUD, NZD, CAD) vs safe havens (JPY, CHF) |

  Earlier I said in passing that the second factor was risk-on vs safe havens. The data shows that's actually the third. The slides use the correct one.
- **The leftover comes back for most pairs:** 15 of 23 crosses have a variance ratio below 1 at 10 days. EURSEK is lowest (0.79). **Gold/silver is the worst of all 24** (1.20). That's the chart for your "gold failed, forex passed" slide.
- **Distance from the 1-year average:** most crosses stay 1.4–3.9% away, while gold/silver is 5.2%.
- **Trading result:** 488 trades. The 2019–2026 test had Sharpe 0.58 and 4.4% a year (swap-free).
- **Charts:** `correlation_heatmap.png`, `pca_forex.png`, `variance_ratio_vs_gold.png`

## 3. Conclusion: when not to trade
- Pairs **break about 3× more often** in low-concentration periods (7.7% vs 2.3%).
- **Days marked safe, per year (live rule, past data only):** 69% on average. The worst years were 2013–14 (31–33%); 2021–26 were 87–100%.
- **Forex trades opened on flagged days were stopped out 13.4% of the time, vs 8.0%** on other days. In 2019–26 they earned 0.04% per trade vs 0.17%. In 2010–18 they actually earned more, so present the gauge as a risk warning, not a profit rule.
- **Charts:** `concentration.png` (main chart), `snapback_by_regime.png`, `tradable_days_by_year.png`

## Small differences from numbers I gave you earlier
These files are the source to quote now.
- **Gold/silver yearly returns** are now counted by calendar year: 2022 is −0.2% (was −2.0%) and 2023 is −3.8% (was −2.1%). Totals and the conclusion are unchanged.
- **No-trade periods:** 44, typically 10 days, longest 236 days. Earlier I said 57; the live rule can't start until 2011 because it needs a year of history.
- **Not every cross comes back.** 8 of 23 are above 1, including AUDNZD at 1.14. Say "most crosses come back" rather than "all".

Each file is safe to run in front of your sir. They only read data already on the G: drive, and each takes about 1–3 minutes. Next I can put these charts into a slide deck.

### You

first explain me that how pca is used here in forex pairs, like what is the pullback explain like to a 2 yar old

### Claude

## The 2-year-old version 🧸

**The playground**
Imagine 9 kids on a playground: Euro, Pound, Aussie, Kiwi, Loonie, Franc, Yen, Krone and Krona. Their **teacher is Mr. Dollar.**

**PCA = finding out who makes the kids move**
When Mr. Dollar walks left, **all the kids walk left together.** That's the biggest reason they move, about half of all movement (PC1).
There are two smaller reasons:
- The shiny balloons, Gold and Silver, float their own way (PC2).
- When there's thunder ⛈️, the shy kids (Yen, Franc) run to hide, and the brave kids (Aussie, Kiwi, Loonie) keep playing (PC3).

PCA is like a camera that sees these big group moves and **takes them away.** What's left is each kid's own little wiggle.

**A pair = two best friends holding a rubber band**
Euro and Pound are best friends (EURGBP). After we remove "everyone walking with the teacher", we only look at **the space between Euro and Pound.**
- Normally they stay close.
- Sometimes Euro runs a bit ahead and **the rubber band stretches.** That's the s-score getting big.
- Soon the rubber band **pulls them back together.** 🪀 **That's the pullback.**

**So:** when the band is very stretched, we guess it will snap back.

**Gold and Silver are not best friends**
They have no rubber band. One wanders off, and they **don't come back.** That's why it failed.

**When not to play**
- **When Mr. Dollar leads everyone,** the kids stay in line, and stretched bands come back. ✅
- **When the teacher isn't leading** and every kid runs their own way (thunder, scary news), **rubber bands snap.** ❌ That's when we don't play. PCA tells us when this is happening.

---

## The grown-up version (same story)

1. **Each currency is priced in dollars:** EUR = EURUSD, JPY = 1/USDJPY, and so on. Gold and silver too.
2. **PCA finds the common forces:**
   - PC1 (49%): the dollar against everything.
   - PC2 (13%): currencies vs metals.
   - PC3 (10%): risk-on vs safe havens.
3. **Remove those forces.** What's left is each currency's **own move**, the residual.
4. **A pair is the difference of two currencies.** EURGBP's leftover = euro's own move − pound's own move. The dollar cancels out.
5. **Add up the leftover over time.** That gives a line that should wiggle around a middle, like the rubber band.
6. **The s-score measures how stretched it is,** in "normal stretch" units:
   - s = 0: at the middle.
   - s = +2.5: stretched up a lot, so expect a pullback **down** and sell.
   - s = −2.5: stretched down a lot, so expect a pullback **up** and buy.
7. **The pullback** is the leftover going back toward the middle (s back near 0). The variance ratio tested whether this really happens:
   - Below 1: it comes back. True for most forex crosses.
   - Above 1: it drifts away. Gold/silver was 1.20.
8. **When not to trade:** each day, PCA checks how much PC1 explains. When that share is low, currencies are moving on their own news. Then the rubber bands snap about 3× more often, so we stay out.

**In one sentence for your sir:**
> "PCA removes the big shared forces (dollar, metals, risk mood). What remains between two currencies usually pulls back to normal, but when PCA shows the shared force weakening, those pullbacks fail more often, so that's when not to trade."

### You

what is s score

### Claude

The **s-score is a number that tells you how stretched a pair is right now, compared with its normal stretch.**

## Simple version 🪀
Think of the rubber band between two friends again:
- **s = 0:** the band is relaxed, the friends are at their normal distance.
- **s = +1:** a little stretched one way. That's normal; it happens all the time.
- **s = +2.5:** very stretched. That's rare, so we expect it to pull back.
- **s = −2.5:** very stretched the other way. Also expect a pull back.
- **s = ±4:** stretched so far the band has probably broken. Get out.

So the s-score is just **"how many normal-stretches away from the middle"**. It's like a z-score, but for the pair's PCA leftover.

## How it's calculated (4 steps)
1. **Leftover:** after PCA removes the big shared forces, take the pair's leftover each day (euro's own move − pound's own move for EURGBP).
2. **Running total:** add it up day by day. That's the rubber-band line, called **X**.
3. **Fit a "pull-back" model** (Ornstein–Uhlenbeck) on the last 120 days: X(tomorrow) = a + b × X(today) + noise. From this:
   - **Middle (m)** = a / (1 − b): where the line is pulled back to.
   - **Normal stretch (σ)** = noise ÷ √(1 − b²): how far it usually wanders.
   - **Half-life** = ln 2 ÷ (−ln b): how many days it takes to come halfway back.
   - **Rule:** b must be between 0 and 1, or there's no pull-back at all, and then there's no s-score and no trade.
4. **The s-score:**

   **s = (X − m) / σ**

   That's today's position minus the middle, divided by the normal stretch.

## Example: EURGBP
- Middle m = 0
- Normal stretch σ = 0.8%
- Today the euro has moved 2.0% more than the pound on its own (after removing the dollar and the other forces), so X = 2.0%.
- **s = (2.0 − 0) / 0.8 = +2.5**, which means very stretched upward.
- Since the euro is "too high" vs the pound, we **sell EURGBP**, expecting the pullback down.
- Close the trade when s comes back to about **+0.5**, near the middle.
- If s instead runs to **+4**, the relationship broke, so exit with a small loss.

## Why use the s-score instead of just the price?
- **It removes the dollar and the other shared forces first,** so EURGBP doesn't look stretched just because the dollar moved.
- **It adjusts for each pair's normal wiggle.** A 1% move is huge for EURCHF but tiny for GBPJPY. With the s-score, 2.5 means "very stretched" on every pair, so one rule works everywhere.

**One line for your sir:**
> "The s-score measures how far a pair's PCA leftover is from its normal level, in units of its usual variation. Beyond ±2.5 we expect it to pull back; beyond ±4 we treat the relationship as broken."

### You

When this share falls into its lowest third, what does this mean?

### Claude

"Share" means **the percentage of all currency movement that the first PCA factor (mostly the dollar) explains**, measured over the last 20 trading days. "Lowest third" just means the share is **low compared with how it usually is**.

## How the cut-off works
1. Every day from 2010 to 2026, we compute the share. It ranged from **28% to 76%**, with a typical value of **52%**.
2. Line up all those days from lowest share to highest and cut them into **three equal groups**:

| Group | Share | Meaning |
|---|---|---|
| **Lowest third** | **48% or less** | Currencies moving on their own → **don't trust pairs** |
| Middle third | 48–57% | Normal |
| Top third | above 57% | The dollar drives almost everything |

So "falls into its lowest third" means that **on this day, the dollar explains 48% or less of the market's movement**, which is lower than on two-thirds of all days in history.

In the live version, the 48% isn't fixed. Each day the cut-off is recalculated from **past days only**, so it uses no future information.

## What it means in the market
- **Normal / high share:** "the dollar is the boss". When the dollar moves, every currency moves with it. The cross pairs (EURGBP, AUDCAD…) just ride along quietly, and their rubber bands hold.
- **Low share:** "no single boss". Each currency follows its own story:
  - a surprise rate decision in one country
  - safe-haven panic (yen and franc jump, aussie and kiwi fall)
  - a central-bank shock (e.g. the SNB removing the CHF floor in 2015)

  The currencies pull in different directions, so the rubber bands between them are much more likely to snap.

## Real examples of low-share periods
- **2013–2014:** Japan printed money (Abenomics) and central banks went different ways. The share dropped as low as 28%, and only about 1 in 3 days was tradable.
- **March 2020, COVID crash:** the share fell to about 30%. Investors rushed into safe havens and dumped risky currencies, so the market split instead of moving as one.
- **January 2015, SNB shock:** the franc jumped about 20% in a day, entirely its own story.

## The numbers behind "don't trade"
- Stretched pairs break **7.7%** of the time in the lowest third, vs **2.3%** in the top third. That's about **3×** more often.
- Trades opened in those periods hit the stop loss **13%** of the time vs **8%**.

**One line for your sir:**
> "When the first PCA factor explains less of the market than on two-thirds of past days, currencies are being driven by their own separate news instead of one common force, and that's when pair relationships break most often."

### You

how we know that is is falling in lower third

### Claude

Every day at the daily close (17:00 New York), we run **two numbers and compare them.**

## Step 1: today's share
- Take the **last 20 trading days of hourly price changes** (480 hours) for the 11 instruments: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF, USDJPY, USDNOK, USDSEK, gold and silver.
- Run PCA on them.
- Look at the first factor: **what % of all movement does it explain?** That's today's share, for example 58.6%.

## Step 2: the cut-off line
- Take **all the shares from past days**, from 2010 up to yesterday.
- Find the value that **one-third of those days fall below**. That's the 33rd percentile. Right now it's **47.5%**.
- It uses only past days, so there's no peeking at the future, and it updates a little every day.

## Step 3: compare
- **Today's share ≤ cut-off:** **lowest third**, a no-trade day ❌
- **Today's share > cut-off:** normal, OK to trade ✅

## Real examples from our data

**COVID, March 2020:**

| Date | Today's share | Cut-off | Result |
|---|---|---|---|
| 9 Mar 2020 | 29.7% | 44.3% | ❌ no-trade |
| 12 Mar 2020 | 37.3% | 44.3% | ❌ no-trade |
| 20 Mar 2020 | 39.6% | 44.3% | ❌ no-trade |

**Latest days in our data:**

| Date | Today's share | Cut-off | Result |
|---|---|---|---|
| 14 Oct 2026 | 62.5% | 47.5% | ✅ trade |
| 16 Oct 2026 | 58.6% | 47.5% | ✅ trade |

So right now (mid-October 2026) the market is **in the tradable zone.** The dollar is driving most of the movement.

## Where this is in the code
In [regime_analysis.py](regime_analysis.py):
- The `pc1_share()` function does step 1, running PCA on each 480-hour window.
- `cut = conc.expanding(min_periods=260).quantile(1/3).shift(1)` does step 2: the 33rd percentile of all past days, shifted so today isn't included in its own cut-off. It starts only after one year (260 days) of history.
- `live = conc > cut` does step 3.

The daily results are saved in `data/regime/concentration_daily.csv`.

**One line for your sir:**
> "Each day we compute the first factor's share from the last 20 days, and compare it with the 33rd percentile of all previous days. If today is below that line, we mark it as a no-trade day."

### You

how do we calculate the today's share

### Claude

Here's the real calculation for **16 October 2026**, the latest day in our data, which gave **58.6%**.

## Step 1: collect the last 480 hours of price changes
- **11 instruments**, each priced in US dollars: EUR, GBP, AUD, NZD, CAD, CHF, JPY, NOK, SEK, gold, silver. The USDxxx pairs are flipped, so USDJPY becomes JPY in dollars.
- **Hourly % change (log return)** for each, for the last **480 hours** (about 20 trading days, 18 Sep → 16 Oct 2026).
- That gives a table of **480 rows × 11 columns.** The last 3 rows:

| Hour (UTC) | EUR | GBP | AUD | NZD | CAD | CHF | JPY | NOK | SEK | XAU | XAG |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 16 Oct 18:00 | +0.056 | +0.042 | +0.017 | +0.034 | +0.056 | +0.049 | +0.038 | +0.054 | +0.057 | −0.086 | −0.305 |
| 16 Oct 19:00 | +0.045 | +0.062 | +0.072 | +0.074 | +0.090 | +0.030 | +0.038 | +0.068 | +0.038 | +0.209 | +0.125 |
| 16 Oct 20:00 | +0.007 | +0.001 | −0.003 | +0.012 | +0.005 | +0.006 | +0.004 | +0.030 | +0.053 | −0.089 | −0.360 |

You can already see the pattern: in each hour, the currencies mostly move **the same direction together.** That's the dollar.

## Step 2: correlation matrix (11 × 11)
For every pair of instruments, how closely did they move together over those 480 hours? 1 means perfectly together, 0 means unrelated. A corner of it:

| | EUR | GBP | AUD | NZD |
|---|---|---|---|---|
| EUR | 1.00 | 0.84 | 0.67 | 0.72 |
| GBP | 0.84 | 1.00 | 0.68 | 0.74 |
| AUD | 0.67 | 0.68 | 1.00 | 0.76 |
| NZD | 0.72 | 0.74 | 0.76 | 1.00 |

Using correlation, not raw moves, gives every instrument an equal vote. Otherwise silver, which moves the most, would dominate.

## Step 3: PCA, splitting the movement into factors
PCA breaks this matrix into 11 independent factors. Each has a size (its **eigenvalue**). The sizes always **add up to 11**, one unit per instrument:

| Factor | PC1 | PC2 | PC3 | PC4 | PC5 | PC6 | PC7 | PC8 | PC9 | PC10 | PC11 | **Total** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Size | **6.45** | 1.23 | 0.89 | 0.58 | 0.48 | 0.36 | 0.34 | 0.21 | 0.19 | 0.14 | 0.11 | **11.0** |

## Step 4: the share

**Share = biggest factor ÷ total = 6.45 ÷ 11.0 = 58.6%**

So over the last 20 days, **58.6% of all movement in these 11 instruments came from one common force**, mostly the dollar.

## What the two extremes would look like
- **All 11 moving exactly together:** PC1 = 11 and the share is **100%**. One boss controls everything.
- **All 11 moving completely independently:** each factor is about 1, so PC1 ≈ 1 and the share is about **9%**. No boss at all.

Real markets sit between these: **28% to 76%** in 2010–2026. On 16 Oct 2026 it was 58.6%, above the 47.5% cut-off, so it's a **tradable day.**

## In the code
In [regime_analysis.py](regime_analysis.py):
```python
def pc1_share(z):
    vals = np.linalg.eigvalsh(np.corrcoef(z.T))   # step 2 + step 3
    return vals[-1] / vals.sum()                  # step 4: biggest ÷ total
```
`z` is the 480 × 11 table from step 1. The function runs once per day, every day from 2010 to 2026.

**One line for your sir:**
> "Each day we take the last 480 hourly returns of 11 dollar-priced instruments, compute their correlation matrix, and run PCA. Today's share is the largest eigenvalue divided by the sum of all eigenvalues, that is, the fraction of total movement explained by the single strongest common factor."

### You

why these eigen value add up to 11? and what is eigen value and eigen vec to a 2 yearold

### Claude

## Why do they add up to 11?

**Short answer:** we have 11 instruments, each counts as **1 unit of wiggle**, so the total is 11. PCA only **re-divides** that total into factors. It can't create or destroy wiggle.

**A bit more detail:**
- We use the **correlation** matrix, which means each instrument is first rescaled so its own wiggle (variance) is exactly **1**. That's why the diagonal of the correlation matrix is all 1s (EUR with EUR = 1.00, and so on).
- **Total wiggle = 1 + 1 + … + 1 = 11.** In maths, that sum of the diagonal is called the **trace**.
- A rule of linear algebra: **the eigenvalues always add up to the trace.** So they must add up to 11.
- PCA just says how that 11 is shared out: PC1 gets 6.45, PC2 gets 1.23, … the last gets 0.11. Total still 11.

It's like 11 sweets 🍬 shared among 11 bowls. On 16 Oct, one bowl (PC1) got 6.45 sweets and the rest share the remaining 4.55. **Share = 6.45 / 11 = 58.6%.**

## Eigenvector and eigenvalue, for a 2-year-old 🧸

**The dance class 💃**
11 kids are dancing. Their movements look messy, but the teacher notices they're really doing a few **dance moves** mixed together.

- **Eigenvector = a dance move.** It's a recipe saying how much each kid moves, and in which direction:
  - **Move 1:** "Everybody step left together!" That's PC1, the dollar.
  - **Move 2:** "Kids step left, but the balloon kids (gold, silver) step right!" That's PC2, currencies vs metals.
  - **Move 3:** "Brave kids (AUD, NZD, CAD) jump, shy kids (JPY, CHF) hide!" That's PC3, risk-on vs safe havens.
- **Eigenvalue = how much that dance move was used.**
  - Move 1 was used a LOT: 6.45 out of 11.
  - Move 2 a bit: 1.23.
  - The last moves hardly at all: 0.11.

So: **the eigenvector is the dance move. The eigenvalue is how much dancing happened with that move.**

## Tiny example with only 2 currencies (EUR and GBP)
Say their correlation is **0.8**, so they usually move together.

Correlation matrix:
```
       EUR   GBP
EUR   1.0   0.8
GBP   0.8   1.0
```
Total wiggle = 1 + 1 = **2**.

PCA finds 2 dance moves:

| Move | Eigenvector (recipe) | Meaning | Eigenvalue (how much) |
|---|---|---|---|
| PC1 | EUR +0.71, GBP +0.71 | both move **together** | **1.8** |
| PC2 | EUR +0.71, GBP −0.71 | they move **opposite** (EUR vs GBP) | **0.2** |
| | | **Total** | **2.0** ✅ |

- **PC1's share = 1.8 / 2 = 90%:** most of the time they move together.
- **PC2 = 0.2 is the "EURGBP leftover":** the small part where they move apart. That's exactly what our pair trading looks at (the rubber band).
- The eigenvalues here are simply **1 + correlation** and **1 − correlation**. Higher correlation means a bigger PC1 share.

**Our real data works the same way, just with 11 kids instead of 2.**

## One line for your sir
> "An eigenvector is a pattern of joint movement (a weighted combination of the currencies), and its eigenvalue is how much of the total variance that pattern accounts for. Because each standardized series has variance 1, the eigenvalues of the 11×11 correlation matrix sum to its trace, 11, so the first eigenvalue divided by 11 gives the share explained by the strongest common factor."

### You

now tell me why we  use only Ornstein–Uhlenbeck there is no alternative?

### Claude

No, there are alternatives. OU is the **standard and simplest** choice for this job, not the only one.

## Why we used OU
1. **It's the simplest model of "pulls back to a middle".** OU says: *the further you are from the middle, the harder you're pulled back, plus some random noise.* That's exactly the rubber band.
2. **It gives the three numbers we need, from one easy fit.** In daily data, OU becomes a straight-line regression: X(tomorrow) = a + b × X(today) + noise. From a and b we get:
   - **the middle** (m)
   - **the speed of the pullback** (half-life)
   - **the normal stretch** (σ), which together give the s-score
3. **It has a built-in safety check.** If b isn't between 0 and 1, there's no pullback, so no s-score and no trade. That's why gold/silver often produced no signal.
4. **It's the standard method in the research.** Avellaneda & Lee (2010), *"Statistical Arbitrage in the U.S. Equities Market"*, used **PCA + OU + s-score**, which is exactly our setup. Using a published method makes the project easy to defend.
5. **It needs only 3 parameters,** so it fits reliably on just 120 days of data.

## Alternatives

| Method | What it does | Compared with OU |
|---|---|---|
| **Rolling z-score** (Bollinger-band style) | (X − rolling average) / rolling std | Simpler, but gives no pullback speed and doesn't check that a pullback exists |
| **ADF / Engle–Granger / Johansen cointegration tests** | Statistical tests that the pair is mean-reverting | They **test** for a pullback but don't give a trading signal; usually combined with OU or a z-score |
| **Hurst exponent / variance ratio** | Measures trending vs mean-reverting | A check, not a signal. **We already used the variance ratio** as an independent test |
| **Kalman filter** | Lets the middle and the relationship change smoothly every day | More flexible for drifting relationships, but more complex and easier to overfit |
| **AR(p) / ARMA** | OU with more lags | Captures more patterns, but needs more data and is harder to explain |
| **Regime-switching OU** (Markov switching) | The pull-back strength changes between "calm" and "stress" states | Close to our concentration idea, but much more complex |
| **GARCH-adjusted s-score** | Lets the "normal stretch" change with volatility | Better in volatile periods, but adds parameters |
| **Machine learning** (random forest, LSTM) | Learns patterns from many features | Powerful, but a black box, easily overfits, and hard to explain to a HOD |

## Does our conclusion depend on OU?
Mostly no:
- **The concentration share** (the "when not to trade" gauge) is pure PCA. No OU is involved.
- **The variance ratio** (forex comes back, gold/silver doesn't) is model-free. No OU is involved.
- **Only the stretch/break test** (7.7% vs 2.3%) uses the OU s-score.

To prove the stretch/break result isn't just an OU artifact, I can **re-run the stretch/break test with a simple rolling z-score** instead of OU. If pairs still break about 3× more in low-concentration periods, the conclusion holds whichever model you use. That's a strong point to show your sir. Should I run it?

## If your sir asks "why OU?"
> "We use the Ornstein–Uhlenbeck model because it is the simplest model of mean reversion. It gives the equilibrium level, the speed of reversion and the normal deviation from one linear regression, and it is the standard approach in the PCA statistical-arbitrage literature (Avellaneda & Lee, 2010). Alternatives such as rolling z-scores, cointegration tests or Kalman filters exist. Our main finding comes from PCA alone, and the mean-reversion result is confirmed separately by the model-free variance-ratio test."

### You

so what the best model for our task if ou is simplest

### Claude

For this project, **OU is the best choice.** Simplest doesn't mean weakest here. A "better" model only counts if it gives better results **on new data**, and that's where complex models usually fail.

## Why OU fits our task best
1. **Our data is small per fit.** Each model is fitted on only **120 daily points.** OU has 3 parameters, so it fits reliably. A Kalman filter, regime-switching model or neural network has many more parameters, which on 120 points mostly means **fitting noise.**
2. **Our main conclusion doesn't come from OU at all.** The "when not to trade" gauge is pure PCA, and the gold vs forex comparison uses the model-free variance ratio. A fancier pullback model wouldn't change the main finding.
3. **We already do the regime part separately.** Regime-switching OU's main advantage is knowing when the pullback weakens. Our PCA concentration gauge does that job in a simpler, more explainable way: **OU for the pullback, PCA for the regime.**
4. **It's the published standard** (Avellaneda & Lee 2010), and you can explain it on one slide.

## If we wanted to improve it, in order of value

| Rank | Model | Why it could help | Risk |
|---|---|---|---|
| 1 | **OU + rolling z-score check** | Proves the result isn't specific to OU | None, it's just a check |
| 2 | **Kalman filter** | The pair's "middle" can drift slowly (e.g. rate differences changing over years) instead of being fixed for each 120-day window | More settings to tune, so more overfitting risk |
| 3 | **OU with volatility adjustment (GARCH)** | The "normal stretch" grows in volatile periods, so fewer false signals in shocks | More parameters, small expected gain |
| 4 | Regime-switching OU / machine learning | In theory the most flexible | Hard to explain, easily overfits, not worth it for this project |

## How you'd prove which one is best
You can only call a model **"best"** by testing it, not by its complexity:
1. Run **OU, rolling z-score and Kalman** through the same tests: the stretch/break test, the variance ratio, and the daily walk-forward.
2. Choose using **2010–2018 only**, then check on **2019–2026.**
3. The model that holds up best on 2019–2026 wins.

If OU and the z-score give similar results, that **confirms OU is enough** and the conclusion is robust. If the Kalman filter is clearly better on 2019–2026, it's worth mentioning as future work.

**For your sir:**
> "We chose OU because, with 120-day fitting windows, a three-parameter model is the most reliable and interpretable; more complex models such as Kalman filters or regime-switching would add parameters that risk overfitting. The regime effect, which those models try to capture, is handled separately and more transparently by our PCA concentration gauge."

Should I run the comparison: OU vs rolling z-score (and the Kalman filter if you want) on the same tests? It would give you a "we checked alternatives" slide.

### You

We already used the variance ratio as an independent test, why we use variance?

### Claude

We use variance because **it measures how far something wanders**, and *how far it wanders over time* is exactly what separates "comes back" from "drifts away".

## The idea: a puppy on a walk 🐶
- **Puppy with no leash (random walk):** every step goes in a random direction. The longer you wait, the further away it gets. After 10 steps it has wandered roughly **10 times as much** (in variance terms) as after 1 step.
- **Puppy on a leash (mean-reverting, pulls back):** it steps away, but the leash pulls it back. After 10 steps it's **not** 10 times further. **Less than 10×.**
- **Puppy chasing a squirrel (trending):** it keeps going the same way. After 10 steps it's **more than 10×** away.

So we just compare: **how much did it wander in 10 days, vs 10 × how much it wanders in 1 day?**

## The formula

**Variance ratio VR(k) = variance of k-day moves ÷ (k × variance of 1-day moves)**

| VR | Meaning | Puppy |
|---|---|---|
| **= 1** | random walk, no pull | no leash |
| **< 1** | moves get undone → **pulls back** ✅ | on a leash |
| **> 1** | moves keep going → **trends** ❌ | chasing a squirrel |

## Why variance specifically
1. **A random walk has a known rule: its variance grows exactly in proportion to time.** For daily moves with variance 1, 10 days of them have variance 10. Any departure from this rule shows a pull-back (below) or a trend (above).
2. **Averages don't work.** The average move is about 0 whether the series comes back or not, so it can't tell them apart. Variance captures the **size** of wandering, whatever the direction.
3. **No model is fitted.** OU assumes a specific shape (the rubber band) and fits it. The variance ratio assumes nothing; it just measures. That's why it works as an **independent check** on OU: two different methods reaching the same answer.
4. **It's a classic test:** Lo & MacKinlay (1988), widely used in finance to test random walks.

## Our numbers (10-day horizon, PCA leftover)

| Series | VR | Meaning |
|---|---|---|
| EURSEK | **0.79** | 10-day wander is only 79% of what a random walk would do → strong pullback |
| EURCHF | 0.83 | pullback |
| median of 23 forex crosses | 0.95 | mild pullback |
| AUDNZD | 1.14 | slight drift |
| **Gold/silver** | **1.20** | wanders **more** than random → **trends, no pullback** |

Gold/silver gets worse at longer horizons: **1.48 at 20 days**. The longer you wait, the further it drifts. That's why the strategy kept losing.

## A tiny numeric example
Suppose the daily leftover moves have variance 1.
- **Random walk:** 10-day variance = 10, so VR = 10 / (10 × 1) = **1.0**
- **EURSEK:** 10-day variance measured = 7.9, so VR = 7.9 / 10 = **0.79**. Some daily moves got undone.
- **Gold/silver:** 10-day variance measured = 12, so VR = 12 / 10 = **1.20**. Daily moves kept adding up in the same direction.

**One line for your sir:**
> "For a random walk, the variance of returns grows linearly with the horizon, so the variance ratio equals 1. A ratio below 1 means moves get partly reversed (mean reversion), above 1 means they persist (trending). It is model-free, so it independently confirms the OU results: most forex cross residuals score below 1, while gold/silver scores 1.20 at 10 days and 1.48 at 20 days."

### You

also include this in ppt

### Claude

I'll build the deck from the result files the three scripts saved. First I'll gather all the numbers into one data file.

### You

The user sent a new message while you were working:
why didnot scale the data? using standard scaler?

This is how Claude Code surfaces messages the user sends mid-turn — within the running turn, often alongside the next tool result, rather than as a separate conversation turn. Address the message above as you continue this turn.

### You

The user sent a new message while you were working:
also include an example where pull back is shown and a trade based on that pullback. in the ppt

This is how Claude Code surfaces messages the user sends mid-turn — within the running turn, often alongside the next tool result, rather than as a separate conversation turn. Address the message above as you continue this turn.

### Claude

I'll add a real pullback trade example as well. First I'll pick a clean one from the actual test-period trades.

### Claude

EURGBP, short on 31 Oct 2024, is the clearest example: simple pair, s = +2.9, back to the target in 4 days. Let me pull its full s-score and price path.

### You

also plot the pull back in a graph of sine wave type of graph

### You

in the ppt

### You

also plot the pull back in a graph of sine wave type of graph

in the ppt

### Claude

I'll add that as well: a sine-wave style chart showing the pullback cycle, with the trades highlighted. Now writing the deck builder.

### Claude

Valid. Now rendering the slides to check them visually.

### Claude

PowerPoint itself refuses the file, even though the validator passed. I'll find which element causes it by testing small decks.

### Claude

Still checking the deck: PowerPoint rejects one element, and I'm testing slides one by one to find which.

### Claude

Found it: on slide 13, the value labels were applied to the dashed "1.0" line as well as the bars, and PowerPoint rejects that position on a line. Fixing.

### Claude

PowerPoint opens it now. Checking every slide visually.

### Claude

I've built the deck: **[PCA_Forex_Analysis.pptx](PCA_Forex_Analysis.pptx)**, 26 slides. PowerPoint opens it, and I checked every slide as an image.

It includes all three things you asked for along the way:

- **Pullback as a sine wave (slide 6):** a stretch-and-return wave with the entry lines at ±2.5 and exit lines at ±0.5. The sell trades are drawn in red and the buy trades in green, so you can see a trade open at each stretch and close on the return.
- **Real pullback trade (slide 8):** EURGBP from our test period.
  - On 31 Oct 2024 the s-score hit +2.91, so the strategy sold at 0.8435.
  - On 6 Nov the s-score was back to +0.30, so it closed at 0.8329.
  - It was held 4 days, for **+1.46% of the account after costs**.
  - Two charts show it: the s-score and the price, with the trade highlighted. A note explains that EUR and GBP both fell against the dollar in US election week. PCA removed that dollar move, so only euro vs pound was traded.
- **Scaling (slide 4):** a chart of how differently each instrument moves before scaling (silver 30% a year, CAD 7%). Next to it, the four scaling steps, showing it's the same as StandardScaler but using only past data.

**Slide order:**

| Slides | Part |
|---|---|
| 1–3 | Title, the answer in three numbers, data used |
| 4–9 | Method: scaling, PCA (eigenvectors and eigenvalues), the sine-wave pullback, how the s-score is built, the real EURGBP trade, variance ratio |
| 10–13 | **Gold/silver fails:** factor shares, the ratio trending, variance ratio rising above 1, the yearly trade table |
| 14–18 | **Forex passes:** correlation heatmap, the 3 factors, variance ratio vs gold/silver, train/test trade tables |
| 19–24 | **When not to trade:** how the daily gauge is calculated, the gauge from 2010 to 2026 with market shocks, breaks 3× more often, safe days per year, the check on real trades |
| 25–26 | Limits, then the conclusion: PCA tells us when not to trust pair relationships |

The charts are real PowerPoint charts, so you can click them to see or edit the numbers. The heatmap is the one picture, because PowerPoint has no heatmap chart. Several slides have speaker notes with the simple "2-year-old" explanations, for when you present.

To rebuild after the analysis changes, run `python export_data.py`, then `node build_deck.js` with `NODE_PATH=./node_modules`, both in `G:\pca-trading-strategy\presentation\`. The slide preview images I checked are in `presentation\qa\`; you can delete them.

### You

https://github.com/tusharnmims/pca-forex-analysis.git

this is the repo from quantara login in git push it to this repo include all ipynb files and plots inside the ipynbs and ppt also. for backtesting make a separate folder and for pca different.

### Claude

I'll first check your git login and what's already in that repo.

### Claude

The repo is empty and **public**, and your active GitHub login (`quantaraxofficial`) has push access. Because it's public, I'll scan the code for anything private before copying it.

### Claude

Clean, no credentials in the project code. Now checking how the scripts locate the data, so they still work once split into folders.

### Claude

Setting up the repo folder: clone, copy the code, and point the scripts at a shared `data/` folder.

### Claude

Now linking the existing data in (without copying it, and git-ignored) and adding `.gitignore` and `requirements.txt`.

### Claude

Now writing the notebooks. Each one explains the step, runs the code, and keeps the charts and tables inside the notebook.

### Claude

Now executing all 8 notebooks so the charts are saved inside them. The walk-forward ones take a while, so this runs in the background.

### Claude

While the notebooks run, I'll write the README.

### Claude

The README is written. Waiting for the notebooks to finish running.

### Claude

All 8 ran without errors. Notebook 05 is suspiciously small, so let me check what each one contains.

### Claude

`data/` was correctly left out. Pushing with the `quantaraxofficial` login.

### Claude

Everything is pushed: **https://github.com/tusharnmims/pca-forex-analysis**

## What's in the repo

| Folder | Contents |
|---|---|
| `pca/` | 3 notebooks, each with its charts saved inside: gold/silver PCA (why it fails), forex PCA (correlations, factors, variance ratios), and when not to trade (the daily gauge) |
| `backtesting/` | 5 notebooks: gold/silver backtest, forex hourly backtest, hourly walk-forward, daily/4H walk-forward (8 and 23 crosses, with and without swap), swap sensitivity |
| `src/` | The shared Python code the notebooks use: data download, PCA model, s-score, backtest engine |
| `presentation/` | `PCA_Forex_Analysis.pptx` plus the scripts that rebuild it |
| `README.md` | Findings, folder layout, method, how to download the data and run everything |

All 8 notebooks were run from start to finish before pushing, with no errors. Each one has its tables and charts saved inside, so GitHub shows them without anyone running anything. The one exception is `05_swap_sensitivity`, which has a short results table and no chart.

## Things to know
- **The repo is public.** Before pushing I checked it for passwords, your MT5 account and personal emails. Nothing was there.
- **Market data isn't included.** It's 664 MB, and the data providers' terms may not allow sharing it. The README lists the commands to download it.
- **The commit is from `quantaraxofficial`** (with its private GitHub no-reply email), as you asked. I didn't change your global git settings; `bnbfx` stays your default for other projects.
- **Two copies now exist:**
  - `G:\pca-forex-analysis` is the repo copy. Its `data` folder links to your existing data, so the notebooks run there without copying anything.
  - `G:\pca-trading-strategy` is your original project, unchanged.
- **In the repo copy, I changed the scripts' data path** so they read from `<repo>/data` instead of next to the scripts. Make future edits in the repo copy, or the two copies will drift apart.

### You

now what a interview level questions can be asked to me based on this project?

### Claude

Below are the questions an interviewer is likely to ask about this project, grouped by topic, each with a short answer based on your actual numbers. The ones marked ⚠️ are the tough follow-ups designed to test whether you really understand the work.

## 1. PCA fundamentals

**Q1. What is PCA, in one sentence?**
It rotates correlated variables into uncorrelated factors (eigenvectors of the covariance or correlation matrix), ordered by how much variance each explains (the eigenvalues).

**Q2. Why did you standardise the returns before PCA?**
Raw volatility differs a lot: silver moves 30% a year, CAD 7%. Without scaling, PCA would mostly describe silver. Standardising means PCA runs on the correlation matrix, so every instrument gets an equal vote.

**Q3. ⚠️ Did you use StandardScaler? Isn't fitting it on all the data a problem?**
I didn't fit one scaler on 2010–2026, because that would leak future means and standard deviations into the past. Each window is standardised with its own past mean and std (480 hours, or 120 days). That's look-ahead-free.

**Q4. Why returns and not prices?**
Prices are non-stationary (EURUSD 1.08 vs gold 2,600). PCA on price levels picks up shared trends, giving spurious correlation. Returns are roughly stationary.

**Q5. Why do the eigenvalues add up to 11?**
The trace of a correlation matrix is 11 (eleven 1s on the diagonal), and the sum of the eigenvalues equals the trace. So PC1's share = λ₁ / 11.

**Q6. What do your first 3 factors mean?**

| Factor | Share | Meaning |
|---|---|---|
| PC1 | 49% | the dollar against everything (all loadings positive) |
| PC2 | 13% | currencies vs metals |
| PC3 | 10% | risk-on (AUD, NZD, CAD) vs safe havens (JPY, CHF) |

**Q7. ⚠️ Eigenvectors have arbitrary sign. How did you handle that?**
I fixed the orientation: EUR positive for PC1, metals negative for PC2, AUD positive for PC3. Without this, loadings can flip between windows and the charts or labels become inconsistent.

**Q8. How many factors did you remove, and why 3?**
k = 3 removes about 72% of the common movement and matches three interpretable factors. I tested k = 2 and k = 4 as a sensitivity check in the hourly model. Removing too many factors starts to strip out the pair-specific signal itself.

**Q9. ⚠️ Are PCA factors stable over time?**
No. That's why I refit the model on rolling windows, and why the concentration gauge itself (PC1's share) moves between 28% and 76%. That instability is the regime signal.

## 2. Residual, s-score and Ornstein–Uhlenbeck

**Q10. How do you get a cross pair's residual?**
EURGBP's return equals r_EUR − r_GBP (both priced in USD), so the residual is e_EUR − e_GBP after removing the factors. The dollar cancels out exactly.

**Q11. Explain the s-score.**
Fit an AR(1) on the cumulative residual X: X(t+1) = a + b·X(t) + ε. Then:
- middle m = a / (1 − b)
- equilibrium stretch σ = sd(ε) / √(1 − b²)
- **s = (X − m) / σ**

Enter at |s| ≥ 2.5, exit at 0.5, stop at 4.

**Q12. Why OU, and what are the alternatives?**
It's the simplest mean-reversion model: 3 parameters that fit reliably on 120 points, and it gives the middle, the speed (half-life) and the normal stretch. It's the standard in Avellaneda & Lee (2010). Alternatives include a rolling z-score, Engle–Granger/Johansen cointegration tests, Kalman filters, and regime-switching OU.

**Q13. What happens when b ≥ 1 or b ≤ 0?**
There's no mean reversion (b ≥ 1 is a random walk or explosive; b ≤ 0 means oscillation), so there's no s-score and no trade. That's a built-in filter.

**Q14. What is the half-life, and how did you use it?**
Half-life = ln 2 / −ln b: the time to revert halfway. I only traded when it was ≤ 10 days on D1, because slow reversion means more cost and more risk while waiting.

**Q15. ⚠️ OU assumes constant variance. Is that true in FX?**
No; volatility clusters. A GARCH-adjusted σ or a Kalman filter would handle it better. I kept OU for robustness and interpretability, and confirmed the result separately with the model-free variance ratio.

## 3. Statistical testing

**Q16. What is the variance ratio, and why use variance?**
VR(k) = Var(k-period return) / (k · Var(1-period return)). For a random walk, variance grows linearly with time, so VR = 1. Below 1 means moves get partly reversed; above 1 means they persist (Lo & MacKinlay, 1988).

**Q17. What did you find?**
15 of 23 cross residuals had VR below 1 at 10 days (EURSEK 0.79). Gold/silver was 1.20 at 10 days and 1.48 at 20, so it trends.

**Q18. ⚠️ Are those variance ratios statistically significant?**
Honest answer: I didn't run the formal Lo–MacKinlay z-test. Many crosses are close to 1 (median 0.95), so individually some aren't significant. The evidence is the cross-sectional pattern and the gold/silver contrast. Adding the heteroskedasticity-robust z-statistic is the obvious next step.

**Q19. Why is the variance ratio a good complement to OU?**
It's model-free: no parameters are fitted. Two independent methods agreeing makes the result more robust.

## 4. The "when not to trade" gauge

**Q20. How is the gauge calculated?**
Each day: the last 480 hourly returns of 11 instruments → correlation matrix → eigenvalues → share = λ₁ / 11. The day is no-trade if the share is at or below the 33rd percentile of all previous days.

**Q21. Is this idea published?**
Yes: the Absorption Ratio (Kritzman et al., 2011), which uses the share of variance in the top eigenvectors as a measure of market fragility.

**Q22. ⚠️ Kritzman found a high absorption ratio signals danger. You found the opposite. Why?**
My universe is currencies priced in USD, so PC1 is the dollar factor. In risk-off shocks (COVID, the SNB in 2015), currencies **split** into safe havens and risky ones, so one factor explains less. In equities, crises make everything fall together, so concentration rises. The meaning of PC1 depends on the universe.

**Q23. What is the evidence that it works?**
Stretched pairs broke 7.7% of the time in low-concentration periods vs 2.3% in high (3,345 events), consistent in all 4 sub-periods and in 22 of 23 pairs. In actual trades, stop-losses hit 13.4% vs 8.0%.

**Q24. ⚠️ Is there look-ahead in the regime analysis?**
The tercile tables use full-sample cut-offs (fine for description). The live rule uses an expanding 33rd percentile, shifted one day, with a 1-year minimum history. The hourly window ends at each daily close, so it's known at decision time.

**Q25. ⚠️ Did the gauge improve profits?**
Not consistently. In 2019–26, trades on no-trade days made 0.04% per trade vs 0.17%. In 2010–18 they made **more** (0.38% vs 0.22%), because bigger moves meant bigger winners. So I present it as a **risk warning, not a profit rule**.

## 5. Backtesting and overfitting

**Q26. How did you avoid overfitting?**
- **Walk-forward:** choose parameters and crosses on 2010–18, test once on 2019–26.
- **Rolling model fits** use past data only.
- **Robustness reported across all 54 combinations** (41 positive, median Sharpe 0.36), not just the best one.

**Q27. ⚠️ You picked 13 crosses on the training data. Isn't that selection bias?**
They were selected only on training data (profitable before costs), so the test period stays clean. But choosing crosses after seeing test results (e.g. dropping NZDCHF) would be curve-fitting, which I avoided.

**Q28. Why did hourly fail but daily work?**
Hourly had an edge before costs (Sharpe ≈ +0.6) but tiny moves, so spreads ate them (after-cost Sharpe about −0.1 to −0.2, walk-forward test ≈ 0.01). Daily trades earn about 0.15–0.3% each, enough to beat spreads.

**Q29. Which costs did you model?**
- Vantage's real per-bar spreads
- commission of 0.003% per side
- swap on the more expensive side, charged 7 nights per 5 trading days

Swap turned out to be decisive: test Sharpe 0.58 swap-free vs about 0 with worst-side swap.

**Q30. ⚠️ Your swap assumption uses today's rates for 2010–2026. Is that right?**
No. Rates were near zero in 2010–21, so this overstates historical swap. The real answer lies between the two scenarios. Historical swap or interest-rate differential data would fix it.

**Q31. What other biases could exist?**
- **Data:** HistData prices are bid-only, and I filled the AUDJPY 2012 gap synthetically.
- **Survivorship:** none here (currencies don't delist).
- **Execution:** trades fill at the candle close with no slippage modelled.
- **Multiple testing:** 54 combinations were tried.

**Q32. What were the final numbers?**
- **Train (2010–18):** Sharpe 1.10, 8.1% a year
- **Test (2019–26):** Sharpe 0.58, 4.4% a year, max drawdown −13%, 239 trades, 66% win rate (swap-free)
- **Gold/silver:** Sharpe −0.61

## 6. Data engineering

**Q33. What data problems did you hit?**
- **HistData time zone:** fixed timestamps ("EST without DST"). I validated them against Yahoo and MT5 and converted to UTC.
- **MT5 server time:** New York time + 7 hours.
- **Daily candle cut-off:** candles close at 17:00 New York.
- **Gaps:** filled from the USD majors (AUDJPY = AUDUSD × USDJPY).

**Q34. How did you validate the data?**
I compared OANDA 1-minute bars with HistData: correlation 0.998, about $0.33 offset (mid vs bid), candle colour matching 91–98%.

## 7. Finance intuition

**Q35. Why do currencies all correlate positively here?**
They're all priced in USD, so dollar strength moves every one of them the same way. That's PC1.

**Q36. Why does JPY behave differently?**
It's a safe haven: in risk-off it strengthens while AUD and NZD weaken. That's PC3.

**Q37. ⚠️ AUDNZD is the most stable pair. Why not trade only that?**
Stable isn't the same as profitable. It has the lowest snap-back rate (32%), the lowest volatility (4.9%), and the spread is about 3% of its daily range. Its VR is 1.14. It drifts slowly, so it's poor value after costs.

**Q38. Why did gold/silver fail economically?**
Silver has an industrial-demand component and gold is a monetary safe haven, so their ratio follows long macro regimes (32 → 122, then 105 → 46) instead of a stable band.

## 8. Extensions and judgement

**Q39. What would you do next?**
- Lo–MacKinlay significance tests
- a Kalman or GARCH s-score
- historical swap data
- applying the gauge as a filter on other strategies
- crypto (no swap issue)
- dynamic factor count, and an out-of-sample threshold for the gauge

**Q40. ⚠️ If you could only say one thing about this project, what would it be?**
"PCA separates the common dollar-driven movement from currency-specific moves. The leftover relationships between cross pairs mostly pull back, but when the common factor weakens, those relationships break three times more often, and a simple PCA gauge built only on past data detects those periods."

**Q41. What did you learn that surprised you?**
Three things:
1. The regime effect went the opposite way to the equity literature.
2. A 68% win rate still lost money on gold/silver.
3. Costs, especially swap, mattered more than the model.

## Points to prepare well
- The **COVID/SNB result** (Q22) is your most impressive insight, so be able to explain it confidently.
- **Admit limits** on Q18, Q25 and Q30. Interviewers respect "I didn't test that, here's how I would" far more than overclaiming.
- **Know your numbers:** 49% / 72%, 15 of 23, 1.20, 7.7% vs 2.3%, 22 of 23, 69%, Sharpe 0.58.

I can also turn these into a one-page cheat sheet in the repo, or run a mock interview where I ask the questions one at a time and give feedback on your answers.

### You

Q2. Why did you standardise the returns before PCA?
Raw volatility differs a lot: silver moves 30% a year, CAD 7%. Without scaling, PCA would mostly describe silver. Standardising means PCA runs on the correlation matrix, so every instrument gets an equal vote.

but is this info not useful that which moves more?

### Claude

Yes, it is useful. We don't throw that information away; we just use it in a different step. Here's the evidence and where volatility comes back in.

## What raw (unscaled) PCA would show
I ran both versions on our 2010–2026 hourly data:

| | **Covariance PCA (no scaling)** | **Correlation PCA (scaled, what we used)** |
|---|---|---|
| PC1 share | 60.5% | 49.4% |
| PC1 loadings | **silver +0.85, gold +0.37**, every currency only +0.07 to +0.16 | every currency +0.29 to +0.36 (JPY +0.17), gold/silver +0.23 |
| What PC1 means | **"silver moved"** | **"the dollar moved"** |

Without scaling, the biggest factor is basically **silver**, just because silver's price swings are about 4× bigger. The dollar factor, the thing we actually want, gets pushed into PC2. The 60.5% looks bigger, but most of it is one noisy instrument, not a force that moves the whole market.

## Why we scale for this step
The question in this step is **"which instruments move together?"** That's about the *direction* of moves, not their *size*. A 1% silver move and a 0.25% CAD move can both be "a normal day". Scaling puts them in the same units ("how many normal moves"), so the factors show **co-movement**, not "who is loudest".

## Where "which moves more" IS used
The volatility information isn't lost. It's used where it actually matters:
1. **The residual is scaled back.** In the model, the leftover is computed in standardised units and then multiplied by each instrument's own standard deviation (`e_win = (z − z V Vᵀ) × sd` in `fx_pca_strategy.py`). So the residual is in real return units again.
2. **The s-score divides by the pair's own normal stretch (σ).** A volatile pair needs a bigger move to reach s = 2.5.
3. **Position size is set by volatility.** Each trade is sized to target 5% yearly volatility, so a volatile pair gets a smaller position.

So: **scaling for the structure (who moves with whom), volatility for the risk (how big the moves are).**

## When unscaled (covariance) PCA is the right choice
- **When all series are in the same units and their size matters**, e.g. a yield curve (all in basis points). Then the big moves are the point.
- **Portfolio risk decomposition:** if you hold real positions, you care where the **money risk** comes from, and a volatile asset really is a bigger risk. Covariance PCA answers "what drives my P&L?".

For our question, "which relationships hold and when", correlation PCA is the right tool.

**Interview answer:**
> "Volatility is useful information, but it answers a different question. Without scaling, PC1 in our data is mostly silver (loading 0.85) because it's 4× more volatile, and the dollar factor gets pushed to PC2. We scale to find co-movement, then put volatility back where it matters: the residuals are rescaled by each series' standard deviation, the s-score is normalised by each pair's own variation, and positions are volatility-targeted. If I were decomposing the risk of an actual portfolio, I'd use covariance PCA instead."

### You

Q4. Why returns and not prices?
Prices are non-stationary (EURUSD 1.08 vs gold 2,600). PCA on price levels picks up shared trends, giving spurious correlation. Returns are roughly stationary.

this was not understood

### Claude

PCA is built on correlations. If the correlations are fake, the PCA factors are fake too. Price levels produce fake correlations; returns (daily % changes) don't. Here's the idea step by step, with proof from our own data.

## 1. Price vs return
- **Price:** the level. Gold was **$1,096** in 2010 and **$4,165** in 2026.
- **Return:** the change each day, like +0.4% today, −0.2% tomorrow.

## 2. The problem: anything that trends looks related
**Example:** your height and the price of petrol both went up from 2005 to 2020. Correlate them and you get about 0.9, very "related". But petrol doesn't make you grow. They just both **trended up over time**.

Price levels do the same. Any two prices that drifted in the same direction for years look strongly correlated, even if they never move together on any single day.

## 3. Proof with completely random data
I generated 1,000 pairs of **completely unrelated** random prices (each one a random walk, with no connection at all):

| Measured on | How often they looked related |
|---|---|
| **Price levels** | **40%** of pairs showed correlation above 0.5 (fake!) |
| **Returns** | **0%** showed correlation above 0.1 (correct: they're unrelated) |

So prices told us unrelated things were related **4 times out of 10**. Returns never did.

## 4. Proof with our real data (daily, 2010–2026)

| Pair | Correlation of **prices** | Correlation of **daily returns** | What's true |
|---|---|---|---|
| CAD vs JPY | **+0.86** | +0.12 | Both fell against the dollar over the years (a shared trend), but day to day they barely move together |
| NZD vs gold | **−0.56** | **+0.36** | Prices say "opposite". Gold went up for years while NZD went down. But on a normal day **they move the same way** (both rise when the dollar falls) |

The NZD/gold case is the worst: price correlation gives **the wrong sign**. PCA on prices would put them on opposite sides of a factor, which is just false.

## 5. What "stationary" means (the word in the answer)
Something is **stationary** if its behaviour stays roughly the same over time: same average, same typical size of moves.
- **Prices aren't stationary.** Gold's "average price" in 2012 means nothing in 2026. There's no fixed level it returns to.
- **Returns are roughly stationary.** The average daily move stays near 0% and the typical size stays similar.

This matters because our model computes means, standard deviations and correlations over a 480-hour window and uses them on the next hours. That only makes sense if the numbers stay similar, which is true for returns, not for prices.

## 6. The other reason: units
EURUSD is about 1.10 and gold about $4,000. Returns put everything in the same unit (% change), so the numbers are comparable. Scaling (from Q2) then equalises the size of moves.

## Better interview answer
> "PCA works on correlations, and correlations of price levels are misleading: two prices that both trended for years look correlated even if they never move together day to day. That's called spurious correlation. In our data, CAD and JPY prices correlate 0.86 but their daily returns only 0.12, and NZD vs gold even flips sign, −0.56 in prices vs +0.36 in returns. In a simulation, 40% of completely unrelated random walks showed price correlation above 0.5. Returns are roughly stationary (stable mean and variance), so their correlations reflect real co-movement, and statistics from a past window remain valid for the next one."

**If they push:** "But you do use prices for the s-score?"
> "Not raw prices. I take the **cumulative sum of the PCA residual returns** of the last 120 days within each window. That's built from returns after removing the common factors, and the OU fit checks that it actually mean-reverts (0 < b < 1) before I use it."

### You

how do I share this chat?
