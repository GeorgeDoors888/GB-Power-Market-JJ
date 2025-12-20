# IRIS Data Ingestion Status - Complete Documentation

**Date**: December 17, 2025
**Feature**: Real-time IRIS data ingestion monitoring with traffic light status
**Location**: Live Dashboard v2, Cell A3
**Update Frequency**: Every 5 minutes (via cron)

---

## Overview

The IRIS ingestion status provides real-time monitoring of data flowing from Elexon's IRIS API → Azure Service Bus → BigQuery. It replaces the old warning system with a comprehensive traffic light dashboard showing:

- **Overall health** (🟢/🟠/🔴)
- **Total data volume** ingested today
- **Individual stream status** (5 separate IRIS tables)
- **Built-in key** explaining traffic light meanings

---

## Dashboard Display Format

### Cell Position
**Cell A3** on "Live Dashboard v2" sheet

### Display Format
```
🟢 IRIS: 74,680 rows today | 5🟢 0🟠 0🔴 | Key: 🟢<30m 🟠30-120m 🔴>120m
```

### Components Breakdown

| Component | Example | Meaning |
|-----------|---------|---------|
| Overall Icon | 🟢 | System-wide health status |
| Total Rows | `74,680 rows today` | Total records ingested since midnight |
| Stream Counts | `5🟢 0🟠 0🔴` | Count of streams in each status |
| Key | `🟢<30m 🟠30-120m 🔴>120m` | Traffic light definitions |

---

## Traffic Light System

### 🟢 Green: FRESH (< 30 minutes old)
- **Meaning**: Data stream is actively updating
- **Settlement Periods**: Within 1 period of current time
- **Action Required**: None - system healthy

### 🟠 Orange: AGING (30-120 minutes old)
- **Meaning**: Data stream has minor delay
- **Settlement Periods**: 1-4 periods behind
- **Action Required**: Monitor - may indicate temporary issue

### 🔴 Red: STALE (> 120 minutes old)
- **Meaning**: Data stream not receiving updates
- **Settlement Periods**: 4+ periods behind
- **Action Required**: Check IRIS pipeline on AlmaLinux server

---

## Monitored Data Streams

The system monitors 5 IRIS tables in BigQuery:

| Table Name | Short Name | Description | Typical Daily Volume |
|------------|------------|-------------|---------------------|
| `bmrs_fuelinst_iris` | Gen Mix | Generation fuel mix by type | ~1,280 rows |
| `bmrs_bod_iris` | BM Bids | Bid-Offer Data submissions | ~50,000-60,000 rows |
| `bmrs_boalf_iris` | Acceptances | Accepted balancing actions | ~4,000-5,000 rows |
| `bmrs_mid_iris` | Market | Market Index Price (wholesale) | ~20-50 rows |
| `bmrs_indgen_iris` | Units | Individual generator output | ~14,000-15,000 rows |

**Total Expected Daily Volume**: 70,000-80,000 rows

---

## Technical Implementation

### File Location
`/home/george/GB-Power-Market-JJ/update_live_dashboard_v2.py`

### Function: `check_data_freshness()`

**Lines**: 68-158

**Logic Flow**:
1. Query each IRIS table for today's data (`WHERE CAST(settlementDate AS DATE) >= CURRENT_DATE()`)
2. Calculate age using settlement period: `date + (period × 30 minutes)`
3. Assign traffic light status based on age thresholds
4. Aggregate statistics across all streams
5. Return formatted status message

### Key SQL Calculation

```sql
-- Age calculation using settlement period (CORRECT method)
SELECT
    COUNT(*) as row_count,
    MAX(CAST(settlementDate AS DATE)) as latest_date,
    MAX(settlementPeriod) as latest_period,
    TIMESTAMP_DIFF(
        CURRENT_TIMESTAMP(),
        TIMESTAMP_ADD(
            CAST(CAST(MAX(settlementDate) AS DATE) AS TIMESTAMP),
            INTERVAL (MAX(settlementPeriod) * 30) MINUTE
        ),
        MINUTE
    ) as age_minutes
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE CAST(settlementDate AS DATE) >= CURRENT_DATE()
```

**Why This Calculation?**
- `settlementDate` is a DATETIME field set to **midnight** of the settlement day
- Using raw timestamp would show data as 23+ hours old at 11:59 PM
- Adding `settlementPeriod × 30 minutes` gives accurate data age
- Settlement Period 48 (23:30-00:00) + midnight = 24:00 = now

### Status Determination Logic

```python
# Individual stream status
if age_minutes < 30:
    status_icon = '🟢'
    status_text = 'FRESH'
elif age_minutes < 120:
    status_icon = '🟠'
    status_text = 'AGING'
else:
    status_icon = '🔴'
    status_text = 'STALE'

# Overall system status (based on freshest stream)
if freshest_age < 30:
    overall_status = 'OK'
    overall_icon = '🟢'
elif freshest_age < 120:
    overall_status = 'AGING'
    overall_icon = '🟠'
else:
    overall_status = 'STALE'
    overall_icon = '🔴'
```

### Return Object Structure

```python
{
    'status': 'OK',                    # Overall: OK/AGING/STALE
    'icon': '🟢',                      # Overall icon
    'text': 'ACTIVE',                  # Overall text
    'total_rows': 74680,               # Total rows today
    'active_streams': 5,               # Count of 🟢 streams
    'aging_streams': 0,                # Count of 🟠 streams
    'stale_streams': 0,                # Count of 🔴 streams
    'freshest_age': -12,               # Freshest stream age (minutes)
    'freshest_table': 'Gen Mix',       # Name of freshest stream
    'table_stats': [                   # Detailed per-table stats
        {
            'table': 'bmrs_fuelinst_iris',
            'name': 'Gen Mix',
            'rows': 1280,
            'age_minutes': -12,
            'latest_period': 48,
            'status_icon': '🟢',
            'status_text': 'FRESH',
            'latest_date': datetime.date(2025, 12, 17)
        },
        # ... 4 more tables
    ],
    'message': '🟢 IRIS: 74,680 rows today | 5🟢 0🟠 0🔴 | Key: 🟢<30m 🟠30-120m 🔴>120m'
}
```

---

## Google Sheets API Integration

### Update Location
**Sheet**: `Live Dashboard v2` (SheetID: 687718775)
**Spreadsheet**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`

### Cell Layout

| Row | Cell | Content | Format | Update Frequency |
|-----|------|---------|--------|------------------|
| 1 | A1 | `⚡ GB Power Market v2 🇬🇧` | Static header | Manual only |
| 2 | A2 | `Last Updated: 17/12/2025, 23:46:58 (v2.0) SP 48` | Timestamp + SP | Every 5 min |
| 3 | A3 | `🟢 IRIS: 74,680 rows today \| 5🟢 0🟠 0🔴 \| Key: 🟢<30m 🟠30-120m 🔴>120m` | IRIS status | Every 5 min |
| 4 | A4 | `🚀 Market Overview` | Section header | Static |

### Update Code (Lines 868-872)

```python
# Update IRIS data ingestion status (Row 3) - Always show status with traffic lights
batch_updates.append({
    'range': 'A3',
    'values': [[freshness_check['message']]]
})
```

**Method**: `sheet.batch_update()` with `value_input_option='USER_ENTERED'`

**Authentication**: Service account credentials (`inner-cinema-credentials.json`)

---

## Automation

### Cron Schedule
```bash
*/5 * * * * /home/george/GB-Power-Market-JJ/bg_live_cron.sh
```

**Script**: `bg_live_cron.sh` → `update_live_dashboard_v2.py`

**Frequency**: Every 5 minutes (12 times per hour, 288 times per day)

### Log Location
```bash
/home/george/GB-Power-Market-JJ/logs/live_dashboard_v2_complete.log
```

**Log Rotation**: Last 1000 lines kept automatically

---

## Historical Context: Why This Changed

### Old System (Before Dec 17, 2025)
```
⚠️ WARNING: IRIS data is 1360 minutes old!
```

**Problems**:
1. Only showed warnings when stale (no positive feedback)
2. Only checked one table (`bmrs_fuelinst_iris`)
3. Used raw timestamp (incorrect - showed 23h old at midnight)
4. Confusing for users (what does 1360 minutes mean?)
5. No context about which streams working vs broken

### New System (After Dec 17, 2025)
```
🟢 IRIS: 74,680 rows today | 5🟢 0🟠 0🔴 | Key: 🟢<30m 🟠30-120m 🔴>120m
```

**Improvements**:
1. **Always visible** - shows status whether good or bad
2. **All 5 streams monitored** - comprehensive coverage
3. **Settlement period calculation** - accurate age measurement
4. **Data volume metric** - shows ingestion productivity
5. **Traffic lights with key** - instant visual understanding
6. **Stream-by-stream breakdown** - pinpoint issues quickly

---

## Troubleshooting Guide

### Status: 🟢 All Green
**Meaning**: All systems operational
**Action**: None required

### Status: 🟠 Some Orange
**Check**:
1. Time of day (early morning may have delays)
2. Settlement period - if SP1-4, historical data may not be ready yet
3. Monitor for 30 minutes - may self-resolve

**Action**:
```bash
# Check IRIS pipeline status
ssh root@94.237.55.234 'ps aux | grep iris'

# Check recent logs
ssh root@94.237.55.234 'tail -50 /opt/iris-pipeline/logs/iris_uploader.log'
```

### Status: 🔴 Some/All Red
**Immediate Checks**:

1. **IRIS Pipeline Running?**
   ```bash
   ssh root@94.237.55.234 'systemctl status iris-client iris-uploader'
   ```

2. **Recent Data Files?**
   ```bash
   ssh root@94.237.55.234 'ls -lht /opt/iris-pipeline/iris-clients/python/iris_data/*/| head -20'
   ```

3. **BigQuery Upload Errors?**
   ```bash
   ssh root@94.237.55.234 'tail -100 /opt/iris-pipeline/logs/iris_uploader.log | grep ERROR'
   ```

**Common Issues**:

| Symptom | Cause | Fix |
|---------|-------|-----|
| All 🔴 red | IRIS pipeline stopped | Restart services on 94.237.55.234 |
| Gen Mix 🔴 only | FUELINST duplicates filtered | Expected - historical data used |
| Market 🔴 only | MID not publishing | Check Elexon IRIS subscription |
| BM Bids/Acceptances 🔴 | Service Bus issue | Check Azure connection |

---

## Related Files

### Main Scripts
- `update_live_dashboard_v2.py` - Main dashboard updater (includes freshness check)
- `bg_live_cron.sh` - Cron wrapper script
- `test_iris_status.py` - Standalone test script for freshness check

### Documentation
- `SPARKLINES_COMPLETE_SOLUTION.md` - Top KPI sparklines documentation
- `BM_METRICS_HEADERS_COMPLETE.md` - BM Metrics section documentation
- `IRIS_PIPELINE_RECOVERY_DEC17_2025.md` - IRIS pipeline troubleshooting

### IRIS Pipeline (AlmaLinux Server)
- `/opt/iris-pipeline/iris-clients/python/client.py` - Message downloader
- `/opt/iris-pipeline/iris_to_bigquery_unified.py` - BigQuery uploader
- `/opt/iris-pipeline/logs/iris_uploader.log` - Upload logs

---

## Example Status Messages

### Perfect Health (All Fresh)
```
🟢 IRIS: 74,680 rows today | 5🟢 0🟠 0🔴 | Key: 🟢<30m 🟠30-120m 🔴>120m
```

### Minor Delay (Some Aging)
```
🟠 IRIS: 68,234 rows today | 3🟢 2🟠 0🔴 | Key: 🟢<30m 🟠30-120m 🔴>120m
```

### Major Issues (Some Stale)
```
🔴 IRIS: 52,120 rows today | 2🟢 1🟠 2🔴 | Key: 🟢<30m 🟠30-120m 🔴>120m
```

### Complete Outage
```
🔴 IRIS: 15,200 rows today | 0🟢 0🟠 5🔴 | Key: 🟢<30m 🟠30-120m 🔴>120m
```

---

## Performance Metrics

### Query Performance
- **5 tables queried**: ~2-4 seconds total
- **Query cost**: Negligible (scans only today's data)
- **Frequency**: Every 5 minutes
- **Daily queries**: 288 × 5 = 1,440 table scans

### Data Volume Trends
- **Midnight-06:00**: ~15,000-25,000 rows (low activity)
- **06:00-12:00**: ~35,000-45,000 rows (morning ramp)
- **12:00-18:00**: ~55,000-65,000 rows (peak)
- **18:00-00:00**: ~70,000-80,000 rows (evening completion)

---

## Future Enhancements

### Potential Additions
1. **Per-stream detail view** - Click to expand individual table stats
2. **Historical trend chart** - Show ingestion rate over time
3. **Alert thresholds** - Email/SMS when streams go red
4. **Comparison to yesterday** - Show if volume is normal
5. **Estimated settlement period** - Predict when next SP will arrive

### Under Consideration
- Move to separate dashboard row with more detail
- Add sparkline showing row count per hour
- Include IRIS → BigQuery upload latency metric
- Show breakdown by message type (BOD, BOALF, etc.)

---

## Testing Commands

### Manual Freshness Check
```bash
cd /home/george/GB-Power-Market-JJ
python3 test_iris_status.py
```

**Expected Output**:
```
🕐 Testing IRIS ingestion status check...

📊 Overall Status: 🟢 ACTIVE
📈 Total rows ingested today: 74,680
🟢 Active streams: 5
🟠 Aging streams: 0
🔴 Stale streams: 0

💬 Dashboard message:
   🟢 IRIS: 74,680 rows today | 5🟢 0🟠 0🔴 | Key: 🟢<30m 🟠30-120m 🔴>120m

📋 Detailed breakdown:
   🟢 Gen Mix     :  1,280 rows (  -12 min)
   🟢 BM Bids     : 54,084 rows (  -15 min)
   🟢 Acceptances :  4,579 rows (  -15 min)
   🟢 Market      :     22 rows (  -12 min)
   🟢 Units       : 14,688 rows (-1455 min)
```

### Force Dashboard Update
```bash
cd /home/george/GB-Power-Market-JJ
python3 update_live_dashboard_v2.py
```

### Check Current Status in Sheet
```bash
python3 << 'EOF'
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
client = gspread.authorize(creds)

sheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA').worksheet('Live Dashboard v2')
print(f"A3: {sheet.acell('A3').value}")
EOF
```

---

## Version History

| Date | Version | Change |
|------|---------|--------|
| Dec 17, 2025 | 1.0 | Initial implementation - replaced warning system |
| Dec 17, 2025 | 1.1 | Fixed age calculation to use settlement period |
| Dec 17, 2025 | 1.2 | Added inline key to dashboard message |

---

## Contact & Support

**Maintainer**: George Major (george@upowerenergy.uk)
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
**Live Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

**For Issues**:
1. Check this documentation first
2. Review `/home/george/GB-Power-Market-JJ/logs/live_dashboard_v2_complete.log`
3. Test with `python3 test_iris_status.py`
4. Check IRIS pipeline on AlmaLinux server

---

*Last Updated: December 17, 2025 23:50 GMT*
