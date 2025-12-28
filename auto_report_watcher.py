#!/usr/bin/env python3
"""
Auto-run report when CALCULATE button is clicked
Watches Analysis!B14 for status marker, then runs generate_analysis_report.py
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import time
import subprocess
import sys

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
CHECK_CELL = 'Analysis!B15'  # Trigger cell
STATUS_CELL = 'Analysis!A18'  # Status message cell

print("🤖 Auto-Report Generator Started")
print("=" * 60)
print(f"📊 Watching: {CHECK_CELL}")
print(f"💡 Click CALCULATE button to trigger report")
print(f"⏸️  Press Ctrl+C to stop\n")

creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
sheets_service = build('sheets', 'v4', credentials=creds)

last_value = None

try:
    while True:
        # Check trigger cell
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=CHECK_CELL
        ).execute()

        current_value = result.get('values', [['']])[0][0] if result.get('values') else ''

        # If value changed to "RUN" or "GENERATE"
        if current_value and current_value != last_value:
            if 'RUN' in str(current_value).upper() or 'GENERATE' in str(current_value).upper():
                print(f"\n🔔 Trigger detected! Value: {current_value}")
                print("▶️  Running generate_analysis_report.py...")

                # Update status
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=STATUS_CELL,
                    valueInputOption='RAW',
                    body={'values': [['⏳ Generating report... Please wait...']]}
                ).execute()

                # Run the script
                result = subprocess.run(
                    ['python3', 'generate_analysis_report.py'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print("✅ Report generated successfully!")
                    # Clear trigger
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=CHECK_CELL,
                        valueInputOption='RAW',
                        body={'values': [['']]}
                    ).execute()
                else:
                    print(f"❌ Error: {result.stderr}")
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=STATUS_CELL,
                        valueInputOption='RAW',
                        body={'values': [[f'❌ Error: {result.stderr[:100]}']]}
                    ).execute()

        last_value = current_value
        time.sleep(2)  # Check every 2 seconds

except KeyboardInterrupt:
    print("\n\n👋 Auto-reporter stopped")
    sys.exit(0)
