# ❌ Why Geographic Constraints Show "N/A" for Costs

**Date:** December 9, 2025  
**Question:** "Why can't we get cost data for Transmission Wind constraints?"  
**Answer:** **Transmission constraint costs are NOT in DISBSAD**

---

## 🔍 The Investigation

### What You're Seeing in the Dashboard

```
🗺️  GEOGRAPHIC CONSTRAINTS (Last 7 Days)

Region                   Actions  Units  MW Adjusted  Cost (£k)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Transmission Wind      5,790     26    189,435      N/A  ← Why?
🔴 Transmission Other     2,203     24     68,091      N/A
🔴 Transmission Hydro     2,100     11     46,196      N/A
🔴 North Scotland         1,221     11     11,431      N/A
```

### What This Data Represents

**BOALF (Balancing Mechanism Offer/Bid Lift)**
- **Source:** `bmrs_boalf` + `bmrs_boalf_iris`
- **What it shows:** SO instructions to generators
  - "T_SGRWO-1, reduce output by 50 MW"
  - "T_MOWWO-2, increase output by 100 MW"
- **soFlag=TRUE:** System constraint actions (not energy balancing)
- **Records:** 5,790 actions for transmission wind (last 7 days)

---

## 🎯 Critical Finding: Two Completely Different Data Streams

### DISBSAD = Flexibility Services (OFR, FFR, STOR)

**What's IN DISBSAD:**
```
Asset Type          Cost (30d)  Actions  Type
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OFR Flexibility     £5.20M      3,490    Battery/DSR services
Non-OFR (Various)   £44.17M     4,016    Generator balancing
```

**OFR Pricing (Nov 9 - Dec 9, 2025):**
- Volume-weighted avg: £109.91/MWh
- Range: £70.94 - £199.00/MWh
- Total: £5.20M for 47,280 MWh

**What's NOT IN DISBSAD:**
- ❌ Transmission wind constraint costs (T_SGRWO, T_MOWWO, T_VKNGW)
- ❌ Most transmission generator constraints
- ❌ Individual constraint action costs

**Test Result:**
```sql
SELECT COUNT(*) 
FROM bmrs_disbsad 
WHERE assetId LIKE 'T_S%'  -- Seagreen wind
  AND settlementDate >= '2025-01-01'
```
**Result: 0 records** ← Transmission wind NOT in DISBSAD

---

## 📊 Where ARE the Constraint Costs?

### Option 1: NETBSAD (Net Balancing Services Adjustment Data)

**Schema:**
```
netBuyPriceCostAdjustmentEnergy     - Energy balancing costs
netBuyPriceVolumeAdjustmentEnergy   - Energy volumes
netBuyPriceVolumeAdjustmentSystem   - System constraint volumes
sellPricePriceAdjustment            - Sell price adjustments
```

**Problem:** NETBSAD is **market-wide aggregated data**, NOT per-unit
- No `bmUnit` field
- No `assetId` field
- Can't attribute to specific generators
- Can't map to regions

**Example NETBSAD Record:**
```
settlementDate: 2025-12-08
settlementPeriod: 38
netBuyPriceVolumeAdjustmentSystem: 12,500 MWh  ← Total system constraints
buyPricePriceAdjustment: £0.45/MWh            ← Market-wide adjustment
```
→ Can't tell which units caused this or where they are

### Option 2: NOT YET PUBLISHED

**Elexon Data Status:**
- BOALF: ✅ Published (we have this - the actions)
- DISBSAD: ✅ Published (but doesn't include transmission constraints)
- NETBSAD: ✅ Published (aggregated, no unit detail)
- **Unit-level constraint costs: ❌ NOT in public BMRS API**

---

## 💡 Why the Confusion?

### What £6,450 Actually Represents

**From the pricing analysis:**
```
Asset:  OFR-UKPR-6
Cost:   £6,450.00
Volume: 50.0 MWh
Price:  £129.00/MWh
```

**This is:**
- ✅ A flexibility service payment (OFR)
- ✅ For energy balancing (SO-Flag=False)
- ❌ NOT a transmission wind constraint cost
- ❌ NOT related to the 5,790 constraint actions we're showing

**The Disconnect:**
- Dashboard shows: **5,790 transmission wind constraint actions**
- DISBSAD contains: **0 transmission wind constraint cost records**
- These are **two separate systems** that don't map to each other

---

## 🔑 The Real Answer: Data Architecture Limitation

### BOALF (Actions) vs DISBSAD (Costs)

```
┌─────────────────────────────────────────────────────────────────┐
│  BALANCING MECHANISM ACTIONS (BOALF)                            │
├─────────────────────────────────────────────────────────────────┤
│  ✅ Instruction: "T_SGRWO-1, reduce 50 MW"                     │
│  ✅ Timestamp: 2025-12-08 18:30 (Period 38)                    │
│  ✅ Action Type: SO-Flag=TRUE (constraint)                     │
│  ✅ MW Adjusted: 50 MW                                          │
│  ❌ Cost: NOT INCLUDED                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  BALANCING SERVICES COSTS (DISBSAD)                             │
├─────────────────────────────────────────────────────────────────┤
│  ✅ Asset: OFR-UKPR-6                                           │
│  ✅ Cost: £6,450.00                                             │
│  ✅ Volume: 50 MWh                                              │
│  ✅ Service Type: Flexibility                                   │
│  ❌ Transmission Wind: NOT INCLUDED                            │
└─────────────────────────────────────────────────────────────────┘
```

**They're measuring different things:**
- BOALF = Physical actions (MW up/down instructions)
- DISBSAD = Financial settlements (£ paid for services)

**For transmission wind constraints:**
- Action recorded: ✅ YES (in BOALF)
- Cost recorded: ❌ NO (not in DISBSAD or any public API)

---

## 📈 What We CAN Calculate

### Implied Cost (Rough Estimate)

**Transmission Wind Constraints (Last 7 Days):**
- Actions: 5,790
- MW Adjusted: 189,435 MW

**Typical Constraint Payment Range:**
- Curtailment (turn down): £0-150/MWh
- Depends on: Contract terms, time of day, market conditions

**Rough Estimate:**
```
If average payment = £50/MWh (conservative):
189,435 MWh × £50/MWh = £9.5M

If average payment = £100/MWh (realistic):
189,435 MWh × £100/MWh = £18.9M
```

**But this is pure speculation** - actual costs could be:
- Fixed contracts (CfD - Contracts for Difference)
- Negative pricing (generators pay to stay on)
- Zero payment (curtailment rights in connection agreement)
- Market-based (spot price compensation)

### What We Actually Know

**Certainty Level:**
```
Actions:        ✅ 100% certain (from BOALF)
MW Adjusted:    ✅ 100% certain (from BOALF)
Timing:         ✅ 100% certain (from BOALF)
Duration:       ✅ 100% certain (from BOALF)
Cost:           ❌ 0% certain (NOT in any public dataset)
```

---

## 🛠️ Why Dashboard Shows "N/A"

### Data Integrity Decision

**Option 1: Show estimate (£9.5M - £18.9M)**
- ❌ Misleading - could be wildly wrong
- ❌ No way to validate
- ❌ Mixes real data with speculation

**Option 2: Show "N/A" ✅**
- ✅ Honest - we don't have this data
- ✅ Accurate - prevents misinformation
- ✅ Clear - user knows what's missing

**Current Implementation:**
```python
# In update_bg_live_dashboard.py
costs = bq_client.query(costs_query).to_dataframe()

if not costs.empty:
    regions = regions.merge(costs, on='region', how='left')
    regions['cost_thousands'] = regions['cost_thousands'].fillna(0)
else:
    # No cost data available
    regions['cost_thousands'] = 'N/A'
```

**Result:** Dashboard correctly shows "N/A" rather than false precision

---

## 📋 Summary Table: Data Availability

| Metric | BOALF | DISBSAD | NETBSAD | Status |
|--------|-------|---------|---------|--------|
| **Transmission Wind Actions** | ✅ YES | ❌ NO | ❌ NO | Available |
| **Action Timestamps** | ✅ YES | ❌ NO | ❌ NO | Available |
| **MW Adjusted** | ✅ YES | ❌ NO | ❌ NO | Available |
| **Unit IDs** | ✅ YES | ❌ NO | ❌ NO | Available |
| **Individual Costs** | ❌ NO | ❌ NO | ❌ NO | **NOT AVAILABLE** |
| **Aggregated Costs** | ❌ NO | ❌ NO | 🟡 YES* | *Market-wide only |

**Legend:**
- ✅ YES = Data available with unit-level detail
- 🟡 YES* = Data available but aggregated/no unit detail
- ❌ NO = Data not available in this dataset

---

## 🔮 Potential Solutions

### 1. Request Elexon Add to BMRS API

**Contact:**
- Email: bmrs@elexon.co.uk
- Request: Unit-level constraint cost data
- Dataset: DISBSAD expansion to include transmission constraints
- Justification: Transparency, market analysis, academic research

**Likelihood:** Low (commercially sensitive data)

### 2. Use Alternative Data Sources

**National Grid ESO Reports:**
- Monthly Constraint Management Reports
- Annual costs published (£1-2 billion/year total)
- But: Aggregated by region, not unit-level

**Freedom of Information Request:**
- Request: Unit-level constraint costs for specific wind farms
- Issue: Could be refused as commercially sensitive

### 3. Infer from Related Data

**Approach:**
```sql
-- Correlate BOALF actions with market prices
SELECT 
  boalf.bmUnit,
  COUNT(*) as actions,
  AVG(costs.systemSellPrice) as avg_imbalance_price,
  SUM(ABS(boalf.levelTo - boalf.levelFrom)) as total_mw
FROM bmrs_boalf boalf
JOIN bmrs_costs costs 
  ON boalf.settlementDate = costs.settlementDate
  AND boalf.settlementPeriod = costs.settlementPeriod
WHERE boalf.soFlag = TRUE
GROUP BY boalf.bmUnit
```

**Then estimate:**
```python
implied_cost = total_mw * avg_imbalance_price * constraint_premium_factor
```

**Issue:** Still speculation, no validation possible

---

## ✅ Recommendation

**Keep showing "N/A" for constraint costs**

**Reasoning:**
1. **Data doesn't exist** in public BMRS API
2. **Estimates would be inaccurate** (±50% error range)
3. **Transparency** - user knows what's missing
4. **Consistency** - we show real data or "N/A", never guesses

**Alternative Display:**
```
Region                   Actions  Units  MW Adjusted  Cost (£k)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Transmission Wind      5,790     26    189,435      N/A*

* Constraint costs not published in BMRS API
  Estimated range: £9.5M - £18.9M (based on typical rates)
  See DISBSAD_CONSTRAINT_COSTS_EXPLAINED.md for details
```

**Trade-off:** Adds context but risks being seen as providing unreliable estimates

---

## 📚 Related Documentation

- **BOALF Schema:** `docs/STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **DISBSAD Analysis:** `docs/DISBSAD_OFR_PRICING_ANALYSIS.md`
- **Geographic Constraints:** `docs/GEOGRAPHIC_CONSTRAINTS_COMPLETE.md`
- **Data Accuracy:** `docs/GEOGRAPHIC_CONSTRAINTS_DATA_ACCURACY_FIX.md`

---

## 🎯 Key Takeaway

**Question:** "Why can't we get cost data?"

**Answer:** Because **transmission constraint costs are not published** in any unit-level public dataset. The £6,450 example you saw was from **OFR flexibility services**, which are completely separate from transmission wind constraint payments.

**What we have:**
- ✅ Constraint actions: 5,790 (transmission wind)
- ✅ MW curtailed: 189,435 MW
- ✅ Timing and duration: Complete

**What we don't have:**
- ❌ Cost per action
- ❌ Payment terms
- ❌ Total constraint costs for specific units

**Why "N/A" is correct:**
- Honest: We don't have this data
- Accurate: Prevents false precision
- Standard: Same reason OFR costs can't be regionally attributed

---

*Last Updated: December 9, 2025*  
*This is a data availability limitation, not a system bug*
