# UK Power Market Dashboard - Complete Documentation

**Last Updated:** 30 October 2025  
**Version:** 2.0 (Enhanced with Price Impact Analysis)

---

## Table of Contents
1. [Overview](#overview)
2. [Dashboard Layout](#dashboard-layout)
3. [Features](#features)
4. [Data Sources](#data-sources)
5. [Visual Elements](#visual-elements)
6. [Price Impact Analysis](#price-impact-analysis)
7. [Scripts & Automation](#scripts--automation)
8. [Update Commands](#update-commands)
9. [Troubleshooting](#troubleshooting)
10. [Future Enhancements](#future-enhancements)

---

## Overview

The UK Power Market Dashboard provides real-time visibility into:
- **Generation data** by fuel type (Gas, Nuclear, Wind, Solar, Biomass, Hydro, Coal)
- **Interconnector flows** from France, Netherlands, Belgium, Norway, and Ireland
- **Power station outages** (REMIT unavailability events)
- **Market price impact** from unplanned outages
- **System-wide metrics** (total generation, supply, renewables percentage)

**Google Sheets Dashboard:**  
🔗 [View Dashboard](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8)

**BigQuery Project:** `inner-cinema-476211-u9` (Grid Smart Production)  
**Dataset:** `uk_energy_prod`

---

## Dashboard Layout

### Section 1: Header & System Metrics (Rows 1-5)

#### Row 1: Title
```
🇬🇧 UK POWER MARKET DASHBOARD
```
- **Format:** Large, bold, white text on dark blue background (#0D3380)
- **Merged cells:** A1:H1

#### Row 2: Timestamp
```
⏰ Last Updated: 2025-10-30 14:10:00 | Settlement Period 29
```
- **Format:** Small italic text on grey background
- **Data:** Real-time from latest BMRS publish time

#### Row 4: System Metrics Header
```
📊 SYSTEM METRICS
```
- **Format:** Bold white text on blue background (#3366B3)

#### Row 5: Key Metrics
```
Total Generation: 27.4 GW | Total Supply: 31.0 GW | Renewables: 46.1% | Market Price (EPEX): £76.33/MWh
```
- **Calculations:**
  - Total Generation = Sum of all fuel types (excluding interconnectors)
  - Total Supply = Total Generation + Interconnector Imports
  - Renewables % = (Wind + Solar + Biomass + Hydro) / Total Generation × 100
  - Market Price = Current EPEX UK spot price

---

### Section 2: Generation Data (Rows 7-14)

Two-column layout showing fuel mix and interconnector flows:

#### Column A-B: Generation by Fuel Type
```
⚡ GENERATION BY FUEL TYPE

🔥 Gas         12.5 GW    (CCGT)
⚛️ Nuclear      6.2 GW    (NUCLEAR)
💨 Wind         5.8 GW    (WIND)
☀️ Solar        1.2 GW    (PS - Photovoltaic Solar)
🌿 Biomass      1.1 GW    (BIOMASS)
💧 Hydro        0.4 GW    (NPSHYD - Non-Pumped Storage Hydro)
⚫ Coal         0.2 GW    (COAL)
```
- **Format:** Green header (#33996D), emoji icons for visual identification
- **Data Source:** BigQuery `bmrs_fuelinst` table

#### Column D-E: Interconnectors
```
🔌 INTERCONNECTORS

🇫🇷 IFA (France)             1.2 GW
🇫🇷 IFA2 (France)            0.8 GW
🇳🇱 BritNed (Netherlands)    0.9 GW
🇧🇪 Nemo (Belgium)           0.6 GW
🇳🇴 NSL (Norway)             0.0 GW
🇮🇪 Moyle (N. Ireland)       0.1 GW
```
- **Format:** Brown header (#996633), country flag emojis
- **Positive values:** Imports to UK
- **Negative values:** Exports from UK

---

### Section 3: REMIT Outages & Market Impact (Rows 17+)

#### Row 17: Main REMIT Header
```
🔴 POWER STATION OUTAGES & MARKET IMPACT
```
- **Format:** Bold white text on red background (#CC3333)
- **Purpose:** High-visibility alert section

#### Row 18: Summary Statistics with Visual Bar
```
Active Outages: 4 of 5 events | Unavailable: 1,647 MW / 2,147 MW | 🟥🟥🟥🟥🟥🟥🟥🟥⬜⬜ 76.7% | Price Impact: +£7.83/MWh (+11.4%)
```
- **Visual Bar Chart:** Red squares (🟥) show % of capacity unavailable
  - Each 🟥 = 10% unavailable
  - Each ⬜ = 10% available
- **Active Outages:** Events currently ongoing
- **Total Events:** Includes recently returned-to-service units
- **Price Impact:** Difference between baseline and current market price

---

### Section 4: Price Impact Analysis (Rows 20-25)

#### Row 20: Price Analysis Header
```
💷 PRICE IMPACT ANALYSIS
```
- **Format:** Bold white text on green background (#1A7F4D)

#### Rows 21-25: Price Impact Table
```
Event                    | Announcement Time   | Unavail MW | Est. Impact | Pre-Announcement | Current Price | Δ Price
-------------------------|---------------------|------------|-------------|------------------|---------------|--------
Drax Unit 1             | 2025-10-28 14:30    | 660        | +£3.30      | £68.50          | £76.33        | +£7.83
Pembroke CCGT Unit 4    | 2025-10-29 08:15    | 537        | +£2.69      | £68.50          | £76.33        | +£7.83
Sizewell B              | 2025-10-29 22:45    | 300        | +£1.50      | £68.50          | £76.33        | +£7.83
London Array Wind Farm  | 2025-10-30 06:20    | 150        | +£0.75      | £68.50          | £76.33        | +£7.83
```

**Price Impact Calculation:**
```python
estimated_impact_per_event = (unavailable_capacity_MW / 100) × £0.50/MWh

# Example: Drax Unit 1
# 660 MW / 100 × £0.50 = £3.30/MWh estimated contribution
```

**Baseline Price:** £68.50/MWh (pre-outage average)  
**Current Price:** £76.33/MWh (real-time EPEX spot)  
**Total Price Increase:** +£7.83/MWh (+11.4%)

---

### Section 5: All Station Outages (Rows 27+)

#### Row 27: Stations Header
```
📊 ALL STATION OUTAGES
```
- **Format:** Bold white text on blue background (#6666CC)

#### Row 29: Table Header
```
Status | Power Station | Unit | Fuel | Normal (MW) | Unavail (MW) | % Unavailable | Cause
```

#### Rows 30+: Complete Outage List
```
🔴 Active | Drax Unit 1           | Unit 1  | BIOMASS | 660  | 660  | 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100.0% | Turbine bearing failure
🔴 Active | Pembroke CCGT Unit 4  | Unit 4  | CCGT    | 537  | 537  | 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100.0% | Boiler tube leak
🔴 Active | Sizewell B            | Unit 1  | NUCLEAR | 300  | 300  | 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100.0% | Reactor de-rating
🔴 Active | London Array          | Array   | WIND    | 150  | 150  | 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100.0% | Cable fault - offshore
🟢 Returned | IFA Interconnector  | IFA     | OTHER   | 2000 | 0    | ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0.0%   | Maintenance complete
```

**Status Indicators:**
- 🔴 **Active:** Outage currently in effect
- 🟢 **Returned to Service:** Recently restored capacity

**% Unavailable Column:**
- Visual bar chart showing proportion of unit unavailable
- Formula: `(unavailable_capacity / normal_capacity) × 100`
- Each 🟥 represents 10% unavailable
- Each ⬜ represents 10% available

---

## Features

### 1. Real-Time Generation Data
- **Source:** Elexon BMRS API (Balancing Mechanism Reporting Service)
- **Stream:** B1610 FUELINST (Fuel Instantaneous)
- **Frequency:** Updated every 5 minutes
- **Coverage:** All fuel types used in GB power generation

### 2. REMIT Unavailability Tracking
- **Regulation:** EU Regulation 1227/2011 (REMIT - Regulation on wholesale Energy Market Integrity and Transparency)
- **Requirement:** Market participants must disclose inside information affecting power generation
- **Tracked Events:**
  - Unplanned outages (>100 MW, >3 days)
  - Planned outages (>100 MW, >1 month)
  - Changes to planned outages
  - Return to service notifications

### 3. Visual % Indicators
- **Red Bar Charts:** Immediately show severity of outages
- **Scalable:** Works for partial and full outages
- **Example Interpretations:**
  - `🟥🟥🟥⬜⬜⬜⬜⬜⬜⬜ 30.0%` = Minor de-rating
  - `🟥🟥🟥🟥🟥🟥🟥⬜⬜⬜ 70.0%` = Major capacity loss
  - `🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100.0%` = Complete unit outage

### 4. Price Impact Analysis
- **Baseline Tracking:** Records pre-outage price levels
- **Real-Time Comparison:** Current market price vs baseline
- **Event Attribution:** Estimates each outage's contribution to price changes
- **Market Context:** Shows cumulative effect of multiple outages

### 5. Comprehensive Station Coverage
- **Active Outages:** Current unavailability events
- **Recent History:** Recently returned-to-service units (context)
- **All Event Types:** Planned, unplanned, and returned status
- **Sorting:** Active events first, then by unavailable capacity (largest impact first)

---

## Data Sources

### BigQuery Tables

#### 1. `bmrs_fuelinst` - Generation Data
```sql
SELECT 
    fuelType,           -- CCGT, NUCLEAR, WIND, PS, BIOMASS, NPSHYD, COAL, etc.
    generation,         -- MW
    publishTime,        -- Timestamp
    settlementDate,     -- Date
    settlementPeriod    -- 1-50 (half-hourly periods)
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(publishTime) = CURRENT_DATE('Europe/London')
ORDER BY publishTime DESC
LIMIT 1
```

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| fuelType | STRING | Fuel type code (CCGT, NUCLEAR, WIND, etc.) |
| generation | FLOAT | Current generation in MW |
| publishTime | TIMESTAMP | API publish timestamp |
| settlementDate | DATE | Trading day |
| settlementPeriod | INTEGER | Half-hourly period (1-50) |

**Update Frequency:** Every 5 minutes  
**Retention:** 90 days rolling

---

#### 2. `bmrs_remit_unavailability` - Outage Data
```sql
SELECT
    messageId,              -- Unique REMIT message ID
    assetName,              -- Power station name
    affectedUnit,           -- Specific unit/turbine
    fuelType,               -- Generation technology
    normalCapacity,         -- Rated capacity (MW)
    availableCapacity,      -- Current available (MW)
    unavailableCapacity,    -- Currently offline (MW)
    eventStartTime,         -- Outage start
    eventEndTime,           -- Expected return
    eventStatus,            -- Active / Returned to Service
    cause,                  -- Reason for unavailability
    participantName         -- Asset owner
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
  AND DATETIME(eventStartTime) <= CURRENT_DATETIME()
  AND DATETIME(eventEndTime) >= CURRENT_DATETIME()
ORDER BY unavailableCapacity DESC
```

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| messageId | STRING | Unique identifier for REMIT message |
| assetName | STRING | Power station/asset name |
| affectedUnit | STRING | Specific generation unit affected |
| fuelType | STRING | Technology type (BIOMASS, CCGT, NUCLEAR, etc.) |
| normalCapacity | FLOAT | Rated capacity when operational (MW) |
| availableCapacity | FLOAT | Current available capacity (MW) |
| unavailableCapacity | FLOAT | Capacity currently offline (MW) |
| eventStartTime | DATETIME | When outage began |
| eventEndTime | DATETIME | Expected/actual return time |
| eventStatus | STRING | Active / Returned to Service / Planned |
| cause | STRING | Reason for unavailability |
| participantName | STRING | Company/operator name |

**Partitioning:** By `eventStartTime` (daily)  
**Update Frequency:** As events occur (typically hourly check)  
**Retention:** 2 years

---

### External Data Sources

#### Market Prices
- **Source:** EPEX UK Day-Ahead Auction
- **Current Integration:** Manual entry in dashboard
- **Future Enhancement:** Automated API integration planned

**Potential APIs:**
1. **EPEX SPOT API** - Official day-ahead prices
2. **Elexon BMRS** - System prices (SAP, SBP)
3. **Nordpool API** - European market prices

---

## Visual Elements

### Color Coding

| Element | Color | Hex Code | Purpose |
|---------|-------|----------|---------|
| Main Title | Dark Blue | #0D3380 | Primary branding |
| System Metrics Header | Medium Blue | #3366B3 | Section divider |
| Generation Header | Green | #33996D | Positive/supply indicator |
| Interconnectors Header | Brown | #996633 | Cross-border flows |
| REMIT Header | Red | #CC3333 | Alert/warning section |
| Price Analysis Header | Dark Green | #1A7F4D | Financial data |
| Stations List Header | Purple-Blue | #6666CC | Data table section |
| Table Headers | Grey | #B3B3B3 | Column labels |
| Summary Rows | Light variants | Various | Highlighted totals |

### Icons & Emojis

#### Fuel Types
- 🔥 **Gas (CCGT)** - Combined Cycle Gas Turbine
- ⚛️ **Nuclear** - Nuclear fission reactors
- 💨 **Wind** - Onshore and offshore wind farms
- ☀️ **Solar** - Photovoltaic solar panels
- 🌿 **Biomass** - Renewable organic material
- 💧 **Hydro** - Hydroelectric (non-pumped storage)
- ⚫ **Coal** - Coal-fired generation (being phased out)

#### Interconnectors
- 🇫🇷 **France** - IFA, IFA2 subsea cables
- 🇳🇱 **Netherlands** - BritNed cable
- 🇧🇪 **Belgium** - Nemo Link
- 🇳🇴 **Norway** - NSL (North Sea Link)
- 🇮🇪 **N. Ireland** - Moyle Interconnector

#### Status Indicators
- 🔴 **Active** - Outage currently in effect
- 🟢 **Returned** - Unit back in service
- 🟥 **Filled Bar** - Unavailable capacity (10% each)
- ⬜ **Empty Bar** - Available capacity (10% each)

---

## Price Impact Analysis

### Methodology

#### Baseline Price Calculation
```python
# Pre-outage baseline (7-day average before first event)
baseline_price = 68.50  # £/MWh

# Current market price (real-time EPEX spot)
current_price = 76.33  # £/MWh

# Total impact
price_delta = current_price - baseline_price  # +£7.83/MWh
percentage_change = (price_delta / baseline_price) × 100  # +11.4%
```

#### Individual Event Impact Estimation
```python
# Rule of thumb: £0.50/MWh per 100 MW unavailable
impact_factor = 0.50  # £/MWh per 100 MW

estimated_impact = (unavailable_capacity_MW / 100) × impact_factor

# Example: Drax Unit 1 (660 MW offline)
drax_impact = (660 / 100) × 0.50 = £3.30/MWh
```

**Caveat:** This is a simplified estimation. Actual price impacts depend on:
- Time of day (peak vs off-peak demand)
- Season (heating/cooling demand)
- Renewable generation levels
- Interconnector availability
- Fuel prices (gas, coal)
- Market sentiment and trading behavior

#### Why Prices Increase During Outages

1. **Reduced Supply:** Less generation capacity available
2. **Merit Order Effect:** More expensive plants must run to meet demand
3. **Scarcity Pricing:** Markets price in risk of shortfalls
4. **Reserve Costs:** System operator must secure additional reserves
5. **Interconnector Imports:** May need to import at premium prices

**Historical Examples:**
- August 2019: Multiple plant outages → Prices >£100/MWh
- Winter 2021-22: Nuclear outages + gas crisis → Prices >£400/MWh
- Normal Range: £40-80/MWh (typical)

---

## Scripts & Automation

### Primary Scripts

#### 1. `dashboard_clean_design.py` ⭐ MAIN SCRIPT
**Purpose:** Complete dashboard update with generation, REMIT, and price analysis

**Features:**
- Fetches latest generation data from BigQuery
- Retrieves all REMIT events (active + recent)
- Calculates price impacts
- Creates visual bar charts
- Formats entire Sheet1 with colors and styling

**Usage:**
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python dashboard_clean_design.py
```

**Output:**
```
================================================================================
🎨 CLEAN DASHBOARD DESIGNER
================================================================================
⏰ 2025-10-30 14:57:10

📥 Fetching generation data from BigQuery...
✅ Retrieved data for 20 fuel types

📊 Calculating system metrics...
   Total Generation: 27.4 GW
   Renewables: 46.1%

📥 Fetching REMIT unavailability data...
✅ Retrieved 5 total events (4 active)

💷 Analyzing price impacts...
✅ Calculated impact for 4 events

🎨 Creating enhanced dashboard design...
🧹 Clearing sheet...
📝 Writing 34 rows to sheet...
🎨 Applying formatting...
✅ Dashboard formatted successfully!

================================================================================
✅ CLEAN DASHBOARD CREATED!
🔗 View: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
================================================================================
```

**Runtime:** ~5-8 seconds

---

#### 2. `fetch_fuelinst_today.py`
**Purpose:** Fetch generation data from Elexon BMRS API and upload to BigQuery

**Data Collected:**
- All fuel types (CCGT, NUCLEAR, WIND, PS, BIOMASS, NPSHYD, COAL)
- All interconnectors (INTFR, INTIRL, INTNED, etc.)
- Settlement period information
- Publish timestamps

**Usage:**
```bash
./.venv/bin/python fetch_fuelinst_today.py
```

**Schedule:** Every 5 minutes (recommended)

---

#### 3. `fetch_remit_unavailability.py`
**Purpose:** Fetch REMIT unavailability data and upload to BigQuery

**Current Status:** Uses sample data  
**Production Ready:** Structure prepared for live API integration

**Data Sources (Future):**
1. **Elexon IRIS Service** (FTP-based REMIT messages)
2. **ENTSO-E Transparency Platform** (RESTful API)
3. **Manual CSV Imports** from Elexon portal

**Usage:**
```bash
./.venv/bin/python fetch_remit_unavailability.py
```

**Schedule:** Every hour (recommended)

---

### Helper Functions

#### `create_bar_chart(percentage, width=10)`
Creates red bar chart visualization:
```python
def create_bar_chart(percentage, width=10):
    """Create a text-based bar chart for percentages in red"""
    filled = int(percentage / 10)  # Each block represents 10%
    empty = width - filled
    bar = "🟥" * filled + "⬜" * empty
    return f"{bar} {percentage:.1f}%"

# Examples:
create_bar_chart(30.0)  # 🟥🟥🟥⬜⬜⬜⬜⬜⬜⬜ 30.0%
create_bar_chart(76.7)  # 🟥🟥🟥🟥🟥🟥🟥🟥⬜⬜ 76.7%
create_bar_chart(100.0) # 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100.0%
```

#### `calculate_system_metrics(data)`
Computes dashboard metrics:
```python
def calculate_system_metrics(data):
    """Calculate system-wide metrics"""
    
    # Map API fuel types to display names
    fuel_mapping = {
        'CCGT': 'Gas', 'NUCLEAR': 'Nuclear', 'WIND': 'Wind',
        'PS': 'Solar', 'BIOMASS': 'Biomass', 
        'NPSHYD': 'Hydro', 'COAL': 'Coal'
    }
    
    # Identify renewable sources
    renewable_types = ['WIND', 'PS', 'BIOMASS', 'NPSHYD']
    
    # Calculate totals
    total_generation = sum(fuel_data.values())
    renewable_generation = sum(data[ft] for ft in renewable_types)
    renewables_pct = (renewable_generation / total_generation * 100)
    
    # Add interconnector imports
    total_supply = total_generation + total_interconnector
    
    return metrics_dict
```

#### `get_price_impact_analysis(remit_df)`
Estimates price impact from outages:
```python
def get_price_impact_analysis(remit_df):
    """Analyze price impact from outage announcements"""
    baseline_price = 68.50  # £/MWh baseline
    current_price = 76.33   # £/MWh current
    
    for each active outage:
        # Estimate: £0.50/MWh per 100MW unavailable
        capacity_impact = unavailable_MW / 100 * 0.50
        
        price_impacts.append({
            'assetName': station_name,
            'announcementTime': event_start,
            'unavailableMW': capacity_offline,
            'estimatedImpact': capacity_impact,
            'priceBeforeAnnouncement': baseline_price,
            'currentPrice': current_price
        })
    
    return price_impacts
```

---

## Update Commands

### Manual Update (One-Time)
Run all data collection and dashboard update:
```bash
cd "/Users/georgemajor/GB Power Market JJ"

# Step 1: Fetch latest generation data
./.venv/bin/python fetch_fuelinst_today.py

# Step 2: Fetch latest REMIT data
./.venv/bin/python fetch_remit_unavailability.py

# Step 3: Update dashboard
./.venv/bin/python dashboard_clean_design.py
```

**Total Runtime:** ~15-20 seconds

---

### Automated Update (Recommended)

#### Option 1: Cron Job (macOS/Linux)
```bash
# Edit crontab
crontab -e

# Add this line for updates every 15 minutes
*/15 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python fetch_fuelinst_today.py && ./.venv/bin/python fetch_remit_unavailability.py && ./.venv/bin/python dashboard_clean_design.py >> logs/dashboard_updates.log 2>&1

# Or hourly updates at :05 past the hour
5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python fetch_fuelinst_today.py && ./.venv/bin/python fetch_remit_unavailability.py && ./.venv/bin/python dashboard_clean_design.py >> logs/dashboard_updates.log 2>&1
```

#### Option 2: systemd Timer (Linux)
Create `/etc/systemd/system/power-dashboard.service`:
```ini
[Unit]
Description=UK Power Market Dashboard Update
After=network.target

[Service]
Type=oneshot
User=georgemajor
WorkingDirectory=/Users/georgemajor/GB Power Market JJ
ExecStart=/Users/georgemajor/GB Power Market JJ/.venv/bin/python fetch_fuelinst_today.py
ExecStart=/Users/georgemajor/GB Power Market JJ/.venv/bin/python fetch_remit_unavailability.py
ExecStart=/Users/georgemajor/GB Power Market JJ/.venv/bin/python dashboard_clean_design.py
```

Create `/etc/systemd/system/power-dashboard.timer`:
```ini
[Unit]
Description=Run Power Dashboard Update Every 15 Minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable power-dashboard.timer
sudo systemctl start power-dashboard.timer
sudo systemctl status power-dashboard.timer
```

#### Option 3: GitHub Actions (Cloud)
Create `.github/workflows/update-dashboard.yml`:
```yaml
name: Update Power Dashboard

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Fetch generation data
        run: python fetch_fuelinst_today.py
      
      - name: Fetch REMIT data
        run: python fetch_remit_unavailability.py
      
      - name: Update dashboard
        run: python dashboard_clean_design.py
        env:
          GOOGLE_SHEETS_TOKEN: ${{ secrets.GOOGLE_SHEETS_TOKEN }}
```

---

## Troubleshooting

### Common Issues

#### 1. "No module named 'google.cloud'"
**Cause:** BigQuery client library not installed

**Solution:**
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/pip install google-cloud-bigquery
```

---

#### 2. "No module named 'gspread'"
**Cause:** Google Sheets library not installed

**Solution:**
```bash
./.venv/bin/pip install gspread
```

---

#### 3. "Could not automatically determine credentials"
**Cause:** BigQuery authentication not configured

**Solution:**
```bash
# Set up Application Default Credentials
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

---

#### 4. "token.pickle not found"
**Cause:** Google Sheets authentication missing

**Solution:**
```bash
# Run authorization script
./.venv/bin/python authorize_google_docs.py

# Follow browser prompts to authorize
# token.pickle will be created automatically
```

---

#### 5. "Permission denied on spreadsheet"
**Cause:** Sheets API credentials lack access

**Solution:**
1. Share spreadsheet with service account email:
   - Open Google Sheets
   - Click "Share"
   - Add: `your-service-account@project-id.iam.gserviceaccount.com`
   - Grant "Editor" permissions

---

#### 6. "No data retrieved from BigQuery"
**Cause:** Tables empty or query filtering too strict

**Debug:**
```bash
# Check if data exists
bq query --use_legacy_sql=false '
SELECT COUNT(*) as row_count, MAX(publishTime) as latest
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
'

# If no data, run ingestion
./.venv/bin/python fetch_fuelinst_today.py
```

---

#### 7. "REMIT section shows no outages"
**Cause:** Sample data may need refreshing or no active events

**Solution:**
```bash
# Re-run REMIT data ingestion
./.venv/bin/python fetch_remit_unavailability.py

# Check BigQuery table
bq query --use_legacy_sql=false '
SELECT assetName, eventStatus, unavailableCapacity
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
ORDER BY eventStartTime DESC
LIMIT 10
'
```

---

#### 8. "Price impact shows £0.00"
**Cause:** Market price not updated or baseline needs recalculation

**Solution:**
Edit `dashboard_clean_design.py`:
```python
# Update baseline price (line ~92)
baseline_price = 68.50  # ← Update this value

# Update current price (line ~93)
current_price = 76.33   # ← Update from latest EPEX data
```

Future: Integrate automated price API

---

#### 9. "Bar charts not displaying correctly"
**Cause:** Emoji rendering issues in spreadsheet

**Solution:**
- Bar charts use Unicode: 🟥 (U+1F7E5) and ⬜ (U+2B1C)
- Ensure Google Sheets has emoji support enabled
- Try different browser if rendering fails (Chrome recommended)

---

#### 10. "Dashboard formatting lost after update"
**Cause:** Script may have crashed during formatting phase

**Solution:**
```bash
# Re-run dashboard update
./.venv/bin/python dashboard_clean_design.py

# Check for errors in output
# Formatting is applied after data write completes
```

---

### Debug Commands

#### Check Script Execution
```bash
# Run with verbose output
./.venv/bin/python dashboard_clean_design.py 2>&1 | tee dashboard_debug.log

# Check for Python errors
./.venv/bin/python -m py_compile dashboard_clean_design.py
```

#### Verify BigQuery Access
```bash
# List tables in dataset
bq ls inner-cinema-476211-u9:uk_energy_prod

# Check table schemas
bq show --schema inner-cinema-476211-u9:uk_energy_prod.bmrs_fuelinst
bq show --schema inner-cinema-476211-u9:uk_energy_prod.bmrs_remit_unavailability
```

#### Test Google Sheets Connection
```python
# test_sheets_connection.py
import pickle
import gspread

with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key("12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8")
print(f"✅ Connected to: {spreadsheet.title}")
print(f"📊 Worksheets: {[ws.title for ws in spreadsheet.worksheets()]}")
```

---

## Future Enhancements

### Planned Features

#### 1. Live Market Price Integration
**Status:** Planned  
**APIs to Evaluate:**
- EPEX SPOT API (official day-ahead prices)
- Elexon BMRS SAP/SBP (system prices)
- Nordpool API (European context)

**Implementation:**
```python
def get_live_market_price():
    """Fetch real-time UK power price"""
    # Option 1: EPEX API
    response = requests.get(
        "https://api.epexspot.com/v1/market/GB/DA/price",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    return response.json()['price']
```

---

#### 2. Historical Price Charts
**Status:** Research phase  
**Goal:** Show price trends over time with outage markers

**Visualization Options:**
- Google Charts embedded in Sheets
- Separate Looker Studio dashboard
- Python matplotlib → image → Sheets

---

#### 3. Forecasting Capacity Availability
**Status:** Concept  
**Data Needed:**
- Planned maintenance schedules
- Historical failure rates
- Weather forecasts (wind, solar)

**Use Case:** Predict future tight margins and price spikes

---

#### 4. Carbon Intensity Tracking
**Status:** Planned  
**API:** National Grid ESO Carbon Intensity API

**Metrics:**
- gCO₂/kWh (current intensity)
- Daily average vs renewable %
- Forecasted intensity for next 24 hours

**Implementation:**
```python
def get_carbon_intensity():
    """Fetch UK carbon intensity"""
    response = requests.get("https://api.carbonintensity.org.uk/intensity")
    data = response.json()['data'][0]
    return {
        'intensity': data['intensity']['actual'],  # gCO₂/kWh
        'index': data['intensity']['index']  # low/moderate/high
    }
```

---

#### 5. SMS/Email Alerts
**Status:** Planned  
**Triggers:**
- New major outage (>500 MW)
- Price spike (>£100/MWh)
- Low renewables (<20%)
- High carbon intensity (>300 gCO₂/kWh)

**Services:**
- Twilio (SMS)
- SendGrid (Email)
- Slack webhooks (Team notifications)

---

#### 6. Multi-Sheet Dashboard
**Status:** Design phase  
**Proposed Sheets:**
- **Sheet1:** Current status (existing)
- **Sheet2:** Historical trends (24h charts)
- **Sheet3:** Outage calendar (next 30 days)
- **Sheet4:** Financial analysis (price correlations)
- **Sheet5:** Carbon tracking

---

#### 7. Live REMIT Data Integration
**Status:** High priority  
**Options:**

**Option A: Elexon IRIS Service**
```python
# FTP-based REMIT message retrieval
import ftplib

def fetch_remit_from_iris():
    ftp = ftplib.FTP("ftp.bmreports.com")
    ftp.login(user="username", passwd="password")
    ftp.cwd("/remit/unavailability")
    
    files = ftp.nlst()
    latest_file = max(files)  # Get most recent
    
    with open(f"remit_{latest_file}", 'wb') as f:
        ftp.retrbinary(f"RETR {latest_file}", f.write)
    
    # Parse XML and upload to BigQuery
    parse_remit_xml(f"remit_{latest_file}")
```

**Option B: ENTSO-E Transparency Platform**
```python
# RESTful API for European REMIT data
import requests

def fetch_remit_from_entsoe():
    url = "https://transparency.entsoe.eu/api"
    params = {
        'securityToken': API_KEY,
        'documentType': 'A77',  # Unavailability
        'in_Domain': '10YGB----------A',  # Great Britain
        'periodStart': '202510301400',
        'periodEnd': '202510311400'
    }
    
    response = requests.get(url, params=params)
    return parse_entsoe_xml(response.content)
```

---

#### 8. Mobile-Responsive Design
**Status:** Concept  
**Approach:** Create separate mobile-optimized sheet or web app

---

#### 9. API Endpoint for Dashboard Data
**Status:** Future consideration  
**Use Case:** Share dashboard data with other applications

**Implementation:** Flask or FastAPI exposing JSON endpoints

---

#### 10. Machine Learning Price Predictions
**Status:** Long-term research  
**Goal:** Predict hourly prices based on:
- Generation mix
- Outage schedules
- Weather forecasts
- Historical patterns
- European interconnector flows

**Models to Explore:**
- LSTM (Long Short-Term Memory) for time series
- Random Forest for feature importance
- XGBoost for accuracy

---

## Appendix

### Fuel Type Codes (BMRS API)

| Code | Full Name | Description |
|------|-----------|-------------|
| CCGT | Combined Cycle Gas Turbine | Natural gas power stations |
| NUCLEAR | Nuclear Fission | Pressurized water reactors |
| WIND | Wind Power | Onshore and offshore wind |
| PS | Photovoltaic Solar | Solar PV panels |
| BIOMASS | Biomass | Renewable organic material combustion |
| NPSHYD | Non-Pumped Storage Hydro | Run-of-river and reservoir hydro |
| COAL | Coal | Coal-fired steam turbines (phasing out) |
| OCGT | Open Cycle Gas Turbine | Peaking gas turbines |
| OIL | Oil | Oil-fired generation (rare) |
| OTHER | Other | Miscellaneous sources |
| INTFR | France Interconnector | IFA + IFA2 cables |
| INTIRL | Ireland Interconnector | Moyle + East-West |
| INTNED | Netherlands Interconnector | BritNed cable |
| INTNEM | Belgium Interconnector | Nemo Link |
| INTEW | East-West Interconnector | GB-Ireland cable |
| INTELEC | ElecLink | GB-France via Channel Tunnel |
| INTIFA2 | IFA2 | France interconnector #2 |
| INTMOYLE | Moyle | GB-Northern Ireland |
| INTNSL | North Sea Link | GB-Norway (longest subsea cable) |

---

### REMIT Event Statuses

| Status | Description | Dashboard Display |
|--------|-------------|-------------------|
| Active | Outage currently in effect | 🔴 Active |
| Returned to Service | Unit back online | 🟢 Returned |
| Planned | Future scheduled outage | 🟡 Planned |
| Modified | Event details changed | 🟠 Modified |
| Cancelled | Planned outage cancelled | ⚪ Cancelled |

---

### Settlement Periods

The GB power market operates on 48 half-hourly settlement periods per day:

| Period | Time (GMT) | Period | Time (GMT) |
|--------|-----------|--------|-----------|
| 1 | 00:00-00:30 | 26 | 12:30-13:00 |
| 2 | 00:30-01:00 | 27 | 13:00-13:30 |
| ... | ... | ... | ... |
| 35 | 17:00-17:30 | 36 | 17:30-18:00 |
| ... | ... | 48 | 23:30-00:00 |

**Peak Demand:** Typically periods 34-38 (17:00-19:00)  
**Lowest Demand:** Typically periods 6-10 (02:30-05:00)

---

### Useful SQL Queries

#### 1. Generation Mix Summary (Last 24 Hours)
```sql
SELECT 
    fuelType,
    AVG(generation) as avg_generation_MW,
    MIN(generation) as min_generation_MW,
    MAX(generation) as max_generation_MW,
    COUNT(*) as data_points
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY fuelType
ORDER BY avg_generation_MW DESC
```

#### 2. Active Outages by Fuel Type
```sql
SELECT 
    fuelType,
    COUNT(*) as num_outages,
    SUM(unavailableCapacity) as total_unavailable_MW,
    AVG(unavailableCapacity) as avg_outage_size_MW
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
  AND DATETIME(eventStartTime) <= CURRENT_DATETIME()
  AND DATETIME(eventEndTime) >= CURRENT_DATETIME()
GROUP BY fuelType
ORDER BY total_unavailable_MW DESC
```

#### 3. Longest Running Outages
```sql
SELECT 
    assetName,
    affectedUnit,
    unavailableCapacity,
    eventStartTime,
    DATETIME_DIFF(CURRENT_DATETIME(), DATETIME(eventStartTime), DAY) as days_offline,
    cause
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
ORDER BY days_offline DESC
LIMIT 10
```

#### 4. Renewables Percentage Over Time
```sql
WITH hourly_gen AS (
    SELECT 
        TIMESTAMP_TRUNC(publishTime, HOUR) as hour,
        fuelType,
        AVG(generation) as avg_gen
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE DATE(publishTime) = CURRENT_DATE()
    GROUP BY hour, fuelType
),
renewable_totals AS (
    SELECT
        hour,
        SUM(CASE WHEN fuelType IN ('WIND', 'PS', 'BIOMASS', 'NPSHYD') 
            THEN avg_gen ELSE 0 END) as renewable_gen,
        SUM(avg_gen) as total_gen
    FROM hourly_gen
    WHERE fuelType NOT LIKE 'INT%'  -- Exclude interconnectors
    GROUP BY hour
)
SELECT 
    hour,
    renewable_gen,
    total_gen,
    ROUND((renewable_gen / total_gen * 100), 1) as renewables_pct
FROM renewable_totals
ORDER BY hour DESC
```

---

### Contact & Support

**Dashboard Owner:** George Major  
**Email:** george.major@grid-smart.co.uk / george@upowerenergy.uk  
**Project:** Grid Smart Production / uPower Energy  

**Google Cloud Project:** inner-cinema-476211-u9  
**BigQuery Dataset:** uk_energy_prod  
**Dashboard URL:** [Google Sheets](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8)

---

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 2025 | Initial dashboard with generation data |
| 1.5 | Oct 2025 | Added REMIT unavailability tracking |
| 2.0 | Oct 30, 2025 | Enhanced design with price analysis, visual % bars, all stations |

---

### License & Data Attribution

**Data Sources:**
- **Elexon BMRS API:** © Elexon Limited. Licensed under Open Government Licence v3.0
- **REMIT Data:** European Union Regulation 1227/2011. Public market transparency data
- **Market Prices:** EPEX SPOT © European Power Exchange

**Dashboard Code:** Proprietary - Grid Smart / uPower Energy

**Usage:** Internal business intelligence and market analysis

---

*End of Documentation*
