#!/usr/bin/env python3
"""
Reusable module for verifying and fixing interconnector country flag emojis.

This module can be imported by any script that updates the Dashboard to ensure
flags remain complete after updates.

Usage:
    from flag_utils import verify_and_fix_flags
    
    # After updating Dashboard
    verify_and_fix_flags(sheets_service, SHEET_ID)
"""

# Flag mapping - complete 2-character country flag emojis
FLAG_MAP = {
    'ElecLink': '🇫🇷',     # France
    'IFA': '🇫🇷',          # France
    'IFA2': '🇫🇷',         # France
    'East-West': '🇮🇪',    # Ireland
    'Greenlink': '🇮🇪',    # Ireland
    'Moyle': '🇮🇪',        # Northern Ireland (uses Ireland flag)
    'BritNed': '🇳🇱',      # Netherlands
    'Nemo': '🇧🇪',         # Belgium
    'NSL': '🇳🇴',          # Norway
    'Viking': '🇩🇰'        # Denmark (Viking Link)
}

def is_flag_complete(text):
    """
    Check if text contains complete country flag emoji(s).
    
    Country flags are 2-character Unicode sequences.
    
    Args:
        text: String to check
        
    Returns:
        bool: True if contains at least one complete 2-char flag
    """
    flag_chars = [c for c in text if ord(c) > 127000]
    return len(flag_chars) >= 2

def clean_broken_flags(text):
    """
    Remove all emoji characters from text.
    
    Args:
        text: String with potentially broken flags
        
    Returns:
        str: Clean text without emoji characters
    """
    clean_text = text
    for char in text:
        if ord(char) > 127000:  # Unicode emoji range
            clean_text = clean_text.replace(char, '')
    return clean_text.strip()

def add_complete_flag(name):
    """
    Add complete country flag emoji to interconnector name.
    
    Args:
        name: Interconnector name (may have broken flag)
        
    Returns:
        str: Name with complete flag, or original if no match
    """
    # Clean existing flags first
    clean_name = clean_broken_flags(name)
    
    # Match and add complete flag
    for key, flag in FLAG_MAP.items():
        if key in clean_name:
            return f"{flag} {clean_name}"
    
    # No match found, return clean name
    return clean_name

def verify_and_fix_flags(sheets_service, sheet_id, verbose=True):
    """
    Verify interconnector flags are complete, fix if broken.
    
    This function:
    1. Reads interconnector data from Dashboard D8:E17
    2. Checks if flags are complete (2 characters)
    3. Fixes broken flags if found
    4. Writes corrected data back using RAW mode
    5. Verifies all flags are now complete
    
    Args:
        sheets_service: Either Google Sheets API service (build('sheets', 'v4', ...))
                       OR sheets.spreadsheets() resource
        sheet_id: Google Sheet ID
        verbose: Print status messages (default: True)
        
    Returns:
        tuple: (all_complete: bool, num_fixed: int)
    """
    if verbose:
        print("\n" + "=" * 70)
        print("🔧 AUTOMATIC FLAG VERIFICATION & FIX...")
        print("=" * 70)
    
    # Handle both API service and spreadsheets() resource
    if hasattr(sheets_service, 'spreadsheets'):
        sheets = sheets_service.spreadsheets()
    else:
        sheets = sheets_service  # Already a spreadsheets() resource
    
    # Read current interconnector data
    result = sheets.values().get(
        spreadsheetId=sheet_id,
        range='Dashboard!D8:E17'
    ).execute()
    ic_data = result.get('values', [])
    
    if not ic_data:
        if verbose:
            print("⚠️  No interconnector data found")
        return (True, 0)
    
    # Check for broken flags
    broken_flags = []
    for i, row in enumerate(ic_data, start=8):
        if not row or len(row) == 0:
            continue
        ic_name = row[0]
        if not is_flag_complete(ic_name):
            broken_flags.append((i, ic_name))
    
    # Fix if needed
    num_fixed = 0
    if broken_flags:
        if verbose:
            print(f"\n⚠️  Found {len(broken_flags)} broken flags, fixing...")
        
        # Build fixed data
        fixed_data = []
        for row in ic_data:
            if not row or len(row) == 0:
                continue
            ic_name = row[0]
            ic_flow = row[1] if len(row) > 1 else ''
            
            # Add complete flag
            fixed_name = add_complete_flag(ic_name)
            fixed_data.append([fixed_name, ic_flow])
        
        # Write fixed data using RAW mode
        sheets.values().update(
            spreadsheetId=sheet_id,
            range='Dashboard!D8:E17',
            valueInputOption='RAW',  # Critical: preserves emoji encoding
            body={'values': fixed_data}
        ).execute()
        
        num_fixed = len(broken_flags)
        if verbose:
            print(f"✅ Fixed {num_fixed} broken flags")
    else:
        if verbose:
            print("✅ All flags are complete (no fixes needed)")
    
    # Final verification
    result = sheets.values().get(
        spreadsheetId=sheet_id,
        range='Dashboard!D8:E17'
    ).execute()
    final_data = result.get('values', [])
    
    if verbose:
        print("\n📋 Flag Verification:")
    
    all_complete = True
    for i, row in enumerate(final_data, start=8):
        if not row or len(row) == 0:
            continue
        ic_name = row[0]
        is_complete = is_flag_complete(ic_name)
        
        if verbose:
            status = '✅' if is_complete else '❌'
            print(f"   Row {i}: {status} {ic_name[:50]}")
        
        if not is_complete:
            all_complete = False
    
    if verbose:
        print("\n" + "=" * 70)
        if all_complete:
            print("🎉 ALL FLAGS VERIFIED COMPLETE!")
        else:
            print("⚠️  Some flags still broken - manual intervention required")
        print("=" * 70)
    
    return (all_complete, num_fixed)

def verify_flags_only(sheets_service, sheet_id, verbose=True):
    """
    Verify flags without fixing (read-only check).
    
    Args:
        sheets_service: Either Google Sheets API service or spreadsheets() resource
        sheet_id: Google Sheet ID
        verbose: Print status messages
        
    Returns:
        bool: True if all flags complete
    """
    # Handle both API service and spreadsheets() resource
    if hasattr(sheets_service, 'spreadsheets'):
        sheets = sheets_service.spreadsheets()
    else:
        sheets = sheets_service
    
    result = sheets.values().get(
        spreadsheetId=sheet_id,
        range='Dashboard!D8:E17'
    ).execute()
    data = result.get('values', [])
    
    if verbose:
        print("\n✅ INTERCONNECTOR FLAGS VERIFICATION:")
        print("=" * 70)
    
    all_complete = True
    for i, row in enumerate(data, start=8):
        if not row or len(row) == 0:
            continue
        ic_name = row[0]
        is_complete = is_flag_complete(ic_name)
        
        if verbose:
            status = '✅ COMPLETE' if is_complete else '❌ BROKEN'
            print(f"Row {i}: {status} - {ic_name}")
        
        if not is_complete:
            all_complete = False
    
    return all_complete

# CLI usage
if __name__ == '__main__':
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    
    SERVICE_ACCOUNT_FILE = 'inner-cinema-credentials.json'
    SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=creds)
    
    # Verify and fix
    all_complete, num_fixed = verify_and_fix_flags(service, SHEET_ID)
    
    import sys
    sys.exit(0 if all_complete else 1)
