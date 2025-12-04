# BOD & BOALF Analysis Sheets Guide

## Overview
Two new analysis sheets added to Dashboard V3 showing detailed balancing mechanism data:
- **BOALF_Analysis** - Accepted balancing actions (what National Grid actually dispatched)
- **BOD_Analysis** - Submitted bids & offers (what generators offered to provide)

## 📊 BOALF_Analysis Sheet

### What is BOALF?
**Balancing Offer Acceptance Level - Flagged (BOALF)** contains the accepted balancing actions that National Grid ESO dispatched to balance the electricity system in real-time.

### Data Sections

#### 1. Daily Accepted Actions (Last 30 Days)
Shows day-by-day breakdown of all accepted actions:
- **Total Actions**: Number of acceptance events
- **Active Units**: How many BM units were dispatched
- **Increase MW**: Total MW of generation increases
- **Decrease MW**: Total MW of generation decreases
- **Total MW**: Sum of all MW changes

**Key Insight**: High action counts indicate system stress or volatility.

#### 2. Top 10 Most Active Units (Last 7 Days)
Identifies which generators are most frequently dispatched:
- **BM Unit**: Generator identifier (e.g., T_DINW-1)
- **Total Actions**: Number of times dispatched
- **Increase Actions**: Called to increase output
- **Decrease Actions**: Called to decrease output
- **Total MW**: Cumulative MW dispatched

**Key Insight**: Batteries (T_* prefix) often dominate due to fast response times.

#### 3. Actions by Fuel Type (Last 7 Days)
Aggregates balancing actions by technology:
- **Fuel Type**: CCGT, WIND, NUCLEAR, PS (pumped storage), etc.
- **Actions**: Total acceptance count
- **Units**: Number of unique generators
- **Total MW**: Cumulative MW dispatched

**Key Insight**: CCGT and batteries are primary balancing resources. High wind curtailment (negative MW) indicates oversupply.

### Business Applications
- **Battery Arbitrage**: Units with highest action counts = most revenue opportunities
- **Market Volatility**: Daily action spikes = profitable trading periods
- **Resource Mix**: Which fuel types provide most system flexibility

---

## 📝 BOD_Analysis Sheet

### What is BOD?
**Bid-Offer Data (BOD)** contains all the prices generators submitted to National Grid for increasing (offers) or decreasing (bids) their output.

**Key Terms**:
- **Bid**: Price (£/MWh) generator will PAY to reduce output (negative revenue)
- **Offer**: Price (£/MWh) generator charges to increase output (positive revenue)
- **Spread**: Offer - Bid (wider spreads = more profit potential)

### Data Sections

#### 1. Daily Bid-Offer Statistics (Last 30 Days)
Market-wide submission trends:
- **Active Units**: Generators submitting data
- **Bid-Offer Pairs**: Total price pairs submitted
- **Avg Bid**: Average price to reduce output (£/MWh)
- **Avg Offer**: Average price to increase output (£/MWh)
- **Avg Spread**: Average price difference (£/MWh)

**Key Insight**: Increasing spreads = generators expecting volatile prices.

#### 2. Bid-Offer Spreads by Fuel Type (Last 7 Days)
Which technologies price most aggressively:
- **Fuel Type**: Technology category
- **Units**: Number of generators
- **Avg Bid/Offer**: Average prices by fuel type
- **Avg Spread**: Typical profit margin
- **Total Submissions**: Data volume

**Key Insight**: 
- Batteries typically have widest spreads (high flexibility value)
- CCGT spreads reflect fuel costs + margins
- WIND spreads driven by constraint payments

#### 3. Top 10 Units by Submission Volume (Last 7 Days)
Most active price submitters:
- **BM Unit**: Generator ID
- **Pairs Submitted**: Number of bid-offer pairs
- **Avg Bid/Offer**: Typical prices
- **Total Rows**: Raw data volume

**Key Insight**: High submission frequency = active participation in balancing market.

---

## 🔄 Auto-Refresh

Both sheets update **every 15 minutes** via cron job:
```bash
*/15 * * * * /usr/bin/python3 /Users/georgemajor/GB-Power-Market-JJ/python/dashboard_v3_master_fix.py
```

**Data Freshness**: 
- Tables contain data from **2022-01-01 to 2025-10-28**
- No November/December 2025 data yet (awaiting IRIS real-time pipeline)
- Analysis uses last 30 days (daily trends) and last 7 days (detailed breakdowns)

---

## 📈 Combined Analysis: BOD + BOALF

### The Full Picture
1. **BOD** = What generators **offered** to do
2. **BOALF** = What National Grid **actually accepted**

### Key Analysis Patterns

#### Pattern 1: High BOD Submissions + Low BOALF Actions
**Interpretation**: Oversupply, generators competing for dispatch  
**Market Signal**: Prices likely falling

#### Pattern 2: Low BOD Submissions + High BOALF Actions
**Interpretation**: Supply shortage, frequent emergency dispatch  
**Market Signal**: Prices spiking

#### Pattern 3: Wide Spreads in BOD + Frequent BOALF
**Interpretation**: Market volatility, balancing mechanism heavily utilized  
**Market Signal**: High revenue opportunity for flexible assets

### Example Revenue Calculation
```
Unit: T_BATTERY-1 (100 MW battery)

From BOALF_Analysis:
- 50 increase actions @ avg 200 MW for 1 hour each
- 50 decrease actions @ avg 200 MW for 1 hour each

From BOD_Analysis:
- Avg Offer Price: £80/MWh
- Avg Bid Price: £40/MWh

Revenue Calculation:
- Increase revenue: 50 × 200 MWh × £80 = £800,000
- Decrease revenue: 50 × 200 MWh × £40 = £400,000
- Total monthly revenue: £1,200,000
```

---

## 🛠️ Manual Refresh

To manually update (bypasses 15-min schedule):

```bash
cd /Users/georgemajor/GB-Power-Market-JJ
python3 python/dashboard_v3_master_fix.py
```

Or just BOD/BOALF sheets:

```bash
python3 python/create_bod_boalf_analysis.py
```

---

## 📊 Data Sources

### BigQuery Tables
- **`bmrs_boalf`** - Accepted balancing actions
  - 11,330,547 rows
  - 668 unique BM units
  - Columns: acceptanceNumber, levelFrom, levelTo, settlementDate
  
- **`bmrs_bod`** - Submitted bid-offer data
  - 391,287,533 rows
  - 1,957 unique BM units
  - Columns: pairId, bid, offer, levelFrom, levelTo, settlementDate

### Reference Data
- **`bmu_registration_data`** - Fuel type lookup for BM units

---

## 🚨 Known Limitations

1. **Data Ends 2025-10-28**
   - Historical tables don't have Nov/Dec 2025 data yet
   - Check for `bmrs_boalf_iris` and `bmrs_bod_iris` tables when available

2. **BOALF Missing Prices**
   - BOALF table only contains accepted volumes (MW)
   - Actual acceptance prices would require joining with BOD on acceptanceNumber
   - Future enhancement: Calculate actual revenue by joining BOD + BOALF

3. **Aggregation Trade-offs**
   - Analysis uses averages to handle 391M BOD rows
   - Detailed unit-level analysis available by querying BigQuery directly

---

## 📖 Related Documentation
- `PROJECT_CONFIGURATION.md` - Main project setup
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Table schemas and gotchas
- `ENHANCED_BI_ANALYSIS_README.md` - Advanced analysis methods
- `BATTERY_TRADING_STRATEGY_ANALYSIS.md` - VLP revenue models

---

**Last Updated**: December 4, 2025  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production - Auto-refreshes every 15 minutes
