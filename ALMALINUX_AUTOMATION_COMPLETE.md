# 🚀 GB Power Map - AlmaLinux Automation Complete

## 📦 What's Been Created

You now have a **complete deployment package** for hosting your GB Power Map on your AlmaLinux UpCloud server with full automation.

---

## 🎯 System Overview

```
┌─────────────────────────────────────────────────────────┐
│  AlmaLinux Server (94.237.55.234)                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Nginx Web Server (Port 80)                       │  │
│  │  - Serves: gb_power_complete_map.html             │  │
│  │  - Public: http://94.237.55.234/...               │  │
│  └───────────────────────────────────────────────────┘  │
│                         ↑                                │
│                         │                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Python Script (Cron: every 30 min)              │  │
│  │  - Queries: BigQuery GSP/Generator data          │  │
│  │  - Generates: Interactive Leaflet map            │  │
│  │  - Updates: Map with latest data                 │  │
│  └───────────────────────────────────────────────────┘  │
│                         ↑                                │
│                         │                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Google BigQuery                                  │  │
│  │  - GSP flows (bmrs_indgen/inddem)               │  │
│  │  - Offshore wind (35 farms)                      │  │
│  │  - All generators (8,653 total)                  │  │
│  │  - DNO boundaries (14 regions)                   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Google Sheets Dashboard                                │
│  - Hyperlink: "View Live GB Power Map"                  │
│  - URL: http://94.237.55.234/gb_power_complete_map.html │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Files Created

### Deployment Package (Ready to Upload)

✅ **gb_power_map_deployment.zip** (1.0 MB)
   - Contains all necessary files
   - Ready to upload to server

Inside the package:

1. **auto_generate_map_linux.py** (15 KB)
   - Queries BigQuery for latest data
   - Generates complete interactive map
   - Saves to /var/www/maps/
   - Logs all operations

2. **dno_regions.geojson** (5.6 MB)
   - 14 DNO boundary polygons
   - Used for map overlay

3. **setup_nginx_web_server.sh** (4.5 KB)
   - Installs & configures Nginx
   - Creates directory structure
   - Configures firewall
   - Tests web server

4. **setup_cron_job.sh** (3.8 KB)
   - Sets up automated task
   - Runs every 30 minutes
   - Configures logging
   - Tests execution

5. **deploy.sh** (1.1 KB)
   - One-command deployment
   - Installs all prerequisites
   - Sets up everything automatically

6. **README.md** (9.9 KB)
   - Complete documentation
   - Step-by-step instructions
   - Troubleshooting guide

7. **QUICK_START.txt** (534 B)
   - Quick reference
   - Essential commands

8. **requirements.txt** (30 B)
   - Python dependencies

### Local Files (For Your Use)

✅ **ALMALINUX_DEPLOYMENT_GUIDE.md** (9.9 KB)
   - Comprehensive deployment guide
   - All server details
   - Step-by-step instructions
   - Troubleshooting section

✅ **update_dashboard_with_server_url.py** (2.3 KB)
   - Updates Google Sheets
   - Adds map hyperlink
   - Automatic integration

✅ **package_for_almalinux.sh** (1.7 KB)
   - Creates deployment package
   - (Already executed)

---

## 🚀 Quick Deployment Guide

### 1. Upload Package to Server

```bash
# From your Mac
cd "/Users/georgemajor/GB Power Market JJ"

# Upload deployment package
scp gb_power_map_deployment.zip root@94.237.55.234:/root/

# Upload BigQuery credentials
scp credentials.json root@94.237.55.234:/root/
```

### 2. Deploy on Server

```bash
# SSH into server
ssh root@94.237.55.234

# Extract package
unzip gb_power_map_deployment.zip
cd gb_power_map_deployment

# Run one-command deployment
sudo ./deploy.sh
```

### 3. Configure Credentials

```bash
# Still on server
export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json
echo 'export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json' >> ~/.bashrc
source ~/.bashrc

# Test BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✓ BigQuery OK')"
```

### 4. Test the Map

```bash
# Generate map manually first time
python3 /var/www/maps/scripts/auto_generate_map_linux.py

# Check if it worked
ls -lh /var/www/maps/gb_power_complete_map.html

# Test web access
curl -I http://localhost/gb_power_complete_map.html
```

### 5. Open in Browser

**Visit**: http://94.237.55.234/gb_power_complete_map.html

You should see:
- Interactive map of Great Britain
- 5 toggleable layers (DNO, GSP, Offshore Wind, CVA, SVA)
- All 8,653 generators with clustering
- GSP flow indicators (blue = exporter, orange = importer)
- Latest data timestamp

### 6. Update Google Sheets

```bash
# Back on your Mac
cd "/Users/georgemajor/GB Power Market JJ"
python3 update_dashboard_with_server_url.py
```

Or manually add to your Google Sheet:
```
=HYPERLINK("http://94.237.55.234/gb_power_complete_map.html", "🗺️ View Live GB Power Map")
```

---

## ⚙️ Automation Details

### Cron Schedule

The map automatically regenerates **every 30 minutes**:

```
*/30 * * * * python3 /var/www/maps/scripts/auto_generate_map_linux.py
```

**Run times**: 00:00, 00:30, 01:00, 01:30, 02:00, etc.

### What Happens Each Run

1. Script queries BigQuery for latest data
2. Retrieves:
   - Latest GSP flows (generation & demand)
   - All offshore wind farms (35)
   - All CVA plants (1,581)
   - All SVA generators (7,072)
   - DNO boundaries (14 regions)
3. Generates HTML with embedded Leaflet map
4. Saves to /var/www/maps/gb_power_complete_map.html
5. Nginx serves the updated file
6. Your Google Sheets link always shows latest version

---

## 📊 Map Features

### 5 Interactive Layers

1. **DNO Boundaries** (14 regions)
   - Green polygons
   - Clickable for DNO name

2. **GSP Flow Points** (18 GSPs)
   - Blue circles = Exporters (generation > demand)
   - Orange circles = Importers (demand > generation)
   - Size = magnitude of net flow
   - Shows generation, demand, net flow

3. **Offshore Wind Farms** (35 sites)
   - Cyan circles
   - Size = capacity (MW)
   - Total: 14.3 GW capacity

4. **CVA Power Plants** (1,581 large generators)
   - Color-coded by fuel type
   - Clustered for performance
   - Shows name, fuel, capacity, DNO, GSP

5. **SVA Generators** (7,072 small generators)
   - Color-coded by fuel type
   - Clustered for performance
   - Shows name, fuel, capacity, DNO, GSP

### Fuel Type Colors

- 🟢 Green = Wind
- 🟡 Yellow = Solar
- 🟠 Orange = Gas
- 🟣 Purple = Nuclear
- 🔵 Blue = Hydro
- 🟢 Light Green = Biomass
- ⚫ Gray = Other/Oil

---

## 🔍 Monitoring

### Check Map Status

```bash
# SSH into server
ssh root@94.237.55.234

# View map file
ls -lh /var/www/maps/gb_power_complete_map.html

# Check generation logs
tail -f /var/www/maps/logs/map_generation_$(date +%Y%m%d).log

# Check cron execution
tail -f /var/www/maps/logs/cron.log

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
```

### View Cron Jobs

```bash
# List all cron jobs
crontab -l

# Check cron service
systemctl status crond

# View recent cron executions
sudo grep CRON /var/log/cron | tail -20
```

---

## 🌐 Access URLs

### Live Map
**Primary**: http://94.237.55.234/gb_power_complete_map.html

### Test Page
**Test**: http://94.237.55.234/

### Google Sheets
Add this formula to your dashboard:
```
=HYPERLINK("http://94.237.55.234/gb_power_complete_map.html", "View Live GB Power Map")
```

---

## 🔐 Security Notes

### Firewall Configuration

Ensure port 80 is open:

```bash
# On server
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

Also check **UpCloud firewall** in web console:
- Go to Server → Firewall
- Ensure rule: Allow TCP port 80 from 0.0.0.0/0

### BigQuery Credentials

```bash
# Secure credentials file
chmod 600 /root/credentials.json

# Credentials should have minimal permissions:
# - BigQuery Data Viewer
# - BigQuery Job User
```

### Optional: Add SSL/HTTPS

```bash
# Install Certbot
sudo dnf install certbot python3-certbot-nginx

# Get certificate (requires domain name)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo systemctl enable certbot-renew.timer
```

---

## 🆘 Troubleshooting

### Map Not Accessible

```bash
# Check Nginx status
systemctl status nginx

# Restart if needed
sudo systemctl restart nginx

# Test configuration
sudo nginx -t

# Check firewall
sudo firewall-cmd --list-all
```

### Map Not Updating

```bash
# Check cron service
systemctl status crond

# Verify cron job exists
crontab -l | grep map

# Check recent logs
tail -50 /var/www/maps/logs/map_generation_$(date +%Y%m%d).log

# Test manual generation
python3 /var/www/maps/scripts/auto_generate_map_linux.py
```

### BigQuery Errors

```bash
# Test credentials
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print(list(client.query('SELECT 1 as test').result()))"

# Check environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Set if missing
export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R nginx:nginx /var/www/maps

# Fix permissions
sudo chmod -R 755 /var/www/maps
sudo chmod +x /var/www/maps/scripts/auto_generate_map_linux.py
```

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Package uploaded to server
- [ ] All files in correct locations
- [ ] Nginx installed and running
- [ ] Map file exists and is recent
- [ ] Map accessible via HTTP
- [ ] Cron job scheduled
- [ ] Logs being created
- [ ] BigQuery connection working
- [ ] Google Sheets updated with link

---

## 📞 Next Steps

1. **Deploy Now**
   ```bash
   scp gb_power_map_deployment.zip root@94.237.55.234:/root/
   ssh root@94.237.55.234
   unzip gb_power_map_deployment.zip
   cd gb_power_map_deployment
   sudo ./deploy.sh
   ```

2. **Configure Credentials**
   ```bash
   scp credentials.json root@94.237.55.234:/root/
   ssh root@94.237.55.234
   export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json
   ```

3. **Test the Map**
   ```bash
   python3 /var/www/maps/scripts/auto_generate_map_linux.py
   # Then visit: http://94.237.55.234/gb_power_complete_map.html
   ```

4. **Update Google Sheets**
   ```bash
   python3 update_dashboard_with_server_url.py
   ```

5. **Monitor**
   ```bash
   tail -f /var/www/maps/logs/map_generation_$(date +%Y%m%d).log
   ```

---

## 🎉 Summary

You now have:

✅ **Automated GB Power Map** hosted on AlmaLinux server  
✅ **Live data** from BigQuery (updated every 30 minutes)  
✅ **5 interactive layers** (DNO, GSP, Offshore, CVA, SVA)  
✅ **8,653 generators** with full details  
✅ **Public URL** accessible from anywhere  
✅ **Google Sheets integration** ready  
✅ **Complete documentation** and monitoring  

**URL**: http://94.237.55.234/gb_power_complete_map.html

Enjoy your automated live GB Power System visualization! 🗺️⚡
