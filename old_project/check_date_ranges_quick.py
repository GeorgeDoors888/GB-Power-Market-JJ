#!/usr/bin/env python3
"""
Check date ranges of key tables in BigQuery.
"""

from google.cloud import bigquery

def check_date_range(client, dataset_id, table_id):
    """Check the date range of a specific table."""
    try:
        # Get table schema
        table_ref = client.dataset(dataset_id).table(table_id)
        table = client.get_table(table_ref)
        
        # Try to find date column
        date_cols = [field.name for field in table.schema 
                     if field.field_type in ('DATE', 'DATETIME', 'TIMESTAMP')]
        
        if not date_cols:
            print(f"  {dataset_id}.{table_id}: No date columns found")
            return
        
        # Try common date column names first
        priority_cols = ['settlement_date', 'settlementDate', 'date', 'time', 'timestamp', 'reporting_date', 'measurementTime']
        date_col = next((col for col in date_cols if col.lower() in [p.lower() for p in priority_cols]), date_cols[0])
        
        # Get row count
        count_query = f"""
        SELECT COUNT(*) as count
        FROM `jibber-jabber-knowledge.{dataset_id}.{table_id}`
        """
        count_result = client.query(count_query).result()
        count = next(iter(count_result)).count
        
        if count == 0:
            print(f"  {dataset_id}.{table_id}: Empty table (0 rows)")
            return
        
        # Query date range
        query = f"""
        SELECT 
            MIN({date_col}) as min_date, 
            MAX({date_col}) as max_date,
            COUNT(*) as row_count
        FROM `jibber-jabber-knowledge.{dataset_id}.{table_id}`
        """
        
        result = client.query(query).result()
        row = next(iter(result))
        
        print(f"  {dataset_id}.{table_id}: {row.min_date} to {row.max_date} ({row.row_count:,} rows) [column: {date_col}]")
        
    except Exception as e:
        print(f"  {dataset_id}.{table_id}: Error - {str(e)}")

def main():
    print("Date Ranges for NESO and Elexon Data")
    print("===================================")
    
    client = bigquery.Client(project='jibber-jabber-knowledge')
    
    # Check production dataset
    print("\nProduction dataset (uk_energy_prod):")
    tables = [
        "neso_demand_forecasts",
        "neso_wind_forecasts",
        "neso_balancing_services",
        "neso_carbon_intensity",
        "neso_interconnector_flows",
        "elexon_system_warnings",
        "elexon_demand_outturn",
        "elexon_generation_outturn"
    ]
    
    for table in tables:
        check_date_range(client, "uk_energy_prod", table)
    
    # Check uk_energy_data dataset (contains 2016 data)
    print("\nData dataset (uk_energy_data):")
    tables = [
        "elexon_fuel_generation",
        "elexon_frequency",
        "elexon_system_prices",
        "elexon_boa_acceptances",
        "neso_gsp_demand"
    ]
    
    for table in tables:
        check_date_range(client, "uk_energy_data", table)
    
    # Check other datasets with 2016 data
    print("\nOther datasets with 2016 data:")
    check_date_range(client, "uk_energy_data_gemini_eu", "elexon_fuel_generation")
    check_date_range(client, "us_central1_gemini_models", "elexon_fuel_generation")
    
    # Check uk_energy dataset
    print("\nUK Energy dataset (uk_energy):")
    tables = [
        "elexon_demand_outturn_2023",
        "elexon_generation_outturn_2023"
    ]
    
    for table in tables:
        check_date_range(client, "uk_energy", table)

if __name__ == "__main__":
    main()
