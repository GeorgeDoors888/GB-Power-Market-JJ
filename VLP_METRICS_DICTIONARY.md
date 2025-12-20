# VLP Metrics Dictionary

**Last Updated:** December 18, 2025
**Purpose:** Comprehensive definitions for all Virtual Lead Party (VLP) dashboard metrics
**Audience:** Trading desk, analysts, strategy team

---

## 📊 Core Price Metrics

### Avg Accept (Average Acceptance Price, £/MWh)
**What it is:** Arithmetic mean of all acceptance prices in the period, regardless of volume.

**Why it matters:** Your "headline" BM execution price. If you're getting accepted at high prices (offers) or low/negative prices (bids), that's the raw edge you're trying to capture.

**Formula:**
```
Avg Accept = SUM(acceptance_price) / COUNT(acceptances)
```

**Typical values:**
- Normal market: £40-80/MWh
- High-price events: £100-200/MWh
- Extreme events: £500-9,999/MWh

**Interpretation:**
- Rising trend → BM getting more expensive (opportunity for offer strategies)
- Falling trend → BM getting cheaper (opportunity for bid strategies)
- High variance → volatile market (more VLP opportunities)

---

### Vol-Wtd (Volume-Weighted Acceptance Price, £/MWh)
**What it is:** Weighted average of acceptance prices, where each price is multiplied by its volume.

**Why it matters:** Simple average can lie if big volumes clear at different prices. Volume-weighted is what drives real £ P&L. A single 100MW acceptance at £50/MWh has more impact than ten 1MW acceptances at £200/MWh.

**Formula:**
```
Vol-Wtd = SUM(price × volume) / SUM(volume)
       = Total Revenue / Total MWh
```

**Typical values:**
- Usually within ±10% of Avg Accept
- Can diverge significantly in mixed-volume markets
- Example: Avg Accept £100/MWh, Vol-Wtd £60/MWh → most volume cleared cheap

**Interpretation:**
- Vol-Wtd > Avg Accept → Large volumes at high prices (good for offers)
- Vol-Wtd < Avg Accept → Large volumes at low prices (many small high-price actions)
- Gap >20% → Volume concentration at specific price points

---

### Mkt Index (Market Index Reference Price, £/MWh)
**What it is:** Wholesale market benchmark price, typically from:
- MID (Market Index Data) - within-day spot
- APX/N2EX - day-ahead auction
- Curve reference (e.g., Month+1)

**Why it matters:** VLPs aren't just "BM-only"; you compare BM prices to a wholesale reference to see if BM is rich/cheap versus the market you could hedge against. Essential for deciding whether to execute virtual actions or stay flat.

**Data source:** `bmrs_mid` table (Market Index Data)

**Typical values:**
- Aligned with Sys Buy/Sell: £40-80/MWh
- Can spike to £200+ during scarcity
- Can go negative during surplus renewables

**Interpretation:**
- BM > Mkt Index → BM paying premium (offer opportunity)
- BM < Mkt Index → BM at discount (bid opportunity)
- Spread >£20/MWh → Strong arbitrage signal

---

### Sys Buy / Sys Sell (System Cash-Out Prices, £/MWh)
**What it is:** The imbalance settlement prices charged/paid to parties for being short/long.

**Post-P305 (Nov 2015):** Single pricing means Sys Buy = Sys Sell (no spread).

**Why it matters:**
- **Risk yardstick:** What's the system price environment?
- **Sanity check:** BM acceptances tend to relate to the stack that drives system price
- **Benchmark:** Are you being paid more/less than system price?

**Data source:** `bmrs_costs` table (formerly DISBSAD, now DISEBSP)

**Typical values:**
- Normal: £40-80/MWh
- Tight system (low wind/high demand): £100-200/MWh
- Long system (high wind/low demand): £10-40/MWh
- Scarcity events: £500-6,000/MWh

**Interpretation:**
- High system price → Tight system (offer value high)
- Low system price → Long system (bid value high)
- Volatile system price → VLP opportunity window

---

## 📈 Spread Metrics (The Real VLP Signals)

### BM – MID (Balancing Mechanism vs Market Index Spread, £/MWh)
**What it is:** Difference between your BM acceptance prices and the wholesale market index.

**Formula:**
```
BM - MID = (Vol-Wtd Acceptance Price) - (Market Index Price)
```

**Why it matters:** Tells you if BM acceptances are better or worse than wholesale. This is core for deciding whether virtual actions are worth pursuing and how aggressively to price. If BM-MID is positive and large, you can make money by offering into BM and hedging in wholesale.

**Typical values:**
- Normal: ±£5-10/MWh
- Opportunity window: >£20/MWh
- Extreme events: £50-500/MWh

**Interpretation:**
- Positive → BM paying premium vs wholesale (offer strategy)
- Negative → BM at discount vs wholesale (bid strategy)
- Zero → No arbitrage opportunity (stay flat)

**Strategy implications:**
- BM-MID >£20 → Aggressive offer pricing
- BM-MID £10-20 → Moderate offer sizing
- BM-MID <£5 → Preserve cycles, wait for better spreads

---

### BM – SysBuy / BM – SysSell (BM vs Cash-Out Spread, £/MWh)
**What it is:** Difference between your acceptance prices and the system imbalance price.

**Formula:**
```
BM - SysBuy = (Vol-Wtd Acceptance Price) - (System Buy Price)
BM - SysSell = (Vol-Wtd Acceptance Price) - (System Sell Price)
```

**Why it matters:**
- **Strategy selection:** When BM is paying a premium above cash-out
- **Regime detection:** Tight system vs long system
- **P&L explanation:** Did you make money because system price moved, or because your actions cleared at a premium?

**Typical values:**
- Normal: ±£5-15/MWh
- Stacked actions: Can be £50-100/MWh above system price
- STOR/CADL flags: Often at system price (£0 spread)

**Interpretation:**
- BM > SysBuy → Your offers clearing above imbalance price (extracting premium)
- BM < SysBuy → Your bids clearing below imbalance price (cheap energy)
- Large spread → You're marginal in the stack (price-setting)

---

## 💰 Revenue & Performance Metrics

### VLP £/MWh (VLP Margin Per MWh, £/MWh)
**What it is:** Your realised profit margin per MWh after applying your pricing model and accounting for costs/fees.

**Formula:**
```
VLP £/MWh = (Acceptance Revenue - Hedge Costs - Fees) / Total MWh
          = Net P&L / Volume
```

**Why it matters:** It's the simplest KPI for "is the strategy working?" Tracks your edge per unit of execution.

**Typical values:**
- Target: £10-20/MWh (sustainable)
- High-value periods: £30-50/MWh
- Extreme events: £100+/MWh
- Below £5/MWh → Strategy not profitable

**Interpretation:**
- Rising → Strategy improving (better pricing, better spread capture)
- Falling → Market tightening or strategy degradation
- Negative → Losing money (stop trading or adjust pricing)

---

### VLP Rev (Total VLP Revenue, £)
**What it is:** Total £ revenue over the period.

**Formula:**
```
VLP Rev = SUM(MWh executed × VLP £/MWh)
        = Total Volume × Average Margin
```

**Why it matters:** What you report internally (and what determines if the desk should scale or stop). Absolute revenue metric for P&L tracking.

**Typical values:**
- Daily: £1k-50k (depends on capacity and strategy)
- Weekly: £10k-500k
- Monthly: £50k-2M
- Oct 17-23 high event: £79.83/MWh avg × large volume

**Interpretation:**
- Track vs budget/forecast
- Seasonality patterns (winter>summer for VLP)
- Event-driven spikes (wind lulls, cold snaps)

---

### Supp Comp / Daily Comp (Supplementary Compensation / Daily Adjustments, £)
**What it is:**
- **Supp Comp:** Supplementary compensation/adjustments for missing matches, late data, corrections
- **Daily Comp:** Daily compounding/aggregation depending on internal naming

**Why it matters:** VLP P&L often needs adjustment lines. You track these so you don't mistake data artefacts for alpha.

**Common adjustments:**
- Missing BOALF→BOD matches (estimated revenue)
- Late settlement data corrections
- Rule-based adders (e.g., minimum price floors)
- Data quality patches

**Interpretation:**
- High Supp Comp → Data quality issues or matching failures
- Should be <10% of VLP Rev
- If >20% → Investigate data pipeline

---

### Net Spread (Net Strategy Margin After Adjustments, £/MWh)
**What it is:** Your realised edge after supplementary adjustments.

**Formula:**
```
Net Spread = (VLP Rev + Supp Comp) / Total MWh
          = True Strategy Margin
```

**Why it matters:** Separates "true strategy margin" from "patches / reconciliation". This is your actual performance metric.

**Typical values:**
- Should be close to VLP £/MWh if data quality is good
- Gap >£5/MWh → Significant adjustments being made

**Interpretation:**
- Net Spread > VLP £/MWh → Adjustments adding value (conservative pricing)
- Net Spread < VLP £/MWh → Adjustments reducing value (data issues)
- Track over time to ensure consistency

---

## 🔄 Market Condition Metrics

### Contango (Forward Curve Shape Metric, £/MWh)
**What it is:** Difference between forward prices and spot prices. Positive = contango (forward > spot), negative = backwardation (spot > forward).

**Formula:**
```
Contango = Forward Price (e.g., Month+1) - Spot Price (e.g., Within-Day)
```

**Why it matters:** For VLPs it's a regime indicator. When the forward curve is in contango/backwardation, the economics of hedging vs spot exposure and the expected BM/wholesale relationship can change.

**Typical values:**
- Contango: +£2-10/MWh (normal)
- Backwardation: -£5-15/MWh (tight near-term)
- Flat: ±£2/MWh (balanced market)

**Interpretation:**
- Strong contango → Market expects tightness ahead (hedge forward)
- Backwardation → Near-term shortage (stay exposed to spot)
- For VLP: Affects hedge timing and pricing strategy

---

### Imb Index (Imbalance Index, %)
**What it is:** Percentage measure of system imbalance severity or frequency.

**Formula:**
```
Imb Index = (System Imbalance Volume / Total System Demand) × 100
         or
          = (Count of High Imbalance Periods / Total Periods) × 100
```

**Why it matters:** High imbalance → More BM actions needed → More VLP opportunities. Low imbalance → System balanced → Fewer actions, lower spreads.

**Typical values:**
- Low: 0-2% (calm system)
- Moderate: 2-5% (normal volatility)
- High: >5% (stressed system)
- Extreme: >10% (scarcity or surplus events)

**Interpretation:**
- Rising → More BM activity expected (VLP opportunity)
- Falling → System stabilizing (reduce exposure)
- Spike → Event-driven opportunity (wind drop, interconnector trip)

---

### Volatility (Price Volatility, £/MWh StdDev or %)
**What it is:** Standard deviation or coefficient of variation of BM prices or system prices.

**Formula:**
```
Volatility = STDEV(prices)
        or
          = STDEV(prices) / AVG(prices) × 100  (coefficient of variation %)
```

**Why it matters:** High volatility = high risk but also high VLP opportunity. Low volatility = stable market, smaller spreads, less opportunity for arbitrage.

**Typical values:**
- Low: <£10/MWh (stable market)
- Moderate: £10-30/MWh (normal)
- High: >£30/MWh (volatile market, VLP opportunity)
- Extreme: >£100/MWh (crisis or scarcity)

**Interpretation:**
- High volatility → More aggressive pricing, wider spreads
- Low volatility → Conservative sizing, tight spreads
- Track 7-day rolling volatility for regime detection

---

## ⚡ Energy & Efficiency Metrics

### BM Energy (Total BM Acceptance Energy, MWh)
**What it is:** Total megawatt-hours of accepted balancing mechanism actions.

**Formula:**
```
BM Energy = SUM(acceptance volumes in MWh)
```

**Why it matters:** Volume is the denominator in all margin calculations. More volume = more revenue opportunity (if margins hold). Track to ensure you're not over/under-executing vs capacity.

**Typical values:**
- Daily: 50-500 MWh (depends on capacity)
- Weekly: 500-5,000 MWh
- Monthly: 2,000-20,000 MWh
- Oct 17-23 event: Huge volumes at high prices

**Interpretation:**
- Rising volume + rising margin → Scale up
- Rising volume + falling margin → Market getting competitive
- Falling volume → Less opportunity or capacity constraints

---

### Eff Rev (Effective Revenue, £/MWh or % of potential)
**What it is:** Actual revenue achieved as percentage of theoretical maximum, or revenue per MWh accounting for all costs.

**Formula:**
```
Eff Rev = (Actual Revenue / Theoretical Max Revenue) × 100
     or
        = (Revenue - All Costs) / MWh
```

**Why it matters:** Measures execution quality. Are you capturing the available spread, or leaving money on the table? Tracks slippage, timing losses, and operational inefficiency.

**Typical values:**
- Excellent: >80% of theoretical
- Good: 60-80%
- Needs improvement: <60%
- In £/MWh: Should be close to VLP £/MWh

**Interpretation:**
- High Eff Rev → Good execution, capturing spreads
- Low Eff Rev → Slippage, poor timing, or conservative pricing
- Track vs VLP £/MWh to identify inefficiencies

---

### Coverage (Data Coverage %, or Match Rate %)
**What it is:** Percentage of acceptances that have matched price data for revenue calculation.

**Formula:**
```
Coverage = (Acceptances with prices / Total acceptances) × 100
```

**Why it matters:** If coverage is low, your revenue calculations are incomplete. You're flying blind on actual P&L. High coverage = trustworthy data.

**Data sources:**
- BOALF→BOD matching: 85-95% coverage (current method)
- EBOCF cashflows: ~95% coverage (recommended)
- Hybrid approach: 98% coverage (best)

**Typical values:**
- Target: >95%
- Acceptable: 90-95%
- Problematic: <90%
- Current (hybrid): 98%

**Interpretation:**
- Coverage <95% → Data quality issues, investigate
- Falling coverage → API issues or matching logic broken
- 100% coverage impossible (some actions unmatchable)

---

## 🎯 Using the Metrics Together

### Daily Trading Decisions

**Pre-Market Setup:**
1. Check **Contango** - Forward curve shape
2. Review **Volatility** - Expected market stability
3. Assess **Imb Index** - Recent imbalance trends

**Intraday Execution:**
4. Monitor **BM - MID** - Current arbitrage spread
5. Watch **Sys Buy/Sell** - System tightness
6. Track **Avg Accept** - Real-time price levels

**Post-Trade Analysis:**
7. Calculate **VLP £/MWh** - Margin achieved
8. Review **Eff Rev** - Execution quality
9. Check **Coverage** - Data completeness

### Weekly Performance Review

**Volume & Revenue:**
- **BM Energy** - Total volume executed
- **VLP Rev** - Total revenue achieved
- **Net Spread** - True margin after adjustments

**Quality Metrics:**
- **Vol-Wtd vs Avg Accept** - Volume concentration
- **Eff Rev** - Execution effectiveness
- **Coverage** - Data reliability

**Market Context:**
- **Volatility** trend - Market regime
- **Imb Index** trend - Opportunity level
- **BM - MID** average - Spread environment

---

## 📋 Common Dashboard Issues

### Why Zeros Appear

If you see metrics showing **0** when Market Index and System Prices have values (e.g., 81.65, 40.03):

**Likely causes:**
1. **No acceptances in selected window** - No executed virtual actions
2. **Join/match step didn't populate** - Missing BOALF→price mapping
3. **Coverage issues** - Acceptances exist but no price data
4. **Date filter mismatch** - Acceptances outside selected period

**How to diagnose:**
```sql
-- Check if acceptances exist
SELECT COUNT(*) FROM bmrs_boalf
WHERE settlementDate >= '2025-12-01';

-- Check if prices exist
SELECT COUNT(*) FROM boalf_with_ebocf_hybrid
WHERE settlementDate >= '2025-12-01';

-- Check coverage
SELECT
  (SELECT COUNT(*) FROM boalf_with_ebocf_hybrid WHERE settlementDate >= '2025-12-01') * 100.0 /
  (SELECT COUNT(*) FROM bmrs_boalf WHERE settlementDate >= '2025-12-01') as coverage_pct;
```

---

## 🔗 Related Documentation

- **BOALF_PRICE_DERIVATION_COMPLETE.md** - Technical guide to price derivation
- **STOP_DATA_ARCHITECTURE_REFERENCE.md** - Data table schemas
- **PROJECT_CONFIGURATION.md** - BigQuery setup
- **ENHANCED_BI_ANALYSIS_README.md** - Dashboard analysis guide

---

**Last Updated:** December 18, 2025
**Maintained by:** George Major (george@upowerenergy.uk)
**Status:** ✅ Production reference
