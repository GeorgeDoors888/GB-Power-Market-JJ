# Complete VLP Analysis - All 4 Parts

**Generated:** 2025-11-09  
**Data Source:** BigQuery analysis.vlp_activity_summary table

---

## PART 1: TOP 20 VLP UNITS BY SPREAD

### Elite VLP Performers (£20K+ Spreads)

| Rank | Unit | Avg Spread | Avg Offer | Avg Bid | Acceptance Rate | Accepted Actions |
|------|------|------------|-----------|---------|-----------------|------------------|
| 1 | 2__FFSEN005 | £53,683/MWh | £26,173/MWh | -£27,510/MWh | **11.8%** | 41,626 |
| 2 | 2__BBPGM001 | £51,021/MWh | £23,955/MWh | -£27,066/MWh | 7.5% | 10,458 |
| 3 | 2__BFSEN005 | £42,612/MWh | £19,219/MWh | -£23,393/MWh | **16.7%** | 31,491 |
| 4 | 2__NFSEN007 | £38,428/MWh | £17,495/MWh | -£20,933/MWh | 8.8% | 24,244 |
| 5 | 2__GFSEN005 | £35,696/MWh | £15,622/MWh | -£20,075/MWh | **23.3%** ⭐ | 10,399 |
| 6 | 2__ECNDL001 | £30,020/MWh | £15,072/MWh | -£14,948/MWh | 3.9% | 4,586 |
| 7 | 2__GFSEN006 | £25,044/MWh | £9,733/MWh | -£15,311/MWh | **28.3%** ⭐⭐ | 23,417 |
| 8 | 2__FFSEN007 | £24,573/MWh | £8,658/MWh | -£15,915/MWh | **26.8%** ⭐ | 43,310 |
| 9 | 2__FBPGM002 | £20,662/MWh | £10,359/MWh | -£10,303/MWh | **44.1%** ⭐⭐⭐ | 56,283 |
| 10 | 2__GSTAT005 | £20,201/MWh | £10,064/MWh | -£10,137/MWh | 5.7% | 15,990 |

### Defensive Bidders (£19K-£20K Spreads - Rarely Accepted)

| Rank | Unit | Spread | Acceptance Rate | Comment |
|------|------|--------|-----------------|---------|
| 11 | 2__ALOND001 | £20,000/MWh | **0.001%** | Defensive only |
| 12 | 2__NANGE003 | £19,998/MWh | **0.001%** | Defensive only |
| 13-16 | 2__BANGE003/1, 2__EANGE002/1 | £19,998/MWh | **0.001%** or null | Defensive only |
| 17 | 2__FANGE001 | £19,564/MWh | 0.04% | Rarely dispatched |
| 18 | 2__GANGE004 | £18,703/MWh | 0.3% | Rarely dispatched |
| 19 | 2__NANGE001 | £17,181/MWh | 0.5% | Rarely dispatched |

### Key Insights - Part 1:

**Unit Naming Pattern:**
- `2__FFSEN` = Flexgen units (demand response/batteries?)
- `2__FBPGM` / `2__BBPGM` = Battery generation modules?
- `2__ANGE` = Defensive bidders (almost never accepted)

**Best Units:**
- **Highest Spread:** 2__FFSEN005 (£53,683/MWh)
- **Highest Acceptance:** 2__FBPGM002 (44.1% - dispatched almost half the time!)
- **Most Dispatches:** 2__FFSEN007 (43,310 accepted actions)
- **Best Combo:** 2__GFSEN005 (23.3% acceptance + £35K spread)

**Patterns:**
- Negative bids indicate **demand response** (paid to reduce load)
- High spreads with low acceptance = defensive bidding strategy
- Units with 20-44% acceptance are actively trading
- "ANGE" units bid at ±£10K but almost never get accepted (placeholder bids)

---

## PART 2: SYSTEM PRICE TRENDS (Daily Aggregates)

### Last 10 Days of Price Data

| Date | Avg SBP | Avg SSP | Avg MIP | Avg NIV | Avg Spread |
|------|---------|---------|---------|---------|------------|
| 2025-10-28 | £49.70 | £49.70 | £10.86 | -£45.04 | £38.85 |
| 2025-10-27 | £56.44 | £56.44 | £27.63 | -£124.00 | £28.81 |
| 2025-10-26 | £28.81 | £28.81 | £13.78 | -£142.69 | £15.03 |
| 2025-10-25 | £24.96 | £24.96 | £11.78 | -£148.37 | £13.18 |
| 2025-10-24 | £36.05 | £36.05 | £19.92 | -£254.08 | £16.13 |
| 2025-10-23 | £73.83 | £73.83 | £36.92 | £17.52 | £36.91 |
| 2025-10-22 | **£101.38** | **£101.38** | £48.24 | -£100.05 | **£53.13** |
| 2025-10-21 | £79.41 | £79.41 | £39.92 | -£1.95 | £39.49 |
| 2025-10-20 | £76.25 | £76.25 | £39.54 | -£96.21 | £36.71 |
| 2025-10-19 | £66.56 | £66.56 | £33.48 | -£60.57 | £33.08 |

### Column Definitions:
- **SBP** = System Buy Price (what National Grid pays)
- **SSP** = System Sell Price (what National Grid charges)
- **MIP** = Market Index Price (reference price)
- **NIV** = Net Imbalance Volume (negative = system short, positive = system long)
- **Spread** = Price volatility/arbitrage potential

### Key Insights - Part 2:

**Recent Market Activity:**
- **Peak Day:** Oct 22 (£101.38 avg, £53.13 spread)
  - System was significantly short (NIV: -100 MW)
  - High price + high spread = major arbitrage opportunity
  
- **Quiet Days:** Oct 25-26 (£25-29 avg prices)
  - System very short (NIV: -142 to -148 MW)
  - But prices stayed low (renewable generation high?)

**Imbalance Patterns:**
- System almost always **SHORT** (negative NIV)
- Exception: Oct 23 had +17.52 MW surplus
- Shortages don't always mean high prices (supply can still meet demand)

**Arbitrage Opportunities:**
- Oct 22: £53 spread - excellent trading day
- Oct 28: £39 spread - good opportunity
- Oct 23: £37 spread - decent day
- Oct 25-26: £13-15 spread - minimal opportunities

---

## PART 3: CORPORATE OWNERSHIP DATA

### Companies House Data Quality

**Problem:** The `companies` table has **NULL company_name** fields
- Row count: 3,476,304 companies
- But names are missing in primary table

**Solution:** Use `company_profiles` table instead
- Has complete company information
- Includes addresses, SIC codes, company types

### Sample Energy Companies Found:

| Company Name | Company Number | Status | Type | Purpose |
|--------------|----------------|--------|------|---------|
| TEIGN ENERGY COMMUNITIES LIMITED | RS007210 | Active | Registered Society | Community energy |
| TEMPUS ENERGY TECHNOLOGY LTD | 09255104 | **Liquidation** | Private Ltd | Tech (closed) |
| TETRO ENERGY LIMITED | SC233931 | Active | Private Ltd | Electricity production |
| TETCOTT ENERGY LIMITED | 09341376 | Active | Private Ltd | Electricity production |
| THE ENERGY GROUP LIMITED | 03613919 | Proposal to Strike off | Holding Company | Parent company |

**Key SIC Codes for Power Generation:**
- **35110** - Production of electricity
- **74901** - Environmental consulting
- **82990** - Business support services

### Challenges Linking VLP Units to Companies:

1. **Unit Naming Convention:** `2__FFSEN005`
   - First digit: Region?
   - Double underscore: Separator
   - FFSEN: Could be company code or location
   - Numbers: Unit identifier

2. **No Direct Mapping:** 
   - Companies House doesn't have "FFSEN" or "BBPGM" in names
   - These might be:
     - Internal BMRS codes
     - Settlement Party IDs
     - Plant/site codes not public company names

3. **Potential Sources:**
   - Elexon BM Unit registry (external)
   - REMIT unavailability data (might have operator names)
   - Cross-reference with `sva_generators` or `cva_plants` tables

### Next Steps for Ownership Analysis:

```sql
-- Check if generator tables have company links
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.sva_generators`
WHERE bmUnit IN ('2__FFSEN005', '2__BBPGM001', '2__FBPGM002')
LIMIT 10;

-- Check REMIT data for operator information
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_iris`
WHERE CONTAINS_SUBSTR(bmUnit, 'FFSEN')
LIMIT 10;
```

---

## PART 4: VLP PROFIT MODEL (10 MW Battery)

### Assumptions:
- **Capacity:** 10 MW
- **Duration:** 30 minutes per dispatch (0.5 hours)
- **Trading Days:** 250 per year
- **Daily Dispatch Attempts:** 2 (adjusted by acceptance rate)
- **Battery Cost:** £5M (£500K per MW)

### Top 5 Units - Profit Analysis

#### Unit 1: 2__FFSEN005
- **Spread:** £53,683/MWh
- **Acceptance:** 11.8%
- **Daily Profit:** £63,346
- **Annual Profit:** £15,836,453
- **Payback:** **0.3 years**
- **ROI:** **317%/year** 🔥

#### Unit 2: 2__BBPGM001
- **Spread:** £51,021/MWh
- **Acceptance:** 7.5%
- **Daily Profit:** £38,266
- **Annual Profit:** £9,566,391
- **Payback:** **0.5 years**
- **ROI:** **191%/year** 🔥

#### Unit 3: 2__BFSEN005
- **Spread:** £42,612/MWh
- **Acceptance:** 16.7%
- **Daily Profit:** £71,162
- **Annual Profit:** £17,790,543
- **Payback:** **0.3 years**
- **ROI:** **356%/year** 🔥🔥🔥

#### Unit 4: 2__NFSEN007
- **Spread:** £38,428/MWh
- **Acceptance:** 8.8%
- **Daily Profit:** £33,817
- **Annual Profit:** £8,454,134
- **Payback:** **0.6 years**
- **ROI:** **169%/year**

#### Unit 5: 2__GFSEN005 ⭐
- **Spread:** £35,696/MWh
- **Acceptance:** 23.3% (HIGHEST!)
- **Daily Profit:** £83,173
- **Annual Profit:** £20,793,165
- **Payback:** **0.2 years** (2.4 months!)
- **ROI:** **416%/year** 🔥🔥🔥

### Market Statistics:
- **Average Spread (Top 5):** £44,288/MWh
- **Median Spread:** £42,612/MWh
- **Std Dev:** £7,819/MWh
- **Average Acceptance:** 13.6%
- **Best Acceptance:** 23.3% (2__GFSEN005)

---

## 🚨 CRITICAL ANALYSIS

### These Numbers Are TOO GOOD To Be True

**Why the profit calculations are unrealistic:**

1. **Massive Spreads:**
   - Average £44K/MWh spreads are **100x normal market prices**
   - These are likely **defensive bids** (units don't want to be dispatched)
   - Real trading spreads: £10-500/MWh, not £50K/MWh

2. **Actual Arbitrage Events:**
   - Jan 8, 2025: £1,353/MWh max (from bmrs_mid analysis)
   - This is **40x smaller** than average VLP spreads
   - Real spreads: £100-1,000/MWh on extreme days

3. **What's Really Happening:**
   - Units bid at ±£27K to avoid dispatch
   - Only accepted during **extreme emergencies**
   - Acceptance rate 11-23% means they got dispatched in crisis situations
   - Real profit: Much lower, based on actual accepted prices not average bids

### Realistic Profit Model:

**Assumptions (Conservative):**
- 10 extreme events per year (like Jan 8)
- Average real spread: £500/MWh (not £50K)
- 4 settlement periods per event (2 hours)
- 10 MW battery

**Calculation:**
```
Annual opportunities: 10 events × 4 periods × 0.5 hr × 10 MW = 200 MWh
Annual profit: 200 MWh × £500/MWh = £100,000
Battery cost: £5,000,000
Payback: 50 years
ROI: 2%/year
```

**Plus normal arbitrage (200 days/year):**
```
Daily trades: 200 days × 2 cycles × 0.5 hr × 10 MW × £50/MWh = £100,000
Total annual profit: £100K + £100K = £200K
ROI: 4%/year
Payback: 25 years
```

### What the VLP Summary ACTUALLY Shows:

1. **Defensive Bidding Strategy:**
   - Units bid at £20K-50K to say "don't dispatch me"
   - Only accepted when National Grid is desperate
   - 11-23% acceptance = worked 88-77% of the time

2. **Emergency Pricing:**
   - When accepted, they got paid their £20K-50K ask
   - This happens during grid emergencies (frequency events, outages)
   - Acceptance rate measures how often emergencies occurred

3. **Market Power:**
   - These units know they're critical for system stability
   - Price very high because they can
   - Accepted actions represent genuine system stress events

---

## 📊 ACTIONABLE VLP STRATEGY

### Based on REAL Data (bmrs_mid + vlp_activity_summary):

#### Strategy 1: Target Extreme Events
- **Historical:** Jan 8, 2025 (£1,353/MWh)
- **Frequency:** ~10 extreme days per year
- **Profit per event:** £5,000-10,000 (10 MW, 2 hours)
- **Annual:** £50,000-100,000 from extremes

#### Strategy 2: Daily Arbitrage
- **Normal spreads:** £20-100/MWh
- **Trading days:** 200 per year
- **Profit per day:** £500-1,000
- **Annual:** £100,000-200,000 from regular trading

#### Strategy 3: Follow the Leaders
- **2__FBPGM002:** 44% acceptance rate
  - Most consistently dispatched
  - Lower spread but high volume
- **2__GFSEN005:** 23% acceptance + decent spread
  - Good balance of frequency and profit
- **2__FFSEN007:** 43,310 accepted actions
  - Most active unit overall

#### Strategy 4: Understand Your Competition
- Top units are demand response (negative bids)
- They're paid to reduce load, not generate
- Different business model than battery storage
- VLP must compete with industrial load shedding

---

## 💡 RECOMMENDATIONS

### For VLP Development:

1. **Use Realistic Profit Expectations:**
   - Target: £200K-500K annual profit for 10 MW
   - Payback: 10-25 years (not 3 months!)
   - ROI: 2-5%/year (not 400%!)

2. **Study Actual Price Spikes:**
   - Query bmrs_mid for real spreads
   - Identify patterns before spikes (low wind, high demand)
   - Build predictive model

3. **Analyze Unit Types:**
   - FFSEN units = demand response?
   - FBPGM/BBPGM = batteries?
   - Learn from their acceptance patterns

4. **Cross-Reference Data:**
   ```sql
   -- Link VLP units to actual dispatch prices
   SELECT 
     v.bmUnit,
     v.avg_spread as defensive_spread,
     b.offer as actual_accepted_price,
     b.timeFrom
   FROM `analysis.vlp_activity_summary` v
   JOIN `uk_energy_prod.bmrs_bod` b
     ON v.bmUnit = b.bmUnit
   WHERE b.offer < 5000  -- Real prices only
   ORDER BY b.timeFrom DESC
   LIMIT 1000;
   ```

5. **Find Company Ownership:**
   - Check sva_generators table for operator names
   - Look up in Companies House company_profiles
   - Analyze financial health via accounts_filings

---

## 🎯 SUMMARY

### What We Discovered:

✅ **200 VLP units** tracked with performance metrics  
✅ **Pre-calculated spreads** and acceptance rates  
✅ **System price trends** showing arbitrage opportunities  
✅ **Companies House data** (3.5M companies, though hard to link to units)  
✅ **Profit model** showing unrealistic 300-400% ROI (due to defensive bidding)

### Reality Check:

⚠️ **VLP spreads £44K/MWh** = Defensive bids (don't dispatch me)  
⚠️ **Real spreads £100-1,000/MWh** = Actual trading opportunities  
⚠️ **Acceptance rate 11-23%** = How often defensive bidding failed  
⚠️ **Realistic ROI 2-5%/year** = True battery economics

### Next Steps:

1. Query bmrs_bod for **actual accepted prices** (filter offer < £5,000)
2. Correlate VLP acceptance events with **system stress** (frequency, imbalance)
3. Build **predictive model** for price spikes
4. Link units to **companies** via sva_generators table
5. Calculate **realistic profit** based on historical price data

**The data is GOLD, but interpretation requires understanding defensive vs. actual bidding!** 🎯
