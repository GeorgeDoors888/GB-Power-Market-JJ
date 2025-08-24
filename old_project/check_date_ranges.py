#!/usr/bin/env python3
from google.cloud import bigquery
import pandas as pd

def check_date_ranges():
    """Check the actual date ranges in all tables."""
    client = bigquery.Client(project='jibber-jabber-knowledge')
    
    tables = client.list_tables('uk_energy_prod')
    table_list = [table.table_id for table in tables]
    
    print("Checking date ranges in BigQuery tables:")
    print("=======================================")
    
    for table_id in table_list:
        try:
            # Use a more general approach to find date columns
            schema = client.get_table(f"uk_energy_prod.{table_id}").schema
            date_cols = [field.name for field in schema if field.field_type in ('DATE', 'DATETIME', 'TIMESTAMP')]
            
            if not date_cols:
                print(f"- {table_id}: No date columns found")
                continue
            
            # Try common date column names first
            priority_date_cols = [col for col in date_cols if col.lower() in 
                                ('settlement_date', 'date', 'timestamp', 'reporting_date')]
            
            date_col = priority_date_cols[0] if priority_date_cols else date_cols[0]
            
            query = f"""
            SELECT 
                MIN({date_col}) as min_date, 
                MAX({date_col}) as max_date,
                COUNT(*) as row_count
            FROM `jibber-jabber-knowledge.uk_energy_prod.{table_id}`
            """
            
            results = client.query(query).to_dataframe()
            min_date = results.iloc[0]['min_date']
            max_date = results.iloc[0]['max_date']
            row_count = results.iloc[0]['row_count']
            
            print(f"- {table_id}: {min_date} to {max_date} ({row_count:,} rows)")
            
        except Exception as e:
            print(f"- {table_id}: Error - {str(e)}")
    
    print("\nDone!")

if __name__ == "__main__":
    check_date_ranges()
