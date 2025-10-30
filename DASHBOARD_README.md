# 🇬🇧 UK Power Market Dashboard

**Real-time electricity generation, outages, and market impact tracking**

Version 2.0 | Last Updated: 30 October 2025

---

## 🎯 What is This?

A live dashboard that tracks:
- ⚡ **Real-time generation** by fuel type (Gas, Nuclear, Wind, Solar, etc.)
- 🔌 **Interconnector flows** from 6 European countries
- 🔴 **Power station outages** (REMIT unavailability events)
- 💷 **Market price impacts** from outages
- 📊 **Visual analytics** with red bar charts showing % capacity unavailable

**Live Dashboard:** [View on Google Sheets](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8)

---

## 🚀 Quick Start

### Update Dashboard (One Command)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python dashboard_clean_design.py
```

**Runtime:** ~5-8 seconds  
**Output:** Formatted Google Sheet with latest data

---

## ✨ Key Features

### 1. Real-Time Generation Mix
- 7 fuel types with emoji icons (🔥 Gas, ⚛️ Nuclear, 💨 Wind, ☀️ Solar, etc.)
- Live data from Elexon BMRS API (every 5 minutes)
- System metrics: Total generation, renewables %, supply

### 2. REMIT Outage Tracking
- EU regulatory reporting (Regulation 1227/2011)
- Active and recently returned-to-service units
- Visual % unavailable bar charts: 🟥🟥🟥⬜⬜⬜⬜⬜⬜⬜
- Cause and duration details

### 3. Price Impact Analysis
- Pre-outage baseline vs current market price
- Individual event impact estimates
- Total price delta tracking
- Announcement timestamps

### 4. Visual Bar Charts
- Red squares (🟥) = 10% unavailable
- White squares (⬜) = 10% available
- Instant visual assessment of outage severity

---

## 📊 Current Data Snapshot

**Last Known (30 Oct 2025):**
- Total Generation: **27.4 GW**
- Renewables: **46.1%**
- Active Outages: **4 stations**
- Unavailable Capacity: **1,647 MW**
- Price Impact: **+£7.83/MWh (+11.4%)**

**Active Outages:**
1. Drax Unit 1 - 660 MW (turbine bearing failure)
2. Pembroke CCGT Unit 4 - 537 MW (boiler tube leak)
3. Sizewell B - 300 MW (reactor de-rating)
4. London Array - 150 MW (cable fault)

---

## 📚 Documentation

We have **30,500+ words** of documentation across 5 comprehensive guides:

### Start Here
📖 **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Master index of all docs

### Quick Reference
🚀 **[DASHBOARD_QUICK_REFERENCE.md](DASHBOARD_QUICK_REFERENCE.md)** - 5-page cheat sheet
- One-command updates
- Visual element key
- Quick troubleshooting
- Automation setup

### Complete Guide
⭐ **[DASHBOARD_DOCUMENTATION.md](DASHBOARD_DOCUMENTATION.md)** - 50-page comprehensive reference
- Feature descriptions
- BigQuery schemas
- SQL queries
- Troubleshooting (10+ solutions)
- Future roadmap

### Specialist Guides
🔴 **[REMIT_DASHBOARD_DOCUMENTATION.md](REMIT_DASHBOARD_DOCUMENTATION.md)** - REMIT regulation & data  
🏗️ **[SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)** - Architecture & data pipelines  
📝 **[DASHBOARD_CHANGELOG.md](DASHBOARD_CHANGELOG.md)** - Version history & migration notes

---

## 🔧 Technology Stack

**Data Sources:**
- Elexon BMRS API (B1610 FUELINST stream)
- REMIT unavailability data (sample/production)
- EPEX SPOT market prices

**Storage:**
- Google BigQuery (inner-cinema-476211-u9)
- Tables: bmrs_fuelinst, bmrs_remit_unavailability

**Visualization:**
- Google Sheets (formatted dashboard)
- Python gspread library

**Languages & Tools:**
- Python 3.11+
- BigQuery SQL
- Google Sheets API

---

## 🎨 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ 🇬🇧 UK POWER MARKET DASHBOARD                              │
│ ⏰ Last Updated: 2025-10-30 14:10 | Period 29              │
├─────────────────────────────────────────────────────────────┤
│ 📊 SYSTEM METRICS                                           │
│ Total: 27.4 GW | Supply: 31.0 GW | Renewables: 46.1%      │
├──────────────────────────┬──────────────────────────────────┤
│ ⚡ GENERATION            │ 🔌 INTERCONNECTORS                │
│ 🔥 Gas        12.5 GW    │ 🇫🇷 IFA          1.2 GW          │
│ ⚛️ Nuclear     6.2 GW    │ 🇫🇷 IFA2         0.8 GW          │
│ 💨 Wind        5.8 GW    │ 🇳🇱 BritNed      0.9 GW          │
│ ☀️ Solar       1.2 GW    │ 🇧🇪 Nemo         0.6 GW          │
│ ...                      │ ...                              │
├─────────────────────────────────────────────────────────────┤
│ 🔴 POWER STATION OUTAGES & MARKET IMPACT                    │
│ Active: 4 of 5 | 1,647 MW unavail | 🟥🟥🟥🟥🟥🟥🟥🟥⬜⬜      │
│ Price Impact: +£7.83/MWh (+11.4%)                          │
├─────────────────────────────────────────────────────────────┤
│ 💷 PRICE IMPACT ANALYSIS                                    │
│ Event | Announcement | MW | Impact | Pre | Current | Δ     │
│ Drax  | 2025-10-28  | 660 | +£3.30 | £68.50 | £76.33 |+£7.83│
│ ...                                                         │
├─────────────────────────────────────────────────────────────┤
│ 📊 ALL STATION OUTAGES                                      │
│ Status | Station | Fuel | Normal | Unavail | % Unavailable │
│ 🔴 Active | Drax | BIOMASS | 660 | 660 | 🟥��🟥🟥🟥🟥🟥🟥🟥🟥 │
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Automation

### Set Up Auto-Updates (15 minutes)
```bash
# Edit crontab
crontab -e

# Add this line for updates every 15 minutes
*/15 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python fetch_fuelinst_today.py && ./.venv/bin/python fetch_remit_unavailability.py && ./.venv/bin/python dashboard_clean_design.py >> logs/dashboard.log 2>&1
```

**Or hourly at :05 past:**
```bash
5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python dashboard_clean_design.py >> logs/dashboard.log 2>&1
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

# Google Sheets
./.venv/bin/python authorize_google_docs.py
```

### Missing dependencies?
```bash
./.venv/bin/pip install google-cloud-bigquery gspread pandas db-dtypes
```

**More solutions:** See [DASHBOARD_DOCUMENTATION.md](DASHBOARD_DOCUMENTATION.md) → Troubleshooting section (10+ fixes)

---

## 📈 What's New in Version 2.0

**Visual Enhancements:**
- 🟥 Red bar chart graphics for % unavailable (was black)
- 8-column layout (was 6 columns)
- Enhanced color coding for sections

**New Features:**
- 💷 Price impact analysis section
- 📊 Complete station list (active + returned)
- Individual event price impact estimates
- Pre/post-announcement price comparison
- "% Unavailable" column header corrected

**Performance:**
- Same 5-8 second update time
- No new dependencies
- Backward compatible

**See:** [DASHBOARD_CHANGELOG.md](DASHBOARD_CHANGELOG.md) for full details

---

## 🗺️ Roadmap

### Version 2.1 (Planned)
- Live market price API integration (EPEX)
- Carbon intensity tracking (National Grid ESO API)
- Historical price charts

### Version 2.2 (Planned)
- SMS/email alerts for major outages
- Multi-sheet dashboard (trends, forecasts, financials)

### Version 3.0 (Future)
- Live REMIT data integration (Elexon IRIS / ENTSO-E)
- Machine learning price predictions
- Advanced analytics & pattern detection

---

## 🎓 Learning Resources

### For New Users
1. Read: [DASHBOARD_QUICK_REFERENCE.md](DASHBOARD_QUICK_REFERENCE.md) (5 min)
2. Run: `./.venv/bin/python dashboard_clean_design.py`
3. View: [Dashboard on Google Sheets](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8)

### For Developers
1. Architecture: [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)
2. Complete API Reference: [DASHBOARD_DOCUMENTATION.md](DASHBOARD_DOCUMENTATION.md)
3. REMIT Details: [REMIT_DASHBOARD_DOCUMENTATION.md](REMIT_DASHBOARD_DOCUMENTATION.md)

### For Analysts
- SQL Query Library: [DASHBOARD_DOCUMENTATION.md](DASHBOARD_DOCUMENTATION.md) → "Useful SQL Queries"
- BigQuery Tables: `bmrs_fuelinst`, `bmrs_remit_unavailability`
- Sample queries for generation mix, outage analysis, renewables tracking

---

## 📊 Key Metrics & Definitions

**Total Generation:** Sum of all fuel types (MW → GW)  
**Total Supply:** Generation + Interconnector Imports  
**Renewables %:** (Wind + Solar + Biomass + Hydro) / Total Generation × 100  
**Settlement Period:** 48 half-hourly periods per day (1-48)  
**REMIT:** EU Regulation 1227/2011 requiring disclosure of generation unavailability  
**Price Impact:** Estimated contribution of outages to market price changes

---

## 📞 Contact & Support

**Project Owner:** George Major  
**Email:** george.major@grid-smart.co.uk / george@upowerenergy.uk  
**Organization:** Grid Smart / uPower Energy

**BigQuery Project:** inner-cinema-476211-u9  
**Dataset:** uk_energy_prod

**Questions?** Check [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for relevant guides

---

## 📄 License & Attribution

**Data Sources:**
- Elexon BMRS © Elexon Limited (Open Government Licence v3.0)
- REMIT Data (EU Regulation 1227/2011 - Public transparency data)
- EPEX SPOT © European Power Exchange

**Dashboard Code:** Proprietary - Grid Smart / uPower Energy  
**Usage:** Internal business intelligence and market analysis

---

## 🔗 Quick Links

- 📊 [Live Dashboard](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8)
- 📚 [Documentation Index](DOCUMENTATION_INDEX.md)
- 🚀 [Quick Reference](DASHBOARD_QUICK_REFERENCE.md)
- 📖 [Complete Guide](DASHBOARD_DOCUMENTATION.md)
- 📝 [Changelog](DASHBOARD_CHANGELOG.md)
- �� [REMIT Guide](REMIT_DASHBOARD_DOCUMENTATION.md)
- 🏗️ [System Overview](SYSTEM_OVERVIEW.md)

---

**Built with ❤️ for the UK electricity market**

*Last Updated: 30 October 2025 | Version 2.0*
