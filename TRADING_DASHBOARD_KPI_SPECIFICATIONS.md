# Trading Dashboard KPI Specifications
# Complete Definitions for CHP + Battery Trading Operations

**Generated:** 2025-12-29
**Purpose:** Authoritative KPI definitions for Live Dashboard v2 enhancements
**Context:** CHP + Battery trading (BM/wholesale/imbalance/ancillary)

---

## Table of Contents

1. [KPI Dictionary - Market Signals](#1-kpi-dictionary---market-signals)
2. [KPI Dictionary - BM Activity](#2-kpi-dictionary---bm-activity)
3. [KPI Dictionary - Asset Readiness](#3-kpi-dictionary---asset-readiness)
4. [KPI Dictionary - Financial Outcomes](#4-kpi-dictionary---financial-outcomes)
5. [KPI Dictionary - Risk Metrics](#5-kpi-dictionary---risk-metrics)
6. [Dashboard Layout Specification](#6-dashboard-layout-specification)
7. [Implementation Formulas](#7-implementation-formulas)

---

## 1. KPI Dictionary - Market Signals

### Real-time Imbalance Price

**Definition:** The imbalance price applied to the current Settlement Period.

**Formula:**
```
If single pricing: Price = SSP = SBP
Else:
  Long → SSP
  Short → SBP
```

**Unit:** £/MWh
**Source:** BMRS `bmrs_costs` or `bmrs_costs_iris`
**Update Frequency:** Every 30 minutes (per SP)

**Notes:**
- Do NOT label SSP=SBP as "balanced" — indicates single-price conditions (often stress)
- Since Nov 2015 (P305): SSP = SBP in all periods

---

### Single-Price Frequency

**Definition:** Percentage of Settlement Periods where SSP = SBP.

**Formula:**
```
(# SPs where SSP = SBP) / (Total SPs) × 100%
```

**Unit:** %
**Lookback:** 7d / 30d
**Use:** Battery risk asymmetry indicator

**Notes:**
- Higher frequency → more single-price periods → lower risk spread
- Post-P305 (Nov 2015): Always 100% (retained as historical reference)

---

### Rolling Mean Price (7d / 30d)

**Definition:** Rolling average of imbalance price over lookback window.

**Formula:**
```sql
AVG(imbalance_price) OVER (
  ORDER BY settlementDate, settlementPeriod
  ROWS BETWEEN N PRECEDING AND CURRENT ROW
)
```

**Unit:** £/MWh
**Windows:** 7d (336 SPs), 30d (1440 SPs)

**Interpretation:**
- Rising mean → tightening market
- Falling mean → loosening market
- Compare to current price for deviation %

---

### Price Volatility (StdDev)

**Definition:** Standard deviation of imbalance price over lookback window.

**Formula:**
```sql
STDDEV(imbalance_price) OVER (
  ORDER BY settlementDate, settlementPeriod
  ROWS BETWEEN N PRECEDING AND CURRENT ROW
)
```

**Unit:** £/MWh
**Interpretation:** Battery optionality ↑ as volatility ↑

**Alert Thresholds:**
- Low: < £5/MWh (low arbitrage opportunity)
- Normal: £5-15/MWh
- High: £15-30/MWh (high arbitrage)
- Extreme: > £30/MWh (system stress)

---

### Price Regime

**Definition:** Categorical classification of price environment.

**Rules:**
```
Low:      < £20/MWh
Normal:   £20–£80/MWh
High:     £80–£150/MWh
Scarcity: > £150/MWh
```

**Unit:** Category (enum)
**Use:** Strategy selection (charge / discharge / hold)

**Strategy Map:**
- **Low:** Charge aggressively (if SoC < 80%)
- **Normal:** Optimize based on forecast
- **High:** Discharge aggressively (if SoC > 20%)
- **Scarcity:** Full discharge + BM offers

---

## 2. KPI Dictionary - BM Activity

### Dispatch Intensity

**Definition:** Rate at which BM acceptances occur.

**Formula:**
```
Total acceptances / hour
```

**Unit:** acceptances/hour
**Companion KPIs:**
- % of SPs with ≥1 acceptance
- Median accepted MW

**Interpretation:**
- Low (< 20/hr): Quiet market
- Normal (20-50/hr): Standard activity
- High (50-100/hr): Active balancing
- Extreme (> 100/hr): System stress

---

### Acceptance Energy-Weighted Price (EWAP)

**Definition:** Average price weighted by accepted energy.

**Formula:**
```
Σ(accepted_MW × 0.5 × price) / Σ(accepted_MW × 0.5)
```

**Unit:** £/MWh

**Important:**
- If no acceptances → EWAP = NULL (not zero)
- Separate by BID/OFFER for directional insight
- Use `bmrs_boalf_complete` for individual acceptance prices

**Data State Flags:**
- `valid`: Sufficient data for calculation
- `no_activity`: Zero acceptances in period
- `insufficient_volume`: < threshold MW accepted

---

### SO-Flag Rate

**Definition:** Share of acceptances marked as SO-Flag (system events).

**Formula:**
```
(# acceptances with soFlag=TRUE) / (Total acceptances) × 100%
```

**Unit:** %
**Interpretation:**
- High SO-flag rate → network constraints (not pure market)
- Low SO-flag rate → market-driven balancing

---

## 3. KPI Dictionary - Asset Readiness

### State of Charge (SoC)

**Definition:** Current battery energy level as percentage of capacity.

**Formula:**
```
(Current Energy MWh / Max Capacity MWh) × 100%
```

**Unit:** %
**Alert Thresholds:**
- Critical low: < 10%
- Low: 10-20%
- Optimal: 20-80%
- High: 80-90%
- Critical high: > 90%

---

### Headroom / Footroom

**Definition:** Available power capability in each direction.

**Formulas:**
```
Headroom (MW) = Max Export Power - Current Output
Footroom (MW) = Max Import Power - Current Output
```

**Unit:** MW
**Use:** Dispatch constraint checking

---

### Equivalent Full Cycles (EFC)

**Definition:** Cumulative battery degradation metric.

**Formula:**
```
EFC = Σ(|ΔSoC| / 200%)
```

**Unit:** Cycles
**Lookback:** Daily / Weekly / Lifetime

**Example:**
- 100% → 50% → 100% = 1.0 EFC
- 80% → 60% → 70% = 0.15 EFC

---

### Cycle Value (£/cycle)

**Definition:** Profit per equivalent full cycle.

**Formula:**
```
(Total Profit £) / (Total EFC) = £/cycle
```

**Unit:** £/cycle
**Benchmark:** Compare to degradation cost (typically £50-200/cycle)

**Decision Rule:**
- If Cycle Value > Degradation Cost → Dispatch
- Else → Hold for better opportunity

---

### CHP Spark Spread

**Definition:** Gross margin from electricity generation minus fuel/carbon costs.

**Formula:**
```
Spark Spread = (Electricity Price £/MWh) -
               (Gas Price £/MWh / Efficiency) -
               (Carbon Price £/tCO2 × Emission Factor)
```

**Unit:** £/MWh
**Threshold:** Spark Spread > £0 → Run CHP

**Typical Values:**
- Negative: Don't run (unless heat-led)
- £0-10: Marginal
- £10-30: Good
- > £30: Excellent

---

### Heat Constraint Index

**Definition:** Percentage of time CHP output constrained by heat demand.

**Formula:**
```
(# hours heat-limited) / (Total hours) × 100%
```

**Unit:** %
**Interpretation:**
- Low (< 20%): Electrically optimizable
- Medium (20-50%): Partial constraint
- High (> 50%): Heat-led operation

---

## 4. KPI Dictionary - Financial Outcomes

### Pay-as-Bid Revenue (BM Acceptances)

**Definition:** Revenue from BM acceptances at acceptance prices.

**Formula:**
```
Σ(accepted MW × 0.5h × acceptance price £/MWh)
```

**Unit:** £
**Source:** `bmrs_boalf_complete` (with prices)
**Lookback:** 24h / 7d / 30d

**Sign Convention:**
- Positive accepted MW + positive price = revenue (discharge)
- Negative accepted MW + negative price = revenue (charge)

---

### Imbalance Settlement Outcome

**Definition:** What settlement (P114) says you paid/received for being long/short.

**Formula:**
```
(Metered Position - Contracted Position) × Imbalance Price
```

**Unit:** £
**Source:** P114 settlement files
**Note:** Not available immediately (days/weeks lag)

---

### Total Net Value

**Definition:** Combined value from all revenue streams minus costs.

**Formula:**
```
Total Value = Pay-as-bid Revenue +
              Wholesale Revenue +
              Imbalance Settlement ±
              Ancillary Revenue -
              Fuel Cost -
              Carbon Cost -
              Degradation Cost
```

**Unit:** £
**Lookback:** 24h / 7d / 30d

---

### Value per MWh Throughput (Battery)

**Definition:** Normalized battery profitability metric.

**Formula:**
```
Total Battery Profit £ / Total MWh Throughput
```

**Unit:** £/MWh
**Benchmark:** > £5/MWh = good performance

---

### Value per Running Hour (CHP)

**Definition:** Normalized CHP profitability metric.

**Formula:**
```
Total CHP Profit £ / Total Running Hours
```

**Unit:** £/hour
**Benchmark:** Compare to spark spread × rated output

---

## 5. KPI Dictionary - Risk Metrics

### Worst SP Loss (Tail Risk)

**Definition:** Largest single Settlement Period loss in lookback window.

**Formula:**
```
MIN(SP_profit) over lookback period
```

**Unit:** £
**Lookback:** 7d / 30d
**Alert:** Flag if exceeds threshold (e.g., < -£500)

---

### Imbalance Tail Exposure (95th Percentile)

**Definition:** Loss at 95th percentile of worst outcomes.

**Formula:**
```
PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SP_profit)
```

**Unit:** £
**Interpretation:** "95% of the time, worst loss is no worse than X"

---

### Forecast Error (MAPE)

**Definition:** Mean Absolute Percentage Error of key forecasts.

**Formula:**
```
MAPE = (1/n) × Σ(|Actual - Forecast| / Actual) × 100%
```

**Unit:** %
**Apply to:**
- Site load forecast
- CHP output forecast
- SoC trajectory forecast

**Benchmark:**
- Excellent: < 5%
- Good: 5-10%
- Acceptable: 10-20%
- Poor: > 20%

---

### Missed Delivery Count

**Definition:** Number of periods where position ≠ ability to deliver.

**Examples:**
- Sold discharge but battery empty
- Contracted generation but CHP unavailable

**Unit:** Count (events)
**Alert:** Any occurrence = critical issue

---

## 6. Dashboard Layout Specification

### Block 1: Market State "Now" (A5:D12)

4 KPI cards with sparklines:

1. **Real-time Imbalance Price**
   - Large number: £80.08/MWh
   - Sparkline: price last 24h

2. **Pricing Mode**
   - Single-price (SSP=SBP) / Dual-price
   - Sparkline: single-price frequency 30d

3. **Volatility (30d)**
   - StdDev value: £15.23/MWh
   - Sparkline: volatility trend 30d

4. **Price Regime**
   - Category: Low/Normal/High/Scarcity
   - Color-coded background

---

### Block 2: System Operator Activity (E5:H12)

4 KPI cards:

1. **Dispatch Intensity**
   - Acceptances/hour: 56.0/hr
   - % active SPs: 10.4%

2. **Acceptance EWAP**
   - £/MWh: £82.50
   - Sparkline: EWAP 24h

3. **SO-Flag Rate**
   - %: 15.2%

4. **Median Acceptance Size**
   - MW: 25.3 MW

---

### Block 3: Trading Outcomes (I5:L12)

4 KPI cards:

1. **Pay-as-bid £ (24h)**
   - £1,234.56
   - Sparkline: £ per SP last 24h

2. **Imbalance Settlement £ (24h)**
   - £567.89 (if available)

3. **Total Net £ (24h)**
   - £1,802.45
   - Sparkline: cumulative £ over 7d

4. **Worst SP Loss (30d)**
   - -£89.12 (tail risk)

---

### Block 4: Battery Panel (A14:F22)

1. **SoC (%):** 65%
2. **Headroom (MW):** 10 MW
3. **Footroom (MW):** 10 MW
4. **Throughput (MWh, 24h):** 120 MWh
5. **EFC (7d):** 3.5 cycles
6. **Cycle Value (£/cycle):** £85.50

---

### Block 5: CHP Panel (G14:L22)

1. **Output (MW, now):** 5.2 MW
2. **Spark Spread (£/MWh):** £18.30
3. **Heat Constraint (%):** 35%
4. **Starts/Stops (7d):** 12
5. **Runtime Hours (7d):** 96.5 hrs

---

### Block 6: 30-Day Market Dynamics (A24:L40)

Table format (not paragraphs):

| KPI | 30d Value | 30d High | 30d Low | Sparkline |
|-----|-----------|----------|---------|-----------|
| Daily Avg Price | £72.23 | £149.95 | -£17.03 | ▁▂▃▅▇█ |
| Daily Price Range | £166.98 | - | - | ▃▅▇▆▄ |
| Daily Volatility | £10.35 | - | - | ▂▃▅▆▅▃ |
| Total Acceptances/Day | 1,344 | - | - | ▄▅▆▇▆▅ |
| Total £/Day | £18.2k | - | - | ▂▅▇█▆▃ |

---

## 7. Implementation Formulas

### Google Sheets Formulas

**Real-time Imbalance Price:**
```
=INDEX(Data_Hidden!C:C, MATCH(MAX(Data_Hidden!A:A), Data_Hidden!A:A, 0))
```

**7-Day Average:**
```
=AVERAGE(FILTER(Data_Hidden!C:C, Data_Hidden!A:A >= TODAY()-7))
```

**Volatility (30d):**
```
=STDEV(FILTER(Data_Hidden!C:C, Data_Hidden!A:A >= TODAY()-30))
```

**Price Regime:**
```
=IFS(L13<20,"Low", L13<80,"Normal", L13<150,"High", L13>=150,"Scarcity")
```

**Dispatch Intensity:**
```
=COUNTIF(Data_Hidden!D:D, ">0") / ((NOW()-MIN(Data_Hidden!A:A))*24)
```

---

### BigQuery Queries

**Market Signals (Last 24h):**
```sql
SELECT
  MAX(imbalance_price) as current_price,
  AVG(imbalance_price) as avg_24h,
  STDDEV(imbalance_price) as volatility_24h,
  COUNT(DISTINCT CASE WHEN ssp = sbp THEN settlement_period END) / COUNT(*) as single_price_freq
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs_iris`
WHERE settlementDate >= CURRENT_DATE() - 1
```

**Pay-as-Bid Revenue (7d):**
```sql
SELECT
  DATE(acceptanceTime) as date,
  SUM(acceptanceVolume * acceptancePrice * 0.5) as revenue_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE validation_flag = 'Valid'
  AND acceptanceTime >= CURRENT_DATE() - 7
GROUP BY date
ORDER BY date
```

**Worst SP Loss (30d):**
```sql
SELECT
  MIN(sp_profit) as worst_sp_loss
FROM (
  SELECT
    settlementDate,
    settlementPeriod,
    SUM(revenue) as sp_profit
  FROM your_profit_table
  WHERE settlementDate >= CURRENT_DATE() - 30
  GROUP BY settlementDate, settlementPeriod
)
```

---

## Appendix: Alert Thresholds

### Critical Alerts (Immediate Action)

| Metric | Threshold | Action |
|--------|-----------|--------|
| SoC | < 10% or > 90% | Rebalance immediately |
| Imbalance Price | > £200/MWh | Consider emergency discharge |
| Missed Delivery | Any occurrence | Investigate compliance |
| Forecast Error | > 20% MAPE | Recalibrate model |

### Warning Alerts (Review)

| Metric | Threshold | Action |
|--------|-----------|--------|
| Volatility | > 2× 30d avg | Review strategy |
| SO-Flag Rate | > 50% | Network stress - adjust offers |
| Cycle Value | < Degradation Cost | Reduce cycling |
| Spark Spread | < £0 for 4hrs | Shut down CHP (unless heat-led) |

---

## Document Maintenance

**Last Updated:** 2025-12-29
**Author:** George Major
**Version:** 1.0

**Implementation Status:**
- [ ] Task 5: Dashboard KPI enhancements (not started)
- Uses data from Task 1 (completed): BigQuery stats updated
- Requires Task 2 (in progress): Test sheet for safe implementation

**Next Steps:**
1. Complete Task 2 (Test sheet creation)
2. Implement KPIs in Test sheet first
3. Validate formulas with live data
4. Deploy to Live Dashboard v2 after testing
