#!/usr/bin/env python3
"""
Export CVA Plants to Google Sheets

This script exports CVA (transmission) plant data
from cva_plants_map.json to your Google Sheets dashboard.

Creates a new tab: "CVA Plants"

Usage:
    python export_cva_to_sheets.py
"""

import json
import gspread
import pickle
from gspread_formatting import *
from collections import Counter

SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def export_cva_to_sheets():
    """Export CVA plant data to Google Sheets"""
    
    print("⚡ Exporting CVA Plants to Google Sheets")
    print("=" * 60)
    
    # Load CVA plant data
    print("\n📥 Loading CVA plant data...")
    try:
        with open('cva_plants_map.json', 'r') as f:
            plants = json.load(f)
        print(f"   ✅ Loaded {len(plants):,} CVA plants")
    except FileNotFoundError:
        print("   ❌ cva_plants_map.json not found")
        print("   Run: python generate_cva_map_json.py first")
        print("   (After scraping completes)")
        return
    
    # Authenticate with Google Sheets (using OAuth token)
    print("\n🔐 Authenticating with Google Sheets...")
    try:
        with open('token.pickle', 'rb') as f:
            creds = pickle.load(f)
        gc = gspread.authorize(creds)
        print("   ✅ Authenticated")
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
        print("   Make sure token.pickle exists")
        return
    
    # Open spreadsheet
    print(f"\n📊 Opening spreadsheet: {SPREADSHEET_ID}")
    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        print(f"   ✅ Opened: {spreadsheet.title}")
    except Exception as e:
        print(f"   ❌ Failed to open spreadsheet: {e}")
        return
    
    # Check if sheet exists, create if not
    sheet_name = 'CVA Plants'
    print(f"\n📝 Preparing '{sheet_name}' sheet...")
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        print(f"   Found existing sheet, clearing...")
        sheet.clear()
    except:
        print(f"   Creating new sheet...")
        sheet = spreadsheet.add_worksheet(
            title=sheet_name,
            rows=len(plants) + 100,
            cols=12
        )
    
    # Prepare data
    print("\n🔄 Preparing data...")
    headers = [
        'Plant ID', 'Name', 'Type', 'Type Category',
        'Latitude', 'Longitude', 'Capacity (MW)', 
        'Fuel Type', 'Status', 'Operator',
        'Source URL', 'Connection Level'
    ]
    
    data = [headers]
    
    for plant in plants:
        data.append([
            plant.get('plant_id', ''),
            plant.get('name', ''),
            'CVA (Transmission)',
            plant.get('type_category', ''),
            plant.get('lat', ''),
            plant.get('lng', ''),
            plant.get('capacity', ''),
            plant.get('fuel_type', ''),
            plant.get('status', ''),
            plant.get('operator', ''),
            plant.get('url', ''),
            'Transmission (400kV/275kV)'
        ])
    
    print(f"   Prepared {len(data)-1:,} rows")
    
    # Write to sheet
    print("\n📝 Writing to Google Sheets...")
    try:
        sheet.update('A1', data, value_input_option='USER_ENTERED')
        print(f"   ✅ Wrote {len(data):,} rows")
    except Exception as e:
        print(f"   ❌ Write failed: {e}")
        return
    
    # Format header
    print("\n🎨 Formatting...")
    try:
        header_format = CellFormat(
            backgroundColor=Color(0.60, 0.22, 0.69),  # Purple (for CVA)
            textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
            horizontalAlignment='CENTER'
        )
        
        format_cell_range(sheet, 'A1:L1', header_format)
        
        # Freeze header row
        set_frozen(sheet, rows=1)
        
        # Auto-resize columns
        sheet.columns_auto_resize(0, 11)
        
        print("   ✅ Formatting applied")
    except Exception as e:
        print(f"   ⚠️  Formatting warning: {e}")
    
    # Success message
    print(f"\n✅ Export Complete!")
    print(f"\n📊 Summary:")
    print(f"   Total CVA Plants: {len(plants):,}")
    print(f"   Sheet: {sheet_name}")
    print(f"   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    
    # Statistics
    print(f"\n📈 Statistics:")
    
    # By type category
    type_counts = Counter(p.get('type_category', 'Unknown') for p in plants)
    print(f"\n   ⚡ By Type Category:")
    for ptype, count in type_counts.most_common(10):
        pct = (count / len(plants)) * 100
        print(f"      {ptype}: {count:,} plants ({pct:.1f}%)")
    
    # By status
    status_counts = Counter(p.get('status', 'Unknown') for p in plants)
    print(f"\n   🔄 By Status:")
    for status, count in status_counts.most_common():
        print(f"      {status}: {count:,} plants")
    
    # Total capacity
    plants_with_capacity = [p for p in plants if p.get('capacity')]
    total_capacity = sum(p.get('capacity', 0) for p in plants_with_capacity)
    avg_capacity = total_capacity / len(plants_with_capacity) if plants_with_capacity else 0
    
    print(f"\n   💪 Capacity:")
    print(f"      Total: {total_capacity:,.0f} MW")
    print(f"      Average: {avg_capacity:.1f} MW per plant")
    print(f"      Plants with data: {len(plants_with_capacity):,}/{len(plants):,}")
    
    # Geographic spread
    with_coords = [p for p in plants if p.get('lat') and p.get('lng')]
    print(f"\n   📍 With Coordinates: {len(with_coords):,} ({len(with_coords)/len(plants)*100:.1f}%)")
    
    print(f"\n🔗 Next Steps:")
    print(f"   1. Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    print(f"   2. Go to '{sheet_name}' tab")
    print(f"   3. Compare with 'SVA Generators' tab")
    print(f"   4. Create combined analysis (CVA + SVA)")

if __name__ == '__main__':
    export_cva_to_sheets()
