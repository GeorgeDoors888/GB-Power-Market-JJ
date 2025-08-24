#!/usr/bin/env python3
"""
Summary of UK Energy Data Investigation and Resolution

This script summarizes the findings of our investigation into the UK energy data
range discrepancy and provides recommendations for resolving the issue.
"""

import json
from datetime import datetime

def generate_summary():
    """Generate a summary of the investigation and resolution steps."""
    
    # Current findings
    findings = {
        "investigation_date": "2025-08-22",
        "data_range_discrepancy": {
            "documented_range": "2016-2025",
            "actual_range": "primarily 2023-2024",
            "tables_with_2016_data": [
                {"dataset": "uk_energy_data", "table": "elexon_fuel_generation", "date_range": "2016-01-01 to 2016-01-08"},
                {"dataset": "uk_energy_data_gemini_eu", "table": "elexon_fuel_generation", "date_range": "2016-01-01 to 2016-01-08"}
            ]
        },
        "historical_data_location": {
            "gcs_bucket": "elexon-historical-data-storage",
            "file_counts_by_year": {
                "2016": 59,
                "2017": 32,
                "2018": 32,
                "2019": 32,
                "2020": 33,
                "2021": 33,
                "2022": 36
            }
        },
        "resolution_tools": [
            {"name": "check_date_ranges_2016_to_present.py", "purpose": "Identify date ranges in BigQuery tables"},
            {"name": "scan_gcs_for_historical_data.py", "purpose": "Find historical data in GCS buckets"},
            {"name": "gcs_to_bq_loader.py", "purpose": "Generate loading plans for historical data"},
            {"name": "load_2016_data.py", "purpose": "Directly load 2016 data from GCS to BigQuery"}
        ],
        "report_files": [
            {"name": "UK_ENERGY_DATA_INVESTIGATION_REPORT.md", "purpose": "Comprehensive findings report"},
            {"name": "uk_energy_date_ranges_*.md", "purpose": "BigQuery table date range analysis"},
            {"name": "gcs_historical_data_scan_*.md", "purpose": "GCS historical data analysis"},
            {"name": "loading_plan_*.md", "purpose": "Data loading plans"}
        ]
    }
    
    # Resolution steps
    resolution_steps = [
        {
            "step": 1,
            "description": "Load 2016 data from GCS to BigQuery",
            "command": "python load_2016_data.py",
            "estimated_time": "30 minutes"
        },
        {
            "step": 2,
            "description": "Verify 2016 data loading",
            "command": "SELECT COUNT(*) as row_count, MIN(date_column) as min_date, MAX(date_column) as max_date FROM table WHERE EXTRACT(YEAR FROM date_column) = 2016",
            "estimated_time": "5 minutes"
        },
        {
            "step": 3,
            "description": "Generate loading plan for 2017-2022 data",
            "command": "python gcs_to_bq_loader.py --bucket elexon-historical-data-storage",
            "estimated_time": "10 minutes"
        },
        {
            "step": 4,
            "description": "Execute loading plan for 2017-2022 data",
            "command": "Follow instructions in loading_plan_*.md",
            "estimated_time": "2-3 hours"
        },
        {
            "step": 5,
            "description": "Update documentation with actual data ranges",
            "command": "Manual documentation updates",
            "estimated_time": "30 minutes"
        }
    ]
    
    # Combine everything into a complete summary
    summary = {
        "title": "UK Energy Data Range Investigation and Resolution",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "findings": findings,
        "resolution_steps": resolution_steps,
        "conclusion": "The investigation confirms that there is a significant discrepancy between the documented data range (2016-2025) and what's actually available in BigQuery (primarily 2023-2024). However, we've located historical data from 2016-2022 in GCS storage that can be loaded to resolve this issue. The provided tools and reports should enable a complete resolution of this data discrepancy."
    }
    
    # Save the summary to a JSON file
    with open("uk_energy_data_investigation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Generate a readable markdown report
    md_report = f"""# UK Energy Data Range Investigation and Resolution
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Investigation Findings

### Data Range Discrepancy
- **Documented Range:** 2016-2025
- **Actual Range:** Primarily 2023-2024 
- **Tables with 2016 Data:** Only 2 tables contain 2016 data, and only for Jan 1-8, 2016:
  - `uk_energy_data.elexon_fuel_generation`: 2016-01-01 to 2016-01-08
  - `uk_energy_data_gemini_eu.elexon_fuel_generation`: 2016-01-01 to 2016-01-08

### Historical Data Location
- **GCS Bucket:** `elexon-historical-data-storage`
- **Files by Year:**
  - 2016: 59 files
  - 2017: 32 files
  - 2018: 32 files
  - 2019: 32 files
  - 2020: 33 files
  - 2021: 33 files
  - 2022: 36 files

## Resolution Tools

The following tools were developed to investigate and resolve this issue:

1. **check_date_ranges_2016_to_present.py**  
   Purpose: Identify date ranges in BigQuery tables

2. **scan_gcs_for_historical_data.py**  
   Purpose: Find historical data in GCS buckets

3. **gcs_to_bq_loader.py**  
   Purpose: Generate loading plans for historical data

4. **load_2016_data.py**  
   Purpose: Directly load 2016 data from GCS to BigQuery

## Resolution Steps

1. **Load 2016 data from GCS to BigQuery**  
   Command: `python load_2016_data.py`  
   Estimated time: 30 minutes

2. **Verify 2016 data loading**  
   Command: Run validation queries against loaded tables  
   Estimated time: 5 minutes

3. **Generate loading plan for 2017-2022 data**  
   Command: `python gcs_to_bq_loader.py --bucket elexon-historical-data-storage`  
   Estimated time: 10 minutes

4. **Execute loading plan for 2017-2022 data**  
   Command: Follow instructions in generated loading plan  
   Estimated time: 2-3 hours

5. **Update documentation with actual data ranges**  
   Action: Manual documentation updates  
   Estimated time: 30 minutes

## Conclusion

The investigation confirms that there is a significant discrepancy between the documented data range (2016-2025) and what's actually available in BigQuery (primarily 2023-2024). However, we've located historical data from 2016-2022 in GCS storage that can be loaded to resolve this issue. The provided tools and reports should enable a complete resolution of this data discrepancy.

## Report Files

The following detailed reports were generated during this investigation:

1. **UK_ENERGY_DATA_INVESTIGATION_REPORT.md**  
   Comprehensive findings report

2. **uk_energy_date_ranges_*.md**  
   BigQuery table date range analysis

3. **gcs_historical_data_scan_*.md**  
   GCS historical data analysis

4. **loading_plan_*.md**  
   Data loading plans
"""
    
    # Save the markdown report
    with open("UK_ENERGY_DATA_RESOLUTION_PLAN.md", "w") as f:
        f.write(md_report)
    
    print(f"Summary saved to uk_energy_data_investigation_summary.json")
    print(f"Resolution plan saved to UK_ENERGY_DATA_RESOLUTION_PLAN.md")

if __name__ == "__main__":
    generate_summary()
