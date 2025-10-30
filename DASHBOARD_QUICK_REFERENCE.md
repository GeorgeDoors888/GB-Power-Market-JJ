# UK Power Market Dashboard - Quick Reference

**Version 2.0** | Last Updated: 30 October 2025

---

## 🚀 Quick Start

### Update Dashboard (One Command)
```bash
cd "/Users/georgemajor/GB Power Market JJ" && ./.venv/bin/python dashboard_clean_design.py
```

### View Dashboard
🔗 [Open Dashboard](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8)

---

## 📊 Dashboard Sections

| Section | Rows | Content |
|---------|------|---------|
| **Header** | 1-2 | Title, timestamp, settlement period |
| **System Metrics** | 4-5 | Total generation, supply, renewables %, market price |
| **Generation Mix** | 7-14 | Fuel types & interconnectors with emoji icons |
| **REMIT Outages** | 17-18 | Active outages summary with visual bar chart |
| **Price Impact** | 20-25 | Price change analysis from outage announcements |
| **All Stations** | 27+ | Complete outage list with status & % unavailable |

---

## 🎨 Visual Elements

### Status Indicators
- 🔴 **Active** - Outage currently in effect
- 🟢 **Returned** - Unit back in service

### Bar Charts (% Unavailable)
- 🟥 = 10% capacity offline (red squares)
- ⬜ = 10% capacity available (white squares)

**Examples:**
- `🟥🟥🟥⬜⬜⬜⬜⬜⬜⬜ 30.0%` = Minor de-rating
- `🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100.0%` = Complete unit offline

### Fuel Type Icons
- 🔥 Gas (CCGT)
- ⚛️ Nuclear
- 💨 Wind
- ☀️ Solar
- 🌿 Biomass
- 💧 Hydro
- ⚫ Coal

### Interconnector Flags
- 🇫🇷 France (IFA, IFA2)
- 🇳🇱 Netherlands (BritNed)
- 🇧🇪 Belgium (Nemo)
- 🇳🇴 Norway (NSL)
- 🇮🇪 N. Ireland (Moyle)

---

## 🔧 Key Scripts

### 1. `dashboard_clean_design.py` ⭐
**Main dashboard update script**
- Fetches generation & REMIT data from BigQuery
- Calculates price impacts
- Creates visual bar charts
- Formats Sheet1 with colors & styling

**Runtime:** ~5-8 seconds

### 2. `fetch_fuelinst_today.py`
**Generation data ingestion**
- Pulls from Elexon BMRS API
- Uploads to BigQuery `bmrs_fuelinst` table
- Run every 5 minutes (recommended)

### 3. `fetch_remit_unavailability.py`
**REMIT outage data ingestion**
- Currently uses sample data
- Uploads to BigQuery `bmrs_remit_unavailability` table
- Run every hour (recommended)

---

## 💷 Price Impact Analysis

### Current Metrics
- **Baseline Price:** £68.50/MWh (pre-outage average)
- **Current Price:** £76.33/MWh (EPEX spot)
- **Price Increase:** +£7.83/MWh (+11.4%)

### Estimation Method
```
Estimated Impact = (Unavailable MW / 100) × £0.50/MWh
```

**Example:**
- Drax Unit 1: 660 MW offline
- Estimated impact: (660 / 100) × £0.50 = **£3.30/MWh**

---

## 🗄️ Data Sources

### BigQuery Tables
**Project:** `inner-cinema-476211-u9`  
**Dataset:** `uk_energy_prod`

| Table | Content | Update Frequency |
|-------|---------|------------------|
| `bmrs_fuelinst` | Generation by fuel type | Every 5 minutes |
| `bmrs_remit_unavailability` | Power station outages | Hourly |

### External APIs
- **Elexon BMRS:** Generation data (B1610 FUELINST)
- **EPEX SPOT:** UK day-ahead prices (manual entry)
- **REMIT:** EU Regulation 1227/2011 unavailability data

---

## 🔄 Automation Setup

### Cron Job (Recommended)
```bash
# Edit crontab
crontab -e

# Add: Update every 15 minutes
*/15 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python fetch_fuelinst_today.py && ./.venv/bin/python fetch_remit_unavailability.py && ./.venv/bin/python dashboard_clean_design.py >> logs/dashboard.log 2>&1
```

### Manual Update (All Steps)
```bash
cd "/Users/georgemajor/GB Power Market JJ"

# 1. Fetch generation data
./.venv/bin/python fetch_fuelinst_today.py

# 2. Fetch REMIT data
./.venv/bin/python fetch_remit_unavailability.py

# 3. Update dashboard
./.venv/bin/python dashboard_clean_design.py
```

---

## 🐛 Troubleshooting

### Dashboard not updating?
```bash
# Check BigQuery data
bq query --use_legacy_sql=false '
SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(publishTime) = CURRENT_DATE()
'

# Re-run update
./.venv/bin/python dashboard_clean_design.py
```

### Authentication errors?
```bash
# BigQuery
gcloud auth application-default login

# Google Sheets (creates token.pickle)
./.venv/bin/python authorize_google_docs.py
```

### Missing dependencies?
```bash
./.venv/bin/pip install google-cloud-bigquery gspread pandas db-dtypes
```

---

## 📈 Current Dashboard Data

**Last Known Values (30 Oct 2025):**
- Total Generation: **27.4 GW**
- Total Supply: **31.0 GW**
- Renewables: **46.1%**
- Active Outages: **4 events**
- Total Unavailable: **1,647 MW**

**Active Outages:**
1. Drax Unit 1 - 660 MW BIOMASS (turbine bearing failure)
2. Pembroke CCGT Unit 4 - 537 MW CCGT (boiler tube leak)
3. Sizewell B - 300 MW NUCLEAR (reactor de-rating)
4. London Array Wind Farm - 150 MW WIND (cable fault)

---

## 📚 Documentation

**Full Documentation:** `DASHBOARD_DOCUMENTATION.md` (50+ pages)
- Complete schema details
- API integration guides
- SQL query examples
- Future enhancement plans

**Related Docs:**
- `REMIT_DASHBOARD_DOCUMENTATION.md` - REMIT-specific details
- `SYSTEM_OVERVIEW.md` - Architecture diagrams

---

## 📞 Support

**Owner:** George Major  
**Email:** george.major@grid-smart.co.uk  
**Project:** Grid Smart Production / uPower Energy

**Dashboard URL:**  
🔗 https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

---

## ✨ Version 2.0 Features

**New in this version:**
- ✅ Visual % unavailability bar charts (red squares)
- ✅ Price impact analysis section
- ✅ Complete station list (active + returned to service)
- ✅ Individual event price impact estimates
- ✅ Pre/post-announcement price comparison
- ✅ Enhanced color coding and formatting
- ✅ Column header fix: "% Unavailable" (was "% Unavail")

---

*Quick Reference Guide - v2.0*
