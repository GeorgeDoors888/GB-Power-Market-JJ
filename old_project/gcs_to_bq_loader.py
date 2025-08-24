#!/usr/bin/env python3
"""
GCS to BigQuery Historical Data Loader

This script assists with loading historical data from GCS to BigQuery.
It helps identify which files in the elexon-historical-data-storage bucket
should be loaded into which BigQuery tables.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from google.cloud import storage, bigquery

def print_with_timestamp(message):
    """Print message with timestamp."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] {message}")
    sys.stdout.flush()  # Ensure output is displayed immediately

def list_historical_files(bucket_name="elexon-historical-data-storage", year=None):
    """List all files in the specified GCS bucket, optionally filtered by year."""
    try:
        client = storage.Client()
        bucket = client.get_bucket(bucket_name)
        
        print_with_timestamp(f"Listing files in bucket: {bucket_name}")
        
        # Build prefix filter if year is specified
        prefix = None
        if year:
            # Try both patterns: direct year in filename and in folder structure
            prefixes = [f"{year}", f"{year}-"]
        else:
            prefixes = [""]
        
        all_files = []
        
        # List files for each prefix
        for prefix in prefixes:
            blobs = list(bucket.list_blobs(prefix=prefix, max_results=1000))
            for blob in blobs:
                file_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "content_type": blob.content_type
                }
                all_files.append(file_info)
        
        # Group files by type/category based on path structure
        file_categories = {}
        
        for file in all_files:
            # Parse path to determine category
            path_parts = file["name"].split("/")
            
            if len(path_parts) >= 2:
                category = path_parts[0]  # First folder level
                if category not in file_categories:
                    file_categories[category] = []
                file_categories[category].append(file)
            else:
                # Files at root level
                if "root" not in file_categories:
                    file_categories["root"] = []
                file_categories["root"].append(file)
        
        # Print summary
        print_with_timestamp("\nFile Categories:")
        for category, files in file_categories.items():
            print(f"  {category}: {len(files)} files")
        
        return file_categories
    
    except Exception as e:
        print_with_timestamp(f"Error: {str(e)}")
        return None

def map_gcs_to_bq(file_categories):
    """Create a mapping between GCS file categories and BigQuery tables."""
    # Define known mappings
    gcs_to_bq_mapping = {
        "demand": {
            "table": "elexon_demand_outturn",
            "dataset": "uk_energy_prod",
            "description": "Demand data including forecasts and actuals"
        },
        "frequency": {
            "table": "elexon_frequency",
            "dataset": "uk_energy_data",
            "description": "System frequency data"
        },
        "generation": {
            "table": "elexon_generation_outturn",
            "dataset": "uk_energy_prod",
            "description": "Generation data including fuel type breakdowns"
        },
        "balancing": {
            "table": "neso_balancing_services",
            "dataset": "uk_energy_prod",
            "description": "Balancing services and bid/offer data"
        },
        "interconnector": {
            "table": "neso_interconnector_flows",
            "dataset": "uk_energy_prod",
            "description": "Interconnector flow data"
        }
    }
    
    # Create mapping report
    mapping_report = []
    
    for category, files in file_categories.items():
        if category in gcs_to_bq_mapping:
            mapping = gcs_to_bq_mapping[category]
            sample_files = [f["name"] for f in files[:3]]
            
            mapping_report.append({
                "gcs_category": category,
                "file_count": len(files),
                "bq_table": mapping["table"],
                "bq_dataset": mapping["dataset"],
                "description": mapping["description"],
                "sample_files": sample_files
            })
        else:
            # For unknown categories, provide suggestions
            mapping_report.append({
                "gcs_category": category,
                "file_count": len(files),
                "bq_table": "Unknown - manual mapping needed",
                "bq_dataset": "Unknown - manual mapping needed",
                "description": "No automatic mapping available",
                "sample_files": [f["name"] for f in files[:3]]
            })
    
    return mapping_report

def generate_loading_plan(mapping_report, year=None):
    """Generate a loading plan for historical data."""
    loading_plan = {
        "loading_steps": [],
        "estimated_row_count": 0,
        "estimated_size_bytes": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    year_filter = f" WHERE EXTRACT(YEAR FROM timestamp_column) = {year}" if year else ""
    
    for mapping in mapping_report:
        if "Unknown" not in mapping["bq_table"]:
            # Create a loading step for this category
            loading_step = {
                "source_category": mapping["gcs_category"],
                "target_table": f"{mapping['bq_dataset']}.{mapping['bq_table']}",
                "file_count": mapping["file_count"],
                "sample_files": mapping["sample_files"],
                "loading_command": f"bq load --source_format=CSV {mapping['bq_dataset']}.{mapping['bq_table']} gs://elexon-historical-data-storage/{mapping['gcs_category']}/*",
                "validation_query": f"SELECT COUNT(*) as row_count, MIN(timestamp_column) as min_date, MAX(timestamp_column) as max_date FROM {mapping['bq_dataset']}.{mapping['bq_table']}{year_filter}"
            }
            
            loading_plan["loading_steps"].append(loading_step)
    
    return loading_plan

def main():
    parser = argparse.ArgumentParser(description="GCS to BigQuery Historical Data Loader")
    parser.add_argument("--year", type=str, help="Filter files by year (e.g., 2016)")
    parser.add_argument("--bucket", type=str, default="elexon-historical-data-storage", 
                        help="GCS bucket name (default: elexon-historical-data-storage)")
    parser.add_argument("--output", type=str, default="loading_plan", 
                        help="Output filename prefix (default: loading_plan)")
    
    args = parser.parse_args()
    
    # List historical files
    file_categories = list_historical_files(args.bucket, args.year)
    
    if not file_categories:
        print_with_timestamp("No files found. Exiting.")
        return
    
    # Map GCS categories to BigQuery tables
    mapping_report = map_gcs_to_bq(file_categories)
    
    # Generate loading plan
    loading_plan = generate_loading_plan(mapping_report, args.year)
    
    # Save mapping report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    year_suffix = f"_{args.year}" if args.year else ""
    
    mapping_filename = f"{args.output}_mapping{year_suffix}_{timestamp}.json"
    with open(mapping_filename, 'w') as f:
        json.dump(mapping_report, f, indent=2)
    
    # Save loading plan
    plan_filename = f"{args.output}_plan{year_suffix}_{timestamp}.json"
    with open(plan_filename, 'w') as f:
        json.dump(loading_plan, f, indent=2)
    
    # Generate Markdown report
    md_report = f"""# Historical Data Loading Plan
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{f"Year filter: {args.year}" if args.year else "All years"}

## File to Table Mapping

| GCS Category | File Count | Target BigQuery Table | Sample Files |
|--------------|------------|----------------------|--------------|
"""
    
    for mapping in mapping_report:
        sample_files_str = "<br>".join(mapping["sample_files"])
        md_report += f"| {mapping['gcs_category']} | {mapping['file_count']} | {mapping['bq_dataset']}.{mapping['bq_table']} | {sample_files_str} |\n"
    
    md_report += """
## Loading Steps

Follow these steps to load the historical data into BigQuery:

1. **Verify Table Schemas**: Ensure target tables exist and have compatible schemas
2. **Review Sample Files**: Check sample files to confirm data format matches table schema
3. **Execute Loading Commands**: Run the following loading commands

```bash
"""
    
    for step in loading_plan["loading_steps"]:
        md_report += f"# Load {step['source_category']} files into {step['target_table']}\n"
        md_report += f"{step['loading_command']}\n\n"
    
    md_report += """```

4. **Validate Loaded Data**: Run these validation queries

```sql
"""
    
    for step in loading_plan["loading_steps"]:
        md_report += f"-- Validate {step['target_table']}\n"
        md_report += f"{step['validation_query']}\n\n"
    
    md_report += """```

## Post-Loading Tasks

1. Update data documentation to reflect newly loaded historical data
2. Verify data quality using standard validation queries
3. Update dashboards and applications to use the historical data
"""
    
    md_filename = f"{args.output}_plan{year_suffix}_{timestamp}.md"
    with open(md_filename, 'w') as f:
        f.write(md_report)
    
    print_with_timestamp(f"Mapping report saved to {mapping_filename}")
    print_with_timestamp(f"Loading plan saved to {plan_filename}")
    print_with_timestamp(f"Markdown report saved to {md_filename}")

if __name__ == "__main__":
    main()
