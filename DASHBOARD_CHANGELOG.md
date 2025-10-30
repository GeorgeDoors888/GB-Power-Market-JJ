# Dashboard Changelog

All notable changes to the UK Power Market Dashboard.

---

## [2.0.0] - 2025-10-30

### ✨ Major Features Added

#### Visual Enhancements
- **Red Bar Chart Graphics** for % unavailable capacity
  - Changed from black blocks (█) to red squares (🟥)
  - White squares (⬜) represent available capacity
  - Each square = 10% of unit capacity
  - Example: `🟥🟥🟥🟥🟥🟥🟥⬜⬜⬜ 70.0%`

#### Price Impact Analysis Section
- **New section** showing market price changes since outage announcements
- Displays pre-announcement baseline price (£68.50/MWh)
- Current market price (£76.33/MWh from EPEX)
- Total price delta: +£7.83/MWh (+11.4%)
- Individual event impact estimates
- Event-by-event breakdown with announcement timestamps

#### Comprehensive Station Coverage
- Shows **all REMIT events** (not just active)
- Includes recently returned-to-service units for context
- Status indicators: 🔴 Active, 🟢 Returned
- Sorted by status (active first), then by capacity (largest first)

### 🔧 Improvements
- Column header corrected: "% Unavail" → "% Unavailable"
- Expanded dashboard from 6 columns to 8 columns
- Enhanced color scheme for new sections:
  - Price analysis header: Dark green (#1A7F4D)
  - Stations list header: Purple-blue (#6666CC)
- Better row spacing and visual hierarchy

### 📊 Dashboard Layout Updates
- **Row 17:** Main REMIT header with market impact message
- **Row 18:** Summary with visual bar chart + total price impact
- **Row 20:** Price Impact Analysis section header
- **Rows 21-25:** Price impact table (event, timestamp, MW, impact, prices)
- **Row 27:** All Station Outages section header
- **Row 29:** Table header (Status, Station, Unit, Fuel, Normal MW, Unavail MW, % Unavailable, Cause)
- **Rows 30+:** Complete station list with visual bars

### 🐛 Fixes
- Fixed deprecation warning for `sheet.update()` (now uses named parameters)
- Improved bar chart function with red emoji squares
- Enhanced `get_all_remit_events()` to fetch complete event history

### 📝 Documentation
- Created `DASHBOARD_DOCUMENTATION.md` (15,000+ words)
  - Complete feature reference
  - Data source details
  - SQL query examples
  - Troubleshooting guide
  - Future enhancement roadmap
- Created `DASHBOARD_QUICK_REFERENCE.md` (condensed guide)
- Created `CHANGELOG.md` (this file)

### 🔍 Technical Changes
**Files Modified:**
- `dashboard_clean_design.py` - Main dashboard script
  - New function: `create_bar_chart(percentage, width=10)` with red squares
  - New function: `get_price_impact_analysis(remit_df)`
  - Modified: `get_all_remit_events()` (was `get_active_remit_events()`)
  - Enhanced: `create_clean_dashboard()` with 8-column layout
  - Updated formatting logic for new sections

**Dependencies:**
- No new dependencies required
- Compatible with existing environment

---

## [1.5.0] - 2025-10-30 (Earlier)

### ✨ Features Added
- REMIT unavailability data integration
- Separate "REMIT Unavailability" sheet (later consolidated)
- BigQuery table: `bmrs_remit_unavailability`
- Active outage tracking
- Consolidated view: REMIT data moved to Sheet1

### 🔧 Improvements
- Created `fetch_remit_unavailability.py` ingestion script
- Created `dashboard_remit_updater.py` (separate sheet)
- Created `dashboard_updater_combined.py` (consolidated Sheet1)
- Fixed datetime comparison issues in BigQuery queries
- Installed `db-dtypes` for BigQuery datetime handling

### 📝 Documentation
- Created `REMIT_DASHBOARD_DOCUMENTATION.md`
- Created `SYSTEM_OVERVIEW.md`

---

## [1.0.0] - 2025-10 (Initial Version)

### ✨ Initial Features
- Real-time generation data by fuel type
- Interconnector flow tracking
- System metrics calculation
  - Total generation
  - Total supply
  - Renewables percentage
- Two-column layout (Generation | Interconnectors)
- Color-coded sections
- Emoji fuel type icons
- Auto-refresh capability

### 🗄️ Data Infrastructure
- BigQuery project setup: `inner-cinema-476211-u9`
- Dataset: `uk_energy_prod`
- Table: `bmrs_fuelinst`
- Elexon BMRS API integration (B1610 FUELINST stream)

### 🔧 Scripts Created
- `fetch_fuelinst_today.py` - Data ingestion from BMRS API
- `dashboard_updater_complete.py` - Original dashboard updater
- `authorize_google_docs.py` - Google Sheets authentication

### 📊 Initial Dashboard Layout
- Row 1: Title
- Row 2: Timestamp
- Rows 4-5: System metrics
- Rows 7-14: Generation mix (7 fuel types)
- Rows 7-14: Interconnectors (6 countries)

### 🎨 Design Elements
- Dark blue header (#0D3380)
- Green generation section (#33996D)
- Brown interconnectors section (#996633)
- Blue metrics section (#3366B3)

---

## Planned Future Releases

### [2.1.0] - Planned
**Live Market Price Integration**
- Automated EPEX API connection
- Real-time price updates
- Historical price tracking

**Carbon Intensity**
- National Grid ESO API integration
- gCO₂/kWh tracking
- Carbon intensity forecasts

### [2.2.0] - Planned
**Alert System**
- SMS/email notifications for major outages
- Price spike alerts
- Low renewables warnings

**Multi-Sheet Dashboard**
- Sheet2: Historical trends (24h charts)
- Sheet3: Outage calendar (30-day view)
- Sheet4: Financial analysis
- Sheet5: Carbon tracking

### [3.0.0] - Future Vision
**Live REMIT Data**
- Elexon IRIS FTP integration
- ENTSO-E Transparency Platform API
- Automated outage detection

**Forecasting**
- Machine learning price predictions
- Capacity availability forecasts
- Tight margin warnings

**Advanced Analytics**
- Historical correlation analysis
- Seasonal pattern detection
- Market regime identification

---

## Version Numbering

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes, major redesigns
- **MINOR:** New features, significant enhancements
- **PATCH:** Bug fixes, minor improvements

---

## Migration Notes

### Upgrading from 1.5 to 2.0

**No breaking changes.** Simply replace scripts:
```bash
# Backup old version
cp dashboard_updater_combined.py dashboard_updater_combined.py.v1.5.backup

# Use new script
# dashboard_clean_design.py is the new main script
./.venv/bin/python dashboard_clean_design.py
```

**What's different:**
- More columns in Sheet1 (6 → 8)
- New price impact section
- New visual bar charts
- More comprehensive outage list

**What's the same:**
- Same BigQuery tables
- Same authentication
- Same update frequency
- Same dependencies

### Cron Job Update

**Old (v1.5):**
```bash
*/15 * * * * ./.venv/bin/python dashboard_updater_combined.py
```

**New (v2.0):**
```bash
*/15 * * * * ./.venv/bin/python dashboard_clean_design.py
```

---

## Contributors

**Lead Developer:** George Major (george.major@grid-smart.co.uk)  
**Organization:** Grid Smart / uPower Energy  
**Project Start:** October 2025

---

## Data Attribution

- **Elexon BMRS:** © Elexon Limited, Open Government Licence v3.0
- **REMIT Data:** EU Regulation 1227/2011
- **Market Prices:** EPEX SPOT © European Power Exchange

---

*For detailed documentation, see `DASHBOARD_DOCUMENTATION.md`*
