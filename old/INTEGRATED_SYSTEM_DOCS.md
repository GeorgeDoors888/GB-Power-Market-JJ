# Integrated ELEXON Data and Watermark Management System

## Overview
This document describes the integrated system for ELEXON data ingestion and watermark management. The system is designed to run automatically when your machine starts up and at regular intervals to ensure you always have the most up-to-date data.

## Components

### 1. Integrated Update Script (`integrated_update.sh`)
This script orchestrates the entire process:
- Ingests the latest ELEXON data
- Generates updated watermark files
- Manages watermark files (keeping only the most recent)
- Analyzes data freshness and generates reports
- Maintains its own logs with automatic cleanup

### 2. Automated Scheduling (`integrated_crontab.txt`)
The crontab configuration provides:
- **System Startup**: Runs immediately when your machine starts up (@reboot)
- **High-Frequency Updates**: Runs every 15 minutes for continuous updates
- **Weekly Full Refresh**: Runs every Sunday at 2:00 AM for a complete 7-day data refresh
- **Monthly Analysis**: Generates a comprehensive report on the 1st of each month

### 3. ELEXON Data Ingestion (`ingest_elexon_fixed.py`)
This script handles:
- Fetching data from ELEXON for specified datasets
- Cleaning and processing the data
- Loading it into BigQuery with schema adaptation

### 4. Watermark Management (`manage_watermarks.sh`)
This script handles:
- Finding all watermark files
- Keeping only the 5 most recent files
- Cleaning up old files to save disk space

### 5. Watermark Analysis (`analyze_watermarks.py`)
This script provides:
- Comprehensive analysis of data freshness
- Identification of stale tables
- Storage usage statistics
- Recommendations for data refreshes

## Installation and Usage

### Installing the Integrated System
Run the installation script to set up the crontab:
```bash
./install_crontab.sh
```

### Manual Execution
You can also run the integrated update manually:
```bash
./integrated_update.sh
```

### Monitoring
The system generates log files in the `logs` directory:
- `integrated_update_TIMESTAMP.log`: Log files for each run
- `watermark_analysis_TIMESTAMP.md`: Analysis reports
- `watermark_analysis_monthly_YYYYMM.md`: Monthly comprehensive reports

## Customization

### Modifying the Schedule
Edit the crontab file and reinstall:
```bash
nano integrated_crontab.txt
./install_crontab.sh
```

### Adding More Datasets
To include additional datasets in the high-frequency updates, modify the `--only` parameter in the `integrated_update.sh` script.

## Troubleshooting

### Common Issues
1. **Data not updating**: Check the logs in the `logs` directory for errors
2. **Cron not running**: Verify with `crontab -l` that the jobs are installed
3. **Script permissions**: Ensure all scripts have execute permissions (`chmod +x script.sh`)

### Log Files
The system maintains log files for each component:
- Integrated update logs: `logs/integrated_update_*.log`
- Weekly update logs: `elexon_weekly_update.log`
- Monthly watermark logs: `logs/watermark_monthly_*.log`

## Benefits of the Integrated System

1. **Automatic startup**: Data collection begins as soon as your machine starts
2. **Regular updates**: Ensures you always have the most recent data (15-minute intervals)
3. **Storage efficiency**: Automatically manages watermark files to save disk space
4. **Data quality monitoring**: Regular analysis reports on data freshness
5. **Comprehensive reporting**: Monthly reports for long-term monitoring

## Next Steps

To further enhance the system, consider:
1. Adding email notifications for failed updates
2. Implementing a dashboard to visualize data freshness
3. Adding more sophisticated error handling and recovery mechanisms
