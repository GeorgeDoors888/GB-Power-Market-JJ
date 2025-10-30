# MPAN to DNO Mapping: Implementation Summary

## Overview

I've created a comprehensive solution for identifying Distribution Network Operators (DNOs) from MPANs (Meter Point Administration Numbers) in your data, and integrating this information with your existing DNO DUoS data.

## Files Created

1. **`mpan_dno_mapper.py`**: The main script for parsing MPANs and mapping to DNOs
   - Implements industry-standard MPAN validation and DNO mapping
   - Handles various MPAN formats (with spaces, hyphens, etc.)
   - Includes the complete DNO lookup table
   - Provides functions for enriching CSV files with DNO information
   - Can merge with your existing DUoS data

2. **`MPAN_DNO_MAPPING_GUIDE.md`**: Detailed documentation
   - Explains MPAN structure and Distributor ID
   - Documents the DNO lookup table
   - Provides usage examples
   - Explains integration with your DUoS data

3. **`mpan_dno_mapper_demo.py`**: Demo script showing the mapper in action
   - Tests with example MPANs
   - Processes a sample CSV file
   - Shows how to merge with your DUoS reference data

4. **`example_mpan_data.csv`**: Sample data for testing
   - Contains various MPAN formats
   - Covers all DNO regions in the UK

## How It Works

The implementation follows the industry-standard approach:

1. **MPAN Parsing**: Extracts the MPAN core (13 digits) from various input formats
2. **Validation**: Checks that the MPAN core is valid using the check digit algorithm
3. **DNO Identification**: Maps the first two digits (Distributor ID) to the corresponding DNO
4. **Data Enrichment**: Adds DNO information to CSV files
5. **DUoS Integration**: Merges MPAN data with your existing DUoS reference data

## Features

- **Comprehensive DNO Lookup**: Includes all 14 DNO regions in the UK
- **Robust MPAN Handling**: Handles various formats and validates check digits
- **Flexible Integration**: Works with your existing DUoS data structure
- **Clear Documentation**: Detailed guides and examples
- **Easy to Use**: Simple command-line interface and Python API

## Usage

### Basic MPAN Processing

```bash
python mpan_dno_mapper.py input.csv output_enriched.csv --mpan-column "MPAN"
```

### Merging with DUoS Data

```bash
python mpan_dno_mapper.py input.csv output_enriched.csv --mpan-column "MPAN" --duos-file duos_outputs2/gsheets_csv/DNO_Reference_20250914_195528.csv
```

### As a Python Module

```python
from mpan_dno_mapper import enrich_dataframe, process_csv_file, merge_with_duos_data

# Enrich a DataFrame with DNO information
enriched_df = enrich_dataframe(df, mpan_column="MPAN")

# Process a CSV file
process_csv_file("input.csv", "output.csv", mpan_column="MPAN")

# Merge with DUoS data
merge_with_duos_data("enriched.csv", "duos_ref.csv", "merged.csv")
```

## Next Steps

1. **Integrate with Your Workflow**: Use the script in your data processing pipeline
2. **Upload to Google Sheets**: Use your existing scripts to upload the enriched data
3. **Extend as Needed**: The code is modular and can be extended for additional requirements

## References

Based on official UK electricity industry standards and documentation:
- Elexon "MSID and MPAN Guidance"
- EDF Energy documentation
- DCUSA / BSCP standards
