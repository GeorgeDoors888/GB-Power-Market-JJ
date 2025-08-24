# System Warnings & Outages Monitor

## Overview
The system now includes a dedicated monitor for UK electricity system warnings and outages. This enhanced monitoring solution addresses the previous issues with the live data updater and provides more reliable monitoring of system events.

## Key Features

### Dedicated Process
- The system warnings monitor runs as a separate process from the main data updater
- Checks for warnings every 10 minutes (vs hourly in the main updater)
- More robust error handling and logging

### Enhanced Data Collection
- Collects system warnings data from ELEXON BMRS API via the SYSWARN endpoint
- Looks back 48 hours for warnings to ensure no events are missed
- Proper deduplication to avoid duplicate entries in BigQuery

### Warning Detection
- Immediate logging of new warnings with detailed information
- Classification by warning type
- Full warning text captured and stored

### Reliability Improvements
- Auto-restart capability to prevent hanging
- Process cleanup to avoid multiple instances
- Uses virtual environment for dependency isolation

## How It Works

1. **System Warnings Endpoint**
   - Endpoint: `datasets/SYSWARN`
   - Table: `elexon_system_warnings`
   - Check frequency: Every 10 minutes

2. **Storage**
   - Warnings are stored in both Cloud Storage and BigQuery
   - Full warning details preserved including timestamp, type, and text

3. **Starting the Monitor**
   - Use the `restart_energy_system.sh` script to start/restart the system
   - Handles termination of hung processes
   - Starts both the warnings monitor and standard data updater

## Viewing Warnings

You can view system warnings through:

1. **Log Files**
   - `system_warnings_monitor.log` shows real-time warnings
   - New warnings are clearly marked with ⚠️ in the logs

2. **BigQuery**
   - Query the `elexon_system_warnings` table in BigQuery
   - Filter by timestamp to see recent warnings

3. **Dashboard**
   - The live energy dashboard includes a warnings section
   - Shows active and recent warnings

## Troubleshooting

If the system warnings monitor stops working:

1. Check if processes are running:
   ```
   ps aux | grep python
   ```

2. View the most recent logs:
   ```
   tail -50 system_warnings_monitor.log
   ```

3. Restart the system using the restart script:
   ```
   ./restart_energy_system.sh
   ```

The dedicated System Warnings Monitor ensures you'll never miss important system warnings or outages in the UK electricity grid.
