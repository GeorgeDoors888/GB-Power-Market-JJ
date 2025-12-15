# 💰 DISBSAD Pricing Structure: OFR Services Analysis

**Date:** December 9, 2025  
**Dataset:** `bmrs_disbsad` (Last 30 Days: Nov 9 - Dec 9, 2025)  
**Analysis Tool:** `ofr_pricing_analysis.py`  
**Key Finding:** OFR services account for £5.20M (11%) of DISBSAD costs with distinct pricing characteristics vs generator balancing

---

## 📊 Executive Summary

**DISBSAD (Disaggregated Balancing Services Adjustment Data)** records the costs of balancing services used by National Grid ESO. The data reveals clear distinctions between **Optional Frequency Response (OFR)** flexibility services and traditional generator-based balancing.

### Key Metrics (Last 30 Days: Nov 9 - Dec 9, 2025)
- **Total DISBSAD Costs:** £49.36M
- **OFR Flexibility:** £5.20M (11%) - 3,490 actions, 47,280 MWh
- **Non-OFR (Generators):** £44.17M (89%) - 4,016 actions, 208,683 MWh
- **OFR Price Advantage:** 48% cheaper (£109.91 vs £211.64/MWh)

**Note:** These are realised utilisation prices from DISBSAD only (cost ÷ volume). Availability payments, capacity revenues, and other commercial terms are NOT included.

---

## 🔍 DISBSAD Schema & Fields

### Core Pricing Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `cost` | FLOAT64 | **Total payment in GBP** for the action | £6,450.00 |
| `volume` | FLOAT64 | **Energy delivered in MWh** | 50.0 MWh |
| `price_per_mwh` | (Calculated) | **Utilisation price** = cost / volume | £129.00/MWh |
| `assetId` | STRING | Service provider identifier | 'OFR-UKPR-6' |
| `soFlag` | BOOL | System Operator flag (True = non-energy action) | False |
| `storFlag` | BOOL | STOR service flag | False |
| `service` | STRING | Service type description | 'Non-BM STOR' |

### Settlement Fields
- `settlementDate` (DATETIME): Date of the balancing action
- `settlementPeriod` (INT64): Half-hourly period (1-50)
- `id` (INT64): Unique action identifier per settlement period

### Metadata Fields
- `partyId`: Lead party/provider ID
- `isTendered`: Tendered service flag
- `dataset`: Source dataset name

---

## 💷 Pricing Structure Analysis

### 1. OFR Flexibility Services

**Asset ID Pattern:** `OFR-{PROVIDER}-{ID}`
- OFR-UKPR-6 (UK Power Reserve)
- OFR-HAB-1 through OFR-HAB-7 (Habitat Energy)
- OFR-ENWL-1 (Electricity North West)

**Pricing Characteristics (Last 30 Days: Nov 9 - Dec 9, 2025):**
```
Volume-Weighted Avg:  £109.91/MWh
Price Range:          £70.94 - £199.00/MWh
Quartiles:            Q1=£100, Median=£106, Q3=£115
Total Volume:         47,280 MWh
Total Cost:           £5.20M
Actions:              3,490
```

**Example Pricing Distribution:**
```
Min Price:    £70.94/MWh (low-demand periods)
Q1:           £100.00/MWh (25th percentile)
Median:       £106.00/MWh (50th percentile)
Q3:           £115.00/MWh (75th percentile)
Max Price:    £199.00/MWh (high-stress periods)
```

**Key Observations:**
- ✅ **ALL records have volume > 0** (no availability payments in DISBSAD)
- ✅ **100% utilisation-based pricing** (payment only when called)
- ✅ **SO-Flag = False** (energy balancing, not system services)
- ✅ **Consistent 50 MWh blocks** (suggests standardised response sizes)

### 2. Generator-Based Balancing (Non-OFR)

**Asset ID Pattern:** Various generators, interconnectors, other balancing services

**Pricing Characteristics (Last 30 Days: Nov 9 - Dec 9, 2025):**
```
Volume-Weighted Avg:  £211.64/MWh
Total Volume:         208,683 MWh
Total Cost:           £44.17M
Actions:              4,016
```

**Key Comparison:** 
- **OFR vs Non-OFR Price Difference:** 48% cheaper (£109.91 vs £211.64/MWh)
- Non-OFR includes: CCGT generators, interconnectors, demand-side services
- Higher pricing reflects marginal generation costs and opportunity costs

---

## 🔑 Understanding the Pricing Model

### OFR Contracts: Utilisation-Only Payment

**Contract Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  OPTIONAL FREQUENCY RESPONSE (OFR) CONTRACT                  │
├─────────────────────────────────────────────────────────────┤
│  Availability Payment:   £0 (NOT in DISBSAD)                │
│  Utilisation Payment:    £80-150/MWh (IN DISBSAD)           │
│                                                              │
│  When Called:            Pay for actual MWh delivered        │
│  When Not Called:        No payment recorded in DISBSAD      │
└─────────────────────────────────────────────────────────────┘
```

**Why no zero-volume records?**
- OFR providers bid utilisation prices into the balancing mechanism
- National Grid only calls them when economically optimal
- DISBSAD only records **actual utilisations** (volume > 0)
- If not called → no cost → no DISBSAD record

### Firm Frequency Response: Availability + Utilisation

**Contract Structure (NOT in DISBSAD):**
```
┌─────────────────────────────────────────────────────────────┐
│  FIRM FREQUENCY RESPONSE (FFR) CONTRACT                      │
├─────────────────────────────────────────────────────────────┤
│  Availability Payment:   £X/MW/h (separate invoice)         │
│  Utilisation Payment:    £Y/MWh (IN DISBSAD if called)      │
│                                                              │
│  Monthly Invoice:        Availability fees (NOT in DISBSAD) │
│  Settlement:             Utilisation in DISBSAD              │
└─────────────────────────────────────────────────────────────┘
```

**Key Distinction:**
- FFR availability payments: Billed monthly, NOT in DISBSAD
- FFR utilisation payments: In DISBSAD when service is triggered
- OFR: Only utilisation in DISBSAD (no availability component)

---

## 📐 Price Calculation

### How Prices Are Determined

**1. Bid Price (Provider submits):**
```
Provider: "OFR-UKPR-6"
Bid:      £125.00/MWh
Volume:   50 MW available
```

**2. Market Dispatch (National Grid calls when needed):**
```
Period 38 (18:30-19:00), Dec 3:
  System Price:        £80/MWh (imbalance price)
  Provider Bid:        £125/MWh
  Dispatch Decision:   ACCEPT (need balancing despite higher price)
  Volume Delivered:    50.0 MWh
```

**3. DISBSAD Record Created:**
```python
cost = volume * agreed_price
cost = 50.0 MWh * £125.00/MWh = £6,250.00

Record:
  assetId: 'OFR-UKPR-6'
  cost: 6250.00
  volume: 50.0
  price_per_mwh: 125.0  # Calculated: cost / volume
  soFlag: False  # Energy balancing
```

### Price Variability Factors

**OFR prices vary by:**
1. **Time of Day** - Evening peak (SP 34-42) = higher prices
2. **Market Conditions** - Tight system = higher bids accepted
3. **Provider Strategy** - Different providers have different cost structures
4. **Service Speed** - Faster response = premium pricing

**Example Price Range (Last 7 Days):**
```
Lowest:   £80.42/MWh (off-peak, low demand)
Average:  £108.72/MWh
Highest:  £149.00/MWh (evening peak, tight system)
```

---

## 🚩 SO-Flag: System vs Energy Balancing

### SO-Flag = False (Energy Balancing)

**OFR Services: 834 actions, £1.40M**
- Purpose: Balance short-term energy imbalance
- Trigger: System frequency deviation from 50 Hz
- Pricing: Competitive bids (£80-150/MWh)
- Cost Recovery: Socialised via BSUoS (Balancing Services Use of System) charges

### SO-Flag = True (System Actions)

**Generators: 899 actions, £378k**
- Purpose: Transmission constraint management, voltage support
- Trigger: Network constraints, not energy imbalance
- Pricing: Can be negative (paying generators to turn down)
- Cost Recovery: Typically via TNUoS (Transmission Network Use of System)

**Key Finding:**
- **100% of OFR actions have SO-Flag=False** (pure energy balancing)
- OFR services NOT used for system constraint management
- Constraint costs (transmission wind curtailment) show SO-Flag=True

---

## 📊 Comparative Analysis

### OFR vs Generator Balancing Costs

| Metric | OFR Flexibility | Generators | Ratio |
|--------|----------------|------------|-------|
| **Records** | 834 | 901 | 0.93:1 |
| **Total Cost** | £1.40M (79%) | £0.38M (21%) | 3.7:1 |
| **Avg Price** | £108.72/MWh | £138.79/MWh* | 0.78:1 |
| **Total Volume** | 12,647 MWh | 2,760 MWh | 4.6:1 |
| **Cost per Action** | £1,680 | £421 | 4.0:1 |

*Generators: Excluding SO-Flag=True negative payments

**Interpretation:**
- OFR provides **4.6x more energy volume** than generators
- OFR has **lower average price** (£109 vs £139/MWh)
- But OFR dominates total costs due to **high utilisation volume**
- OFR actions are larger blocks (avg 15.2 MWh vs 3.1 MWh)

---

## 🔍 Data Quality & Completeness

### What DISBSAD Contains

✅ **Included:**
- Utilisation payments for OFR services
- Utilisation payments for FFR services (when called)
- Constraint payments to generators (SO-Flag=True)
- STOR (Short-Term Operating Reserve) utilisations
- Emergency actions (when actual delivery occurs)

❌ **NOT Included:**
- FFR availability payments (monthly invoices)
- OFR tender costs (if any)
- Capacity Market payments
- CM availability fees
- Long-term contracts (e.g., 10-year FFR EFAs)
- Administrative costs

### Geographic Attribution Limitation

**Problem:** 79% of costs (OFR services) have no regional data

**Why:**
```
OFR-UKPR-6 = UK Power Reserve aggregator
  ├─ Battery A (London)
  ├─ Battery B (Manchester)
  ├─ Industrial Load C (Birmingham)
  └─ Wind Farm D (Scotland)

Single assetId = Multiple physical locations
→ No meaningful regional breakdown possible
```

**Implication:**
- Dashboard shows "N/A" for OFR costs
- Only 21% of costs (£378k generators) can be regionally attributed
- This is a **data structure limitation**, not a data quality issue

---

## 📈 Price Trends & Patterns

### Peak Pricing Periods

**Highest Utilisation:** Settlement Periods 34-42 (17:00-21:00)
```
SP 38 (18:30-19:00):  £129.00/MWh avg
SP 39 (19:00-19:30):  £125.00/MWh avg
SP 37 (18:00-18:30):  £125.00/MWh avg
```

**Lowest Utilisation:** Overnight periods (SP 1-10)
```
SP 5 (02:00-02:30):   £80.42/MWh avg
```

### Provider Pricing Strategies

**UK Power Reserve (OFR-UKPR-6):** £321k (7 days)
- High volume provider (2,623 MWh)
- Consistent 50 MWh blocks
- Price range: £118-129/MWh
- Strategy: Large-scale aggregator, competitive pricing

**Habitat Energy (OFR-HAB-1 to 7):** £774k total
- Multiple asset pools (OFR-HAB-1 through OFR-HAB-7)
- Variable pricing by asset pool
- Largest single provider group
- Strategy: Portfolio approach, risk diversification

---

## 💡 Business Insights

### For Battery/Flexibility Operators

**Revenue Opportunity:**
```
Average OFR Payment:  £108.72/MWh
Frequency of Call:    ~120 dispatches per week (system-wide)
Typical Block Size:   50 MWh
Revenue per Call:     ~£5,400
```

**Competitive Positioning:**
- Price below £110/MWh for regular dispatch
- Price above £120/MWh for peak-only strategy
- Offer 50+ MWh blocks for preference

### For Market Analysis

**Constraint Cost Breakdown:**
```
Total (7 days):           £1.78M
├─ OFR Flexibility:       £1.40M (79%)
│  └─ Energy balancing only (SO-Flag=False)
│
└─ Generators:            £0.38M (21%)
   ├─ Energy balancing:   £0.06M (SO-Flag=False)
   └─ Constraints:        £0.38M (SO-Flag=True)
```

**Key Takeaway:**
- OFR dominates energy balancing costs
- Traditional generators still used for constraint management
- Wind curtailment costs appear as negative payments (SO-Flag=True)

---

## 🔮 Future Enhancements

### 1. Add Price Forecasting Model

**Inputs:**
- Historical OFR utilisation prices
- System imbalance prices (SSP/SBP)
- Demand levels
- Wind generation
- Settlement period

**Output:** Predicted OFR dispatch price for next day

### 2. Provider Performance Tracking

**Metrics:**
- Average price by provider
- Dispatch frequency
- Volume reliability (bid vs delivered)
- Market share trends

### 3. Regional Cost Allocation (if data becomes available)

**Approach:** Use DNO-level flexibility tender data to infer OFR locations
```sql
-- Hypothetical future query
SELECT 
  ofr.assetId,
  flex.dno_region,
  SUM(ofr.cost) as regional_cost
FROM bmrs_disbsad ofr
JOIN flexibility_services_reference flex
  ON ofr.assetId = flex.asset_id
WHERE ofr.assetId LIKE 'OFR-%'
GROUP BY ofr.assetId, flex.dno_region
```

---

## 📚 Related Documentation

- **DISBSAD Backfill:** `DISBSAD_BACKFILL_SETUP.md`
- **Geographic Constraints:** `docs/GEOGRAPHIC_CONSTRAINTS_COMPLETE.md`
- **Data Accuracy Fix:** `docs/GEOGRAPHIC_CONSTRAINTS_DATA_ACCURACY_FIX.md`
- **Architecture:** `docs/UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`

---

## 📖 Glossary

**OFR (Optional Frequency Response):**
- Flexible balancing service with utilisation-only payment
- Providers bid prices to respond when called
- No guaranteed payment (no availability fee in contract)

**FFR (Firm Frequency Response):**
- Contracted frequency response with availability + utilisation payments
- Availability paid monthly regardless of use
- Utilisation paid when service is triggered (appears in DISBSAD)

**DISBSAD (Disaggregated Balancing Services Adjustment Data):**
- Settlement-level record of balancing service utilisations
- Records actual energy delivered and payment made
- Does NOT include availability-only payments

**SO-Flag (System Operator Flag):**
- True: Action taken for system reasons (constraints, voltage)
- False: Action taken for energy balancing (frequency deviation)

**Price per MWh:**
- Calculated: `cost / volume`
- Represents the agreed utilisation rate
- NOT the system imbalance price (SSP/SBP)

---

## ✅ Key Findings Summary

1. **No Availability Payments in DISBSAD**
   - All records have volume > 0
   - Only utilisations recorded, not monthly availability fees

2. **OFR Prices: £80-150/MWh**
   - Average: £108.72/MWh
   - Lower than generator balancing (£138.79/MWh)
   - Variable by time of day and market conditions

3. **Price is Utilisation Rate**
   - Calculated as: cost ÷ volume
   - Represents agreed dispatch price, not system price
   - Higher than typical imbalance prices (indicates balancing need)

4. **SO-Flag Distinguishes Service Type**
   - False: Energy balancing (100% of OFR)
   - True: System constraints (generators)

5. **Regional Attribution Impossible for OFR**
   - OFR services are aggregated portfolios
   - Single assetId spans multiple physical locations
   - Would need separate flexibility services database

---

*Last Updated: December 9, 2025*  
*Data Source: bmrs_disbsad (Dec 2-8, 2025)*  
*Next Review: When flexibility services location data becomes available*
