#!/usr/bin/env python3
"""
Verify Dashboard Interconnector Flags
Ensures all 10 interconnector flags are correctly displayed
Run after any dashboard update script changes
"""

import pickle
from googleapiclient.discovery import build

SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

# Expected flags in order (rows 8-17)
REQUIRED_FLAGS = [
    ('🇫🇷', 'ElecLink (France)'),
    ('🇮🇪', 'East-West (Ireland)'),
    ('🇫🇷', 'IFA (France)'),
    ('🇮🇪', 'Greenlink (Ireland)'),
    ('🇫🇷', 'IFA2 (France)'),
    ('🇮🇪', 'Moyle (N.Ireland)'),
    ('🇳🇱', 'BritNed (Netherlands)'),
    ('🇧🇪', 'Nemo (Belgium)'),
    ('🇳🇴', 'NSL (Norway)'),
    ('🇩🇰', 'Viking Link (Denmark)')
]

def main():
    print("🔍 Verifying Dashboard interconnector flags...")
    print("=" * 70)
    
    # Load credentials
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    
    sheets = build('sheets', 'v4', credentials=creds)
    
    # Read interconnector section
    result = sheets.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Dashboard!D8:D17'
    ).execute()
    
    values = result.get('values', [])
    
    if not values or len(values) != 10:
        print(f"❌ ERROR: Expected 10 interconnectors, found {len(values)}")
        return False
    
    all_correct = True
    
    for i, ((expected_flag, expected_name), row) in enumerate(zip(REQUIRED_FLAGS, values), 8):
        actual = row[0] if row else ''
        
        # Check if flag is present
        if not actual.startswith(expected_flag):
            print(f"❌ Row {i}: Missing {expected_flag}")
            print(f"   Expected: {expected_flag} {expected_name}")
            print(f"   Got: {actual}")
            all_correct = False
        else:
            # Verify full content
            print(f"✅ Row {i}: {actual}")
    
    print("=" * 70)
    
    if all_correct:
        print("✅ ALL INTERCONNECTOR FLAGS VERIFIED CORRECT!")
        return True
    else:
        print("❌ FLAG VERIFICATION FAILED!")
        print("\n🔧 To fix:")
        print("   1. Check update_dashboard_preserve_layout.py flag_map")
        print("   2. Run: python3 update_dashboard_preserve_layout.py")
        print("   3. Verify flags appear in Dashboard")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
