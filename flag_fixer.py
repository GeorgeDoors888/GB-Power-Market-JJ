#!/usr/bin/env python3
"""
Flag Verification Utility
=========================
Verifies and restores country flag emojis in the Dashboard.

This script is designed to be run after any major formatting change
to ensure that interconnector flags are not lost.
"""

import gspread
from google.oauth2.service_account import Credentials

# --- Configuration ---
DASHBOARD_SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_NAME = 'Dashboard'
FLAG_RANGE = 'D8:D17'

# Expected flags and names
EXPECTED_FLAGS = {
    "IFA": "🇫🇷 IFA",
    "IFA2": "🇫🇷 IFA2",
    "ElecLink": "🇫🇷 ElecLink",
    "BritNed": "🇳🇱 BritNed",
    "Moyle": "🇮🇪 Moyle",
    "EWIC": "🇮🇪 EWIC",
    "Nemo Link": "🇧🇪 Nemo Link",
    "North Sea Link": "🇳🇴 North Sea Link",
    "Viking Link": "🇩🇰 Viking Link",
}

def get_sheet():
    """Connects to Google Sheets and returns the dashboard worksheet."""
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(DASHBOARD_SHEET_ID)
    return spreadsheet.worksheet(SHEET_NAME)

def verify_and_fix_flags():
    """Verifies interconnector flags and fixes them if they are missing."""
    print("🔍 Verifying and fixing country flags...")
    try:
        dashboard = get_sheet()
        
        # Read current values
        current_values = dashboard.get(FLAG_RANGE)
        
        updates = []
        num_fixed = 0
        
        for i, row in enumerate(current_values):
            cell_value = row[0]
            cell_updated = False
            
            # Find which interconnector this is
            for key, expected_value in EXPECTED_FLAGS.items():
                if key in cell_value:
                    if cell_value != expected_value:
                        # Flag is missing or incorrect, prepare an update
                        updates.append({
                            'range': f'D{8+i}',
                            'values': [[expected_value]],
                        })
                        print(f"   - Fixing '{cell_value}' -> '{expected_value}'")
                        num_fixed += 1
                    cell_updated = True
                    break
        
        if updates:
            print(f"\n✍️ Applying {num_fixed} flag fixes...")
            dashboard.batch_update(updates)
            print("✅ Flags restored.")
        else:
            print("✅ All flags are correct. No fixes needed.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_and_fix_flags()
