#!/usr/bin/env python3
"""
Load DNO and GSP GeoJSON Files to BigQuery
Loads spatial boundary data for all 14 GB DNO license areas and GSP regions
"""

import json
import argparse
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "gb_power"
CREDENTIALS_FILE = "jibber_jabber_key.json"


def create_client():
    """Create BigQuery client"""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    return bigquery.Client(credentials=credentials, project=PROJECT_ID)


def load_dno_boundaries(client, geojson_file: str):
    """Load DNO license area boundaries from GeoJSON"""
    print(f"\n📍 Loading DNO boundaries from {geojson_file}")
    
    # Read GeoJSON
    with open(geojson_file, 'r') as f:
        data = json.load(f)
        
    features = data.get('features', [])
    print(f"  Found {len(features)} DNO license areas")
    
    # Map property names to DNO keys
    property_mapping = {
        "Eastern Power Networks plc": "UKPN-EPN",
        "London Power Networks plc": "UKPN-LPN",
        "South Eastern Power Networks plc": "UKPN-SPN",
        "Electricity North West Limited": "ENWL",
        "Northern Powergrid (Northeast) plc": "NPg-NE",
        "Northern Powergrid (Yorkshire) plc": "NPg-Y",
        "SP Distribution plc": "SP-Distribution",
        "SP Manweb plc": "SP-Manweb",
        "Scottish Hydro Electric Power Distribution plc": "SSE-SHEPD",
        "Southern Electric Power Distribution plc": "SSE-SEPD",
        "West Midlands": "NGED-WM",
        "East Midlands": "NGED-EM",
        "South West": "NGED-SW",
        "South Wales": "NGED-SWales"
    }
    
    # Prepare rows
    rows_to_insert = []
    
    for feature in features:
        props = feature.get('properties', {})
        geometry = feature.get('geometry')
        
        # Try to identify DNO key from properties
        long_name = props.get('LongName', '')
        short_name = props.get('ShortName', '')
        gsp_group = props.get('GSP_Group', '')
        
        # Map to standard DNO key
        dno_key = None
        for name_variant, key in property_mapping.items():
            if name_variant.lower() in long_name.lower():
                dno_key = key
                break
                
        if not dno_key:
            # Try GSP group mapping
            gsp_to_dno = {
                'A': 'UKPN-EPN', 'B': 'NGED-EM', 'C': 'UKPN-LPN', 'D': 'SP-Manweb',
                'E': 'NGED-WM', 'F': 'NPg-NE', 'G': 'ENWL', 'H': 'SSE-SEPD',
                'J': 'UKPN-SPN', 'K': 'NGED-SWales', 'L': 'NGED-SW',
                'M': 'NPg-Y', 'N': 'SP-Distribution', 'P': 'SSE-SHEPD'
            }
            dno_key = gsp_to_dno.get(gsp_group)
            
        if not dno_key:
            print(f"  ⚠️  Could not map: {long_name} (GSP: {gsp_group})")
            continue
            
        # Convert geometry to WKT for BigQuery
        geojson_str = json.dumps(geometry)
        
        row = {
            "dno_key": dno_key,
            "boundary_name": long_name,
            "boundary_type": "LICENSE_AREA",
            "geometry": geojson_str,  # BigQuery will parse this
            "area_km2": None,  # Will calculate in BigQuery
            "population_served": None,
            "source": "Ofgem DNO License Areas",
            "source_date": "2024-05-03"
        }
        
        rows_to_insert.append(row)
        print(f"  ✓ Mapped: {long_name} → {dno_key}")
        
    # Insert rows
    table_id = f"{PROJECT_ID}.{DATASET_ID}.dno_boundaries"
    
    # First, create newline-delimited JSON file
    ndjson_file = "dno_boundaries_temp.ndjson"
    with open(ndjson_file, 'w') as f:
        for row in rows_to_insert:
            f.write(json.dumps(row) + '\n')
            
    print(f"\n  Preparing to load {len(rows_to_insert)} rows to {table_id}")
    
    # Load via file (better for GEOGRAPHY type)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    with open(ndjson_file, 'rb') as f:
        load_job = client.load_table_from_file(f, table_id, job_config=job_config)
        
    load_job.result()  # Wait for completion
    
    # Clean up temp file
    Path(ndjson_file).unlink()
    
    # Calculate areas
    query = f"""
    UPDATE `{PROJECT_ID}.{DATASET_ID}.dno_boundaries`
    SET area_km2 = ST_AREA(ST_GEOGFROMGEOJSON(geometry)) / 1000000
    WHERE area_km2 IS NULL
    """
    
    print("  Calculating areas...")
    client.query(query).result()
    
    print(f"\n  ✅ Loaded {len(rows_to_insert)} DNO boundaries")
    
    # Verify
    query = f"""
    SELECT dno_key, boundary_name, ROUND(area_km2, 0) as area_km2
    FROM `{PROJECT_ID}.{DATASET_ID}.dno_boundaries`
    ORDER BY dno_key
    """
    
    results = client.query(query).result()
    print("\n  📊 DNO Boundaries Summary:")
    for row in results:
        print(f"    {row.dno_key:20s}: {row.boundary_name:50s} ({row.area_km2:,.0f} km²)")


def load_gsp_boundaries(client, geojson_file: str):
    """Load GSP region boundaries from GeoJSON"""
    print(f"\n📍 Loading GSP boundaries from {geojson_file}")
    
    # Read GeoJSON
    with open(geojson_file, 'r') as f:
        data = json.load(f)
        
    features = data.get('features', [])
    print(f"  Found {len(features)} GSP regions")
    
    # GSP Group to DNO mapping
    gsp_to_dno = {
        'A': 'UKPN-EPN', 'B': 'NGED-EM', 'C': 'UKPN-LPN', 'D': 'SP-Manweb',
        'E': 'NGED-WM', 'F': 'NPg-NE', 'G': 'ENWL', 'H': 'SSE-SEPD',
        'J': 'UKPN-SPN', 'K': 'NGED-SWales', 'L': 'NGED-SW',
        'M': 'NPg-Y', 'N': 'SP-Distribution', 'P': 'SSE-SHEPD'
    }
    
    # Prepare rows
    rows_to_insert = []
    
    for feature in features:
        props = feature.get('properties', {})
        geometry = feature.get('geometry')
        
        gsp_id = props.get('ID', props.get('GSP_ID', ''))
        gsp_name = props.get('Name', props.get('GSP_NAME', ''))
        gsp_group = props.get('GSP_Group', props.get('GroupId', ''))
        
        if not gsp_id or not gsp_group:
            continue
            
        dno_key = gsp_to_dno.get(gsp_group)
        if not dno_key:
            print(f"  ⚠️  Unknown GSP group: {gsp_group}")
            continue
            
        geojson_str = json.dumps(geometry)
        
        row = {
            "gsp_id": gsp_id,
            "gsp_name": gsp_name,
            "gsp_group_id": gsp_group,
            "dno_key": dno_key,
            "geometry": geojson_str,
            "area_km2": None,
            "source": "NESO GSP Regions 2025-01-09"
        }
        
        rows_to_insert.append(row)
        
    print(f"\n  Preparing to load {len(rows_to_insert)} GSP regions")
    
    # Create NDJSON file
    ndjson_file = "gsp_boundaries_temp.ndjson"
    with open(ndjson_file, 'w') as f:
        for row in rows_to_insert:
            f.write(json.dumps(row) + '\n')
            
    # Load to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.gsp_boundaries"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    with open(ndjson_file, 'rb') as f:
        load_job = client.load_table_from_file(f, table_id, job_config=job_config)
        
    load_job.result()
    
    Path(ndjson_file).unlink()
    
    # Calculate areas
    query = f"""
    UPDATE `{PROJECT_ID}.{DATASET_ID}.gsp_boundaries`
    SET area_km2 = ST_AREA(ST_GEOGFROMGEOJSON(geometry)) / 1000000
    WHERE area_km2 IS NULL
    """
    
    print("  Calculating areas...")
    client.query(query).result()
    
    print(f"\n  ✅ Loaded {len(rows_to_insert)} GSP boundaries")
    
    # Summary by DNO
    query = f"""
    SELECT 
      dno_key,
      COUNT(*) as gsp_count,
      ROUND(SUM(area_km2), 0) as total_area_km2
    FROM `{PROJECT_ID}.{DATASET_ID}.gsp_boundaries`
    GROUP BY dno_key
    ORDER BY dno_key
    """
    
    results = client.query(query).result()
    print("\n  📊 GSP Summary by DNO:")
    for row in results:
        print(f"    {row.dno_key:20s}: {row.gsp_count:3d} GSPs ({row.total_area_km2:,.0f} km²)")


def validate_spatial_data(client):
    """Run validation queries on loaded spatial data"""
    print("\n🔍 Validating spatial data...")
    
    # Check DNO boundaries are valid
    query = f"""
    SELECT 
      dno_key,
      ST_ISVALID(ST_GEOGFROMGEOJSON(geometry)) as is_valid,
      area_km2
    FROM `{PROJECT_ID}.{DATASET_ID}.dno_boundaries`
    WHERE NOT ST_ISVALID(ST_GEOGFROMGEOJSON(geometry))
    """
    
    results = list(client.query(query).result())
    if results:
        print(f"  ⚠️  Found {len(results)} invalid DNO geometries")
        for row in results:
            print(f"    {row.dno_key}: Invalid geometry")
    else:
        print("  ✅ All DNO geometries are valid")
        
    # Check for overlaps
    query = f"""
    SELECT 
      a.dno_key as dno1,
      b.dno_key as dno2,
      ST_AREA(ST_INTERSECTION(
        ST_GEOGFROMGEOJSON(a.geometry),
        ST_GEOGFROMGEOJSON(b.geometry)
      )) / 1000000 as overlap_km2
    FROM `{PROJECT_ID}.{DATASET_ID}.dno_boundaries` a
    CROSS JOIN `{PROJECT_ID}.{DATASET_ID}.dno_boundaries` b
    WHERE a.dno_key < b.dno_key
      AND ST_INTERSECTS(
        ST_GEOGFROMGEOJSON(a.geometry),
        ST_GEOGFROMGEOJSON(b.geometry)
      )
    """
    
    results = list(client.query(query).result())
    if results:
        print(f"\n  ⚠️  Found {len(results)} DNO boundary overlaps:")
        for row in results:
            print(f"    {row.dno1} ↔ {row.dno2}: {row.overlap_km2:.2f} km²")
    else:
        print("  ✅ No DNO boundary overlaps (boundaries are mutually exclusive)")
        
    # Test point containment
    print("\n  🎯 Testing point containment (London coordinates)...")
    query = f"""
    SELECT dno_key, boundary_name
    FROM `{PROJECT_ID}.{DATASET_ID}.dno_boundaries`
    WHERE ST_CONTAINS(
      ST_GEOGFROMGEOJSON(geometry),
      ST_GEOGPOINT(-0.1278, 51.5074)  -- London
    )
    """
    
    results = list(client.query(query).result())
    if results:
        for row in results:
            print(f"    London is in: {row.dno_key} ({row.boundary_name})")
    else:
        print("    ⚠️  London coordinates not contained in any DNO")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Load DNO and GSP GeoJSON to BigQuery")
    parser.add_argument("--dno-file", default="old_project/GIS_data/gb-dno-license-areas-20240503-as-geojson.geojson")
    parser.add_argument("--gsp-file", default="old_project/GIS_data/GSP_regions_4326_20250109_simplified.geojson")
    parser.add_argument("--skip-dno", action="store_true", help="Skip loading DNO boundaries")
    parser.add_argument("--skip-gsp", action="store_true", help="Skip loading GSP boundaries")
    
    args = parser.parse_args()
    
    print("="*70)
    print("LOADING GEOJSON SPATIAL DATA TO BIGQUERY")
    print("="*70)
    
    client = create_client()
    print(f"\n✅ Connected to BigQuery project: {PROJECT_ID}")
    
    if not args.skip_dno:
        load_dno_boundaries(client, args.dno_file)
        
    if not args.skip_gsp:
        load_gsp_boundaries(client, args.gsp_file)
        
    validate_spatial_data(client)
    
    print("\n" + "="*70)
    print("SPATIAL DATA LOADING COMPLETE")
    print("="*70)
    print(f"\n✅ DNO boundaries loaded to: {PROJECT_ID}.{DATASET_ID}.dno_boundaries")
    print(f"✅ GSP boundaries loaded to: {PROJECT_ID}.{DATASET_ID}.gsp_boundaries")
    print("\n🎯 Next steps:")
    print("  1. Extract tariff data from NGED files")
    print("  2. Join tariffs to geographic boundaries")
    print("  3. Create Google Sheets with spatial filters")


if __name__ == "__main__":
    main()
