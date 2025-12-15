# 🚀 IRIS Pipeline Quick Reference Card

**Print this and keep it visible!**

---

## ⚡ Emergency Commands

```bash
# SSH to server
ssh root@94.237.55.234

# Check if pipeline is running
screen -ls
# Should show: iris_client, iris_uploader

# Restart pipeline
cd /opt/iris-pipeline && ./start_iris_pipeline.sh

# View live logs
tail -f /opt/iris-pipeline/logs/iris_uploader.log

# Check data freshness (local Mac)
python3 check_iris_data.py

# View alerts
cat /opt/iris-pipeline/alerts.txt
```

---

## ✅ The 5 Golden Rules

### 1. NEVER query only IRIS tables
```sql
-- ❌ WRONG
SELECT * FROM bmrs_fuelinst_iris WHERE DATE(settlementDate) = CURRENT_DATE()

-- ✅ CORRECT (with historical fallback)
SELECT * FROM (
  SELECT * FROM bmrs_fuelinst WHERE settlementDate < CURRENT_DATE()
  UNION ALL
  SELECT * FROM bmrs_fuelinst_iris WHERE settlementDate >= CURRENT_DATE() - 1
)
```

### 2. ALWAYS use time-based lookback
```sql
-- ❌ WRONG
WHERE DATE(settlementDate) = CURRENT_DATE()

-- ✅ CORRECT  
WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
```

### 3. ALWAYS check data freshness
```python
# Check age before using
age_hours = (datetime.now() - latest_time).total_seconds() / 3600
if age_hours > 2:
    logging.warning(f"⚠️ Data is {age_hours:.1f}h old!")
```

### 4. ALWAYS have monitoring
- ✅ Health checks every 5 minutes
- ✅ Auto-restart on failure
- ✅ Alerts logged

### 5. ALWAYS test failures
- Test at midnight transition
- Test with IRIS pipeline stopped
- Test with stale data

---

## 📊 Table Reference

| Data Type | Historical | IRIS | Query Pattern |
|-----------|-----------|------|---------------|
| Fuel Gen | `bmrs_fuelinst` | `bmrs_fuelinst_iris` | UNION both |
| Interconnectors | `bmrs_indo` | `bmrs_indo_iris` | UNION both |
| Outages | `bmrs_remit_unavailability` | (same)* | Single table |
| Individual Gen | `bmrs_indgen` | `bmrs_indgen_iris` | UNION both |
| Frequency | `bmrs_freq` | `bmrs_freq_iris` | UNION both |

*REMIT messages go to `bmrs_remit_unavailability` (NOT `bmrs_remit_iris`)

---

## 🔍 Health Check Status

```bash
# View recent health checks
ssh root@94.237.55.234 'tail -20 /opt/iris-pipeline/logs/health_check.log'

# Expected output every 5 minutes:
# ✅ Health check passed

# If you see alerts:
# ⚠️ IRIS UPLOADER IS DOWN! → Check screen -ls
# ⚠️ BigQuery data is stale! → Check if processing backlog
```

---

## 🚨 Troubleshooting

### Issue: "Retrieved 0 fuel types"

**Quick Fix:**
```bash
# 1. Check if uploader is running
ssh root@94.237.55.234 'screen -ls'

# 2. If missing iris_uploader, restart
ssh root@94.237.55.234 'cd /opt/iris-pipeline && ./start_iris_pipeline.sh'

# 3. Check data freshness
python3 check_iris_data.py

# 4. Wait 30 minutes if processing backlog
```

### Issue: Dashboard shows stale data

**Quick Fix:**
```bash
# 1. Run freshness check
python3 check_iris_data.py

# 2. If IRIS stale, check if uploader is running
ssh root@94.237.55.234 'ps aux | grep iris_to_bigquery'

# 3. Check uploader logs
ssh root@94.237.55.234 'tail -50 /opt/iris-pipeline/logs/iris_uploader.log'

# 4. Restart if needed
ssh root@94.237.55.234 'cd /opt/iris-pipeline && ./start_iris_pipeline.sh'
```

---

## 📁 Key Files

### On Server (94.237.55.234)
```
/opt/iris-pipeline/
├── start_iris_pipeline.sh       # Restart script
├── health_check.sh               # Health monitoring
├── alerts.txt                    # Alert log
├── logs/
│   ├── iris_client.log           # Download activity
│   ├── iris_uploader.log         # Upload activity
│   └── health_check.log          # Health check results
└── iris_data/                    # JSON files (temp storage)
```

### On Local Mac
```
~/GB Power Market JJ/
├── check_iris_data.py                        # Data freshness checker
├── IRIS_PIPELINE_SAFEGUARDS_MANDATORY.md     # THE RULES (read first!)
├── IRIS_INCIDENT_RESOLUTION_NOV11_2025.md    # Full incident report
└── realtime_dashboard_updater.py             # Dashboard script
```

---

## 🎯 Daily Checks (Quick)

```bash
# Morning check (30 seconds)
python3 check_iris_data.py

# Expected output:
# ✅ GOOD - All tables <2h old
# ⚠️ STALE - Some tables 2-24h old (investigate)
# ❌ FAILED - Tables >24h old (restart needed)
```

---

## 📞 If Nothing Else Works

```bash
# Nuclear option: Full restart
ssh root@94.237.55.234 << 'EOF'
screen -S iris_client -X quit
screen -S iris_uploader -X quit
sleep 5
cd /opt/iris-pipeline
./start_iris_pipeline.sh
screen -ls
EOF

# Then wait 5 minutes and check
python3 check_iris_data.py
```

---

## 📚 Documentation Index

1. **IRIS_PIPELINE_SAFEGUARDS_MANDATORY.md** - Production rules ⭐
2. **IRIS_INCIDENT_RESOLUTION_NOV11_2025.md** - Full incident report
3. **IRIS_PIPELINE_DIAGNOSIS_NOV11_2025.md** - Detailed diagnosis
4. **STOP_DATA_ARCHITECTURE_REFERENCE.md** - Table schemas
5. **check_iris_data.py** - Data freshness script

**Read in this order:** 1 → 5 → 2 → 4 → 3

---

## ✅ System is Healthy When

- [ ] `screen -ls` shows iris_client + iris_uploader
- [ ] `python3 check_iris_data.py` shows all ✅ GOOD
- [ ] Health check log shows ✅ passed (last 15 min)
- [ ] No recent entries in alerts.txt
- [ ] Dashboard shows current data

**Check these daily at 9am!**

---

**Quick Access:**
- Dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
- Server: `ssh root@94.237.55.234`
- Logs: `/opt/iris-pipeline/logs/`

**Updated:** 2025-11-11  
**Status:** 🟢 **ACTIVE & MONITORED**
