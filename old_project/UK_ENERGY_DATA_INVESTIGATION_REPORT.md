# UK Energy Data Investigation Report

## Summary of Findings

1. **Data Range Discrepancy**: We've identified a significant gap between the documented data range (2016-2025) and what's actually available in BigQuery tables (primarily 2023-2024).

2. **2016 Data Status**:
   - Only 2 BigQuery tables contain 2016 data: `elexon_fuel_generation` tables in both `uk_energy_data` and `uk_energy_data_gemini_eu` datasets
   - The 2016 data is limited to January 1-8, 2016 (just one week)

3. **GCS Storage Findings**:
   - Discovered historical data in the `elexon-historical-data-storage` bucket
   - Files exist for all years from 2016-2022
   - For 2016, we found both demand and frequency data files

4. **Production Dataset Timeframe**:
   - Most tables in `uk_energy_prod` contain data only from 2023-2024
   - Earliest data in the production dataset starts at 2022-12-31

## Analysis and Recommendations

### 1. Missing Data Identification

We have confirmed that historical data from 2016-2022 exists in Google Cloud Storage but hasn't been fully loaded into BigQuery. Specifically:

- The `elexon-historical-data-storage` bucket contains files for all years 2016-2022
- The files appear to be organized by data type (demand, frequency, generation, etc.)
- The 2016 data we found in BigQuery (Jan 1-8 only) matches the first week of data files found in GCS

### 2. Data Loading Strategy

To resolve the discrepancy between documentation and actual data, we recommend:

1. **Prioritize Data Loading**:
   - Create a data loading pipeline to import the historical GCS data into BigQuery
   - Start with the most critical tables (based on user requirements)
   - Use the existing table schemas in the production dataset

2. **Incremental Loading Approach**:
   - Load data year by year to avoid overwhelming resources
   - Validate data quality after each loading step
   - Update documentation to track progress

### 3. Specific Recommendations

1. **Immediate Action**:
   - Create a detailed inventory of all files in the `elexon-historical-data-storage` bucket
   - Match GCS file types to existing BigQuery table schemas
   - Create a data loading priority list based on user requirements

2. **Implementation Plan**:
   - Develop and test a data loading script for one data type (e.g., demand data)
   - Scale the loading process to handle all data types
   - Set up validation queries to verify data integrity after loading

3. **Documentation Updates**:
   - Update all documentation to accurately reflect current data availability
   - Create a timeline for when historical data will be available
   - Document any known gaps or quality issues in the historical data

## Detailed Data Findings

### BigQuery Tables with 2016 Data

| Dataset | Table | Date Range | Row Count |
|---------|-------|------------|-----------|
| uk_energy_data | elexon_fuel_generation | 2016-01-01 to 2016-01-08 | 4,992 |
| uk_energy_data_gemini_eu | elexon_fuel_generation | 2016-01-01 to 2016-01-08 | 4,992 |

### Production Tables Date Ranges

| Table | Date Range | Rows |
|-------|------------|------|
| elexon_system_warnings | 2023-01-10 to 2024-12-25 | 56 |
| neso_balancing_services | 2023-01-01 to 2024-12-31 | 35,088 |
| neso_carbon_intensity | 2023-01-01 to 2024-12-31 | 35,088 |
| neso_demand_forecasts | 2022-12-31 to 2024-12-30 | 35,088 |
| neso_interconnector_flows | 2023-01-01 to 2024-12-31 | 210,528 |
| neso_wind_forecasts | 2023-01-01 to 2025-01-01 | 175,440 |

### GCS Historical Data Files

The `elexon-historical-data-storage` bucket contains files for all years 2016-2022:

- 2016: 59 files
- 2017: 32 files
- 2018: 32 files
- 2019: 32 files
- 2020: 33 files
- 2021: 33 files
- 2022: 36 files

## Next Steps

1. Create a detailed loading plan for the historical data
2. Develop a prioritized backfill process
3. Update documentation to reflect accurate data availability
4. Implement regular data inventory checks to prevent similar issues in the future

This investigation confirms that most of the 2016-2022 data exists in Google Cloud Storage but has not been loaded into BigQuery. The data is available for loading, and with a proper loading strategy, we can resolve the discrepancy between documentation and available data.
