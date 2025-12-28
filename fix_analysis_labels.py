#!/usr/bin/env python3
"""
Fix Analysis sheet labels to match dropdown order
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
service = build('sheets', 'v4', credentials=creds)

print("🔧 Fixing Analysis sheet labels to match dropdown order...\n")

# Correct labels matching the dropdown order (B5-B9):
# B5: Party Role
# B6: BMU IDs
# B7: Unit Names
# B8: Generation Type
# B9: Lead Party

labels = [
    ['Party Role:'],      # A5
    ['BMU IDs:'],         # A6
    ['Unit Names:'],      # A7
    ['Generation Type:'], # A8
    ['Lead Party:']       # A9
]

service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Analysis!A5:A9',
    valueInputOption='RAW',
    body={'values': labels}
).execute()

print("✅ Labels updated in column A:")
print("   A5: Party Role:")
print("   A6: BMU IDs:")
print("   A7: Unit Names:")
print("   A8: Generation Type:")
print("   A9: Lead Party:")
print("\n✅ Now matches dropdown order in column B!")
