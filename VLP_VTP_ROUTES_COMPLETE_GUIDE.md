# VLP/VTP Routes for Battery Revenue: Complete Analysis

**Date**: December 5, 2025  
**Status**: ✅ Production Ready - View Created, Documentation Complete  
**Key Finding**: VLP aggregator route saves £95k upfront costs for 25 MW battery

---

## Executive Summary

This document explains **why Virtual Lead Party (VLP) and Virtual Trading Party (VTP) routes exist** and how batteries can participate in the Balancing Mechanism without expensive direct BSC accreditation.

### The Problem: Direct BSC Accreditation is Expensive

- **Setup costs**: £50k-£150k+ (legal, systems, compliance)
- **Annual fees**: £10k-£25k+ BSC membership
- **Time to market**: 6-12 months
- **Operational overhead**: Dedicated BSC team required

### The Solution: VLP Aggregator Route

- **Setup costs**: ~£5k (contract with VLP)
- **Annual fees**: 10-30% revenue share (£96k net vs £110k net for 25 MW battery)
- **Time to market**: 4-8 weeks
- **Operational overhead**: Minimal (VLP handles BSC complexity)

---

## BSC Definitions: Bids vs Offers

Per **Elexon guidance** and **BSCP01**:

### Offers
> "An Offer indicates a willingness to **increase the level of generation** or **reduce the level of demand**."

Examples:
- Generator: Increase export to grid (turn up generation)
- BESS: Discharge battery (reduce demand / add generation)
- Load: Reduce consumption (demand turn down)

### Bids
> "A Bid is a proposal to **reduce generation** or **increase demand**."

Examples:
- Generator: Reduce export to grid (**curtailment**)
- BESS: Charge battery (increase demand / soak excess)
- Load: Increase consumption (demand turn up)

### ESO Usage

- **System SHORT** (need more power): ESO accepts **OFFERS** (increase generation / reduce demand)
- **System LONG** (excess power): ESO accepts **BIDS** (reduce generation / increase demand)

---

## How This Applies to VLPs and VTPs

### Virtual Lead Party (VLP)

From **BSCP01** and **Wider Access Guidance**:

- **Definition**: Independent aggregators who register **Secondary BM Units (sBMUs)**
- **Purpose**: Provide balancing services via BM without owning physical assets
- **Capability**: Submit bids/offers same as traditional generators/suppliers
- **BSC Status**: VLP is already BSC accredited (passes through to aggregated assets)

### Virtual Trading Party (VTP)

- **Definition**: BSC Party role focused on wholesale trading (ECVNs/MVRNs)
- **Purpose**: Trade energy contracts rather than physical balancing
- **BM Participation**: Can also participate in BM if desired
- **Use Case**: Large battery portfolios (50+ MW) with in-house trading desk

### Key Insight

✅ **Bid/offer definitions and BOALF data model apply identically to VLPs and VTPs**  
✅ **VLPs avoid BSC accreditation costs by aggregating via licensed VLP party**  
✅ **Revenue calculation: accepted MWh × acceptance price (from bmrs_boalf)**

---

## BigQuery Implementation

### View Created: `v_bm_curtailment_classified`

**Location**: `inner-cinema-476211-u9.uk_energy_prod.v_bm_curtailment_classified`  
**Purpose**: Classify all BOALF bid-offer acceptances per BSC definitions  
**Status**: ✅ Deployed (December 5, 2025)

### Classification Logic

```sql
CASE
  -- CURTAILMENT: ESO taking generation off system
  WHEN bid_offer_type = 'BID' AND bmu_type IN ('GENERATOR', 'RENEWABLE_GEN') 
    THEN 'CURTAIL_GEN'
  
  -- TURN UP DEMAND: ESO soaking up excess (BESS charging)
  WHEN bid_offer_type = 'BID' AND bmu_type IN ('LOAD', 'VLP', 'BESS') 
    THEN 'TURN_UP_DEMAND'
  
  -- TURN UP GEN: ESO adding generation to system
  WHEN bid_offer_type = 'OFFER' AND bmu_type IN ('GENERATOR', 'RENEWABLE_GEN') 
    THEN 'TURN_UP_GEN'
  
  -- TURN DOWN DEMAND: BESS discharging (reduce demand / add generation)
  WHEN bid_offer_type = 'OFFER' AND bmu_type IN ('LOAD', 'VLP', 'BESS') 
    THEN 'TURN_DOWN_DEMAND'
END AS eso_action_type
```

### Revenue Calculation

```sql
bm_revenue_gbp = (accepted_volume_mw * duration_hours) * acceptance_price_gbp_mwh
```

### Data Sources

1. **bmrs_boalf**: Bid-Offer Acceptance data (11.3M rows, 2022-2025)
2. **bmrs_bod**: Bid-Offer prices (391M rows)
3. **Join logic**: Match on bmUnit + settlementDate + settlementPeriod

---

## Route Comparison: VLP vs Direct BSC

### Direct BSC Accreditation Route

**Requirements**:
- BSC Party accreditation (£50k-£150k legal/setup)
- Annual BSC membership fees (£10k-£25k+)
- Credit cover requirements (£££ collateral)
- P272 compliant metering infrastructure
- Dedicated BSC operations team
- Ongoing compliance/audit costs

**Benefits**:
- ✅ Direct settlement from BSCCo
- ✅ Full control over BMU registration
- ✅ Can trade ECVNs/MVRNs directly
- ✅ No revenue share with aggregator

**Best for**:
- Large portfolios (> 100 MW)
- In-house trading desk
- Long-term strategic control needed

---

### VLP Aggregator Route

**Requirements**:
- Contract with licensed VLP aggregator (examples: Limejump, Flexitricity, Kiwi Power)
- Metering (VLP handles P272 compliance)
- Operational coordination with VLP

**Benefits**:
- ✅ **No BSC accreditation costs** (VLP already accredited)
- ✅ VLP handles all BSC settlement complexity
- ✅ **Faster to market** (weeks not months)
- ✅ Shared infrastructure costs
- ✅ VLP expertise in BM optimization

**Trade-offs**:
- ⚠️  Revenue share with VLP (typically 10-30% of BM revenue)
- ⚠️  Less control over bidding strategy
- ⚠️  Dependent on VLP's systems/performance

**Best for**:
- Small-medium batteries (< 50 MW)
- Fast time to market
- No in-house BSC expertise

---

### VTP (Virtual Trading Party) Route

**Requirements**:
- BSC Party accreditation (same as direct route)
- Trading systems/expertise
- Can also participate in BM if desired

**Focus**: Wholesale trading (ECVNs/MVRNs) rather than BM

**Best for**:
- Large battery portfolios (50-100 MW+)
- In-house trading desk
- Want direct wholesale market access
- BM participation secondary to trading

---

## Cost Analysis: 50 MWh / 25 MW Battery

### VLP Route

| Item | Amount |
|------|--------|
| **Setup Cost** | £5,000 |
| **BM Revenue (gross)** | £113,000/month |
| **VLP Fee (15%)** | -£17,000/month |
| **Net BM Revenue** | **£96,000/month** |
| **Time to Market** | 4-8 weeks |

### Direct BSC Route

| Item | Amount |
|------|--------|
| **Setup Cost** | £100,000+ |
| **BM Revenue (gross)** | £113,000/month |
| **BSC Costs (annual £35k)** | -£3,000/month |
| **Net BM Revenue** | **£110,000/month** |
| **Time to Market** | 6-12 months |

### Break-Even Analysis

- **Upfront savings**: £95,000 (£100k - £5k)
- **Monthly difference**: £14,000 (£110k - £96k)
- **Break-even period**: **7 months** (£95k / £14k)

### Verdict: VLP Route Recommended

✅ **Save £95k+ upfront**  
✅ **Faster to market** (4-8 weeks vs 6-12 months)  
✅ **Only £14k/month difference**  
✅ **Can switch to direct route later if portfolio grows**

---

## Route Recommendations by Battery Size

| Battery Size | Recommended Route | Reasoning |
|--------------|-------------------|-----------|
| **< 10 MW** | VLP aggregator | Lowest overhead, BSC costs don't justify |
| **10-50 MW** | VLP or Supplier PPA | Depends on revenue split negotiation |
| **50-100 MW** | Supplier PPA or VTP | Trading focus, can justify BSC costs |
| **> 100 MW** | Direct BSC + VTP | Justify fixed costs with volume |

---

## BOALF Data Status

### Current State

- **Table**: `bmrs_boalf` (11.3M rows)
- **Date Range**: 2022-01-01 to 2025-10-28
- **Unique BMUs**: 668
- **Potential BESS/VLP**: 256,338 acceptances
- **View**: `v_bm_curtailment_classified` ✅ Created

### Data Gap

⚠️ **No recent data** (last date: Oct 28, 2025)  
⚠️ **Need**: IRIS B1770 configuration for real-time BOALF stream

### Next Steps

1. ✅ View created and tested
2. ⏳ Configure IRIS B1770 for real-time BM data
3. ⏳ Backfill Oct 29 - Dec 5 BOALF data
4. ⏳ Update Battery_Revenue_Analysis sheet with VLP comparison

---

## Revenue Reality Check

### From Previous Analysis

**Arbitrage Revenue** (PROVEN):
- £120,531/month net (energy arbitrage via imbalance settlement)
- Based on bmrs_costs (system prices)
- **No special contracts needed** - basic electricity market

**BM Revenue** (CONDITIONAL):
- £112,946/month gross (via bmrs_boalf acceptances)
- **Requires**: VLP contract OR direct BSC accreditation
- **VLP route**: £96k/month net (after 15% VLP fee)
- **Direct route**: £110k/month net (after BSC costs)

### Combined Total (VLP Route)

- Arbitrage: £120k/month (PROVEN)
- BM via VLP: £96k/month (CONDITIONAL on VLP contract)
- **Total**: £216k/month

### Important Distinction

1. **Arbitrage** (£120k) = basic imbalance settlement, no BM participation
2. **BM Revenue** (£96k) = additional revenue from BM bids/offers via VLP
3. These are **complementary** not double-counting

---

## Known VLP Aggregators (UK Market)

1. **Limejump** (Shell subsidiary) - Major VLP, 1+ GW portfolio
2. **Flexitricity** (Centrica subsidiary) - Demand response + storage
3. **Kiwi Power** - Independent aggregator
4. **Enel X** - Global flexibility provider
5. **Origami Energy** - AI-driven optimization
6. **Habitat Energy** - Trading + optimization platform
7. **Open Energi** - Dynamic Demand + storage

### Typical VLP Contract Terms

- **Revenue share**: 10-30% of gross BM revenue
- **Contract length**: 1-5 years
- **Exclusivity**: Often required (can't use multiple VLPs)
- **Minimum size**: Typically 1 MW+ (some accept smaller portfolios)
- **Services**: BM bidding, optimization, settlement, reporting

---

## Files Created

### SQL View
- **File**: `create_bm_curtailment_view.sql`
- **Purpose**: Define classification logic per BSC definitions
- **Status**: ✅ Deployed in BigQuery

### Analysis Script
- **File**: `analyze_vlp_bm_revenue.py`
- **Purpose**: Query and analyze VLP/BESS BM revenue
- **Features**:
  - Action type breakdown (curtail/turn-up/turn-down)
  - Generator vs BESS comparison
  - Top VLP units ranking
  - Route comparison documentation

### Documentation
- **File**: `VLP_VTP_ROUTES_COMPLETE_GUIDE.md` (this file)
- **Purpose**: Complete reference for VLP/VTP routes
- **Audience**: Business stakeholders, technical team

---

## Technical References

### BSC Code Documents (from vlp_documents_complete.csv)

1. **BSCP01**: Overview of Trading Arrangements
2. **BSCP15**: BM Unit Registration
3. **BSC Section Q**: Balancing Mechanism Activities
4. **P415**: Facilitating Access to Wholesale Markets for Flexibility Dispatched by VLPs
5. **P444**: Compensation for Virtual Lead Party actions in the Balancing Mechanism
6. **Wider Access Guidance**: For Virtual Lead Parties (VLPs) and Asset Metering VLPs

### Key Legal Changes

- **P305** (Nov 2015): Merged SSP/SBP to single imbalance price
- **P415** (Oct 2023): VLP access to wholesale markets (Ofgem approved)
- **P444** (Apr 2025): VLP compensation for BM actions (Ofgem approved)
- **CMP295** (Nov 2019): CUSC contractual arrangements for VLPs

---

## Contact & Support

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Last Updated**: December 5, 2025  
**Status**: ✅ Production Ready

---

## Appendix: Terminology Clarification

### Curtailment
- **Traditional meaning**: Paying generators to reduce output (wind/solar)
- **BM context**: Any ESO action to "take generation off system" including:
  - Generator BIDs (reduce export)
  - BESS BIDs (charge = increase demand = reduce net export)

### Energy Action vs Service Payment
- **Energy action**: Physical MWh moved (charged to BESS, discharged from BESS)
- **Service payment**: Payment for availability or capability (CM, FR, DR)
- **BM revenue**: Mix of both (utilisation price × volume)

### Behind-the-Meter (BTM) vs Standalone
- **BTM**: Battery co-located with demand site (avoids import charges)
- **Standalone**: Battery grid-connected (pays import charges)
- **VLP route**: Works for both configurations

---

*End of Document*
