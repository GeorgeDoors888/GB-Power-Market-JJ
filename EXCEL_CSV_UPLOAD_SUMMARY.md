# Excel/CSV Upload Summary
**Date**: November 18, 2025

## ✅ Successfully Uploaded (3 new files)

### 1. gsp_wind_data_latest.csv
- **BigQuery Table**: `uk_energy_prod.gsp_wind_data_latest`
- **Rows**: 500
- **Size**: 0.05 MB
- **Columns**: 6
- **Description**: Latest GSP wind generation data by Grid Supply Point
- **Contains**: Real-time wind generation and import/export data per GSP

### 2. bmu_registration_data.csv
- **BigQuery Table**: `uk_energy_prod.bmu_registration_data`
- **Rows**: 2,783
- **Size**: 0.54 MB
- **Columns**: 24
- **Description**: BMU (Balancing Mechanism Unit) registration data from Elexon
- **Contains**: BMU IDs, fuel types, lead party names, GSP groups, interconnector info

### 3. All_Generators.xlsx
- **BigQuery Table**: `uk_energy_prod.all_generators`
- **Rows**: 7,384
- **Size**: 6.28 MB
- **Columns**: 70
- **Description**: Comprehensive generator registration data
- **Contains**: MPAN/MSID, customer details, addresses, site info, coordinates, resource types
- **Note**: Multi-sheet Excel file, only Sheet1 contained data

## 📋 Already Uploaded (Previously)

- `uk_power_plants_cva.csv` → `cva_plants` (1,581 rows)
- `generators_list.csv` → `sva_generators` (7,072 rows)
- `offshore_wind_farms.csv` → `offshore_wind_farms` (35 rows)

## 🛠️ Upload Scripts Created

### upload_missing_csv_files.py
- Generic CSV uploader for multiple files
- Handles column name cleaning
- Adds metadata (_uploaded_at, _source_file)
- Sets table descriptions

### upload_all_generators_excel.py
- Excel-specific uploader with multi-sheet support
- Advanced column name sanitization (removes newlines, special chars)
- Detects and uses first row as headers
- Handles data type conversion issues

## 🔧 Technical Notes

### Column Name Cleaning
All column names are sanitized to meet BigQuery requirements:
- Newlines/tabs → spaces → underscores
- Special characters removed or replaced
- Maximum length: 128 characters
- Lowercase for consistency

### Dependencies Installed
- `openpyxl` (3.1.5) - For reading Excel files
- `et-xmlfile` (2.0.0) - Required by openpyxl

### Data Type Handling
- Object columns converted to strings
- NaN values replaced with None
- Metadata columns added for tracking

## 📊 Total Dataset Coverage

**Generator/Plant Data Now in BigQuery**:
1. CVA plants (1,581)
2. SVA generators (7,072)
3. All generators comprehensive (7,384)
4. BMU registration (2,783)
5. Offshore wind farms (35)
6. GSP wind data (500 records)

All generator-related Excel/CSV files are now uploaded to BigQuery.
