#!/usr/bin/env python3
"""
Load CVA plants data to BigQuery (FIXED VERSION)
Uploads CVA plant data without GEOGRAPHY field issues
"""

from google.cloud import bigquery
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "cva_plants"

def load_to_bigquery():
    """Load CVA plants to BigQuery"""
    
    input_file = "cva_plants_map.json"
    
    print(f"\n🔋 Loading CVA Plants to BigQuery (Fixed Version)")
    print("="*90)
    
    # Load data
    print(f"📂 Loading {input_file}...")
    with open(input_file, 'r') as f:
        plants = json.load(f)
    
    print(f"✅ Loaded {len(plants)} plants with coordinates")
    
    # Connect to BigQuery
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Define schema WITHOUT GEOGRAPHY field (causes issues with JSON insert)
    schema = [
        bigquery.SchemaField("plant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("lat", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("lng", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("url", "STRING"),
        bigquery.SchemaField("fuel_type", "STRING"),
        bigquery.SchemaField("status", "STRING"),
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
    
    # Prepare rows (simplified, no GEOGRAPHY field)
    print(f"\n⚡ Preparing data for BigQuery...")
    rows_to_insert = []
    
    for plant in plants:
        row = {
            'plant_id': plant.get('id', plant.get('plant_id', 'UNKNOWN')),
            'name': plant.get('name', 'Unknown'),
            'lat': plant['lat'],
            'lng': plant['lng'],
            'url': plant.get('url', ''),
            'fuel_type': plant.get('fuel_type', plant.get('type', 'Unknown')),
            'status': plant.get('status', 'Unknown'),
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
    
    print(f"\n✅ Successfully loaded {total_inserted} CVA plants to BigQuery!")
    
    # Verify
    print(f"\n📊 Verifying data...")
    query = f"""
    SELECT 
        COUNT(*) as total_plants,
        COUNT(DISTINCT fuel_type) as unique_fuel_types,
        COUNT(CASE WHEN lat IS NOT NULL THEN 1 END) as with_coords
    FROM `{table_ref}`
    """
    
    result = client.query(query).result()
    for row in result:
        print(f"\n✅ Verification:")
        print(f"   Total plants: {row.total_plants:,}")
        print(f"   With coordinates: {row.with_coords:,}")
        print(f"   Unique fuel types: {row.unique_fuel_types}")
    
    print(f"\n🎉 BigQuery upload complete!")
    print(f"   Table: {table_ref}")
    print(f"   Rows: {total_inserted:,}")
    
    return total_inserted

if __name__ == "__main__":
    try:
        load_to_bigquery()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
