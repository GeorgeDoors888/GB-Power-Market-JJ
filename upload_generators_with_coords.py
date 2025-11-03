#!/usr/bin/env python3
"""
Update sva_generators in BigQuery with coordinate and DNO/GSP data from generators.json
"""

from google.cloud import bigquery
import json

def main():
    print("=" * 70)
    print("📊 UPDATING SVA GENERATORS WITH COORDINATE DATA")
    print("=" * 70)
    
    # Load generators.json
    print("\n🔍 Loading generators.json...")
    with open('generators.json', 'r') as f:
        generators = json.load(f)
    
    print(f"✅ Loaded {len(generators):,} generators from JSON")
    
    # Check how many have coordinates
    with_coords = sum(1 for g in generators if g.get('lat') and g.get('lng'))
    with_dno = sum(1 for g in generators if g.get('dno'))
    with_gsp = sum(1 for g in generators if g.get('gsp'))
    
    print(f"   📍 With coordinates: {with_coords:,}")
    print(f"   🏢 With DNO: {with_dno:,}")
    print(f"   ⚡ With GSP: {with_gsp:,}")
    
    # Create a new table with this data
    client = bigquery.Client(project="inner-cinema-476211-u9")
    
    table_id = "inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords"
    
    # Transform data for BigQuery
    rows_to_insert = []
    for g in generators:
        row = {
            'plant_id': g.get('name', 'UNKNOWN')[:100],  # Use name as ID for now
            'name': g.get('name'),
            'dno': g.get('dno'),
            'gsp': g.get('gsp'),
            'lat': float(g['lat']) if g.get('lat') else None,
            'lng': float(g['lng']) if g.get('lng') else None,
            'capacity_mw': float(g['capacity']) if g.get('capacity') else None,
            'fuel_type': g.get('type') or g.get('source'),
            'technology': g.get('type'),
            'postcode': g.get('postcode'),
            'status': g.get('status')
        }
        rows_to_insert.append(row)
    
    print(f"\n⬆️  Uploading {len(rows_to_insert):,} rows to BigQuery...")
    print(f"   Table: {table_id}")
    
    # Define schema
    schema = [
        bigquery.SchemaField("plant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("dno", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("gsp", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("lat", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("lng", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("capacity_mw", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("fuel_type", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("technology", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("postcode", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("status", "STRING", mode="NULLABLE"),
    ]
    
    # Create table
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=True)
    
    # Insert data in batches
    batch_size = 500
    errors = []
    
    for i in range(0, len(rows_to_insert), batch_size):
        batch = rows_to_insert[i:i+batch_size]
        batch_errors = client.insert_rows_json(table, batch)
        if batch_errors:
            errors.extend(batch_errors)
        print(f"   Uploaded batch {i//batch_size + 1}/{(len(rows_to_insert)-1)//batch_size + 1}")
    
    if errors:
        print(f"\n⚠️  Encountered {len(errors)} errors:")
        for error in errors[:5]:
            print(f"   {error}")
    else:
        print("\n✅ Upload complete!")
    
    # Verify data
    print("\n🔍 Verifying uploaded data...")
    verify_query = f"""
    SELECT 
        COUNT(*) as total_count,
        SUM(CASE WHEN lat IS NOT NULL THEN 1 ELSE 0 END) as with_coords,
        SUM(CASE WHEN dno IS NOT NULL AND dno != '' THEN 1 ELSE 0 END) as with_dno,
        SUM(CASE WHEN gsp IS NOT NULL AND gsp != '' THEN 1 ELSE 0 END) as with_gsp,
        COUNT(DISTINCT dno) as distinct_dnos,
        COUNT(DISTINCT gsp) as distinct_gsps
    FROM `{table_id}`
    """
    
    result = list(client.query(verify_query).result())[0]
    print(f"   Total rows: {result.total_count:,}")
    print(f"   With coordinates: {result.with_coords:,}")
    print(f"   With DNO: {result.with_dno:,}")
    print(f"   With GSP: {result.with_gsp:,}")
    print(f"   Distinct DNOs: {result.distinct_dnos}")
    print(f"   Distinct GSPs: {result.distinct_gsps}")
    
    print("\n✅ Done! New table created: sva_generators_with_coords")

if __name__ == "__main__":
    main()
