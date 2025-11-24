# 🎯 GB Energy Dashboard Implementation Plan

**Date**: November 23, 2025  
**Based On**: `energy_dashboard_complete_design.md` from ChatGPT  
**Current State**: Partial implementation with daily charts and Apps Script  
**Goal**: Full dark-themed professional dashboard with real-time KPIs

---

## 📊 What You Already Have ✅

### 1. **Python Scripts** ✅
- `daily_dashboard_auto_updater.py` - Fetches TODAY's data, creates 4 embedded charts
- BigQuery queries for prices, demand, generation, frequency
- Google Sheets API integration
- Deployed on UpCloud with 30-min cron

### 2. **Apps Script** ✅
- `gb_energy_dashboard_apps_script.gs` - Enhanced maintenance script
- Custom menu with manual refresh
- Audit logging with color-coded status
- Auto-refresh trigger (15 minutes)
- Chart creation functions

### 3. **Google Sheets Structure** ✅
- Dashboard sheet (48 worksheets total)
- Daily_Chart_Data sheet
- KPIs in F7:G17
- Charts in A18:H29
- Connected to BigQuery

### 4. **Railway Integration** ✅
- Railway API with workspace endpoints
- Python analytics accessible via API
- ChatGPT integration ready

---

## 🆕 What the Design Adds

### 1. **Dark Theme** 🎨
**Status**: ❌ NOT IMPLEMENTED  
**Effort**: Low (30 minutes)

The design specifies:
- Background: `#121212` (charcoal black)
- Primary text: `#FFFFFF` (white)
- KPI colors: Red/Blue/Green/Orange/Purple
- Professional Material Black theme

**Implementation**:
- Apply via Apps Script formatting
- Can be done programmatically
- Won't affect data or logic

### 2. **Enhanced KPI Layout** 📊
**Status**: ⚠️ PARTIALLY IMPLEMENTED  
**Effort**: Medium (1-2 hours)

**Current**: KPIs in F7:G17 (11 rows, compact)  
**Design**: KPIs in A3:G4 (single row, horizontal, color-coded)

| Current KPIs | Design KPIs |
|--------------|-------------|
| ✅ Avg Price | ✅ Avg Price |
| ✅ Max Price | Demand MW (NEW) |
| ✅ Min Price | Generation MW (NEW) |
| ✅ Demand (avg) | Wind Share % (NEW) |
| ✅ Frequency (avg) | Margin MW (NEW) |
| Settlement Periods | Constraint MW (NEW) |

**Missing KPIs**:
- Total Demand MW (current)
- Total Generation MW (current)
- Wind Share % (calculated)
- Margin MW (Gen - Demand)
- Constraint MW (NEW - needs bmrs_bod_iris)

### 3. **Enhanced Charts** 📈
**Status**: ⚠️ PARTIALLY IMPLEMENTED  
**Effort**: High (3-4 hours)

#### Current Charts (4 total):
1. Market Price (line chart)
2. Demand (line chart)
3. IC Import (line chart)
4. Frequency (line chart)

#### Design Charts (4 total):
1. **Demand vs Generation vs Constraints** (Combo chart)
   - Missing: Constraints data
   - Missing: Wind as area series
   
2. **Price vs Frequency** (Dual axis)
   - ✅ Have both metrics
   - Need: Combine into single dual-axis chart
   
3. **GSP Regional Generation Mix** (Stacked column)
   - ❌ NOT IMPLEMENTED
   - Need: GSP data by region
   - Need: Fuel type breakdown
   
4. **Forecast & Constraint Projection** (Line forecast)
   - ❌ NOT IMPLEMENTED
   - Need: ARIMA forecasting integration
   - Need: Constraint forecast logic

### 4. **Apps Script Enhancements** 🔧
**Status**: ⚠️ PARTIALLY IMPLEMENTED  
**Effort**: Medium (2 hours)

#### Current Features:
- ✅ Custom menu
- ✅ Manual refresh
- ✅ Audit logging
- ✅ Auto-refresh trigger

#### Design Additions:
- ❌ "Run Analytics" button (trigger Python on Railway)
- ❌ "Export Report" button (PDF to Drive)
- ❌ Connected Sheets refresh integration

### 5. **Python Analytics Integration** 🧠
**Status**: ⚠️ PARTIALLY AVAILABLE  
**Effort**: Medium (2-3 hours)

**Available** (not integrated):
- `advanced_statistical_analysis_enhanced.py`
- ARIMA forecasting
- Regression models
- Seasonal decomposition

**Need to Add**:
- Railway API endpoint to trigger analytics
- Apps Script button to call Railway
- Write results back to BigQuery/Sheets
- Display forecasts in Chart 4

---

## 🎯 Implementation Priorities

### Phase 1: Quick Wins (2-3 hours) ⭐
**Goal**: Improve current dashboard aesthetics and add missing KPIs

1. **Dark Theme Formatting** (30 min)
   - Create Apps Script function to apply dark theme
   - Background colors, text colors, borders
   - Professional Material Black palette

2. **Enhance KPI Layout** (1 hour)
   - Move KPIs from F7:G17 to A3:G4 (horizontal)
   - Add missing KPIs: Total Demand/Gen, Wind Share, Margin, Constraints
   - Color-code each KPI with accent colors
   - Update Python script to calculate new metrics

3. **Improve Chart Positioning** (30 min)
   - Ensure charts fit properly in A6:G60
   - Adjust chart sizes and spacing
   - Add chart titles and axis labels

### Phase 2: Enhanced Analytics (3-4 hours) ⭐⭐
**Goal**: Add constraint tracking and GSP regional data

1. **Add Constraint Data** (1.5 hours)
   - Query `bmrs_bod_iris` for constraint volumes
   - Calculate constraint MW totals
   - Add to KPI row
   - Add constraint area series to Chart 1

2. **Create GSP Regional Chart** (2 hours)
   - Query BigQuery for GSP-level generation
   - Break down by fuel type (CCGT, Wind, Solar, Nuclear)
   - Create stacked column chart
   - Replace Chart 3

3. **Combine Price/Frequency Chart** (30 min)
   - Merge current Chart 2 and Chart 4
   - Dual-axis line chart
   - Better use of space

### Phase 3: Advanced Features (4-5 hours) ⭐⭐⭐
**Goal**: Full analytics integration and forecasting

1. **Python Analytics Button** (1 hour)
   - Create Railway endpoint: `/trigger_analytics`
   - Apps Script button: "Run Analytics"
   - Progress indicator and completion alert

2. **ARIMA Forecasting Integration** (2 hours)
   - Run `advanced_statistical_analysis_enhanced.py` via Railway
   - Store forecast results in BigQuery
   - Display in Chart 4 with confidence intervals

3. **PDF Export to Drive** (1 hour)
   - Apps Script export function
   - Create daily PDF snapshots
   - Save to designated Drive folder
   - Track in audit log

4. **Connected Sheets Refresh** (1 hour)
   - BigQuery Connected Sheets setup
   - Auto-refresh on data updates
   - Reduce reliance on Python scripts

---

## 📋 Detailed Implementation Steps

### Phase 1.1: Dark Theme (30 min)

**Create new Apps Script function:**

```javascript
function applyDarkTheme() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dashboard = ss.getSheetByName('Dashboard');
  
  // Theme colors
  const DARK_BG = '#121212';
  const WHITE_TEXT = '#FFFFFF';
  const ACCENT_GREY = '#9E9E9E';
  
  // Apply to entire sheet
  dashboard.setBackground(DARK_BG);
  dashboard.getDataRange().setFontColor(WHITE_TEXT);
  
  // KPI row colors
  dashboard.getRange('A3').setBackground('#E53935'); // Red - Demand
  dashboard.getRange('B3').setBackground('#1E88E5'); // Blue - Generation
  dashboard.getRange('C3').setBackground('#43A047'); // Green - Wind
  dashboard.getRange('D3').setBackground('#FB8C00'); // Orange - Margin
  dashboard.getRange('E3').setBackground('#9E9E9E'); // Grey - Price
  dashboard.getRange('F3').setBackground('#8E24AA'); // Purple - Constraint
  
  // Gridlines
  dashboard.setGridlinesHidden(false);
  
  SpreadsheetApp.getUi().alert('✅ Dark theme applied!');
}
```

**Add to custom menu:**
```javascript
ui.createMenu('🔄 Dashboard')
  .addItem('Refresh Data Now', 'manualRefresh')
  .addItem('🎨 Apply Dark Theme', 'applyDarkTheme')  // NEW
  .addToUi();
```

### Phase 1.2: Enhanced KPIs (1 hour)

**Update Python script** (`daily_dashboard_auto_updater.py`):

```python
def create_summary_kpis(df):
    """
    Create 6 horizontal KPIs for A3:G4
    """
    # Calculate totals and metrics
    total_demand_mw = df['demand_mw'].iloc[-1] if len(df) > 0 else 0
    total_generation_mw = df['generation_mw'].iloc[-1] if len(df) > 0 else 0
    
    # Calculate wind share
    wind_generation = df['wind_mw'].sum() if 'wind_mw' in df.columns else 0
    wind_share_pct = (wind_generation / total_generation_mw * 100) if total_generation_mw > 0 else 0
    
    # Calculate margin
    margin_mw = total_generation_mw - total_demand_mw
    
    # Average price
    avg_price = df['market_price'].mean()
    
    # Constraint MW (need to add this data)
    constraint_mw = 0  # TODO: Query bmrs_bod_iris
    
    # Create 2-row data: Row 1 = Labels, Row 2 = Values
    kpi_data = [
        ['Total Demand MW', 'Generation MW', 'Wind Share %', 'Margin MW', 'Avg Price £/MWh', 'Constraint MW'],
        [
            f'{total_demand_mw:,.0f}',
            f'{total_generation_mw:,.0f}',
            f'{wind_share_pct:.1f}%',
            f'{margin_mw:,.0f}',
            f'£{avg_price:.2f}',
            f'{constraint_mw:,.0f}'
        ]
    ]
    
    return kpi_data
```

**Update sheet write location:**
```python
# Write to A3:G4 instead of F7:G17
dashboard.update(range_name='A3:G4', values=kpi_data, value_input_option='USER_ENTERED')
```

### Phase 1.3: Chart Repositioning (30 min)

**Update chart positions** in `daily_dashboard_auto_updater.py`:

```python
# Chart 1: A6:G18 (Demand vs Generation vs Constraints)
# Chart 2: A20:G32 (Price vs Frequency - dual axis)
# Chart 3: A34:G46 (GSP Regional Mix)
# Chart 4: A48:G60 (Forecast Overlay)
```

---

### Phase 2.1: Add Constraint Data (1.5 hours)

**Add to BigQuery query**:

```python
# Add constraint CTE
constraints AS (
    SELECT
        CAST(settlementDate AS DATE) as date,
        settlementPeriod as sp,
        SUM(ABS(CAST(levelFrom AS FLOAT64) - CAST(levelTo AS FLOAT64))) as constraint_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod_iris`
    WHERE CAST(settlementDate AS DATE) = CURRENT_DATE('Europe/London')
    GROUP BY date, sp
)
```

**Add to final SELECT**:
```python
SELECT
    ...existing columns...,
    COALESCE(c.constraint_mw, 0) as constraint_mw
FROM prices p
...existing joins...
LEFT JOIN constraints c ON p.date = c.date AND p.sp = c.sp
```

**Add to Chart 1** as area series:
```python
# In create_embedded_charts()
{
    "type": "AREA",
    "targetAxis": "LEFT_AXIS",
    "series": {
        "dataSourceColumnReference": {
            "name": "constraint_mw"
        }
    },
    "color": {"red": 0.55, "green": 0.14, "blue": 0.67}  # Purple
}
```

### Phase 2.2: GSP Regional Chart (2 hours)

**Create new BigQuery query for GSP data**:

```python
def fetch_gsp_regional_data(bq_client):
    """
    Fetch GSP-level generation by fuel type for TODAY
    """
    query = f"""
    SELECT
        gsp_region,
        fuel_type,
        SUM(generation) as generation_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE settlementDate = CURRENT_DATE('Europe/London')
    GROUP BY gsp_region, fuel_type
    ORDER BY gsp_region, fuel_type
    """
    return bq_client.query(query).to_dataframe()
```

**Create stacked column chart**:
```python
# Chart 3 config
{
    "basicChart": {
        "chartType": "COLUMN",
        "stackedType": "STACKED",
        "axis": [
            {
                "position": "BOTTOM_AXIS",
                "title": "GSP Region"
            },
            {
                "position": "LEFT_AXIS",
                "title": "Generation (MW)"
            }
        ],
        "series": [
            # One series per fuel type (CCGT, Wind, Solar, Nuclear)
        ]
    }
}
```

### Phase 3.1: Python Analytics Button (1 hour)

**Add Railway endpoint** to `api_gateway.py`:

```python
@app.post("/trigger_analytics")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
async def trigger_analytics(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Trigger Python analytics suite"""
    log_action("TRIGGER_ANALYTICS", {"source": "chatgpt"})
    
    try:
        # Run analytics script
        import subprocess
        result = subprocess.run(
            ["python3", "advanced_statistical_analysis_enhanced.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return {
            "success": True,
            "message": "Analytics completed",
            "output": result.stdout[-500:]  # Last 500 chars
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Add Apps Script button**:

```javascript
function triggerAnalytics() {
  const url = 'https://jibber-jabber-production.up.railway.app/trigger_analytics';
  const token = 'codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA';
  
  const options = {
    method: 'post',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const result = JSON.parse(response.getContentText());
    SpreadsheetApp.getUi().alert(`✅ Analytics completed!\n\n${result.message}`);
  } catch (e) {
    SpreadsheetApp.getUi().alert(`❌ Error: ${e.message}`);
  }
}
```

---

## 🎨 Complete Dark Theme Color Reference

```javascript
const THEME = {
  // Background
  DARK_BG: '#121212',        // Main background
  GRID: '#333333',           // Gridlines
  
  // Text
  PRIMARY: '#FFFFFF',        // Main text
  SECONDARY: '#9E9E9E',      // Muted text
  
  // KPI Colors
  RED: '#E53935',           // Demand
  BLUE: '#1E88E5',          // Generation
  GREEN: '#43A047',         // Wind
  ORANGE: '#FB8C00',        // Margin
  PURPLE: '#8E24AA',        // Constraints
  GREY: '#9E9E9E',          // Price
  
  // Chart Colors
  CYAN: '#00BCD4',          // Forecast
  MAGENTA: '#D81B60',       // Projection
  YELLOW: '#FDD835'         // Solar
};
```

---

## ✅ Implementation Checklist

### Phase 1: Quick Wins (2-3 hours)
- [ ] Create `applyDarkTheme()` function in Apps Script
- [ ] Add dark theme menu button
- [ ] Update KPI layout from vertical to horizontal (A3:G4)
- [ ] Add missing KPIs (Total Demand, Total Gen, Wind Share, Margin)
- [ ] Apply color-coding to KPI cells
- [ ] Reposition charts to match design (A6:G60)
- [ ] Test on actual dashboard

### Phase 2: Enhanced Analytics (3-4 hours)
- [ ] Add constraint data query to Python script
- [ ] Calculate constraint MW totals
- [ ] Add constraint area series to Chart 1
- [ ] Create GSP regional data query
- [ ] Implement stacked column chart for GSP mix
- [ ] Combine Price/Frequency into dual-axis chart
- [ ] Test chart rendering and data accuracy

### Phase 3: Advanced Features (4-5 hours)
- [ ] Create `/trigger_analytics` endpoint on Railway
- [ ] Add "Run Analytics" button to Apps Script menu
- [ ] Integrate ARIMA forecasting results
- [ ] Display forecasts in Chart 4
- [ ] Implement PDF export function
- [ ] Set up Drive folder for exports
- [ ] Test Connected Sheets refresh
- [ ] Document all new features

---

## 🚀 Recommended Approach

### Start with Phase 1 (Today - 2-3 hours)
This gives you:
- Professional dark theme
- Better KPI layout
- Improved visual hierarchy
- No data pipeline changes needed

### Then Phase 2 (This Week - 3-4 hours)
Adds valuable analytics:
- Constraint tracking (critical for market analysis)
- Regional generation breakdown
- Better chart organization

### Finally Phase 3 (Next Week - 4-5 hours)
Advanced features:
- Automated analytics
- Forecasting
- PDF exports

---

## 📁 Files to Modify

### Python Scripts
1. `daily_dashboard_auto_updater.py` - Main updates
   - KPI layout change (A3:G4)
   - Add constraint query
   - Add GSP query
   - Reposition charts

### Apps Script
1. `gb_energy_dashboard_apps_script.gs` - Add functions
   - `applyDarkTheme()`
   - `triggerAnalytics()`
   - `exportDashboardToDrive()`
   - Update menu

### Railway API
1. `api_gateway.py` - New endpoint
   - `/trigger_analytics`

---

## 🎯 Success Criteria

**Phase 1 Success**:
- ✅ Dashboard has dark theme (Material Black)
- ✅ KPIs displayed horizontally in A3:G4
- ✅ All 6 KPIs showing correct values
- ✅ Color-coded KPI cells
- ✅ Charts properly positioned in A6:G60

**Phase 2 Success**:
- ✅ Constraint MW displayed in KPI row
- ✅ Constraint area visible on Chart 1
- ✅ GSP regional chart showing fuel mix breakdown
- ✅ Price/Frequency combined in dual-axis chart
- ✅ All data updating every 30 minutes

**Phase 3 Success**:
- ✅ "Run Analytics" button triggers Python suite
- ✅ Forecasts displayed in Chart 4
- ✅ PDF exports saved to Drive
- ✅ Audit log tracking all operations
- ✅ ChatGPT can query dashboard via Railway

---

**Next Step**: Start with Phase 1.1 (Dark Theme) - 30 minutes to instant visual upgrade!

*Created: November 23, 2025*  
*Status: Ready to implement*
