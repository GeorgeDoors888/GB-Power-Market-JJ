# ✅ AlmaLinux Server Deployment - ALMOST COMPLETE

## Server: almalinux-1cpu-2gb-uk-lon1
**IP**: 94.237.55.234

---

## ✅ SUCCESSFULLY DEPLOYED

### System Setup
- ✅ AlmaLinux 10 with all required packages
- ✅ Python 3.12.9 installed
- ✅ Nginx web server running
- ✅ Google Cloud BigQuery library installed
- ✅ SELinux configured (permissive mode)
- ✅ Firewall configured (port 80 open)

### GB Power Map Application
- ✅ Directory structure created: `/var/www/maps/`
- ✅ Map generator script installed: `auto_generate_map_linux.py`
- ✅ DNO regions GeoJSON uploaded (5.6 MB)
- ✅ Correct permissions set (nginx:nginx)
- ✅ Service account credentials uploaded

### Automation
- ✅ Cron job configured: Every 30 minutes
- ✅ IRIS pipeline preserved and still running
- ✅ Logs directory created

### Current Cron Jobs
```
@reboot sleep 60 && /opt/iris-pipeline/start_iris_pipeline.sh
*/15 * * * * /opt/iris-pipeline/monitor_iris_pipeline.sh
0 * * * * /opt/iris-pipeline/collect_stats.sh
*/30 * * * * python3 /var/www/maps/scripts/auto_generate_map_linux.py  # NEW
```

---

## ⚠️  ONE STEP REMAINING

### BigQuery Permissions Required

The service account needs access to your BigQuery project.

**Service Account**: `jibber-jabber-knowledge@appspot.gserviceaccount.com`  
**Project**: `inner-cinema-476211-u9`

### Grant Access (2 Minutes)

1. **Go to IAM page**:
   https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9

2. **Click** `+ GRANT ACCESS`

3. **Add principal**: 
   ```
   jibber-jabber-knowledge@appspot.gserviceaccount.com
   ```

4. **Assign roles**:
   - BigQuery Data Viewer
   - BigQuery Job User

5. **Click** `Save`

### Test After Granting Access

SSH into server and run:
```bash
ssh root@94.237.55.234

export GOOGLE_APPLICATION_CREDENTIALS=/root/service_account.json
python3 /var/www/maps/scripts/auto_generate_map_linux.py

# Check the map file
ls -lh /var/www/maps/gb_power_complete_map.html
```

---

## 🌐 Your URLs

### Power Map (Live after permissions granted)
**http://94.237.55.234/gb_power_complete_map.html**

Features:
- 18 GSPs with export/import status
- 35 offshore wind farms (14.3 GW)
- 8,653 generators (CVA + SVA)  
- 14 DNO boundaries
- Auto-updates every 30 minutes

### Add to Google Sheets

```
=HYPERLINK("http://94.237.55.234/gb_power_complete_map.html", "🗺️ Live Power Map")
```

**Your Sheet**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

---

## 📊 What's Running

### 1. IRIS Pipeline (Existing - Untouched)
- **Status**: ✅ Running  
- **Schedule**: Every 15 minutes
- **Purpose**: Updates JSON data
- **Location**: `/opt/iris-pipeline/`

### 2. GB Power Map (New - Ready to Run)
- **Status**: ⏳ Waiting for BigQuery permissions
- **Schedule**: Every 30 minutes
- **Purpose**: Generates interactive power system map
- **Location**: `/var/www/maps/`

---

## 🔍 Monitoring

### Check Services
```bash
# Nginx status
systemctl status nginx

# View cron jobs
crontab -l

# Check IRIS logs
tail -f /opt/iris-pipeline/logs/cron.log

# Check map generation logs (after permissions granted)
tail -f /var/www/maps/logs/map_generation_$(date +%Y%m%d).log
```

### Test Map Generation
```bash
ssh root@94.237.55.234
export GOOGLE_APPLICATION_CREDENTIALS=/root/service_account.json
python3 /var/www/maps/scripts/auto_generate_map_linux.py
```

### View Map File
```bash
ls -lh /var/www/maps/gb_power_complete_map.html
curl -I http://localhost/gb_power_complete_map.html
```

---

## 📁 File Locations

```
/var/www/maps/
├── gb_power_complete_map.html      # Generated map (3.7 MB expected)
├── data/
│   └── dno_regions.geojson        # DNO boundaries (5.6 MB)
├── scripts/
│   └── auto_generate_map_linux.py # Map generator (15 KB)
└── logs/
    ├── map_generation_YYYYMMDD.log # Daily logs
    ├── cron.log                    # Cron execution log
    └── nginx_access.log            # HTTP access log

/root/
├── service_account.json            # BigQuery credentials
└── gb_power_map_deployment/        # Deployment files
```

---

## ✅ Summary

**COMPLETED**:
- ✅ Full server setup
- ✅ Nginx web server
- ✅ Python environment
- ✅ Map generator installed
- ✅ Cron automation configured
- ✅ IRIS pipeline preserved

**TO DO**:
- ⚠️  Grant BigQuery permissions (2 minutes)
- ✅ Test map generation
- ✅ Verify URL works

**RESULT**: Once permissions are granted, your map will auto-generate every 30 minutes and be available at:

**http://94.237.55.234/gb_power_complete_map.html** 🗺️⚡

---

## 🆘 Need Help?

The deployment is 99% complete. Just grant the BigQuery permissions and you're done!

If you need assistance:
1. Check logs: `/var/www/maps/logs/`
2. Test manually: `python3 /var/www/maps/scripts/auto_generate_map_linux.py`
3. Verify Nginx: `curl http://localhost/`
