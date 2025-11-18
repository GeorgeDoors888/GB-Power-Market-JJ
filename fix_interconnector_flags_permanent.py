#!/usr/bin/env python3
"""
Fix Interconnector Flags - Permanent Solution
==============================================

Restores complete country flag emojis to interconnector names.

The issue: Google Sheets sometimes corrupts multi-byte emoji characters
when using USER_ENTERED mode or when data is modified externally.

Solution: Always write interconnector names with RAW mode and complete flags.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import sys

# Configuration
SERVICE_ACCOUNT_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Complete flag mappings (2-character Unicode flags)
FLAG_MAP = {
    'ElecLink': '🇫🇷',
    'IFA': '🇫🇷', 
    'IFA2': '🇫🇷',
    'East-West': '🇮🇪',
    'Greenlink': '🇮🇪',
    'Moyle': '🇮🇪',
    'BritNed': '🇳🇱',
    'Nemo': '🇧🇪',
    'NSL': '🇳🇴',
    'Viking': '🇩🇰'
}

def fix_flags():
    """Fix broken interconnector flags"""
    
    # Authenticate
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=creds)
    sheets = service.spreadsheets()
    
    print("\n🔧 FIXING INTERCONNECTOR FLAGS...")
    print("=" * 70)
    
    # Read current interconnector data (column D, rows 8-17)
    result = sheets.values().get(
        spreadsheetId=SHEET_ID,
        range='Dashboard!D8:E17'
    ).execute()
    
    current_data = result.get('values', [])
    
    if not current_data:
        print("❌ No interconnector data found!")
        return False
    
    # Build fixed data
    fixed_data = []
    
    for i, row in enumerate(current_data, start=8):
        if not row or len(row) == 0:
            continue
            
        ic_name = row[0]
        ic_flow = row[1] if len(row) > 1 else ''
        
        # Strip ALL existing emoji characters (including broken ones)
        clean_name = ic_name
        for char in ic_name:
            if ord(char) > 127000:  # Unicode emoji range
                clean_name = clean_name.replace(char, '')
        
        clean_name = clean_name.strip()
        
        # Find matching flag and add complete emoji
        flag_added = False
        for key, flag in FLAG_MAP.items():
            if key in clean_name:
                fixed_name = f"{flag} {clean_name}"
                fixed_data.append([fixed_name, ic_flow])
                print(f"Row {i}: ✅ Fixed - {fixed_name}")
                flag_added = True
                break
        
        if not flag_added:
            # Fallback: keep original name
            fixed_data.append([clean_name, ic_flow])
            print(f"Row {i}: ⚠️ No match - {clean_name}")
    
    # Write fixed data using RAW mode (critical for emoji preservation)
    print("\n📝 Writing fixed data with RAW mode...")
    
    sheets.values().update(
        spreadsheetId=SHEET_ID,
        range='Dashboard!D8:E17',
        valueInputOption='RAW',  # CRITICAL: Preserves emoji encoding
        body={'values': fixed_data}
    ).execute()
    
    print("\n" + "=" * 70)
    print("✅ FLAGS FIXED SUCCESSFULLY!")
    print("\nComplete flags restored:")
    print("  🇫🇷 France (ElecLink, IFA, IFA2)")
    print("  🇮🇪 Ireland (East-West, Greenlink, Moyle)")
    print("  🇳🇱 Netherlands (BritNed)")
    print("  🇧🇪 Belgium (Nemo)")
    print("  🇳🇴 Norway (NSL)")
    print("  🇩🇰 Denmark (Viking Link)")
    print("\n💡 Tip: Always use 'RAW' mode when writing emoji characters")
    
    return True

if __name__ == '__main__':
    try:
        success = fix_flags()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
