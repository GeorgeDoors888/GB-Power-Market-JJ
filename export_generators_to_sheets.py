#!/usr/bin/env python3
"""
Export SVA Generators to Google Sheets

This script exports the 7,072 SVA generator locations and data
from generators.json to your Google Sheets dashboard.

Creates a new tab: "SVA Generators"

Usage:
    python export_generators_to_sheets.py
"""

import json
import gspread
import pickle
from gspread_formatting import *
from collections import Counter

SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def export_generators_to_sheets():
    """Export SVA generator data to Google Sheets"""
    
    print("🔋 Exporting SVA Generators to Google Sheets")
    print("=" * 60)
    
    # Load generator data
    print("\n📥 Loading generator data...")
    try:
        with open('generators.json', 'r') as f:
            generators = json.load(f)
        print(f"   ✅ Loaded {len(generators):,} generators")
    except FileNotFoundError:
        print("   ❌ generators.json not found")
        print("   Make sure you're in the correct directory")
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
    sheet_name = 'SVA Generators'
    print(f"\n📝 Preparing '{sheet_name}' sheet...")
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        print(f"   Found existing sheet, clearing...")
        sheet.clear()
    except:
        print(f"   Creating new sheet...")
        sheet = spreadsheet.add_worksheet(
            title=sheet_name,
            rows=len(generators) + 100,
            cols=15
        )
    
    # Prepare data
    print("\n🔄 Preparing data...")
    headers = [
        'Plant ID', 'Name', 'DNO', 'DNO Region', 
        'Latitude', 'Longitude', 'Capacity (MW)', 
        'Fuel Type', 'Technology', 'Status',
        'Commissioned Date', 'Postcode', 'Address',
        'Grid Connection', 'Export Limit (MW)'
    ]
    
    data = [headers]
    
    for gen in generators:
        data.append([
            gen.get('plant_id', ''),
            gen.get('name', ''),
            gen.get('dno', ''),
            gen.get('dno_long_name', ''),
            gen.get('lat', ''),
            gen.get('lng', ''),
            gen.get('capacity', ''),
            gen.get('type', ''),
            gen.get('technology', ''),
            gen.get('status', 'Active'),
            gen.get('commissioned', ''),
            gen.get('postcode', ''),
            gen.get('address', ''),
            gen.get('grid_connection', ''),
            gen.get('export_limit', '')
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
            backgroundColor=Color(0.26, 0.47, 0.91),  # Blue
            textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
            horizontalAlignment='CENTER'
        )
        
        format_cell_range(sheet, 'A1:O1', header_format)
        
        # Freeze header row
        set_frozen(sheet, rows=1)
        
        # Auto-resize columns
        sheet.columns_auto_resize(0, 14)
        
        print("   ✅ Formatting applied")
    except Exception as e:
        print(f"   ⚠️  Formatting warning: {e}")
    
    # Success message
    print(f"\n✅ Export Complete!")
    print(f"\n📊 Summary:")
    print(f"   Total Generators: {len(generators):,}")
    print(f"   Sheet: {sheet_name}")
    print(f"   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    
    # Statistics
    print(f"\n📈 Statistics:")
    
    # By DNO
    dno_counts = Counter(g.get('dno', 'Unknown') for g in generators)
    print(f"\n   🏢 Top DNOs:")
    for dno, count in dno_counts.most_common(5):
        print(f"      {dno}: {count:,} generators")
    
    # By fuel type
    fuel_counts = Counter(g.get('type', 'Unknown') for g in generators)
    print(f"\n   ⚡ Top Fuel Types:")
    for fuel, count in fuel_counts.most_common(5):
        print(f"      {fuel}: {count:,} generators")
    
    # Total capacity
    total_capacity = sum(g.get('capacity', 0) for g in generators if isinstance(g.get('capacity'), (int, float)))
    print(f"\n   💪 Total Capacity: {total_capacity:,.0f} MW")
    
    # Geographic spread
    with_coords = [g for g in generators if g.get('lat') and g.get('lng')]
    print(f"\n   📍 With Coordinates: {len(with_coords):,} ({len(with_coords)/len(generators)*100:.1f}%)")
    
    print(f"\n🔗 Next Steps:")
    print(f"   1. Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    print(f"   2. Go to '{sheet_name}' tab")
    print(f"   3. Create pivot tables, charts, filters")
    print(f"   4. Export CVA plants: python export_cva_to_sheets.py")

if __name__ == '__main__':
    export_generators_to_sheets()
