# GB Power Market Dashboard - Complete Guide

**Last Updated**: November 9, 2025  
**Version**: 3.0  
**Status**: ✅ Production Ready with Live REMIT Data

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Dashboard Tabs](#dashboard-tabs)
3. [REMIT Outages (NEW!)](#remit-outages-new)
4. [Setup & Access](#setup--access)
5. [Refresh Mechanisms](#refresh-mechanisms)
6. [Data Sources](#data-sources)
7. [Using the Dashboard](#using-the-dashboard)
8. [Troubleshooting](#troubleshooting)
9. [Technical Details](#technical-details)

---

## Overview

The **GB Power Market Dashboard** provides real-time insights into UK energy markets, including:

- ✅ **Live REMIT Outages** (NEW as of Nov 9, 2025) - Real-time power plant unavailability
- ✅ **BESS VLP DNO Lookup** - Distribution Network Operator identification
- ✅ **Statistical Analysis** - Market price trends and battery arbitrage
- ✅ **Generator Maps** - Geographic visualization of UK power plants

### Quick Links

| Resource | URL |
|----------|-----|
| **Main Dashboard** | [Google Sheet](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/) |
| **Generator Map** | http://94.237.55.15/gb_power_comprehensive_map.html |
| **ChatGPT Proxy** | https://gb-power-market-jj.vercel.app/api/proxy-v2 |
| **GitHub Repo** | https://github.com/GeorgeDoors888/GB-Power-Market-JJ |

---

## Dashboard Tabs

### 1. BESS_VLP (DNO Lookup)

**Purpose**: Identify UK Distribution Network Operators by postcode or MPAN ID

**Features**:
- Postcode lookup via postcodes.io API
- DNO dropdown selection (14 UK DNOs)
- Google Maps integration
- Hidden reference table (14 DNO records)
- Auto-refresh from BigQuery

**Key Cells**:
- B4: Postcode input
- E4: DNO dropdown
- Row 10: Results (MPAN, DNO Key, Name, GSP, etc.)
- Rows 14-15: Coordinates
- Row 19: Google Maps link

**Menu**: 🔋 BESS VLP Tools
- Lookup DNO from Postcode/Dropdown
- Refresh DNO Reference Table
- Show/Hide Reference Table

**Documentation**: See `BESS_VLP_COMPLETE_GUIDE.md`

---

### 2. Live_Raw_REMIT_Outages (NEW!)

**Purpose**: Real-time power plant unavailability tracking

**Status**: ✅ **LIVE DATA** (as of Nov 9, 2025, 22:05 UTC)

**Current Metrics**:
- **Total Outages**: 654 records
- **Active Outages**: 576 outages
- **Unique Assets**: 75 power plants
- **Most Recent Data**: Nov 9, 22:04:47 UTC (real-time)
- **Data Freshness**: Within 1 minute

**Columns**:
1. **assetId** - Unit identifier (e.g., T_LBAR-1)
2. **assetName** - Power plant name
3. **fuelType** - Fossil Gas, Nuclear, Wind, Solar, etc.
4. **normalCapacity** - Normal capacity in MW
5. **unavailableCapacity** - Unavailable capacity in MW
6. **eventStatus** - Active or Dismissed
7. **eventStartTime** - Outage start timestamp
8. **eventEndTime** - Outage end timestamp
9. **publishTime** - When message was published
10. **cause** - Reason for outage (e.g., "Turbine bearing failure")
11. **mrid** - Unique message reference ID
12. **affectedUnitEIC** - EIC code for affected unit
13. **biddingZone** - Market bidding zone

**Sample Outages**:
```
LBAR-1 (Little Barford):
- Fuel: Fossil Gas
- Normal: 735 MW
- Unavailable: 376 MW
- Status: Active
- Cause: "1+1 Operation see SONAR ad. GT"
- Start: 2025-11-08 21:00:00
- End: 2025-11-09 15:00:02
```

**Data Source**: 
- IRIS Pipeline → Azure Service Bus → BigQuery
- Table: `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
- Update Frequency: Real-time (within seconds)

**Use Cases**:
- Battery arbitrage analysis (plant outages = price spikes)
- VLP revenue forecasting (reduced competition)
- Grid stability monitoring
- Capacity margin tracking

---

### 3. Analysis & Statistics Tabs

**Enhanced BI Analysis** - Market price statistics
**Statistical Analysis** - Advanced analytics
**Battery Revenue** - VLP arbitrage calculations
**Frequency Analysis** - Grid stability metrics

**Documentation**: See `ENHANCED_BI_ANALYSIS_README.md`, `STATISTICAL_ANALYSIS_GUIDE.md`

---

## REMIT Outages (NEW!)

### What is REMIT?

**REMIT** = Regulation on Energy Market Integrity and Transparency

EU regulation requiring power plant operators to report:
- Unplanned outages
- Planned maintenance
- Capacity changes
- Transmission constraints

**Why It Matters for BESS/VLP**:
1. **Price Impact**: Large outages → higher prices → better arbitrage opportunities
2. **Competition Analysis**: Which generators are offline → market dynamics
3. **Revenue Forecasting**: Correlate outages with historical price spikes
4. **Real-Time Strategy**: Adjust bidding based on current unavailability

### REMIT Data Pipeline

```
Elexon REMIT API
       ↓
Azure Service Bus (IRIS)
       ↓
AlmaLinux Server (94.237.55.234)
  - iris_client (downloads)
  - iris_uploader (uploads)
       ↓
BigQuery: bmrs_remit_unavailability
       ↓
Google Sheets: Live_Raw_REMIT_Outages
       ↓
Your Analysis!
```

### Key Features

#### 1. Real-Time Updates
- **Latency**: <1 minute from publish to dashboard
- **Frequency**: Continuous streaming
- **Reliability**: Automatic retry on failure

#### 2. Historical Tracking
- **Retention**: 5+ days (Nov 4-9 currently)
- **Backfill**: 652 messages recovered from Oct 30 outage
- **Archive**: Can extend retention in BigQuery

#### 3. Comprehensive Details
Every outage includes:
- Power plant identification (assetId, assetName, EIC code)
- Fuel type (Gas, Nuclear, Wind, etc.)
- Capacity impact (normal vs unavailable MW)
- Timing (start, end, publish timestamps)
- Cause description
- Status (Active/Dismissed)

### Sample Analysis Queries

#### Find Large Gas Plant Outages:
```sql
SELECT 
  assetId,
  assetName,
  unavailableCapacity,
  eventStartTime,
  cause
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE fuelType = 'Fossil Gas'
  AND unavailableCapacity > 200
  AND eventStatus = 'Active'
ORDER BY unavailableCapacity DESC
```

#### Track Outages Over Time:
```sql
SELECT 
  DATE(eventStartTime) as date,
  COUNT(*) as outage_count,
  SUM(unavailableCapacity) as total_mw_unavailable
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
GROUP BY date
ORDER BY date DESC
```

#### Correlate with Prices (requires joining with bmrs_mid):
```sql
WITH outages AS (
  SELECT 
    DATE(eventStartTime) as date,
    SUM(unavailableCapacity) as unavailable_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
  WHERE fuelType = 'Fossil Gas'
  GROUP BY date
),
prices AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    AVG(systemSellPrice) as avg_price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  GROUP BY date
)
SELECT 
  o.date,
  o.unavailable_mw,
  p.avg_price
FROM outages o
JOIN prices p ON o.date = p.date
ORDER BY o.date DESC
```

---

## Setup & Access

### Prerequisites

- ✅ Google account with Sheets access
- ✅ Access to Google Cloud project: `inner-cinema-476211-u9`
- ✅ BigQuery read permissions
- ✅ Service account credentials: `service_account.json`

### Access the Dashboard

**Direct Link**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

### Share with Team

1. Click **Share** button (top right)
2. Enter email addresses
3. Set permissions:
   - **Viewer**: Read-only access
   - **Editor**: Can modify formulas/formatting (not recommended)
   - **Commenter**: Can add comments

---

## Refresh Mechanisms

### 1. Automatic (REMIT Data) ✅ REAL-TIME

**How It Works**:
```
1. Power plant operator reports outage to Elexon
2. Elexon publishes to Azure Service Bus (within seconds)
3. IRIS client downloads message (PID 7260 on server)
4. IRIS uploader inserts to BigQuery (PID 22590 on server)
5. Dashboard shows updated data (<1 min total)
```

**Status Check**:
```bash
ssh root@94.237.55.234 'ps aux | grep iris | grep -v grep'
```

**Expected Output**:
```
root      7260  iris_client
root     22590  iris_uploader
```

**Recent Activity**:
```bash
ssh root@94.237.55.234 'tail -50 /opt/iris-pipeline/logs/iris_uploader.log | grep remit'
```

---

### 2. Manual (Dashboard Refresh)

**Script**: `tools/refresh_live_dashboard.py`

**Command**:
```bash
cd tools
SHEET_ID="12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8" \
GOOGLE_APPLICATION_CREDENTIALS="../service_account.json" \
python3 refresh_live_dashboard.py
```

**What It Does**:
1. Queries BigQuery for all active REMIT outages
2. Formats data for Sheets API
3. Writes to "Live_Raw_REMIT_Outages" tab
4. Updates timestamp

**Frequency**: On-demand (or add to cron for auto-refresh)

---

### 3. Auto-Refresh (Cron Job)

**Setup**:
```bash
crontab -e

# Add line:
*/5 * * * * cd /Users/georgemajor/GB\ Power\ Market\ JJ/tools && SHEET_ID="12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8" GOOGLE_APPLICATION_CREDENTIALS="../service_account.json" /opt/homebrew/bin/python3 refresh_live_dashboard.py >> /tmp/dashboard_refresh.log 2>&1
```

**Runs**: Every 5 minutes

---

## Data Sources

### Primary BigQuery Tables

| Table | Purpose | Update Freq | Status |
|-------|---------|-------------|--------|
| `bmrs_remit_unavailability` | Power plant outages | Real-time | ✅ LIVE |
| `neso_dno_reference` | DNO reference data | Static | ✅ OK |
| `neso_dno_boundaries` | DNO geographic boundaries | Static | ✅ OK |
| `bmrs_mid` | Market prices | 5-min | ⚠️ Stale (Oct 30) |
| `bmrs_bod` | Bid-offer data | 5-min | ⚠️ Stale (Oct 28) |
| `bmrs_fuelinst` | Fuel generation | 5-min | ⚠️ Stale (Oct 30) |

### External APIs

| API | Purpose | Auth Required | Status |
|-----|---------|---------------|--------|
| postcodes.io | UK postcode lookup | No | ✅ OK |
| Azure Service Bus (IRIS) | Real-time data stream | Service account | ✅ OK |
| Elexon BMRS | Historical batch data | API key | ⚠️ Some tables stale |

---

## Using the Dashboard

### Scenario 1: Check Current Outages

**Goal**: See which power plants are offline right now

**Steps**:
1. Open [Dashboard](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/)
2. Go to **"Live_Raw_REMIT_Outages"** tab
3. Filter by **eventStatus** = "Active"
4. Sort by **unavailableCapacity** (descending)

**Result**: List of largest current outages

---

### Scenario 2: Find DNO for Battery Site

**Goal**: Identify which DNO serves a proposed battery location

**Steps**:
1. Open [Dashboard](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/)
2. Go to **"BESS_VLP"** tab
3. Cell B4 → Enter postcode (e.g., "RH19 4LX")
4. Menu → **🔋 BESS VLP Tools** → **Lookup DNO from Postcode/Dropdown**
5. View results in row 10

**Result**: MPAN ID, DNO name, GSP group, coverage area

---

### Scenario 3: Analyze Outage Impact on Prices

**Goal**: Correlate large outages with price spikes

**Steps**:
1. Query BigQuery (see sample queries above)
2. Join REMIT outages with market prices
3. Export to CSV or connect to visualization tool
4. Identify patterns

**Result**: Data for revenue forecasting models

---

### Scenario 4: Track Specific Power Plant

**Goal**: Monitor Little Barford (LBAR-1) outages

**Steps**:
1. Open **"Live_Raw_REMIT_Outages"** tab
2. Use Google Sheets filter: **assetId** contains "LBAR"
3. View all historical outages for Little Barford

**Result**: Complete outage history for target plant

---

## Troubleshooting

### Issue: REMIT Data Not Updating

**Symptoms**: Most recent data >5 minutes old

**Check Pipeline**:
```bash
# Check if IRIS processes running
ssh root@94.237.55.234 'ps aux | grep iris | grep -v grep'

# Check recent logs
ssh root@94.237.55.234 'tail -100 /opt/iris-pipeline/logs/iris_uploader.log'
```

**Solution**:
```bash
# Restart IRIS services
ssh root@94.237.55.234 'systemctl restart iris-client iris-uploader'

# Wait 1 minute, verify data flowing
```

---

### Issue: Dashboard Not Refreshing

**Symptoms**: Sheets showing old data

**Solution**:
```bash
# Manual refresh
cd tools
SHEET_ID="12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8" \
GOOGLE_APPLICATION_CREDENTIALS="../service_account.json" \
python3 refresh_live_dashboard.py
```

---

### Issue: "Permission Denied" Errors

**Symptoms**: Can't access BigQuery or Sheets

**Solution**:
1. Check service account credentials exist:
   ```bash
   ls service_account.json
   ```
2. Verify BigQuery permissions:
   ```bash
   bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability\`"
   ```
3. Contact project owner: george@upowerenergy.uk

---

### Issue: Wrong BigQuery Project

**Symptoms**: "Table not found" errors

**Solution**: Always use `inner-cinema-476211-u9` (NOT `jibber-jabber-knowledge`)

---

## Technical Details

### REMIT Pipeline Architecture

**Server**: 94.237.55.234 (almalinux-1cpu-2gb-uk-lon1)

**Process 1: iris_client**
- **PID**: 7260
- **Purpose**: Download messages from Azure Service Bus
- **Config**: `/opt/iris-pipeline/iris-clients/python/config.json`
- **Output**: JSON files in `/opt/iris-pipeline/iris-clients/python/iris_data/`
- **Frequency**: Continuous polling

**Process 2: iris_uploader**
- **PID**: 22590
- **Purpose**: Upload JSON to BigQuery
- **Script**: `/opt/iris-pipeline/iris_to_bigquery_unified.py`
- **Table Mapping**: `'REMIT': 'bmrs_remit_unavailability'`
- **Frequency**: Every 5 seconds

**Modified Fields**:
```python
# Removed incompatible fields
if 'outageProfile' in data:
    del data['outageProfile']  # Array field
if 'durationUncertainty' in data:
    del data['durationUncertainty']
```

### BigQuery Schema (34 fields)

**Table**: `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`

**Key Fields**:
- messageId (STRING)
- mrid (STRING) - Unique message reference
- assetId (STRING) - Unit identifier
- assetName (STRING)
- assetType (STRING)
- fuelType (STRING)
- normalCapacity (FLOAT64)
- availableCapacity (FLOAT64)
- unavailableCapacity (FLOAT64)
- eventStatus (STRING) - Active/Dismissed
- eventStartTime (TIMESTAMP)
- eventEndTime (TIMESTAMP)
- publishTime (TIMESTAMP)
- cause (STRING)
- affectedUnitEIC (STRING)
- biddingZone (STRING)
- + 18 more fields

**Schema File**: `/tmp/remit_schema_fixed.json`

### Dashboard Refresh Script

**File**: `tools/refresh_live_dashboard.py`

**Key Functions**:
```python
def write_df(tab_name, start_cell, df):
    """Write dataframe to Sheets tab"""
    
# REMIT query
SQL_REMIT_OUTAGES = """
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
ORDER BY publishTime DESC
"""

# Execute and write
remit = q_no_date(SQL_REMIT_OUTAGES)
write_df("Live_Raw_REMIT_Outages", "A1", remit)
```

**Dependencies**:
- google-cloud-bigquery
- gspread
- oauth2client
- pandas

---

## Performance & Costs

### BigQuery Usage

| Operation | Frequency | Data Scanned | Cost |
|-----------|-----------|--------------|------|
| REMIT insert | Real-time | N/A | Free |
| Dashboard refresh | Manual/5-min | ~100KB | Free tier |
| Analysis queries | Ad-hoc | Varies | <$1/month |

**Total Monthly Cost**: ~$0 (within free tier)

### IRIS Pipeline

**Server Cost**: ~$5/month (AlmaLinux VPS)  
**Storage**: <1GB for 30-day rolling window  
**Bandwidth**: Negligible (<1GB/month)

---

## Related Documentation

- **BESS VLP Guide**: `BESS_VLP_COMPLETE_GUIDE.md`
- **REMIT Restoration**: `REMIT_DATA_PIPELINE_RESTORED.md`
- **Project Configuration**: `PROJECT_CONFIGURATION.md`
- **Data Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **Statistical Analysis**: `STATISTICAL_ANALYSIS_GUIDE.md`
- **ChatGPT Integration**: `CHATGPT_INSTRUCTIONS.md`

---

## Support & Contact

**Maintainer**: George Major  
**Email**: george@upowerenergy.uk  
**Server**: 94.237.55.234 (root@94.237.55.234)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

**For Issues**:
1. Check relevant troubleshooting section
2. Review logs: `/opt/iris-pipeline/logs/iris_uploader.log`
3. Test BigQuery connectivity
4. Contact maintainer with error details

---

## Changelog

### Version 3.0 (November 9, 2025)
- ✅ Added **Live_Raw_REMIT_Outages** tab (real-time data!)
- ✅ Fixed REMIT pipeline (652 backlog files processed)
- ✅ Recreated BigQuery table with 34-field schema
- ✅ Integrated dashboard refresh script
- ✅ Confirmed <1 minute data freshness
- ✅ Restored live outage tracking for 75 power plants

### Version 2.0 (November 6, 2025)
- ✅ Added BESS_VLP DNO lookup
- ✅ Enhanced menu with 3 options
- ✅ Fixed centroid coordinate mappings
- ✅ Added toggle visibility function

### Version 1.0 (October 2025)
- ✅ Initial dashboard with statistical analysis
- ✅ Battery revenue tracking
- ✅ Frequency analysis

---

**Last Updated**: November 9, 2025, 22:30 UTC  
**Status**: ✅ **FULLY OPERATIONAL** - Real-time REMIT data confirmed  
**Next Review**: Weekly (check for stale tables: bmrs_mid, bmrs_bod, bmrs_fuelinst)

*For updates to this guide, see: `CHANGELOG.md`*
