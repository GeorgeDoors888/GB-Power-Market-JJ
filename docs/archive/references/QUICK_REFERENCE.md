# 🎯 Quick Reference Card

## Daily Commands (Copy-Paste Ready)

### Check Health Status
```bash
ssh root@94.237.55.15 "cat /opt/arbitrage/reports/data/health.json | python3 -m json.tool"
```

### View Recent Logs
```bash
ssh root@94.237.55.15 "tail -30 /opt/arbitrage/logs/arbitrage.log"
```

### Check Next Run Time
```bash
ssh root@94.237.55.15 "systemctl list-timers | grep arbitrage"
```

### Check Last Run Status
```bash
ssh root@94.237.55.15 "systemctl status arbitrage.service | head -15"
```

### Force Manual Run
```bash
ssh root@94.237.55.15 "systemctl start arbitrage.service && sleep 5 && tail -20 /opt/arbitrage/logs/arbitrage.log"
```

### List Recent Reports
```bash
ssh root@94.237.55.15 "ls -lht /opt/arbitrage/reports/data/*.csv | head -5"
```

### Download Latest CSV
```bash
scp root@94.237.55.15:/opt/arbitrage/reports/data/price_data_*.csv ~/Downloads/
```

### Check Disk Usage
```bash
ssh root@94.237.55.15 "du -sh /opt/arbitrage/reports /opt/arbitrage/logs"
```

---

## Systemd Timer Commands

### View Timer Configuration
```bash
ssh root@94.237.55.15 "systemctl cat arbitrage.timer"
```

### Stop Timer (Pause Automation)
```bash
ssh root@94.237.55.15 "systemctl stop arbitrage.timer"
```

### Start Timer (Resume Automation)
```bash
ssh root@94.237.55.15 "systemctl start arbitrage.timer"
```

### Disable Timer (Prevent Auto-Start on Boot)
```bash
ssh root@94.237.55.15 "systemctl disable arbitrage.timer"
```

### Enable Timer (Auto-Start on Boot)
```bash
ssh root@94.237.55.15 "systemctl enable arbitrage.timer"
```

---

## Troubleshooting Commands

### View Full Service Logs
```bash
ssh root@94.237.55.15 "journalctl -u arbitrage.service --no-pager | tail -100"
```

### Test BigQuery Authentication
```bash
ssh root@94.237.55.15 "cd /opt/arbitrage && GOOGLE_APPLICATION_CREDENTIALS=/opt/arbitrage/service-account.json python3 -c 'from google.cloud import bigquery; c=bigquery.Client(); print(f\"✅ Connected to project: {c.project}\")'"
```

### Check Service Account Permissions
```bash
gcloud projects get-iam-policy inner-cinema-476211-u9 --flatten="bindings[].members" --filter="bindings.members:arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com" --format="table(bindings.role)"
```

### Check Data Freshness in BigQuery
```bash
ssh root@94.237.55.15 "cd /opt/arbitrage && GOOGLE_APPLICATION_CREDENTIALS=/opt/arbitrage/service-account.json python3 <<'PY'
from google.cloud import bigquery
c = bigquery.Client()
result = c.query('''
  SELECT MAX(DATE(settlementDate)) as latest_date 
  FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid\`
''').to_dataframe()
print(f\"Latest data: {result['latest_date'][0]}\")
PY"
```

---

## File Locations

```
/opt/arbitrage/battery_arbitrage.py       # Main script
/opt/arbitrage/service-account.json        # Credentials (chmod 600)
/opt/arbitrage/logs/arbitrage.log          # Execution logs
/opt/arbitrage/reports/data/health.json    # Health status
/opt/arbitrage/reports/data/*.csv          # Price data
/opt/arbitrage/reports/data/*.json         # Summaries

/etc/systemd/system/arbitrage.service      # Service definition
/etc/systemd/system/arbitrage.timer        # Timer schedule
/etc/logrotate.d/arbitrage                 # Log rotation
```

---

## Key Information

| Setting | Value |
|---------|-------|
| **Server IP** | 94.237.55.15 |
| **SSH User** | root |
| **Schedule** | Daily at 04:00 UTC |
| **GCP Project** | inner-cinema-476211-u9 |
| **Dataset** | uk_energy_prod |
| **Table** | bmrs_mid |
| **Service Account** | arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com |
| **Query Cost** | ~5.7 MB per run (~$0.0009/month) |

---

## Emergency Commands

### Stop Everything
```bash
ssh root@94.237.55.15 "systemctl stop arbitrage.timer && systemctl stop arbitrage.service && echo '⛔ All stopped'"
```

### Restart Everything
```bash
ssh root@94.237.55.15 "systemctl daemon-reload && systemctl restart arbitrage.timer && systemctl start arbitrage.service && echo '✅ Restarted'"
```

### Backup Current State
```bash
ssh root@94.237.55.15 "tar -czf /tmp/arbitrage-backup-$(date +%Y%m%d).tar.gz /opt/arbitrage /etc/systemd/system/arbitrage.* /etc/logrotate.d/arbitrage"
scp root@94.237.55.15:/tmp/arbitrage-backup-*.tar.gz ~/Downloads/
```

---

## Monitoring Checklist

Weekly checks:
- [ ] Verify health.json shows `"ok": true`
- [ ] Check last_run_utc is within 24 hours
- [ ] Confirm rows_retrieved > 0
- [ ] Review logs for any warnings

Monthly checks:
- [ ] Check disk usage (should be < 100MB)
- [ ] Verify log rotation is working
- [ ] Review BigQuery costs in GCP Console
- [ ] Test manual run works

---

*Keep this handy for quick reference!* 📋
