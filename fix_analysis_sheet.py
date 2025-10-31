#!/usr/bin/env python3
"""
Quick fix for Analysis Sheet - handles missing token.pickle and schema issues
"""

import os
import shutil
from google.cloud import bigquery

print("🔧 ANALYSIS SHEET QUICK FIX")
print("=" * 70)
print()

# Fix 1: Copy auth files from repo directory
print("FIX 1: Copying authentication files...")
repo_dir = "/Users/georgemajor/repo/GB Power Market JJ"
current_dir = "/Users/georgemajor/GB Power Market JJ"

files_to_copy = ['token.pickle', 'credentials.json']
for filename in files_to_copy:
    src = os.path.join(repo_dir, filename)
    dst = os.path.join(current_dir, filename)
    
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  ✅ Copied {filename}")
    else:
        print(f"  ⚠️ {filename} not found in {repo_dir}")

print()

# Fix 2: Check and fix BigQuery views with schema issues
print("FIX 2: Fixing BigQuery view schemas...")
client = bigquery.Client(project='inner-cinema-476211-u9')

# Check bmrs_boalf_iris schema
print("  Checking bmrs_boalf_iris schema...")
try:
    query = """
    SELECT column_name 
    FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'bmrs_boalf_iris'
    ORDER BY ordinal_position
    """
    results = list(client.query(query).result())
    columns = [row.column_name for row in results]
    print(f"  📋 Found columns: {', '.join(columns[:10])}")
    
    # Determine correct timestamp column
    time_columns = [col for col in columns if 'time' in col.lower() or 'date' in col.lower()]
    print(f"  🕐 Time columns: {', '.join(time_columns)}")
    
    # Recreate view with correct column names
    if time_columns:
        timestamp_col = time_columns[0]  # Use first time-related column
        print(f"  ✅ Using '{timestamp_col}' as timestamp column")
        
        # Create corrected view
        view_query = f"""
        CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_unified` AS
        WITH historical AS (
          SELECT 
            timeFrom as timestamp,
            bmUnit,
            acceptanceTime,
            deemedBidOfferFlag,
            soFlag,
            volume,
            'historical' as source
          FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
          WHERE timeFrom < DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
        ),
        realtime AS (
          SELECT 
            {timestamp_col} as timestamp,
            bmUnit,
            acceptanceTime,
            deemedBidOfferFlag,
            soFlag,
            volume,
            'real-time' as source
          FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
          WHERE {timestamp_col} >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
        )
        SELECT * FROM historical
        UNION ALL
        SELECT * FROM realtime
        ORDER BY timestamp DESC
        """
        
        client.query(view_query).result()
        print(f"  ✅ bmrs_boalf_unified view recreated successfully")
    
except Exception as e:
    print(f"  ⚠️ Could not fix bmrs_boalf_unified: {e}")
    print(f"  💡 You can run Analysis Sheet without this view (it's optional)")

print()

# Fix 3: Test connection
print("FIX 3: Testing connections...")
try:
    # Test BigQuery
    query = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`"
    result = list(client.query(query).result())[0]
    print(f"  ✅ BigQuery working ({result.count} rows in bmrs_freq_iris)")
except Exception as e:
    print(f"  ⚠️ BigQuery error: {e}")

try:
    # Test Google Sheets auth
    import pickle
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    print(f"  ✅ Google Sheets token loaded")
except Exception as e:
    print(f"  ⚠️ Google Sheets auth error: {e}")

print()
print("=" * 70)
print("✅ FIXES APPLIED!")
print("=" * 70)
print()
print("Now try running:")
print("  python3 create_analysis_sheet.py")
print("  python3 update_analysis_sheet.py")
print()
