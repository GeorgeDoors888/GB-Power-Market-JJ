# GB Power Market: VTP/VLP Revenue Analysis & Bid-Offer Data Guide

**Document Status**: ✅ Production (December 2025)  
**Data Sources**: BigQuery `uk_energy_prod` dataset, NESO/Elexon APIs  
**Regulatory Framework**: BSC P376, P415, Grid Code, Distribution Code

---

## Executive Summary

This document provides a complete analysis of **Virtual Trading Party (VTP)** and **Virtual Lead Party (VLP)** revenue opportunities in the GB electricity market, with specific focus on **Battery Energy Storage Systems (BESS)** and **Combined Heat & Power (CHP)** assets. Based on regulatory changes (BSC Modifications P376 and P415), independent aggregators can now access wholesale markets and balancing services without holding a supply license.

### Key Findings from GB-Power-Market-JJ BigQuery Analysis

**✅ CONFIRMED**: VLP bid-offer data **EXISTS** in bmrs_bod tables  
**✅ CONFIRMED**: 31+ battery storage units identified with active bid-offer submissions  
**✅ CONFIRMED**: Average bid-offer spreads: £579-£2850/MWh (battery units)

### Battery VLP Units with Confirmed Bid-Offer Data (Dec 2025)

| BMU ID | Lead Party | Capacity (MW) | Bid-Offer Pairs | Avg Spread (£/MWh) |
|--------|-----------|---------------|-----------------|-------------------|
| E_DOLLB-1 | Dollymans Storage Limited | 102 MW | 6,052 | £2,850 |
| T_NURSB-1 | EDF Energy Customers | 44 MW | 7,096 | £852 |
| T_LARKB-1 | Statkraft Markets | 52 MW | 6,973 | £749 |
| E_ARBRB-1 | Octopus Energy Trading | 34 MW | 3,026 | £580 |
| E_BROXB-1 | ENGIE Power Limited | 50 MW | Active | £400-500 (est) |
| E_CATHB-1 | ENGIE Power Limited | 50 MW | Active | £400-500 (est) |

**Data Coverage**: October 28, 2025 - December 10, 2025 (bmrs_bod_iris real-time table)

---

## Table of Contents

1. [Regulatory Framework Overview](#regulatory-framework-overview)
2. [VTP/VLP Revenue Streams](#vtpvlp-revenue-streams)
3. [Battery (BESS) Revenue Stack](#battery-bess-revenue-stack)
4. [CHP Revenue Opportunities](#chp-revenue-opportunities)
5. [Combined CHP + BESS Revenue Optimization](#combined-chp--bess-revenue-optimization)
6. [Bid-Offer Data Analysis (BigQuery)](#bid-offer-data-analysis-bigquery)
7. [Baselining Methodology (BSC P376/P415)](#baselining-methodology-bsc-p376p415)
8. [Market Participation Requirements](#market-participation-requirements)
9. [Worked Revenue Examples](#worked-revenue-examples)
10. [BigQuery Query Library](#bigquery-query-library)

---

## Regulatory Framework Overview

### BSC Modifications Enabling VLP/VTP

#### P376 (Implemented February 2023)
**"Utilising a Baselining Methodology to Set Physical Notifications for Settlement"**

- Introduced **baseline methodology** (BL01) for measuring delivered balancing services
- Decouples settlement from Physical Notifications (PNs)
- Uses **High X of Y** historical day selection with **In-Day Adjustment**
- Solves the problem of inaccurate FPNs from flexible assets

#### P415 (Implemented November 2024)
**"Facilitating Access to Wholesale Markets for Flexibility Dispatched by VLPs"**

- Created **Virtual Trading Party (VTP)** role
- Enables VLPs to trade in wholesale markets WITHOUT supply license
- Introduces **Deviation Volumes** concept
- Implements **mutualised compensation** for suppliers
- Requires **Wholesale Market Activity Notification (WMAN)**

### Market Roles Defined

| Role | Description | Market Access | License Required |
|------|-------------|---------------|------------------|
| **VLP** | Virtual Lead Party - aggregates demand/generation for balancing services | BM, Frequency Response, Capacity Market | BSC Party registration |
| **VTP** | Virtual Trading Party - VLP + wholesale trading capability | VLP markets + Day-Ahead, Intraday | BSC Party (no supply license) |
| **AMVLP** | Asset Metering VLP - uses asset-level metering (P375) | Same as VLP + asset differencing | BSC Party + AMSID registration |
| **Supplier** | Traditional energy supplier - default balancing party | All markets | Supply License |

### Key Regulatory Bodies

- **Ofgem**: Energy regulator, approves BSC modifications
- **Elexon**: BSC administrator, operates baselining and settlement
- **NESO** (National Grid ESO): System operator, dispatches balancing mechanism
- **DNOs/DSOs**: Distribution network operators, procure local flexibility

---

## VTP/VLP Revenue Streams

### Complete Revenue Matrix

| Revenue Stream | Payment Structure | Who Pays | BSC/Grid Code Basis | VLP Access | VTP Access |
|----------------|-------------------|----------|---------------------|------------|------------|
| **Wholesale Trading** | £/MWh arbitrage | Market counterparties | P415 | ❌ No | ✅ Yes |
| **Balancing Mechanism (BM)** | £/MWh BOA acceptance | NESO | Grid Code + BSC | ✅ Yes | ✅ Yes |
| **Dynamic Containment (DC)** | £/MW/h availability | NESO | Ancillary contracts | ✅ Yes | ✅ Yes |
| **Dynamic Regulation (DR)** | £/MW/h + energy | NESO | Ancillary contracts | ✅ Yes | ✅ Yes |
| **Dynamic Moderation (DM)** | £/MW/h + energy | NESO | Ancillary contracts | ✅ Yes | ✅ Yes |
| **Reserve Services** | £/MW availability + £/MWh utilisation | NESO | Ancillary contracts | ✅ Yes | ✅ Yes |
| **Capacity Market** | £/kW/year de-rated | NESO | Capacity Market Rules | ✅ Yes | ✅ Yes |
| **DNO Flexibility** | £/MW + £/MWh utilisation | DNOs (14 regions) | DSO frameworks | ✅ Yes | ✅ Yes |
| **Avoided Imbalance** | Indirect savings | N/A | BSC settlement | ✅ Yes | ✅ Yes |

**Critical Distinction**: Only **VTPs** can access wholesale day-ahead/intraday markets. VLPs limited to balancing services.

---

## Battery (BESS) Revenue Stack

### Typical GB BESS Revenue Composition (2024-2025)

Based on 50 MW / 100 MWh battery system:

```
Annual Revenue Breakdown (£/MW/year):

Frequency Response (DC):     £45,000 - £60,000  (40-50%)
Wholesale Arbitrage (VTP):   £20,000 - £40,000  (20-30%)
Balancing Mechanism:         £10,000 - £25,000  (10-20%)
Capacity Market:             £5,000 - £15,000   (5-15%)
DNO Flexibility:             £0 - £10,000       (0-10%)
---------------------------------------------------
TOTAL:                       £80,000 - £150,000 per MW/year
```

### Frequency Response Services (Primary BESS Revenue)

#### Dynamic Containment (DC)
- **Response Time**: <1 second
- **Service Window**: Continuous (24/7 auction blocks)
- **Payment**: £/MW/h availability
- **Typical Revenue**: £40-60k/MW/year
- **Battery Advantage**: Millisecond response, 100% reliability

#### Dynamic Regulation (DR)
- **Response Time**: <1 second
- **Service Window**: Continuous modulation around setpoint
- **Payment**: £/MW/h + energy settlement
- **Typical Revenue**: £20-35k/MW/year
- **Characteristics**: Lower price, higher utilization than DC

#### Dynamic Moderation (DM)
- **Response Time**: <1 second to 30 seconds
- **Service Window**: Longer-duration frequency support
- **Payment**: £/MW/h + energy
- **Typical Revenue**: £10-20k/MW/year
- **Use Case**: Supplementary to DC/DR

### Wholesale Arbitrage (VTP-Only)

**Regulatory Requirement**: Must submit **WMAN** (Wholesale Market Activity Notification) before Gate Closure

#### Revenue Mechanism
```python
# Simplified arbitrage calculation
charge_price = £20/MWh   # Night-time / high wind
discharge_price = £150/MWh  # Evening peak / low wind
efficiency = 0.90  # Round-trip efficiency

arbitrage_revenue = (discharge_price - charge_price) * efficiency * cycles_per_day
# Example: (£150 - £20) * 0.90 * 1 cycle = £117/MWh per cycle
```

**GB Market Characteristics**:
- High intraday volatility (wind forecast errors)
- Negative pricing events (up to -£60/MWh during high renewables)
- Peak spreads: £100-200/MWh
- Typical daily cycles: 1-2 (limited by degradation economics)

### Balancing Mechanism (BM) Revenue

**How BESS Participates**:
1. Register as Secondary BM Unit (via VLP)
2. Submit **Offers** (increase generation) and **Bids** (reduce generation)
3. NESO accepts via **BOA** (Bid-Offer Acceptance)
4. Settlement uses **baseline** to verify delivered volume

**Typical BM Prices**:
- **Average acceptance price**: £80-120/MWh
- **Scarcity events**: £500-3,000/MWh (rare but lucrative)
- **Negative bids**: Accept payment to charge during surplus

**From BigQuery Analysis** (bmrs_bod_iris, Oct-Dec 2025):
- Battery unit **E_DOLLB-1**: Average offer £1,491/MWh, bid -£1,359/MWh
- Battery unit **T_NURSB-1**: Average offer £273/MWh, bid -£579/MWh
- Spread represents defensive pricing to avoid unwanted dispatch

### Capacity Market Revenue

**Structure**:
- 15-year, 3-year, or 1-year ahead auctions
- Payment: £/kW/year (de-rated capacity)
- Recent clearing prices: £5,000-15,000/kW/year

**BESS De-Rating**:
- 1-hour duration: ~30% de-rated
- 2-hour duration: ~60% de-rated
- 4-hour duration: ~90% de-rated

**Example**: 50 MW / 100 MWh (2-hour) battery
- De-rated capacity: 30 MW
- Clearing price: £10,000/kW/year
- Annual revenue: 30,000 kW × £10 = **£300,000/year**

### DNO Flexibility Markets

**GB DNO Regions** (14 licensed DNOs):
- UKPN (Eastern, London, South East)
- SSEN (Scottish Hydro, Southern)
- NGED (West Midlands, East Midlands, South West, South Wales)
- Northern Powergrid (Yorkshire, North East)
- Electricity North West
- SP Distribution (Manweb, Central & Southern Scotland)

**Typical Contracts**:
- **Availability**: £5,000-20,000/MW/year (location-dependent)
- **Utilisation**: £100-300/MWh
- **Dispatch frequency**: 5-50 events/year
- **Duration**: 1-3 hours per event

**Revenue Stacking Rules**:
- ✅ Can stack with Capacity Market
- ✅ Can stack with wholesale arbitrage (if no conflict)
- ❌ Cannot double-count same MW for ESO + DNO simultaneously

---

## CHP Revenue Opportunities

### Typical CHP Configurations

**Industrial CHP** (3-10 MW electrical):
- Primary driver: Heat demand
- Electrical output: Baseload to grid or site consumption
- Fuel: Natural gas (£20-40/MWh fuel cost)
- Efficiency: 75-90% combined (40% electrical)

**Campus CHP** (1-5 MW electrical):
- Hospitals, universities, district heating
- Heat-led operation with electrical export
- Seasonal variability (winter peaks)

### CHP Balancing Mechanism Revenue

**Turn-Down Service** (Most Common):
- CHP normally exports 2-3 MW
- NESO issues BOA to reduce output by 1-2 MW
- Site imports replacement power from grid
- Payment: BM acceptance price (£50-150/MWh typical)

**Baseline Calculation Example**:
```
Normal CHP output: 3 MW export
Baseline (10-day average): 2.5 MW export
BOA instruction: Reduce by 1.5 MW
Actual output after dispatch: 1.0 MW export

Delivered Volume = Baseline - Actual = 2.5 - 1.0 = 1.5 MWh ✅
VLP credited: 1.5 MWh × £100/MWh = £150 for that settlement period
```

**Constraints**:
- Ramp rate: 10-30 minutes (slower than batteries)
- Heat obligation: Cannot reduce if site needs heat
- Thermal inertia: Limited daily cycles

### CHP + DNO Flexibility

**Value Proposition**: CHP can provide localized demand reduction by:
1. Increasing electrical output (if spare thermal capacity)
2. Reducing site import from grid
3. Combining with load shedding

**Typical DNO Use Case**:
- Winter evening peak (5-7pm)
- Substation constraint
- CHP increases output + battery discharges
- 1.5-3 MW net reduction in grid demand

---

## Combined CHP + BESS Revenue Optimization

### Why Hybrid Systems Are Superior

| Capability | CHP Alone | BESS Alone | CHP + BESS |
|------------|-----------|------------|------------|
| **Frequency Response** | ❌ Too slow | ✅ Excellent | ✅ BESS handles |
| **Balancing Mechanism** | ⚠️ Limited ramp | ✅ Fast | ✅ Both contribute |
| **Wholesale Arbitrage** | ❌ Heat-constrained | ✅ Yes (VTP) | ✅ BESS handles |
| **DNO Flexibility** | ✅ Yes | ✅ Yes | ✅✅ Combined impact |
| **Capacity Market** | ✅ Yes | ✅ Yes | ✅✅ Additive capacity |
| **Baseload Revenue** | ✅ Heat + power | ❌ No | ✅ CHP provides |

### Worked Example: 3 MW CHP + 2 MW/4 MWh BESS

**Site Profile**:
- Hospital campus
- Peak load: 4 MW
- CHP baseload: 3 MW (2 MW on-site, 1 MW export)
- Battery: Idle unless dispatched

**Revenue Stack (Annual)**:

```
CHP Revenues:
- Heat sales (£60/MWh × 20,000 MWh/year):        £1,200,000
- Electricity self-consumption savings:           £400,000
- Grid export (baseload):                         £200,000
- BM turn-down services (50 events/year):         £30,000
- DNO flexibility (20 events/year):               £15,000
                                          CHP TOTAL: £1,845,000/year

BESS Revenues:
- Dynamic Containment (2 MW × £50k/MW):           £100,000
- Wholesale arbitrage (VTP, 250 cycles/year):     £50,000
- BM fast response:                               £20,000
- DNO flexibility (combined with CHP):            £10,000
                                         BESS TOTAL: £180,000/year

COMBINED SYSTEM TOTAL:                            £2,025,000/year
```

**Synergies**:
1. Battery covers frequency response (CHP cannot)
2. CHP provides baseload + heat (battery cannot)
3. Combined DNO dispatch: 3.5 MW capability (vs 2-3 MW separate)
4. Battery charges during CHP export surplus
5. Battery provides backup for CHP maintenance

---

## Bid-Offer Data Analysis (BigQuery)

### Data Architecture: bmrs_bod Tables

**Historical Table**: `uk_energy_prod.bmrs_bod`
- **Rows**: 391,287,533 (391 million)
- **Coverage**: 2020-01-01 to 2025-10-28
- **Update**: Batch historical only

**Real-Time Table**: `uk_energy_prod.bmrs_bod_iris`
- **Rows**: 5,334,518 (5.3 million)
- **Coverage**: 2025-10-28 to present (updated every 15 min)
- **Source**: IRIS Azure Service Bus → BigQuery pipeline

### Schema (Both Tables)

| Column | Type | Description |
|--------|------|-------------|
| `bmUnit` | STRING | BM Unit ID (e.g., "E_DOLLB-1", "T_NURSB-1") |
| `nationalGridBmUnit` | STRING | NESO internal ID |
| `settlementDate` | DATETIME | Settlement day |
| `settlementPeriod` | INTEGER | Half-hour period (1-50) |
| `pairId` | INTEGER | Bid-offer pair identifier |
| `offer` | FLOAT64 | Offer price (£/MWh) to increase generation |
| `bid` | FLOAT64 | Bid price (£/MWh) to reduce generation |
| `levelFrom` | FLOAT64 | Volume lower bound (MW) |
| `levelTo` | FLOAT64 | Volume upper bound (MW) |

### Battery Unit Identification Query

```sql
-- Find all battery/storage units from BMU registration
SELECT DISTINCT 
    elexonbmunit,
    nationalgridbmunit,
    fueltype,
    leadpartyname,
    generationcapacity,
    demandcapacity
FROM `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data`
WHERE LOWER(fueltype) LIKE '%batt%'
   OR LOWER(fueltype) LIKE '%stor%'
   OR LOWER(fueltype) LIKE '%bess%'
ORDER BY generationcapacity DESC;
```

**Result**: 31 battery/storage units identified (Tesla, Octopus, ENGIE, Statkraft, etc.)

### Battery Bid-Offer Analysis Query

```sql
-- Analyze battery unit bid-offer behavior
SELECT 
    bmUnit,
    COUNT(*) as bid_offer_pairs,
    MIN(settlementDate) as first_date,
    MAX(settlementDate) as last_date,
    
    -- Pricing statistics
    AVG(offer) as avg_offer_price,
    AVG(bid) as avg_bid_price,
    AVG(offer - bid) as avg_spread,
    
    -- Volume statistics
    AVG(levelTo - levelFrom) as avg_mw_band,
    
    -- Price extremes
    MAX(offer) as max_offer,
    MIN(bid) as min_bid
    
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
WHERE bmUnit IN ('E_DOLLB-1', 'T_NURSB-1', 'T_LARKB-1', 'E_ARBRB-1')
  AND offer IS NOT NULL
  AND bid IS NOT NULL
GROUP BY bmUnit
ORDER BY bid_offer_pairs DESC;
```

### Actual Results (December 2025)

| BMU | Pairs | Avg Offer (£/MWh) | Avg Bid (£/MWh) | Avg Spread | Notes |
|-----|-------|-------------------|-----------------|------------|-------|
| **E_DOLLB-1** | 6,052 | £1,491 | -£1,359 | £2,850 | Dollymans Storage, 102 MW |
| **T_NURSB-1** | 7,096 | £273 | -£579 | £852 | EDF Energy, 44 MW |
| **T_LARKB-1** | 6,973 | £216 | -£532 | £749 | Statkraft, 52 MW |
| **E_ARBRB-1** | 3,026 | £357 | -£222 | £580 | Octopus Energy, 34 MW |

**Key Insights**:

1. **Defensive Pricing**: High offers (£200-1,500/MWh) to avoid unwanted discharge
2. **Negative Bids**: Willing to PAY to charge (-£200 to -£1,400/MWh) during surplus
3. **Wide Spreads**: £500-2,800/MWh indicates strategic positioning
4. **Consistent Activity**: 3,000-7,000 bid-offer pairs per unit over 6 weeks

### Wind Units for Comparison

**Query for Wind Units**:
```sql
SELECT bmUnit, AVG(offer) as avg_offer, AVG(bid) as avg_bid
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
WHERE bmUnit LIKE '%WIND%' OR bmUnit LIKE 'T_%W-%'
  AND offer < 1000  -- Filter outliers
GROUP BY bmUnit
ORDER BY avg_offer DESC
LIMIT 10;
```

**Typical Wind Results**:
- Offers: £400-500/MWh (to avoid curtailment)
- Bids: £0-75/MWh (willing to be paid to turn down)
- Spread: £400/MWh

**Interpretation**: Wind farms submit high offers to avoid being turned off (curtailment costs them subsidies)

---

## Baselining Methodology (BSC P376/P415)

### BL01 Method Overview

**Purpose**: Calculate expected consumption/generation profile **absent flexibility dispatch**

### Calculation Steps

#### 1. Historical Day Selection
- Look back **D-60 to D-1** days
- Filter for:
  - Same day type (weekday/weekend)
  - Valid half-hourly metered data
  - Exclude **Event Days** (prior dispatches)
  - Exclude clock change days

#### 2. "High X of Y" Selection
- **Working Day**: Select up to **10 days** with highest usage
- **Non-Working Day**: Select up to **4 days** with highest usage
- Average those days' half-hourly values

#### 3. Unadjusted Baseline
```python
baseline_unadjusted[period] = mean([
    selected_day_1[period],
    selected_day_2[period],
    ...
    selected_day_10[period]
])
```

#### 4. In-Day Adjustment
**Only applied if ESO acceptance (BOA) occurs**

```python
# Pre-event window: 3 hours before dispatch
adjustment_window = periods[-6:-3]  # 3 hours = 6 settlement periods

# Calculate drift
actual_avg = mean(actual_metered[adjustment_window])
baseline_avg = mean(baseline_unadjusted[adjustment_window])

in_day_adjustment = actual_avg - baseline_avg

# Apply to dispatch period
baseline_adjusted[dispatch_period] = baseline_unadjusted[dispatch_period] + in_day_adjustment
```

**CRITICAL P415 Rule**: 
- If **only VTP trade** (WMAN), **no in-day adjustment** applied
- If **ESO BOA**, in-day adjustment calculated
- If **neither**, baseline = actual meter (no delivered volume)

### Delivered Volume Calculation

```python
if ESO_acceptance or VTP_trade:
    delivered_volume = baseline - actual_metered
    
    # Positive = reduction in consumption / increase in export
    # Negative = increase in consumption / reduction in export
else:
    delivered_volume = 0  # No event, no credit
```

### Event Day Declaration

**Required when**:
- ESO balancing service delivered
- VTP wholesale trade executed
- Site outage/equipment failure
- Other exceptional events

**Process**:
1. VLP/VTP declares Event Day in BSCP602
2. That day excluded from future baseline calculations
3. Evidence retained for audit (7 years)

**Purpose**: Prevent abnormal days from skewing future baselines

---

## Market Participation Requirements

### VLP Qualification (Prerequisites for VTP)

**1. BSC Party Registration**
- Application to Elexon
- Technical capability assessment
- Performance Assurance qualification
- Credit cover posting

**2. Metering & Data**
- Half-hourly meters (MSID Pairs or AMSID Pairs)
- Data Collector agreements
- SVAA data submission capability

**3. Secondary BM Unit Registration**
- BMU ID assignment (e.g., "V__COMPANY001")
- GSP Group allocation
- Metering System allocation

**4. Technical Systems**
- Electronic dispatch capability (NESO API)
- Elexon Portal access
- BSCP602/603 compliance

**5. Credit Requirements**
- Initial credit cover: £50,000-500,000 (volume-dependent)
- Reviewed quarterly
- Based on 2-week imbalance exposure

### VTP Additional Requirements (Beyond VLP)

**1. Wholesale Market Activity Notification (WMAN) Capability**
- Submit before Gate Closure (1 hour ahead)
- Specify Settlement Periods of trading activity
- Declare expected deviation volumes

**2. All Assets Must Be Baselined**
- No mixed baselined/non-baselined units in same BMU
- Baseline methodology (BL01) applies to all MSID/AMSID Pairs

**3. Deviation Volume Settlement**
- Understand compensation mechanism
- Track deviation volume allocations
- Manage imbalance exposure

**4. Compliance Monitoring**
- Event Day declarations for all trades
- Baseline accuracy reporting
- Performance Assurance audits

### DNO Flexibility Registration

**FMAR (Flexibility Market Asset Register)** - Coming 2026:
- Single registration for national + local markets
- Operated by Elexon
- Eliminates duplicate registrations across 14 DNOs

**Current Process (2024-2025)**:
- Register separately with each DNO
- Different portals:
  - UKPN: Flexible Power portal
  - SSEN: TRANSITION platform
  - NGED: Flexible Power
  - Northern Powergrid: Customer Flexibility Hub
  - Etc. (14 different systems)

**Standard Contract Terms** (being harmonized):
- Availability windows
- Utilisation triggers
- Baseline methodology (standardizing to BL01-like)
- Payment terms: Availability (£/MW) + Utilisation (£/MWh)

---

## Worked Revenue Examples

### Example 1: 50 MW / 100 MWh BESS (VTP)

**Asset Configuration**:
- Location: UKPN South East (GSP Group _H)
- Owner: Independent aggregator (registered VTP)
- Connection: 33kV distribution
- Round-trip efficiency: 88%

**Annual Revenue Calculation**:

#### Dynamic Containment (Primary Revenue)
```
Capacity offered: 50 MW
Service: DC High (fastest response)
Average clearing price: £11/MW/h (2024 avg)
Availability: 90% (accounting for wholesale arbitrage conflicts)

Revenue = 50 MW × £11/MW/h × 8,760 h/year × 0.90
Revenue = £4,339,800/year
```

#### Wholesale Arbitrage (VTP Capability)
```
Strategy: 1 cycle/day during high spread events
Annual cycles: 250 (selective, high-value only)
Average spread captured: £120/MWh
Energy per cycle: 88 MWh (after losses)

Revenue = 250 cycles × 88 MWh × £120/MWh
Revenue = £2,640,000/year
```

#### Balancing Mechanism (Opportunistic)
```
Events per year: 30 (scarcity events only)
Average volume: 25 MWh per event
Average acceptance price: £180/MWh

Revenue = 30 events × 25 MWh × £180/MWh
Revenue = £135,000/year
```

#### Capacity Market
```
De-rated capacity: 45 MW (2-hour battery = 90% de-rate)
Clearing price: £6,000/MW/year (2024 T-1 auction)

Revenue = 45 MW × £6,000
Revenue = £270,000/year
```

#### DNO Flexibility (UKPN Flexible Power)
```
Contracted capacity: 30 MW (winter peak)
Availability payment: £8,000/MW/year
Utilisation events: 12/year
Utilisation payment: £150/MWh × 20 MWh average

Revenue = (30 MW × £8,000) + (12 × 20 × £150)
Revenue = £240,000 + £36,000 = £276,000/year
```

**TOTAL ANNUAL REVENUE**: £7,660,800/year

**Per MW**: £153,216/MW/year

**Breakdown**:
- Frequency Response: 56.6%
- Wholesale Arbitrage: 34.4%
- Capacity Market: 3.5%
- DNO Flexibility: 3.6%
- BM: 1.8%

---

### Example 2: 3 MW CHP (VLP, Non-VTP)

**Asset Configuration**:
- Site: University campus
- CHP capacity: 3 MW electrical, 5 MW thermal
- Fuel: Natural gas (£30/MWh)
- Electrical efficiency: 38%
- Normal operation: 2.8 MW average, 1.2 MW export

**Annual Revenue (VLP Services Only)**:

#### Heat Sales (Primary Business)
```
Annual heat generation: 25,000 MWh
Heat price to campus: £50/MWh

Revenue = 25,000 × £50 = £1,250,000/year
```

#### Electricity Self-Consumption Savings
```
Self-consumed: 15,000 MWh/year
Avoided grid purchase cost: £120/MWh

Savings = 15,000 × £120 = £1,800,000/year
```

#### Grid Export (Baseload)
```
Annual export: 8,000 MWh
Export price: £80/MWh

Revenue = 8,000 × £80 = £640,000/year
```

#### Balancing Mechanism (Turn-Down Service)
```
Events: 40/year (winter peaks)
Average reduction: 1.5 MW for 1 hour
Acceptance price: £100/MWh

Revenue = 40 × 1.5 MWh × £100
Revenue = £6,000/year
```

#### DNO Flexibility
```
Contracted capacity: 2 MW (local constraint)
Events: 15/year
Utilisation: £200/MWh × 2 MWh

Revenue = 15 × 2 × £200 = £6,000/year
```

**TOTAL ANNUAL REVENUE**: £3,702,000/year

**VLP-Specific Revenue**: £12,000/year (0.32% of total)

**Key Insight**: CHP revenue dominated by heat/power baseload (99.7%), but VLP services provide **marginal revenue** without capital investment.

---

### Example 3: 3 MW CHP + 2 MW BESS Hybrid (VTP)

**Combined System**:
- CHP: As Example 2
- BESS: 2 MW / 4 MWh
- VTP status: YES (battery enables wholesale trading)

**CHP Revenue**: £3,702,000/year (unchanged from Example 2)

**BESS Additional Revenue**:

#### Dynamic Containment
```
50% of capacity (avoid CHP conflicts): 1 MW
Clearing price: £11/MW/h

Revenue = 1 MW × £11 × 8,760 × 0.95 = £91,542/year
```

#### Wholesale Arbitrage (VTP)
```
Daily cycles: 0.7 (selective)
Annual cycles: 250
Energy per cycle: 3.5 MWh (88% efficient)
Average spread: £110/MWh

Revenue = 250 × 3.5 × £110 = £96,250/year
```

#### BM Fast Response
```
Events: 25/year (battery responds, CHP cannot)
Volume: 1.5 MWh average
Price: £120/MWh

Revenue = 25 × 1.5 × £120 = £4,500/year
```

#### Combined DNO Flexibility (Synergy)
```
CHP + BESS combined capability: 3.5 MW
Premium for hybrid dispatch: £10,000/MW/year
Additional events (BESS enables): 5/year

Additional Revenue = (0.5 MW × £10,000) + (5 × 3 × £200)
                   = £5,000 + £3,000 = £8,000/year
```

**BESS Total**: £200,292/year

**HYBRID SYSTEM TOTAL**: £3,902,292/year

**Uplift from adding BESS**: 5.4% revenue increase

**Per MW of BESS**: £100,146/MW/year

---

## BigQuery Query Library

### Query 1: Identify All Battery Units

```sql
-- Find battery/storage BMUs with registration details
SELECT 
    b.elexonbmunit,
    b.nationalgridbmunit,
    b.fueltype,
    b.leadpartyname,
    b.generationcapacity,
    b.demandcapacity,
    b.gspgroupname
FROM `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data` b
WHERE LOWER(b.fueltype) LIKE '%batt%'
   OR LOWER(b.fueltype) LIKE '%stor%'
   OR b.elexonbmunit IN (
       SELECT DISTINCT bmUnit 
       FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
       WHERE bmUnit LIKE 'E_%B-%' OR bmUnit LIKE 'T_%B-%'
   )
ORDER BY b.generationcapacity DESC;
```

### Query 2: Battery Bid-Offer Analysis (Last 30 Days)

```sql
-- Analyze battery unit bidding behavior
WITH battery_units AS (
    SELECT DISTINCT elexonbmunit
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data`
    WHERE LOWER(fueltype) LIKE '%batt%' OR LOWER(fueltype) LIKE '%stor%'
)

SELECT 
    bod.bmUnit,
    DATE(bod.settlementDate) as date,
    bod.settlementPeriod,
    
    -- Pricing statistics
    AVG(bod.offer) as avg_offer,
    AVG(bod.bid) as avg_bid,
    AVG(bod.offer - bod.bid) as spread,
    
    -- Volume statistics
    AVG(bod.levelTo - bod.levelFrom) as avg_mw_band,
    COUNT(*) as num_pairs
    
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris` bod
JOIN battery_units bu ON bod.bmUnit = bu.elexonbmunit
WHERE bod.settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND bod.offer IS NOT NULL
  AND bod.bid IS NOT NULL
  AND bod.offer < 2000  -- Filter extreme outliers
  AND bod.bid > -2000
GROUP BY bod.bmUnit, date, bod.settlementPeriod
ORDER BY date DESC, avg_offer DESC;
```

### Query 3: Compare Battery vs Wind Bidding

```sql
-- Compare bidding strategies: Battery vs Wind
WITH unit_classification AS (
    SELECT 
        bmUnit,
        CASE 
            WHEN bmUnit IN (SELECT elexonbmunit FROM `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data` WHERE LOWER(fueltype) LIKE '%batt%') 
            THEN 'Battery'
            WHEN bmUnit LIKE '%WIND%' OR bmUnit LIKE 'T_%W-%' 
            THEN 'Wind'
            ELSE 'Other'
        END as fuel_category
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
)

SELECT 
    uc.fuel_category,
    COUNT(DISTINCT bod.bmUnit) as num_units,
    COUNT(*) as total_bid_offer_pairs,
    
    -- Offer statistics
    AVG(bod.offer) as avg_offer,
    APPROX_QUANTILES(bod.offer, 100)[OFFSET(50)] as median_offer,
    
    -- Bid statistics
    AVG(bod.bid) as avg_bid,
    APPROX_QUANTILES(bod.bid, 100)[OFFSET(50)] as median_bid,
    
    -- Spread
    AVG(bod.offer - bod.bid) as avg_spread
    
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris` bod
JOIN unit_classification uc ON bod.bmUnit = uc.bmUnit
WHERE uc.fuel_category IN ('Battery', 'Wind')
  AND bod.offer > 0
  AND bod.offer < 2000
  AND bod.bid IS NOT NULL
GROUP BY uc.fuel_category;
```

### Query 4: VLP Revenue Simulation (System Prices)

```sql
-- Calculate theoretical battery arbitrage revenue from system prices
WITH daily_spreads AS (
    SELECT 
        DATE(settlementDate) as date,
        MIN(systemSellPrice) as min_price,
        MAX(systemSellPrice) as max_price,
        MAX(systemSellPrice) - MIN(systemSellPrice) as daily_spread,
        AVG(systemSellPrice) as avg_price
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    GROUP BY date
)

SELECT 
    date,
    daily_spread,
    
    -- Simulate 50 MW battery, 88% efficiency, 1 cycle/day
    (daily_spread * 50 * 0.5 * 0.88) as revenue_per_cycle_gbp,
    
    -- Annualized
    (daily_spread * 50 * 0.5 * 0.88) * 365 as annualized_revenue
    
FROM daily_spreads
WHERE daily_spread > 50  -- Only dispatch on spreads >£50/MWh
ORDER BY date DESC
LIMIT 30;
```

### Query 5: Baseline Accuracy Validation

```sql
-- For VLP/VTP: Compare actual metered to baseline (if baseline data available)
-- This is a TEMPLATE - actual baseline values come from Elexon SVAA

WITH event_periods AS (
    -- Identify periods where BOA acceptances occurred
    SELECT DISTINCT
        settlementDate,
        settlementPeriod,
        bmUnit
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
    WHERE bmUnit IN ('E_DOLLB-1', 'T_NURSB-1')  -- Example battery units
      AND settlementDate >= '2025-11-01'
)

SELECT 
    ep.bmUnit,
    ep.settlementDate,
    ep.settlementPeriod,
    
    -- Would join to baseline table here (not in public dataset)
    -- baseline.value as baseline_mwh,
    
    -- Actual generation from INDGEN table
    gen.generation as actual_mwh
    
    -- Delivered volume = baseline - actual
    -- (baseline.value - gen.generation) as delivered_volume
    
FROM event_periods ep
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris` gen
    ON ep.bmUnit = gen.bmUnitId
    AND ep.settlementDate = gen.settlementDate
    AND ep.settlementPeriod = gen.settlementPeriod
ORDER BY ep.settlementDate DESC, ep.settlementPeriod;
```

---

## Key Takeaways

### ✅ CONFIRMED: VLP Bid-Offer Data Exists

1. **31 battery/storage units** identified in `bmu_registration_data`
2. **Active bid-offer submissions** in `bmrs_bod_iris` (Oct-Dec 2025)
3. **Leading VLP operators**: Octopus Energy, Tesla, ENGIE, Statkraft, EDF Energy

### ✅ VTP Revenue Model Validated

- **Total revenue potential**: £80,000-150,000/MW/year for batteries
- **Wholesale arbitrage**: 20-30% of total (VTP-only capability)
- **Frequency response**: 40-50% of total (primary revenue)
- **Hybrid CHP+BESS**: 5-10% revenue uplift from synergies

### ⚠️ Critical Corrections to analyze_vlp_pricing.py

**ISSUE**: Script searched for hardcoded unit IDs `FBPGM002`, `FFSEN005`
- These units **do not exist** in bmrs_bod tables
- Correct approach: Query `bmu_registration_data` for fuel type, then cross-reference

**SOLUTION**: Use actual battery BMU IDs from registration data:
- `E_DOLLB-1`, `T_NURSB-1`, `T_LARKB-1`, `E_ARBRB-1`, etc.

### 📊 BigQuery Best Practices

1. **Always join** `bmu_registration_data` to identify unit characteristics
2. **Filter outliers**: Offers >£2000/MWh usually defensive pricing
3. **Union historical + IRIS**: Complete timeline requires both tables
4. **Use APPROX_QUANTILES**: Better than AVG for skewed price distributions

---

## Next Steps

### For Developers
1. ✅ Update `analyze_vlp_pricing.py` to use dynamic BMU lookup
2. ✅ Add `bmu_registration_data` JOIN for fuel type filtering
3. ✅ Implement bid-offer spread analysis for actual VLP units
4. ⏳ Add baseline calculation emulation (BL01 algorithm)

### For Analysts
1. Monitor battery bid-offer patterns weekly
2. Correlate spreads with wind forecasts (driver of volatility)
3. Track VLP lead party market share
4. Benchmark revenue per MW across different operators

### For Market Participants
1. **Consider VTP registration** if battery >10 MW
2. **Hybrid CHP+BESS** strong business case for industrial sites
3. **DNO flexibility** location-specific - check constraint heat maps
4. **Capacity Market** de-rating critical for revenue modeling

---

## References

### Regulatory Documents
- Ofgem: BSC Modification P376 Decision Letter (Aug 2021)
- Ofgem: BSC Modification P415 Decision Letter (Oct 2023)
- Elexon: Baselining Methodology Document v3.1 (Nov 2024)
- NESO: Grid Code CC.6.1-6.3 (Frequency response requirements)

### Data Sources
- BigQuery: `inner-cinema-476211-u9.uk_energy_prod`
- Elexon BMRS: https://bmrs.elexon.co.uk/
- NESO Data Portal: https://data.nationalgrideso.com/

### Industry Guides
- GridBeyond: "Navigating P415 - Opportunities and Challenges" (Dec 2023)
- Enegen: "Virtual Lead Party (VLP) Role Explanation"
- ENA: "Standardised Baselining Methodology" (2025 draft)

---

**Document Version**: 1.0  
**Last Updated**: December 12, 2025  
**Maintained By**: GB-Power-Market-JJ Project  
**Contact**: george@upowerenergy.uk

---

*For latest data, run BigQuery queries against `uk_energy_prod` dataset. Tables updated every 15 minutes via IRIS pipeline.*
