#!/usr/bin/env python3
"""
Check date ranges in BigQuery tables from 2016 to present.
This script analyzes UK energy datasets to find tables with data from 2016 to the present day.
"""

import os
import sys
import time
import json
from datetime import datetime
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

# Current date for comparison
TODAY = datetime.now().strftime('%Y-%m-%d')
TARGET_START_DATE = '2016-01-01'

def print_with_timestamp(message):
    """Print message with timestamp."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] {message}")
    sys.stdout.flush()  # Ensure output is displayed immediately

def get_date_range(client, dataset_id, table_id):
    """
    Get the date range for a specific table using a more efficient query.
    Only examine tables with timestamp/date columns.
    """
    try:
        # First, get the table schema to identify date/timestamp columns
        table_ref = f"{client.project}.{dataset_id}.{table_id}"
        table = client.get_table(table_ref)
        
        # Find timestamp or date columns
        date_columns = []
        for field in table.schema:
            if field.field_type in ('TIMESTAMP', 'DATE', 'DATETIME'):
                date_columns.append(field.name)
        
        if not date_columns:
            return None, None, "No date columns found"
        
        # Check just the first date column for efficiency
        date_col = date_columns[0]
        
        query = f"""
        SELECT 
            MIN({date_col}) as min_date,
            MAX({date_col}) as max_date,
            COUNT(*) as row_count
        FROM `{table_ref}`
        """
        
        # Fixed: Use the correct timeout parameters
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=10_000_000_000  # 10 GB
        )
        query_job = client.query(query, job_config=job_config)
        
        # Wait for the results with a timeout
        start_time = time.time()
        results = None
        
        try:
            # Set a 60-second timeout for the query to complete
            while time.time() - start_time < 60:
                if query_job.done():
                    results = list(query_job.result())
                    break
                time.sleep(1)
            
            if not results:
                return None, None, "Query timed out"
        except Exception as query_error:
            return None, None, f"Query error: {str(query_error)}"
        
        if not results or len(results) == 0:
            return None, None, "Empty table"
        
        row = results[0]
        min_date = row.min_date
        max_date = row.max_date
        row_count = row.row_count
        
        # Format dates if they're datetime objects
        min_date_str = min_date.strftime('%Y-%m-%d') if min_date and hasattr(min_date, 'strftime') else str(min_date)
        max_date_str = max_date.strftime('%Y-%m-%d') if max_date and hasattr(max_date, 'strftime') else str(max_date)
        
        return min_date_str, max_date_str, row_count
    except Exception as e:
        return None, None, f"Error: {str(e)}"

def check_tables_for_date_range(project_id='jibber-jabber-knowledge'):
    """Check BigQuery tables for date ranges from 2016 to present."""
    print_with_timestamp(f"Starting date range check from {TARGET_START_DATE} to {TODAY}")
    
    results = {
        "tables_with_2016_data": [],
        "tables_with_partial_range": [],
        "tables_with_no_2016_data": [],
        "tables_with_errors": [],
        "summary": {}
    }
    
    try:
        client = bigquery.Client(project=project_id)
        datasets = list(client.list_datasets())
        
        for dataset in datasets:
            dataset_id = dataset.dataset_id
            
            # Skip non-UK energy datasets for efficiency
            if not any(x in dataset_id.lower() for x in ['uk_energy', 'elexon', 'neso']):
                continue
                
            print_with_timestamp(f"Scanning dataset: {dataset_id}")
            tables = list(client.list_tables(dataset_id))
            
            # Process NESO and Elexon tables first
            prioritized_tables = []
            other_tables = []
            
            for table in tables:
                table_id = table.table_id
                if any(x in table_id.lower() for x in ['neso', 'elexon']):
                    prioritized_tables.append(table)
                else:
                    other_tables.append(table)
            
            # Process prioritized tables first, then others
            for table in prioritized_tables + other_tables:
                table_id = table.table_id
                print_with_timestamp(f"  Checking table: {dataset_id}.{table_id}")
                
                min_date, max_date, status = get_date_range(client, dataset_id, table_id)
                
                result = {
                    "dataset": dataset_id,
                    "table": table_id,
                    "min_date": min_date,
                    "max_date": max_date,
                    "status": status if isinstance(status, str) else f"{status} rows"
                }
                
                if min_date and min_date.startswith('2016'):
                    results["tables_with_2016_data"].append(result)
                    print_with_timestamp(f"    ✅ HAS 2016 DATA: {min_date} to {max_date}")
                elif min_date:
                    # Check if it covers a partial range starting after 2016
                    if min_date > TARGET_START_DATE:
                        results["tables_with_partial_range"].append(result)
                        print_with_timestamp(f"    ⚠️ PARTIAL RANGE: {min_date} to {max_date}")
                    else:
                        results["tables_with_no_2016_data"].append(result)
                        print_with_timestamp(f"    ❌ NO 2016 DATA: {min_date} to {max_date}")
                else:
                    results["tables_with_errors"].append(result)
                    print_with_timestamp(f"    ❗ ERROR: {status}")
        
        # Generate summary
        results["summary"] = {
            "tables_with_2016_data": len(results["tables_with_2016_data"]),
            "tables_with_partial_range": len(results["tables_with_partial_range"]),
            "tables_with_no_2016_data": len(results["tables_with_no_2016_data"]),
            "tables_with_errors": len(results["tables_with_errors"]),
            "scan_date": TODAY
        }
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"uk_energy_date_ranges_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print_with_timestamp(f"Results saved to {filename}")
        
        # Print summary
        print_with_timestamp("\nSUMMARY:")
        print(f"Tables with 2016 data: {results['summary']['tables_with_2016_data']}")
        print(f"Tables with partial range (after 2016): {results['summary']['tables_with_partial_range']}")
        print(f"Tables with no 2016 data: {results['summary']['tables_with_no_2016_data']}")
        print(f"Tables with errors: {results['summary']['tables_with_errors']}")
        
        # Generate a simple markdown report
        md_report = f"""# UK Energy Data Date Range Report
Generated: {TODAY}

## Summary
- **Tables with 2016 data:** {results['summary']['tables_with_2016_data']}
- **Tables with partial range (after 2016):** {results['summary']['tables_with_partial_range']}
- **Tables with no 2016 data:** {results['summary']['tables_with_no_2016_data']}
- **Tables with errors:** {results['summary']['tables_with_errors']}

## Tables with 2016 Data
| Dataset | Table | Date Range | Row Count |
|---------|-------|------------|-----------|
"""
        for table in results["tables_with_2016_data"]:
            md_report += f"| {table['dataset']} | {table['table']} | {table['min_date']} to {table['max_date']} | {table['status']} |\n"
        
        md_report += "\n## Tables with Partial Range (after 2016)\n"
        md_report += "| Dataset | Table | Date Range | Row Count |\n"
        md_report += "|---------|-------|------------|----------|\n"
        for table in results["tables_with_partial_range"]:
            md_report += f"| {table['dataset']} | {table['table']} | {table['min_date']} to {table['max_date']} | {table['status']} |\n"
        
        md_filename = f"uk_energy_date_ranges_{timestamp}.md"
        with open(md_filename, 'w') as f:
            f.write(md_report)
        
        print_with_timestamp(f"Markdown report saved to {md_filename}")
        
    except Exception as e:
        print_with_timestamp(f"Error: {str(e)}")

if __name__ == "__main__":
    check_tables_for_date_range()
