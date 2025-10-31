#!/usr/bin/env python3
"""
Watch Google Sheet for Refresh Requests
Monitors cell M5 for "REFRESH_REQUESTED" trigger from Google Apps Script menu
When detected, automatically runs the data refresh
"""

import pickle
import time
from datetime import datetime
import gspread
import subprocess
import sys

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SHEET_NAME = 'Analysis BI Enhanced'
TRIGGER_CELL = 'M5'
STATUS_CELL = 'L5'
CHECK_INTERVAL = 10  # seconds

print("=" * 80)
print("👀 WATCHING SHEET FOR REFRESH REQUESTS")
print("=" * 80)
print()
print(f"Sheet: {SHEET_NAME}")
print(f"Trigger Cell: {TRIGGER_CELL}")
print(f"Check Interval: {CHECK_INTERVAL}s")
print()
print("💡 In Google Sheets, click: Power Market > Refresh Data Now")
print()
print("Press Ctrl+C to stop watching...")
print()

# Initialize
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet(SHEET_NAME)

last_trigger_value = None

try:
    while True:
        try:
            # Check trigger cell
            current_value = sheet.acell(TRIGGER_CELL).value
            
            if current_value and current_value.startswith('REFRESH_REQUESTED:'):
                # Only refresh if this is a new request
                if current_value != last_trigger_value:
                    timestamp = current_value.replace('REFRESH_REQUESTED:', '')
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔔 REFRESH REQUEST DETECTED")
                    print(f"   Timestamp: {timestamp}")
                    print()
                    
                    # Update status to "Refreshing..."
                    sheet.update_acell(STATUS_CELL, '⏳ Refreshing...')
                    
                    # Run the update script
                    print("   Running: python3 update_analysis_bi_enhanced.py")
                    print("   " + "-" * 60)
                    
                    try:
                        result = subprocess.run(
                            ['python3', 'update_analysis_bi_enhanced.py'],
                            capture_output=True,
                            text=True,
                            timeout=180  # 3 minute timeout
                        )
                        
                        if result.returncode == 0:
                            print("   " + "-" * 60)
                            print("   ✅ REFRESH COMPLETE!")
                            print()
                            
                            # Update status to success
                            sheet.update_acell(STATUS_CELL, '✅ Up to date')
                            
                            # Clear trigger
                            sheet.update_acell(TRIGGER_CELL, '')
                            
                            # Update timestamp
                            sheet.update_acell('A110', f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                            
                        else:
                            print("   " + "-" * 60)
                            print(f"   ❌ REFRESH FAILED (exit code: {result.returncode})")
                            print(f"   Error: {result.stderr[:200]}")
                            print()
                            
                            # Update status to error
                            sheet.update_acell(STATUS_CELL, '❌ Error')
                            
                    except subprocess.TimeoutExpired:
                        print("   " + "-" * 60)
                        print("   ❌ REFRESH TIMEOUT (took more than 3 minutes)")
                        print()
                        sheet.update_acell(STATUS_CELL, '❌ Timeout')
                    
                    except Exception as e:
                        print("   " + "-" * 60)
                        print(f"   ❌ REFRESH ERROR: {e}")
                        print()
                        sheet.update_acell(STATUS_CELL, '❌ Error')
                    
                    last_trigger_value = current_value
                    print(f"   Resuming watch... (checking every {CHECK_INTERVAL}s)")
                    print()
            
            # Sleep before next check
            time.sleep(CHECK_INTERVAL)
            
        except gspread.exceptions.APIError as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️ API Error: {e}")
            print(f"   Retrying in {CHECK_INTERVAL}s...")
            print()
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            raise
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Error: {e}")
            print(f"   Retrying in {CHECK_INTERVAL}s...")
            print()
            time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print()
    print("=" * 80)
    print("👋 STOPPED WATCHING")
    print("=" * 80)
    print()
    sys.exit(0)
