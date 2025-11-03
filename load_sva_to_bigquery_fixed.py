#!/usr/bin/env python3
"""
Load SVA generators data to BigQuery (FIXED VERSION)
Uploads the 7,072 embedded generation sites with correct field mapping
"""

from google.cloud import bigquery
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "sva_generators"

def load_sva_to_bigquery():
    """Load SVA generators to BigQuery"""
    
    input_file = "generators.json"
    
    print(f"\n⚡ Loading SVA Generators to BigQuery (Fixed Version)")
    print("="*90)
    
    # Load data
    print(f"📂 Loading {input_file}...")
    with open(input_file, 'r') as f:
        generators = json.load(f)
    
    print(f"✅ Loaded {len(generators)} generators")
    
    # Connect to BigQuery
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Define schema based on actual data structure
    schema = [
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno", "STRING"),
        bigquery.SchemaField("gsp", "STRING"),
        bigquery.SchemaField("lat", "FLOAT64"),
        bigquery.SchemaField("lng", "FLOAT64"),
        bigquery.SchemaField("capacity_mw", "FLOAT64"),
        bigquery.SchemaField("fuel_type", "STRING"),
        bigquery.SchemaField("technology_type", "STRING"),
        bigquery.SchemaField("status", "STRING"),
        bigquery.SchemaField("postcode", "STRING"),
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
    
    # Wait for table to be ready
    import time
    time.sleep(2)
    
    # Prepare rows with correct field mapping
    print(f"\n⚡ Preparing data for BigQuery...")
    rows_to_insert = []
    
    for gen in generators:
        row = {
            'name': gen.get('name', ''),
            'dno': gen.get('dno', ''),
            'gsp': gen.get('gsp', ''),
            'lat': float(gen['lat']) if gen.get('lat') is not None else None,
            'lng': float(gen['lng']) if gen.get('lng') is not None else None,
            'capacity_mw': float(gen['capacity']) if gen.get('capacity') is not None else None,
            'fuel_type': gen.get('source', ''),  # 'source' field contains fuel type
            'technology_type': gen.get('type', ''),  # 'type' field contains technology
            'status': gen.get('status', ''),
            'postcode': gen.get('postcode', ''),
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
            print(f"❌ Errors in batch {i//batch_size + 1}: {errors[:3]}...")
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
        total_cap = row.total_capacity_mw if row.total_capacity_mw else 0
        print(f"\n✅ Verification:")
        print(f"   Total generators: {row.total_generators:,}")
        print(f"   With coordinates: {row.with_coords:,} ({row.with_coords/row.total_generators*100:.1f}%)")
        print(f"   Unique DNOs: {row.unique_dnos}")
        print(f"   Unique fuel types: {row.unique_fuel_types}")
        print(f"   Total capacity: {total_cap:,.2f} MW")
    
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
        total = row.total_mw if row.total_mw else 0
        pct = (row.count / total_inserted) * 100
        print(f"   {row.fuel_type}: {row.count:,} generators ({pct:.1f}%) | {total:,.2f} MW")
    
    # Top DNOs
    print(f"\n📊 Top DNOs:")
    query = f"""
    SELECT 
        dno,
        COUNT(*) as count
    FROM `{table_ref}`
    WHERE dno IS NOT NULL AND dno != ''
    GROUP BY dno
    ORDER BY count DESC
    LIMIT 10
    """
    
    result = client.query(query).result()
    for row in result:
        pct = (row.count / total_inserted) * 100
        print(f"   {row.dno}: {row.count:,} generators ({pct:.1f}%)")
    
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
