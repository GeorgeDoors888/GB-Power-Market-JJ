# 🚀 AlmaLinux Server - Power Map + IRIS

## Server: almalinux-1cpu-2gb-uk-lon1
**IP**: 94.237.55.234

---

## What's Running

### 1. 🗺️ GB Power Map (NEW - Auto-updates every 30 min)
- **URL**: http://94.237.55.234/gb_power_complete_map.html
- Shows 18 GSPs, 35 offshore wind farms, 8,653 generators
- Queries BigQuery for latest data
- Cron: `*/30 * * * *`

### 2. 📡 IRIS Pipeline (EXISTING - Keeps running)
- Already updating JSON data every 5 minutes
- **Not touched by this deployment**
- Continues running as before

---

## 🚀 Deploy in 3 Commands

```bash
# 1. SSH to server
ssh root@94.237.55.234

# 2. Extract deployment
cd /root
unzip -o gb_power_map_deployment_updated.zip
cd gb_power_map_deployment

# 3. Deploy (only installs Power Map, leaves IRIS alone)
sudo ./deploy_power_map_only.sh
```

---

## ⚙️ What Gets Installed

```
/var/www/maps/
├── gb_power_complete_map.html     # Generated map (auto-updates)
├── data/
│   └── dno_regions.geojson       # DNO boundaries
├── scripts/
│   └── auto_generate_map_linux.py # Map generator
└── logs/
    ├── map_generation_YYYYMMDD.log
    └── cron.log
```

**IRIS files**: Not touched, continue running

---

## 🌐 Access

**Power Map**: http://94.237.55.234/gb_power_complete_map.html

Add to your Google Sheets:
```
=HYPERLINK("http://94.237.55.234/gb_power_complete_map.html", "🗺️ Live Power Map")
```

**Your Sheet**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

---

## 📊 Automation Schedule

```
┌─────────────────────────────────────┐
│  GB Power Map                       │
│  ├─ Every 30 minutes                │
│  ├─ 00:00, 00:30, 01:00, etc.     │
│  └─ Cron: */30 * * * *             │
├─────────────────────────────────────┤
│  IRIS Pipeline                      │
│  ├─ Every 5 minutes (existing)     │
│  └─ Not modified                    │
└─────────────────────────────────────┘
```

---

## 🔍 Monitoring

```bash
# Power Map logs
tail -f /var/www/maps/logs/map_generation_$(date +%Y%m%d).log

# Check cron jobs
crontab -l

# Test map generation
python3 /var/www/maps/scripts/auto_generate_map_linux.py

# Check Nginx
systemctl status nginx

# View map file
ls -lh /var/www/maps/gb_power_complete_map.html
```

---

## ✅ Quick Checklist

- [ ] SSH to 94.237.55.234
- [ ] Extract deployment package
- [ ] Run `deploy_power_map_only.sh`
- [ ] Configure Google Cloud credentials
- [ ] Test: `python3 /var/www/maps/scripts/auto_generate_map_linux.py`
- [ ] Visit: http://94.237.55.234/gb_power_complete_map.html
- [ ] Verify: IRIS still running normally
- [ ] Update Google Sheets with URL

---

## 🎉 Result

✅ **GB Power Map**: Auto-updates every 30 min  
✅ **IRIS Pipeline**: Continues running unchanged  
✅ **Public URL**: Accessible from anywhere  
✅ **Google Sheets Ready**: Add hyperlink  

**Map URL**: http://94.237.55.234/gb_power_complete_map.html
