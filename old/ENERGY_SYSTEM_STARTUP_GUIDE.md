# Energy Data System Automated Startup and Updates

This document explains how the automated startup and update system works for the energy data pipeline.

## System Components

1. **energy_system_startup.py**: The main startup manager that runs at system boot/login
2. **update_all_data_15min.py**: The 15-minute update script (enhanced with continuous mode)
3. **LaunchAgent**: macOS service that runs the startup manager automatically at login

## How It Works

### Initial Setup at System Startup

When your computer starts up or you log in, the LaunchAgent automatically runs the `energy_system_startup.py` script, which:

1. Prompts you for how many days of historical data to catch up on
2. Runs the data ingestion to catch up on any data missed while your machine was off
3. Starts the continuous 15-minute update process in the background

### Continuous Updates While Running

Once started, the system:

1. Runs high-priority Elexon data updates every 15 minutes (FREQ, FUELINST, BOD, etc.)
2. Runs standard-priority Elexon data updates every 30 minutes (MELS, MILS, etc.)
3. Updates REMIT data every 30 minutes
4. Updates NESO data every 2 hours
5. Keeps all data current in BigQuery

## Installation Instructions

1. Make the startup script executable:
   ```bash
   chmod +x /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop/energy_system_startup.py
   ```

2. Copy the LaunchAgent file to your user's LaunchAgents directory:
   ```bash
   mkdir -p ~/Library/LaunchAgents
   cp /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop/com.georgemajor.energy-system-startup.plist ~/Library/LaunchAgents/
   ```

3. Load the LaunchAgent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.georgemajor.energy-system-startup.plist
   ```

## Manual Operation

If you need to run the system manually:

1. **Start the full system** (catch up and continuous updates):
   ```bash
   cd /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop
   source .venv/bin/activate
   python energy_system_startup.py
   ```

2. **Just catch up on missed data** (no continuous updates):
   ```bash
   cd /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop
   source .venv/bin/activate
   python energy_system_startup.py --skip-15min
   ```

3. **Just start continuous updates** (no catch up):
   ```bash
   cd /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop
   source .venv/bin/activate
   python energy_system_startup.py --skip-catchup
   ```

4. **Run a single update cycle**:
   ```bash
   cd /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop
   source .venv/bin/activate
   python update_all_data_15min.py
   ```

## Monitoring and Logs

The system produces several log files to help you monitor its operation:

1. **startup_manager.log**: Logs from the startup manager
2. **15_minute_update.log**: Logs from the 15-minute update process
3. **launchagent.log**: Output from the LaunchAgent
4. **launchagent_error.log**: Error output from the LaunchAgent
5. **15_minute_update_last_run.json**: JSON summary of the last update cycle
6. **system_startup.json**: Record of when the system was last started

You can check these logs to verify the system is working correctly.

## Stopping the System

To stop the continuous updates, you can:

1. **Gracefully stop the startup manager**:
   Press Ctrl+C if it's running in a terminal, or find its process and send SIGTERM:
   ```bash
   pkill -f energy_system_startup.py
   ```

2. **Unload the LaunchAgent** (to prevent automatic startup):
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.georgemajor.energy-system-startup.plist
   ```

## Troubleshooting

If you encounter issues:

1. Check the log files mentioned above
2. Verify the Python virtual environment is activated
3. Make sure all required dependencies are installed
4. Ensure the API credentials are properly configured

## System Recovery

If the system has been down for an extended period:

1. Run with a larger number of days to catch up:
   ```bash
   python energy_system_startup.py --days 7
   ```

2. For very long outages, consider using the batch ingestion scripts directly with custom date ranges.
