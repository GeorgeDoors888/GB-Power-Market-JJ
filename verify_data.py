#!/usr/bin/env python3
"""
Query and verify downloaded Elexon data in BigQuery
Shows sample data, statistics, and data quality checks
"""

import os
from datetime import date, timedelta
from google.cloud import bigquery
from tabulate import tabulate

PROJECT_ID = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"

def format_bytes(bytes_val):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"

def get_table_summary(client):
    """Get summary of all tables in the dataset"""
    tables = list(client.list_tables(BQ_DATASET))
    
    summary = []
    total_rows = 0
    total_bytes = 0
    
    for table in tables:
        table_ref = client.get_table(table.reference)
        total_rows += table_ref.num_rows
        total_bytes += table_ref.num_bytes
        
        summary.append({
            "Table": table.table_id,
            "Rows": f"{table_ref.num_rows:,}",
            "Columns": len(table_ref.schema),
            "Size": format_bytes(table_ref.num_bytes),
            "Created": table_ref.created.strftime("%Y-%m-%d %H:%M") if table_ref.created else "N/A"
        })
    
    return summary, total_rows, total_bytes

def get_sample_data(client, table_id, limit=5):
    """Get sample rows from a table"""
    query = f"""
    SELECT *
    FROM `{PROJECT_ID}.{BQ_DATASET}.{table_id}`
    ORDER BY RAND()
    LIMIT {limit}
    """
    
    try:
        results = client.query(query).result()
        rows = [dict(row) for row in results]
        return rows
    except Exception as e:
        return f"Error: {e}"

def get_date_range(client, table_id):
    """Get date range of data in a table"""
    # Try common date column names
    date_columns = ['settlementDate', 'startTime', 'timestamp', 'date', 'datetime']
    
    for col in date_columns:
        try:
            query = f"""
            SELECT 
                MIN({col}) as min_date,
                MAX({col}) as max_date,
                COUNT(DISTINCT {col}) as unique_dates
            FROM `{PROJECT_ID}.{BQ_DATASET}.{table_id}`
            """
            result = list(client.query(query).result())[0]
            return {
                "min_date": result['min_date'],
                "max_date": result['max_date'],
                "unique_dates": result['unique_dates'],
                "date_column": col
            }
        except:
            continue
    
    return None

def check_data_quality(client, table_id):
    """Run basic data quality checks"""
    query = f"""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT *) as unique_rows
    FROM `{PROJECT_ID}.{BQ_DATASET}.{table_id}`
    """
    
    try:
        result = list(client.query(query).result())[0]
        duplicate_pct = ((result['total_rows'] - result['unique_rows']) / result['total_rows'] * 100) if result['total_rows'] > 0 else 0
        
        return {
            "total_rows": result['total_rows'],
            "unique_rows": result['unique_rows'],
            "duplicate_pct": f"{duplicate_pct:.2f}%"
        }
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 80)
    print("🔍 BigQuery Data Verification Report")
    print("=" * 80)
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {BQ_DATASET}")
    print()
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    
    # Get table summary
    print("📊 Dataset Summary")
    print("=" * 80)
    summary, total_rows, total_bytes = get_table_summary(client)
    
    print(tabulate(summary, headers="keys", tablefmt="grid"))
    print()
    print(f"📈 Total rows across all tables: {total_rows:,}")
    print(f"💾 Total storage used: {format_bytes(total_bytes)}")
    print()
    
    # Detailed analysis of top 5 tables by size
    print("=" * 80)
    print("🔬 Detailed Analysis - Top 5 Tables by Row Count")
    print("=" * 80)
    
    # Sort tables by row count
    sorted_tables = sorted(summary, key=lambda x: int(x["Rows"].replace(",", "")), reverse=True)[:5]
    
    for table_info in sorted_tables:
        table_id = table_info["Table"]
        print(f"\n📋 Table: {table_id}")
        print("-" * 80)
        
        # Date range
        date_range = get_date_range(client, table_id)
        if date_range:
            print(f"📅 Date Range:")
            print(f"   First record: {date_range['min_date']}")
            print(f"   Last record:  {date_range['max_date']}")
            print(f"   Unique dates: {date_range['unique_dates']}")
            print(f"   Date column:  {date_range['date_column']}")
        else:
            print(f"📅 Date Range: Unable to determine (no standard date column found)")
        
        # Data quality
        quality = check_data_quality(client, table_id)
        if isinstance(quality, dict):
            print(f"✅ Data Quality:")
            print(f"   Total rows:    {quality['total_rows']:,}")
            print(f"   Unique rows:   {quality['unique_rows']:,}")
            print(f"   Duplicates:    {quality['duplicate_pct']}")
        
        # Sample data
        print(f"📝 Sample Data (5 random rows):")
        samples = get_sample_data(client, table_id, limit=5)
        if isinstance(samples, list) and samples:
            # Show first sample with all fields
            print("\n   First sample record:")
            for key, value in samples[0].items():
                print(f"      {key}: {value}")
        else:
            print(f"   {samples}")
    
    # Generate SQL queries for common analyses
    print("\n" + "=" * 80)
    print("📊 Suggested Analysis Queries")
    print("=" * 80)
    
    queries = [
        {
            "name": "Daily Generation by Fuel Type",
            "sql": f"""
SELECT 
    DATE(startTime) as date,
    fuelType,
    SUM(generation) as total_generation_mw
FROM `{PROJECT_ID}.{BQ_DATASET}.generation_fuel_instant`
GROUP BY date, fuelType
ORDER BY date DESC, total_generation_mw DESC
LIMIT 100;
"""
        },
        {
            "name": "Demand vs Forecast Comparison",
            "sql": f"""
SELECT 
    d.settlementDate,
    d.settlementPeriod,
    d.initialDemandOutturn as actual_demand,
    f.nationalDemandForecast as forecast_demand,
    (d.initialDemandOutturn - f.nationalDemandForecast) as forecast_error
FROM `{PROJECT_ID}.{BQ_DATASET}.demand_outturn` d
JOIN `{PROJECT_ID}.{BQ_DATASET}.demand_forecast_national` f
ON d.settlementDate = f.settlementDate 
AND d.settlementPeriod = f.settlementPeriod
ORDER BY d.settlementDate DESC
LIMIT 100;
"""
        },
        {
            "name": "System Frequency Statistics",
            "sql": f"""
SELECT 
    DATE(startTime) as date,
    AVG(frequency) as avg_frequency,
    MIN(frequency) as min_frequency,
    MAX(frequency) as max_frequency,
    STDDEV(frequency) as stddev_frequency
FROM `{PROJECT_ID}.{BQ_DATASET}.system_frequency`
GROUP BY date
ORDER BY date DESC
LIMIT 30;
"""
        }
    ]
    
    for query_info in queries:
        print(f"\n💡 {query_info['name']}:")
        print("-" * 80)
        print(query_info['sql'])
    
    print("\n" + "=" * 80)
    print("✅ Verification Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
