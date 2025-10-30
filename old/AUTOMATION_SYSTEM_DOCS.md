# Energy Data Automation System Docu## 📊 Data Sources

### Elexon BMRS (Balancing Mechanism Reporting Service)
- **Frequency**: Every 15 minutes
- **Datasets**: 55 datasets including BOD, FREQ, FUELINST, MILS, MELS, etc.
- **Method**: REST API with intelligent chunking
- **Storage**: BigQuery `jibber-jabber-knowledge.uk_energy_insights`

### Elexon IRIS (Insights Real-time Information Service)
- **Frequency**: Real-time (push-based)
- **Datasets**: REMIT (unplanned outages), real-time market events
- **Method**: Azure Service Bus subscription
- **Storage**: Local JSON files → BigQuery
- **Processing**: 5-minute intervals, 1-hour cleanup cycle

### NESO (National Energy System Operator)
- **Frequency**: Every hour (less frequent updates)
- **Method**: Data portal API
- **Status**: Implemented with tracking# 🚀 Overview

This system provides **automated 15-minute updates** for Elexon BMRS and NESO energy data, with intelligent incremental ingestion that only processes missing data since the last successful run.

## 📊 Key Features

- ✅ **15-minute automated updates** via cron
- ✅ **Google Sheets tracking** of last ingestion times
- ✅ **Incremental ingestion** - only fetches missing data
- ✅ **BigQuery integration** with 396+ tables
- ✅ **Comprehensive logging** and monitoring
- ✅ **Error handling** and recovery
- ✅ **Real-time status dashboard**

## 🔧 System Components

### Core Scripts

| Script                                   | Purpose                              |
| ---------------------------------------- | ------------------------------------ |
| `energy_15min_updater.sh`                | Main automation orchestrator         |
| `automated_data_tracker.py`              | Google Sheets integration & tracking |
| `ingest_elexon_fixed.py`                 | Elexon BMRS data ingestion           |
| `neso_data_updater.py`                   | NESO data updates                    |
| `monitor_automation_status.py`           | System status checker                |
| `live_dashboard.py`                      | Real-time monitoring dashboard       |
| `elexon_iris/client.py`                  | Real-time IRIS data collection       |
| `elexon_iris/iris_to_bigquery.py`        | Process IRIS data to BigQuery        |
| `elexon_iris/cleanup_processed_files.sh` | Clean up processed IRIS files        |

### Setup Scripts

| Script                            | Purpose                  |
| --------------------------------- | ------------------------ |
| `setup_15min_automation.sh`       | Install cron automation  |
| `setup_google_sheets_tracking.py` | Initialize Google Sheets |

## 📈 Data Sources

### Elexon BMRS (Balancing Mechanism Reporting Service)
- **Frequency**: Every 15 minutes
- **Datasets**: 55 datasets including BOD, FREQ, FUELINST, MILS, MELS, etc.
- **Method**: REST API with intelligent chunking
- **Storage**: BigQuery `jibber-jabber-knowledge.uk_energy_insights`

### NESO (National Energy System Operator)
- **Frequency**: Every hour (less frequent updates)
- **Method**: Data portal API
- **Status**: Implemented with tracking

## ⚙️ Configuration

### Environment Variables
```bash
# Required in .env file
BMRS_API_KEY_1=your_key_here
BMRS_API_KEY_2=your_key_here
# ... up to BMRS_API_KEY_20
```

### Google Cloud Setup
```bash
# Authentication with required scopes
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/cloud-platform,\
           https://www.googleapis.com/auth/spreadsheets,\
           https://www.googleapis.com/auth/drive
```

### Virtual Environment
- **Location**: `.venv_ingestion/`
- **Python**: 3.13.7
- **Key packages**: pandas, google-cloud-bigquery, gspread, httpx, tenacity

## 📊 Tracking & Monitoring

### Google Sheets Dashboard
**URL**: https://docs.google.com/spreadsheets/d/1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw/edit

**Columns**:
- `Source`: Data source (ELEXON, NESO)
- `Dataset`: Dataset identifier
- `Last_Update`: Timestamp of last successful update
- `Status`: Current status (SUCCESS, FAILED, STARTED)
- `Tracked_At`: When this entry was recorded
- `Notes`: Additional information

### Cron Schedule
```bash
# Every 15 minutes
*/15 * * * * /path/to/energy_15min_updater.sh >> logs/automation/cron_output.log 2>&1
```

## 🔍 Monitoring Commands

### Status Check
```bash
# Quick status overview
python monitor_automation_status.py

# Live dashboard (refreshes every 30s)
python live_dashboard.py
```

### Log Monitoring
```bash
# View today's automation logs
tail -f logs/automation/15min_updates_$(date +%Y%m%d).log

# View cron output
tail -f logs/automation/cron_output.log
```

### Manual Operations
```bash
# Manual update (bypasses timing checks)
./energy_15min_updater.sh

# Test specific date range
python ingest_elexon_fixed.py --start 2025-09-20 --end 2025-09-21 --log-level DEBUG
```

## 🔧 Management

### Enable/Disable Automation
```bash
# View current cron jobs
crontab -l

# Edit cron schedule
crontab -e

# Disable by commenting out the line:
# */15 * * * * /path/to/energy_15min_updater.sh...
```

### Troubleshooting

#### Google Sheets Issues
```bash
# Re-authenticate with correct scopes
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/cloud-platform,\
           https://www.googleapis.com/auth/spreadsheets,\
           https://www.googleapis.com/auth/drive

# Test connection
python -c "from automated_data_tracker import DataTracker; DataTracker()"
```

#### BigQuery Issues
```bash
# Test BigQuery connectivity
python -c "from google.cloud import bigquery; print(bigquery.Client().query('SELECT 1').to_dataframe())"
```

#### Virtual Environment Issues
```bash
# Recreate environment
rm -rf .venv_ingestion
python -m venv .venv_ingestion
source .venv_ingestion/bin/activate
pip install pandas google-cloud-bigquery gspread httpx tenacity requests tqdm python-dotenv pyarrow
```

## 📈 Performance & Efficiency

### Intelligent Features
- **Skip existing data**: Checks BigQuery for existing windows before fetching
- **Incremental updates**: Only processes data since last successful run
- **Rate limiting**: Respects API quotas with exponential backoff
- **Chunked processing**: Handles large datasets efficiently
- **Deduplication**: Hash-based detection of duplicate data

### Resource Usage
- **Disk space**: ~22GB free space maintained
- **API calls**: Optimized with 20 rotating API keys
- **BigQuery quota**: Managed with staging tables and batch operations
- **Memory**: Efficient pandas operations with chunking

## 🎯 Future Enhancements

### Planned Improvements
- [ ] Web-based dashboard with real-time charts
- [ ] Slack/email notifications for failures
- [ ] Predictive data quality monitoring
- [ ] Enhanced NESO dataset coverage
- [ ] Machine learning anomaly detection
- [ ] Cost optimization analytics

### Extension Points
- Add new data sources by creating similar updater modules
- Integrate with other cloud platforms (AWS, Azure)
- Export to additional formats (Parquet, JSON)
- Real-time streaming ingestion

## 📞 Support

### Quick Reference
- **Status**: `python monitor_automation_status.py`
- **Dashboard**: `python live_dashboard.py`
- **Logs**: `tail -f logs/automation/15min_updates_*.log`
- **Manual run**: `./energy_15min_updater.sh`
- **Google Sheets**: https://docs.google.com/spreadsheets/d/1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw/edit
- **REMIT Documentation**: [REMIT_DATA_DOCUMENTATION.md](/REMIT_DATA_DOCUMENTATION.md)

### System Requirements
- macOS/Linux with cron support
- Python 3.13+
- Google Cloud SDK
- Internet connectivity
- 25GB+ free disk space

---

*Last updated: 2025-09-20*
*System status: ✅ Active and monitoring*
