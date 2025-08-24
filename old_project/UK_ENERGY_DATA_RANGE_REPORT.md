# UK Energy Data Range Analysis (2016-2025)

## Summary of Findings

- **Only 2 tables contain 2016 data**: Both are `elexon_fuel_generation` tables (in different datasets)
- **Limited 2016 data**: Only covers January 1-8, 2016 (just one week)
- **Main production dataset contains only 2023-2024 data**: Most tables in `uk_energy_prod` start in 2023
- **Many tables appear empty**: Several tables show "None to None" date ranges with 0 rows

## Detailed Analysis

### Tables with 2016 Data

Only two tables contain data from 2016, and both only have the first week of January 2016:

1. `uk_energy_data.elexon_fuel_generation`: 2016-01-01 to 2016-01-08 (4,992 rows)
2. `uk_energy_data_gemini_eu.elexon_fuel_generation`: 2016-01-01 to 2016-01-08 (4,992 rows)

### Tables with Recent Data (2023-2025)

The main production dataset (`uk_energy_prod`) contains data primarily from 2023-2024:

| Table | Date Range | Rows |
|-------|------------|------|
| elexon_system_warnings | 2023-01-10 to 2024-12-25 | 56 |
| neso_balancing_services | 2023-01-01 to 2024-12-31 | 35,088 |
| neso_carbon_intensity | 2023-01-01 to 2024-12-31 | 35,088 |
| neso_demand_forecasts | 2022-12-31 to 2024-12-30 | 35,088 |
| neso_interconnector_flows | 2023-01-01 to 2024-12-31 | 210,528 |
| neso_wind_forecasts | 2023-01-01 to 2025-01-01 | 175,440 |

### Other Notable Date Ranges

- `uk_energy_data.met_office_weather`: 2024-01-01 to 2024-07-31 (213 rows)
- `uk_energy_data_gemini_eu.met_office_weather`: 2024-01-01 to 2024-07-31 (213 rows)
- `uk_energy_data.elexon_frequency`: 2025-08-07 to 2025-08-08 (46,088 rows)
- `uk_energy_data_gemini_eu.elexon_frequency`: 2025-08-07 to 2025-08-08 (46,088 rows)

### Empty or Problem Tables

Many tables appear to be empty or have issues, showing "None to None" date ranges with 0 rows. This could indicate:

1. Recently created tables that haven't been populated yet
2. Views that aren't properly resolving to data
3. Tables with permission issues

## Recommendations

1. **Investigate the Missing 2016-2022 Data**:
   - Check if this data exists in Google Cloud Storage buckets but hasn't been loaded to BigQuery
   - Verify if documentation is incorrect about the 2016 start date
   - Check if data is in other projects/datasets not covered in this scan

2. **Review Empty Tables**:
   - Determine if the empty tables are intentional or indicate data loading issues
   - Verify permissions and access for these tables

3. **Data Backfill Strategy**:
   - If 2016-2022 data exists elsewhere, create a plan to backfill the BigQuery tables
   - Prioritize which historical data is most critical to recover

4. **Documentation Update**:
   - Update documentation to accurately reflect the actual date ranges available
   - Clearly mark which datasets contain which date ranges

5. **Regular Data Inventory**:
   - Implement regular data inventory checks to catch issues with data availability
   - Include date range verification in data quality monitoring

This report confirms that the concern about missing 2016-2022 data is valid. The documentation indicating data from 2016-2025 does not match the actual available data in BigQuery, which primarily covers 2023-2025, with only a single week of 2016 data in two tables.

## Recommendations

1. **Investigate the Missing 2016-2022 Data**:
   - Check if this data exists in Google Cloud Storage buckets but hasn't been loaded to BigQuery
   - Verify if documentation is incorrect about the 2016 start date
   - Check if data is in other projects/datasets not covered in this scan

2. **Review Empty Tables**:
   - Determine if the empty tables are intentional or indicate data loading issues
   - Verify permissions and access for these tables

3. **Data Backfill Strategy**:
   - If 2016-2022 data exists elsewhere, create a plan to backfill the BigQuery tables
   - Prioritize which historical data is most critical to recover

4. **Documentation Update**:
   - Update documentation to accurately reflect the actual date ranges available
   - Clearly mark which datasets contain which date ranges

5. **Regular Data Inventory**:
   - Implement regular data inventory checks to catch issues with data availability
   - Include date range verification in data quality monitoring

This report confirms that the concern about missing 2016-2022 data is valid. The documentation indicating data from 2016-2025 does not match the actual available data in BigQuery, which primarily covers 2023-2025, with only a single week of 2016 data in two tables.
