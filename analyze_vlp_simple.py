#!/usr/bin/env python3
"""
Analyze REMIT Assets and Battery BMUs for Virtual Lead Parties
Simplified version that works with the actual API responses
"""

import requests
import json
import pandas as pd
from datetime import datetime
import os

# Configuration
BMRS_API = 'https://data.elexon.co.uk/bmrs/api/v1'

# VLP keywords
VLP_KEYWORDS = ['virtual', 'aggregat', 'portfolio', 'vlp', 'multi', 'flex']

def download_remit_assets():
    """Download REMIT asset registry"""
    print("📥 Downloading REMIT assets...")
    
    url = f"{BMRS_API}/reference/remit/assets/all"
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        assets = response.json()
        
        print(f"✅ Downloaded {len(assets)} REMIT assets")
        return assets
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def download_remit_participants():
    """Download REMIT participants"""
    print("📥 Downloading REMIT participants...")
    
    url = f"{BMRS_API}/reference/remit/participants/all"
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        participants = response.json()
        
        print(f"✅ Downloaded {len(participants)} REMIT participants")
        return participants
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def analyze_assets_for_vlps(assets):
    """Identify potential VLPs from asset data"""
    print(f"\n🔍 Analyzing {len(assets)} assets for VLP patterns...")
    
    vlp_records = []
    
    for asset in assets:
        asset_name = str(asset.get('assetName', '')).lower()
        
        # Check for VLP keywords
        matched_keywords = [kw for kw in VLP_KEYWORDS if kw in asset_name]
        
        if matched_keywords:
            vlp_records.append({
                'asset_id': asset.get('assetId', ''),
                'asset_name': asset.get('assetName', ''),
                'eic_code': asset.get('eicCode', ''),
                'fuel_type': asset.get('fuelType', ''),
                'matched_keywords': ', '.join(matched_keywords),
                'asset_type': asset.get('assetType', '')
            })
    
    df = pd.DataFrame(vlp_records)
    print(f"✅ Found {len(df)} potential VLPs based on name patterns")
    
    return df

def analyze_battery_assets(assets):
    """Identify battery storage assets from REMIT data"""
    print(f"\n🔋 Analyzing assets for battery storage...")
    
    battery_keywords = ['bess', 'battery', 'stor', 'energy storage', 'btry']
    battery_records = []
    
    for asset in assets:
        asset_name = str(asset.get('assetName', '')).lower()
        fuel_type = str(asset.get('fuelType', '')).lower()
        
        # Check for battery indicators
        is_battery = (
            any(kw in asset_name for kw in battery_keywords) or
            'other' in fuel_type or
            'storage' in fuel_type
        )
        
        if is_battery:
            matched = [kw for kw in battery_keywords if kw in asset_name]
            battery_records.append({
                'asset_id': asset.get('assetId', ''),
                'asset_name': asset.get('assetName', ''),
                'eic_code': asset.get('eicCode', ''),
                'fuel_type': asset.get('fuelType', ''),
                'matched_keywords': ', '.join(matched) if matched else 'fuel_type',
                'asset_type': asset.get('assetType', '')
            })
    
    df = pd.DataFrame(battery_records)
    print(f"✅ Found {len(df)} battery storage assets")
    
    return df

def find_vlp_batteries(vlp_df, battery_df):
    """Find assets that are both VLPs and batteries"""
    print("\n🔗 Finding VLP battery assets...")
    
    if len(vlp_df) == 0 or len(battery_df) == 0:
        print("⚠️ No VLPs or batteries to compare")
        return pd.DataFrame()
    
    # Merge to find overlap
    vlp_batteries = pd.merge(
        vlp_df, 
        battery_df,
        on='asset_id',
        suffixes=('_vlp', '_battery'),
        how='inner'
    )
    
    print(f"✅ Found {len(vlp_batteries)} assets that are both VLP and battery")
    
    return vlp_batteries

def export_results(vlp_df, battery_df, vlp_batteries, assets, participants):
    """Export all results to CSV files"""
    print("\n💾 Exporting results...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Export VLPs
    if len(vlp_df) > 0:
        file = f'vlp_assets_{timestamp}.csv'
        vlp_df.to_csv(file, index=False)
        print(f"   ✅ Exported: {file}")
    
    # Export Batteries
    if len(battery_df) > 0:
        file = f'battery_assets_{timestamp}.csv'
        battery_df.to_csv(file, index=False)
        print(f"   ✅ Exported: {file}")
    
    # Export VLP Batteries
    if len(vlp_batteries) > 0:
        file = f'vlp_battery_assets_{timestamp}.csv'
        vlp_batteries.to_csv(file, index=False)
        print(f"   ✅ Exported: {file}")
    
    # Export all assets
    if len(assets) > 0:
        file = f'all_remit_assets_{timestamp}.csv'
        pd.DataFrame(assets).to_csv(file, index=False)
        print(f"   ✅ Exported: {file}")
    
    # Export participants
    if len(participants) > 0:
        file = f'remit_participants_{timestamp}.csv'
        pd.DataFrame(participants).to_csv(file, index=False)
        print(f"   ✅ Exported: {file}")

def generate_report(vlp_df, battery_df, vlp_batteries, assets):
    """Generate summary report"""
    print("\n" + "="*80)
    print("📊 VLP & BATTERY ANALYSIS REPORT")
    print("="*80)
    
    print(f"\n📅 Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "-"*80)
    print("📋 REMIT ASSET SUMMARY")
    print("-"*80)
    print(f"Total REMIT assets: {len(assets)}")
    
    # Count by fuel type
    if len(assets) > 0:
        fuel_counts = pd.DataFrame(assets)['fuelType'].value_counts()
        print(f"\nTop 10 Fuel Types:")
        print(fuel_counts.head(10))
    
    print("\n" + "-"*80)
    print("🏢 VIRTUAL LEAD PARTY (VLP) ANALYSIS")
    print("-"*80)
    print(f"Total VLPs identified: {len(vlp_df)}")
    
    if len(vlp_df) > 0:
        print(f"\nVLPs by keyword:")
        keyword_counts = vlp_df['matched_keywords'].value_counts()
        print(keyword_counts.head(10))
        
        print(f"\n🔝 Top 20 VLPs:")
        print(vlp_df[['asset_name', 'fuel_type', 'matched_keywords']].head(20).to_string(index=False))
    
    print("\n" + "-"*80)
    print("🔋 BATTERY STORAGE ANALYSIS")
    print("-"*80)
    print(f"Total battery assets identified: {len(battery_df)}")
    
    if len(battery_df) > 0:
        print(f"\n🔝 Top 20 Battery Assets:")
        print(battery_df[['asset_name', 'fuel_type', 'matched_keywords']].head(20).to_string(index=False))
    
    print("\n" + "-"*80)
    print("⚡ VLP BATTERY STORAGE (Overlap)")
    print("-"*80)
    print(f"Assets that are BOTH VLP and Battery: {len(vlp_batteries)}")
    
    if len(vlp_batteries) > 0:
        print(f"\n🎯 VLP Battery Assets:")
        print(vlp_batteries[['asset_name_vlp', 'fuel_type_vlp']].to_string(index=False))
    
    print("\n" + "="*80)

def main():
    """Main execution"""
    print("🚀 VLP & Battery Asset Analysis")
    print("="*80)
    
    # Step 1: Download data
    print("\n📥 STEP 1: Download REMIT Data")
    print("-"*80)
    assets = download_remit_assets()
    participants = download_remit_participants()
    
    if len(assets) == 0:
        print("❌ No assets downloaded. Exiting.")
        return
    
    # Step 2: Analyze for VLPs
    print("\n🔍 STEP 2: Identify VLPs")
    print("-"*80)
    vlp_df = analyze_assets_for_vlps(assets)
    
    # Step 3: Analyze for batteries
    print("\n🔋 STEP 3: Identify Battery Assets")
    print("-"*80)
    battery_df = analyze_battery_assets(assets)
    
    # Step 4: Find overlap
    print("\n🔗 STEP 4: Find VLP Batteries")
    print("-"*80)
    vlp_batteries = find_vlp_batteries(vlp_df, battery_df)
    
    # Step 5: Export
    print("\n💾 STEP 5: Export Results")
    print("-"*80)
    export_results(vlp_df, battery_df, vlp_batteries, assets, participants)
    
    # Step 6: Report
    print("\n📊 STEP 6: Generate Report")
    print("-"*80)
    generate_report(vlp_df, battery_df, vlp_batteries, assets)
    
    print("\n✅ Analysis Complete!")
    print("="*80)
    
    return vlp_df, battery_df, vlp_batteries

if __name__ == '__main__':
    vlp_results, battery_results, vlp_battery_results = main()
