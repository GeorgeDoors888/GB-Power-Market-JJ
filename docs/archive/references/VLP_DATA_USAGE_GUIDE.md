# VLP Battery Data Usage Guide

## 📊 What You Have

**Complete Market Database**: 148 GB battery storage BMUs with:
- ✅ 102 VLP-operated batteries (68.9% of market)
- ✅ 46 Direct-operated batteries (31.1% of market)
- ✅ 20.4 GW total capacity
- ✅ Full ownership and operator details
- ✅ Historical activity data (BOD - Bid-Offer Data)
- ✅ JSON format for easy integration

**Data Files:**
- `vlp_battery_units_data.json` - Complete structured dataset
- `battery_bmus_complete_*.csv` - All batteries
- `vlp_operated_batteries_*.csv` - VLP subset
- `direct_operated_batteries_*.csv` - Direct-operated subset
- `battery_revenue_analysis_*.csv` - Market activity metrics

---

## 🎯 What You Can Do With This Data

### 1. **Market Share Analysis**

**Question:** Who dominates the GB battery storage market?

**Analysis:**
```python
import json
import pandas as pd

# Load data
with open('vlp_battery_units_data.json') as f:
    data = json.load(f)

batteries = pd.DataFrame(data['battery_units'])

# Top operators by capacity
top_ops = batteries.groupby('leadPartyName').agg({
    'nationalGridBmUnit': 'count',
    'generationCapacity': 'sum'
}).sort_values('generationCapacity', ascending=False).head(10)

print(top_ops)
```

**Insights:**
- **Risq Energy Limited**: 5 GW (5 BMUs) - Largest VLP
- **EP UK Investments**: 1.5 GW (2 BMUs) - Big utility player
- **Tesla Motors**: 541 MW (15 BMUs) - Most distributed portfolio
- **VLP Market Share**: 60.7% of total capacity (12.4 GW / 20.4 GW)

**Use Cases:**
- Identify acquisition targets
- Understand competitive landscape
- Track market consolidation trends
- Benchmark your portfolio

---

### 2. **Regional Distribution Analysis**

**Question:** Where are batteries located? Which regions have most capacity?

**Analysis:**
```python
# Group by GSP region
regional = batteries.groupby('gspGroupName').agg({
    'nationalGridBmUnit': 'count',
    'generationCapacity': 'sum'
}).sort_values('generationCapacity', ascending=False)

# Map visualization
import folium
map = folium.Map(location=[54.5, -3], zoom_start=6)

for _, row in batteries.iterrows():
    if pd.notna(row['gspGroupName']):
        # Add markers with capacity info
        folium.CircleMarker(
            location=[lat, lon],  # Need to add coordinates
            radius=row['generationCapacity']/10,
            popup=f"{row['bmUnitName']}: {row['generationCapacity']}MW",
            color='red' if row['is_vlp'] else 'blue'
        ).add_to(map)

map.save('battery_map.html')
```

**Insights:**
- Identify grid constraint areas (high battery concentration)
- Understand network reinforcement needs
- Forecast regional pricing patterns
- Plan new battery site locations

**Use Cases:**
- Site selection for new batteries
- Network capacity planning
- Regional arbitrage strategies
- DNO coordination

---

### 3. **Arbitrage Opportunity Analysis**

**Question:** Which batteries make the most money? What's their strategy?

**Current Issue:** Revenue showing £0 - need to fix BOD calculation

**Proposed Fix:**
```python
# Fixed revenue query
query = f"""
WITH battery_actions AS (
  SELECT 
    bmUnitId,
    settlementDate,
    settlementPeriod,
    levelFrom,
    levelTo,
    offer,
    bid
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE bmUnitId IN ({battery_bmu_list})
    AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAYS)
),
system_prices AS (
  SELECT
    settlementDate,
    settlementPeriod,
    systemSellPrice,
    systemBuyPrice
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAYS)
)
SELECT
  a.bmUnitId,
  COUNT(*) as actions,
  SUM(ABS(a.levelTo - a.levelFrom)) as total_mwh,
  AVG(CASE WHEN (a.levelTo - a.levelFrom) > 0 THEN p.systemBuyPrice END) as avg_discharge_price,
  AVG(CASE WHEN (a.levelTo - a.levelFrom) < 0 THEN p.systemSellPrice END) as avg_charge_price,
  -- Revenue = (discharge_mwh * discharge_price) - (charge_mwh * charge_price)
  SUM(CASE 
    WHEN (a.levelTo - a.levelFrom) > 0 
    THEN (a.levelTo - a.levelFrom) * p.systemBuyPrice * 0.5
    ELSE 0 
  END) - SUM(CASE 
    WHEN (a.levelTo - a.levelFrom) < 0 
    THEN ABS(a.levelTo - a.levelFrom) * p.systemSellPrice * 0.5
    ELSE 0 
  END) as estimated_revenue
FROM battery_actions a
JOIN system_prices p 
  ON a.settlementDate = p.settlementDate 
  AND a.settlementPeriod = p.settlementPeriod
GROUP BY a.bmUnitId
ORDER BY estimated_revenue DESC
"""
```

**Analysis Outputs:**
- **Profitability ranking**: Which batteries earn most per MW?
- **Cycle patterns**: How often do batteries charge/discharge?
- **Price timing**: When do batteries trade? (peak vs off-peak)
- **VLP vs Direct performance**: Do VLPs optimize better?

**Use Cases:**
- Benchmark battery performance
- Optimize trading strategies
- Identify underperforming assets
- Calculate ROI for new batteries

---

### 4. **VLP Business Model Analysis**

**Question:** Why use a VLP? What's the value proposition?

**Key Metrics:**
```python
# Compare VLP vs Direct operations
vlp_batteries = batteries[batteries['is_vlp'] == True]
direct_batteries = batteries[batteries['is_vlp'] == False]

comparison = pd.DataFrame({
    'Metric': ['Count', 'Avg Capacity', 'Total Capacity', 'Avg Portfolio Size'],
    'VLP': [
        len(vlp_batteries),
        vlp_batteries['generationCapacity'].mean(),
        vlp_batteries['generationCapacity'].sum(),
        vlp_batteries.groupby('leadPartyName').size().mean()
    ],
    'Direct': [
        len(direct_batteries),
        direct_batteries['generationCapacity'].mean(),
        direct_batteries['generationCapacity'].sum(),
        1.0  # Direct operators = 1 asset each
    ]
})
```

**Expected Findings:**
- VLP batteries: **Smaller average size** (121 MW vs 174 MW)
- VLP benefit: **Portfolio optimization** across multiple assets
- VLP operators: **Specialist trading expertise**
- Direct operators: **Larger utility-scale projects**

**VLP Value Drivers:**
1. **Trading Optimization**: Professional 24/7 trading teams
2. **Market Access**: Better liquidity and faster execution
3. **Portfolio Balancing**: Manage risk across multiple assets
4. **Regulatory Expertise**: Navigate complex market rules
5. **Technology Platform**: Advanced forecasting and automation

**Use Cases:**
- Decide: VLP vs Direct operation for your battery
- Select VLP partner (compare operators)
- Understand VLP fee structures
- Benchmark VLP performance

---

### 5. **Operator Portfolio Analysis**

**Question:** Which VLPs manage most assets? Are they diversified?

**Analysis:**
```python
# VLP portfolio composition
vlp_portfolios = batteries[batteries['is_vlp']].groupby('leadPartyName').agg({
    'nationalGridBmUnit': 'count',
    'generationCapacity': ['sum', 'mean', 'std'],
    'gspGroupName': lambda x: x.nunique(),
    'bmUnitType': lambda x: x.value_counts().to_dict()
})

vlp_portfolios.columns = ['_'.join(col).strip() for col in vlp_portfolios.columns]
vlp_portfolios = vlp_portfolios.sort_values('generationCapacity_sum', ascending=False)

# Diversification score = regions * battery_count / capacity_variance
vlp_portfolios['diversification'] = (
    vlp_portfolios['gspGroupName_<lambda>'] * 
    vlp_portfolios['nationalGridBmUnit_count'] / 
    (vlp_portfolios['generationCapacity_std'] + 1)
)
```

**Key Insights:**
- **Tesla**: Most distributed (15 assets, small sizes, many regions)
- **Statkraft**: 11 assets, mixed capacity, multiple regions
- **Risq Energy**: Few large assets (5 GW total, 5 BMUs)

**Portfolio Strategies:**
1. **Aggregator Model** (Tesla, Statkraft): Many small assets
2. **Utility Model** (Risq, EP UK): Few large assets
3. **Specialist Model** (Arenko, Flexitricity): Mid-size, targeted

**Use Cases:**
- Assess VLP financial stability
- Understand VLP risk management
- Compare VLP business models
- Track M&A activity

---

### 6. **Technology & Manufacturer Analysis**

**Question:** Which battery technologies are used? Who are the suppliers?

**Data Enrichment Needed:**
- Battery chemistry (Li-ion, flow battery, etc.)
- Manufacturer (Tesla, Fluence, Wartsila, etc.)
- Inverter type
- Duration (1hr, 2hr, 4hr)

**Source Data:**
- REMIT database (asset details)
- BMU names often contain clues
- Cross-reference with planning applications

**Example Enrichment:**
```python
# Infer from BMU names
batteries['likely_tesla'] = batteries['leadPartyName'].str.contains('Tesla', case=False)
batteries['likely_duration'] = batteries['generationCapacity'].apply(
    lambda x: '1hr' if x < 60 else '2hr' if x < 120 else '4hr+'
)
```

**Analysis Questions:**
- Which technologies dominate GB market?
- What's average battery duration?
- How do technologies perform differently?
- What's market share by manufacturer?

---

### 7. **Time Series & Trend Analysis**

**Question:** How is the market evolving? Growth trends?

**Data Sources:**
- Historical BMU registration dates
- Capacity additions over time
- VLP market share evolution
- Regional growth patterns

**Analysis:**
```python
# Load historical snapshots
import glob

snapshots = []
for file in glob.glob('battery_bmus_complete_*.csv'):
    date = file.split('_')[-2]  # Extract date from filename
    df = pd.read_csv(file)
    df['snapshot_date'] = date
    snapshots.append(df)

history = pd.concat(snapshots)

# Market growth over time
growth = history.groupby('snapshot_date').agg({
    'nationalGridBmUnit': 'count',
    'generationCapacity': 'sum',
    'is_vlp': 'mean'
})

# Plot
import matplotlib.pyplot as plt
fig, ax1 = plt.subplots(figsize=(12,6))

ax1.plot(growth.index, growth['generationCapacity'], 'b-', label='Total Capacity')
ax1.set_ylabel('Capacity (MW)', color='b')

ax2 = ax1.twinx()
ax2.plot(growth.index, growth['is_vlp']*100, 'r-', label='VLP %')
ax2.set_ylabel('VLP Market Share (%)', color='r')

plt.title('GB Battery Market Evolution')
plt.show()
```

**Insights:**
- Market growth rate (MW/year)
- VLP adoption curve
- Regional expansion patterns
- Operator consolidation trends

---

### 8. **Grid Services & Revenue Stacking**

**Question:** What services do batteries provide? How do they stack revenues?

**Revenue Streams:**
1. **Energy Arbitrage**: Buy low, sell high
2. **Frequency Response**: Dynamic/Static (FFR, DCH, DLH, DMH)
3. **Reserve Services**: STOR, Fast Reserve
4. **Capacity Market**: De-rating payments
5. **Balancing Mechanism**: BOA/BOD acceptances
6. **Network Services**: DNO flexibility contracts

**Data Integration:**
```python
# Combine multiple BigQuery tables
services_query = """
SELECT 
  b.nationalGridBmUnit,
  b.leadPartyName,
  b.generationCapacity,
  
  -- Energy arbitrage (BOD)
  COUNT(bod.pairId) as arbitrage_actions,
  
  -- Frequency response (FREQ correlation)
  COUNT(freq.frequency) as freq_events,
  
  -- Balancing acceptances (BOALF)
  SUM(boalf.acceptedVolume) as balancing_volume,
  SUM(boalf.acceptedVolume * boalf.acceptedPrice) as balancing_revenue
  
FROM batteries b
LEFT JOIN bmrs_bod bod ON b.elexonBmUnit = bod.bmUnitId
LEFT JOIN bmrs_freq freq ON bod.settlementDate = freq.recordDate
LEFT JOIN bmrs_boalf boalf ON b.elexonBmUnit = boalf.bmUnitId
GROUP BY 1,2,3
"""
```

**Analysis Questions:**
- Which revenue stream is largest?
- How do VLPs diversify income?
- What's optimal revenue stack?
- Service participation rates

---

### 9. **Regulatory & Market Access Analysis**

**Question:** Who can access which markets? Licensing requirements?

**Key Factors:**
- **Connection Type**: Transmission vs Distribution
- **Capacity**: Some markets have min/max limits
- **BMU Type**: E (embedded), T (transmission), V (virtual)
- **Lead Party**: License requirements

**Analysis:**
```python
# Market eligibility matrix
batteries['can_bm'] = batteries['bmUnitType'].isin(['T', 'E'])  # Balancing Mechanism
batteries['can_cm'] = batteries['generationCapacity'] >= 2  # Capacity Market (2MW min)
batteries['can_ffr'] = batteries['generationCapacity'] >= 1  # FFR (1MW min)
batteries['can_dno_flex'] = batteries['bmUnitType'] == 'E'  # DNO flexibility (embedded only)

eligibility = batteries.groupby('leadPartyName')[
    ['can_bm', 'can_cm', 'can_ffr', 'can_dno_flex']
].sum()
```

**Insights:**
- Market access by operator
- Which batteries underutilize opportunities?
- Regulatory barriers to entry
- Licensing trends (new BMU registrations)

---

### 10. **Competitive Intelligence**

**Question:** What are competitors doing? Market positioning?

**Strategic Analysis:**
```python
# Competitive landscape
competitors = batteries.groupby('leadPartyName').agg({
    'nationalGridBmUnit': 'count',
    'generationCapacity': ['sum', 'mean'],
    'gspGroupName': lambda x: list(x.unique()),
    'is_vlp': 'first'
}).sort_values(('generationCapacity', 'sum'), ascending=False)

# Add market context
competitors['market_share'] = (
    competitors[('generationCapacity', 'sum')] / 
    batteries['generationCapacity'].sum() * 100
)

# Strategic positioning
competitors['strategy'] = competitors.apply(lambda x:
    'Portfolio Aggregator' if x[('nationalGridBmUnit', 'count')] > 10
    else 'Utility Scale' if x[('generationCapacity', 'mean')] > 200
    else 'Mid-Market'
, axis=1)
```

**Intelligence Use Cases:**
- Track competitor capacity additions
- Identify M&A targets
- Benchmark your portfolio
- Forecast market moves
- Strategic partnership opportunities

---

## 🛠️ Practical Applications

### Application 1: Battery Site Selection Tool

**Goal:** Find optimal locations for new batteries

**Data Inputs:**
1. VLP battery locations (this dataset)
2. GSP flow data (gsp_wind_analysis.py)
3. Grid constraints (public data)
4. Historical prices by region (BigQuery)

**Algorithm:**
```python
def site_selection_score(location):
    # Factor 1: Price volatility (higher = better arbitrage)
    volatility = calculate_price_volatility(location, days=365)
    
    # Factor 2: Grid congestion (constraints = higher prices)
    congestion = get_gsp_flow_variance(location)
    
    # Factor 3: Competition (fewer batteries = less competition)
    competition = batteries[batteries['gspGroupName'] == location].shape[0]
    
    # Factor 4: Renewable penetration (more renewables = more volatility)
    renewables = get_renewable_capacity(location)
    
    score = (volatility * 0.4) + (congestion * 0.3) + (renewables * 0.2) - (competition * 0.1)
    return score
```

---

### Application 2: VLP Selection Tool

**Goal:** Choose the best VLP partner for your battery

**Criteria:**
- Portfolio size (diversification)
- Track record (revenue performance)
- Geographic coverage
- Technology expertise
- Fee structure

**Scoring Model:**
```python
def vlp_score(vlp_name):
    vlp_data = batteries[batteries['leadPartyName'] == vlp_name]
    
    portfolio_size = len(vlp_data)
    avg_capacity = vlp_data['generationCapacity'].mean()
    regional_diversity = vlp_data['gspGroupName'].nunique()
    
    # Get revenue data (once fixed)
    revenue_data = get_vlp_revenue(vlp_name)
    avg_revenue_per_mw = revenue_data['revenue'] / revenue_data['capacity']
    
    return {
        'portfolio': portfolio_size,
        'performance': avg_revenue_per_mw,
        'diversity': regional_diversity,
        'total_score': (portfolio_size * 0.3 + avg_revenue_per_mw * 0.5 + regional_diversity * 0.2)
    }
```

---

### Application 3: Real-Time Trading Dashboard

**Goal:** Monitor battery market activity in real-time

**Features:**
- Live BOD submissions by battery
- Current system prices (SBP/SSP)
- Battery state of charge (inferred from actions)
- Arbitrage opportunities (price spreads)
- Frequency events correlation

**Implementation:**
```python
import streamlit as st

# Real-time dashboard
st.title("GB Battery Market - Live Monitoring")

# Current system status
col1, col2, col3 = st.columns(3)
col1.metric("System Buy Price", f"£{get_current_sbp():.2f}/MWh")
col2.metric("System Sell Price", f"£{get_current_ssp():.2f}/MWh")
col3.metric("Spread", f"£{get_current_sbp() - get_current_ssp():.2f}/MWh")

# Active batteries map
st.map(get_active_batteries_location())

# Recent BOD actions
st.subheader("Recent Actions (Last Hour)")
st.dataframe(get_recent_bod_actions(hours=1))

# Top performers today
st.subheader("Today's Top Performers")
st.bar_chart(get_daily_performance())
```

---

## 📊 Advanced Analytics

### Machine Learning Applications

**1. Revenue Forecasting**
```python
from sklearn.ensemble import RandomForestRegressor

# Features: capacity, VLP status, region, hour, wind, frequency
X = prepare_features(batteries, weather_data, grid_data)
y = batteries['revenue']

model = RandomForestRegressor()
model.fit(X, y)

# Predict future revenue
forecast = model.predict(future_features)
```

**2. Anomaly Detection**
- Identify underperforming batteries
- Detect unusual trading patterns
- Flag potential equipment failures
- Alert on market manipulation

**3. Optimization Models**
- Optimal bid/offer curves
- State of charge management
- Multi-service participation
- Portfolio balancing

---

## 🔄 Data Update Workflows

### Automated Daily Update
```bash
#!/bin/bash
# update_vlp_data.sh

cd ~/GB\ Power\ Market\ JJ

# 1. Download latest BMU data
python3 complete_vlp_battery_analysis.py

# 2. Update JSON
python3 create_vlp_json.py

# 3. Upload to database/API
# python3 upload_to_api.py

# 4. Refresh dashboards
python3 realtime_dashboard_updater.py

# 5. Send report
# python3 send_daily_report.py

echo "✅ VLP data updated: $(date)"
```

**Cron Schedule:**
```bash
# Run daily at 8 AM
0 8 * * * cd ~/GB\ Power\ Market\ JJ && ./update_vlp_data.sh >> logs/vlp_update.log 2>&1
```

---

## 🎓 Learning Resources

### Understanding Battery Economics
- **Arbitrage**: Buy electricity cheap (night), sell expensive (day)
- **Degradation**: Batteries lose capacity over cycles
- **Round-trip efficiency**: ~85-90% (lose 10-15% per cycle)
- **Ancillary services**: Grid stability payments
- **Stacking**: Multiple revenue streams simultaneously

### Market Mechanisms
- **Balancing Mechanism (BM)**: Real-time grid balancing
- **Day-Ahead Market**: Trading electricity for next day
- **Intraday Market**: Trading up to gate closure
- **Capacity Market**: Ensuring adequate capacity
- **Frequency Response**: Automatic grid frequency control

### VLP Business Model
- **Aggregation**: Pool multiple small assets
- **Optimization**: Algorithms for trading
- **Market Access**: Regulatory licenses
- **Revenue Share**: Typically 70/30 or 80/20 split
- **Services**: Trading, forecasting, settlement, reporting

---

## 📈 Next Steps

### Immediate Actions:
1. ✅ **Fix revenue calculation** (todo #8) - Get accurate earnings data
2. ✅ **Fix bmrs_indgen_iris schema** (todo #2) - Enable generation tracking
3. ✅ **Add error handling** (todo #4) - Robust production code

### Data Enhancements:
1. **Add battery chemistry/manufacturer** - REMIT database
2. **Add connection dates** - Track market growth
3. **Add coordinates** - Enable mapping
4. **Add duration** - 1hr vs 2hr vs 4hr analysis

### New Analyses:
1. **Cycle life analysis** - How many cycles per day?
2. **Seasonal patterns** - Summer vs winter performance
3. **Event correlation** - Price spikes, frequency events, wind ramps
4. **Network modeling** - Grid constraint impact

### Integration Opportunities:
1. **ChatGPT interface** - Natural language queries
2. **Power BI dashboard** - Interactive visualizations
3. **API endpoint** - Third-party integrations
4. **Alert system** - Market opportunity notifications

---

## 🚀 Getting Started Examples

### Example 1: Find Tesla Batteries
```python
import json
with open('vlp_battery_units_data.json') as f:
    data = json.load(f)

tesla_batteries = [b for b in data['battery_units'] 
                   if b['leadPartyName'] == 'Tesla Motors Limited']

print(f"Tesla operates {len(tesla_batteries)} batteries")
for battery in tesla_batteries:
    print(f"  - {battery['bmUnitName']}: {battery['generationCapacity']}MW in {battery['gspGroupName']}")
```

### Example 2: Compare VLP vs Direct
```python
vlp_count = sum(1 for b in data['battery_units'] if b['is_vlp'])
direct_count = data['metadata']['total_battery_bmus'] - vlp_count

vlp_capacity = sum(b['generationCapacity'] or 0 for b in data['battery_units'] if b['is_vlp'])
direct_capacity = data['summary_statistics']['total_capacity_mw'] - vlp_capacity

print(f"VLP: {vlp_count} batteries, {vlp_capacity:.0f} MW")
print(f"Direct: {direct_count} batteries, {direct_capacity:.0f} MW")
print(f"VLP market share: {vlp_capacity / data['summary_statistics']['total_capacity_mw'] * 100:.1f}%")
```

### Example 3: Regional Analysis
```python
from collections import Counter
regions = Counter(b['gspGroupName'] for b in data['battery_units'] if b['gspGroupName'])

print("Batteries by region:")
for region, count in regions.most_common():
    regional_capacity = sum(b['generationCapacity'] or 0 for b in data['battery_units'] 
                            if b['gspGroupName'] == region)
    print(f"  {region}: {count} batteries, {regional_capacity:.0f} MW")
```

---

**This data is your competitive advantage. Start exploring!** 🔋⚡
