# DNO DATA ENHANCED FOLDER ANALYSIS
=====================================================================

## OVERVIEW

The `dno_data_enhanced` folder contains an extensive collection of DNO (Distribution Network Operator) files with detailed charging information spanning multiple years and covering all major UK DNOs. This represents a significant expansion of the data analyzed in our previous scripts.

## DNO COVERAGE

This enhanced dataset includes files from all major UK DNOs:

1. **National Grid (formerly WPD)**:
   - East Midlands (EMEB/MIDE) - MPAN 12
   - West Midlands (WMID) - MPAN 14
   - South Wales (SWAE) - MPAN 21
   - South West (SWEB) - MPAN 22

2. **Northern Powergrid**:
   - Yorkshire - MPAN 15
   - Northeast - MPAN 23

3. **SP Energy Networks**:
   - SP Distribution (Scotland) - MPAN 16
   - SP Manweb - MPAN 13

4. **SSEN**:
   - Scottish Hydro (SHEPD) - MPAN 17
   - Southern Electric (SEPD) - MPAN 20

5. **UK Power Networks**:
   - Eastern (EPN) - MPAN 10
   - London (LPN) - MPAN 11
   - South Eastern (SPN) - MPAN 19

6. **Electricity North West (ENWL)** - MPAN 16

## YEAR COVERAGE

The files span a wide range of years:
- Historical data: 2014-2020
- Current data: 2021-2024
- Future projections: 2025-2027

## FILE TYPES

The collection includes several types of documents:

1. **Schedule of Charges and Other Tables**:
   - Primary documents containing DUoS rates and time bands
   - Example: `sepd---schedule-of-charges-and-other-tables---april-2025-v0.2.xlsx`

2. **CDCM Models** (Common Distribution Charging Methodology):
   - Detailed charge calculation models
   - Example: `shepd_cdcm_v10_20231106_25-26_final.xlsx`

3. **PCDM Models** (Pricing Common Distribution Charging Methodology):
   - Pricing-specific models
   - Example: `shepd_pcdm_v5_20241025_26-27_final.xlsx`

4. **Embedded Networks Files**:
   - Special charging information for embedded networks
   - Example: `sepd---schedule-of-charges-and-other-tables--embedded-networks-april-2025-v.0.2.xlsx`

5. **ARP Models**:
   - Additional regulatory pricing models
   - Example: `shepd-arp-model-2020-21.xlsx`

## DATABASE FILES

The folder also contains database files for structured storage:
- SQLite database: `dno_enhanced.sqlite`
- Parquet files: `collection_summary.parquet` and `/parquet` directory
- Python integration: `load_to_bigquery.py`

## STATISTICAL SUMMARY

Total file count: 192 files
- Northern Powergrid: 38 files
- SSEN (SHEPD & SEPD): 71 files
- National Grid (formerly WPD): 61 files
- ENWL: 9 files
- Other: 13 files

## COMPARATIVE ANALYSIS WITH PREVIOUS DATA

This enhanced dataset represents a significant expansion from our previous analysis:
- **Complete DNO Coverage**: All 14 DNOs are now represented
- **Extended Year Range**: Coverage from 2014 through 2027
- **Multiple Model Types**: Beyond just schedule of charges, includes detailed calculation models
- **Database Integration**: Includes structured data formats for analytics

## VALUE FOR DUOS ANALYSIS

This expanded dataset will enable:

1. **Complete Time Band Analysis**:
   - RED, AMBER, GREEN band definitions for all DNOs
   - Historical changes in time band definitions

2. **Comprehensive Rate Comparison**:
   - Full historical rate trends
   - Predictive analysis for future rates
   - Regional variations across all UK areas

3. **Advanced Analytics**:
   - Correlation between rates and regional factors
   - Year-over-year changes in charging structures
   - Forecasting for budget planning

## NEXT STEPS FOR ANALYSIS

To fully utilize this expanded dataset:

1. **Update Time Band Analyzer**:
   - Enhance the script to process all file formats
   - Add specific parsers for each DNO's file structure

2. **Create Longitudinal Analysis**:
   - Track changes in rates and bands over time
   - Identify trends and forecast future changes

3. **Compare DNO Approaches**:
   - Analyze differences in band definitions between DNOs
   - Quantify regional variations in rates

4. **Database Integration**:
   - Leverage the SQLite database for comprehensive querying
   - Use the BigQuery integration for cloud-based analytics

This enhanced dataset provides the foundation for a complete UK-wide analysis of DUoS charging structures across all DNOs and multiple years.
