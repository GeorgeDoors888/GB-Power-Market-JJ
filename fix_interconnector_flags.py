#!/usr/bin/env python3
"""
Fix Interconnector Flag Placement
Moves country flags to the LEFT of interconnector names (before name, not after)
Format: "🇫🇷 IFA (France)" not "⚡ IFA (France) 🇫"
"""

import gspread
from google.oauth2.service_account import Credentials

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

# Interconnector formatting: FLAG on LEFT, no emoji on right
INTERCONNECTOR_FORMATS = {
    'NSL (Norway)': '🇳🇴 NSL (Norway)',
    'IFA (France)': '🇫🇷 IFA (France)',
    'IFA2 (France)': '🇫🇷 IFA2 (France)',
    'ElecLink (France)': '🇫🇷 ElecLink (France)',
    'Nemo (Belgium)': '🇧🇪 Nemo (Belgium)',
    'Viking Link (Denmark)': '🇩🇰 Viking Link (Denmark)',
    'BritNed (Netherlands)': '🇳🇱 BritNed (Netherlands)',
    'Moyle (N.Ireland)': '🇮🇪 Moyle (N.Ireland)',
    'East-West (Ireland)': '🇮🇪 East-West (Ireland)',
    'Greenlink (Ireland)': '🇮🇪 Greenlink (Ireland)'
}

def main():
    print("🔧 Fixing Interconnector Flag Placement...")
    
    # Authenticate
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open spreadsheet
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Dashboard')
    
    # Get all values (to find interconnector cells)
    all_values = sheet.get_all_values()
    
    updates = []
    fixed_count = 0
    
    # Search for interconnector cells (they contain the keywords)
    for row_idx, row in enumerate(all_values, start=1):
        for col_idx, cell_value in enumerate(row, start=1):
            # Check if this cell contains an interconnector name
            for old_name, new_format in INTERCONNECTOR_FORMATS.items():
                # Match various formats (with or without emoji)
                if old_name in cell_value or new_format in cell_value:
                    # Only update if not already in correct format
                    if cell_value != new_format:
                        cell_notation = gspread.utils.rowcol_to_a1(row_idx, col_idx)
                        updates.append({
                            'range': cell_notation,
                            'values': [[new_format]]
                        })
                        print(f"  {cell_notation}: '{cell_value}' → '{new_format}'")
                        fixed_count += 1
                    break
    
    # Apply updates in batch
    if updates:
        sheet.batch_update(updates, value_input_option='USER_ENTERED')
        print(f"\n✅ Fixed {fixed_count} interconnector cells")
        print(f"   Format: FLAG on LEFT (e.g., '🇫🇷 IFA (France)')")
    else:
        print("✅ All interconnector flags already correctly positioned")

if __name__ == '__main__':
    main()
