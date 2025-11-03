#!/usr/bin/env python3
"""
Download BMU data from NESO (National Energy System Operator)
They publish BMU registration data publicly
"""

import requests
import pandas as pd
import json

def try_neso_download():
    """Try to download BMU data from NESO/ESO website"""
    
    print("🔍 Downloading CVA/BMU data from NESO...\n")
    print("="*90)
    
    # NESO publishes BMU data as CSV
    # https://data.nationalgrideso.com/
    
    urls = [
        # Try BMU Fuel Type
        "https://data.nationalgrideso.com/backend/dataset/2810092e-d4b2-472f-b955-d8ae59499f1c/resource/ae0d835e-28f7-4651-a12f-a5f2f2d89043/download/bmu-fuel-type.csv",
        # Try Registered BMUs
        "https://data.nationalgrideso.com/backend/dataset/2810092e-d4b2-472f-b955-d8ae59499f1c/resource/f7c876eb-f662-4de0-83da-6f74ca5b0e84/download/registered-bmus.csv",
    ]
    
    for url in urls:
        print(f"\n📥 Trying: {url}")
        try:
            response = requests.get(url, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   Size: {len(response.content) / 1024:.1f} KB")
                
                # Parse as CSV
                df = pd.read_csv(pd.io.common.StringIO(response.text))
                print(f"   ✅ Successfully parsed!")
                print(f"   Rows: {len(df):,}")
                print(f"   Columns: {len(df.columns)}")
                print(f"\n   Column names:")
                for i, col in enumerate(df.columns, 1):
                    print(f"      {i}. {col}")
                
                # Show sample
                print(f"\n   Sample data (first 5 rows):")
                print(df.head().to_string())
                
                return df, url
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None, None

if __name__ == '__main__':
    df, url = try_neso_download()
    
    if df is not None:
        # Save it
        filename = 'neso_bmu_data.csv'
        df.to_csv(filename, index=False)
        print(f"\n✅ Saved {len(df):,} BMUs to {filename}")
        print(f"\n📊 Data source: {url}")
    else:
        print("\n❌ Could not download BMU data")
        print("\n💡 Alternative: Check https://data.nationalgrideso.com/ manually")
