# BM KPI Implementation Plan
**Based on**: bm_kpi_definitions.md  
**Current Status**: 4 basic sparklines implemented (Total £, Net MWh, EWAP, Top BMU)  
**Remaining Work**: Full KPI system with BOALF + BOD data + benchmarking

---

## ✅ COMPLETED (Dec 14, 2025)

### Phase 1: Basic Settlement Period Sparklines
- ✅ KPI_BMU_001: Net BM Revenue (£) by SP - implemented as "Total £" sparkline
- ✅ KPI_BMU_003: Net MWh by SP - implemented as "Net MWh" sparkline  
- ✅ KPI_BMU_004: £/MWh (EWAP) by SP - implemented as "EWAP" sparkline
- ✅ KPI_MKT_006: Top BMU revenue by SP - implemented as "Top BMU £" sparkline

**Data Sources Used**: BOAV + EBOCF (settlement-level)  
**Implementation**: `update_battery_bm_revenue.py` (lines 1-280)  
**Dashboard Location**: S30-T34, Data_Hidden rows 21-24

---

## 🔄 PHASE 2: BOALF Integration (Acceptance-Level Data)

### New Data Sources Required
1. **BOALF API**: `https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptance/all`
   - Returns: acceptanceNumber, acceptanceTime, timeFrom, timeTo, levelFrom, levelTo
   - Purpose: Dispatch intensity, acceptance counts, granularity, timing

### KPIs to Add

**KPI_MKT_005 — Dispatch Intensity (acceptances/hour)**
- Formula: `count(BOALF.acceptanceNumber) / hoursElapsed`
- Display: Single cell in market header
- Update: Real-time (TodaySoFar from 00:00)

**KPI_BMU_006 — Acceptance Count**
- Formula: `count(BOALF rows for BMU)`
- Display: New column in battery table (K-R range)
- Update: Per battery, daily rollup

**KPI_BMU_007 — Granularity (MWh per acceptance)**
- Formula: `(offerMWh + bidMWh) / acceptanceCount`
- Display: New column in battery table
- Update: Derived from BOAV + BOALF

**KPI_BMU_008 — Time-of-day profile (% MWh in bands)**
- Formula: `sum(MWh where SP in band) / sum(MWh)`
- Display: New sparklines (3 bands: 00-06, 06-18, 18-24)
- Update: Percentage distribution by time window

### Implementation Plan
```python
# New function in update_battery_bm_revenue.py
def fetch_boalf_data(date, bmu_id):
    """
    Fetch BOALF acceptance-level data for timing and count metrics
    Returns: list of acceptances with times, MW deltas
    """
    url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptance/all/{date}"
    params = {'bmUnit': bmu_id}
    # Process acceptances, count by SP, extract timing
    
# Add to battery data collection:
acceptance_count = len(boalf_data)
granularity = total_mwh / acceptance_count if acceptance_count > 0 else 0
```

**Estimated API Load**: 3 batteries × 1 call = 3 additional requests (vs current 576)  
**Runtime Impact**: +2-3 seconds

---

## 🔄 PHASE 3: BOD Integration (Bid-Offer Stack Data)

### New Data Sources Required
1. **BOD API**: `https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer/all`
   - Returns: pairId, bidPrice, offerPrice, levelFrom, levelTo
   - Purpose: Stack depth, defensive pricing, spreads, available MW

### KPIs to Add

**KPI_STACK_001 — Stack Depth (pairs per SP)**
- Formula: `countDistinct(BOD.pairId) per SP`
- Display: New sparkline (48-period trend)
- Update: Shows market "granularity" over the day

**KPI_STACK_002 — Defensive Pricing Share (%)**
- Formula: `count(pairs where abs(bid)≥9999 or abs(offer)≥9999) / total pairs`
- Display: Single cell percentage + sparkline
- Update: Market-level and per-BMU

**KPI_STACK_003 — Offered Flex MW**
- Formula: `sum(|levelTo - levelFrom|) by direction`
- Display: Bid MW available, Offer MW available
- Update: Total MW "on the table" from stack

**KPI_STACK_004 — Indicative Spread (£/MWh)**
- Formula: `median(offer - bid) across non-defensive pairs`
- Display: Single cell + sparkline (spread over day)
- Update: Market pricing aggressiveness

### Implementation Plan
```python
# New function
def fetch_bod_data(date, bmu_id):
    """
    Fetch BOD stack data for pricing and availability metrics
    Returns: pairs with prices, MW bands, defensive flags
    """
    url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer/all/{date}"
    params = {'bmUnit': bmu_id, 'settlementPeriod': sp}
    # Process pairs, identify defensive pricing, calc spreads
    
# Market-level aggregation:
stack_depth_by_sp = [count_pairs(sp) for sp in range(1, 49)]
defensive_share = defensive_pairs / total_pairs
median_spread = median([offer - bid for (offer, bid) in non_defensive_pairs])
```

**Estimated API Load**: 48 SPs × 1 call = 48 requests (market-level) or 3 × 48 = 144 (per-BMU)  
**Runtime Impact**: +15-20 seconds (significant)

---

## 🔄 PHASE 4: Market-Wide KPIs (All BMUs)

### KPIs to Add

**KPI_MKT_001 — Total BM Cashflow (£) TodaySoFar**
- Formula: `sum(EBOCF_bid + EBOCF_offer) across all BMUs`
- Display: Header KPI cell
- Update: Requires fetching EBOCF for all BMUs (not just batteries)

**KPI_MKT_002 — Total Accepted Volume (MWh) TodaySoFar**
- Formula: `sum(BOAV_bid + BOAV_offer) across all BMUs`
- Display: Header KPI cell
- Update: Market-wide query

**KPI_MKT_003 — System Direction (Net MWh)**
- Formula: `netMWh = offerMWh - bidMWh` (all BMUs)
- Display: Header KPI cell with direction indicator
- Update: Shows if system is "long" (negative) or "short" (positive)

**KPI_MKT_007 — Workhorse Index (Active SPs/48)**
- Formula: `activeSPs = countDistinct(SP where BOAV_MWh > 0); index = activeSPs/48`
- Display: Market-level percentage
- Update: How "busy" the BM is

### Implementation Challenge
- Market-wide queries need **all BMUs**, not just 3 batteries
- Options:
  1. Query without bmUnit filter (returns all BMUs, heavier response)
  2. Query top 20-50 BMUs only (partial but fast)
  3. Use pre-aggregated data if available

**Estimated API Load**: 48 SPs × 2 endpoints = 96 requests (if no bmUnit filter works)  
**Runtime Impact**: +30-40 seconds OR needs caching/background job

---

## 🔄 PHASE 5: Benchmarking System (Historical Context)

### Data Storage Required
- **BigQuery table**: `bm_kpi_daily_benchmarks`
- Columns: date, kpi_id, bmu_id, value, time_of_day_cutoff
- Purpose: Store last 365 days of KPI values for comparison

### Benchmark Calculations

For each KPI:
- **Mean**: Average over 365 days
- **Min/Max**: Range boundaries
- **p10/p50/p90**: Percentile distribution
- **StdDev**: Variance measure
- **Z-Score**: `(today - mean) / stddev`
- **Rank Percentile**: Where today sits vs history

### Implementation Plan
```python
# Daily benchmark update job (separate script)
def update_bm_kpi_benchmarks():
    """
    Run once per day (e.g., 02:00) to store yesterday's KPIs
    Compute rolling 365-day stats for each KPI
    """
    for kpi_id in ALL_KPI_IDS:
        for bmu_id in TRACKED_BMUS:
            value = calculate_kpi(kpi_id, bmu_id, yesterday)
            store_to_bigquery(kpi_id, bmu_id, value)
            
            # Compute benchmarks
            historical_values = fetch_last_365_days(kpi_id, bmu_id)
            benchmarks = {
                'mean': mean(historical_values),
                'p10': percentile(historical_values, 10),
                'p50': percentile(historical_values, 50),
                'p90': percentile(historical_values, 90),
                'stddev': stddev(historical_values)
            }
            update_benchmark_table(kpi_id, bmu_id, benchmarks)

# Dashboard display
def get_kpi_with_context(kpi_id, bmu_id, today_value):
    """
    Fetch benchmark and compute context
    Returns: value, mean, z_score, percentile, trend_indicator
    """
    benchmarks = fetch_benchmarks(kpi_id, bmu_id)
    z_score = (today_value - benchmarks['mean']) / benchmarks['stddev']
    percentile = calculate_percentile_rank(today_value, benchmarks)
    
    return {
        'value': today_value,
        'vs_mean': f"+{((today_value/benchmarks['mean'])-1)*100:.1f}%",
        'z_score': z_score,
        'percentile': percentile,
        'indicator': '🔥' if z_score > 2 else '✅' if z_score > 0 else '⚪'
    }
```

**Storage Requirements**: ~50 KPIs × 10 BMUs × 365 days × 5 stats = ~90k rows/year  
**Query Performance**: Indexed by (kpi_id, bmu_id, date) - fast lookups

---

## 🔄 PHASE 6: Enhanced Dashboard Layout

### New Dashboard Sections

**Market Header (New Row Above Current)**
```
Row 22 (NEW):
  A22: 💰 Total BM £     | B22: [KPI_MKT_001 value] | C22: [vs 30d avg]
  D22: ⚡ Total MWh      | E22: [KPI_MKT_002 value] | F22: [vs 30d avg]
  G22: 📊 Dispatch/hr    | H22: [KPI_MKT_005 value] | I22: [vs 30d avg]
  J22: 🏆 Top-1 Share    | K22: [KPI_MKT_006 value] | L22: [vs 30d avg]
```

**Battery Table Enhancements (K24-R29 → K24-U29)**
```
Current columns: BMU ID, Name, Net £, Volume MWh, £/MWh, Type, Active SPs, Status
New columns to add:
  S: Acceptance Count (KPI_BMU_006)
  T: MWh/Acceptance (KPI_BMU_007)
  U: Z-Score (benchmark context)
```

**Stack Analysis Panel (New Section V30-Z40)**
```
V30: 📚 BM STACK ANALYSIS
V31: Stack Depth (pairs)    | W31: [sparkline A-AV]    | X31: [current avg]
V32: Defensive Share (%)    | W32: [sparkline]         | X32: [current %]
V33: Offer MW Available     | W33: [sparkline]         | X33: [current MW]
V34: Bid MW Available       | W34: [sparkline]         | X34: [current MW]
V35: Median Spread (£/MWh)  | W35: [sparkline]         | X35: [current spread]
```

**Time-of-Day Profile (New Sparklines Below Battery Section)**
```
S35: 🕐 Revenue by Time Band
S36: Night (00-06):     | T36: [% sparkline showing 6 SPs]
S37: Day (06-18):       | T37: [% sparkline showing 24 SPs]
S38: Evening (18-24):   | T38: [% sparkline showing 12 SPs]
```

---

## 📋 IMPLEMENTATION ROADMAP

### Priority 1: BOALF Integration (Week 1)
- [ ] Create `fetch_boalf_data()` function
- [ ] Add acceptance count to battery table
- [ ] Add granularity (MWh/acceptance) metric
- [ ] Calculate dispatch intensity (market-level)
- [ ] Test with 1-day historical data
- **Deliverable**: Enhanced battery table with 2 new columns

### Priority 2: Time-of-Day Profiles (Week 1)
- [ ] Split SP-level data into 3 time bands
- [ ] Calculate % distribution by band
- [ ] Create 3 new sparklines for time profile
- [ ] Add to dashboard at S35-T38
- **Deliverable**: Time-of-day revenue visibility

### Priority 3: BOD Stack Analysis (Week 2)
- [ ] Create `fetch_bod_data()` function
- [ ] Calculate stack depth by SP
- [ ] Identify defensive pricing (threshold: ±9,999)
- [ ] Calculate median spread (non-defensive pairs)
- [ ] Create stack analysis panel (V30-Z40)
- **Deliverable**: Market pricing transparency

### Priority 4: Market-Wide KPIs (Week 2)
- [ ] Fetch BOAV/EBOCF for all BMUs (or top 50)
- [ ] Calculate market totals (£, MWh, direction)
- [ ] Add market header row (row 22)
- [ ] Calculate top-1/top-5 concentration
- **Deliverable**: Full market context

### Priority 5: Benchmarking System (Week 3)
- [ ] Create BigQuery table `bm_kpi_daily_benchmarks`
- [ ] Build daily benchmark update script
- [ ] Calculate 365-day stats (mean, p10/p50/p90, stddev)
- [ ] Add z-score column to battery table
- [ ] Add context indicators (🔥/✅/⚪)
- **Deliverable**: Historical context for every metric

### Priority 6: Documentation & Optimization (Week 3)
- [ ] Update LIVE_DASHBOARD_V2_DOCUMENTATION.md with all KPIs
- [ ] Add cell notes to dashboard (copy from bm_kpi_definitions.md)
- [ ] Implement caching for expensive queries
- [ ] Add error handling for API failures
- [ ] Create monitoring dashboard for API usage
- **Deliverable**: Production-ready system

---

## 🚨 TECHNICAL CHALLENGES

### 1. API Rate Limits
- **Current**: 576 requests (BOAV + EBOCF for 3 batteries)
- **Phase 2**: +3 requests (BOALF)
- **Phase 3**: +144 requests (BOD for 3 batteries × 48 SPs)
- **Phase 4**: +96 requests (market-wide BOAV/EBOCF)
- **Total**: ~820 requests per update
- **Mitigation**: Caching, background jobs, request throttling

### 2. Runtime Performance
- **Current**: ~20 seconds
- **Full implementation**: ~90-120 seconds (unacceptable for 5-min updates)
- **Solutions**:
  - Cache BOD data (updates less frequently than settlement)
  - Run market-wide KPIs every 15 min instead of 5 min
  - Use async/parallel requests
  - Pre-compute benchmarks (daily job, not real-time)

### 3. Data Freshness
- BOAV/EBOCF are "latest settlement run" - values can change
- BOD is submitted stack - may update throughout the day
- BOALF is operational - real-time but noisy
- **Solution**: Display data timestamp + "provisional" indicator

### 4. BigQuery Costs
- Benchmarking requires daily writes (50 KPIs × 10 BMUs = 500 rows/day)
- Historical queries for 365 days per KPI
- **Mitigation**: Efficient schema, indexed queries, aggregate tables

---

## 💡 RECOMMENDATIONS

### Immediate Actions (This Week)
1. ✅ **Keep current 4 sparklines** - they're working and valuable
2. 🔄 **Add BOALF integration** - low cost (3 API calls), high value (dispatch intensity)
3. 🔄 **Add time-of-day profiles** - no new APIs needed, uses existing BOAV data

### Medium-Term (Next 2 Weeks)
4. 🔄 **Add BOD stack analysis** - higher cost but critical for pricing insights
5. 🔄 **Add market-wide KPIs** - context for battery performance

### Long-Term (Month 1-2)
6. 🔄 **Build benchmarking system** - enables year-over-year comparisons
7. 🔄 **Optimize performance** - caching, async, background jobs

### User Experience Priorities
- Keep dashboard fast (<30 sec updates)
- Add cell notes explaining each KPI (copy from bm_kpi_definitions.md)
- Use conditional formatting (🔥 for outliers, ✅ for normal, ⚪ for low)
- Add "Last Updated" timestamp for each data source

---

## 📊 SUCCESS METRICS

1. **Data Coverage**: 100% of specified KPIs implemented
2. **Performance**: Dashboard updates in <60 seconds (target <30)
3. **Accuracy**: API data matches NESO published reports
4. **Usability**: Cell notes explain every metric
5. **Context**: Every KPI has benchmark comparison (vs 30d/365d)

---

**Status**: Phase 1 complete (4 sparklines), Phases 2-6 planned  
**Next Step**: Implement BOALF integration (Priority 1)  
**Decision Required**: Approve runtime trade-offs for full implementation
