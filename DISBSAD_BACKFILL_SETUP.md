# DISBSAD Constraint Cost Backfill Setup

**Status:** ✅ Active (15-minute automated backfill)  
**Purpose:** Keep constraint cost data current since DISBSAD is NOT available via IRIS  
**Last Updated:** 9 December 2025

---

## Why DISBSAD Requires Backfill

### IRIS Limitation
**IRIS Subscribed Streams:**
- INDO, BOALF, BOD, FUELINST, FREQ, INDGEN, REMIT, WINDFOR

**NOT Available in IRIS:**
- ❌ **DISBSAD** (constraint costs)
- ❌ **DETS/B1770** (detailed system prices)
- ❌ **COSTS** (imbalance prices)

**Why:** Elexon doesn't stream DISBSAD via IRIS. Constraint costs require post-settlement calculations, making real-time streaming impractical.

**Solution:** Automated backfill from Elexon BMRS REST API every 15 minutes.

---

## Data Volume & Frequency

### BOALF (Constraint Actions)
- **~12,500 actions per day** (captured by IRIS ✅)
- **Peak: 20,823 actions/day** (Dec 4, 2025)
- **~194 unique units** involved daily
- **~207 GW** adjusted per day

### DISBSAD (Constraint Costs)
- **~228 cost records per day** (NOT in IRIS ❌)
- **£0.36M average daily cost**
- **Peak: £1.16M/day** (Dec 1, 2025)
- **Only 1.8% of BOALF actions have cost data**

**Business Impact:**
Without DISBSAD, you see 12,500 actions but don't know which ones cost money. Critical for:
- Regional constraint cost tracking
- VLP battery dispatch optimization during expensive periods
- Interconnector flow cost analysis

---

## Automated Backfill Configuration

### Script: `auto_backfill_disbsad_daily.py`

**What it does:**
- Fetches last 2 days of DISBSAD data every 15 minutes
- Uses `ingest_elexon_fixed.py` infrastructure
- Logs to `logs/disbsad_15min.log`
- Overwrites existing data to handle corrections/amendments

**Data range per run:**
- `start_date`: 2 days ago
- `end_date`: today
- Ensures no gaps even if API has delays

### Cron Schedule

```bash
# DISBSAD constraint cost backfill (every 15 minutes)
*/15 * * * * /usr/bin/python3 /home/george/GB-Power-Market-JJ/auto_backfill_disbsad_daily.py >> /home/george/GB-Power-Market-JJ/logs/cron_disbsad.log 2>&1
```

**Runs at:** :00, :15, :30, :45 every hour, 24/7

---

## Installation

### 1. Ensure logs directory exists
```bash
mkdir -p /home/george/GB-Power-Market-JJ/logs
```

### 2. Make script executable
```bash
chmod +x /home/george/GB-Power-Market-JJ/auto_backfill_disbsad_daily.py
```

### 3. Add to crontab
```bash
crontab -e
```

Add this line:
```cron
*/15 * * * * /usr/bin/python3 /home/george/GB-Power-Market-JJ/auto_backfill_disbsad_daily.py >> /home/george/GB-Power-Market-JJ/logs/cron_disbsad.log 2>&1
```

### 4. Verify cron installation
```bash
crontab -l | grep disbsad
```

---

## Monitoring

### Check if backfill is running
```bash
# View recent log entries
tail -f /home/george/GB-Power-Market-JJ/logs/disbsad_15min.log

# Check cron execution log
tail -f /home/george/GB-Power-Market-JJ/logs/cron_disbsad.log

# View today's activity
grep "$(date +%Y-%m-%d)" /home/george/GB-Power-Market-JJ/logs/disbsad_15min.log
```

### Verify data freshness
```bash
python3 << 'EOF'
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
query = """
SELECT 
    MAX(CAST(settlementDate AS DATE)) as latest_date,
    COUNT(*) as records_today
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
"""
df = client.query(query).to_dataframe()
print(f"Latest DISBSAD date: {df['latest_date'].values[0]}")
print(f"Records today: {df['records_today'].values[0]}")
EOF
```

### Expected behavior
- **Lag:** ~15-30 minutes (Elexon API delay + backfill interval)
- **Records per day:** 100-600 (varies by grid activity)
- **Log entries:** ~96 per day (every 15 min × 4 per hour × 24 hours)

---

## Troubleshooting

### Issue: No data appearing
```bash
# Check if cron is running the script
grep disbsad /var/log/cron

# Test manual execution
python3 /home/george/GB-Power-Market-JJ/auto_backfill_disbsad_daily.py

# Check BigQuery credentials
ls -la ~/inner-cinema-credentials.json
```

### Issue: High cost/rate limit errors
**Symptom:** API returns 429 errors  
**Solution:** DISBSAD backfill uses minimal API calls (~2-3 per run). Free tier sufficient.

### Issue: Duplicate data
**Not a problem:** Script uses `--overwrite` flag. BigQuery handles deduplication via `_hash_key` column.

---

## Cost Analysis

### API Usage
- **Calls per hour:** 4 (one every 15 min)
- **Calls per day:** 96
- **Calls per month:** ~2,880
- **Elexon API:** Free tier (no rate limits for DISBSAD)

### BigQuery Costs
- **Storage:** ~200 KB per day (~6 MB/month)
- **Inserts:** ~15,000 rows/month
- **Cost:** Free tier (well under 10 GB storage limit)

---

## Related Systems

### Similar Backfill Scripts
1. **`auto_backfill_costs_daily.py`** - System prices (bmrs_costs)
   - Runs: Daily at 6:30 AM
   - Why: COSTS also not in IRIS

2. **`backfill_constraints_gap.py`** - One-time gap fill (Oct 29 - Nov 3)
   - Purpose: Historical gap correction
   - Status: Complete (148,927 BOALF + 2,024 DISBSAD records loaded)

### Dashboard Integration
- **Script:** `update_bg_live_dashboard.py`
- **Section:** Geographic Constraints (rows 65-78)
- **Uses:** Combined BOALF (actions) + DISBSAD (costs) data
- **Update frequency:** Manual/on-demand (consider automating)

---

## Future Enhancements

1. **Request IRIS stream from Elexon**
   - Contact: iris-support@elexon.co.uk
   - Request: Add DISBSAD to subscription (if available)
   - Impact: Eliminate 15-min lag

2. **Add alerting**
   - Monitor backfill failures
   - Alert on data gaps > 1 hour
   - Track API error rates

3. **Optimize schedule**
   - Current: Every 15 min (96 runs/day)
   - Alternative: Every 30 min (48 runs/day) if 15-min lag acceptable
   - Consider: Peak hours only (16:00-19:00) if costs are time-specific

---

## Contact

**Maintainer:** George Major  
**Email:** george@upowerenergy.uk  
**Server:** AlmaLinux 94.237.55.234 (IRIS pipeline)  
**Repository:** https://github.com/GeorgeDoors888/GB-Power-Market-JJ

---

*Last Updated: 9 December 2025 - DISBSAD 15-minute backfill active*
