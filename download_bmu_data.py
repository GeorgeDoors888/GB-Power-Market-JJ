#!/usr/bin/env python3
"""
Download CVA site data from Elexon
BMU (Balancing Mechanism Unit) registration data
"""

import requests
import pandas as pd
import json

# Elexon provides BMU data files
# Try different endpoints

def download_bmu_data():
    """Download BMU registration data from Elexon"""
    
    print("🔍 Attempting to download CVA/BMU data from Elexon...\n")
    print("="*90)
    
    # Try the Data Portal CSV download
    # https://www.elexonportal.co.uk/article/view/46?cachebust=dymqb86z9f
    
    urls_to_try = [
        # BMU Reference Data
        "https://downloads.elexonportal.co.uk/file/download/BMUNITS_FILE?key=ju89x1a0fl",
        "https://downloads.elexonportal.co.uk/bmunit",
        "https://bm unit.elexonportal.co.uk/",
        # Try BMRS API
        "https://api.bmreports.com/BMRS/BMUNITSEARCH/v1?APIKey=b83b66er7kfpq9i",
    ]
    
    for url in urls_to_try:
        print(f"\n📥 Trying: {url}")
        try:
            response = requests.get(url, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   Size: {len(response.content)} bytes")
                
                # Try to parse as CSV
                try:
                    df = pd.read_csv(pd.io.common.StringIO(response.text))
                    print(f"   ✅ Successfully parsed as CSV!")
                    print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
                    print(f"   Columns: {list(df.columns[:10])}")
                    return df
                except Exception as e:
                    print(f"   ⚠️  Not CSV: {e}")
                
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(f"   ✅ Successfully parsed as JSON!")
                    print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                    return data
                except Exception as e:
                    print(f"   ⚠️  Not JSON: {e}")
                
                # Show first 500 chars
                print(f"\n   Preview:")
                print(response.text[:500])
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ Could not download from any URL")
    return None

if __name__ == '__main__':
    data = download_bmu_data()
    
    if data is not None:
        # Save it
        if isinstance(data, pd.DataFrame):
            data.to_csv('bmu_registration_data.csv', index=False)
            print(f"\n✅ Saved to bmu_registration_data.csv")
        else:
            with open('bmu_registration_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n✅ Saved to bmu_registration_data.json")
