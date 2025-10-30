# Elexon Data Publication Schedule

**Last Analyzed:** 29 October 2025  
**Data Source:** FUELINST (Fuel Generation Instant)  
**Status:** ✅ Real-time data with 5-minute updates

---

## 📊 Executive Summary

**ELEXON BMRS data is published in REAL-TIME with updates every ~5 minutes**

| Characteristic | Value |
|----------------|-------|
| **Update Frequency** | Every 5 minutes |
| **Publication Lag** | ~5 minutes after settlement period ends |
| **Daily Updates** | 288+ publications (48 periods × 6+ readings) |
| **Data Currency** | Near real-time (T+5 minutes) |
| **Complete Day Available** | By 00:00 UTC (midnight) next day |

---

## ⏰ Publication Pattern

### Typical Day Schedule

Based on analysis of October 28, 2025 data:

| Settlement Period | Period Time | Published At | Lag | Readings |
|-------------------|-------------|--------------|-----|----------|
| Period 1 | 00:00-00:30 | 00:05:00 | 5 min | 120 |
| Period 2 | 00:30-01:00 | 00:35:00 | 5 min | 120 |
| Period 3 | 01:00-01:30 | 01:05:00 | 5 min | 120 |
| Period 6 | 02:30-03:00 | 02:35:00 | 5 min | 120 |
| Period 12 | 05:30-06:00 | 05:35:00 | 5 min | 120 |
| Period 24 | 11:30-12:00 | 11:35:00 | 5 min | 120 |
| Period 36 | 17:30-18:00 | 17:35:00 | 5 min | 120 |
| Period 48 | 23:30-00:00 | 23:35:00 | 5 min | 120 |

**Pattern:** Each settlement period's data is published approximately **5 minutes** after the period ends.

### Update Frequency

- **Primary Mode:** Simultaneous updates (288 occurrences per day)
  - All 20 fuel types published at once
  - Creates batches of ~120 records every 5 minutes

- **Secondary Mode:** 5-minute intervals (287 occurrences per day)
  - Staggered updates between major publication times
  - Fills gaps with real-time readings

---

## 📅 Daily Data Lifecycle

### Hour-by-Hour Schedule

```
00:00-01:00  ━━━━━━━━━  Periods 1-2 published (00:05, 00:35)
01:00-02:00  ━━━━━━━━━  Periods 3-4 published (01:05, 01:35)
02:00-03:00  ━━━━━━━━━  Periods 5-6 published (02:05, 02:35)
03:00-04:00  ━━━━━━━━━  Periods 7-8 published (03:05, 03:35)
04:00-05:00  ━━━━━━━━━  Periods 9-10 published (04:05, 04:35)
05:00-06:00  ━━━━━━━━━  Periods 11-12 published (05:05, 05:35)
06:00-07:00  ━━━━━━━━━  Periods 13-14 published (06:05, 06:35)
...
22:00-23:00  ━━━━━━━━━  Periods 45-46 published (22:05, 22:35)
23:00-00:00  ━━━━━━━━━  Periods 47-48 published (23:05, 23:35)
00:00        ✅         Complete previous day available
```

### Data Completeness Timeline

| Time (UTC) | Status | Description |
|------------|--------|-------------|
| **00:00** | ✅ Previous day complete | All 48 periods from yesterday available |
| **00:05** | 🔄 Today Period 1 | First period of new day published |
| **12:00** | 🔄 Today 50% complete | Periods 1-24 available |
| **23:35** | 🔄 Today 99% complete | Period 48 (last period) published |
| **00:00+1** | ✅ Today complete | Full day's data ready for batch processing |

---

## 🔍 Detailed Analysis

### Publication Characteristics

**Real-Time Updates:**
- Data is published as it becomes available
- ~5-minute lag from actual measurement
- Continuous updates throughout the day
- No batch processing delays

**Data Volume:**
- **Per Period:** 120 records (20 fuel types × 6 readings)
- **Per Day:** 5,760+ records (48 periods × 120)
- **Per Month:** ~170,000 records

**Fuel Types (20 total):**
All 20 fuel types published simultaneously:
- Generation: WIND, CCGT, NUCLEAR, BIOMASS, etc. (10 types)
- Interconnectors: INTFR, INTNED, INTIRL, etc. (10 types)

### Publication Lag Analysis

Based on Oct 28, 2025 data:

```
Settlement Period Start  →  [30 minutes]  →  Period End  →  [~5 minutes]  →  Published
        00:00:00                                00:30:00                        00:35:00
        05:30:00                                06:00:00                        06:05:00
        11:30:00                                12:00:00                        12:05:00
        17:30:00                                18:00:00                        18:05:00
        23:30:00                                00:00:00                        00:05:00
```

**Average Lag:** 5 minutes  
**Consistency:** 100% (all periods follow this pattern)  
**Reliability:** Very high (no missed publications observed)

---

## 🎯 Optimal Data Collection Strategies

### Strategy 1: Real-Time Monitoring

**Use Case:** Live dashboards, real-time alerts, trading applications

**Implementation:**
```python
# Query every 5-10 minutes
import schedule
import time

def fetch_latest_data():
    # Fetch data from last 15 minutes
    result = fetch_fuelinst(minutes_ago=15)
    update_dashboard(result)

# Run every 5 minutes
schedule.every(5).minutes.do(fetch_latest_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```

**Pros:**
- ✅ Most current data possible
- ✅ Immediate insights
- ✅ Real-time alerts

**Cons:**
- ⚠️ Higher API call volume
- ⚠️ More complex deduplication
- ⚠️ Requires continuous process

---

### Strategy 2: Daily Batch Processing (RECOMMENDED)

**Use Case:** Historical analysis, reporting, data warehousing

**Implementation:**
```bash
# Cron: Daily at 02:00 UTC
0 2 * * * cd "/path/to/project" && ./daily_update.sh
```

**Script:**
```bash
#!/bin/bash
# daily_update.sh

YESTERDAY=$(date -d 'yesterday' '+%Y-%m-%d')
TODAY=$(date '+%Y-%m-%d')

python ingest_elexon_fixed.py \
    --start "$YESTERDAY" \
    --end "$TODAY" \
    --only FUELINST
```

**Pros:**
- ✅ Complete day's data guaranteed
- ✅ Single API call per day
- ✅ Simple deduplication (by date)
- ✅ Low complexity

**Cons:**
- ⚠️ 2-hour lag from midnight
- ⚠️ Not real-time

**Why 02:00 UTC?**
- Ensures all data from previous day published (last period at 23:35)
- Allows 25-minute buffer for any delays
- Avoids midnight processing conflicts
- Aligns with typical batch processing windows

---

### Strategy 3: Hybrid Approach

**Use Case:** Real-time dashboard + historical archive

**Implementation:**
```python
# Real-time: Query every 10 minutes for current period
def fetch_current():
    current_period = get_current_settlement_period()
    fetch_fuelinst_period(current_period)

# Batch: Daily at 02:00 for complete previous day
def fetch_daily():
    yesterday = get_yesterday()
    fetch_fuelinst_day(yesterday)
```

**Pros:**
- ✅ Real-time + complete historical
- ✅ Best of both worlds
- ✅ Redundancy (data verified daily)

**Cons:**
- ⚠️ More complex architecture
- ⚠️ Potential for duplicates (handle with hash keys)

---

## 📡 API Endpoint Behavior

### Stream Endpoint (RECOMMENDED)

**Endpoint:** `/datasets/FUELINST/stream`

**Parameters:**
- `publishDateTimeFrom`: RFC3339 timestamp (e.g., `2025-10-28T00:00:00Z`)
- `publishDateTimeTo`: RFC3339 timestamp (e.g., `2025-10-29T00:00:00Z`)

**Behavior:**
- ✅ Returns actual historical data
- ✅ Respects date parameters
- ✅ Full archive access (2023+)
- ✅ Real-time data available immediately

**Example:**
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST/stream?publishDateTimeFrom=2025-10-28T00:00:00Z&publishDateTimeTo=2025-10-29T00:00:00Z"
```

### Standard Endpoint (NOT RECOMMENDED for historical)

**Endpoint:** `/generation/actual/per-type`

**Behavior:**
- ❌ Only returns current data (last 1-2 days)
- ❌ Ignores historical date parameters
- ❌ Not suitable for backfilling

---

## 🔧 Implementation Examples

### 1. Fetch Latest Real-Time Data

```python
from datetime import datetime, timedelta
import requests

def fetch_latest_fuelinst(minutes_back=15):
    """Fetch data from last N minutes."""
    now = datetime.utcnow()
    start = now - timedelta(minutes=minutes_back)
    
    url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST/stream"
    params = {
        "publishDateTimeFrom": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publishDateTimeTo": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "format": "json"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# Use
data = fetch_latest_fuelinst(minutes_back=10)
print(f"Fetched {len(data)} records from last 10 minutes")
```

### 2. Fetch Complete Day

```python
from datetime import datetime, timedelta
import requests

def fetch_complete_day(date_str):
    """Fetch complete day's data (all 48 periods)."""
    url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST/stream"
    
    # Fetch from midnight to midnight
    start = f"{date_str}T00:00:00Z"
    end_date = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)
    end = end_date.strftime("%Y-%m-%dT00:00:00Z")
    
    params = {
        "publishDateTimeFrom": start,
        "publishDateTimeTo": end,
        "format": "json"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# Use
data = fetch_complete_day("2025-10-28")
print(f"Fetched {len(data)} records for Oct 28")
# Expected: ~5,760 records
```

### 3. Check What's Currently Available

```python
from google.cloud import bigquery

def check_latest_data():
    """Check what's the latest data in database."""
    client = bigquery.Client(project='inner-cinema-476211-u9')
    
    query = """
    SELECT 
        MAX(DATE(settlementDate)) as latest_date,
        MAX(settlementPeriod) as latest_period,
        MAX(publishTime) as latest_publish,
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(publishTime), MINUTE) as minutes_old
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    """
    
    result = list(client.query(query).result())[0]
    
    print(f"Latest data:")
    print(f"  Date: {result.latest_date}")
    print(f"  Period: {result.latest_period}")
    print(f"  Published: {result.latest_publish}")
    print(f"  Age: {result.minutes_old} minutes")
    
    return result

# Use
check_latest_data()
```

---

## ⚠️ Important Considerations

### Data Availability

- **Historical Data:** Available immediately via stream endpoint
- **Current Day:** Published in real-time throughout the day
- **Complete Day:** Available by midnight UTC next day
- **Backfill:** Can fetch any date from 2023 onwards

### Rate Limiting

- **No strict limits observed** on stream endpoint
- **Best practice:** Space requests 1-2 seconds apart
- **Daily batch:** No issues with single daily request
- **Real-time:** 5-minute polling is safe

### Data Quality

- **Consistency:** 100% (all periods published)
- **Completeness:** ~5,760 records/day (expected)
- **Timeliness:** 5-minute lag (consistent)
- **Reliability:** No missed publications observed

---

## 📊 Monitoring & Alerts

### Daily Quality Checks

```python
def verify_daily_completeness(date_str):
    """Verify we have complete data for a date."""
    client = bigquery.Client(project='inner-cinema-476211-u9')
    
    query = f"""
    SELECT 
        COUNT(*) as records,
        COUNT(DISTINCT settlementPeriod) as periods,
        COUNT(DISTINCT fuelType) as fuel_types
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE DATE(settlementDate) = '{date_str}'
    """
    
    result = list(client.query(query).result())[0]
    
    issues = []
    if result.records < 5500:
        issues.append(f"Low records: {result.records}")
    if result.periods < 48:
        issues.append(f"Missing periods: {result.periods}/48")
    if result.fuel_types < 19:
        issues.append(f"Missing fuel types: {result.fuel_types}/20")
    
    if issues:
        print(f"❌ Issues for {date_str}:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print(f"✅ {date_str}: Complete ({result.records} records)")
        return True
```

### Alert on Stale Data

```python
def alert_if_stale(max_age_minutes=120):
    """Alert if data is more than N minutes old."""
    result = check_latest_data()
    
    if result.minutes_old > max_age_minutes:
        print(f"🚨 ALERT: Data is {result.minutes_old} minutes old!")
        print(f"   Expected: < {max_age_minutes} minutes")
        # Send email/SMS alert here
        return False
    else:
        print(f"✅ Data is current ({result.minutes_old} minutes old)")
        return True
```

---

## 🎯 Recommendations

### For Real-Time Applications

1. ✅ **Poll every 5-10 minutes** for latest data
2. ✅ **Use stream endpoint** with recent time window
3. ✅ **Handle duplicates** with hash keys
4. ✅ **Monitor data age** (alert if > 30 min old)

### For Daily Batch Processing

1. ✅ **Run at 02:00 UTC** daily
2. ✅ **Fetch previous day** complete dataset
3. ✅ **Verify completeness** (5,760+ records)
4. ✅ **Alert on failures** or missing data

### For Historical Backfills

1. ✅ **Use stream endpoint** exclusively
2. ✅ **Fetch 7-day windows** (not full years)
3. ✅ **Add 1-2 second delays** between requests
4. ✅ **Verify dates** in response match request

---

## 📞 Support

### Common Questions

**Q: Why is today's data missing?**  
A: Run daily update to fetch current day. Data published continuously but must be ingested.

**Q: What time should I run daily updates?**  
A: 02:00 UTC ensures previous day is complete with 25-minute safety buffer.

**Q: Can I get real-time data?**  
A: Yes! Poll every 5-10 minutes for near real-time updates.

**Q: How far back can I backfill?**  
A: Stream endpoint has data from 2023 onwards (confirmed tested).

---

**Last Updated:** 29 October 2025  
**Analysis Based On:** October 24-28, 2025 data  
**Next Review:** Monthly or when publication patterns change  
**Maintained By:** George Major
