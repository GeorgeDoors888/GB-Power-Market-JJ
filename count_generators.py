#!/usr/bin/env python3
"""
Count generators from Google Sheets
"""

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import os.path
import pickle

# Set up credentials
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Your sheet ID from the URL
SHEET_ID = '1A9nwNYafh0bMcMiTeIot8LYybpzLiO-I'

def get_credentials():
    """Get OAuth credentials"""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def count_generators():
    """Read the Google Sheet and count generators"""
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        creds = get_credentials()
        
        client = gspread.authorize(creds)
        
        # Open the spreadsheet
        print(f"📊 Opening spreadsheet...")
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # List all worksheets
        print(f"\n📋 Available worksheets:")
        for i, worksheet in enumerate(spreadsheet.worksheets(), 1):
            print(f"   {i}. {worksheet.title} ({worksheet.row_count} rows x {worksheet.col_count} cols)")
        
        # Get the first worksheet (or you can specify by name)
        worksheet = spreadsheet.sheet1
        
        print(f"\n📖 Reading worksheet: {worksheet.title}")
        
        # Get all values
        data = worksheet.get_all_records()
        
        if not data:
            print("❌ No data found in worksheet")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        print(f"\n✅ Successfully loaded data")
        print(f"   Total rows: {len(df)}")
        print(f"   Total columns: {len(df.columns)}")
        
        print(f"\n📊 Column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        
        # Try to identify generator/station column
        generator_cols = [col for col in df.columns if any(
            keyword in col.lower() 
            for keyword in ['generator', 'station', 'name', 'plant', 'unit', 'bmunit']
        )]
        
        if generator_cols:
            print(f"\n🔍 Potential generator identifier columns:")
            for col in generator_cols:
                unique_count = df[col].nunique()
                print(f"   • {col}: {unique_count} unique values")
        
        # Count total generators (non-empty rows)
        non_empty_rows = df.dropna(how='all')
        print(f"\n🎯 TOTAL GENERATORS: {len(non_empty_rows)}")
        
        # Show first few rows
        print(f"\n📋 First 5 rows:")
        print(df.head().to_string())
        
        # Try to group by fuel type if column exists
        fuel_cols = [col for col in df.columns if any(
            keyword in col.lower() 
            for keyword in ['fuel', 'type', 'technology']
        )]
        
        if fuel_cols:
            print(f"\n⚡ Breakdown by fuel type:")
            for col in fuel_cols[:1]:  # Use first matching column
                print(f"\n   Column: {col}")
                counts = df[col].value_counts()
                for fuel, count in counts.items():
                    if pd.notna(fuel) and fuel != '':
                        print(f"   • {fuel}: {count}")
        
        # Save to CSV for further analysis
        output_file = 'generators_list.csv'
        df.to_csv(output_file, index=False)
        print(f"\n💾 Saved to: {output_file}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Check credentials.json exists")
        print(f"2. Verify service account has access to the sheet")
        print(f"3. Share the Google Sheet with the service account email")
        raise

if __name__ == '__main__':
    print("🔌 Generator Counter - Google Sheets")
    print("=" * 50)
    count_generators()
