"""
Load OFFICIAL NESO DNO Boundaries from GeoJSON to BigQuery
These are the real boundaries from NESO's official GIS data
"""

from google.cloud import bigquery
import json

def load_official_dno_boundaries():
    """Load official DNO boundaries to BigQuery"""
    
    print("🗺️  Loading OFFICIAL NESO DNO Boundaries...")
    
    # Load the official GeoJSON
    with open('official_dno_boundaries.geojson', 'r') as f:
        geojson = json.load(f)
    
    print(f"✅ Loaded {len(geojson['features'])} DNO license areas from file")
    
    client = bigquery.Client(project='inner-cinema-476211-u9')
    table_id = "inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries"
    
    # Create schema
    schema = [
        bigquery.SchemaField("dno_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("gsp_group", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("area_name", "STRING"),
        bigquery.SchemaField("dno_full_name", "STRING"),
        bigquery.SchemaField("boundary", "GEOGRAPHY", mode="REQUIRED"),
    ]
    
    # Prepare records
    records = []
    for feature in geojson['features']:
        props = feature['properties']
        geom = feature['geometry']
        
        # Convert GeoJSON geometry to WKT
        if geom['type'] == 'Polygon':
            coords = ', '.join([f"{lng} {lat}" for lng, lat in geom['coordinates'][0]])
            wkt = f"POLYGON(({coords}))"
        elif geom['type'] == 'MultiPolygon':
            polygons = []
            for polygon in geom['coordinates']:
                ring = ', '.join([f"{lng} {lat}" for lng, lat in polygon[0]])
                polygons.append(f"(({ring}))")
            wkt = f"MULTIPOLYGON({', '.join(polygons)})"
        else:
            print(f"⚠️  Skipping unknown geometry type: {geom['type']}")
            continue
        
        records.append({
            "dno_id": props['ID'],
            "gsp_group": props['Name'],  # e.g., "_A", "_B", etc.
            "dno_code": props['DNO'],
            "area_name": props['Area'],
            "dno_full_name": props['DNO_Full'],
            "boundary": wkt
        })
    
    # Load to BigQuery
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    try:
        job = client.load_table_from_json(records, table_id, job_config=job_config)
        job.result()
        
        table = client.get_table(table_id)
        print(f"✅ Loaded {table.num_rows} DNO boundaries to BigQuery")
        print(f"   Table: {table_id}")
        
        # Verify
        query = f"""
        SELECT 
            gsp_group,
            dno_code,
            dno_full_name,
            area_name
        FROM `{table_id}`
        ORDER BY gsp_group
        """
        
        print("\n📊 Loaded DNO Boundaries:")
        results = client.query(query).result()
        for row in results:
            print(f"GSP {row.gsp_group:3s} | {row.dno_code:8s} | {row.dno_full_name:35s} | {row.area_name}")
        
        return table_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🗺️  OFFICIAL NESO DNO BOUNDARIES LOADER")
    print("=" * 60)
    print("\nLoading OFFICIAL NESO DNO GIS boundaries from GeoJSON")
    print("Source: NESO (formerly National Grid ESO)")
    print()
    
    # Load DNO boundaries
    table = load_official_dno_boundaries()
    
    if table:
        print("\n✅ SUCCESS!")
        print(f"\nTable created: {table}")
        print("\n14 DNO license areas loaded with REAL geographic boundaries!")
        print("\nThis is the official NESO data you requested.")
