# GSP Wind Analysis Guide

## 📊 What is GSP Wind Analysis?

**Grid Supply Points (GSPs)** are the 17 regional connection points between the national transmission network and local distribution networks in Great Britain. Analyzing power flows at GSPs reveals:

- Regional energy balance (generation vs demand)
- Wind generation correlation with imports/exports
- Network constraints and bottlenecks
- Real-time grid flexibility needs

**Your Script:** `gsp_wind_analysis.py`  
**Update Frequency:** Every 30 minutes (configurable)  
**Data Source:** BigQuery (`bmrs_indgen_iris` + `bmrs_fuelinst`)

---

## 🎯 What You Can Analyze

### 1. **Regional Power Balance**

**Question:** Which regions export power? Which import?

**How It Works:**
```python
# Your script calculates for each GSP:
- Total Generation (from bmrs_indgen_iris)
- Total Demand (inferred from national totals)
- Net Flow = Generation - Demand
  - Positive = Exporter (surplus generation)
  - Negative = Importer (deficit, needs power)
```

**Current Issue:** Script references `nationalGridBmUnit` column that doesn't exist in `bmrs_indgen_iris`

**Schema Fix Needed:**
```sql
-- Check actual columns
SELECT column_name FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'bmrs_indgen_iris'

-- Actual columns are:
-- dataset, publishTime, startTime, settlementDate, settlementPeriod, 
-- generation, boundary, ingested_utc, source
```

**Fixed Query:**
```python
query = f"""
WITH gsp_generation AS (
  SELECT
    boundary as gspGroup,  -- NOT nationalGridBmUnit!
    settlementDate,
    settlementPeriod,
    SUM(generation) as total_generation
  FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
  WHERE settlementDate = CURRENT_DATE()
    AND boundary IS NOT NULL
  GROUP BY boundary, settlementDate, settlementPeriod
),
national_wind AS (
  SELECT
    settlementDate,
    settlementPeriod,
    SUM(generation) as wind_mw
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
  WHERE fuelType = 'WIND'
    AND settlementDate = CURRENT_DATE()
  GROUP BY settlementDate, settlementPeriod
)
SELECT
  g.gspGroup,
  g.total_generation,
  w.wind_mw as national_wind,
  -- Net flow calculation (need demand data)
  g.total_generation - <demand_estimate> as net_flow
FROM gsp_generation g
JOIN national_wind w USING (settlementDate, settlementPeriod)
ORDER BY g.settlementDate DESC, g.settlementPeriod DESC
LIMIT 17  -- 17 GSPs in GB
"""
```

---

### 2. **Wind Correlation Analysis**

**Question:** How does wind generation affect regional power flows?

**Hypothesis:**
- High wind in Scotland → Scotland exports more
- Low wind nationally → More imports to demand centers
- Wind ramps (sudden changes) → Grid balancing challenges

**Analysis Approach:**
```python
import pandas as pd
import numpy as np

# Load GSP data with wind
df = pd.read_csv('gsp_wind_data_latest.csv')

# Calculate correlation
correlation = df.groupby('gspGroup').apply(lambda x: 
    np.corrcoef(x['national_wind_mw'], x['net_flow_mw'])[0,1]
)

print("Wind Correlation by Region:")
print(correlation.sort_values(ascending=False))
```

**Expected Patterns:**
- **North Scotland**: Strong positive correlation (wind rich, exports when windy)
- **South East**: Negative correlation (demand center, imports more when wind low)
- **Yorkshire**: Mixed (some wind, some demand)

**Use Cases:**
- Predict regional prices from wind forecasts
- Identify grid constraint risks
- Optimize battery placement (high volatility areas)
- Forecast interconnector flows

---

### 3. **Network Congestion Detection**

**Question:** Where are grid bottlenecks? Which regions are constrained?

**Indicators:**
- GSP consistently exporting (generation can't flow out)
- Large generation but low net export (constraint)
- Price differences vs national average

**Analysis:**
```python
# Identify constrained GSPs
df['constraint_indicator'] = df['total_generation'] / df['net_flow']
# Ratio > 2 suggests constraint (generating but not exporting)

constrained = df[df['constraint_indicator'] > 2].groupby('gspGroup').size()
print("Most Constrained GSPs:")
print(constrained.sort_values(ascending=False).head(10))
```

**Example:**
- **North Scotland**: High wind generation but limited transmission capacity to south
- **South Wales**: Large power stations but local demand low
- **Eastern**: Offshore wind but limited interconnection

**Implications:**
- Higher curtailment risk (turn down generators)
- Price premiums for local flexibility (batteries!)
- Network reinforcement needs
- Battery co-location opportunities

---

### 4. **Real-Time Grid Flexibility Needs**

**Question:** When does the grid need most flexibility? Battery opportunities?

**Flexibility Indicators:**
- **Ramp rates**: How fast does net flow change?
- **Volatility**: Standard deviation of net flow
- **Imbalance**: Difference between forecast and actual

**Calculate Flexibility Value:**
```python
# Ramp rate (MW change per 30 minutes)
df['ramp_rate'] = df.groupby('gspGroup')['net_flow'].diff()

# Volatility (rolling window)
df['volatility'] = df.groupby('gspGroup')['net_flow'].rolling(4).std()

# High flexibility value regions
flexibility_score = df.groupby('gspGroup').agg({
    'ramp_rate': lambda x: abs(x).mean(),
    'volatility': 'mean'
})

flexibility_score['score'] = (
    flexibility_score['ramp_rate'] * 0.6 + 
    flexibility_score['volatility'] * 0.4
)

print("Regions with Highest Flexibility Needs:")
print(flexibility_score.sort_values('score', ascending=False))
```

**Battery Siting Strategy:**
- Deploy batteries in high-flexibility regions
- Size based on typical ramp requirements
- Co-locate with wind farms (smooth output)
- Target constrained areas (local solutions)

---

### 5. **Interconnector Flow Prediction**

**Question:** Can we predict interconnector flows from GSP data?

**Logic:**
- GB is net importer or exporter
- Southern GSPs (near France/Belgium) import more when GB needs power
- Northern GSPs export when Scotland has surplus wind

**Predictive Model:**
```python
from sklearn.linear_model import LinearRegression

# Features: GSP flows
X = df.pivot(columns='gspGroup', values='net_flow')
X['national_wind'] = df.groupby(['settlementDate', 'settlementPeriod'])['national_wind'].mean()

# Target: interconnector flows (from your Dashboard data)
y = get_interconnector_flows()  # From bmrs_interconnector table

model = LinearRegression()
model.fit(X, y)

# Predict
predictions = model.predict(X)
print(f"Model R²: {model.score(X, y):.3f}")
```

**Use Cases:**
- Forecast interconnector congestion
- Predict cross-border pricing
- Optimize battery near interconnectors
- Trading strategies (import when cheap)

---

### 6. **Renewable Integration Monitoring**

**Question:** How well does the grid absorb renewable energy?

**Metrics:**
- **Curtailment risk**: High wind generation + low demand = must turn down wind
- **Balancing costs**: More renewables = more frequency regulation needed
- **Storage utilization**: Do batteries absorb excess wind?

**Dashboard Visualization:**
```python
import plotly.express as px

fig = px.scatter(df, 
    x='national_wind_mw', 
    y='net_flow_mw',
    color='gspGroup',
    size='total_generation',
    hover_data=['settlementDate', 'settlementPeriod'],
    title='Wind Generation vs Regional Flows'
)

fig.add_hline(y=0, line_dash="dash", line_color="red", 
              annotation_text="Balance Point")
fig.show()
```

**Insights:**
- When wind > X MW, certain GSPs always export
- Curtailment events visible as plateau in export
- Battery charging correlated with high wind periods

---

## 🛠️ Fixing Your Script

### Issue 1: Missing Module
```bash
# Error: ModuleNotFoundError: No module named 'gspread_dataframe'
# Fix:
pip3 install --user gspread-dataframe
```

### Issue 2: Wrong Column Name
```python
# Current (WRONG):
query = """
SELECT nationalGridBmUnit, generation
FROM bmrs_indgen_iris
"""

# Fixed:
query = """
SELECT boundary as gspGroup, generation
FROM bmrs_indgen_iris
WHERE boundary IS NOT NULL  -- Filter out nulls
"""
```

### Issue 3: Missing GSP Name Mapping
```python
# bmrs_indgen_iris uses boundary codes (_A, _B, _C, etc.)
# Need to map to readable names
GSP_NAMES = {
    '_A': 'Northern Scotland',
    '_B': 'Southern Scotland',
    '_C': 'North West England',
    '_D': 'North East England',
    '_E': 'Yorkshire',
    '_F': 'North Wales & Mersey',
    '_G': 'East Midlands',
    '_H': 'Midlands',
    '_J': 'South Wales',
    '_K': 'South East England',
    '_L': 'London',
    '_M': 'Southern England',
    '_N': 'South West England',
    '_P': 'Eastern England'
}
```

### Full Fixed Query
```python
query = f"""
WITH gsp_latest AS (
  SELECT
    boundary,
    LAST_VALUE(generation) OVER (
      PARTITION BY boundary 
      ORDER BY publishTime 
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as latest_generation,
    LAST_VALUE(publishTime) OVER (
      PARTITION BY boundary 
      ORDER BY publishTime 
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as timestamp
  FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
  WHERE DATE(publishTime) = CURRENT_DATE()
    AND boundary IS NOT NULL
    AND boundary != ''
),
wind_latest AS (
  SELECT
    LAST_VALUE(generation) OVER (
      ORDER BY publishTime 
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as wind_mw,
    LAST_VALUE(publishTime) OVER (
      ORDER BY publishTime 
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as timestamp
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
  WHERE fuelType = 'WIND'
    AND DATE(publishTime) = CURRENT_DATE()
)
SELECT
  g.boundary as gsp_code,
  g.latest_generation as generation_mw,
  g.timestamp as gsp_timestamp,
  w.wind_mw as national_wind_mw,
  w.timestamp as wind_timestamp
FROM gsp_latest g
CROSS JOIN wind_latest w
ORDER BY g.boundary
"""
```

---

## 📊 Output to Google Sheets

### Sheet Structure
```
| GSP Group            | Generation | Net Flow | Wind MW | Status    | Timestamp          |
|----------------------|------------|----------|---------|-----------|-------------------|
| Northern Scotland    | 3,245 MW   | +1,200   | 13,323  | 🟢 Export | 2025-11-10 09:16  |
| Southern Scotland    | 2,156 MW   | +500     | 13,323  | 🟢 Export | 2025-11-10 09:16  |
| North West England   | 1,890 MW   | -1,200   | 13,323  | 🔴 Import | 2025-11-10 09:16  |
| Yorkshire            | 2,450 MW   | -200     | 13,323  | 🔴 Import | 2025-11-10 09:16  |
| ...                  | ...        | ...      | ...     | ...       | ...               |
```

### Formatting Rules
```python
def format_gsp_row(gsp):
    """Format GSP data for Google Sheets"""
    status_emoji = "🟢" if gsp['net_flow'] > 100 else "🔴" if gsp['net_flow'] < -100 else "🟡"
    status_text = "Export" if gsp['net_flow'] > 100 else "Import" if gsp['net_flow'] < -100 else "Balanced"
    
    return [
        gsp['gsp_name'],
        f"{gsp['generation']:.0f} MW",
        f"{gsp['net_flow']:+.0f} MW",  # + or - sign
        f"{gsp['national_wind']:.0f} MW",
        f"{status_emoji} {status_text}",
        gsp['timestamp'].strftime('%Y-%m-%d %H:%M')
    ]
```

### Conditional Formatting
```python
# Apply color coding
requests = [
    {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 20, "startColumnIndex": 2, "endColumnIndex": 3}],
                "booleanRule": {
                    "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                    "format": {"backgroundColor": {"red": 0.85, "green": 1, "blue": 0.85}}  # Light green
                }
            }
        }
    },
    {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 20, "startColumnIndex": 2, "endColumnIndex": 3}],
                "booleanRule": {
                    "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
                    "format": {"backgroundColor": {"red": 1, "green": 0.85, "blue": 0.85}}  # Light red
                }
            }
        }
    }
]

dashboard.spreadsheet.batch_update({"requests": requests})
```

---

## 🔄 Automation Setup

### Cron Schedule
```bash
# Every 30 minutes
*/30 * * * * cd ~/GB\ Power\ Market\ JJ && .venv/bin/python gsp_wind_analysis.py >> logs/gsp_wind.log 2>&1

# Every 10 minutes (more frequent)
*/10 * * * * cd ~/GB\ Power\ Market\ JJ && .venv/bin/python gsp_wind_analysis.py >> logs/gsp_wind.log 2>&1
```

### Error Handling
```python
import logging
from datetime import datetime

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    # Main analysis
    df = client.query(query).to_dataframe()
    
    if df.empty:
        logging.warning("No data returned from BigQuery")
        sys.exit(1)
    
    # Update sheet
    dashboard.update(values=rows, range_name='A2:F20')
    logging.info(f"✅ Updated {len(df)} GSPs")
    
except Exception as e:
    logging.error(f"❌ Analysis failed: {e}")
    # Send alert
    send_alert(f"GSP Wind Analysis failed: {e}")
    sys.exit(1)
```

---

## 📈 Advanced Use Cases

### 1. Battery Dispatch Optimization
```python
def optimal_battery_dispatch(gsp_data, battery_capacity=50):
    """Calculate optimal battery charge/discharge based on GSP flows"""
    
    recommendations = []
    for _, row in gsp_data.iterrows():
        gsp = row['gsp_name']
        net_flow = row['net_flow_mw']
        wind = row['national_wind_mw']
        
        # High wind + export → Charge battery (absorb surplus)
        if wind > 10000 and net_flow > 500:
            action = 'CHARGE'
            reason = f'High wind ({wind:.0f}MW), {gsp} exporting ({net_flow:.0f}MW)'
        
        # Low wind + import → Discharge battery (support demand)
        elif wind < 5000 and net_flow < -500:
            action = 'DISCHARGE'
            reason = f'Low wind ({wind:.0f}MW), {gsp} importing ({net_flow:.0f}MW)'
        
        else:
            action = 'HOLD'
            reason = 'Balanced conditions'
        
        recommendations.append({
            'gsp': gsp,
            'action': action,
            'reason': reason,
            'confidence': calculate_confidence(row)
        })
    
    return recommendations
```

### 2. Price Forecasting
```python
def forecast_regional_price(gsp_flow, national_wind, base_price=50):
    """Estimate regional price premium/discount"""
    
    # Import regions pay premium
    import_premium = max(0, -gsp_flow / 1000 * 5)  # £5/MWh per GW imported
    
    # High wind = lower prices
    wind_discount = (national_wind / 1000) * 2  # £2/MWh per GW wind
    
    estimated_price = base_price + import_premium - wind_discount
    return max(0, estimated_price)
```

### 3. Curtailment Risk Alert
```python
def curtailment_risk_score(gsp_data):
    """Calculate wind curtailment risk by region"""
    
    risks = []
    for _, row in gsp_data.iterrows():
        if row['national_wind_mw'] > 15000:  # High wind
            if row['net_flow_mw'] > 1000:  # Exporting but...
                if row['generation_mw'] > 3000:  # ...still high local generation
                    risk = 'HIGH'
                    message = f"{row['gsp_name']}: Export constrained, curtailment likely"
                    risks.append({'gsp': row['gsp_name'], 'risk': risk, 'message': message})
    
    return risks
```

---

## 🎓 Learning Resources

### GSP Basics
- **17 GSPs in GB**: Northern Scotland → Southern England
- **Connection voltage**: 275kV or 400kV
- **Metering**: All flows measured in real-time
- **Charging**: TNUoS charges based on location and flow

### Power Flow Concepts
- **Generation > Demand**: GSP exports (flows to transmission)
- **Demand > Generation**: GSP imports (receives from transmission)
- **Constraints**: Physical limits on transmission capacity
- **Losses**: ~2-3% transmission losses

### Wind Patterns
- **Scotland**: 50%+ of GB wind capacity
- **Offshore**: Large farms in North Sea, Irish Sea
- **Ramp events**: Wind can change 10 GW in hours
- **Curtailment**: Must turn down when grid can't absorb

---

## 🚀 Quick Start

### Step 1: Fix Dependencies
```bash
cd ~/GB\ Power\ Market\ JJ
pip3 install --user gspread-dataframe
```

### Step 2: Fix Script
Update `gsp_wind_analysis.py` query to use `boundary` instead of `nationalGridBmUnit`

### Step 3: Test Run
```bash
python3 gsp_wind_analysis.py
```

### Step 4: Check Output
Open Google Sheet: [GSP Wind Analysis](https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID)

### Step 5: Schedule
```bash
./setup_gsp_cron.sh  # Already exists for GSP auto-updater
```

---

## 📊 Data Quality Checks

### Validation Rules
```python
def validate_gsp_data(df):
    """Ensure data quality"""
    
    issues = []
    
    # Check 1: Have all 17 GSPs?
    if len(df) != 17:
        issues.append(f"Expected 17 GSPs, got {len(df)}")
    
    # Check 2: Generation positive?
    if (df['generation_mw'] < 0).any():
        issues.append("Negative generation detected")
    
    # Check 3: Wind realistic? (0-25 GW typical)
    if df['national_wind_mw'].max() > 30000:
        issues.append(f"Unrealistic wind: {df['national_wind_mw'].max():.0f} MW")
    
    # Check 4: Timestamps recent?
    latest = pd.to_datetime(df['timestamp'].max())
    if (datetime.now() - latest).total_seconds() > 3600:
        issues.append(f"Data stale: {latest}")
    
    return issues
```

---

**Ready to understand GB's real-time power flows!** 🌬️⚡
