#!/usr/bin/env python3
"""
Quick scan for NESO and Elexon data in BigQuery

This script quickly scans for NESO and Elexon data in the specified BigQuery project
and outputs a detailed report on what it finds.
"""

import json
import datetime
import argparse
from google.cloud import bigquery

def main():
    parser = argparse.ArgumentParser(description="Quick scan for NESO and Elexon data in BigQuery")
    parser.add_argument("--project", default="jibber-jabber-knowledge", help="Google Cloud project ID")
    args = parser.parse_args()
    
    print(f"Scanning project {args.project} for NESO and Elexon data in BigQuery...")
    
    # Connect to BigQuery
    client = bigquery.Client(project=args.project)
    
    # Get all datasets
    print("Listing all datasets...")
    datasets = list(client.list_datasets())
    
    if not datasets:
        print("No datasets found in the project.")
        return
    
    print(f"Found {len(datasets)} datasets.")
    
    report = {
        "project": args.project,
        "scan_time": datetime.datetime.now().isoformat(),
        "datasets": []
    }
    
    # Check each dataset
    for dataset_ref in datasets:
        dataset_id = dataset_ref.dataset_id
        print(f"\nExamining dataset: {dataset_id}")
        
        dataset_info = {
            "dataset_id": dataset_id,
            "tables": []
        }
        
        # Get all tables in the dataset
        tables = list(client.list_tables(dataset_ref))
        
        if not tables:
            print(f"  No tables found in dataset {dataset_id}")
            continue
        
        print(f"  Found {len(tables)} tables in dataset {dataset_id}")
        
        # Check each table
        for table_ref in tables:
            table_id = table_ref.table_id
            
            try:
                # Get table details
                table = client.get_table(table_ref)
                
                # Get schema information
                schema_info = []
                for field in table.schema:
                    schema_info.append({
                        "name": field.name,
                        "type": field.field_type,
                        "mode": field.mode
                    })
                
                # Get table statistics
                table_info = {
                    "table_id": table_id,
                    "full_id": f"{args.project}.{dataset_id}.{table_id}",
                    "row_count": table.num_rows,
                    "size_bytes": table.num_bytes,
                    "created": table.created.isoformat() if table.created else None,
                    "modified": table.modified.isoformat() if table.modified else None,
                    "schema": schema_info
                }
                
                # Check for NESO or Elexon prefixes in table name
                if table_id.lower().startswith("neso_") or "neso" in table_id.lower():
                    table_info["data_source"] = "NESO"
                    print(f"  ✓ NESO data found in table: {table_id}")
                elif table_id.lower().startswith("elexon_") or "elexon" in table_id.lower():
                    table_info["data_source"] = "Elexon"
                    print(f"  ✓ Elexon data found in table: {table_id}")
                else:
                    # Check schema for indicators
                    schema_text = ' '.join([field.name.lower() for field in table.schema])
                    if "neso" in schema_text:
                        table_info["data_source"] = "NESO (detected in schema)"
                        print(f"  ✓ NESO data detected in schema of table: {table_id}")
                    elif "elexon" in schema_text or "bmrs" in schema_text:
                        table_info["data_source"] = "Elexon (detected in schema)"
                        print(f"  ✓ Elexon data detected in schema of table: {table_id}")
                    else:
                        table_info["data_source"] = "Unknown"
                
                # Check row count
                if table.num_rows > 0:
                    print(f"    - Contains {table.num_rows:,} rows")
                    
                    # Query sample data to determine date range
                    try:
                        # Look for date columns
                        date_cols = [field.name for field in table.schema 
                                     if field.field_type in ('DATE', 'DATETIME', 'TIMESTAMP')]
                        
                        if date_cols:
                            # Try common date column names first
                            priority_date_cols = [col for col in date_cols if col.lower() in 
                                                ('settlement_date', 'date', 'timestamp', 'reporting_date')]
                            
                            date_col = priority_date_cols[0] if priority_date_cols else date_cols[0]
                            
                            # Query for min and max dates
                            query = f"""
                            SELECT 
                                MIN({date_col}) as min_date, 
                                MAX({date_col}) as max_date
                            FROM `{args.project}.{dataset_id}.{table_id}`
                            """
                            
                            query_job = client.query(query)
                            results = next(query_job.result())
                            
                            min_date = results.min_date
                            max_date = results.max_date
                            
                            if min_date and max_date:
                                print(f"    - Date range: {min_date} to {max_date}")
                                table_info["date_range"] = {
                                    "min_date": min_date.isoformat() if hasattr(min_date, 'isoformat') else str(min_date),
                                    "max_date": max_date.isoformat() if hasattr(max_date, 'isoformat') else str(max_date),
                                    "date_column": date_col
                                }
                    except Exception as e:
                        print(f"    - Could not determine date range: {str(e)}")
                
                dataset_info["tables"].append(table_info)
                
            except Exception as e:
                print(f"  Error getting information for table {table_id}: {str(e)}")
                dataset_info["tables"].append({
                    "table_id": table_id,
                    "error": str(e)
                })
        
        report["datasets"].append(dataset_info)
    
    # Calculate summary statistics
    neso_tables = sum(1 for dataset in report["datasets"] 
                     for table in dataset["tables"] 
                     if table.get("data_source", "").startswith("NESO"))
    
    elexon_tables = sum(1 for dataset in report["datasets"] 
                       for table in dataset["tables"] 
                       if table.get("data_source", "").startswith("Elexon"))
    
    total_tables = sum(len(dataset["tables"]) for dataset in report["datasets"])
    
    report["summary"] = {
        "total_datasets": len(report["datasets"]),
        "total_tables": total_tables,
        "neso_tables": neso_tables,
        "elexon_tables": elexon_tables,
        "other_tables": total_tables - neso_tables - elexon_tables
    }
    
    # Write report to JSON file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"bigquery_neso_elexon_report_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nScan complete! Report saved to {output_file}")
    print("\nSummary:")
    print(f"  Total datasets: {report['summary']['total_datasets']}")
    print(f"  Total tables: {report['summary']['total_tables']}")
    print(f"  NESO tables: {report['summary']['neso_tables']}")
    print(f"  Elexon tables: {report['summary']['elexon_tables']}")
    print(f"  Other tables: {report['summary']['other_tables']}")
    
    # Also generate a simplified text report
    text_report = f"bigquery_neso_elexon_report_{timestamp}.txt"
    with open(text_report, 'w') as f:
        f.write(f"NESO and Elexon Data in BigQuery - Project: {args.project}\n")
        f.write(f"Scan time: {report['scan_time']}\n\n")
        
        f.write("SUMMARY\n")
        f.write("=======\n")
        f.write(f"Total datasets: {report['summary']['total_datasets']}\n")
        f.write(f"Total tables: {report['summary']['total_tables']}\n")
        f.write(f"NESO tables: {report['summary']['neso_tables']}\n")
        f.write(f"Elexon tables: {report['summary']['elexon_tables']}\n")
        f.write(f"Other tables: {report['summary']['other_tables']}\n\n")
        
        f.write("DETAILED FINDINGS\n")
        f.write("=================\n\n")
        
        for dataset in report["datasets"]:
            dataset_id = dataset["dataset_id"]
            f.write(f"Dataset: {dataset_id}\n")
            f.write(f"{'-' * (len(dataset_id) + 9)}\n")
            
            neso_tables = [t for t in dataset["tables"] if t.get("data_source", "").startswith("NESO")]
            elexon_tables = [t for t in dataset["tables"] if t.get("data_source", "").startswith("Elexon")]
            
            if neso_tables:
                f.write("\nNESO Tables:\n")
                for table in neso_tables:
                    f.write(f"  • {table['table_id']} ({table.get('row_count', 'unknown')} rows)\n")
                    if "date_range" in table:
                        f.write(f"    - Date range: {table['date_range']['min_date']} to {table['date_range']['max_date']}\n")
            
            if elexon_tables:
                f.write("\nElexon Tables:\n")
                for table in elexon_tables:
                    f.write(f"  • {table['table_id']} ({table.get('row_count', 'unknown')} rows)\n")
                    if "date_range" in table:
                        f.write(f"    - Date range: {table['date_range']['min_date']} to {table['date_range']['max_date']}\n")
            
            other_tables = [t for t in dataset["tables"] 
                          if not t.get("data_source", "").startswith("NESO") 
                          and not t.get("data_source", "").startswith("Elexon")]
            
            if other_tables:
                f.write(f"\nOther Tables: {len(other_tables)} table(s)\n")
            
            f.write("\n\n")
    
    print(f"Text report saved to {text_report}")

if __name__ == "__main__":
    main()
