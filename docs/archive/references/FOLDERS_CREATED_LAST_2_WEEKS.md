# Folders Created in Last 2 Weeks

**Generated**: 31 October 2025  
**Period**: 18 October - 31 October 2025 (14 days)

---

## Summary

**Total New Folders**: 6 top-level folders (+ 120+ subfolders)

---

## Top-Level Folders

| Folder | Created | Purpose |
|--------|---------|---------|
| **`.git/`** | 2025-10-31 22:17 | Git repository (initialized today) |
| **`iris_windows_deployment/`** | 2025-10-31 17:35 | **Windows deployment package** ⭐ |
| **`.venv/`** | 2025-10-31 14:10 | Python virtual environment |
| **`statistical_analysis_output/`** | 2025-10-31 12:50 | Statistical analysis results |
| **`logs/`** | 2025-10-30 22:45 | Application logs |

---

## Detailed Breakdown

### 1. `.git/` (Today: 31 Oct 2025, 22:17)
- **Purpose**: Git version control repository
- **Status**: Just initialized today for GitHub sync
- **Contents**: Repository metadata, refs, objects
- **Size**: Small (metadata only)

---

### 2. `iris_windows_deployment/` (Today: 31 Oct 2025, 17:35) ⭐

**Main deployment package for Windows UpCloud server**

#### Structure:
```
iris_windows_deployment/
├── scripts/                    (17:41) - Main pipeline scripts
├── iris_client/               (17:40) - IRIS client package
│   ├── iris_data/            - Sample IRIS message data
│   │   ├── AGPT/             - 36 message type folders
│   │   ├── BOALF/
│   │   ├── BOD/
│   │   ├── FREQ/
│   │   ├── FUELINST/
│   │   └── ... (36 total)
│   ├── python/               - Python client implementation
│   │   └── iris_data/        - 50+ message type subfolders
│   └── __pycache__/
├── iris_data/                 (17:27) - Working data directory
└── logs/                      (17:27) - Pipeline logs
```

#### Subfolders (120+ total):
- **36 message type folders** in `iris_client/iris_data/`:
  - AGPT, AOBE, ATL, BEB, BOALF, BOD, CBS, DAG, DATL, DGWS
  - EBOCF, FOU2T3YW, FREQ, ISPSTACK, MELS, MZT, NETBSAD
  - NOU2T3YW, NTO, OCNMFD, OCNMFW, QAS, QPN, RDRE, RURE
  - RZDF, SEL, SMSG, TEMP, TSDFW, UOU2T14D, etc.

- **50+ message type folders** in `iris_client/python/iris_data/`:
  - All of the above PLUS:
  - ABUC, AGWS, BOAV, DISBSAD, DISEBSP, DISPTAV
  - FOU2T14D, FUELHH, FUELINST, IMBALNGC, INDDEM, INDGEN
  - INDO, INDOD, ITSDO, LOLPDM, MELNGC, MID, MILS, MNZT
  - NDF, NDFD, NDFW, NDZ, NONBM, NOU2T14D, NTB
  - OCNMF3Y, OCNMF3Y2, OCNMFD2, OCNMFW2
  - PBC, PN, PPBR, REMIT, RURI, SIL, SOSO, SYS_WARN
  - TSDF, TSDFD, UOU2T3YW, WINDFOR

#### Purpose:
- Complete IRIS deployment package for Windows server
- Contains all scripts needed for real-time data ingestion
- Includes BigQuery upload and auto-delete functionality
- Ready to upload to UpCloud server

#### Related Documentation:
- `UPCLOUD_DEPLOYMENT_PLAN.md`
- `WINDOWS_DEPLOYMENT_COMMANDS.md`
- `iris_windows_deployment.zip`

---

### 3. `.venv/` (Today: 31 Oct 2025, 14:10)
- **Purpose**: Python virtual environment
- **Contains**: Python packages and dependencies
- **Key Packages**:
  - google-cloud-bigquery
  - google-api-python-client
  - gspread
  - pandas
  - dacite (for IRIS)
- **Status**: Active and in use
- **Size**: ~200-500 MB (typical for Python env)

---

### 4. `statistical_analysis_output/` (Today: 31 Oct 2025, 12:50)
- **Purpose**: Output directory for statistical analysis results
- **Created By**: `advanced_statistical_analysis_enhanced.py`
- **Contents**: Statistical charts and analysis results
- **Types of Files**:
  - PNG charts (time series, correlations)
  - CSV exports (statistical summaries)
  - Analysis reports
- **Related Scripts**:
  - `advanced_statistical_analysis_enhanced.py`
  - Related to "Analysis BI Enhanced" sheet

---

### 5. `logs/` (Yesterday: 30 Oct 2025, 22:45)
- **Purpose**: Application logging directory
- **Contains**: Log files from various scripts
- **Typical Contents**:
  - Script execution logs
  - Error logs
  - BigQuery operation logs
  - API call logs
- **Size**: Varies (log rotation recommended)

---

## Message Type Folders Explanation

The IRIS deployment folders contain subfolders for different BMRS message types:

| Folder | Message Type | Description |
|--------|--------------|-------------|
| **BOD** | Bid Offer Data | Balancing mechanism bids/offers |
| **FREQ** | Frequency | System frequency (Hz) |
| **FUELINST** | Fuel Instantaneous | Real-time generation by fuel type |
| **MID** | Market Index Data | System prices |
| **INDDEM** | Indicative Demand | Demand outturn |
| **INDGEN** | Indicative Generation | Generation outturn |
| **WINDFOR** | Wind Forecast | Wind generation forecasts |
| **TEMP** | Temperature | Temperature data |
| **REMIT** | REMIT Messages | Plant unavailability |
| **SYS_WARN** | System Warnings | Grid warnings/alerts |

*And 40+ more message types covering all aspects of GB power system*

---

## Folder Sizes (Estimated)

| Folder | Size | Notes |
|--------|------|-------|
| `.git/` | ~10 MB | Growing as commits added |
| `iris_windows_deployment/` | ~50 MB | Sample IRIS data included |
| `.venv/` | ~300 MB | Python packages |
| `statistical_analysis_output/` | ~5 MB | Charts and exports |
| `logs/` | ~1 MB | Log files |

**Total**: ~366 MB

---

## Folders NOT Created (Still from Before)

These folders existed before the 2-week period:
- Root project files (Python scripts, .md files)
- Historical data folders (if any)
- Configuration files

---

## Key Observations

1. **Most Active Day**: 31 October 2025 (today)
   - 4 out of 6 folders created today
   - Major focus on IRIS deployment package

2. **Primary Activity**: Windows deployment preparation
   - Creating deployment structure
   - Organizing IRIS message types
   - Setting up logging infrastructure

3. **Development Focus**: 
   - Google Sheets integration (yesterday/today)
   - Statistical analysis tools (today)
   - Real-time IRIS data pipeline (today)

4. **Git Integration**: Just initialized today
   - Ready to sync with GitHub
   - 98 files pending commit

---

## Related Files Created (Same Period)

- `UPCLOUD_DEPLOYMENT_PLAN.md`
- `iris_windows_deployment.zip`
- `add_chart_only.py`
- `restore_sheet1_clean.py`
- `create_latest_day_chart.py`
- `read_dashboard_full.py`
- Plus 40+ more Python scripts and documentation files

---

## Next Steps

1. **Git Sync**: Commit and push all folders to GitHub
2. **Deployment**: Upload `iris_windows_deployment/` to UpCloud
3. **Cleanup**: Consider archiving `statistical_analysis_output/` periodically
4. **Monitoring**: Set up log rotation for `logs/` folder

---

**Status**: Development environment fully set up and ready for deployment
