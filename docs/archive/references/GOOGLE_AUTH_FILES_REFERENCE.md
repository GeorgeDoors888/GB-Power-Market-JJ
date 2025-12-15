# 🔐 Google Authentication & Integration Files Reference

> **Purpose**: Universal/Permanent authentication for Google Sheets, BigQuery, and Drive  
> **Auth Method**: Service Account (no OAuth prompts, works in cron jobs)  
> **Date**: November 11, 2025

---

## 📋 Credential Files (Service Accounts)

### **1. Primary Credentials** ⭐
```bash
inner-cinema-credentials.json
```
- **Project**: inner-cinema-476211-u9
- **Permissions**: Full access to BigQuery, Sheets, Drive
- **Used by**: 90% of scripts
- **Security**: chmod 600 (owner read/write only)

### **2. Alternative Credentials**
```bash
arbitrage-bq-key.json          # Some dashboard scripts
smart_grid_credentials.json    # Backup/legacy
oauth_credentials.json         # OAuth (less common)
client_credentials.json        # OAuth client config
```

---

## 🔧 Core Integration Scripts (Service Account Auth)

### **Dashboard Auto-Updater** 🏆
**Most Important Production Script**

```python
# realtime_dashboard_updater.py
from google.oauth2 import service_account
import gspread

# Runs every 5 minutes via cron
# Sheet: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
# Credentials: inner-cinema-credentials.json
```

**Usage**: 
```bash
python3 realtime_dashboard_updater.py  # Manual test
tail -f logs/dashboard_updater.log     # Monitor auto-updates
```

---

### **GSP Wind Analysis** 🌬️
```python
# gsp_auto_updater.py
# gsp_wind_analysis.py

# Both use service_account.Credentials
# Auto-updates wind generation by GSP region
# Credentials: inner-cinema-credentials.json
```

**Fixed Nov 10, 2025**: Removed 9 deprecation warnings

---

### **Battery VLP Tracking** 🔋
```python
# complete_vlp_battery_analysis.py
# battery_profit_analysis.py
# create_bess_vlp_sheet.py

# All use: 
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
```

**Results**: 104 batteries, £12.76M top revenue

---

## 📊 All Files Using Google Auth (By Category)

### **BigQuery + Sheets (Dashboard Scripts)**
1. **realtime_dashboard_updater.py** - Auto-refresh every 5 min ⭐
2. **update_dashboard_complete.py** - Manual full refresh
3. **update_dashboard_full.py** - Legacy updater
4. **final_dashboard_update.py** - One-time updates
5. **update_outages.py** - Outage data
6. **update_outages_realtime.py** - Real-time outages

### **GSP (Grid Supply Point) Scripts**
7. **gsp_auto_updater.py** - Main GSP auto-updater ⭐
8. **gsp_wind_analysis.py** - Wind by region ⭐
9. **format_gsp_display.py** - Formatting
10. **add_gsp_to_dashboard.py** - Add GSP data

### **Dashboard Design & Formatting**
11. **enhance_dashboard_design.py** - Visual improvements
12. **improve_dashboard_design.py** - Layout fixes
13. **final_polish.py** - Final touches
14. **lock_dashboard_design.py** - Protect layout
15. **flag_fixer.py** - Fix interconnector flags
16. **fix_interconnector_flags.py** - Flag utilities

### **Analysis & Charts**
17. **populate_chart_data.py** - Prepare chart data
18. **check_chart_data.py** - Verify charts
19. **deploy_and_execute_charts.py** - Deploy charts
20. **add_dashboard_charts.py** - Add new charts

### **Battery & VLP Analysis**
21. **complete_vlp_battery_analysis.py** - VLP revenue tracking ⭐
22. **battery_profit_analysis.py** - Profit analysis ⭐
23. **battery_charging_cost_analysis.py** - Cost modeling
24. **create_bess_vlp_sheet.py** - Create BESS sheet
25. **enhance_bess_vlp_sheet.py** - Enhance BESS sheet
26. **test_bess_vlp_lookup.py** - Test lookups

### **Statistical Analysis**
27. **advanced_statistical_analysis.py** - 8 analyses (NEW Nov 10)
28. **advanced_stats_simple.py** - Simplified version (NEW Nov 10)

### **Diagnostics & Testing**
29. **test_sheets_api.py** - Test Sheets API
30. **check_dashboard_issues.py** - Diagnose issues
31. **diagnose_dashboard.py** - Deep diagnostics
32. **verify_dashboard.py** - Verify data
33. **read_actual_dashboard.py** - Read structure

### **Tools Directory**
34. **tools/refresh_live_dashboard.py** - Live refresh
35. **tools/update_dashboard_display.py** - Update display
36. **tools/debug_dashboard_read.py** - Debug reads
37. **tools/fix_dashboard_comprehensive.py** - Comprehensive fixes

### **Fuel & Interconnector Data**
38. **fix_dashboard_graphics.py** - Fix graphics
39. **clean_fuel_graphics.py** - Clean fuel data
40. **complete_graphics_cleanup.py** - Full cleanup
41. **check_ic_data.py** - Check interconnector data
42. **check_flags_source.py** - Check flag source

### **Dashboard Sections**
43. **add_unavailability_to_dashboard.py** - Add unavailability
44. **update_unavailability.py** - Update unavailability
45. **auto_refresh_outages.py** - Auto-refresh outages
46. **add_dashboard_analysis.py** - Add analysis section
47. **remove_analysis_section.py** - Remove analysis

### **Layout & Structure**
48. **redesign_dashboard_layout.py** - Redesign layout
49. **comprehensive_dashboard_redesign.py** - Major redesign
50. **verify_clean_layout.py** - Verify layout
51. **show_dashboard_layout.py** - Display structure
52. **check_dashboard_structure.py** - Check structure

### **Specialized Updates**
53. **update_dashboard_header.py** - Update header
54. **add_freshness_indicator.py** - Add freshness indicator
55. **add_flags_manual.py** - Manual flag updates
56. **verify_flags.py** - Verify flags
57. **test_flag_write.py** - Test flag writes

---

## 🔑 Authentication Pattern (Used by ALL Scripts)

### **Modern Pattern** (Recommended)
```python
from google.oauth2.service_account import Credentials
import gspread
from google.cloud import bigquery

# 1. Set environment variable
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# 2. Create credentials with scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery'
]

creds = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=SCOPES
)

# 3. Authorize clients
gc = gspread.authorize(creds)  # Sheets
bq = bigquery.Client(project='inner-cinema-476211-u9', credentials=creds)  # BigQuery
```

### **Legacy Pattern** (Still works)
```python
from oauth2client.service_account import ServiceAccountCredentials
import gspread

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    'inner-cinema-credentials.json',
    scope
)

client = gspread.authorize(creds)
```

---

## 🚀 Deployment Script

**File**: `deploy_google_integration.sh`

**Purpose**: 
- Verify credentials
- Test BigQuery connection
- Test Sheets connection
- Create datasets
- Configure permissions

**Usage**:
```bash
# Make executable (IMPORTANT!)
chmod +x deploy_google_integration.sh

# Run deployment
./deploy_google_integration.sh
```

**Current Status**: ⚠️ **Not executable** - needs `chmod +x`

---

## 📊 Google Sheets Dashboard

### **Main Dashboard**
- **Sheet ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
- **URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
- **Auto-refresh**: Every 5 minutes via `realtime_dashboard_updater.py`

### **Worksheets**:
- **Live Dashboard** - Real-time metrics
- **GSP Wind** - Wind by region
- **BESS VLP** - Battery revenue
- **Outages** - Generator outages
- **Interconnector Flags** - Cross-border flows

---

## 🗄️ BigQuery Configuration

### **Projects**:
1. **inner-cinema-476211-u9** ⭐ (PRIMARY - use this!)
   - Location: US
   - Datasets: `uk_energy_prod`, `uk_energy_analysis`
   - 174+ tables

2. **jibber-jabber-knowledge** ❌ (DO NOT USE)
   - Limited permissions
   - Missing `bigquery.jobs.create`

### **Key Tables**:
```sql
-- Historical data (2020-present)
inner-cinema-476211-u9.uk_energy_prod.bmrs_bod        -- Bid-offer data (391M rows)
inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst   -- Fuel generation
inner-cinema-476211-u9.uk_energy_prod.bmrs_freq       -- Grid frequency
inner-cinema-476211-u9.uk_energy_prod.bmrs_mid        -- Market prices

-- Real-time data (last 24-48h)
inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris
inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris
```

---

## ⚙️ Cron Jobs (Automated Tasks)

### **Active Cron Jobs**:
```bash
# Dashboard auto-refresh (every 5 minutes)
*/5 * * * * cd ~/GB\ Power\ Market\ JJ && python3 realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1

# GSP wind analysis (every 15 minutes)
*/15 * * * * cd ~/GB\ Power\ Market\ JJ && python3 gsp_auto_updater.py >> logs/gsp_updater.log 2>&1
```

**Check status**:
```bash
tail -f logs/dashboard_updater.log
tail -f logs/gsp_updater.log
```

---

## 🔒 Security & Permissions

### **Service Account Email**:
```
inner-cinema@inner-cinema-476211-u9.iam.gserviceaccount.com
```

### **Required Permissions**:
- **BigQuery**: `roles/bigquery.admin` or `bigquery.jobs.create`
- **Sheets**: Shared with service account email (Editor access)
- **Drive**: Can create/edit files

### **Best Practices**:
1. **Never commit credentials to git**
   ```bash
   # Already in .gitignore
   *credentials*.json
   *.json
   ```

2. **Secure permissions**
   ```bash
   chmod 600 inner-cinema-credentials.json
   ```

3. **Use environment variables**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"
   ```

---

## 🧪 Testing Authentication

### **Quick Test**:
```bash
# Test BigQuery
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ BigQuery OK')"

# Test Sheets
python3 -c "import gspread; from google.oauth2.service_account import Credentials; creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets']); gc = gspread.authorize(creds); print('✅ Sheets OK')"
```

### **Full Test Script**:
```bash
python3 test_sheets_api.py  # Tests Sheets connection
python3 test_bess_vlp_lookup.py  # Tests data lookup
```

---

## 📝 Recent Changes (Nov 10-11, 2025)

### **Fixed Deprecation Warnings** ✅
- **gsp_auto_updater.py**: 5 warnings fixed (lines 280, 292, 298, 299, 310)
- **gsp_wind_analysis.py**: 4 warnings fixed (lines 242-245)
- Changed from: `update('A55', [[value]])`
- Changed to: `update(range_name='A55', values=[[value]])`

### **Added Error Handling** ✅
- 50+ try-except blocks across all scripts
- Connection retries with exponential backoff
- Graceful degradation on failures

### **New Scripts** ✅
- **advanced_statistical_analysis.py**: 8 statistical analyses
- **battery_charging_cost_analysis.py**: Cost modeling for 5 durations
- **GOOGLE_AUTH_FILES_REFERENCE.md**: This document!

---

## 📖 Documentation Files

- **PROJECT_CONFIGURATION.md** - All settings & config
- **STOP_DATA_ARCHITECTURE_REFERENCE.md** - Data schema reference
- **DEPLOYMENT_COMPLETE.md** - Full deployment guide
- **CHATGPT_INSTRUCTIONS.md** - ChatGPT proxy setup
- **GOOGLE_AUTH_FILES_REFERENCE.md** - This file ⭐

---

## 🆘 Troubleshooting

### **Problem: "Permission Denied"**
**Solution**: 
```bash
# 1. Check credentials exist
ls -la inner-cinema-credentials.json

# 2. Check permissions
chmod 600 inner-cinema-credentials.json

# 3. Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"
```

### **Problem: "Dataset not found in europe-west2"**
**Solution**: Always use `location="US"` not `"europe-west2"`
```python
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
```

### **Problem: "Access Denied: jibber-jabber-knowledge"**
**Solution**: Use `inner-cinema-476211-u9` project instead

### **Problem: "deploy_google_integration.sh: command not found"**
**Solution**:
```bash
chmod +x deploy_google_integration.sh
./deploy_google_integration.sh
```

---

## 🎯 Quick Reference Commands

```bash
# Manual dashboard refresh
python3 realtime_dashboard_updater.py

# GSP wind update
python3 gsp_auto_updater.py

# Battery analysis
python3 battery_profit_analysis.py

# VLP tracking
python3 complete_vlp_battery_analysis.py

# Statistical analysis (NEW)
python3 advanced_statistical_analysis.py

# Deploy everything
chmod +x deploy_google_integration.sh
./deploy_google_integration.sh

# Monitor auto-updates
tail -f logs/dashboard_updater.log
tail -f logs/gsp_updater.log
```

---

## 📞 Support

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production (Nov 2025)  
**Key Files**: 57 scripts using service account authentication

---

*Last Updated: November 11, 2025*  
*This document lists ALL files that connect to Google services using permanent/universal authentication*
