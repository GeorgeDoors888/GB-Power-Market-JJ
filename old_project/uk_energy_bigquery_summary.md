# UK Energy BigQuery Dataset Summary

## Overview

This report provides a comprehensive analysis of the UK energy data stored in the BigQuery dataset `uk_energy_prod`. The dataset contains a total of 97 tables, with 88 tables from National Grid ESO (NESO) and 9 tables from Elexon. The data is located in the europe-west2 (London) region, complying with UK data residency requirements.

## Data Sources

### NESO Data (88 tables)

The National Grid ESO data is categorized as follows:
- Skip rates data (29 tables)
- Dispatch transparency (10 tables)
- Static reference data (10 tables)
- Network infrastructure (24 tables)
- Balancing mechanisms (2 tables)
- Demand forecasts (5 tables)
- Capacity market (4 tables)
- Carbon intensity (2 tables)
- Generation data (1 table)
- Constraint information (1 table)

### Elexon Data (9 tables)

Elexon provides market-related data including:
- Demand outturn
- Generation outturn
- System frequency
- System warnings

## Data Timeframes

Most of the time-series data in the dataset covers the period from 2024 to 2025, with some historical tables going back to 2020. The tables appear to be a mix of:

1. **Live production tables** - Empty or with minimal rows, prepared for ongoing data collection
2. **Temporary staging tables** - Containing test data (usually 100 rows) with "_temp_" in the name
3. **Historical imports** - Containing data imported from previous years (2016 onwards)

For instance, the demand forecasts typically cover from August 2025 (current period in test data), while historical balancing mechanism actions go back to April 2020.

## Key Data Tables

### Demand Data

The `neso_demand_forecasts` and `elexon_demand_outturn` tables contain demand forecast and actual data. The forecasts appear to be daily projections, while the outturn data shows the actual demand recorded. This allows for analysis of forecast accuracy and demand patterns.

Key fields in these tables include:
- `settlementDate`: The date for which the data applies
- `settlementPeriod`: The half-hour settlement period within the day
- `demand`: The forecasted or actual demand in MW
- `publishTime`: When the data was published

Sample date ranges:
- `elexon_demand_outturn`: 2025-08-08 (test data)
- `elexon_demand_outturn_temp_20250823001616`: 2025-08-16 to 2025-08-18 (test data)

### Generation Data

Generation data is available in the `elexon_generation_outturn` table, showing actual generation by type. The data includes:
- Total generation output
- Breakdown by fuel type (embedded in nested fields)
- Timestamps and settlement periods

Sample date ranges:
- `elexon_generation_outturn_temp_20250823001619`: 2025-08-16 to 2025-08-18 (test data)

### Balancing Mechanism Data

The dispatch transparency tables contain detailed information about Balancing Mechanism actions taken by the system operator. These tables cover multiple financial years from April 2020 to March 2025, enabling long-term analysis of balancing actions:

- `neso_dispatch_transparency_all_boas_april2020_march2021`
- `neso_dispatch_transparency_all_boas_april2021_march2022`
- `neso_dispatch_transparency_all_boas_april2022_march2023`
- `neso_dispatch_transparency_all_boas_april2023_march2024`
- `neso_dispatch_transparency_all_boas_april2024_march2025`

### Geographic Data

The dataset includes several geographic data tables:
- `neso_dno_licence_areas`: Distribution Network Operator boundaries
- `neso_generation_charging_zones`: Generation charging zones
- `neso_grid_supply_points`: Grid connection points (multiple versions from 2018-2025)

These tables include GeoJSON data that can be used for spatial visualization and analysis.

### Reference Data

Static reference tables provide important context:
- `neso_transmission_capacity_tec_register`: Transmission capacity information
- `neso_school_holiday`: School holiday dates affecting demand patterns
- `neso_static_system_operating_plan`: System operation parameters

## Data Structure Analysis

### Schema Design

The tables follow consistent schema patterns:

1. **Time-series data tables** typically include:
   - Timestamp columns (publishTime, startTime)
   - Date columns (settlementDate)
   - Period identifiers (settlementPeriod)
   - Numeric measurements (demand, generation, frequency)

2. **Geographic data tables** include:
   - GeoJSON formatted spatial data
   - Identifiers and metadata for each geographic feature
   - WGS84 coordinate reference system for international compatibility

3. **Reference data tables** include:
   - Static identifiers
   - Descriptive text fields
   - Categorical variables
   - Date ranges for validity periods

### Data Types

The dataset uses appropriate BigQuery data types:
- `DATE` for calendar dates
- `TIMESTAMP` and `DATETIME` for time-precise events
- `INTEGER` for discrete values and IDs
- `FLOAT` for continuous measurements
- `STRING` for textual data and identifiers
- `RECORD` for nested structures (particularly in Elexon import tables)

## Data Quality Assessment

Based on the table analysis, several observations can be made about data quality:

1. **Completeness**: Many production tables are currently empty or contain minimal data, suggesting they are prepared for ongoing data collection.

2. **Test Data**: Temporary tables with the "_temp_" suffix contain test data (usually exactly 100 rows), with clearly synthetic values (e.g., "Test data 13").

3. **Schema Design**:
   - Properly typed schemas with appropriate data types
   - Some tables use nested RECORD types for complex data structures
   - Consistent naming conventions across related tables

4. **Historical Coverage**: Good historical coverage for key metrics, with data going back to 2016 for some metrics and comprehensive coverage from 2020 onwards.

5. **Spatial Data**: The inclusion of geographic data enables spatial analysis of the UK energy system.

## Recommendations

Based on the dataset analysis, we recommend:

1. **Production Data Collection**: Implement automated data collection processes to populate the currently empty production tables.

2. **Data Type Standardization**: Ensure numeric data is consistently stored as numeric types (FLOAT, INTEGER) rather than STRING to facilitate analysis.

3. **Date Range Validation**: Verify that date ranges in historical imports align properly with the intended coverage periods.

4. **Test Data Cleanup**: Consider removing or clearly marking test data tables to avoid confusion in analysis.

5. **Documentation**: Create comprehensive data dictionary and schema documentation for all tables.

6. **Query Optimization**: Design optimized views and partitioning strategies for frequently accessed data patterns.

## Conclusion

The BigQuery dataset `uk_energy_prod` provides a comprehensive foundation for UK energy system analysis, with a well-structured collection of tables covering key aspects of the electricity system. While many tables currently contain test data or are empty, the dataset structure is robust and ready for production data collection and analysis.

The geographic data provides unique opportunities for spatial analysis, while the historical balancing mechanism data enables detailed study of system operation. The consistent schema design and proper regional placement (europe-west2) ensure the dataset is well-positioned for both operational and analytical use cases.
