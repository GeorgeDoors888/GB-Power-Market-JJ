# REMIT Unavailability Dashboard - Documentation

**Created**: 30 October 2025  
**Status**: ✅ **OPERATIONAL**

---

## 📋 Overview

The REMIT (Regulation on wholesale Energy Market Integrity and Transparency) Unavailability Dashboard tracks unplanned outages of UK power generation facilities. This is "inside information" that market participants must publish before trading on it.

### What is REMIT?

REMIT is EU regulation requiring energy market participants to publicly disclose:
- **Unplanned unavailability** of generation units
- **Capacity reductions** and plant outages
- **Grid connection issues** and interconnector failures
- **Return to service** announcements

This transparency ensures fair market access to critical operational information.

---

## 🎯 Dashboard Features

### New Google Sheets Tab: "REMIT Unavailability"

**Location**: Same spreadsheet as main dashboard  
**Sheet Name**: `REMIT Unavailability`  
**URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

### Dashboard Sections

1. **Summary Statistics**
   - Total active outages
   - Total unavailable capacity (MW)
   - Impact by fuel type

2. **Unavailable Capacity by Fuel Type**
   - Breakdown showing which technologies are most affected
   - Percentage of total unavailable capacity

3. **Active Events Table**
   Columns:
   - Asset Name (e.g., "Drax Unit 1")
   - BM Unit (Balancing Mechanism Unit ID)
   - Fuel Type (CCGT, Nuclear, Wind, etc.)
   - Normal Capacity (MW)
   - Available Capacity (MW)
   - Unavailable Capacity (MW)
   - Start Time
   - End Time (Estimated)
   - Duration (hours)
   - Cause (reason for outage)
   - Operator (participant name)

---

## 💾 BigQuery Table

### Table Details
- **Project**: `inner-cinema-476211-u9`
- **Dataset**: `uk_energy_prod`
- **Table**: `bmrs_remit_unavailability`
- **Full ID**: `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`

### Schema

```sql
messageId              STRING    -- Unique REMIT message ID
revisionNumber         INTEGER   -- Version of the message
messageType            STRING    -- "Unavailability", "Return to Service"
eventType              STRING    -- "Unplanned Outage", etc.
unavailabilityType     STRING    -- "Unplanned" or "Planned"

-- Asset Information
participantId          STRING    -- Market participant ID
participantName        STRING    -- Company name
assetId                STRING    -- Asset identifier
assetName              STRING    -- Human-readable name
assetType              STRING    -- "Generation Unit", "Wind Farm", etc.
affectedUnit           STRING    -- BM Unit code
eicCode                STRING    -- European EIC code

-- Capacity
fuelType               STRING    -- CCGT, NUCLEAR, WIND, etc.
normalCapacity         FLOAT     -- Normal capacity in MW
availableCapacity      FLOAT     -- Current available capacity
unavailableCapacity    FLOAT     -- Amount offline

-- Timing
eventStartTime         DATETIME  -- When outage started
eventEndTime           DATETIME  -- Expected/actual end time
publishTime            DATETIME  -- When message was published

-- Details
eventStatus            STRING    -- Active, Cancelled, Completed
cause                  STRING    -- Reason for outage
relatedInfo            STRING    -- Additional context

-- Metadata
_ingested_utc          DATETIME  -- Data ingestion timestamp
_source                STRING    -- Data source identifier
```

**Table Partitioning**: Partitioned by `eventStartTime` (daily) for query performance

---

## 🔧 Working Scripts

### 1. `fetch_remit_unavailability.py` ✅

**Purpose**: Fetch REMIT data and upload to BigQuery

**Usage**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python fetch_remit_unavailability.py
```

**What It Does**:
1. Creates BigQuery table if it doesn't exist
2. Fetches REMIT unavailability data
3. Converts data types for BigQuery
4. Uploads to `bmrs_remit_unavailability` table
5. Shows preview of current outages

**Current Implementation**: Sample data for demonstration

**Production Integration**:
To fetch live REMIT data, integrate with:
- **Elexon IRIS Service**: FTP-based REMIT message feed
- **ENTSO-E Transparency Platform**: REST API for European data
- **Elexon Portal**: Manual CSV downloads

**Key Code**:
```python
# Create table with proper schema
schema = [
    bigquery.SchemaField("messageId", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("assetName", "STRING"),
    bigquery.SchemaField("fuelType", "STRING"),
    bigquery.SchemaField("unavailableCapacity", "FLOAT"),
    # ... more fields
]

table = bigquery.Table(table_id, schema=schema)
table.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY,
    field="eventStartTime"
)
```

**Expected Output**:
```
🔴 REMIT UNAVAILABILITY DATA INGESTION
⏰ 2025-10-30 14:31:27

✅ Created table inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability
📊 Creating sample REMIT unavailability data...
✅ Created 5 sample REMIT events

📋 Preview of REMIT events:
   🔴 Drax Unit 1 (BIOMASS)
      Unavailable: 660 MW
      Cause: Generator fault - turbine bearing failure
      Until: 2025-11-02 14:31

✅ Uploaded 5 records to BigQuery
✅ REMIT DATA INGESTION COMPLETE!
```

---

### 2. `dashboard_remit_updater.py` ✅

**Purpose**: Update Google Sheets with REMIT unavailability data

**Usage**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python dashboard_remit_updater.py
```

**What It Does**:
1. Queries BigQuery for active unavailability events
2. Calculates summary statistics
3. Creates/updates "REMIT Unavailability" sheet
4. Formats data with colors and styling
5. Auto-resizes columns for readability

**Authentication**: Uses same credentials as main dashboard
- BigQuery: Application Default Credentials
- Google Sheets: token.pickle

**Query Logic**:
```python
# Get active events (currently ongoing)
query = """
SELECT *
FROM bmrs_remit_unavailability
WHERE eventStatus = 'Active'
  AND DATETIME(eventStartTime) <= CURRENT_DATETIME()
  AND DATETIME(eventEndTime) >= CURRENT_DATETIME()
ORDER BY unavailableCapacity DESC
"""
```

**Formatting**:
- Red header with white text
- Bold section headers
- Grey table header row
- Auto-sized columns
- Frozen header rows

**Expected Output**:
```
🔴 REMIT DASHBOARD UPDATER
⏰ 2025-10-30 14:33:38

✅ Found existing 'REMIT Unavailability' sheet
✅ Retrieved 4 active unavailability events
📝 Updating sheet with 23 rows...

✅ REMIT DASHBOARD UPDATE COMPLETE!
📊 Active Events: 4
⚡ Total Unavailable: 1647.0 MW
```

---

## 🔄 Data Flow

```
┌─────────────────────────┐
│  REMIT Data Sources     │
│  • Elexon IRIS          │
│  • ENTSO-E Platform     │
│  • Manual CSV Import    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  fetch_remit_           │
│  unavailability.py      │
│  • Parse REMIT messages │
│  • Extract outage info  │
│  • Convert data types   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Google BigQuery        │
│  bmrs_remit_            │
│  unavailability         │
│  • Store all events     │
│  • Historical tracking  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  dashboard_remit_       │
│  updater.py             │
│  • Query active events  │
│  • Calculate summaries  │
│  • Format for display   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Google Sheets          │
│  "REMIT Unavailability" │
│  • Summary stats        │
│  • Detailed event table │
└─────────────────────────┘
```

---

## 📊 Sample Data

### Current Active Outages (as of 30 Oct 2025)

| Asset | Fuel Type | Unavailable | Cause | Duration |
|-------|-----------|-------------|-------|----------|
| Drax Unit 1 | BIOMASS | 660 MW | Generator fault - turbine bearing failure | 72 hrs |
| Pembroke CCGT Unit 4 | CCGT | 537 MW | Boiler tube leak - emergency shutdown | 120 hrs |
| Sizewell B | NUCLEAR | 300 MW | Reactor de-rating for maintenance | 12 hrs |
| London Array Wind Farm | WIND | 150 MW | Grid connection issue - cable fault | 48 hrs |

**Total Unavailable**: 1,647 MW

### By Fuel Type
- BIOMASS: 660 MW (40.1%)
- CCGT: 537 MW (32.6%)
- NUCLEAR: 300 MW (18.2%)
- WIND: 150 MW (9.1%)

---

## 🔗 Integration with Main Dashboard

### Combined Update Command

Update both main dashboard and REMIT data:

```bash
cd "/Users/georgemajor/GB Power Market JJ"

# Update main generation data
./.venv/bin/python fetch_fuelinst_today.py && \
./.venv/bin/python dashboard_updater_complete.py && \

# Update REMIT unavailability data
./.venv/bin/python fetch_remit_unavailability.py && \
./.venv/bin/python dashboard_remit_updater.py
```

### Automation (Cron)

Add to crontab for regular updates:

```bash
# Update every 30 minutes (REMIT less frequent than real-time data)
*/30 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python fetch_remit_unavailability.py && ./.venv/bin/python dashboard_remit_updater.py >> logs/remit_dashboard.log 2>&1
```

**Note**: REMIT data doesn't change as frequently as real-time generation data, so 30-minute updates are sufficient.

---

## 🐛 Troubleshooting

### Issue: "No matching signature for operator <="

**Cause**: BigQuery DATETIME vs TIMESTAMP comparison issue

**Solution**: Cast datetime fields explicitly:
```sql
WHERE DATETIME(eventStartTime) <= CURRENT_DATETIME()
```

### Issue: "Please install the 'db-dtypes' package"

**Cause**: Missing dependency for BigQuery datetime types

**Solution**:
```bash
pip install db-dtypes
```

### Issue: No active events shown

**Check**:
1. Query BigQuery directly:
```sql
SELECT * 
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
```

2. Verify data was uploaded:
```bash
./.venv/bin/python fetch_remit_unavailability.py
```

3. Check event times are current (not expired):
```sql
SELECT 
    assetName, 
    eventStatus,
    eventStartTime,
    eventEndTime,
    CURRENT_DATETIME() as now
FROM bmrs_remit_unavailability
```

### Issue: Sheet not created

**Verify**:
- Google Sheets authentication working (token.pickle exists)
- Spreadsheet ID correct
- Sheet permissions allow adding new tabs

---

## 📈 Future Enhancements

### Production Data Sources

**Option 1: Elexon IRIS Service** (Recommended)
- FTP-based feed of all REMIT messages
- Real-time updates
- Requires Elexon account and FTP credentials
- Implementation: Extend existing `ingest_remit.py` script

**Option 2: ENTSO-E Transparency Platform**
- REST API for European electricity data
- Includes UK REMIT messages
- Free API key required
- URL: https://transparency.entsoe.eu/
- Implementation:
```python
# Example ENTSO-E API call
url = "https://web-api.tp.entsoe.eu/api"
params = {
    'documentType': 'A80',  # Unavailability documents
    'in_Domain': '10YGB----------A',  # UK
    'periodStart': '202510300000',
    'periodEnd': '202510312359',
    'securityToken': API_KEY
}
```

**Option 3: Manual CSV Import**
- Download from Elexon Portal: https://www.elexonportal.co.uk/
- Convert CSV to BigQuery format
- Schedule daily batch uploads

### Dashboard Enhancements

1. **Add Charts**:
   - Pie chart of unavailable capacity by fuel type
   - Timeline showing duration of outages
   - Historical trend of average unavailability

2. **Alerts**:
   - Email notification for large outages (>500 MW)
   - Slack/Teams integration for real-time alerts
   - Threshold alerts (e.g., total unavailability >2000 MW)

3. **Analytics**:
   - Calculate impact on market prices
   - Predict supply shortfalls
   - Compare planned vs unplanned outages

4. **Mobile View**:
   - Responsive dashboard design
   - Key metrics on mobile-friendly page

---

## 🔐 Security & Compliance

### Data Privacy
- REMIT data is **public information** by regulation
- No personal data or confidential information
- Safe to share and publish

### Authentication
Same as main dashboard:
- **BigQuery**: Application Default Credentials
- **Google Sheets**: OAuth 2.0 token.pickle

### Audit Trail
- All data ingestion timestamped (`_ingested_utc`)
- Source tracking (`_source` field)
- Revision numbers tracked for message updates

---

## 📚 Useful Queries

### Get Current Total Unavailable Capacity
```sql
SELECT 
    SUM(unavailableCapacity) as total_unavailable_mw,
    COUNT(*) as active_events
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
  AND DATETIME(eventStartTime) <= CURRENT_DATETIME()
  AND DATETIME(eventEndTime) >= CURRENT_DATETIME()
```

### Unavailability by Fuel Type (Last 7 Days)
```sql
SELECT 
    fuelType,
    AVG(unavailableCapacity) as avg_unavailable_mw,
    COUNT(*) as num_events,
    AVG(DATETIME_DIFF(eventEndTime, eventStartTime, HOUR)) as avg_duration_hours
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE DATETIME(eventStartTime) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
GROUP BY fuelType
ORDER BY avg_unavailable_mw DESC
```

### Longest Outages This Month
```sql
SELECT 
    assetName,
    fuelType,
    unavailableCapacity,
    eventStartTime,
    eventEndTime,
    DATETIME_DIFF(eventEndTime, eventStartTime, HOUR) as duration_hours,
    cause
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE EXTRACT(MONTH FROM eventStartTime) = EXTRACT(MONTH FROM CURRENT_DATETIME())
ORDER BY duration_hours DESC
LIMIT 10
```

### Assets with Most Frequent Outages
```sql
SELECT 
    assetName,
    fuelType,
    COUNT(*) as num_outages,
    SUM(unavailableCapacity) as total_capacity_affected_mw,
    AVG(DATETIME_DIFF(eventEndTime, eventStartTime, HOUR)) as avg_duration_hours
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
WHERE DATETIME(eventStartTime) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 30 DAY)
GROUP BY assetName, fuelType
HAVING num_outages > 1
ORDER BY num_outages DESC, total_capacity_affected_mw DESC
```

---

## 📞 Resources

### Official Documentation
- **REMIT Guidance**: https://www.ofgem.gov.uk/environmental-and-social-schemes/remit
- **Elexon IRIS**: https://www.elexon.co.uk/operations-settlement/bsc-central-services/elexon-iris-service/
- **ENTSO-E Transparency**: https://transparency.entsoe.eu/
- **Elexon Portal**: https://www.elexonportal.co.uk/

### REMIT Regulation
- **EU Regulation 1227/2011**: Wholesale energy market integrity
- **UK Implementation**: Financial Conduct Authority (FCA)
- **Reporting Requirements**: Inside information must be disclosed "as soon as possible"

---

## ✅ Success Criteria

### System Working Correctly When:
1. ✅ REMIT sheet exists in spreadsheet
2. ✅ Active outages displayed with correct capacity values
3. ✅ Summary statistics calculate correctly
4. ✅ BigQuery table contains historical REMIT data
5. ✅ Event timestamps are reasonable (not expired events shown as active)
6. ✅ Fuel type breakdown sums to total unavailable capacity
7. ✅ Dashboard updates without errors

### Red Flags:
- ❌ Total unavailable capacity > 10,000 MW (unrealistic unless major grid issue)
- ❌ Events with negative unavailability
- ❌ Start time after end time
- ❌ Duration > 30 days (possible, but unusual for unplanned outage)

---

**Last Updated**: 30 October 2025, 14:35:00  
**Status**: ✅ **OPERATIONAL WITH SAMPLE DATA**  
**Next Step**: Integrate with live REMIT feed (Elexon IRIS or ENTSO-E)

---

*This REMIT dashboard provides transparency into UK power market unavailability events, helping market participants make informed trading decisions based on publicly disclosed inside information.*
