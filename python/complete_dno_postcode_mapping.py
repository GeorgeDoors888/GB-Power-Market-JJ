#!/usr/bin/env python3
"""
Complete DNO → Postcode District Mapping Script
Exports DNO boundaries from BigQuery and maps to UK postcode districts
"""

import geopandas as gpd
import pandas as pd
import json
from google.cloud import bigquery
from google.oauth2 import service_account
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def export_dno_from_bigquery():
    """Step 1: Export DNO boundaries from BigQuery to GeoJSON"""
    print("="*80)
    print("STEP 1: Export DNO Boundaries from BigQuery")
    print("="*80)
    
    cred_path = os.path.expanduser('~/inner-cinema-credentials.json')
    if not os.path.exists(cred_path):
        cred_path = 'inner-cinema-credentials.json'
    
    creds = service_account.Credentials.from_service_account_file(cred_path)
    client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    
    print("\n📥 Querying neso_dno_boundaries...")
    query = f"""
    SELECT 
        dno_code,
        area_name,
        ST_ASGEOJSON(boundary) as geojson
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
    WHERE boundary IS NOT NULL
    ORDER BY dno_code
    """
    
    df = client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} DNO regions")
    
    # Build GeoJSON
    features = []
    for _, row in df.iterrows():
        print(f"   - {row['dno_code']:15s} {row['area_name']}")
        feature = {
            "type": "Feature",
            "properties": {
                "dno_code": row['dno_code'],
                "dno_name": row['area_name']
            },
            "geometry": json.loads(row['geojson'])
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_file = 'dno_boundaries_from_bigquery.geojson'
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"\n✅ Saved to: {output_file}")
    print(f"   Size: {os.path.getsize(output_file) / 1024:.1f} KB")
    
    return output_file

def download_uk_postcodes():
    """Step 2: Download UK postcode district boundaries"""
    print("\n" + "="*80)
    print("STEP 2: Download UK Postcode Districts")
    print("="*80)
    
    print("\n📥 Attempting to download UK postcode districts...")
    
    # Try multiple sources
    sources = [
        {
            'name': 'ONS Postcode Districts (December 2023)',
            'url': 'https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/PCD_DEC_2023_EN_BFC/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson',
            'file': 'uk_postcode_districts.geojson'
        },
        {
            'name': 'Backup: Postcode Districts 2021',
            'url': 'https://opendata.arcgis.com/api/v3/datasets/d419b95860f9417787f0999e7c74dfa3_0/downloads/data?format=geojson&spatialRefId=4326',
            'file': 'uk_postcode_districts_2021.geojson'
        }
    ]
    
    for source in sources:
        try:
            print(f"\n📡 Trying: {source['name']}")
            print(f"   URL: {source['url'][:80]}...")
            
            import urllib.request
            urllib.request.urlretrieve(source['url'], source['file'])
            
            # Verify file
            if os.path.getsize(source['file']) > 1000:
                print(f"✅ Downloaded: {source['file']}")
                print(f"   Size: {os.path.getsize(source['file']) / 1024 / 1024:.1f} MB")
                return source['file']
            else:
                print(f"❌ File too small, trying next source...")
                os.remove(source['file'])
        except Exception as e:
            print(f"❌ Failed: {str(e)[:100]}")
            continue
    
    print("\n⚠️  Automatic download failed")
    print("\n📝 Manual download required:")
    print("   1. Visit: https://geoportal.statistics.gov.uk/")
    print("   2. Search: 'Postcode Districts'")
    print("   3. Download: GeoJSON or Shapefile")
    print("   4. Save as: uk_postcode_districts.geojson (or .shp)")
    print("   5. Place in current directory")
    
    return None

def perform_spatial_join(dno_file, postcode_file):
    """Step 3: Spatial join - which postcode districts are in each DNO?"""
    print("\n" + "="*80)
    print("STEP 3: Spatial Join (DNO → Postcode Districts)")
    print("="*80)
    
    print("\n📥 Loading DNO boundaries...")
    dno_gdf = gpd.read_file(dno_file)
    print(f"   Loaded {len(dno_gdf)} DNO regions")
    print(f"   CRS: {dno_gdf.crs}")
    print(f"   Columns: {list(dno_gdf.columns)}")
    
    print("\n📥 Loading postcode districts...")
    pcd_gdf = gpd.read_file(postcode_file)
    print(f"   Loaded {len(pcd_gdf)} postcode districts")
    print(f"   CRS: {pcd_gdf.crs}")
    print(f"   Columns: {list(pcd_gdf.columns)}")
    
    # Ensure same CRS
    if dno_gdf.crs is None:
        print("\n⚙️  Setting DNO CRS to EPSG:4326 (WGS84)")
        dno_gdf = dno_gdf.set_crs("EPSG:4326")
    
    if pcd_gdf.crs != dno_gdf.crs:
        print(f"\n⚙️  Reprojecting postcodes from {pcd_gdf.crs} to {dno_gdf.crs}")
        pcd_gdf = pcd_gdf.to_crs(dno_gdf.crs)
    
    print("\n🔗 Performing spatial join (this may take 1-2 minutes)...")
    joined = gpd.sjoin(pcd_gdf, dno_gdf, how="left", predicate="intersects")
    
    print(f"✅ Join complete: {len(joined)} rows")
    
    # Identify postcode district column (try common names)
    pcd_col = None
    for col in ['pcd', 'pcds', 'PCD', 'PCDS', 'postcode', 'PostCode', 'pc_district']:
        if col in joined.columns:
            pcd_col = col
            break
    
    if pcd_col is None:
        print(f"\n⚠️  Could not auto-detect postcode column")
        print(f"   Available columns: {list(joined.columns)}")
        pcd_col = input("   Enter postcode district column name: ")
    
    print(f"\n📊 Using columns:")
    print(f"   Postcode: {pcd_col}")
    print(f"   DNO Code: dno_code")
    print(f"   DNO Name: dno_name")
    
    # Extract clean data
    out = joined[[pcd_col, 'dno_code', 'dno_name']].copy()
    out.columns = ['postcode_district', 'dno_id', 'dno_name']
    out = out.drop_duplicates()
    out = out.dropna(subset=['dno_id'])
    
    # Save
    output_csv = 'postcode_district_to_dno_mapping.csv'
    out.to_csv(output_csv, index=False)
    
    print(f"\n✅ Saved mapping to: {output_csv}")
    print(f"   Total mappings: {len(out)}")
    
    # Show summary
    print("\n📊 DNO Coverage:")
    summary = out.groupby(['dno_id', 'dno_name']).size().reset_index(name='postcode_count')
    print(summary.to_string(index=False))
    
    print("\n📋 Sample mappings:")
    print(out.head(10).to_string(index=False))
    
    return output_csv

def main():
    print("🗺️  Complete DNO → Postcode District Mapping Pipeline")
    print("="*80)
    
    # Step 1: Export from BigQuery
    dno_file = export_dno_from_bigquery()
    
    # Step 2: Download postcode districts
    postcode_file = download_uk_postcodes()
    
    if postcode_file is None:
        print("\n❌ Cannot proceed without postcode district file")
        print("   Please download manually and run script again")
        return
    
    # Step 3: Spatial join
    output_csv = perform_spatial_join(dno_file, postcode_file)
    
    print("\n" + "="*80)
    print("✅ COMPLETE!")
    print("="*80)
    print(f"\n📄 Output: {output_csv}")
    print("\n📝 Next steps:")
    print("   1. Import CSV to Google Sheets (new tab: DNO_PCD_MAP)")
    print("   2. Add value column: =IF(B2='Dashboard V3'!$B$10, 1, 0)")
    print("   3. Insert → Chart → Geo Chart")
    print("   4. Region: United Kingdom")
    print("   5. Location: Column A (postcode_district)")
    print("   6. Color: Value column")
    print("\n🎉 You'll have a fully shaded interactive DNO map!")

if __name__ == "__main__":
    main()
