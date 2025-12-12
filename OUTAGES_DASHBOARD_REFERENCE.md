# Outages Dashboard - Quick Reference

**Last Updated**: 12 December 2025  
**Location**: Live Dashboard v2, Row 40+, Columns G-Q  
**Auto-Updates**: Every 5 minutes  
**Script**: `update_live_dashboard_v2_outages.py`

---

## 📊 Dashboard Columns (11 Total)

| Column | Field | Description | Example |
|--------|-------|-------------|---------|
| **G** | Asset Name | Station/unit name from BMU registration | IED-FRAN1, Didcot B main unit 6 |
| **H** | Fuel Type | Type with emoji | 🏭 CCGT, ⚛️ NUCLEAR, 🇫🇷 INTFR |
| **I** | Unavail (MW) | Capacity currently offline | 750, 666, 660 |
| **J** | Normal (MW) | Total installed capacity | 2000, 710, 1285 |
| **K** | Cause | Reason for outage | DC Cable Fault, Turbine/Generator, OPR |
| **L** | Type | Planned or Unplanned | 📅 Planned, ⚡ Unplanned |
| **M** | Expected Return | When unit comes back online | 2026-02-20 16:00 |
| **N** | Duration | Time offline (days/hours) | 130d 9h, 54d 15h |
| **O** | Operator | Company operating the asset | (Often blank in REMIT data) |
| **P** | Area | Geographic area affected | (Often blank) |
| **Q** | Zone | Bidding zone | 10YGB----------A (GB) |

---

## 💡 Key Insights Available

### Capacity Context
- **Normal (MW)** shows total unit size
- Calculate % offline: (Unavail / Normal) × 100
- Example: 666 MW / 710 MW = 93.8% of unit offline

### Market Impact Assessment
- **Type** field shows Planned vs Unplanned
- **⚡ Unplanned** = Higher market impact (unexpected scarcity)
- **📅 Planned** = Market already priced in

### Return Forecasting
- **Expected Return** shows restoration date
- **Duration** shows total outage length
- Long durations (130+ days) indicate major repairs

### Real-World Examples

**IFA2 Interconnector Outage (I_IED-FRAN1)**:
```
Unavail:    750 MW
Normal:     2000 MW (37.5% offline)
Type:       ⚡ Unplanned
Cause:      DC Cable Fault
Duration:   130d 9h (since Oct 13, 2025)
Return:     2026-02-20 16:00
Impact:     Reduced France-GB import capacity
```

**Didcot B Unit 6 (DIDCB6)**:
```
Unavail:    666 MW
Normal:     710 MW (93.8% offline)
Type:       ⚡ Unplanned
Fuel:       🏭 CCGT (Fossil Gas)
Cause:      Turbine / Generator
Duration:   54d 15h (since Nov 11, 2025)
Return:     2026-01-05 07:00
Impact:     Loss of baseload gas generation
```

**Heysham 2 Reactor 7 (T_HEYM27)**:
```
Unavail:    660 MW
Normal:     1285 MW (51.4% offline)
Type:       ⚡ Unplanned
Fuel:       ⚛️ NUCLEAR
Cause:      OPR (Operational)
Duration:   ~60 days
Impact:     Reduced nuclear baseload capacity
```

---

## 🔍 Data Sources

### BigQuery Tables
- **`bmrs_remit_unavailability`** - REMIT transparency outage reports
  - All EU/GB generation & transmission outages >100 MW
  - Updated in near real-time by market participants
  - Includes planned & unplanned events

- **`bmu_registration_data`** - National Grid BMU registry
  - Proper asset names (REMIT often uses codes)
  - Fuel type mapping
  - Joins on `nationalgridbmunit` or `elexonbmunit`

### Data Processing
```sql
-- Deduplication: Latest revision only
WITH latest_revisions AS (
    SELECT affectedUnit, MAX(revisionNumber) as max_rev
    FROM bmrs_remit_unavailability
    WHERE eventStatus = 'Active'
    GROUP BY affectedUnit
)

-- Join with BMU registration for names
LEFT JOIN bmu_registration_data bmu
    ON u.affectedUnit = bmu.nationalgridbmunit
    OR u.affectedUnit = bmu.elexonbmunit

-- Duration calculation
TIMESTAMP_DIFF(
    COALESCE(eventEndTime, CURRENT_TIMESTAMP()), 
    eventStartTime, 
    HOUR
) as duration_hours
```

---

## 📈 Using the Data

### Market Analysis
1. **Check Type column** - Unplanned outages have higher impact
2. **Compare Unavail vs Normal** - % of capacity offline
3. **Review Expected Return** - When scarcity ends
4. **Monitor Duration** - Long outages = structural issues

### Trading Signals
- **Large nuclear outages** (>500 MW) → Price spike risk
- **Multiple CCGT outages** → Reduced gas flexibility
- **Interconnector outages** → Import/export constraints
- **Planned outages** in winter → Capacity margin concerns

### Reporting
- **Export to CSV**: Use Google Sheets download
- **API Access**: Query `bmrs_remit_unavailability` directly
- **Historical Analysis**: All revisions stored in BigQuery

---

## 🔧 Maintenance

### Update Frequency
- **Auto-update**: Every 5 minutes via cron
- **Manual update**: `python3 update_live_dashboard_v2_outages.py`
- **Log file**: `~/dashboard_v2_updates.log`

### Monitoring
```bash
# Check last update
tail -f ~/dashboard_v2_updates.log

# Verify data freshness
python3 -c "
from google.oauth2 import service_account
import gspread
credentials = service_account.Credentials.from_service_account_file(
    '/home/george/inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA').worksheet('Live Dashboard v2')
data = sheet.get('G41:G45')
print('Current outages:', [row[0] for row in data if row])
"
```

### Troubleshooting
- **Missing asset names**: Check `bmu_registration_data` coverage
- **Empty operator field**: Normal - REMIT often doesn't include this
- **Wrong duration**: Check `eventStartTime`/`eventEndTime` in source data
- **Column width issues**: Run script again (auto-sets widths)

---

## 📊 Column Width Settings

Optimized for readability:
```python
G (Asset Name):      200px
H (Fuel Type):       140px
I (Unavail MW):      100px
J (Normal MW):       100px
K (Cause):           150px
L (Type):            130px
M (Expected Return): 140px
N (Duration):         90px
O (Operator):        180px
P (Area):            120px
Q (Zone):            100px
```

---

## 🔗 Related Documentation

- **[DASHBOARD_AUTO_UPDATE_GUIDE.md](DASHBOARD_AUTO_UPDATE_GUIDE.md)** - Complete auto-update setup
- **[DASHBOARD_UPDATES_SUMMARY.md](DASHBOARD_UPDATES_SUMMARY.md)** - Implementation summary
- **[PROJECT_CONFIGURATION.md](docs/PROJECT_CONFIGURATION.md)** - BigQuery setup
- **[STOP_DATA_ARCHITECTURE_REFERENCE.md](docs/STOP_DATA_ARCHITECTURE_REFERENCE.md)** - Data architecture

---

**Dashboard Link**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid=687718775

**Auto-updates every 5 minutes** ✅
