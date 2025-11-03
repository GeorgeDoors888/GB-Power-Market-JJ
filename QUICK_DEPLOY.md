# 🚀 GB Power Map - Quick Deploy

## Server Info
- **Name**: almalinux-1cpu-2gb-uk-lon1  
- **IP**: 94.237.55.234  
- **OS**: AlmaLinux 10  
- **Map URL**: http://94.237.55.234/gb_power_complete_map.html

## Deploy in 4 Commands

```bash
# 1. Upload package
scp gb_power_map_deployment.zip credentials.json root@94.237.55.234:/root/

# 2. SSH and extract
ssh root@94.237.55.234
unzip gb_power_map_deployment.zip && cd gb_power_map_deployment

# 3. Deploy
sudo ./deploy.sh

# 4. Configure credentials
export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json
echo 'export GOOGLE_APPLICATION_CREDENTIALS=/root/credentials.json' >> ~/.bashrc
python3 /var/www/maps/scripts/auto_generate_map_linux.py
```

## Result
✅ Map at: http://94.237.55.234/gb_power_complete_map.html  
✅ Auto-updates: Every 30 minutes  
✅ Shows: 18 GSPs, 35 offshore wind farms, 8,653 generators  

## Add to Google Sheets
```
=HYPERLINK("http://94.237.55.234/gb_power_complete_map.html", "🗺️ View Live GB Power Map")
```

## Monitor
```bash
tail -f /var/www/maps/logs/map_generation_$(date +%Y%m%d).log
```

## Files Ready
- ✅ gb_power_map_deployment.zip (1.0 MB) - **Upload this**
- ✅ ALMALINUX_AUTOMATION_COMPLETE.md - Full documentation
- ✅ update_dashboard_with_server_url.py - Google Sheets integration
