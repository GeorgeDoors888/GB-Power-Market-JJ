"""
Update Google Sheets Dashboard with AlmaLinux-hosted Map URL
Adds a hyperlink to the live map hosted on UpCloud server
"""

import gspread
from google.oauth2.service_account import Credentials
import pickle
import os

# Server details
SERVER_IP = "94.237.55.234"
MAP_URL = f"http://{SERVER_IP}/gb_power_complete_map.html"

# Your Google Sheets details
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SPREADSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"

def authenticate_google():
    """Authenticate with Google Sheets API"""
    print("Authenticating with Google Sheets...")
    
    # Try to use existing token.pickle
    if os.path.exists('token.pickle'):
        print("Using existing token.pickle")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    else:
        # Use service account credentials
        print("Using service account credentials")
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
    
    client = gspread.authorize(creds)
    print("✓ Authentication successful")
    return client

def update_dashboard(client, spreadsheet_id=SPREADSHEET_ID):
    """Update the dashboard with the map URL"""
    print(f"\nOpening spreadsheet ID: {spreadsheet_id}")
    
    try:
        # Open by ID (more reliable)
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✓ Opened spreadsheet: {spreadsheet.title}")
    except Exception as e:
        print(f"❌ Error opening spreadsheet: {e}")
        print("\nPlease ensure:")
        print("1. The service account has access to the spreadsheet")
        print("2. The spreadsheet ID is correct")
        print(f"3. URL: {SPREADSHEET_URL}")
        return False
    
    # Get first worksheet
    try:
        worksheet = spreadsheet.sheet1
        print(f"✓ Opened worksheet: {worksheet.title}")
    except Exception as e:
        print(f"❌ Error accessing worksheet: {e}")
        return False
    
    # Find a good location to add the map link
    # Try to add to cell A1 or find an empty cell
    print("\nAdding map link to sheet...")
    
    # Option 1: Add as hyperlink formula
    hyperlink_formula = f'=HYPERLINK("{MAP_URL}", "🗺️ View Live GB Power Map")'
    
    # Find empty cell in column A
    try:
        values = worksheet.col_values(1)
        row = len(values) + 2  # Add with one blank row
    except:
        row = 1
    
    worksheet.update_acell(f'A{row}', hyperlink_formula)
    print(f"✓ Added hyperlink to cell A{row}")
    
    # Add description in next cell
    worksheet.update_acell(f'B{row}', 'Live map auto-updates every 30 minutes')
    print(f"✓ Added description to cell B{row}")
    
    # Add URL as plain text for reference
    worksheet.update_acell(f'A{row+1}', 'Direct URL:')
    worksheet.update_acell(f'B{row+1}', MAP_URL)
    print(f"✓ Added URL to cells A{row+1}:B{row+1}")
    
    print(f"\n✅ Dashboard updated successfully!")
    print(f"\nMap URL: {MAP_URL}")
    print(f"Spreadsheet: {spreadsheet.url}")
    
    return True

def main():
    """Main execution"""
    print("=== Updating Google Sheets Dashboard ===")
    print(f"Server: almalinux-1cpu-2gb-uk-lon1")
    print(f"IP: {SERVER_IP}")
    print(f"Map URL: {MAP_URL}")
    print()
    
    try:
        # Authenticate
        client = authenticate_google()
        
        # Update dashboard
        success = update_dashboard(client)
        
        if success:
            print("\n=== Update Complete ===")
            print("\nNext Steps:")
            print("1. Open your Google Sheets dashboard")
            print("2. Click the '🗺️ View Live GB Power Map' link")
            print("3. Map will show latest data (auto-updates every 30 minutes)")
        else:
            print("\n⚠️  Update incomplete - check errors above")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n=== Manual Update Instructions ===")
        print("\nIf automatic update fails, add this to your Google Sheet manually:")
        print(f'\n1. In any cell, enter this formula:')
        print(f'   =HYPERLINK("{MAP_URL}", "View Live GB Power Map")')
        print(f'\n2. Or add plain URL:')
        print(f'   {MAP_URL}')

if __name__ == "__main__":
    main()
