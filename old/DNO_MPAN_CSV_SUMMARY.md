# DNO and MPAN CSV Files Summary
*Generated on: 2025-09-15*

This report summarizes the key CSV files related to DNO (Distribution Network Operator) and MPAN (Meter Point Administration Number) data that have been modified in the last 3 days.

## MPAN-Related Files

### `example_mpan_data_enriched.csv`
- **Size**: 2.9 KB
- **Modified**: 2025-09-15
- **Columns**: 13 (customer_id, customer_name, postcode, MPAN, mpan_core, distributor_id, mpan_valid, DNO_Key, DNO_Name, Short_Code, Market_Participant_ID, GSP_Group_ID, GSP_Group_Name)
- **Rows**: Sample data with enriched DNO information for each MPAN
- **Purpose**: Demonstrates the mapping of MPANs to DNO information via the distributor_id

### `example_mpan_data_with_duos.csv`
- **Size**: 1.9 KB 
- **Purpose**: Links MPAN data with DUoS (Distribution Use of System) charges

### `example_mpan_data.csv`
- **Size**: 0.9 KB
- **Purpose**: Basic MPAN customer data for testing and demonstration

## DNO DUoS Summary Files

### `DNO_DUoS_Summary.csv`
- **Size**: 1.2 KB
- **Modified**: 2025-09-14
- **Columns**: 4 (DNO_Name, Files_Count, Years_Covered, Band_Distribution)
- **Rows**: Summary of each DNO's data coverage
- **Purpose**: High-level overview of DUoS data availability by DNO

### `DNO_DUoS_Band_Stats.csv`
- **Size**: 5.5 KB
- **Columns**: 11 (dno_name, dno_key, mpan_code, year, band, sheet_name, time_period, min_rate, max_rate, mean_rate, median_rate, count, unit)
- **Purpose**: Statistical analysis of DUoS bands and rates by DNO

## DNO Reference Files

### `DNO_Reference.csv`
- **Size**: 2.0 KB
- **Columns**: 7 (MPAN_Code, DNO_Key, DNO_Name, Short_Code, Market_Participant_ID, GSP_Group_ID, GSP_Group_Name)
- **Purpose**: Master reference table for mapping MPAN distributor IDs to DNO information

## Complete DUoS Data Files

### `DNO_DUoS_All_Data.csv`
- **Size**: 479.9 KB
- **Modified**: 2025-09-14
- **Columns**: 16 (DNO_Name, DNO_Key, MPAN_Code, Short_Code, Year, Band, Time_Period, Min_Rate_p_kWh, Max_Rate_p_kWh, Mean_Rate_p_kWh, Median_Rate_p_kWh, GSP_Group_ID, GSP_Group_Name, Count, Unit, File_Path)
- **Rows**: Comprehensive dataset with all DUoS rates across DNOs and years
- **Purpose**: Complete consolidated DUoS data for analysis and reporting

### `duos_all_bands_enhanced_v3.csv`
- **Size**: 20.9 KB
- **Purpose**: Enhanced DUoS band data with additional metadata

### `duos_all_bands_combined.csv`
- **Size**: 9.2 KB
- **Purpose**: Combined DUoS band rates across different DNOs

### `duos_time_band_rates.csv`
- **Size**: 3.3 KB
- **Purpose**: Time-specific DUoS band rates

## DNO-Specific Files

Multiple CSV files for individual DNOs are also available, containing year-specific DUoS rates:

- Electricity North West
- National Grid Electricity Distribution (East Midlands, South Wales, South West)
- Northern Powergrid (Northeast, Yorkshire)
- Scottish and Southern Electricity Networks (SEPD, SHEPD)

## Usage Notes

1. The `DNO_Reference.csv` file is the authoritative source for mapping MPAN distributor IDs to DNO information
2. The `mpan_dno_mapper.py` script can be used to enrich MPAN data with DNO information as demonstrated in `example_mpan_data_enriched.csv`
3. For comprehensive DUoS analysis, use the `DNO_DUoS_All_Data.csv` file which consolidates data from all DNOs and years
4. Time band information varies by DNO and year, with RED, AMBER, GREEN classifications used consistently
