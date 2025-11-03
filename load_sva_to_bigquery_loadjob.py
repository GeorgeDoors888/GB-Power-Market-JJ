#!/usr/bin/env python3
"""
Load SVA generators to BigQuery using load job (most reliable method)
"""

from google.cloud import bigquery
import json
import tempfile

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "sva_generators"

def load_sva_to_bigquery():
    """Load SVA generators to BigQuery using load job"""
    
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
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Define schema
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
    
    # Delete existing table if exists
    try:
        client.delete_table(table_id)
        print(f"🗑️  Deleted existing table")
    except:
        pass
    
    # Prepare data in newline-delimited JSON format
    print(f"\n⚡ Preparing data...")
    rows = []
    for gen in generators:
        row = {
            'name': gen.get('name', ''),
            'dno': gen.get('dno', ''),
            'gsp': gen.get('gsp', ''),
            'lat': float(gen['lat']) if gen.get('lat') is not None else None,
            'lng': float(gen['lng']) if gen.get('lng') is not None else None,
            'capacity_mw': float(gen['capacity']) if gen.get('capacity') is not None else None,
            'fuel_type': gen.get('source', ''),
            'technology_type': gen.get('type', ''),
            'status': gen.get('status', ''),
            'postcode': gen.get('postcode', ''),
        }
        rows.append(row)
    
    print(f"✅ Prepared {len(rows)} rows")
    
    # Write to temp file
    print(f"\n📝 Writing temporary file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        for row in rows:
            tmp.write(json.dumps(row) + '\n')
        tmp_path = tmp.name
    
    print(f"✅ Temporary file: {tmp_path}")
    
    # Configure load job
    print(f"\n📤 Loading to BigQuery...")
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    # Load data
    with open(tmp_path, 'rb') as source_file:
        job = client.load_table_from_file(
            source_file,
            table_id,
            job_config=job_config
        )
    
    # Wait for job to complete
    print(f"   Job ID: {job.job_id}")
    print(f"   Waiting for job to complete...")
    job.result()
    
    print(f"\n✅ Successfully loaded {len(rows)} SVA generators to BigQuery!")
    
    # Clean up temp file
    import os
    os.remove(tmp_path)
    
    # Verify and get statistics
    print(f"\n📊 Verifying data...")
    query = f"""
    SELECT 
        COUNT(*) as total_generators,
        COUNT(DISTINCT dno) as unique_dnos,
        COUNT(DISTINCT fuel_type) as unique_fuel_types,
        ROUND(SUM(capacity_mw), 2) as total_capacity_mw,
        COUNT(CASE WHEN lat IS NOT NULL THEN 1 END) as with_coords
    FROM `{table_id}`
    """
    
    result = client.query(query).result()
    for row in result:
        total_cap = row.total_capacity_mw if row.total_capacity_mw else 0
        coord_pct = (row.with_coords / row.total_generators * 100) if row.total_generators > 0 else 0
        print(f"\n✅ Verification:")
        print(f"   Total generators: {row.total_generators:,}")
        print(f"   With coordinates: {row.with_coords:,} ({coord_pct:.1f}%)")
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
    FROM `{table_id}`
    WHERE fuel_type IS NOT NULL AND fuel_type != ''
    GROUP BY fuel_type
    ORDER BY count DESC
    LIMIT 10
    """
    
    result = client.query(query).result()
    for row in result:
        total = row.total_mw if row.total_mw else 0
        print(f"   {row.fuel_type}: {row.count:,} generators | {total:,.2f} MW")
    
    # Top DNOs
    print(f"\n📊 Top DNOs:")
    query = f"""
    SELECT 
        dno,
        COUNT(*) as count,
        ROUND(SUM(capacity_mw), 2) as total_mw
    FROM `{table_id}`
    WHERE dno IS NOT NULL AND dno != ''
    GROUP BY dno
    ORDER BY count DESC
    LIMIT 10
    """
    
    result = client.query(query).result()
    for row in result:
        total = row.total_mw if row.total_mw else 0
        print(f"   {row.dno}: {row.count:,} generators | {total:,.2f} MW")
    
    print(f"\n🎉 Upload complete!")
    print(f"   Table: {table_id}")
    
    return len(rows)

if __name__ == "__main__":
    try:
        load_sva_to_bigquery()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
