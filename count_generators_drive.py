#!/usr/bin/env python3
"""
Download and count generators from Google Drive file
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
import os.path
import pickle
import io

# Set up credentials
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly'
]

# Your file ID from the URL
FILE_ID = '1A9nwNYafh0bMcMiTeIot8LYybpzLiO-I'

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
    """Download the file and count generators"""
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        creds = get_credentials()
        
        # Build the Drive service
        service = build('drive', 'v3', credentials=creds)
        
        # Get file metadata
        print(f"\n📊 Getting file information...")
        file_metadata = service.files().get(fileId=FILE_ID, fields='name,mimeType,size').execute()
        
        print(f"   File name: {file_metadata['name']}")
        print(f"   MIME type: {file_metadata['mimeType']}")
        print(f"   Size: {int(file_metadata.get('size', 0)) / 1024:.1f} KB")
        
        # Download the file
        print(f"\n📥 Downloading file...")
        
        # Download the Excel file directly
        request = service.files().get_media(fileId=FILE_ID)
        output_file = 'All_Generators.xlsx'
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"   Download progress: {int(status.progress() * 100)}%")
        
        # Save to file
        fh.seek(0)
        with open(output_file, 'wb') as f:
            f.write(fh.read())
        
        print(f"✅ Downloaded to: {output_file}")
        
        # Read with pandas
        print(f"\n📖 Reading Excel file...")
        
        # Try to read all sheets
        excel_file = pd.ExcelFile(output_file)
        
        print(f"\n📋 Available sheets:")
        for i, sheet_name in enumerate(excel_file.sheet_names, 1):
            print(f"   {i}. {sheet_name}")
        
        # Read the first sheet
        df = pd.read_excel(output_file, sheet_name=excel_file.sheet_names[0])
        
        print(f"\n✅ Successfully loaded data from: {excel_file.sheet_names[0]}")
        print(f"   Total rows: {len(df)}")
        print(f"   Total columns: {len(df.columns)}")
        
        print(f"\n📊 Column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        
        # Try to identify generator/station column
        generator_cols = [col for col in df.columns if any(
            keyword in str(col).lower() 
            for keyword in ['generator', 'station', 'name', 'plant', 'unit', 'bmunit', 'ngc']
        )]
        
        if generator_cols:
            print(f"\n🔍 Potential generator identifier columns:")
            for col in generator_cols:
                unique_count = df[col].nunique()
                non_null_count = df[col].notna().sum()
                print(f"   • {col}: {non_null_count} non-null, {unique_count} unique")
        
        # Count total generators (non-empty rows)
        non_empty_rows = df.dropna(how='all')
        print(f"\n🎯 TOTAL ROWS WITH DATA: {len(non_empty_rows)}")
        
        # If there's a clear generator name column, count unique generators
        if generator_cols:
            main_col = generator_cols[0]
            unique_generators = df[main_col].notna().sum()
            print(f"🎯 TOTAL GENERATORS (by {main_col}): {unique_generators}")
        
        # Show first few rows
        print(f"\n📋 First 5 rows:")
        print(df.head().to_string())
        
        # Try to group by fuel type if column exists
        fuel_cols = [col for col in df.columns if any(
            keyword in str(col).lower() 
            for keyword in ['fuel', 'type', 'technology', 'class']
        )]
        
        if fuel_cols:
            print(f"\n⚡ Breakdown by fuel type:")
            for col in fuel_cols[:1]:  # Use first matching column
                print(f"\n   Column: {col}")
                counts = df[col].value_counts()
                for fuel, count in counts.head(20).items():
                    if pd.notna(fuel) and str(fuel).strip() != '':
                        print(f"   • {fuel}: {count}")
        
        # Save to CSV for further analysis
        csv_file = 'generators_list.csv'
        df.to_csv(csv_file, index=False)
        print(f"\n💾 Saved to: {csv_file}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    print("🔌 Generator Counter - Google Drive")
    print("=" * 50)
    count_generators()
