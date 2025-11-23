#!/usr/bin/env python3
"""
Import DNO Generation Data (Sites > 1 MW)
Focuses on ENWL and NGED distributed generation registers
"""

import os
import pandas as pd
import requests
from google.cloud import bigquery
from datetime import datetime
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "dno_generation_sites"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'


# Known NGED data sources (manual downloads)
NGED_DATA_SOURCES = {
    "West Midlands": "https://www.nationalgrid.co.uk/downloads-view-reciteme/530531",
    "East Midlands": "https://www.nationalgrid.co.uk/downloads-view-reciteme/530526",
    "South West": "https://www.nationalgrid.co.uk/downloads-view-reciteme/530536",
    "South Wales": "https://www.nationalgrid.co.uk/downloads-view-reciteme/530534"
}


def fetch_enwl_api_data():
    """
    Try to fetch ENWL generation data from OpenDataSoft API
    Note: May not have generation register publicly available
    """
    print("\n" + "="*80)
    print("ELECTRICITY NORTH WEST (ENWL)")
    print("="*80)
    
    base_url = "https://electricitynorthwest.opendatasoft.com/api/explore/v2.1/catalog/datasets"
    
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            print(f"❌ API not accessible (HTTP {response.status_code})")
            return pd.DataFrame()
        
        data = response.json()
        print(f"✅ Found {data['total_count']} datasets")
        
        # Look for generation/capacity datasets
        generation_datasets = []
        for ds in data['results']:
            ds_id = ds['dataset_id'].lower()
            title = ds.get('metas', {}).get('default', {}).get('title', '').lower()
            
            if any(kw in ds_id or kw in title for kw in [
                'generation', 'distributed', 'embedded', 'capacity', 
                'constraint', 'available', 'generator'
            ]):
                generation_datasets.append(ds['dataset_id'])
        
        if not generation_datasets:
            print("⚠️  No generation datasets found in API")
            print("   ENWL may require manual data download from:")
            print("   https://www.enwl.co.uk/zero-carbon/innovation/open-data/")
            return pd.DataFrame()
        
        # Try to fetch from found datasets
        all_data = []
        for ds_id in generation_datasets:
            print(f"\n📥 Checking dataset: {ds_id}")
            rec_url = f"{base_url}/{ds_id}/records?limit=1000"
            
            try:
                rec_resp = requests.get(rec_url, timeout=10)
                if rec_resp.status_code == 200:
                    rec_data = rec_resp.json()
                    total = rec_data.get('total_count', 0)
                    print(f"   Records: {total:,}")
                    
                    if total > 0:
                        # Convert to DataFrame
                        records = rec_data['results']
                        df = pd.json_normalize(records)
                        all_data.append(df)
            except Exception as e:
                print(f"   Error: {e}")
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            print(f"\n✅ Fetched {len(combined)} total records")
            return combined
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return pd.DataFrame()


def create_sample_nged_data():
    """
    Create sample NGED generation data structure
    In production, this would parse downloaded CSV/Excel files
    """
    print("\n" + "="*80)
    print("NATIONAL GRID ELECTRICITY DISTRIBUTION (NGED)")
    print("="*80)
    print("\n⚠️  NGED data requires manual download from:")
    print("   https://connecteddata.nationalgrid.co.uk/")
    print("\nTo import NGED data:")
    print("   1. Download 'Generation Availability' CSV files")
    print("   2. Place in ./nged_data/ directory")
    print("   3. Run this script with --nged-import flag")
    
    # For now, return empty DataFrame with expected schema
    return pd.DataFrame(columns=[
        'dno', 'site_name', 'capacity_mw', 'technology', 
        'connection_voltage', 'gsp_group', 'substation', 
        'status', 'connection_date', 'latitude', 'longitude'
    ])


def import_nged_csv_files(directory='./nged_data/'):
    """
    Import NGED generation CSV files from directory
    """
    import glob
    
    if not os.path.exists(directory):
        print(f"⚠️  Directory not found: {directory}")
        print("   Please create it and add NGED CSV files")
        return pd.DataFrame()
    
    csv_files = glob.glob(f"{directory}/*.csv")
    
    if not csv_files:
        print(f"⚠️  No CSV files found in {directory}")
        return pd.DataFrame()
    
    print(f"\n📁 Found {len(csv_files)} CSV files:")
    
    all_data = []
    for csv_file in csv_files:
        print(f"   • {os.path.basename(csv_file)}")
        
        try:
            df = pd.read_csv(csv_file)
            
            # Standardize column names (NGED uses various formats)
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # Add DNO identifier
            df['dno'] = 'NGED'
            
            # Try to identify capacity column
            capacity_cols = [c for c in df.columns if 'capacity' in c or 'mw' in c or 'mva' in c]
            if capacity_cols:
                # Rename to standard name
                df['capacity_mw'] = df[capacity_cols[0]]
            
            all_data.append(df)
            
        except Exception as e:
            print(f"      ❌ Error reading file: {e}")
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        print(f"\n✅ Loaded {len(combined)} total sites from NGED")
        return combined
    
    return pd.DataFrame()


def filter_large_sites(df, min_capacity_mw=1.0):
    """Filter for sites >= minimum capacity"""
    
    if df.empty:
        return df
    
    # Find capacity column
    capacity_col = None
    for col in df.columns:
        if 'capacity' in col.lower() or col.lower().endswith('mw'):
            capacity_col = col
            break
    
    if not capacity_col:
        print("⚠️  No capacity column found, cannot filter by size")
        return df
    
    # Filter
    original_count = len(df)
    df_filtered = df[df[capacity_col] >= min_capacity_mw].copy()
    
    print(f"\n🔍 Filtering sites >= {min_capacity_mw} MW:")
    print(f"   Before: {original_count:,} sites")
    print(f"   After:  {len(df_filtered):,} sites (>= {min_capacity_mw} MW)")
    print(f"   Removed: {original_count - len(df_filtered):,} small sites")
    
    return df_filtered


def standardize_schema(df, dno_name):
    """Standardize DNO data to common schema"""
    
    if df.empty:
        return df
    
    # Map common column variations to standard names
    column_mapping = {
        # Capacity
        'capacity': 'capacity_mw',
        'capacity_mva': 'capacity_mw',
        'installed_capacity': 'capacity_mw',
        'generation_capacity': 'capacity_mw',
        'registered_capacity': 'capacity_mw',
        
        # Technology
        'technology': 'technology',
        'fuel_type': 'technology',
        'generation_type': 'technology',
        'type': 'technology',
        
        # Location
        'site': 'site_name',
        'site_name': 'site_name',
        'generator_name': 'site_name',
        'name': 'site_name',
        
        # Connection
        'voltage': 'connection_voltage_kv',
        'connection_voltage': 'connection_voltage_kv',
        'voltage_level': 'connection_voltage_kv',
    }
    
    # Rename columns
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Add DNO field if not present
    if 'dno' not in df.columns:
        df['dno'] = dno_name
    
    # Add metadata
    df['_uploaded_at'] = datetime.utcnow()
    df['_source'] = f'{dno_name} Generation Register'
    
    return df


def upload_to_bigquery(df):
    """Upload DNO generation sites to BigQuery"""
    
    if df.empty:
        print("\n⚠️  No data to upload")
        return
    
    client = bigquery.Client(project=PROJECT_ID, location='US')
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    
    print(f"\n📤 Uploading {len(df)} sites to BigQuery...")
    print(f"   Table: {table_id}")
    
    # Configure job
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace existing
        autodetect=True  # Auto-detect schema
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait
        
        print(f"✅ Upload complete!")
        
        # Summary stats
        if 'capacity_mw' in df.columns:
            total_capacity = df['capacity_mw'].sum()
            print(f"   Total capacity: {total_capacity:,.1f} MW")
        
        if 'technology' in df.columns:
            print(f"\n   By technology:")
            tech_summary = df.groupby('technology')['capacity_mw'].sum().sort_values(ascending=False)
            for tech, cap in tech_summary.head(10).items():
                print(f"      {tech}: {cap:,.1f} MW")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")


def main():
    print("="*80)
    print("DNO GENERATION DATA IMPORT (Sites >= 1 MW)")
    print("="*80)
    
    all_data = []
    
    # Try ENWL API
    enwl_data = fetch_enwl_api_data()
    if not enwl_data.empty:
        enwl_data = standardize_schema(enwl_data, 'ENWL')
        enwl_data = filter_large_sites(enwl_data, min_capacity_mw=1.0)
        all_data.append(enwl_data)
    
    # Try NGED CSV import
    nged_data = import_nged_csv_files('./nged_data/')
    if not nged_data.empty:
        nged_data = standardize_schema(nged_data, 'NGED')
        nged_data = filter_large_sites(nged_data, min_capacity_mw=1.0)
        all_data.append(nged_data)
    else:
        # Show instructions for manual download
        create_sample_nged_data()
    
    # Combine all DNO data
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        
        print("\n" + "="*80)
        print("COMBINED DATA SUMMARY")
        print("="*80)
        print(f"Total sites: {len(combined):,}")
        
        if 'dno' in combined.columns:
            print(f"\nBy DNO:")
            for dno, group in combined.groupby('dno'):
                cap = group['capacity_mw'].sum() if 'capacity_mw' in group.columns else 0
                print(f"   {dno}: {len(group):,} sites, {cap:,.1f} MW")
        
        # Upload to BigQuery
        response = input("\n📤 Upload to BigQuery? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            upload_to_bigquery(combined)
            
            # Save backup
            backup_file = f"dno_generation_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            combined.to_csv(backup_file, index=False)
            print(f"💾 Backup saved: {backup_file}")
    else:
        print("\n⚠️  No data collected")
        print("\n📋 MANUAL DATA COLLECTION REQUIRED:")
        print("\n1. ENWL (Electricity North West):")
        print("   https://www.enwl.co.uk/zero-carbon/innovation/open-data/")
        print("   Download: 'Distributed Generation Register'")
        print("\n2. NGED (National Grid ED):")
        print("   https://connecteddata.nationalgrid.co.uk/")
        print("   Download: 'Generation Availability' for each region")
        print("   - West Midlands")
        print("   - East Midlands")
        print("   - South West")
        print("   - South Wales")
        print("\n3. Place CSV files in ./nged_data/ directory")
        print("4. Re-run this script")


if __name__ == "__main__":
    main()
