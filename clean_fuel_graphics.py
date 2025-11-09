#!/usr/bin/env python3
"""
Clean ALL flags and wrong emojis from fuel types section
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

print("\n🔧 CLEANING FUEL TYPE GRAPHICS...")
print("=" * 70)

# Setup
scope = ['https://spreadsheets.google.com/feeds', 
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

ss = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = ss.worksheet('Dashboard')

# Get all values
all_values = dashboard.get_all_values()

# Find "GENERATION BY FUEL TYPE" section
fuel_section_start = None
fuel_section_end = None

for i, row in enumerate(all_values, 1):
    if any('GENERATION BY FUEL TYPE' in str(cell) for cell in row):
        fuel_section_start = i + 1  # Start after header
        print(f"📍 Found GENERATION BY FUEL TYPE at row {i}")
        break

if fuel_section_start:
    # Fuel section typically goes for about 10-15 rows
    fuel_section_end = fuel_section_start + 15
    
    print(f"📊 Checking rows {fuel_section_start} to {fuel_section_end}")
    
    # Country flag emojis to remove
    flags = ['🇫🇷', '🇧🇪', '🇩🇰', '🇮🇪', '🇳🇴', '🇳🇱']
    
    fixes = []
    
    for row_idx in range(fuel_section_start - 1, min(fuel_section_end, len(all_values))):
        if row_idx < len(all_values) and len(all_values[row_idx]) > 0:
            cell_value = all_values[row_idx][0]
            
            # Skip empty cells or headers
            if not cell_value or 'INTERCONNECTOR' in cell_value.upper():
                continue
            
            # Remove any country flags from fuel types
            new_value = cell_value
            for flag in flags:
                if flag in new_value:
                    new_value = new_value.replace(f' {flag}', '').replace(flag, '')
                    print(f"   Row {row_idx + 1}: Removing {flag}")
            
            # Special fix for Pumped Storage
            if 'Pumped Storage' in new_value:
                # Should be: 💧 Pumped Storage 🔋
                if '⚡' in new_value:
                    new_value = new_value.replace('⚡', '')
                if new_value.strip() == 'Pumped Storage':
                    new_value = '💧 Pumped Storage 🔋'
                elif not new_value.startswith('💧'):
                    new_value = '💧 ' + new_value.strip()
                if '🔋' not in new_value:
                    new_value = new_value + ' 🔋'
            
            # Remove multiple spaces
            new_value = ' '.join(new_value.split())
            
            if new_value != cell_value:
                fixes.append((row_idx + 1, cell_value, new_value))
    
    print(f"\n✅ Found {len(fixes)} cells to clean")
    
    if fixes:
        print("\n📝 Applying fixes:")
        for row_num, old_val, new_val in fixes:
            print(f"   Row {row_num}: '{old_val}' → '{new_val}'")
            dashboard.update_acell(f'A{row_num}', new_val)
        
        print(f"\n✅ Cleaned {len(fixes)} fuel type cells")
    else:
        print("✅ No fixes needed - fuel types are clean")

else:
    print("❌ Could not find GENERATION BY FUEL TYPE section")

print("\n" + "=" * 70)
print("✅ CLEANUP COMPLETE")
print("=" * 70)
