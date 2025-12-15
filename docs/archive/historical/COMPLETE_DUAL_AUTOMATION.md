# 🚀 AlmaLinux Server - Complete Dual Automation

## What This Does

Your AlmaLinux server (94.237.55.234) will now run **TWO automated jobs**:

### 1. 🗺️ GB Power Map (Every 30 Minutes)
- Queries BigQuery for latest GSP flows, generators, offshore wind
- Generates interactive map with all 8,653 generators
- URL: **http://94.237.55.234/gb_power_complete_map.html**

### 2. 🏢 Property Companies Extraction (Daily at 2 AM)
- Queries BigQuery for all property-owning companies
- Extracts ~568,000 company registration numbers
- URL: **http://94.237.55.234/property_companies.csv**

---

## 📦 Updated Deployment Package

The package now includes:

```
gb_power_map_deployment/
├── auto_generate_map_linux.py       # Power map generator
├── extract_property_companies.sh    # Property companies extractor (NEW)
├── deploy_complete.sh               # Complete setup script (NEW)
├── setup_dual_cron_jobs.sh         # Dual cron job setup (NEW)
├── setup_nginx_web_server.sh        # Nginx setup
├── setup_cron_job.sh                # Original cron setup
├── dno_regions.geojson              # DNO boundaries
├── requirements.txt                 # Python deps
└── README.md                        # Documentation
```

---

## 🚀 Quick Deploy (5 Commands)

### Step 1: Upload Updated Package

```bash
# Upload to AlmaLinux server
scp gb_power_map_deployment.zip root@94.237.55.234:/root/
```

### Step 2: SSH and Extract

```bash
ssh root@94.237.55.234
cd /root
unzip -o gb_power_map_deployment.zip
cd gb_power_map_deployment
```

### Step 3: Configure Google Cloud Credentials

```bash
# Set BigQuery credentials
export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json
echo 'export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json' >> ~/.bashrc
source ~/.bashrc

# Initialize gcloud (for bq command)
gcloud auth activate-service-account --key-file=/root/credentials.json
gcloud config set project inner-cinema-476211-u9
```

### Step 4: Run Complete Deployment

```bash
# This installs EVERYTHING
sudo ./deploy_complete.sh
```

### Step 5: Test Both Scripts

```bash
# Test power map generation
python3 /var/www/maps/scripts/auto_generate_map_linux.py

# Test property companies extraction
bash /var/www/property_companies/scripts/extract_property_companies.sh

# Check outputs
ls -lh /var/www/maps/gb_power_complete_map.html
ls -lh /var/www/property_companies/data/property_owning_companies_clean.csv
```

---

## 🌐 Access Your Data

### Power Map (Live, Auto-Updates Every 30 Min)
**http://94.237.55.234/gb_power_complete_map.html**

Features:
- 18 GSPs with export/import status
- 35 offshore wind farms (14.3 GW)
- 8,653 generators (CVA + SVA)
- 14 DNO boundaries
- Interactive layers

### Property Companies CSV (Updates Daily at 2 AM)
**http://94.237.55.234/property_companies.csv**

Contains:
- ~568,000 company registration numbers
- Companies that own property in UK
- 8-character format (e.g., 00000086)
- Direct download link

---

## ⚙️ Automation Schedule

```
┌─────────────────────────────────────────────┐
│  Cron Jobs Running 24/7                     │
├─────────────────────────────────────────────┤
│  Power Map:                                 │
│    */30 * * * *  (Every 30 minutes)        │
│    Next runs: 00:00, 00:30, 01:00, etc.   │
│                                             │
│  Property Companies:                        │
│    0 2 * * *  (Daily at 2:00 AM)          │
│    Next run: Tomorrow 2:00 AM              │
└─────────────────────────────────────────────┘
```

---

## 📊 Google Sheets Integration

Add both to your Google Sheets dashboard:

```
# Power Map (Live)
=HYPERLINK("http://94.237.55.234/gb_power_complete_map.html", "🗺️ View Live GB Power Map")

# Property Companies CSV (Daily)
=HYPERLINK("http://94.237.55.234/property_companies.csv", "🏢 Download Property Companies")
```

Or run the Python script:
```bash
python3 update_dashboard_with_server_url.py
```

---

## 🔍 Monitoring

### View Real-Time Logs

```bash
# Power map generation log
tail -f /var/www/maps/logs/map_generation_$(date +%Y%m%d).log

# Property companies extraction log
tail -f /var/www/property_companies/logs/extraction_$(date +%Y%m%d).log

# Cron execution logs
tail -f /var/www/maps/logs/cron.log
tail -f /var/www/property_companies/logs/daily_cron.log
```

### Check Status

```bash
# View cron jobs
crontab -l

# Check Nginx status
systemctl status nginx

# Check recent files
ls -lh /var/www/maps/gb_power_complete_map.html
ls -lh /var/www/property_companies/data/property_owning_companies_clean.csv

# Test URLs
curl -I http://localhost/gb_power_complete_map.html
curl -I http://localhost/property_companies.csv
```

---

## 📁 File Structure on Server

```
/var/www/
├── maps/
│   ├── gb_power_complete_map.html           # Generated map
│   ├── data/
│   │   └── dno_regions.geojson             # DNO boundaries
│   ├── scripts/
│   │   └── auto_generate_map_linux.py      # Generator
│   └── logs/
│       ├── map_generation_YYYYMMDD.log     # Daily logs
│       └── cron.log                         # Cron log
│
└── property_companies/
    ├── data/
    │   └── property_owning_companies_clean.csv  # Extracted companies
    ├── scripts/
    │   └── extract_property_companies.sh    # Extractor
    └── logs/
        ├── extraction_YYYYMMDD.log          # Daily logs
        └── daily_cron.log                   # Cron log
```

---

## 🆘 Troubleshooting

### Power Map Not Updating

```bash
# Check BigQuery access
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✓ OK')"

# Check credentials
echo $GOOGLE_APPLICATION_CREDENTIALS

# Run manually
python3 /var/www/maps/scripts/auto_generate_map_linux.py

# Check logs
tail -50 /var/www/maps/logs/map_generation_$(date +%Y%m%d).log
```

### Property Companies Not Extracting

```bash
# Check if bq command works
bq --version

# Check gcloud auth
gcloud auth list

# Test BigQuery query
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM `inner-cinema-476211-u9.companies_house.land_registry_uk_companies`'

# Run manually
bash /var/www/property_companies/scripts/extract_property_companies.sh

# Check logs
tail -50 /var/www/property_companies/logs/extraction_$(date +%Y%m%d).log
```

### Cron Jobs Not Running

```bash
# Check cron service
systemctl status crond

# View cron jobs
crontab -l

# Check cron logs
sudo grep CRON /var/log/cron | tail -20

# Reinstall cron jobs
./setup_dual_cron_jobs.sh
```

---

## ✅ Success Checklist

- [ ] Package uploaded to server
- [ ] Extracted to /root/gb_power_map_deployment
- [ ] Google Cloud credentials configured
- [ ] deploy_complete.sh executed successfully
- [ ] Power map generated manually (test)
- [ ] Property companies extracted manually (test)
- [ ] Both URLs accessible from browser
- [ ] Cron jobs installed
- [ ] Logs being created
- [ ] Google Sheets updated with links

---

## 🎉 What You Now Have

✅ **Live Power Map** - Auto-updates every 30 minutes  
✅ **Property Companies List** - Updates daily at 2 AM  
✅ **Public URLs** - Accessible from anywhere  
✅ **Fully Automated** - No manual intervention needed  
✅ **Comprehensive Logging** - Track all operations  
✅ **Google Sheets Ready** - Easy integration  

### Your URLs:
- **Power Map**: http://94.237.55.234/gb_power_complete_map.html
- **Companies CSV**: http://94.237.55.234/property_companies.csv
- **Google Sheets**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

---

## 📞 Next Steps

1. **Upload the updated package:**
   ```bash
   scp gb_power_map_deployment.zip root@94.237.55.234:/root/
   ```

2. **SSH and deploy:**
   ```bash
   ssh root@94.237.55.234
   cd /root
   unzip -o gb_power_map_deployment.zip
   cd gb_power_map_deployment
   sudo ./deploy_complete.sh
   ```

3. **Test everything:**
   - Visit http://94.237.55.234/gb_power_complete_map.html
   - Download http://94.237.55.234/property_companies.csv

4. **Update Google Sheets:**
   - Add hyperlinks to both URLs
   - Share with your team

Enjoy your dual-automated AlmaLinux server! 🚀
