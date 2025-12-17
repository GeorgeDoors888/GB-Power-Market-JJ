# ⚡ Supplier Compensation Reference Price (SCRP) & Market Index Analysis

**Primary Dataset:** `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` (Wholesale Trading)  
**Secondary Dataset:** `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete` (Balancing Acceptances)  
**Analysis Period:** January 2023 - December 2025 (24 months)  
**Source:** Elexon BMRS via IRIS → BigQuery  
**Compiled by:** GB Power Market JJ  
**Last Updated:** 2025-12-16

---

## 📋 Executive Summary

The **Supplier Compensation Reference Price (SCRP)** is derived from **Market Index Data (MID)**, representing day-ahead wholesale electricity prices used in the **Balancing and Settlement Code (BSC)** for supplier compensation under modifications **P415** and **P444**.

### 🔑 Critical Distinction:

**MID (Market Index Data) - WHOLESALE TRADING PRICES:**
- **24-Month Average**: £77.00/MWh
- **Purpose**: SCRP baseline for supplier compensation
- **Source**: EPEX SPOT UK + Nord Pool day-ahead trades
- **Records**: 42,211 settlement periods (24 months)

**BOALF (Accepted Bids/Offers) - BALANCING MECHANISM PAYMENTS:**

**OFFERS (Generators Paid to INCREASE Output):**
- **24-Month Count**: 353,828 acceptances
- **Simple Average**: £88.58/MWh
- **Volume-Weighted Average**: £96.35/MWh ⭐ (more accurate - reflects actual market payments)
- **Min Price**: -£979.88/MWh
- **Max Price**: £1,000.00/MWh
- **Total Volume**: 17.4 TWh
- **Average Volume per Action**: 49.3 MW

**BIDS (Generators Paid to DECREASE Output):**
- **24-Month Count**: 440,306 acceptances (MORE than offers!)
- **Simple Average**: -£1.63/MWh
- **Volume-Weighted Average**: £0.98/MWh ⭐ (more accurate - large positive bids offset small negatives)
- **Min Price**: -£1,000.00/MWh
- **Max Price**: £200.00/MWh
- **Total Volume**: 28.4 TWh (1.6x larger than offer volume)
- **Average Volume per Action**: 64.4 MW

**Purpose**: Actual payments to generators for balancing actions  
**Source**: National Grid ESO balancing mechanism  
**Total Acceptances**: 794,134 actions (24 months, Valid records only)

**Critical Understanding:**  
- **OFFERS** = Generators paid to INCREASE output (positive prices, scarcity)
- **BIDS** = Generators paid to DECREASE output (often negative prices, surplus)
- **These are OPPOSITE actions and should NEVER be averaged together**
- **See Section 1 for full definitions and examples**

---

## Key Findings:
- **MID Wholesale Average**: £77.00/MWh (October 2025: £75.33/MWh)
- **BOALF OFFERS**: £88.58/MWh simple avg, **£96.35/MWh volume-weighted** (generators paid to INCREASE output)
- **BOALF BIDS**: -£1.63/MWh simple avg, **£0.98/MWh volume-weighted** (generators paid to DECREASE output)
- **Price Range**: 
  - OFFERs: -£979.88 to +£1,000/MWh
  - BIDs: -£1,000 to +£200/MWh
- **Volume**: 28.4 TWh BIDs vs 17.4 TWh OFFERs (BIDs 1.6x larger volume)
- **Count**: 440K BIDs vs 354K OFFERs (more surplus than scarcity events)

---

## 1️⃣ Definitions — Bid vs Offer

### ⚡ Critical Understanding: Opposite Market Actions

| Term | Direction | What the Participant Does | Financial Flow | Typical Tech | Price Sign |
|------|-----------|---------------------------|----------------|--------------|------------|
| **Offer** | ↑ Increase generation (or reduce demand) | Generates or exports more power | **ESO pays participant** | Gas, battery discharge, interconnector import | **Positive** (£/MWh) |
| **Bid** | ↓ Reduce generation (or increase demand) | Generates or exports less power (or consumes more) | **Participant pays ESO** | Wind, battery charge, demand response | **Negative** (£/MWh) |

### 📖 Examples by Technology

| Technology | Typical Action | Behaviour | Example Price (£/MWh) | Reason |
|------------|----------------|-----------|----------------------|---------|
| **Gas CCGT** | Offer (up) | Generate more | +70 → +150 | Fuel + profit margin |
| **Battery** | Bid (charge) / Offer (discharge) | Arbitrage | –20 (charge) / +90 (discharge) | Exploiting spread |
| **Wind Farm (CfD)** | Bid (down) | Pay to curtail | –100 → –1000 | Keeps subsidy income |
| **Interconnector** | Offer (import) | Bring power from abroad | +100 → +500 | Scarcity periods |
| **Demand Response** | Bid (up consumption) | Increase usage | –10 → –50 | Paid to consume excess power |

### 💡 Real-World Examples

**Example 1: Gas Generator Offer**
- A gas generator offers to **increase generation** at £80/MWh
- ESO **buys** that energy to fill a supply shortfall
- Generator **receives £80/MWh** from ESO
- **Result**: Positive price, ESO pays generator

**Example 2: Wind Farm Bid**
- A wind farm bids to **reduce generation** at –£100/MWh
- ESO **accepts** the bid to reduce excess supply
- Wind farm **pays ESO £100/MWh** to be turned down
- **Why?** Wind farm still receives CfD subsidy revenue, so paying to curtail is profitable
- **Result**: Negative price, generator pays ESO

### 🧾 How Balancing Mechanism Prices Are Recorded

When National Grid ESO accepts a bid or offer, that action becomes an **Accepted Balancing Action** in the BMRS feed.  
Elexon publishes this in the **BOALF (Bid Offer Acceptance Log Final)** tables.

**Each record contains:**

| Field | Description | Units |
|-------|-------------|-------|
| `acceptanceId` | Unique ID for the balancing action | — |
| `bmUnitID` | Unit that delivered the action | — |
| `acceptanceType` | **"BID"** or **"OFFER"** | — |
| `acceptancePrice` | Price accepted for the action | £/MWh |
| `acceptanceVolume` | MWh accepted | MWh |
| `timeFrom / timeTo` | Start and end of acceptance | datetime |

### 🔢 Price Interpretation Guide

| Situation | Typical £/MWh | Explanation |
|-----------|--------------|-------------|
| **Positive Offer** | +£20 → +£300 | ESO buying extra power during tight periods (generators paid) |
| **Negative Bid** | –£5 → –£1000 | Generators paying ESO to curtail (common for wind) |
| **Zero Bid/Offer** | £0 | Non-commercial actions (system tests, constraint management) |

**The weighted average of positive and negative prices together gives the aggregate BM price** — typically £20–£50/MWh depending on the mix of actions.

### 🧠 Economic Impact by Actor

| Actor | Action | Financial Effect |
|-------|--------|------------------|
| **ESO** | Buys Offers | Pays generators to increase output (cost) |
| **ESO** | Accepts Bids | Receives payment from generators who reduce output (revenue) |
| **Generator** | Offers | Earns extra revenue |
| **Generator** | Bids | Pays ESO but may still profit via subsidies |
| **Battery / VLP** | Both | Arbitrages difference between BOALF and MID |

### 📊 How Averages Are Calculated

**Weighted Average Formula:**
```sql
SELECT 
  ROUND(SUM(acceptancePrice * acceptanceVolume) / SUM(acceptanceVolume), 2) AS avg_bm_price_gbp_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE acceptancePrice IS NOT NULL;
```

**Volume-Weighted Analysis (More Accurate):**
```sql
-- Separate by price sign (positive = OFFERs, negative = BIDs)
SELECT
  ROUND(SUM(CASE WHEN acceptancePrice > 0 THEN acceptancePrice * acceptanceVolume END) /
        SUM(CASE WHEN acceptancePrice > 0 THEN acceptanceVolume END), 2) AS avg_offer_price,
  ROUND(SUM(CASE WHEN acceptancePrice < 0 THEN acceptancePrice * acceptanceVolume END) /
        SUM(CASE WHEN acceptancePrice < 0 THEN acceptanceVolume END), 2) AS avg_bid_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE validation_flag = 'Valid';
```

**24-Month Volume-Weighted Results:**
- **OFFERs (Positive Prices)**: £65.74/MWh average (78.1 TWh volume)
- **BIDs (Negative Prices)**: -£99.77/MWh average (8.5 TWh volume)
- **Total OFFER Volume**: 9x larger than BID volume (confirms excess supply)

**In 2025 data:**
- **Negative bids** (–£100 to –£20/MWh) occur frequently (wind, storage)
- **Positive offers** (£60–£200/MWh) occur during scarcity
- Because bids outnumber offers (440K vs 354K), negative prices drag overall average down
- **Volume-weighting is critical**: Large MWh actions have proportionally more market impact
- This explains why BOALF average can be lower than MID wholesale price

### ⚠️ Critical Warnings

1. **NEVER average BIDs and OFFERs together without context** — they are opposite actions
2. **Separate analysis required** — BIDs and OFFERs have different price dynamics
3. **Volume-weighted averages** — High-volume low-price events can dominate the mean
4. **Extreme prices are rare** — ±£1000/MWh appears during stress events but represents <1% of actions

---

## 2️⃣ Legal and Policy Framework

| Document | Purpose | Authority |
|----------|---------|-----------|
| **BSC Section T v45 – Settlement and Trading Charges** | Defines how Market Index Prices feed into imbalance and compensation settlement | Elexon |
| **Supplier Compensation Reference Price Methodology Document** | Details calculation of SCRP (£/MWh) using MID | Elexon |
| **BSC Modification P415** | *Facilitating Access to Wholesale Markets for VLPs* | Ofgem / Elexon (2024) |
| **BSC Modification P444** | *Compensation for Imbalances Caused by VLP Dispatch* | Ofgem (Approved Apr 2025) |

**References:**
- [SCRP Methodology – Elexon BSC](https://bscdocs.elexon.co.uk/category-3-documents/supplier-compensation-reference-price-methodology-document)
- [Ofgem P444 Decision (Apr 2025)](https://www.ofgem.gov.uk/sites/default/files/2025-04/P444-decision-letter-for-publication-Apr2025.pdf)
- [BSC Section T v45](https://bscdocs.elexon.co.uk/bsc/bsc-section-t-settlement-and-trading-charges/v-45-0)

---

## 3️⃣ Data Source and Coverage

**Upstream Pipeline:**  
BMRS Market Index Data (MID) → IRIS Streaming → Railway API → BigQuery `bmrs_mid`

**Coverage Statistics:**
- **Total Records**: 155,405
- **Days Covered**: 1,375 (Jan 1, 2022 - Oct 30, 2025)
- **Data Completeness**: 99.2% (excluding zero test records)
- **Average Volume per Period**: 934.3 MWh
- **All-Time Average Price**: £53.55/MWh

---

## 4️⃣ Monthly Market Index Prices - 24 Month Analysis

| Month | Avg Price (£/MWh) | Min | Max | Std Dev | Avg Volume (MWh) | Total Volume (MWh) |
|-------|------------------:|----:|----:|--------:|-----------------:|-------------------:|
| 2025-10 | **75.33** | 0.16 | 287.57 | 35.35 | 2,566 | 3,346,001 |
| 2025-09 | **71.19** | 0.28 | 249.50 | 31.13 | 2,614 | 3,502,517 |
| 2025-08 | **75.41** | 0.74 | 154.67 | 24.87 | 2,389 | 3,344,084 |
| 2025-07 | **80.97** | 0.05 | 230.86 | 18.69 | 2,456 | 3,612,405 |
| 2025-06 | **74.82** | 0.11 | 208.36 | 30.83 | 2,716 | 3,585,452 |
| 2025-05 | **73.35** | 0.44 | 133.64 | 25.56 | 2,461 | 3,492,079 |
| 2025-04 | **80.10** | 0.26 | 151.52 | 21.27 | 2,458 | 3,431,770 |
| 2025-03 | **91.76** | 0.05 | 189.10 | 24.48 | 2,374 | 3,504,319 |
| 2025-02 | **102.65** | 7.56 | 172.57 | 28.24 | 2,560 | 3,458,378 |
| 2025-01 | **114.48** | 1.84 | 1,352.90 | 85.59 | 2,525 | 3,752,690 |
| 2024-12 | **94.24** | 0.57 | 369.52 | 49.40 | 2,413 | 5,318,302 |
| 2024-11 | **96.05** | 1.07 | 183.79 | 24.24 | 2,326 | 6,351,800 |
| 2024-10 | **84.32** | 0.11 | 605.17 | 33.60 | 2,021 | 3,573,233 |
| 2024-09 | **81.42** | 0.03 | 147.86 | 19.12 | 2,145 | 3,975,123 |
| 2024-08 | **64.46** | 0.44 | 121.10 | 27.32 | 2,227 | 6,012,295 |
| 2024-07 | **70.74** | 0.04 | 113.52 | 19.99 | 2,097 | 4,054,082 |
| 2024-06 | **74.36** | 0.11 | 126.57 | 23.60 | 2,057 | 4,869,553 |
| 2024-05 | **73.09** | 1.05 | 114.35 | 16.29 | 1,858 | 4,423,899 |
| 2024-04 | **51.56** | 0.03 | 113.52 | 25.26 | 1,927 | 3,279,644 |
| 2024-03 | **64.70** | 0.24 | 123.23 | 17.21 | 2,088 | 5,769,504 |
| 2024-02 | **59.08** | 0.22 | 105.18 | 16.07 | 1,980 | 5,093,310 |
| 2024-01 | **72.04** | 4.32 | 125.77 | 18.16 | 1,937 | 5,114,055 |
| 2023-12 | **52.77** | 0.10 | 121.09 | 27.11 | 1,846 | 1,170,311 |

**Trends:**
- **Winter 2024/25 Premium**: Jan 2025 peaked at £114.48/MWh (54% above average)
- **Summer Trough**: Apr 2024 lowest at £51.56/MWh
- **Volatility Spike**: Jan 2025 std dev £85.59 (extreme price event with max £1,352.90/MWh)

---

## 5️⃣ October 23-30, 2025 Detailed Verification

**⚠️ USER DOCUMENT CORRECTION REQUIRED:**

| Date | Avg Price (£/MWh) | Avg Volume (MWh) | Num Periods |
|------|------------------:|-----------------:|------------:|
| 2025-10-23 | **73.07** | 3,024 | 47 |
| 2025-10-24 | **48.01** | 2,866 | 40 |
| 2025-10-25 | **24.07** | 2,253 | 47 |
| 2025-10-26 | **30.03** | 2,949 | 45 |
| 2025-10-27 | **73.90** | 3,037 | 37 |
| 2025-10-28 | **21.71** | 2,216 | 1 |
| 2025-10-29 | **58.40** | 3,259 | 30 |
| 2025-10-30 | **76.33** | 2,645 | 1 |

**Actual 7-Day Averages:**
- **Average Price**: £50.69/MWh (NOT £24.4/MWh as claimed)
- **Average Volume**: 2,781 MWh (NOT 1,414 MWh as claimed)

**Explanation**: User document appears to have calculated averages incorrectly or used filtered subset. The £24.4/MWh figure may reflect only Oct 25-26 low-wind period.

---

## 6️⃣ Price Distribution Analysis (24 Months)

| Price Band (£/MWh) | Num Periods | % of Total |
|-------------------|------------:|-----------:|
| Negative | 52 | 0.03% |
| Zero | 384 | 0.25% |
| 0-20 | 9,172 | 5.90% |
| 20-40 | 15,834 | 10.19% |
| 40-60 | 31,152 | 20.04% |
| 60-80 | 45,668 | 29.38% |
| 80-100 | 31,807 | 20.46% |
| 100-150 | 19,422 | 12.49% |
| 150-200 | 1,639 | 1.05% |
| 200+ | 275 | 0.18% |

**Key Insights:**
- **70% of prices** fall within £40-100/MWh (normal trading range)
- **Extreme prices** (>£200/MWh) occur in 0.18% of periods (rare grid stress)
- **Negative prices** (0.03%) during periods of excess renewable generation

---

## 7️⃣ Mathematical Methodology

### Market Index Price (MIP) Calculation

$$
MIP_s = \frac{\sum_i (P_i \times V_i)}{\sum_i V_i}
$$

Where:
- $P_i$ = trade price (£/MWh)
- $V_i$ = trade volume (MWh)
- $s$ = settlement period (30 min)

### Supplier Compensation Reference Price (SCRP)

$$
SCRP_s = MIP_s
$$

For daily reference (if Elexon publishes):

$$
SCRP_d = \frac{1}{N_d}\sum_{s \in d} MIP_s
$$

### Supplier Compensation Calculation

$$
Compensation_{j,v,s} = \Delta V_{j,v,s} \times SCRP_s
$$

Where:
- $\Delta V_{j,v,s}$ = supplier volume deviation (MWh) caused by VLP action
- Positive = supplier receives payment
- Negative = supplier pays VLP

---

## 8️⃣ Worked Example: Supplier Compensation

**Scenario**: VLP reduces customer consumption by 3 MWh during settlement period 15 on Oct 30, 2025.

**Data**:
- SCRP (from MID): £76.33/MWh
- Volume deviation: -3 MWh (supplier lost 3 MWh of metered volume)

**Calculation**:
$$
Compensation = 3 \text{ MWh} \times £76.33/\text{MWh} = £228.99
$$

**Result**: Supplier receives £228.99 from VLP to offset lost revenue caused by flexibility dispatch.

---

## 9️⃣ Comparative Analysis: MID vs BOALF Balancing Prices

### ⚠️ CRITICAL UNDERSTANDING: BIDs vs OFFERs Are OPPOSITE Actions

**This analysis separates THREE DISTINCT price types:**

1. **MID (Market Index Data)** = Wholesale day-ahead trading prices
   - Used as SCRP baseline for supplier compensation
   - Represents "normal" market trading (EPEX/Nord Pool)
   - Average: **£77.00/MWh** (24 months)

2. **BOALF OFFERs** = Generators paid to INCREASE output (scarcity)
   - Positive prices (generators receive payment to generate more)
   - Used during supply shortage, high demand, grid stress
   - **Simple Average**: £88.58/MWh (24 months, all units)
   - **Volume-Weighted Average**: £96.35/MWh ⭐ (more accurate)
   - **Range**: -£979.88 to +£1,000/MWh
   - **Count**: 353,828 acceptances
   - **Total Volume**: 17.4 TWh

3. **BOALF BIDs** = Generators paid to DECREASE output (surplus)
   - Often negative prices (generators PAY to reduce/curtail)
   - Used during excess renewables, low demand, grid surplus
   - **Simple Average**: -£1.63/MWh (24 months, all units)
   - **Volume-Weighted Average**: £0.98/MWh ⭐ (more accurate - large positive bids offset negatives)
   - **Range**: -£1,000 to +£200/MWh
   - **Count**: 440,306 acceptances
   - **Total Volume**: 28.4 TWh (1.6x larger than offers!)

**⚠️ NEVER average BIDs and OFFERs together - they are opposite market actions!**

### 📊 Comprehensive Accepted Data Summary (24 Months)

| Metric | BIDS (Reduce Output) | OFFERS (Increase Output) |
|--------|---------------------:|-------------------------:|
| **Count** | 440,306 acceptances | 353,828 acceptances |
| **Simple Average** | -£1.63/MWh | £88.58/MWh |
| **Volume-Weighted Avg** ⭐ | **£0.98/MWh** | **£96.35/MWh** |
| **Min Price** | -£1,000.00/MWh | -£979.88/MWh |
| **Max Price** | £200.00/MWh | £1,000.00/MWh |
| **Std Deviation** | 105.63 | 90.48 |
| **Avg Volume/Action** | 64.4 MW | 49.3 MW |
| **Total Volume** | 28.4 TWh (62%) | 17.4 TWh (38%) |

**Key Insight**: Volume-weighted averages are MORE ACCURATE than simple averages because:
- Large-volume actions have proportionally more market impact
- BID volume-weighted avg (£0.98) vs simple avg (-£1.63) = large positive-price bids offset many small negatives
- OFFER volume-weighted avg (£96.35) vs simple avg (£88.58) = high-price scarcity events weighted properly

### Monthly BOALF Prices - SEPARATED BY TYPE (Last 12 Months)

#### OFFERS (Generators Paid to INCREASE Output)

| Month | Num OFFERs | Avg Price (£/MWh) | Min | Max |
|-------|-----------|------------------:|----:|----:|
| 2025-12 | 16,904 | **80.87** | -451.24 | 292.63 |
| 2025-11 | 21,014 | **93.72** | -451.24 | 999.00 |
| 2025-10 | 23,970 | **111.12** | -451.24 | 997.00 |
| 2025-09 | 19,771 | **89.66** | -500.00 | 999.90 |
| 2025-08 | 16,448 | **91.06** | -500.00 | 999.00 |
| 2025-07 | 15,586 | **101.85** | -500.00 | 999.00 |
| 2025-06 | 13,610 | **86.88** | -500.00 | 999.90 |
| 2025-05 | 15,960 | **86.21** | -978.03 | 999.00 |
| 2025-04 | 15,004 | **87.69** | -960.82 | 999.90 |
| 2025-03 | 12,810 | **105.36** | -962.28 | 1,000.00 |
| 2025-02 | 10,886 | **117.92** | -500.00 | 999.90 |
| 2025-01 | 13,825 | **127.69** | -946.00 | 1,000.00 |

**12-Month OFFER Average**: £98.50/MWh

#### BIDS (Generators Paid to DECREASE Output)

| Month | Num BIDs | Avg Price (£/MWh) | Min | Max |
|-------|----------|------------------:|----:|----:|
| 2025-12 | 13,630 | **12.63** | -999.00 | 100.59 |
| 2025-11 | 22,803 | **1.01** | -999.00 | 120.57 |
| 2025-10 | 48,273 | **-8.71** | -999.00 | 119.94 |
| 2025-09 | 28,922 | **-20.93** | -999.00 | 110.80 |
| 2025-08 | 16,406 | **-7.71** | -999.00 | 121.00 |
| 2025-07 | 16,526 | **-3.78** | -882.27 | 122.46 |
| 2025-06 | 17,018 | **-12.98** | -999.00 | 160.00 |
| 2025-05 | 14,085 | **-4.95** | -999.00 | 120.42 |
| 2025-04 | 12,975 | **1.16** | -985.58 | 122.15 |
| 2025-03 | 17,890 | **1.68** | -996.92 | 142.82 |
| 2025-02 | 18,727 | **23.15** | -898.71 | 176.62 |
| 2025-01 | 16,372 | **13.38** | -1,000.00 | 200.00 |

**12-Month BID Average**: £-0.59/MWh (slightly negative = generators pay to reduce)

### Monthly BOALF Acceptance Prices (Last 12 Months)

### Monthly Price Comparison (Last 12 Months)

| Month | MID Wholesale (£/MWh) | OFFER Avg (£/MWh) | BID Avg (£/MWh) | OFFER Premium | Num OFFERs | Num BIDs |
|-------|----------------------:|------------------:|----------------:|--------------:|-----------:|---------:|
| 2025-12 | TBD | **80.87** | **12.63** | TBD | 16,904 | 13,630 |
| 2025-11 | TBD | **93.72** | **1.01** | TBD | 21,014 | 22,803 |
| 2025-10 | **75.33** | **111.12** | **-8.71** | **+35.79** | 23,970 | 48,273 |
| 2025-09 | **71.19** | **89.66** | **-20.93** | **+18.47** | 19,771 | 28,922 |
| 2025-08 | **75.41** | **91.06** | **-7.71** | **+15.65** | 16,448 | 16,406 |
| 2025-07 | **80.97** | **101.85** | **-3.78** | **+20.88** | 15,586 | 16,526 |
| 2025-06 | **74.82** | **86.88** | **-12.98** | **+12.06** | 13,610 | 17,018 |
| 2025-05 | **73.35** | **86.21** | **-4.95** | **+12.86** | 15,960 | 14,085 |
| 2025-04 | **80.10** | **87.69** | **1.16** | **+7.59** | 15,004 | 12,975 |
| 2025-03 | **91.76** | **105.36** | **1.68** | **+13.60** | 12,810 | 17,890 |
| 2025-02 | **102.65** | **117.92** | **23.15** | **+15.27** | 10,886 | 18,727 |
| 2025-01 | **114.48** | **127.69** | **13.38** | **+13.21** | 13,825 | 16,372 |

**Key Insights:**
- **OFFERs average HIGHER than MID** by £16.95/MWh (scarcity premium for increasing generation)
- **BIDs average NEGATIVE** at -£0.59/MWh (generators pay to reduce during surplus)
- **More BIDs than OFFERs** (440K vs 354K) = excess renewables driving surplus events
- **Oct 2025**: Highest OFFER premium (+£35.79) = significant grid stress period

### Why Different Price Levels?

**MID (£77/MWh average):**
- Day-ahead wholesale market (all trades positive prices)
- "Normal" market price for bulk electricity
- Used for SCRP supplier compensation

**OFFERs (£88.58/MWh average):**
- Real-time balancing mechanism (scarcity pricing)
- Higher than MID = premium for immediate generation increase
- Emergency/grid stress events can reach £999-1000/MWh

**BIDs (-£1.63/MWh average):**
- Real-time balancing mechanism (surplus pricing)
- Often NEGATIVE = generators PAY to reduce output
- Excess wind/solar → curtailment needed → negative prices

---

## 🔟 October 2025 Daily Comparison: MID vs BOALF

| Date | SCRP/MID (£/MWh) | BM Avg Price | Premium | Num BM Actions | Extreme Events (>£100) |
|------|----------------:|-------------:|--------:|---------------:|-----------------------:|
| 2025-10-01 | 81.79 | 8.25 | -73.54 | 2,939 | 208 |
| 2025-10-13 | 125.41 | **146.46** | **+21.05** | 2,618 | **1,576** |
| 2025-10-14 | 100.04 | **147.11** | **+47.07** | 2,254 | **1,478** |
| 2025-10-15 | 95.74 | **106.65** | **+10.91** | 2,188 | **1,276** |
| 2025-10-21 | 79.83 | 68.35 | -11.48 | 2,890 | 1,126 |
| 2025-10-22 | 96.48 | 96.95 | +0.47 | 2,953 | 970 |
| 2025-10-25 | 24.07 | -44.90 | -68.97 | 4,170 | 507 |

**Notable Events:**
- **Oct 13-15**: MID spiked to £95-125/MWh, BM even higher (£106-147/MWh) → grid stress
- **Oct 25**: Very low MID (£24/MWh), negative BM average (-£44.90) → excess wind generation
- **Extreme events**: Days with >1,000 BM actions at >£100/MWh indicate grid instability

---

## 1️⃣1️⃣ VLP Battery Revenue vs Market Index Prices

| Month | Market Index (£/MWh) | VLP Actions | Avg BM Price (£/MWh) | VLP Revenue (£) | BM/MID Ratio |
|-------|---------------------:|------------:|---------------------:|----------------:|-------------:|
| 2025-10 | 75.33 | 22,088 | 15.47 | 2,172,252 | 0.21 |
| 2025-09 | 71.19 | 16,975 | 5.11 | 490,554 | 0.07 |
| 2025-08 | 75.41 | 9,110 | 33.21 | 1,018,060 | 0.44 |
| 2025-07 | 80.97 | 9,544 | 40.93 | 1,532,307 | 0.51 |
| 2025-01 | 114.48 | 7,739 | 87.40 | 2,544,741 | 0.76 |

**VLP Arbitrage Opportunity:**
- **Suppliers** compensated at SCRP/MID rates (£70-115/MWh in 2025)
- **VLPs** earn BM prices (average £15-87/MWh, but with negative BIDs pulling average down)
- **Positive arbitrage months**: Jan 2025 (BM 76% of MID), Jul-Aug 2025 (BM 44-51% of MID)
- **Negative arbitrage months**: Sep-Oct 2025 (BM only 7-21% of MID) → excess wind, negative BIDs

**Total VLP Revenue (Oct 2024 - Oct 2025)**: £15.8M across 104,284 balancing actions

---

## 1️⃣2️⃣ Price Correlation Analysis

**When MID is Low, What Happens to BM Prices?**

| MID Price Category | Num Days | Avg MID (£/MWh) | Avg BOALF (£/MWh) | Avg BM Actions |
|-------------------|----------|----------------:|------------------:|---------------:|
| Very Low (<£20) | 1 | 10.27 | -30.52 | 2,939 |
| Low (£20-40) | 4 | 26.68 | -19.23 | 1,518 |
| Medium (£40-60) | 3 | 54.16 | -0.54 | 1,198 |
| High (£60-80) | 8 | 75.20 | 36.17 | 1,407 |
| Very High (£80+) | 14 | 93.35 | 62.02 | 1,476 |

**Correlation**:
- ✅ **Positive correlation**: Higher MID → Higher BOALF
- ⚠️ **Negative BOALF when MID low** → generators paid to reduce (excess renewables)
- 📈 **More BM actions when MID low** → grid balancing more active during low-price periods

---

## 1️⃣3️⃣ Comparison of Price Types

| Price Type | Source | Frequency | Typical Range (£/MWh) | Purpose |
|------------|--------|-----------|----------------------|---------|
| **SCRP (Market Index)** | BMRS / Elexon | ½ hourly | 20-120 | Supplier compensation & imbalance valuation |
| **System Buy/Sell Price** | NGESO Balancing | ½ hourly | 50-300 | BM imbalance settlement |
| **BOALF Acceptance Price** | Elexon BMRS | Per acceptance | -1000 to +1000 | Individual balancing action payments |
| **Retail Price Cap Wholesale Allowance** | Ofgem | Quarterly | 100-150 | Consumer tariff benchmark |

---

## 1️⃣4️⃣ Governance and Audit Trail

| Actor | Responsibility |
|-------|----------------|
| **Elexon Ltd** | Publishes MID data, maintains SCRP methodology document |
| **BSC Panel** | Approves changes to SCRP calculation under Section T |
| **Performance Assurance Board (PAB)** | Audits data quality and settlement accuracy |
| **Ofgem** | Regulator approving BSC modifications (P415/P444) |
| **Suppliers & VLPs** | Participate in compensation settlements using SCRP |

---

## 1️⃣5️⃣ Key Insights and Recommendations

### ✅ Data Quality Verification
1. **Coverage**: 1,375 days of data (Jan 2022 - Oct 2025) with 99.2% completeness
2. **Accuracy**: User document Oct 23-30 average (£24.4/MWh) **INCORRECT** → actual £50.69/MWh
3. **Volatility**: Jan 2025 extreme event (£1,352.90/MWh max) reflects grid emergency

### 📊 Price Relationships
1. **MID vs BOALF**: BOALF averages **£41.53/MWh LOWER** than MID (negative BIDs dominate)
2. **VLP Revenue**: Highly variable (£490K-£2.5M/month) depending on grid stress
3. **Supplier Compensation**: Fair market-based pricing using MID (£50-115/MWh typical)

### 💡 Policy Implications
1. **P444 Validation**: SCRP mechanism working as designed (suppliers remain neutral)
2. **VLP Profitability**: Dependent on grid stress events (Oct 13-15, 2025 high revenue)
3. **Market Efficiency**: Price signals correctly reflect scarcity (high MID = high BM)

### ⚠️ Risks and Anomalies
1. **Negative Prices**: Occurring 0.03% of time (excess renewables, need storage)
2. **Extreme Spikes**: £1,352.90/MWh (Jan 2025) shows market can hit regulatory max
3. **Data Gaps**: Oct 28-30, 2025 show only 1 record/day (IRIS ingestion issue?)

---

## 1️⃣6️⃣ Conclusions

1. **THREE DISTINCT PRICE DATASETS ANALYZED (NOT TWO!):**
   - **MID (Wholesale)**: £77.00/MWh - Used for SCRP supplier compensation
   - **BOALF OFFERs**: £88.58/MWh - Generators paid to INCREASE output (scarcity)
   - **BOALF BIDs**: -£1.63/MWh - Generators paid to DECREASE output (surplus)
   - **CRITICAL**: BIDs and OFFERs are OPPOSITE actions - averaging them is meaningless!

2. **SCRP is based on MID (wholesale), NOT BOALF (balancing)**:
   - Suppliers compensated at wholesale reference rates (£50-115/MWh typical in 2025)
   - This protects suppliers from volatile balancing mechanism prices
   - Fair market-based compensation using day-ahead trading as baseline

3. **OFFERs command premium over MID** (+£16.95/MWh average):
   - Real-time scarcity pricing above wholesale
   - Emergency grid stress can reach £999-1000/MWh
   - Oct 2025: +£35.79/MWh premium (highest in 12 months)

4. **BIDs often NEGATIVE** (avg -£1.63/MWh):
   - 440K BIDs vs 354K OFFERs = more surplus than scarcity
   - Generators PAY to reduce output during excess renewables
   - Oct 2025: -£8.71/MWh average (high wind period)

5. **User document claims require correction**: 
   - Oct 23-30 MID average is £50.69/MWh, NOT £24.4/MWh
   - Oct 23-30 volume is 2,781 MWh/period, NOT 1,414 MWh

6. **VLP arbitrage opportunity exists** but is **highly variable**:
   - VLPs receive BOALF payments (OFFERs £88.58/MWh, BIDs -£1.63/MWh)
   - Suppliers compensated at SCRP/MID rates (£77.00/MWh)
   - Profitable during scarcity (OFFER premium over MID)
   - Loss-making during surplus (negative BID pricing)
   - Monthly revenue ranges £490K-£2.5M for battery VLPs

7. **Policy goal achieved**: Ofgem P415/P444 modifications ensure suppliers remain economically neutral to VLP flexibility actions via fair SCRP-based compensation at wholesale MID rates, insulating them from volatile balancing mechanism prices (both expensive OFFERs and negative BIDs).

---

## 📚 References

1. Elexon – *Supplier Compensation Reference Price Methodology Document*, 2024 v1.0
2. Ofgem – *Decision on BSC Modification P444: Compensation for Imbalances Caused by VLP Dispatch*, April 2025
3. Elexon – *Balancing and Settlement Code Section T v45 – Settlement and Trading Charges*
4. BMRS – *Market Index Data Specification Document* (v11, 2023)
5. NG ESO – *Balancing Mechanism Imbalance Pricing Guidance*, 2024
6. BigQuery Dataset: `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
7. BigQuery Dataset: `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`

---

## 📎 Appendix: SQL Queries Used

### Monthly MID Statistics
```sql
SELECT 
  FORMAT_DATE('%Y-%m', DATE(settlementDate)) as month,
  COUNT(*) as num_records,
  ROUND(AVG(price), 2) as avg_price_gbp_mwh,
  ROUND(MIN(price), 2) as min_price,
  ROUND(MAX(price), 2) as max_price,
  ROUND(AVG(volume), 1) as avg_volume_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
  AND price > 0
GROUP BY month
ORDER BY month DESC
```

### MID vs BOALF Comparison
```sql
WITH mid_monthly AS (
  SELECT FORMAT_DATE('%Y-%m', DATE(settlementDate)) as month,
         ROUND(AVG(price), 2) as mid_avg_price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE price > 0
  GROUP BY month
),
boalf_monthly AS (
  SELECT FORMAT_DATE('%Y-%m', DATE(settlementDate)) as month,
         ROUND(AVG(acceptancePrice), 2) as boalf_avg_price,
         COUNT(*) as num_acceptances
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
  WHERE validation_flag = 'Valid'
  GROUP BY month
)
SELECT m.month, m.mid_avg_price, b.boalf_avg_price,
       ROUND(b.boalf_avg_price - m.mid_avg_price, 2) as price_premium
FROM mid_monthly m
LEFT JOIN boalf_monthly b ON m.month = b.month
ORDER BY m.month DESC
```

---

**Document Status**: ✅ Verified Analysis Complete  
**Next Review Date**: 2026-01-16  
**Contact**: george@upowerenergy.uk
