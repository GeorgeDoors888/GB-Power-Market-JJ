# UK Energy System Dashboard - User Guide

## System Warnings and Outages Monitor

### Overview

The UK Energy System Dashboard now includes enhanced monitoring for system warnings and outages reported by ELEXON. This feature allows you to stay informed about critical events in the UK electricity grid.

### Accessing System Warnings

1. Launch the dashboard by running: `streamlit run live_energy_dashboard.py`
2. Navigate to the "System Warnings" tab (4th tab in the dashboard)
3. The dashboard will automatically display any warnings from the last 7 days

### Understanding the Warnings Display

Each warning card contains:

- **Date**: When the warning was issued
- **Type**: The category of warning (e.g., "System Warning", "Capacity Market Notice", "Electricity Margin Notice")
- **Message**: The full text of the warning message

### Features

- **Automatic Refresh**: The dashboard automatically refreshes every 5 minutes to show the latest warnings
- **Manual Refresh**: Click the "🔄 Refresh Data" button at the top of the page to force an immediate refresh
- **Data Caching**: For performance reasons, warnings data is cached for 5 minutes

### Monitoring Process

Behind the scenes, our system:

1. Connects to the ELEXON BMRS API every 10 minutes via the `system_warnings_monitor.py` script
2. Fetches the latest system warnings and notices
3. Stores them in the BigQuery `elexon_system_warnings` table
4. The dashboard reads from this table when you access the System Warnings tab

### Troubleshooting

If you encounter any issues:

1. Check the Data Update Status section (click to expand at the top of the dashboard)
2. Verify that the `elexon_system_warnings` table shows a recent date
3. If data appears outdated, you can run `python restart_energy_system.sh` to restart the monitoring processes

### Support

For any issues or questions, please contact the data engineering team or raise an issue in the project repository.
