# Dashboard V3 - Quick Command Reference

## 🚀 Essential Commands

### Test Complete System
```bash
cd ~/GB-Power-Market-JJ
python3 python/dashboard_v3_auto_refresh.py
```
**Expected**: ✅ SUCCESS in ~4 seconds, 202 cells updated

### Install Auto-Refresh (15-min cron)
```bash
./install_dashboard_v3_cron.sh
```

### Monitor Live Updates
```bash
tail -f logs/dashboard_v3_cron.log
```

### Manual Refresh Only DNO_Map
```bash
python3 python/populate_dno_map_complete.py
```

### Manual Refresh Only Dashboard KPIs
```bash
python3 python/update_dashboard_v3_kpis.py
```

---

## 📊 Google Sheets Access

**Dashboard V3**: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit#gid=SHEET_ID

**Key Cells**:
- `F3` - Selected DNO (dropdown with 14 regions)
- `B3` - Time range selector
- `F10:L10` - KPI values (updated by script)

---

## 🔧 Cron Management

### View Cron Jobs
```bash
crontab -l
```

### Edit Cron Manually
```bash
crontab -e
```

### Remove Dashboard V3 Cron
```bash
crontab -l | grep -v "dashboard_v3_auto_refresh" | crontab -
```

### Cron Entry (auto-installed)
```
*/15 * * * * /usr/local/bin/python3 /Users/georgemajor/GB-Power-Market-JJ/python/dashboard_v3_auto_refresh.py >> /Users/georgemajor/GB-Power-Market-JJ/logs/dashboard_v3_cron.log 2>&1
```

---

## 🐛 Troubleshooting

### Check BigQuery Access
```bash
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9', location='US'); print('✅ Connected')"
```

### Check Google Sheets Access
```bash
python3 -c "from google.oauth2 import service_account; from googleapiclient.discovery import build; creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json'); service = build('sheets', 'v4', credentials=creds); print('✅ Sheets API ready')"
```

### View Last 20 Cron Executions
```bash
tail -20 logs/dashboard_v3_cron.log
```

### Force Refresh Now
```bash
python3 python/dashboard_v3_auto_refresh.py && echo "✅ Refresh complete"
```

---

## 📈 Performance Benchmarks

| Operation | Time | BigQuery Queries | Sheets API Calls |
|-----------|------|------------------|------------------|
| Full refresh | 3.66s | 3 | 3 |
| DNO_Map only | 2.66s | 3 | 1 |
| KPIs only | 1.00s | 0 | 2 |

---

## 🎯 Common Tasks

### Change Selected DNO
1. Open spreadsheet
2. Click cell F3
3. Select DNO from dropdown (e.g., "NGED-WMID")
4. Wait 0-15 minutes for auto-refresh OR run manually:
   ```bash
   python3 python/update_dashboard_v3_kpis.py
   ```

### Add New DNO Region
1. Edit `DNO_REGIONS` list in scripts:
   - `populate_dno_map_complete.py`
   - `dashboard_v3_auto_refresh.py`
2. Add entry: `{"code": "24", "name": "NEW-DNO", "lat": 52.0, "lng": -1.0}`
3. Run: `python3 python/populate_dno_map_complete.py`

### Update DUoS Rates
1. Edit `duos_dict` in scripts (search for "placeholder")
2. Update rates for specific DNO codes
3. Run refresh script

---

## 📁 Key Files

```
~/GB-Power-Market-JJ/
├── python/
│   ├── populate_dno_map_complete.py      # Populate all 14 DNOs
│   ├── update_dashboard_v3_kpis.py       # Update Dashboard KPIs
│   └── dashboard_v3_auto_refresh.py      # Combined (for cron)
├── logs/
│   ├── dashboard_v3_cron.log             # Cron execution log
│   └── dashboard_v3_auto_refresh.log     # Detailed script log
├── install_dashboard_v3_cron.sh          # Cron installer
├── inner-cinema-credentials.json         # Service account key
└── DASHBOARD_V3_PYTHON_SOLUTION_COMPLETE.md  # Full documentation
```

---

## ⚡ One-Line Installers

### Complete Setup (from scratch)
```bash
cd ~/GB-Power-Market-JJ && python3 python/populate_dno_map_complete.py && ./install_dashboard_v3_cron.sh
```

### Quick Test All
```bash
cd ~/GB-Power-Market-JJ && python3 python/dashboard_v3_auto_refresh.py && echo "✅ All systems operational"
```

---

**Status**: ✅ Production Ready  
**Last Updated**: December 4, 2025
