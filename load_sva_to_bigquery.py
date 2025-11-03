#!/usr/bin/env python3
"""
Load SVA generators data to BigQuery
Uploads the 7,072 embedded generation sites
"""

from google.cloud import bigquery
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "sva_generators"

def load_sva_to_bigquery():
    """Load SVA generators to BigQuery"""
    
    input_file = "generators.json"
    
    print(f"\n⚡ Loading SVA Generators to BigQuery")
    print("="*90)
    
    # Load data
    print(f"📂 Loading {input_file}...")
    with open(input_file, 'r') as f:
        generators = json.load(f)
    
    print(f"✅ Loaded {len(generators)} generators")
    
    # Connect to BigQuery
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Define schema
    schema = [
        bigquery.SchemaField("plant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("dno", "STRING"),
        bigquery.SchemaField("gsp", "STRING"),
        bigquery.SchemaField("lat", "FLOAT64"),
        bigquery.SchemaField("lng", "FLOAT64"),
        bigquery.SchemaField("capacity_mw", "FLOAT64"),
        bigquery.SchemaField("fuel_type", "STRING"),
        bigquery.SchemaField("technology", "STRING"),
        bigquery.SchemaField("commissioned_date", "STRING"),
        bigquery.SchemaField("connection_type", "STRING"),
        bigquery.SchemaField("export_capacity_mw", "FLOAT64"),
    ]
    
    # Delete existing table if it exists
    try:
        client.delete_table(table_ref)
        print(f"🗑️  Deleted existing table")
    except:
        pass
    
    # Create fresh table
    print(f"\n📊 Creating table: {table_ref}")
    
    table = bigquery.Table(table_ref, schema=schema)
    table = client.create_table(table)
    print(f"✅ Table created")
    
    # Prepare rows
    print(f"\n⚡ Preparing data for BigQuery...")
    rows_to_insert = []
    
    for gen in generators:
        row = {
            'plant_id': gen.get('Plant ID', gen.get('id', 'UNKNOWN')),
            'name': gen.get('Plant Name', gen.get('name', '')),
            'dno': gen.get('DNO', ''),
            'gsp': gen.get('GSP', ''),
            'lat': float(gen['Latitude']) if gen.get('Latitude') else None,
            'lng': float(gen['Longitude']) if gen.get('Longitude') else None,
            'capacity_mw': float(gen['Installed Capacity (MW)']) if gen.get('Installed Capacity (MW)') else None,
            'fuel_type': gen.get('Fuel Type', gen.get('fuel_type', '')),
            'technology': gen.get('Technology', ''),
            'commissioned_date': gen.get('Commissioned', ''),
            'connection_type': gen.get('Connection Type', ''),
            'export_capacity_mw': float(gen['Export Capacity (MW)']) if gen.get('Export Capacity (MW)') else None,
        }
        rows_to_insert.append(row)
    
    print(f"✅ Prepared {len(rows_to_insert)} rows")
    
    # Insert in batches
    print(f"\n📤 Inserting to BigQuery...")
    batch_size = 500
    total_inserted = 0
    
    for i in range(0, len(rows_to_insert), batch_size):
        batch = rows_to_insert[i:i+batch_size]
        
        errors = client.insert_rows_json(table_ref, batch)
        
        if errors:
            print(f"❌ Errors in batch {i//batch_size + 1}: {errors[:3]}...")  # Show first 3 errors
        else:
            total_inserted += len(batch)
            print(f"   ✅ Batch {i//batch_size + 1}/{(len(rows_to_insert)-1)//batch_size + 1}: {len(batch)} rows inserted")
    
    print(f"\n✅ Successfully loaded {total_inserted} SVA generators to BigQuery!")
    
    # Verify
    print(f"\n📊 Verifying data...")
    query = f"""
    SELECT 
        COUNT(*) as total_generators,
        COUNT(DISTINCT dno) as unique_dnos,
        COUNT(DISTINCT fuel_type) as unique_fuel_types,
        ROUND(SUM(capacity_mw), 2) as total_capacity_mw,
        COUNT(CASE WHEN lat IS NOT NULL THEN 1 END) as with_coords
    FROM `{table_ref}`
    """
    
    result = client.query(query).result()
    for row in result:
        print(f"\n✅ Verification:")
        print(f"   Total generators: {row.total_generators:,}")
        print(f"   With coordinates: {row.with_coords:,}")
        print(f"   Unique DNOs: {row.unique_dnos}")
        print(f"   Unique fuel types: {row.unique_fuel_types}")
        print(f"   Total capacity: {row.total_capacity_mw:,.2f} MW")
    
    # Top fuel types
    print(f"\n📊 Top Fuel Types:")
    query = f"""
    SELECT 
        fuel_type,
        COUNT(*) as count,
        ROUND(SUM(capacity_mw), 2) as total_mw
    FROM `{table_ref}`
    WHERE fuel_type IS NOT NULL AND fuel_type != ''
    GROUP BY fuel_type
    ORDER BY count DESC
    LIMIT 10
    """
    
    result = client.query(query).result()
    for row in result:
        print(f"   {row.fuel_type}: {row.count:,} generators ({row.total_mw:,.2f} MW)")
    
    print(f"\n🎉 BigQuery upload complete!")
    print(f"   Table: {table_ref}")
    print(f"   Rows: {total_inserted:,}")
    
    return total_inserted

if __name__ == "__main__":
    try:
        load_sva_to_bigquery()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
