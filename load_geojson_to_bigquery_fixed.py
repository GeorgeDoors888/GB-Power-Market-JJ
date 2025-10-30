#!/usr/bin/env python3
"""
FIXED: Load DNO and GSP GeoJSON Files to BigQuery
Loads spatial boundary data for all 14 GB DNO license areas and GSP regions
"""

import json
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "gb_power"
CREDENTIALS_FILE = "jibber_jabber_key.json"
GEOJSON_DIR = Path("old_project/GIS_data")


def create_client():
    """Create BigQuery client"""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    return bigquery.Client(credentials=credentials, project=PROJECT_ID)


def inspect_geojson_properties(geojson_file):
    """Inspect properties in a GeoJSON file"""
    print(f"\n🔍 Inspecting: {geojson_file.name}")
    
    with open(geojson_file, 'r') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    if features:
        print(f"   Features found: {len(features)}")
        print(f"   Sample properties: {list(features[0].get('properties', {}).keys())}")
        
        # Show first few property values
        for key, value in list(features[0].get('properties', {}).items())[:5]:
            print(f"      {key}: {value}")
    
    return features


def load_dno_boundaries_fixed(client):
    """Load DNO boundaries with updated property mapping"""
    print("\n" + "=" * 80)
    print("📍 LOADING DNO BOUNDARIES")
    print("=" * 80)
    
    # Try the most recent DNO file
    dno_files = [
        "gb-dno-license-areas-20240503-as-geojson.geojson",
        "dno_license_areas_20200506.geojson"
    ]
    
    for filename in dno_files:
        file_path = GEOJSON_DIR / filename
        if file_path.exists():
            print(f"\n✅ Found: {filename}")
            features = inspect_geojson_properties(file_path)
            
            # Check what properties are available
            if features:
                sample_props = features[0].get('properties', {})
                print(f"\n📋 Available properties:")
                for key in sample_props.keys():
                    print(f"   - {key}")
                
                # Map based on actual properties
                rows = []
                for feature in features:
                    props = feature.get('properties', {})
                    geometry = feature.get('geometry')
                    
                    # Extract identifiers (adapt based on actual properties)
                    name = props.get('LongName') or props.get('Name') or props.get('name', '')
                    gsp_group = props.get('GSP_Group') or props.get('GSPGroup', '')
                    
                    # Simple DNO mapping from our data
                    dno_code_mapping = {
                        'Eastern Power Networks': 'EPN',
                        'London Power Networks': 'LPN',
                        'South Eastern Power Networks': 'SPN',
                        'Electricity North West': 'ENWL',
                        'Northern Powergrid (Northeast)': 'NE',
                        'Northern Powergrid (Yorkshire)': 'Y',
                        'SP Distribution': 'SPD',
                        'SP Manweb': 'SPM',
                        'Scottish Hydro': 'SHEPD',
                        'Southern Electric': 'SEPD',
                        'West Midlands': 'WMID',
                        'East Midlands': 'EMID',
                        'South West': 'SWEST',
                        'South Wales': 'SWALES'
                    }
                    
                    dno_code = None
                    for key_phrase, code in dno_code_mapping.items():
                        if key_phrase.lower() in name.lower():
                            dno_code = code
                            break
                    
                    if not dno_code:
                        print(f"   ⚠️  Could not map: {name}")
                        continue
                    
                    row = {
                        "dno_code": dno_code,
                        "boundary_name": name,
                        "gsp_group": gsp_group,
                        "geometry_geojson": json.dumps(geometry),
                        "source_file": filename,
                        "loaded_date": datetime.now().isoformat()
                    }
                    
                    rows.append(row)
                    print(f"   ✓ {name} → {dno_code}")
                
                if rows:
                    print(f"\n💾 Loading {len(rows)} DNO boundaries to BigQuery...")
                    
                    table_id = f"{PROJECT_ID}.{DATASET_ID}.dno_boundaries"
                    
                    # Define schema
                    schema = [
                        bigquery.SchemaField("dno_code", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("boundary_name", "STRING"),
                        bigquery.SchemaField("gsp_group", "STRING"),
                        bigquery.SchemaField("geometry_geojson", "STRING"),
                        bigquery.SchemaField("source_file", "STRING"),
                        bigquery.SchemaField("loaded_date", "TIMESTAMP"),
                    ]
                    
                    # Create or replace table
                    table = bigquery.Table(table_id, schema=schema)
                    table = client.create_table(table, exists_ok=True)
                    
                    # Insert rows
                    errors = client.insert_rows_json(table_id, rows)
                    
                    if errors:
                        print(f"   ❌ Errors: {errors}")
                    else:
                        print(f"   ✅ Loaded {len(rows)} DNO boundaries")
                        
                        # Add GEOGRAPHY column
                        print(f"\n🗺️  Adding GEOGRAPHY column...")
                        alter_query = f"""
                        ALTER TABLE `{table_id}`
                        ADD COLUMN IF NOT EXISTS geometry GEOGRAPHY
                        """
                        client.query(alter_query).result()
                        
                        # Parse GeoJSON to GEOGRAPHY
                        update_query = f"""
                        UPDATE `{table_id}`
                        SET geometry = SAFE.ST_GEOGFROMGEOJSON(geometry_geojson)
                        WHERE geometry IS NULL
                        """
                        client.query(update_query).result()
                        print(f"   ✅ GEOGRAPHY column populated")
                        
                        # Calculate areas
                        area_query = f"""
                        SELECT 
                            dno_code,
                            boundary_name,
                            ROUND(ST_AREA(geometry) / 1000000, 0) as area_km2
                        FROM `{table_id}`
                        WHERE geometry IS NOT NULL
                        ORDER BY dno_code
                        """
                        
                        print(f"\n📊 Loaded DNO areas:")
                        results = client.query(area_query).result()
                        for row in results:
                            print(f"   {row.dno_code:6s} {row.boundary_name:45s} {row.area_km2:>10,.0f} km²")
                    
                    return True
            
            break
    
    return False


def load_gsp_regions_fixed(client):
    """Load GSP regions with updated property mapping"""
    print("\n" + "=" * 80)
    print("🗺️  LOADING GSP REGIONS")
    print("=" * 80)
    
    # Use the most recent GSP file in WGS84 (EPSG:4326)
    gsp_files = [
        "GSP_regions_4326_20250109.geojson",
        "gsp_regions_20220314.geojson",
        "gsp_regions_20181031.geojson"
    ]
    
    for filename in gsp_files:
        file_path = GEOJSON_DIR / filename
        if file_path.exists():
            print(f"\n✅ Found: {filename}")
            features = inspect_geojson_properties(file_path)
            
            if features:
                rows = []
                for feature in features:
                    props = feature.get('properties', {})
                    geometry = feature.get('geometry')
                    
                    # Extract GSP info
                    gsp_name = props.get('GSPName') or props.get('Name') or props.get('name', '')
                    gsp_group = props.get('GSPGroup') or props.get('Group', '')
                    
                    row = {
                        "gsp_name": gsp_name,
                        "gsp_group": gsp_group,
                        "geometry_geojson": json.dumps(geometry),
                        "source_file": filename,
                        "loaded_date": datetime.now().isoformat()
                    }
                    
                    rows.append(row)
                    print(f"   ✓ {gsp_name} (Group {gsp_group})")
                
                if rows:
                    print(f"\n💾 Loading {len(rows)} GSP regions to BigQuery...")
                    
                    table_id = f"{PROJECT_ID}.{DATASET_ID}.gsp_regions"
                    
                    schema = [
                        bigquery.SchemaField("gsp_name", "STRING"),
                        bigquery.SchemaField("gsp_group", "STRING"),
                        bigquery.SchemaField("geometry_geojson", "STRING"),
                        bigquery.SchemaField("source_file", "STRING"),
                        bigquery.SchemaField("loaded_date", "TIMESTAMP"),
                    ]
                    
                    table = bigquery.Table(table_id, schema=schema)
                    table = client.create_table(table, exists_ok=True)
                    
                    errors = client.insert_rows_json(table_id, rows)
                    
                    if not errors:
                        print(f"   ✅ Loaded {len(rows)} GSP regions")
                        
                        # Add GEOGRAPHY column
                        alter_query = f"""
                        ALTER TABLE `{table_id}`
                        ADD COLUMN IF NOT EXISTS geometry GEOGRAPHY
                        """
                        client.query(alter_query).result()
                        
                        update_query = f"""
                        UPDATE `{table_id}`
                        SET geometry = SAFE.ST_GEOGFROMGEOJSON(geometry_geojson)
                        WHERE geometry IS NULL
                        """
                        client.query(update_query).result()
                        print(f"   ✅ GEOGRAPHY column populated")
                    
                    return True
            
            break
    
    return False


def main():
    """Main execution"""
    print("=" * 80)
    print("GEOJSON TO BIGQUERY LOADER (FIXED)")
    print("=" * 80)
    print()
    print(f"📁 GeoJSON Directory: {GEOJSON_DIR}")
    print(f"☁️  BigQuery Project: {PROJECT_ID}")
    print(f"📊 Dataset: {DATASET_ID}")
    print()
    
    # Create client
    client = create_client()
    print("✅ Connected to BigQuery")
    
    # Load DNO boundaries
    dno_success = load_dno_boundaries_fixed(client)
    
    # Load GSP regions
    gsp_success = load_gsp_regions_fixed(client)
    
    print()
    print("=" * 80)
    if dno_success and gsp_success:
        print("✅ ALL GEOJSON FILES LOADED SUCCESSFULLY!")
    elif dno_success or gsp_success:
        print("⚠️  PARTIALLY COMPLETE")
    else:
        print("❌ LOADING FAILED")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
