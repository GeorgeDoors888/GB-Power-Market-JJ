# 📱 IRIS Overnight Monitor - Quick Mobile Reference

**Status:** 🟢 ACTIVE  
**Started:** Oct 30, 18:21 GMT  
**Check Every:** 5 minutes

---

## 🚦 Quick Status Check

```bash
# One command to check everything
tail -50 iris_overnight_monitor.log
```

---

## ✅ Expected Status

- Processes: ✅ Running
- Data lag: < 10 min
- Errors: ~100 (normal - datasets without tables)
- File backlog: 25K-50K

---

## ❌ If Something's Wrong

### Process crashed?
```bash
# Check what's running
ps aux | grep -E "81929|596"

# Restart if needed
cd /Users/georgemajor/GB\ Power\ Market\ JJ
./check_iris_health.sh
```

### Data stopped flowing?
```bash
# Check latest data
bq query --use_legacy_sql=false \
'SELECT MAX(ingested_utc) FROM 
`inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`'
```

---

## 📊 Morning Checklist (Oct 31)

```bash
# 1. How many checks ran?
grep "Check #" iris_overnight_monitor.log | tail -1

# 2. Any alerts?
cat iris_overnight_alerts.log

# 3. Final status?
tail -50 iris_overnight_monitor.log

# 4. Processes still running?
ps aux | grep -E "81929|596"
```

**Expect:** ~144 checks, 0 alerts, both processes running

---

## 🎯 Success = 
- ✅ Both PIDs running
- ✅ Data lag < 10 min
- ✅ Records growing
- ✅ < 10 alerts

---

**Don't worry about high error count (~100) - that's normal for datasets without tables!**

Sleep well! 🌙
