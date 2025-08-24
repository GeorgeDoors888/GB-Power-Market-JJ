#!/usr/bin/env python3
from google.cloud import bigquery

def check_table_range(project_id, dataset_id, table_id):
    client = bigquery.Client(project=project_id)
    
    # Get table schema to find the date column
    table_ref = client.dataset(dataset_id).table(table_id)
    try:
        table = client.get_table(table_ref)
        
        # Find date columns
        schema = table.schema
        date_cols = [field.name for field in schema 
                    if field.field_type in ('DATE', 'DATETIME', 'TIMESTAMP')]
        
        if not date_cols:
            print(f"No date columns found in {dataset_id}.{table_id}")
            return
        
        # Try common date column names first
        priority_date_cols = [col for col in date_cols if col.lower() in 
                            ('settlement_date', 'date', 'timestamp', 'reporting_date')]
        
        date_col = priority_date_cols[0] if priority_date_cols else date_cols[0]
        
        # Run query to get date range
        query = f"""
        SELECT 
            MIN({date_col}) as min_date, 
            MAX({date_col}) as max_date,
            COUNT(*) as row_count
        FROM `{project_id}.{dataset_id}.{table_id}`
        """
        
        results = client.query(query).result()
        for row in results:
            print(f'{dataset_id}.{table_id} date range:')
            print(f'  Date column: {date_col}')
            print(f'  Min date: {row.min_date}')
            print(f'  Max date: {row.max_date}')
            print(f'  Row count: {row.row_count:,}')
            
    except Exception as e:
        print(f"Error checking {dataset_id}.{table_id}: {str(e)}")

# Check the tables we found with 2016 data
print("Checking tables with 2016 data...")
check_table_range('jibber-jabber-knowledge', 'uk_energy_data', 'elexon_fuel_generation')
check_table_range('jibber-jabber-knowledge', 'uk_energy_data_gemini_eu', 'elexon_fuel_generation')
check_table_range('jibber-jabber-knowledge', 'us_central1_gemini_models', 'elexon_fuel_generation')

# Also check other interesting tables
print("\nChecking other key tables...")
check_table_range('jibber-jabber-knowledge', 'uk_energy_data', 'elexon_frequency')
check_table_range('jibber-jabber-knowledge', 'uk_energy_data', 'elexon_system_prices')
check_table_range('jibber-jabber-knowledge', 'uk_energy_data', 'neso_gsp_demand')
