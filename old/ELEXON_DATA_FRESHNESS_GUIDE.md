# Elexon BMRS API Data Freshness Guide

## Understanding Data Availability and Freshness

The Elexon BMRS (Balancing Mechanism Reporting Service) API provides various UK electricity market datasets with different publication schedules and latencies. This document explains how to ensure you're getting the most recent data available.

## Data Publication Delays

Most BMRS datasets have some inherent publication delay due to:

1. **Processing Time**: Raw data needs validation and processing before publication
2. **Settlement Periods**: UK electricity market operates in 30-minute settlement periods
3. **API Caching**: The API itself may cache responses for performance reasons

## Dataset Freshness Categories

### High-Frequency Datasets (15-minute update cycle)
- **FREQ**: System frequency (1-5 minute delay)
- **FUELINST**: Fuel mix generation (5-10 minute delay)
- **BOD**: Bid-Offer Data (5-15 minute delay)
- **BOALF**: Bid-Offer Acceptance (5-15 minute delay)
- **COSTS**: System Buy/Sell Prices (10-15 minute delay)
- **DISBSAD**: Disaggregated Balancing Actions (10-15 minute delay)

### Medium-Frequency Datasets (30-minute update cycle)
- **MELS**: Maximum Export Limit (10-20 minute delay)
- **MILS**: Maximum Import Limit (10-20 minute delay)
- **QAS**: Acceptance Data (15-30 minute delay)
- **NETBSAD**: Net Balancing Services Adjustment (15-30 minute delay)
- **PN**: Physical Notification (15-30 minute delay)
- **QPN**: Quiescent Physical Notification (15-30 minute delay)
- **IMBALNGC**: Imbalance Data (15-30 minute delay)

## Retrieving the Most Recent Data

To retrieve the most recent data from the Elexon API:

1. **Use Short Time Windows**: Request only the last 15-30 minutes of data
2. **Include Buffer Time**: End time should be 5-10 minutes before current time
3. **Include the right parameters**: Some datasets require specific parameters

## Using Our Tools

We now have three methods to retrieve data:

1. **Regular Ingestion**: Use `ingest_elexon_fixed.py` with specific date ranges
   ```bash
   python ingest_elexon_fixed.py --start 2025-09-20 --end 2025-09-21 --only FREQ,FUELINST
   ```

2. **Recent Data Retrieval**: Use `fetch_recent_elexon.py` to automatically target recent data
   ```bash
   python fetch_recent_elexon.py
   ```

3. **IRIS Real-Time Push**: Use our Elexon IRIS client for real-time data push
   ```bash
   cd elexon_iris
   python client.py
   ```

   This method receives data directly from Elexon as soon as it's published, providing the lowest possible latency.

## Choosing the Right Method

- **For historical data**: Use `ingest_elexon_fixed.py` with specific date ranges
- **For recent data (last few hours)**: Use `fetch_recent_elexon.py`
- **For real-time, lowest latency data**: Use the IRIS client in the `elexon_iris` directory

See `elexon_iris/ELEXON_IRIS_SETUP.md` for detailed setup instructions for the IRIS client.

## Troubleshooting

If you're not seeing the most recent data:

1. **Check API Status**: Elexon occasionally has service disruptions
2. **Verify Date Parameters**: Ensure you're using proper ISO8601 format with timezone
3. **Look for API Messages**: Error responses may indicate issues with specific datasets
4. **Consider Dataset-Specific Parameters**: Some datasets require filters like BM Unit IDs

## API Response Schema

The API returns data in JSON format with timestamps in UTC. Settlement dates and periods are local UK time (accounting for British Summer Time when applicable).

## Monitoring Data Freshness

Use our data freshness monitoring script to check the latest data in BigQuery:
```bash
python check_latest_data.py
```

This will show the most recent settlement dates across all relevant tables.
