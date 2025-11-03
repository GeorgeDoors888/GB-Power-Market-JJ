#!/usr/bin/env python3
"""
Load CVA plants data to BigQuery
Waits for scraping to complete, then uploads to BigQuery
"""

from google.cloud import bigquery
import json
import time
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "cva_plants"

def wait_for_scraping():
    """Wait for scraping to complete"""
    
    input_file = "cva_plants_data.json"
    
    print("⏳ Waiting for scraping to complete...")
    print(f"   Looking for: {input_file}")
    print()
    
    last_size = 0
    stable_count = 0
    
    while True:
        if os.path.exists(input_file):
            current_size = os.path.getsize(input_file)
            
            # Check if file is still growing
            if current_size == last_size:
                stable_count += 1
            else:
                stable_count = 0
                print(f"   📊 Current file size: {current_size / 1024 / 1024:.2f} MB")
            
            # If file hasn't changed in 3 checks (30 seconds), assume complete
            if stable_count >= 3:
                print(f"\n✅ File appears complete!")
                return input_file
            
            last_size = current_size
        
        time.sleep(10)

def load_to_bigquery():
    """Load CVA plants to BigQuery"""
    
    input_file = "cva_plants_data.json"
    
    # Wait for file if it doesn't exist yet
    if not os.path.exists(input_file):
        print("⏳ Waiting for scraping to complete...")
        wait_for_scraping()
    
    print(f"\n🔋 Loading CVA Plants to BigQuery")
    print("="*90)
    
    # Load data
    print(f"📂 Loading {input_file}...")
    with open(input_file, 'r') as f:
        plants = json.load(f)
    
    print(f"✅ Loaded {len(plants)} plants")
    
    # Filter to only plants with coordinates
    plants_with_coords = [p for p in plants if 'lat' in p and 'lng' in p]
    print(f"   Plants with coordinates: {len(plants_with_coords)}")
    
    # Connect to BigQuery
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Define schema
    schema = [
        bigquery.SchemaField("plant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("lat", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("lng", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("capacity_mw", "FLOAT64"),
        bigquery.SchemaField("fuel_type", "STRING"),
        bigquery.SchemaField("status", "STRING"),
        bigquery.SchemaField("operator", "STRING"),
        bigquery.SchemaField("url", "STRING"),
        bigquery.SchemaField("location_geography", "GEOGRAPHY"),
    ]
    
    # Create table
    print(f"\n📊 Creating table: {table_ref}")
    
    table = bigquery.Table(table_ref, schema=schema)
    table = client.create_table(table, exists_ok=True)
    print(f"✅ Table ready")
    
    # Prepare rows
    print(f"\n⚡ Preparing data for BigQuery...")
    rows_to_insert = []
    
    for plant in plants_with_coords:
        row = {
            'plant_id': plant['plant_id'],
            'name': plant.get('name', 'Unknown'),
            'lat': plant['lat'],
            'lng': plant['lng'],
            'capacity_mw': plant.get('capacity_mw'),
            'fuel_type': plant.get('fuel_type'),
            'status': plant.get('status'),
            'operator': plant.get('operator'),
            'url': plant.get('url'),
            'location_geography': f"POINT({plant['lng']} {plant['lat']})"
        }
        rows_to_insert.append(row)
    
    print(f"✅ Prepared {len(rows_to_insert)} rows")
    
    # Insert in batches
    print(f"\n📤 Inserting to BigQuery...")
    batch_size = 500
    
    for i in range(0, len(rows_to_insert), batch_size):
        batch = rows_to_insert[i:i+batch_size]
        
        # Convert GEOGRAPHY strings to proper format
        for row in batch:
            if row['location_geography']:
                row['location_geography'] = f"ST_GEOGPOINT({row['lng']}, {row['lat']})"
        
        errors = client.insert_rows_json(table_ref, batch)
        
        if errors:
            print(f"❌ Errors in batch {i//batch_size + 1}: {errors}")
        else:
            print(f"   ✅ Batch {i//batch_size + 1}/{(len(rows_to_insert)-1)//batch_size + 1}: {len(batch)} rows")
    
    print(f"\n✅ Successfully loaded {len(rows_to_insert)} CVA plants to BigQuery!")
    
    # Verify
    print(f"\n📊 Verifying data...")
    query = f"""
    SELECT 
        fuel_type,
        COUNT(*) as count,
        SUM(capacity_mw) as total_capacity_mw,
        AVG(capacity_mw) as avg_capacity_mw
    FROM `{table_ref}`
    WHERE capacity_mw IS NOT NULL
    GROUP BY fuel_type
    ORDER BY total_capacity_mw DESC
    """
    
    results = client.query(query).result()
    
    print(f"\n📈 CVA Plants by Fuel Type:")
    print("-"*90)
    print(f"{'Fuel Type':<30} {'Count':<10} {'Total MW':<15} {'Avg MW':<12}")
    print("-"*90)
    
    total_count = 0
    total_capacity = 0
    
    for row in results:
        print(f"{row.fuel_type:<30} {row.count:>8,}  {row.total_capacity_mw:>13,.0f}  {row.avg_capacity_mw:>10,.1f}")
        total_count += row.count
        total_capacity += row.total_capacity_mw
    
    print("-"*90)
    print(f"{'TOTAL':<30} {total_count:>8,}  {total_capacity:>13,.0f}")
    print()
    
    return len(rows_to_insert)

if __name__ == '__main__':
    count = load_to_bigquery()
    print(f"\n🎉 Complete! Loaded {count} CVA plants to BigQuery")
