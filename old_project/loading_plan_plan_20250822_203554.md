# Historical Data Loading Plan
Generated: 2025-08-22 20:35:54
All years

## File to Table Mapping

| GCS Category | File Count | Target BigQuery Table | Sample Files |
|--------------|------------|----------------------|--------------|
| beb | 96 | Unknown - manual mapping needed.Unknown - manual mapping needed | beb/beb_20160101_0000_20160101_0200.json<br>beb/beb_20160101_0200_20160101_0400.json<br>beb/beb_20160101_0400_20160101_0600.json |
| demand | 8 | uk_energy_prod.elexon_demand_outturn | demand/demand_2016-01-01.json<br>demand/demand_2016-01-02.json<br>demand/demand_2016-01-03.json |
| frequency | 8 | uk_energy_data.elexon_frequency | frequency/frequency_2016-01-01.json<br>frequency/frequency_2016-01-02.json<br>frequency/frequency_2016-01-03.json |
| generation | 9 | uk_energy_prod.elexon_generation_outturn | generation/generation_2016-01-01.json<br>generation/generation_2016-01-02.json<br>generation/generation_2016-01-03.json |
| historical_data | 714 | Unknown - manual mapping needed.Unknown - manual mapping needed | historical_data/2024-07/balancing/emergency_orders/EBOCF_20240701.csv<br>historical_data/2024-07/balancing/emergency_orders/EBOCF_20240702.csv<br>historical_data/2024-07/balancing/emergency_orders/EBOCF_20240703.csv |
| neso | 165 | Unknown - manual mapping needed.Unknown - manual mapping needed | neso/1-day-ahead-demand-forecast/9847e7bb-986e-49be-8138-717b25933fbb/1-day-ahead-demand-forecast_9847e7bb-986e-49be-8138-717b25933fbb_20250811_110032.275316.csv<br>neso/1-day-ahead-demand-forecast/9847e7bb-986e-49be-8138-717b25933fbb/1-day-ahead-demand-forecast_9847e7bb-986e-49be-8138-717b25933fbb_20250812_110027.408541.csv<br>neso/1-day-ahead-demand-forecast/aec5601a-7f3e-4c4c-bf56-d8e4184d3c5b/1-day-ahead-demand-forecast_aec5601a-7f3e-4c4c-bf56-d8e4184d3c5b_20250811_110008.273742.csv |

## Loading Steps

Follow these steps to load the historical data into BigQuery:

1. **Verify Table Schemas**: Ensure target tables exist and have compatible schemas
2. **Review Sample Files**: Check sample files to confirm data format matches table schema
3. **Execute Loading Commands**: Run the following loading commands

```bash
# Load demand files into uk_energy_prod.elexon_demand_outturn
bq load --source_format=CSV uk_energy_prod.elexon_demand_outturn gs://elexon-historical-data-storage/demand/*

# Load frequency files into uk_energy_data.elexon_frequency
bq load --source_format=CSV uk_energy_data.elexon_frequency gs://elexon-historical-data-storage/frequency/*

# Load generation files into uk_energy_prod.elexon_generation_outturn
bq load --source_format=CSV uk_energy_prod.elexon_generation_outturn gs://elexon-historical-data-storage/generation/*

```

4. **Validate Loaded Data**: Run these validation queries

```sql
-- Validate uk_energy_prod.elexon_demand_outturn
SELECT COUNT(*) as row_count, MIN(timestamp_column) as min_date, MAX(timestamp_column) as max_date FROM uk_energy_prod.elexon_demand_outturn

-- Validate uk_energy_data.elexon_frequency
SELECT COUNT(*) as row_count, MIN(timestamp_column) as min_date, MAX(timestamp_column) as max_date FROM uk_energy_data.elexon_frequency

-- Validate uk_energy_prod.elexon_generation_outturn
SELECT COUNT(*) as row_count, MIN(timestamp_column) as min_date, MAX(timestamp_column) as max_date FROM uk_energy_prod.elexon_generation_outturn

```

## Post-Loading Tasks

1. Update data documentation to reflect newly loaded historical data
2. Verify data quality using standard validation queries
3. Update dashboards and applications to use the historical data
