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
    
    print(f"✅ Loaded {len(geojson['features'])} DNO license areas")
    
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
            area_name,
            ST_AREA(boundary) / 1000000 as area_sqkm
        FROM `{table_id}`
        ORDER BY dno_id
        """
        
        print("\n📊 Loaded DNO Boundaries:")
        print("-" * 100)
        
        results = client.query(query).result()
        for row in results:
            print(f"GSP {row.gsp_group:3} | {row.dno_code:6} | {row.dno_full_name:25} | {row.area_name:25} | {row.area_sqkm:,.0f} km²")
        
        return table_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_official_gsp_boundaries():
    """Load official GSP boundaries to BigQuery"""
    
    print("\n🗺️  Loading OFFICIAL NESO GSP Boundaries...")
    
    # Load the official GeoJSON
    with open('official_gsp_boundaries.geojson', 'r') as f:
        geojson = json.load(f)
    
    print(f"✅ Loaded {len(geojson['features'])} GSP zones")
    
    client = bigquery.Client(project='inner-cinema-476211-u9')
    table_id = "inner-cinema-476211-u9.uk_energy_prod.neso_gsp_boundaries"
    
    # Check what properties are available
    if geojson['features']:
        print(f"   First feature properties: {geojson['features'][0]['properties'].keys()}")
    
    # Create schema
    schema = [
        bigquery.SchemaField("gsp_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("boundary", "GEOGRAPHY", mode="REQUIRED"),
    ]
    
    # Prepare records
    records = []
    for feature in geojson['features']:
        props = feature['properties']
        geom = feature['geometry']
        
        # Get GSP name from properties (check different possible keys)
        gsp_name = props.get('Name') or props.get('GSP_Name') or props.get('name') or f"GSP_{len(records)+1}"
        
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
            continue
        
        records.append({
            "gsp_name": gsp_name,
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
        print(f"✅ Loaded {table.num_rows} GSP boundaries to BigQuery")
        print(f"   Table: {table_id}")
        
        return table_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🗺️  OFFICIAL NESO GEOGRAPHIC DATA LOADER")
    print("=" * 60)
    print("\nLoading OFFICIAL NESO GIS boundaries from GeoJSON files")
    print("Source: NESO (formerly National Grid ESO)")
    print()
    
    # Load DNO boundaries
    dno_table = load_official_dno_boundaries()
    
    # Load GSP boundaries
    gsp_table = load_official_gsp_boundaries()
    
    if dno_table and gsp_table:
        print("\n✅ SUCCESS!")
        print("\nTables created:")
        print(f"1. {dno_table} - 14 DNO license areas")
        print(f"2. {gsp_table} - GSP zones")
        print("\nThis is the REAL NESO geographic data!")
