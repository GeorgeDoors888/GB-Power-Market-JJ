#!/usr/bin/env python3
"""
Share Dashboard V2 with service account
"""
import gspread
from google.oauth2.service_account import Credentials

# Configuration
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
SERVICE_ACCOUNT_EMAIL = 'all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com'

def main():
    print("📋 Sharing Dashboard V2 with service account...")
    
    # Authenticate with service account
    creds = Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive']
    )
    
    client = gspread.authorize(creds)
    
    try:
        # Open spreadsheet
        sheet = client.open_by_key(SPREADSHEET_ID)
        
        # Share with service account (Editor role)
        sheet.share(SERVICE_ACCOUNT_EMAIL, perm_type='user', role='writer')
        
        print(f"✅ Successfully shared with {SERVICE_ACCOUNT_EMAIL}")
        print(f"   Spreadsheet: {sheet.title}")
        print(f"   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 If permission denied, manually share:")
        print(f"   1. Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print(f"   2. Click Share button")
        print(f"   3. Add: {SERVICE_ACCOUNT_EMAIL}")
        print(f"   4. Give Editor access")

if __name__ == '__main__':
    main()
