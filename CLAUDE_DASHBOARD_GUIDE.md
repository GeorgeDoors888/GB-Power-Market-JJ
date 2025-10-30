# Claude Project Guide: UK Energy Market Dashboard

## 🎯 Project Overview

**Goal:** Create a comprehensive UK energy market dashboard with real-time data visualization, forecasting, and analysis capabilities.

**Data Source:** Complete UK energy market data (2022-2025) loaded into BigQuery
- Project: `inner-cinema-476211-u9`
- Dataset: `uk_energy_prod` (US region)
- 65+ datasets from BMRS (Balancing Mechanism Reporting Service)

---

## 📊 Available Data (Ready to Query!)

### Key Datasets

#### 1. **FUELINST** - Fuel Generation (Instant)
**What:** Current generation by fuel type every 5 minutes
**Key Fields:** `fuelType`, `generation`, `settlementDate`, `settlementPeriod`
**Coverage:** 2022-2025 (Jan-Oct)
**Use Cases:**
- Real-time fuel mix visualization
- Generation trends by fuel type
- Renewable vs fossil analysis
- Peak demand analysis

**Example Query:**
```sql
SELECT 
    fuelType,
    SUM(generation) as total_generation,
    AVG(generation) as avg_generation
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate = '2025-07-16' 
  AND settlementPeriod = 12
GROUP BY fuelType
ORDER BY total_generation DESC
```

#### 2. **BOD** - Bid-Offer Data
**What:** All bids and offers from generation units
**Key Fields:** `bmUnit`, `offer`, `bid`, `levelFrom`, `levelTo`, `timeFrom`, `timeTo`
**Volume:** ~110M rows per year
**Coverage:** 2022-2025
**Use Cases:**
- Price discovery analysis
- Market participant behavior
- Bid-offer spread analysis
- Unit-level profitability

#### 3. **FREQ** - System Frequency
**What:** Grid frequency measurements
**Key Fields:** `frequency`, `settlementDate`, `settlementPeriod`
**Coverage:** 2022-2025
**Use Cases:**
- Grid stability monitoring
- Frequency response analysis
- Correlation with generation changes

#### 4. **COSTS** - System Costs
**What:** System buy/sell prices
**Key Fields:** `systemBuyPrice`, `systemSellPrice`
**Coverage:** 2022-2025
**Use Cases:**
- Imbalance cost tracking
- System price trends
- Arbitrage opportunities

#### 5. **Interconnector Data** (INTFR, INTIRL, INTNED, etc.)
**What:** Import/export flows with neighboring countries
**Coverage:** 2022-2025
**Use Cases:**
- Cross-border flow analysis
- Import dependency tracking
- Price correlation analysis

#### 6. **Wind & Solar** (WIND, WINDFOR, SOLAR)
**What:** Wind and solar generation and forecasts
**Coverage:** 2022-2025
**Use Cases:**
- Renewable generation tracking
- Forecast accuracy analysis
- Weather impact studies

---

## 🚀 Next Phase: Dashboard Development

### Phase 1: Data Exploration & Queries (1-2 days)

#### Tasks:
1. **Explore the data structure**
   - Query each major dataset
   - Understand data granularity and update frequency
   - Identify data quality issues
   - Document relationships between datasets

2. **Create sample queries**
   - Daily generation by fuel type
   - System frequency statistics
   - Price trends over time
   - Interconnector flows
   - Wind/solar capacity factors

3. **Build aggregation views**
   - Daily summaries
   - Weekly summaries
   - Monthly summaries
   - Performance metrics

#### Example Queries to Start With:

**Daily Fuel Mix:**
```sql
SELECT 
    settlementDate,
    fuelType,
    SUM(generation) as daily_generation
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate BETWEEN '2025-01-01' AND '2025-10-28'
GROUP BY settlementDate, fuelType
ORDER BY settlementDate, fuelType
```

**System Frequency Stats:**
```sql
SELECT 
    settlementDate,
    AVG(frequency) as avg_frequency,
    MIN(frequency) as min_frequency,
    MAX(frequency) as max_frequency,
    STDDEV(frequency) as frequency_volatility
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
WHERE settlementDate >= '2025-01-01'
GROUP BY settlementDate
ORDER BY settlementDate
```

**Renewable Penetration:**
```sql
WITH generation AS (
    SELECT 
        settlementDate,
        settlementPeriod,
        SUM(CASE WHEN fuelType IN ('WIND', 'SOLAR', 'HYDRO', 'BIOMASS') 
            THEN generation ELSE 0 END) as renewable,
        SUM(generation) as total
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE settlementDate >= '2025-01-01'
    GROUP BY settlementDate, settlementPeriod
)
SELECT 
    settlementDate,
    AVG(renewable / NULLIF(total, 0) * 100) as renewable_percentage,
    MAX(renewable / NULLIF(total, 0) * 100) as max_renewable_percentage
FROM generation
GROUP BY settlementDate
ORDER BY settlementDate
```

### Phase 2: Dashboard Framework (2-3 days)

#### Technology Options:

**Option A: Streamlit (Recommended for speed)**
- **Pros:** Fast development, Python-native, easy BigQuery integration
- **Cons:** Limited customization vs full web framework
- **Best for:** Internal dashboards, rapid prototyping

**Option B: Dash/Plotly**
- **Pros:** More customization, interactive charts, production-ready
- **Cons:** Steeper learning curve
- **Best for:** Public-facing dashboards

**Option C: Next.js + React**
- **Pros:** Full control, modern web stack, best performance
- **Cons:** Longest development time
- **Best for:** Production applications with complex requirements

#### Recommended Stack (Streamlit):
```python
# requirements.txt
streamlit>=1.28.0
google-cloud-bigquery>=3.11.0
pandas>=2.1.0
plotly>=5.17.0
altair>=5.1.0
```

#### Dashboard Structure:
```
dashboard/
├── app.py                 # Main Streamlit app
├── pages/
│   ├── 1_fuel_mix.py     # Fuel generation analysis
│   ├── 2_frequency.py    # System frequency monitoring
│   ├── 3_costs.py        # Price analysis
│   ├── 4_interconnectors.py  # Cross-border flows
│   └── 5_renewables.py   # Wind/solar analysis
├── components/
│   ├── data_loader.py    # BigQuery connection & caching
│   ├── charts.py         # Reusable chart components
│   └── filters.py        # Date/time range filters
├── utils/
│   ├── queries.py        # SQL query templates
│   └── metrics.py        # Calculation functions
└── config.py             # Configuration settings
```

### Phase 3: Core Visualizations (3-5 days)

#### Must-Have Charts:

1. **Real-Time Fuel Mix (Stacked Area)**
   - X-axis: Time (settlement periods)
   - Y-axis: Generation (MW)
   - Layers: Each fuel type
   - Interactive: Hover for exact values

2. **Daily Generation Heatmap**
   - Rows: Days
   - Columns: Settlement periods (48 per day)
   - Color: Total generation or specific fuel

3. **System Frequency Line Chart**
   - X-axis: Time
   - Y-axis: Frequency (Hz)
   - Highlight: Out-of-range periods (49.5-50.5 Hz)

4. **Price Duration Curve**
   - X-axis: Sorted time periods
   - Y-axis: System price
   - Shows: Price volatility

5. **Renewable Penetration Gauge**
   - Current renewable %
   - Historical trend
   - Target comparison

6. **Interconnector Flow Sankey Diagram**
   - Shows: Import/export flows
   - From: Countries
   - To: GB

#### Interactive Features:
- Date range picker (single day, week, month, custom)
- Settlement period selector
- Fuel type filter
- Aggregation level (5-min, hourly, daily)
- Export to CSV/PNG

### Phase 4: Advanced Analytics (5-7 days)

#### Features:

1. **Forecasting**
   - Prophet/ARIMA for demand forecasting
   - ML models for price prediction
   - Renewable generation forecasting
   - Compare forecast vs actual

2. **Correlation Analysis**
   - Fuel mix vs prices
   - Frequency vs generation
   - Weather vs renewable output
   - Cross-border flows vs prices

3. **Anomaly Detection**
   - Unusual price spikes
   - Frequency deviations
   - Generation outages
   - Alert system

4. **Cost Analysis**
   - System balancing costs
   - Imbalance costs by settlement period
   - Cost trends over time

5. **Unit Performance**
   - Individual unit generation patterns
   - Bid-offer strategy analysis
   - Utilization rates
   - Revenue estimation

### Phase 5: Deployment (1-2 days)

#### Hosting Options:

**Option A: Streamlit Cloud (Free)**
- Push to GitHub
- Connect Streamlit Cloud
- Add BigQuery credentials as secrets
- Deploy (takes 5 minutes)

**Option B: Google Cloud Run**
- Containerize with Docker
- Deploy to Cloud Run
- Auto-scaling, pay-per-use
- Better for production

**Option C: Local/Internal Server**
- Run on local machine or internal server
- Use VPN for access
- No public exposure

---

## 🛠️ Development Setup

### Step 1: Create Dashboard Project
```bash
cd ~/GB\ Power\ Market\ JJ
mkdir dashboard
cd dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install streamlit google-cloud-bigquery pandas plotly altair
```

### Step 2: Create Basic App
```python
# app.py
import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px

# Configure page
st.set_page_config(
    page_title="UK Energy Market Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Initialize BigQuery client
@st.cache_resource
def get_bigquery_client():
    return bigquery.Client(project="inner-cinema-476211-u9")

# Load data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_fuel_data(date):
    client = get_bigquery_client()
    query = f"""
    SELECT 
        settlementPeriod,
        fuelType,
        SUM(generation) as generation
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE settlementDate = '{date}'
    GROUP BY settlementPeriod, fuelType
    ORDER BY settlementPeriod, fuelType
    """
    return client.query(query).to_dataframe()

# Dashboard UI
st.title("⚡ UK Energy Market Dashboard")
st.markdown("Real-time analysis of UK electricity generation and system status")

# Date selector
date = st.date_input("Select Date", value=pd.Timestamp("2025-07-16"))

# Load and display data
with st.spinner("Loading data..."):
    df = load_fuel_data(date)

if not df.empty:
    # Create stacked area chart
    fig = px.area(
        df, 
        x='settlementPeriod', 
        y='generation', 
        color='fuelType',
        title=f"Generation by Fuel Type - {date}"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Generation", f"{df['generation'].sum():,.0f} MW")
    with col2:
        renewable = df[df['fuelType'].isin(['WIND', 'SOLAR'])]['generation'].sum()
        st.metric("Renewable Generation", f"{renewable:,.0f} MW")
    with col3:
        renewable_pct = (renewable / df['generation'].sum() * 100)
        st.metric("Renewable %", f"{renewable_pct:.1f}%")
else:
    st.warning("No data available for selected date")
```

### Step 3: Run Dashboard
```bash
streamlit run app.py
```

---

## 📝 Key Questions to Answer with Dashboard

### Business Questions:
1. What is the current generation mix?
2. How much renewable energy are we generating?
3. What are the peak demand hours?
4. How stable is the grid frequency?
5. What are the system imbalance costs?
6. How much are we importing/exporting?

### Technical Questions:
1. Which units are most/least utilized?
2. What's the typical bid-offer spread?
3. How accurate are renewable forecasts?
4. What's the correlation between wind and prices?
5. How does frequency respond to generation changes?

### Planning Questions:
1. What are generation trends over time?
2. Are renewables increasing their share?
3. What's the seasonal variation?
4. How predictable is demand?

---

## 🔧 Useful Python Snippets

### Connect to BigQuery:
```python
from google.cloud import bigquery
import os

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'

# Create client
client = bigquery.Client(project='inner-cinema-476211-u9')
```

### Query with Pandas:
```python
query = """
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate = '2025-07-16'
LIMIT 1000
"""
df = client.query(query).to_dataframe()
```

### Cache Results (Streamlit):
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def expensive_query():
    # Query runs once, then cached
    return client.query("SELECT ...").to_dataframe()
```

---

## 📊 Sample Dashboard Pages

### Page 1: Overview
- Current generation mix (pie chart)
- 24-hour generation trend (line chart)
- Key metrics (total MW, renewable %, frequency)
- System status indicators

### Page 2: Fuel Analysis
- Generation by fuel type over time
- Fuel mix comparison (day/week/month)
- Capacity factors
- Cost per MWh by fuel

### Page 3: Market Prices
- System buy/sell prices
- Price duration curves
- Imbalance costs
- Price volatility analysis

### Page 4: System Frequency
- Real-time frequency monitoring
- Frequency distribution
- Out-of-range events
- Correlation with generation

### Page 5: Interconnectors
- Import/export flows by country
- Net position over time
- Cross-border price spreads
- Flow vs price correlation

### Page 6: Renewables
- Wind generation and forecasts
- Solar generation and forecasts
- Forecast accuracy metrics
- Curtailment analysis

### Page 7: Unit Analysis
- Top generators by volume
- Bid-offer strategies
- Unit availability
- Revenue estimation

---

## 🎯 Success Metrics

### Dashboard Performance:
- Load time < 2 seconds for cached queries
- Query time < 5 seconds for complex aggregations
- Refresh rate: Every 5 minutes for real-time data

### User Experience:
- Intuitive navigation
- Responsive design (mobile-friendly)
- Clear visualizations
- Helpful tooltips

### Data Quality:
- Zero data gaps
- Accurate calculations
- Consistent time zones
- Proper aggregations

---

## 🚧 Potential Challenges

### Challenge 1: Query Performance
**Issue:** Large datasets (100M+ rows) can be slow
**Solution:** 
- Use materialized views for common aggregations
- Pre-aggregate daily/hourly data
- Implement smart caching
- Query only needed date ranges

### Challenge 2: Real-Time Updates
**Issue:** Dashboard needs fresh data
**Solution:**
- Cache with TTL (time-to-live)
- Incremental refresh strategy
- Load latest day only, merge with cached history

### Challenge 3: Complex Calculations
**Issue:** Some metrics require multi-table joins
**Solution:**
- Pre-compute in BigQuery views
- Use CTEs (Common Table Expressions)
- Optimize query structure

### Challenge 4: User Authentication (if public)
**Issue:** Restricting access
**Solution:**
- Streamlit authentication libraries
- OAuth integration
- API key system

---

## 📚 Resources

### Documentation:
- [Streamlit Docs](https://docs.streamlit.io)
- [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest)
- [Plotly Charts](https://plotly.com/python/)
- [Elexon BMRS API](https://developer.data.elexon.co.uk/)

### Example Dashboards:
- [Streamlit Gallery](https://streamlit.io/gallery)
- [Plotly Dash Gallery](https://dash.gallery/Portal/)

### Similar Projects:
- [UK Grid Status](https://grid.iamkate.com/)
- [Electric Insights](https://electricinsights.co.uk/)

---

## 🎯 Next Steps

1. **Immediate (Tonight):** Wait for data load completion (10 PM)
2. **Tomorrow Morning:** 
   - Verify data quality
   - Run sample queries
   - Document data structure
3. **This Week:**
   - Build basic Streamlit dashboard
   - Create 3-5 core visualizations
   - Test with sample queries
4. **Next Week:**
   - Add advanced analytics
   - Implement forecasting
   - Deploy to production

---

**Ready to build when data loading completes!** 🚀

*Created: 28 Oct 2025*
