"""
Simple script to get advanced statistics from BigQuery for the UK Energy dataset
"""
from google.cloud import bigquery
import pandas as pd
import os
from datetime import datetime, timedelta

# Set proper project ID and dataset information
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_SOURCE = "uk_energy_prod"  # Based on the earlier BigQuery check
DATE_END = "2024-12-31"  # Based on the actual data ranges we found
DATE_START = "2024-12-01"  # Looking at the last month of data

def get_dataset_stats():
    """Get basic statistics about the BigQuery dataset."""
    print(f"Connecting to BigQuery project: {PROJECT_ID}")
    client = bigquery.Client(project=PROJECT_ID)
    
    print(f"\nRetrieving tables in dataset: {DATASET_SOURCE}")
    tables = client.list_tables(f"{PROJECT_ID}.{DATASET_SOURCE}")
    
    stats = []
    for table in tables:
        table_id = table.table_id
        table_ref = client.get_table(f"{PROJECT_ID}.{DATASET_SOURCE}.{table_id}")
        
        # Get row count and size
        row_count = table_ref.num_rows
        table_size_mb = table_ref.num_bytes / (1024 * 1024)
        
        # Get schema information
        field_count = len(table_ref.schema)
        
        # Get creation time
        created = table_ref.created.strftime("%Y-%m-%d")
        
        # Get last modified time
        modified = table_ref.modified.strftime("%Y-%m-%d")
        
        stats.append({
            "table_name": table_id,
            "row_count": row_count,
            "size_mb": round(table_size_mb, 2),
            "field_count": field_count,
            "created": created,
            "last_modified": modified
        })
    
    # Convert to DataFrame for better display
    stats_df = pd.DataFrame(stats)
    
    # Sort by row count (descending)
    stats_df = stats_df.sort_values("row_count", ascending=False)
    
    return stats_df

def get_date_range_stats():
    """Get statistics for the data within the specified date range."""
    print(f"\nAnalyzing data from {DATE_START} to {DATE_END}")
    client = bigquery.Client(project=PROJECT_ID)
    
    # Manually specify the tables we know have settlement_date
    known_tables = [
        "neso_interconnector_flows",
        "neso_wind_forecasts",
        "neso_carbon_intensity",
        "neso_balancing_services",
        "neso_demand_forecasts",
        "elexon_system_warnings",
        "elexon_demand_outturn",
        "elexon_generation_outturn"
    ]
    
    date_stats = []
    for table_name in known_tables:
        # First check if the table has a settlement_date column
        try:
            schema = client.get_table(f"{PROJECT_ID}.{DATASET_SOURCE}.{table_name}").schema
            has_settlement_date = any(field.name == 'settlement_date' for field in schema)
            
            if has_settlement_date:
                query = f"""
                SELECT 
                  '{table_name}' as table_name,
                  COUNT(*) as row_count,
                  MIN(settlement_date) as min_date,
                  MAX(settlement_date) as max_date
                FROM `{PROJECT_ID}.{DATASET_SOURCE}.{table_name}`
                WHERE settlement_date BETWEEN '{DATE_START}' AND '{DATE_END}'
                """
                
                results = client.query(query).result()
                for row in results:
                    if row.row_count > 0:
                        date_stats.append({
                            "table_name": row.table_name,
                            "rows_in_period": row.row_count,
                            "min_date": row.min_date.strftime("%Y-%m-%d") if row.min_date else "N/A",
                            "max_date": row.max_date.strftime("%Y-%m-%d") if row.max_date else "N/A"
                        })
            else:
                # Check if there's a different date column
                timestamp_columns = [field.name for field in schema 
                                    if field.field_type in ('DATE', 'TIMESTAMP', 'DATETIME')]
                
                if timestamp_columns:
                    date_col = timestamp_columns[0]
                    date_cast = f"DATE({date_col})" if 'DATE' not in date_col.upper() else date_col
                    query = f"""
                    SELECT 
                      '{table_name}' as table_name,
                      COUNT(*) as row_count,
                      MIN({date_cast}) as min_date,
                      MAX({date_cast}) as max_date
                    FROM `{PROJECT_ID}.{DATASET_SOURCE}.{table_name}`
                    WHERE {date_cast} BETWEEN '{DATE_START}' AND '{DATE_END}'
                    """
                    
                    results = client.query(query).result()
                    for row in results:
                        if row.row_count > 0:
                            date_stats.append({
                                "table_name": row.table_name,
                                "rows_in_period": row.row_count,
                                "date_column": date_col,
                                "min_date": row.min_date.strftime("%Y-%m-%d") if row.min_date else "N/A",
                                "max_date": row.max_date.strftime("%Y-%m-%d") if row.max_date else "N/A"
                            })
                else:
                    print(f"No date columns found in {table_name}")
                
        except Exception as e:
            print(f"Error processing {table_name}: {e}")
    
    # Convert to DataFrame
    if date_stats:
        date_stats_df = pd.DataFrame(date_stats)
        date_stats_df = date_stats_df.sort_values("rows_in_period", ascending=False)
        return date_stats_df
    else:
        return "No tables with date data found in the specified period"

def check_actual_date_ranges():
    """Check the actual date ranges in all tables."""
    print("\nChecking actual date ranges in tables:")
    client = bigquery.Client(project=PROJECT_ID)
    
    # Manually specify the tables we know have settlement_date
    known_tables = [
        "neso_interconnector_flows",
        "neso_wind_forecasts",
        "neso_carbon_intensity",
        "neso_balancing_services",
        "neso_demand_forecasts",
        "elexon_system_warnings",
        "elexon_demand_outturn",
        "elexon_generation_outturn"
    ]
    
    date_ranges = []
    for table_name in known_tables:
        try:
            schema = client.get_table(f"{PROJECT_ID}.{DATASET_SOURCE}.{table_name}").schema
            date_columns = [field.name for field in schema 
                           if field.field_type in ('DATE', 'TIMESTAMP', 'DATETIME')]
            
            if not date_columns:
                print(f"  - {table_name}: No date columns found")
                continue
                
            date_col = next((col for col in date_columns if col == 'settlement_date'), date_columns[0])
            date_cast = f"DATE({date_col})" if 'DATE' not in date_col.upper() else date_col
            
            query = f"""
            SELECT 
              '{table_name}' as table_name,
              '{date_col}' as date_column,
              MIN({date_cast}) as min_date,
              MAX({date_cast}) as max_date,
              COUNT(*) as row_count
            FROM `{PROJECT_ID}.{DATASET_SOURCE}.{table_name}`
            """
            
            results = client.query(query).result()
            for row in results:
                date_ranges.append({
                    "table_name": row.table_name,
                    "date_column": row.date_column,
                    "min_date": row.min_date.strftime("%Y-%m-%d") if row.min_date else "N/A",
                    "max_date": row.max_date.strftime("%Y-%m-%d") if row.max_date else "N/A",
                    "row_count": row.row_count
                })
        except Exception as e:
            print(f"  - Error processing {table_name}: {e}")
    
    if date_ranges:
        date_ranges_df = pd.DataFrame(date_ranges)
        return date_ranges_df
    else:
        return "No date data found in any tables"

if __name__ == "__main__":
    print("==== UK Energy BigQuery Dataset Statistics ====")
    
    # Get overall dataset statistics
    stats_df = get_dataset_stats()
    print("\nDataset Table Statistics:")
    print(stats_df.to_string(index=False))
    
    # Check actual date ranges
    date_ranges = check_actual_date_ranges()
    if isinstance(date_ranges, pd.DataFrame):
        print("\nActual Date Ranges in Tables:")
        print(date_ranges.to_string(index=False))
    else:
        print(f"\n{date_ranges}")
    
    # Get date range statistics
    date_stats = get_date_range_stats()
    print(f"\nData Statistics for {DATE_START} to {DATE_END}:")
    if isinstance(date_stats, pd.DataFrame):
        print(date_stats.to_string(index=False))
    else:
        print(date_stats)
    
    print("\nAnalysis complete!")
