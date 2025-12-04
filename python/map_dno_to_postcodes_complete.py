#!/usr/bin/env python3
"""
Complete DNO → Postcode District Mapping Pipeline

This script:
1. Exports DNO boundaries from BigQuery (already on Dell: dno_boundaries_export.geojson)
2. Downloads UK Postcode District boundaries
3. Performs spatial join to map postcodes → DNOs
4. Outputs CSV ready for Google Sheets GeoChart

Run on Dell machine: ssh george@100.119.237.107
"""

import geopandas as gpd
import pandas as pd
import json
import os
import urllib.request

def download_postcode_districts():
    """Download UK Postcode District boundaries if not already present"""
    
    print("\n📥 Downloading UK Postcode District boundaries...")
    
    # Option 1: Try direct download from a reliable source
    # Using ONS Open Geography API for Postcode Districts
    url = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Postcode_Districts_December_2021_Boundaries_UK_BUC/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
    
    output_file = "uk_postcode_districts.geojson"
    
    if os.path.exists(output_file):
        print(f"   ✅ {output_file} already exists")
        return output_file
    
    try:
        print(f"   Downloading from ONS Open Geography...")
        urllib.request.urlretrieve(url, output_file)
        print(f"   ✅ Downloaded to {output_file}")
        return output_file
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        print("\n📝 Manual download required:")
        print("   1. Visit: https://geoportal.statistics.gov.uk/")
        print("   2. Search: 'Postcode Districts Boundaries'")
        print("   3. Download as GeoJSON or Shapefile")
        print("   4. Save as: uk_postcode_districts.geojson")
        print("   5. Re-run this script")
        return None

def inspect_geojson_fields(filepath):
    """Inspect GeoJSON to show field names"""
    print(f"\n🔍 Inspecting {filepath}...")
    
    gdf = gpd.read_file(filepath)
    
    print(f"   Columns: {list(gdf.columns)}")
    print(f"   CRS: {gdf.crs}")
    print(f"   Rows: {len(gdf)}")
    
    if len(gdf) > 0:
        print(f"\n   Sample row:")
        for col in gdf.columns:
            if col != 'geometry':
                print(f"      {col}: {gdf[col].iloc[0]}")
    
    return gdf

def main():
    print("🗺️  DNO → Postcode District Mapping Pipeline")
    print("="*80)
    
    # -------------------------------------------------------
    # 1. CHECK DNO GEOJSON EXISTS
    # -------------------------------------------------------
    dno_geojson_path = "dno_boundaries_export.geojson"
    
    if not os.path.exists(dno_geojson_path):
        print(f"\n❌ {dno_geojson_path} not found!")
        print("   Run: python3 export_dno_geojson.py first")
        return
    
    # -------------------------------------------------------
    # 2. DOWNLOAD POSTCODE DISTRICTS
    # -------------------------------------------------------
    pcd_path = download_postcode_districts()
    
    if pcd_path is None:
        print("\n❌ Cannot proceed without postcode district data")
        return
    
    # -------------------------------------------------------
    # 3. INSPECT FIELD NAMES
    # -------------------------------------------------------
    print("\n📊 Inspecting DNO GeoJSON fields...")
    dno_gdf = inspect_geojson_fields(dno_geojson_path)
    
    print("\n📊 Inspecting Postcode District fields...")
    pcd_gdf = inspect_geojson_fields(pcd_path)
    
    # -------------------------------------------------------
    # 4. IDENTIFY CORRECT COLUMN NAMES
    # -------------------------------------------------------
    # DNO columns (from export_dno_geojson.py)
    dno_id_column = 'dno_code'
    dno_name_column = 'dno_name'
    
    # Postcode columns (detect automatically)
    # Common names: 'pcds', 'pcd', 'postcode', 'POSTDIST', 'pc_dist'
    postcode_column = None
    for col in pcd_gdf.columns:
        col_lower = col.lower()
        if any(x in col_lower for x in ['pcd', 'postcode', 'post_code', 'postdist']):
            postcode_column = col
            break
    
    if postcode_column is None:
        print("\n❌ Cannot identify postcode district column!")
        print(f"   Available columns: {list(pcd_gdf.columns)}")
        print("   Please manually specify the postcode column")
        return
    
    print(f"\n✅ Column mapping:")
    print(f"   Postcode District: {postcode_column}")
    print(f"   DNO ID: {dno_id_column}")
    print(f"   DNO Name: {dno_name_column}")
    
    # -------------------------------------------------------
    # 5. ENSURE SAME CRS
    # -------------------------------------------------------
    print("\n🔄 Ensuring same coordinate system...")
    
    if dno_gdf.crs is None:
        print("   Setting DNO CRS to EPSG:4326 (WGS84)")
        dno_gdf = dno_gdf.set_crs("EPSG:4326")
    
    print(f"   DNO CRS: {dno_gdf.crs}")
    print(f"   Postcode CRS: {pcd_gdf.crs}")
    
    if pcd_gdf.crs != dno_gdf.crs:
        print(f"   Reprojecting postcodes to {dno_gdf.crs}...")
        pcd_gdf = pcd_gdf.to_crs(dno_gdf.crs)
    
    print("   ✅ CRS aligned")
    
    # -------------------------------------------------------
    # 6. SPATIAL JOIN
    # -------------------------------------------------------
    print("\n🔗 Performing spatial join...")
    print("   This may take a few minutes for ~2,500 postcode districts...")
    
    joined = gpd.sjoin(
        pcd_gdf,
        dno_gdf,
        how="left",
        predicate="intersects"
    )
    
    print(f"   ✅ Join complete: {len(joined)} postcode districts processed")
    
    # -------------------------------------------------------
    # 7. SELECT AND CLEAN FIELDS
    # -------------------------------------------------------
    print("\n🧹 Cleaning data...")
    
    # Select relevant columns
    out = joined[[postcode_column, dno_id_column, dno_name_column]].copy()
    
    # Rename for clarity
    out.columns = ['postcode_district', 'dno_id', 'dno_name']
    
    # Remove duplicates
    out = out.drop_duplicates()
    
    # Remove rows with no DNO assignment
    initial_count = len(out)
    out = out.dropna(subset=['dno_id'])
    dropped = initial_count - len(out)
    
    if dropped > 0:
        print(f"   ⚠️  Dropped {dropped} postcode districts with no DNO match")
    
    # -------------------------------------------------------
    # 8. SAVE CSV
    # -------------------------------------------------------
    output_csv = "postcode_district_to_dno_mapping.csv"
    out.to_csv(output_csv, index=False)
    
    print(f"\n✅ Saved: {output_csv}")
    print(f"   Rows: {len(out)}")
    
    # -------------------------------------------------------
    # 9. SUMMARY STATISTICS
    # -------------------------------------------------------
    print("\n📊 DNO Coverage Summary:")
    summary = out.groupby(['dno_id', 'dno_name']).size().reset_index(name='postcode_count')
    summary = summary.sort_values('postcode_count', ascending=False)
    
    for _, row in summary.iterrows():
        print(f"   {row['dno_id']:15s} {row['dno_name']:40s} {row['postcode_count']:4d} postcodes")
    
    # -------------------------------------------------------
    # 10. SAMPLE OUTPUT
    # -------------------------------------------------------
    print(f"\n📋 Sample output (first 10 rows):")
    print(out.head(10).to_string(index=False))
    
    print(f"\n✅ COMPLETE!")
    print(f"\n📝 Next steps:")
    print(f"   1. Download {output_csv} from Dell machine")
    print(f"   2. Import to Google Sheets (new tab 'DNO_PCD_MAP')")
    print(f"   3. Add value column: =IF(B2='Dashboard V3'!$B$10, 1, 0)")
    print(f"   4. Insert → Chart → Geo chart → Region: United Kingdom")
    print(f"   5. Location: postcode_district (column A)")
    print(f"   6. Color: value (column D)")
    print(f"\n📄 Full instructions: DNO_GEOCHART_MAPPING_GUIDE.md")

if __name__ == "__main__":
    main()
