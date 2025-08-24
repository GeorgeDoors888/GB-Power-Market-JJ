# Live Data Updater for UK Energy Data

## Overview

The Live Data Updater is a service that continuously monitors and updates data from the National Energy System Operator (NESO) and Elexon sources. It specifically focuses on capturing data published within the last 25 hours, ensuring that your datasets are always up-to-date with the most recent energy market information.

## Features

- **Real-time Monitoring**: Continuously checks for new data from NESO and Elexon sources
- **Immediate Updates**: Captures new data as soon as it's published
- **Efficient Storage**: Uploads data to both Google Cloud Storage and BigQuery
- **Smart Deduplication**: Prevents duplicate records in your datasets
- **Configurable Update Frequency**: Different datasets are updated at different intervals based on their update frequency
- **Comprehensive Logging**: Detailed logs of all operations for monitoring and debugging
- **Status Reporting**: Regular reports of available data sources and update statistics

## Available Data Sources

### ELEXON Datasets

- **Demand Outturn**
  - Table: `elexon_demand_outturn`
  - Update Frequency: Every 30 minutes

- **Generation Outturn**
  - Table: `elexon_generation_outturn`
  - Update Frequency: Every 30 minutes

- **System Warnings**
  - Table: `elexon_system_warnings`
  - Update Frequency: Every 60 minutes

### NESO Datasets

- **Demand Forecasts**
  - Table: `neso_demand_forecasts`
  - Update Frequency: Every 60 minutes

- **Wind Forecasts**
  - Table: `neso_wind_forecasts`
  - Update Frequency: Every 60 minutes

- **Carbon Intensity**
  - Table: `neso_carbon_intensity`
  - Update Frequency: Every 60 minutes

- **Interconnector Flows**
  - Table: `neso_interconnector_flows`
  - Update Frequency: Every 60 minutes

- **Balancing Services**
  - Table: `neso_balancing_services`
  - Update Frequency: Every 120 minutes

## Usage

### Starting the Service

To start the Live Data Updater service, run:

```bash
./run_live_data_updater.sh
```

This will start the service in the background and create a log file in the `logs` directory.

### Viewing Available Data Sources

To view a list of all available data sources with their last update times:

```bash
python live_data_updater.py list
```

### Manually Triggering Updates

To manually trigger an update of all datasets:

```bash
python live_data_updater.py update
```

To update only Elexon datasets:

```bash
python live_data_updater.py elexon
```

To update only NESO datasets:

```bash
python live_data_updater.py neso
```

### Stopping the Service

To stop the Live Data Updater service:

```bash
pkill -f live_data_updater.py
```

## Monitoring

### Logs

Logs are stored in the `logs` directory with timestamps. To view the most recent logs:

```bash
tail -f logs/live_data_updater_YYYYMMDD_HHMMSS.log
```

### Statistics

Statistics about the updates are stored in `live_data_update_stats.json`. This file is updated after each update cycle and contains information about:

- Total number of Elexon updates
- Total number of NESO updates
- Total number of records updated
- Last update time
- Last check time for each dataset

## Integration with the Dashboard

The Live Data Updater ensures that your GB Energy Dashboard always displays the most recent data. As new data is published, it is automatically added to the relevant BigQuery tables, which the dashboard queries to display information.

## Technical Details

- **Rate Limiting**: The service respects the rate limits of both the Elexon API (1 request per second) and the NESO API (1 request per 30 seconds)
- **Deduplication**: Before uploading data to BigQuery, the service checks for existing records to prevent duplicates
- **Cloud Storage**: All downloaded data is also stored in Google Cloud Storage for archival purposes
- **Scheduling**: Uses the `schedule` library to manage regular updates at different intervals for different datasets

## Dependencies

- Python 3.7+
- Google Cloud Storage
- Google BigQuery
- `schedule` library for task scheduling
- `pandas` for data manipulation
- `requests` for API calls

## Setup

Make sure you have the necessary Python dependencies installed:

```bash
pip install google-cloud-storage google-cloud-bigquery pandas requests schedule
```

Also, ensure that your Google Cloud credentials are properly set up:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
```

For Elexon API access, set your API key:

```bash
export BMRS_API_KEY="your-bmrs-api-key"
```

## Troubleshooting

If you encounter any issues:

1. Check the logs in the `logs` directory
2. Verify that your Google Cloud credentials are correctly set up
3. Make sure the BMRS API key is valid
4. Check the network connectivity to the NESO and Elexon APIs

## Future Enhancements

- Email notifications for failed updates
- Web interface for monitoring the service
- Advanced error recovery mechanisms
- Support for additional data sources
- Historical data backfilling capabilities
