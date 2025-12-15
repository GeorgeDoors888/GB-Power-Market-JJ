# Live Dashboard v2 - Technical Documentation

**Spreadsheet**: [GB Live 2](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)  
**Last Updated**: December 14, 2025 (Sparklines added)  
**Status**: ✅ Production - Auto-updating every 5 minutes

---

## 📊 Dashboard Architecture

### Layout Structure

```
Row 1-2:    Header & Last Updated timestamp
Row 4-6:    KPIs (VLP Revenue, Wholesale Price, Frequency, Total Gen, Wind, Demand)
Row 10:     Section headers
Row 12:     Column headers

GENERATION MIX (Rows 13-22):
  Column A: Fuel Type (🌬️ WIND, ⚛️ NUCLEAR, etc.)
  Column B: GW (current generation)
  Column C: Share %
  Column D: Sparkline (48-period trend) ← Line charts

INTERCONNECTORS (Rows 13-22):
  Column G: Connection (🇫🇷 ElecLink, 🇮🇪 East-West, etc.)
  Column H-I: Sparkline (MERGED, 48-period trend) ← Bar charts, 35px tall
  Column J: MW (current flow, positive=import, negative=export)

BATTERY BM REVENUE (Rows 24-29):
  Columns K-R:
    Row 24: Header (date + period count)
    Row 25: Totals (revenue, discharge/charge split)
    Row 26: Column headers
    Rows 27-29: 3 batteries (Lakeside, Tesla Hornsea, Whitelee)
  
  Columns S-T (Rows 30-34): BATTERY REVENUE SPARKLINES
    Row 30: Section header "📊 BM Revenue Trends (by Settlement Period)"
    Row 31: Total £ sparkline (orange line, 48-period trend)
    Row 32: Net MWh sparkline (blue columns, 48-period trend)
    Row 33: EWAP £/MWh sparkline (green line, 48-period trend)
    Row 34: Top BMU £ sparkline (red line, 48-period trend)

WIND ANALYSIS & OUTAGES (Row 30+):
  Row 30: Section header
  Columns A-C (Rows 40+): Wind Chart (Settlement Period, Actual GW, Forecast GW)
  Columns G-Q (Rows 31+): Outages (Asset Name, Fuel Type, Unavail MW, Cause, etc.)
```

### Hidden Sheet: Data_Hidden

**Purpose**: Stores 48-period timeseries data for sparklines

```
Rows 1-10:  Fuel type generation (WIND, NUCLEAR, CCGT, etc.) - 48 columns (A-AV)
Rows 11-20: Interconnector flows (INTELEC, INTEW, INTFR, etc.) - 48 columns (A-AV)
Rows 21-24: Battery revenue metrics (48 columns each):
  Row 21: Total £ by settlement period (all batteries combined)
  Row 22: Net MWh by settlement period (offer volume - bid volume)
  Row 23: EWAP £/MWh by settlement period (Energy Weighted Average Price)
  Row 24: Top BMU £ by settlement period (highest revenue battery each SP)
```

**Sparkline References**:
- Generation Mix sparklines (Column D): `=SPARKLINE(Data_Hidden!A1:AV1, {...})` (row 1 = WIND, row 2 = NUCLEAR, etc.)
- Interconnector sparklines (Column H): `=SPARKLINE(Data_Hidden!A11:AV11, {...})` (row 11 = ElecLink, row 12 = East-West, etc.)
- Battery Revenue sparklines (Column T): 
  - T31: Total £ by SP `=SPARKLINE(Data_Hidden!A21:AV21, {...})` (orange line)
  - T32: Net MWh by SP `=SPARKLINE(Data_Hidden!A22:AV22, {...})` (blue columns)
  - T33: EWAP £/MWh by SP `=SPARKLINE(Data_Hidden!A23:AV23, {...})` (green line)
  - T34: Top BMU £ by SP `=SPARKLINE(Data_Hidden!A24:AV24, {...})` (red line)

---

## 🔄 Auto-Update System

**Cron Schedule**: `*/5 * * * * /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh`

### Update Workflow (Every 5 minutes)

```bash
#!/bin/bash
# auto_update_dashboard_v2.sh

cd /home/george/GB-Power-Market-JJ

# 1. Main dashboard update
python3 update_live_dashboard_v2.py >> ~/dashboard_v2_updates.log 2>&1

# 2. Outages update
python3 update_live_dashboard_v2_outages.py >> ~/dashboard_v2_updates.log 2>&1

# 3. Wind chart update
python3 update_intraday_wind_chart.py >> ~/dashboard_v2_updates.log 2>&1

# 4. Battery BM revenue update
python3 update_battery_bm_revenue.py >> ~/dashboard_v2_updates.log 2>&1
```

**Log File**: `~/dashboard_v2_updates.log`

---

## 🐍 Python Scripts

### 1. update_live_dashboard_v2.py

**Purpose**: Main dashboard updater - KPIs, Generation Mix, Interconnectors, timeseries data

**Location**: `/home/george/GB-Power-Market-JJ/update_live_dashboard_v2.py`  
**Lines**: 566  
**Runtime**: ~5-10 seconds

**Data Sources**:
- BigQuery tables: `bmrs_fuelinst_iris`, `bmrs_mid_iris`, `bmrs_freq_iris`, `bmrs_windfor_iris`
- Project: `inner-cinema-476211-u9`
- Dataset: `uk_energy_prod`

**What it updates**:

1. **Timestamp** (Row 2): `Last Updated: 14/12/2025, 11:45:11 (v2.0) SP 24`

2. **KPIs** (Row 6, batch update):
   - A6: VLP Revenue (7-day avg, currently placeholder)
   - C6: Wholesale Price (£/MWh from bmrs_mid_iris)
   - E6: Grid Frequency (Hz)
   - G6: Total Generation (GW)
   - I6: Wind Generation (GW)
   - K6: Demand (GW)

3. **Generation Mix** (Rows 13-22, columns B-C):
   - Queries latest settlement period from `bmrs_fuelinst_iris`
   - Deduplicates by latest `publishTime`
   - Updates GW values and percentage shares
   - Fuel order: WIND, NUCLEAR, CCGT, BIOMASS, NPSHYD, OTHER, OCGT, COAL, OIL, PS

4. **Interconnectors** (Rows 13-22, column J):
   - Filters `fuelType LIKE 'INT%'` from `bmrs_fuelinst_iris`
   - Maps to rows:
     ```python
     'INTELEC': ('🇫🇷 ElecLink', 13),
     'INTEW': ('🇮🇪 East-West', 14),
     'INTFR': ('🇫🇷 IFA', 15),
     'INTGRNL': ('🇮🇪 Greenlink', 16),
     'INTIFA2': ('🇫🇷 IFA2', 17),
     'INTIRL': ('🇮🇪 Moyle', 18),
     'INTNED': ('🇳🇱 BritNed', 19),
     'INTNEM': ('🇧🇪 Nemo', 20),
     'INTNSL': ('🇳🇴 NSL', 21),
     'INTVKL': ('🇩🇰 Viking Link', 22)
     ```

5. **Data_Hidden Sheet**:
   - Fuel timeseries (A1:AV10): 48-period generation data for each fuel type
   - IC timeseries (A11:AV20): 48-period flow data for each interconnector
   - Battery sparkline data (A21:AV24): 48-period revenue metrics - NEW Dec 14, 2025
     * Row 21: Total £ by settlement period (all batteries combined)
     * Row 22: Net MWh by settlement period (offer - bid volumes)
     * Row 23: EWAP £/MWh by settlement period (energy weighted avg price)
     * Row 24: Top BMU £ by settlement period (highest revenue battery)
   - Pads missing periods with empty strings (future periods)

**Key Functions**:
- `get_latest_settlement_period()`: Calculates current SP from system time
- `get_kpis()`: Aggregates KPI values
- `get_gen_mix()`: Latest generation mix with deduplication
- `get_interconnectors()`: Latest IC flows with deduplication
- `get_48_period_timeseries()`: Builds pivot table for sparklines
- `get_48_period_interconnectors()`: IC flows by settlement period

**API Optimization**:
- Uses batch updates (6 API calls instead of 30+)
- Single batch for KPIs
- Single batch for all 10 fuel types
- Single batch for all 10 interconnectors

---

### 2. update_live_dashboard_v2_outages.py

**Purpose**: Updates generator outages section

**Location**: `/home/george/GB-Power-Market-JJ/update_live_dashboard_v2_outages.py`  
**Lines**: 282  
**Runtime**: ~3-5 seconds

**Data Source**: 
- BigQuery: `bmrs_remit_unavailability` (REMIT outage notifications)
- Joined with `bmu_registration_data` for proper asset names

**What it updates**:

**Rows 31+, Columns G-Q**:
- G: Asset Name (from BMU registration or REMIT data)
- H: Fuel Type (with emoji: 🏭 Fossil Gas, ⚛️ Nuclear, etc.)
- I: Unavail (MW) - unavailable capacity
- J: Normal (MW) - normal capacity
- K: Cause (e.g., "Planned Outage", "DC Cable Fault")
- L: Type (📅 Planned / ⚡ Unplanned)
- M: Expected Return (date/time)
- N: Duration (e.g., "5d 12h", "36h")
- O: Operator (participant name)
- P: Area (affected area)
- Q: Zone (bidding zone)

**Query Logic**:
```sql
WITH latest_revisions AS (
    SELECT affectedUnit, MAX(revisionNumber) as max_rev
    FROM bmrs_remit_unavailability
    WHERE eventStatus = 'Active'
      AND eventStartTime <= CURRENT_TIMESTAMP()
      AND (eventEndTime >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
    GROUP BY affectedUnit
)
SELECT ... 
WHERE unavailableCapacity > 50  -- Filter small outages
ORDER BY unavailableCapacity DESC
LIMIT 15
```

**Column Width Optimization**:
- Sets precise pixel widths for each column (200px for Asset Name, 140px for Fuel Type, etc.)

---

### 3. update_intraday_wind_chart.py

**Purpose**: Updates wind forecast chart

**Location**: `/home/george/GB-Power-Market-JJ/update_intraday_wind_chart.py`  
**Lines**: ~180 (updated Dec 14, 2025)
**Runtime**: ~2-3 seconds

**Data Sources**:
- `bmrs_fuelinst_iris` (actual wind generation by SP)
- `bmrs_windfor_iris` (wind forecasts - hourly data)

**What it updates**:

**Rows 40+, Columns A-C**:
- Row 40: Headers ("Settlement Period", "Actual (GW)", "Forecast (GW)")
- Rows 41-88: 48 settlement periods with actual and forecast wind generation

**Key Features**:
- Converts MW to GW
- Expands hourly forecasts to half-hourly settlement periods (duplicates each hourly value to both SPs)
- Uses fallback to latest available forecast date if today's forecast not available
- Applies proper number formatting (prevents currency symbols)
- Deduplicates data by latest publishTime

**Forecast Fallback Logic**:
- Attempts to fetch today's forecast data first
- If unavailable, uses most recent forecast date in table (typically 1-2 days lag)
- Hourly forecast values are replicated to both settlement periods in that hour

---

### 4. update_battery_bm_revenue.py

**Purpose**: Updates battery balancing mechanism revenue section + sparklines

**Location**: `/home/george/GB-Power-Market-JJ/update_battery_bm_revenue.py`  
**Lines**: ~280 (updated Dec 14, 2025)  
**Runtime**: ~20 seconds (3 batteries × 48 SPs × 4 API calls = 576 API requests)

**Data Sources**:
- Elexon BMRS API (NOT BigQuery):
  - BOAV: `https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all`
  - EBOCF: `https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all`

**What it updates**:

**Rows 24-29, Columns K-R**:
- Row 24: Header with date
- Row 25: Summary totals (total revenue, discharge/charge split, active SPs)
- Row 26: Column headers
- Rows 27-29: 3 batteries:
  - `T_LKSDB-1`: Lakeside (50 MW)
  - `E_CONTB-1`: Tesla Hornsea (100 MW)
  - `T_WHLWB-1`: Whitelee (50 MW)

**Columns**:
- K: BMU ID
- L: Name
- M: Net Revenue £ (discharge revenue - charge costs)
- N: Volume MWh (total accepted volume)
- O: £/MWh (average price)
- P: Type (Discharge/Charge/Idle)
- Q: Active SPs (e.g., "46/48")
- R: Status (% share with emoji: 🔥 >50%, ✅ >10%, ⚪ <10%)

**API Query Pattern**:
```python
for battery in BATTERIES:
    for sp in range(1, 49):  # 48 settlement periods
        # Offer acceptances (discharge = battery generating)
        offer_vol = GET /balancing/settlement/acceptance/volumes/all/offer/{date}/{sp}?bmUnit={bmu_id}
        offer_cash = GET /balancing/settlement/indicative/cashflows/all/offer/{date}/{sp}?bmUnit={bmu_id}
        
        # Bid acceptances (charge = battery consuming)
        bid_vol = GET /balancing/settlement/acceptance/volumes/all/bid/{date}/{sp}?bmUnit={bmu_id}
        bid_cash = GET /balancing/settlement/indicative/cashflows/all/bid/{date}/{sp}?bmUnit={bmu_id}
```

**Revenue Calculation**:
```python
net_revenue = total_offer_cash - total_bid_cash  # Positive = net earning
activity_type = 'Discharge' if offer_cash > bid_cash else 'Charge'
avg_price = net_revenue / total_volume if total_volume > 0 else 0
```

**Market Intelligence**:
- 100% discharge = TIGHT market (system short of power, NESO buying from batteries)
- Mixed discharge/charge = Normal balancing
- Dominant charge = System long (NESO paying batteries to consume excess power)

**Settlement Period Sparklines** (NEW - Dec 14, 2025):

The script now also generates 4 sparkline datasets showing battery revenue patterns across all 48 settlement periods:

1. **Total £ by SP** (Data_Hidden row 21):
   - Aggregate revenue across all 3 batteries per settlement period
   - Shows which periods have highest revenue opportunities
   - Orange line sparkline in dashboard

2. **Net MWh by SP** (Data_Hidden row 22):
   - Net energy delivery (offer volume - bid volume) per settlement period
   - Positive = discharge (battery generating), Negative = charge (battery consuming)
   - Blue column sparkline in dashboard

3. **EWAP £/MWh by SP** (Data_Hidden row 23):
   - Energy Weighted Average Price: `Total £ / Total Volume`
   - Shows price efficiency per settlement period
   - Green line sparkline in dashboard

4. **Top BMU £ by SP** (Data_Hidden row 24):
   - Highest revenue battery each settlement period
   - Shows competitive dynamics (which battery winning each period)
   - Red line sparkline in dashboard

**Data Collection Logic**:
```python
# For each settlement period (1-48):
sp_total_revenue = [0] * 48
sp_net_mwh = [0] * 48
sp_total_volume = [0] * 48
sp_bmu_revenue = {bmu_id: [0] * 48 for each battery}

# In API fetch loop:
sp_net_revenue = sp_offer_cash - sp_bid_cash
sp_total_revenue[sp-1] += sp_net_revenue
sp_net_mwh[sp-1] += (sp_offer_vol - sp_bid_vol)
sp_total_volume[sp-1] += (sp_offer_vol + sp_bid_vol)
sp_bmu_revenue[bmu_id][sp-1] = sp_net_revenue

# Derived calculations:
sp_ewap[i] = sp_total_revenue[i] / sp_total_volume[i]
sp_top_bmu[i] = max([sp_bmu_revenue[bmu][i] for all batteries])
```

**Dashboard Placement**:
- Row 30: Header "📊 BM Revenue Trends (by Settlement Period)"
- Rows 31-34: Labels + sparkline formulas (columns S-T)
- Formulas written with `value_input_option='USER_ENTERED'`
- Individual updates (gspread batch doesn't support value_input_option)

**Example Output** (Dec 14, 2025):
- Total Revenue: £72,539 across 48 periods
- Lakeside dominating: £65,324 (90%)
- Peak periods visible in Total £ sparkline
- 100% discharge market (all batteries generating)

**Market Intelligence**:
- 100% discharge = TIGHT market (system short of power, NESO buying from batteries)
- Mixed discharge/charge = Normal balancing
- Dominant charge = System long (NESO paying batteries to consume excess power)

---

## 📜 Apps Script Code (CLASP)

### Location: clasp-gb-live-2/

**Script ID**: `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`

### Files:

#### 1. Code.gs

**Purpose**: Main entry point, menu creation, dashboard update trigger

```javascript
function onOpen() {
  SpreadsheetApp.getUi()
      .createMenu('GB Live Dashboard')
      .addItem('Force Refresh Dashboard', 'updateDashboard')
      .addItem('Setup Live Dashboard v2', 'createV2Dashboard')
      .addItem('Test Connection', 'testConnection')
      .addToUi();
}

function updateDashboard() {
  // Fetches data from BigQuery publication table
  // Calls setupDashboardLayoutV2() for layout
  // Calls displayData() to populate values
  // Calls createCharts() for visualizations
}
```

**Note**: Currently NOT actively used - Python scripts handle all updates. Apps Script provides menu interface and backup manual refresh option.

#### 2. Dashboard.gs

**Purpose**: Dashboard layout setup functions

```javascript
function setupDashboardLayoutV2(sheet) {
  // Sets up the v2 layout with modern styling
  // Creates header with emojis ⚡🇬🇧
  // Formats KPI section
  // Sets up Generation Mix headers
  // Sets up Interconnector headers
}
```

#### 3. Data.gs

**Purpose**: BigQuery data fetching (legacy - not actively used)

```javascript
function fetchData() {
  // Queries publication_dashboard_live table
  // Parses JSON structure
  // Returns data object with:
  //   - KPIs
  //   - Generation Mix
  //   - Interconnectors
  //   - Intraday timeseries
  //   - Outages
  //   - Constraint analysis
}

function addFuelEmoji(fuelType) {
  // Maps fuel types to emojis
  // Returns formatted string like "🌬️ WIND"
}
```

**Note**: The publication table (`publication_dashboard_live`) exists in BigQuery but is NOT updated by the current Python workflow. Python scripts write directly to sheets.

#### 4. Charts.gs

**Purpose**: Chart creation (legacy - sparklines used instead)

```javascript
function createCharts(sheet, data) {
  // Would create embedded charts
  // Currently unused - sparklines are faster and cleaner
}
```

#### 5. setup_btm_calculator.gs

**Purpose**: Behind-the-Meter calculator setup (separate feature)

---

## 🔧 Configuration Files

### config.py

```python
GOOGLE_SHEETS_CONFIG = {
    'MAIN_DASHBOARD_ID': '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
    # Other sheet IDs...
}
```

### Credentials

**Service Account**: `inner-cinema-credentials.json`
- Used by Python scripts for Google Sheets API access
- Scopes: `['https://www.googleapis.com/auth/spreadsheets']`

**BigQuery Authentication**:
- Uses same service account or Application Default Credentials
- Project: `inner-cinema-476211-u9`
- Location: `US`

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     EVERY 5 MINUTES (CRON)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              auto_update_dashboard_v2.sh                    │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
│ update_live_     │  │ update_live_ │  │ update_intraday_ │
│ dashboard_v2.py  │  │ dashboard_v2_│  │ wind_chart.py    │
│                  │  │ outages.py   │  │                  │
└──────────────────┘  └──────────────┘  └──────────────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│              BigQuery (inner-cinema-476211-u9)           │
│  • bmrs_fuelinst_iris    • bmrs_mid_iris                │
│  • bmrs_freq_iris        • bmrs_windfor_iris            │
│  • bmrs_remit_unavailability                            │
│  • bmu_registration_data                                │
└──────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│         Google Sheets API (gspread library)              │
│  • Batch updates (optimized for rate limits)            │
│  • Direct cell writes (values + formulas)               │
└──────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│         Live Dashboard v2 (Google Sheets)                │
│  • KPIs (Row 6)                                         │
│  • Generation Mix (Rows 13-22, Cols A-D)               │
│  • Interconnectors (Rows 13-22, Cols G-J)              │
│  • Battery Revenue (Rows 24-29, Cols K-R)              │
│  • Wind Chart (Rows 40+, Cols A-C)                     │
│  • Outages (Rows 31+, Cols G-Q)                        │
│  • Data_Hidden (Rows 1-20, 48 periods for sparklines)  │
└──────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│           Sparkline Formulas (Auto-refresh)              │
│  • Fuel sparklines: =SPARKLINE(Data_Hidden!A1:AV1)      │
│  • IC sparklines: =SPARKLINE(Data_Hidden!A11:AV11)      │
└──────────────────────────────────────────────────────────┘

                    SEPARATE WORKFLOW:
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│         update_battery_bm_revenue.py                     │
│  • Queries Elexon BMRS API (NOT BigQuery)               │
│  • BOAV endpoint: Acceptance volumes                    │
│  • EBOCF endpoint: Indicative cashflows                 │
│  • 3 batteries × 48 SPs × 4 calls = 576 API requests    │
└──────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│         Elexon BMRS API                                  │
│  https://data.elexon.co.uk/bmrs/api/v1/...              │
└──────────────────────────────────────────────────────────┘
```

---

## 🚨 Common Issues & Fixes

### Issue 1: Sparklines Not Showing

**Symptom**: Column H or D shows blank/empty instead of sparklines

**Cause**: 
- Formulas reference wrong data source
- Data_Hidden sheet missing/empty
- Columns not merged for interconnectors

**Fix**:
```python
# Re-run sparkline setup
python3 <<'EOF'
import gspread
from google.oauth2.service_account import Credentials

gc = gspread.authorize(Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets']))
ws = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA').worksheet('Live Dashboard v2')

# Fuel sparklines
fuel_formulas = []
for row in range(13, 23):
    formula = f'=SPARKLINE(Data_Hidden!A{row-12}:AV{row-12}, {{"charttype","line";"color1","#3498db"}})'
    fuel_formulas.append([formula])
ws.update(values=fuel_formulas, range_name='D13:D22', value_input_option='USER_ENTERED')

# IC sparklines
ic_formulas = []
for row in range(13, 23):
    formula = f'=SPARKLINE(Data_Hidden!A{row-2}:AV{row-2}, {{"charttype","bar";"max",2000;"color1","#2ecc71"}})'
    ic_formulas.append([formula])
ws.update(values=ic_formulas, range_name='H13:H22', value_input_option='USER_ENTERED')
EOF
```

### Issue 2: Data Overlapping

**Symptom**: Battery data mixing with outages, wind chart, etc.

**Cause**: Wrong row/column ranges in Python scripts

**Fix**: Check placement in each script:
- `update_live_dashboard_v2.py`: Gen Mix B13:C22, ICs J13:J22
- `update_live_dashboard_v2_outages.py`: G40:Q60
- `update_intraday_wind_chart.py`: A40:C88
- `update_battery_bm_revenue.py`: K24:R29

### Issue 3: Cron Not Running

**Symptom**: Dashboard not updating automatically

**Check**:
```bash
# Verify cron job exists
crontab -l | grep dashboard

# Check logs
tail -50 ~/dashboard_v2_updates.log

# Manual test
bash /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh
```

### Issue 4: BigQuery Errors

**Symptom**: "Table not found", "Access denied"

**Fix**:
- Always use project: `inner-cinema-476211-u9` (NOT jibber-jabber-knowledge)
- Location: `US` (NOT europe-west2)
- Check service account has BigQuery permissions

### Issue 5: Battery Data Shows £0

**Symptom**: Battery revenue shows all zeros

**Cause**: 
- Data for current day not yet settled (24-48h lag)
- API returning empty responses

**Fix**:
```bash
# Test with historical date
python3 update_battery_bm_revenue.py 2025-12-10

# Check API directly
curl "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/offer/2025-12-10/20?bmUnit=T_LKSDB-1"
```

---

## 📝 Maintenance Tasks

### Daily
- Monitor logs: `tail -f ~/dashboard_v2_updates.log`
- Check dashboard visually for data freshness

### Weekly
- Review battery revenue trends
- Check for new outages/patterns
- Verify interconnector flows

### Monthly
- Clean old logs: `truncate -s 0 ~/dashboard_v2_updates.log`
- Review cron job performance
- Update battery BMU list if new units added

### As Needed
- Add new fuel types to Generation Mix mapping
- Add new interconnectors to IC mapping
- Adjust sparkline color schemes
- Update row heights/column widths

---

## 🔗 Related Documentation

- **Project Configuration**: `PROJECT_CONFIGURATION.md`
- **Data Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **IRIS Pipeline**: `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`
- **BigQuery Setup**: `BIGQUERY_IMPLEMENTATION_GUIDE.md`
- **Full Docs Index**: `DOCUMENTATION_INDEX.md`

---

## 📞 Support

**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Status**: ✅ Production (December 2025)

---

**Last Updated**: December 14, 2025
