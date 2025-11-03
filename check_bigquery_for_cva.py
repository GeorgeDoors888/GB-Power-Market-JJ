#!/usr/bin/env python3
"""
Check what Elexon data we have in BigQuery and look for CVA sites
"""

from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"

def list_datasets_and_tables():
    """List all datasets and tables to find Elexon data"""
    
    client = bigquery.Client(project=PROJECT_ID)
    
    print("🔍 Searching for Elexon/CVA data in BigQuery...\n")
    print("="*90)
    
    # List all datasets
    datasets = list(client.list_datasets())
    
    if not datasets:
        print("No datasets found in project.")
        return
    
    print(f"Found {len(datasets)} dataset(s):\n")
    
    for dataset in datasets:
        dataset_id = dataset.dataset_id
        print(f"\n📁 Dataset: {dataset_id}")
        print("-"*90)
        
        # List tables in dataset
        tables = list(client.list_tables(f"{PROJECT_ID}.{dataset_id}"))
        
        if not tables:
            print("   (No tables)")
            continue
        
        for table in tables:
            table_ref = f"{PROJECT_ID}.{dataset_id}.{table.table_id}"
            
            # Get table metadata
            table_obj = client.get_table(table_ref)
            
            print(f"\n   📊 Table: {table.table_id}")
            print(f"      Rows: {table_obj.num_rows:,}")
            print(f"      Size: {table_obj.num_bytes / 1024 / 1024:.2f} MB")
            print(f"      Created: {table_obj.created}")
            
            # Show schema (first 10 columns)
            print(f"      Columns ({len(table_obj.schema)}):")
            for i, field in enumerate(table_obj.schema[:10], 1):
                print(f"         {i}. {field.name} ({field.field_type})")
            if len(table_obj.schema) > 10:
                print(f"         ... and {len(table_obj.schema) - 10} more columns")
            
            # If table name suggests it might have generator/BMU data, show sample
            if any(keyword in table.table_id.lower() for keyword in 
                   ['bmu', 'bmunit', 'generator', 'plant', 'station', 'power', 'unit']):
                print(f"\n      🔍 This might contain CVA data! Checking sample...")
                
                query = f"""
                SELECT *
                FROM `{table_ref}`
                LIMIT 5
                """
                
                try:
                    results = client.query(query).result()
                    print(f"      Sample rows:")
                    for row in results:
                        print(f"         {dict(row)}")
                except Exception as e:
                    print(f"      Error querying: {e}")
    
    print("\n" + "="*90)
    print("\n💡 Looking for tables with keywords: BMU, BMUNIT, Generator, Plant, Station")

if __name__ == '__main__':
    list_datasets_and_tables()
