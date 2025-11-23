# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2025-11-23

### Added
- **Daily Dashboard with Auto-Updating Charts**:
  - New script: `daily_dashboard_auto_updater.py` - Fetches 30 days of settlement period data
  - Auto-creates 4 professional charts: Prices (SSP/SBP), Demand/Generation, Interconnector Imports, Frequency
  - Apps Script: `daily_dashboard_charts.gs` - Auto-refreshes charts every 30 minutes
  - Market summary KPIs displayed in Dashboard rows 18-29:
    - Today's averages (SSP, SBP, Demand, Generation, IC Import, Frequency)
    - 30-day statistics (avg, max, min prices)
  - New sheet: `Daily_Chart_Data` - Stores all settlement period data
  - Documentation: `DAILY_DASHBOARD_SETUP.md` - Complete setup guide
  - Deployment script: `deploy_daily_dashboard.sh` - One-click UpCloud deployment

### Changed
- Dashboard layout: Rows 18-29 now reserved for market summary KPIs (was blank spacing)
- Updated `DUAL_SERVER_ARCHITECTURE.md` with new daily dashboard script in cron schedule

### Technical Details
- Python queries BigQuery (bmrs_mid, bmrs_indod, bmrs_fuelinst, bmrs_freq + _iris tables)
- Combines last 30 days of data (historical + real-time)
- Writes to Google Sheets every 30 minutes via cron
- Apps Script trigger auto-refreshes charts every 30 minutes
- Professional formatting with color-coded headers and spacing

## [2.1.0] - 2025-11-23

### Changed
- **Dashboard Layout Restructure**: Moved outage section from row 22 to row 30
  - Outage header now at row 30 (was row 22)
  - Outage data starts at row 31 (was row 23)
  - Added 8 blank spacing rows (22-29) between fuel data and outages
  - Improves visual separation and organization

### Fixed
- Removed orphaned GSP analysis data that appeared below outages section (rows 55-75)
- `update_outages_enhanced.py` now clears rows 31-70 (was 23-60) before writing fresh data
- `update_dashboard_preserve_layout.py` now writes outage header at row 30 (was row 22)

### Technical Details
- Both scripts updated and deployed to UpCloud server (94.237.55.234)
- Cron jobs continue running every 10 minutes with new row structure
- TOTAL row dynamically placed based on number of outages (currently row 58 for 26 outages)

## [2.0.0] - 2025-11-22

### Added
- **Dual-Server Architecture** with automatic failover
  - UpCloud server (94.237.55.234): Primary lightweight dashboard updates + IRIS streaming
  - Dell server (local): Heavy compute + failover backup
- Failover monitoring script (`monitor_and_failover.py`)
- Health check endpoint on UpCloud (`health_check_server.py`)
- Complete documentation in `DUAL_SERVER_ARCHITECTURE.md`

### Changed
- All scripts migrated from OAuth token.pickle to service account authentication
- `update_outages_enhanced.py`: Added clear operation before writing to prevent duplicates
- Authentication architecture unified across all scripts

### Fixed
- Duplicate TOTAL rows issue in Dashboard outages section (removed conflicting Apps Script trigger)
- Missing cron job for outages updates (added 10-minute schedule)
- OAuth authentication failures on UpCloud server

## [0.1.0] - 2025-11-01

### Added
- Initial project setup
- README.md with project documentation
- CONTRIBUTING.md with contribution guidelines
- CHANGELOG.md for tracking changes
- .gitignore for common files to exclude
- Project initialized
- Basic documentation structure
