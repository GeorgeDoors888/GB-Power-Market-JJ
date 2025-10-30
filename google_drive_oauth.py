#!/usr/bin/env python3
"""
Google Drive OAuth Browser Authentication
Downloads UK electricity charges data (TNUoS, FiT, ROC, LEC, BSUoS) from Google Drive
Uses OAuth2 flow with web browser login
"""

import os
import io
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd

# Scopes for Google Drive API
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

# Credentials file (you'll need to create this in Google Cloud Console)
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

def get_drive_service():
    """Initialize Google Drive service with OAuth2 browser authentication"""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists(TOKEN_FILE):
        print("📂 Loading saved credentials...")
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print("❌ credentials.json not found!")
                print("\n📝 To create credentials.json:")
                print("   1. Go to: https://console.cloud.google.com/apis/credentials")
                print("   2. Create OAuth 2.0 Client ID (Desktop application)")
                print("   3. Download JSON and save as 'credentials.json'")
                print("\n💡 Detailed instructions below...")
                return None
            
            print("🌐 Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print("✅ Credentials saved to token.pickle")
    
    service = build('drive', 'v3', credentials=creds)
    return service

def list_all_accessible_files(service):
    """List ALL files the user can access"""
    print("\n📂 Listing all accessible files and folders...\n")
    
    results = service.files().list(
        pageSize=100,
        fields="files(id, name, mimeType, size, modifiedTime, parents, webViewLink)",
        orderBy="modifiedTime desc"
    ).execute()
    
    items = results.get('files', [])
    
    if not items:
        print("❌ No files found.")
        return []
    
    print(f"✅ Found {len(items)} items\n")
    print("="*100)
    
    folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
    files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
    
    if folders:
        print(f"\n📁 FOLDERS ({len(folders)}):")
        print("-"*100)
        for item in folders:
            print(f"   📁 {item['name']}")
            print(f"      ID: {item['id']}")
            print()
    
    if files:
        print(f"\n📄 FILES ({len(files)}):")
        print("-"*100)
        for item in files[:20]:  # Show first 20 files
            size = int(item.get('size', 0)) / 1024 if item.get('size') else 0
            mime = item['mimeType'].split('/')[-1] if '/' in item['mimeType'] else item['mimeType']
            print(f"   📄 {item['name']}")
            print(f"      Type: {mime} | Size: {size:.1f} KB | Modified: {item.get('modifiedTime', 'N/A')[:10]}")
            print()
        
        if len(files) > 20:
            print(f"   ... and {len(files) - 20} more files")
    
    return items

def search_charges_data(service):
    """Search for all electricity charges data"""
    
    print("\n" + "="*100)
    print("🔍 Searching for electricity charges data...")
    print("="*100)
    
    # Search terms for each charge type
    searches = {
        "TNUoS": ["TNUoS", "transmission network", "transmission charges", "transmission tariff"],
        "BSUoS": ["BSUoS", "balancing services", "balancing charges"],
        "DUoS": ["DUoS", "distribution use of system", "distribution charges"],
        "FiT": ["FiT", "feed-in tariff", "feed in tariff"],
        "ROC": ["ROC", "renewables obligation", "renewable obligation certificate"],
        "LEC": ["LEC", "levy exemption", "levy exemption certificate"]
    }
    
    all_results = {}
    
    for charge_type, search_terms in searches.items():
        print(f"\n📊 Searching for {charge_type}...")
        found_files = []
        
        for term in search_terms:
            try:
                results = service.files().list(
                    q=f"name contains '{term}'",
                    pageSize=50,
                    fields="files(id, name, mimeType, size, modifiedTime, webViewLink)"
                ).execute()
                
                files = results.get('files', [])
                
                for file in files:
                    # Avoid duplicates
                    if not any(f['id'] == file['id'] for f in found_files):
                        found_files.append(file)
            
            except Exception as e:
                print(f"   ⚠️ Error searching '{term}': {e}")
        
        all_results[charge_type] = found_files
        print(f"   Found {len(found_files)} file(s)")
        
        for file in found_files:
            size = int(file.get('size', 0)) / 1024 if file.get('size') else 0
            print(f"      • {file['name']} ({size:.1f} KB)")
    
    return all_results

def download_file(service, file_id, file_name, output_path):
    """Download a file from Google Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"      Progress: {int(status.progress() * 100)}%", end='\r')
        
        # Save to file
        fh.seek(0)
        with open(output_path, 'wb') as f:
            f.write(fh.read())
        
        print(f"      ✅ Downloaded: {file_name}")
        return True
    
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False

def export_google_sheet(service, file_id, output_path):
    """Export a Google Sheet to Excel format"""
    try:
        request = service.files().export_media(
            fileId=file_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        with open(output_path, 'wb') as f:
            f.write(fh.read())
        
        print(f"      ✅ Exported: {os.path.basename(output_path)}")
        return True
    
    except Exception as e:
        print(f"      ❌ Error exporting: {e}")
        return False

def download_charges_data(service, results, output_dir="google_drive_data"):
    """Download all found charges data"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n" + "="*100)
    print(f"📥 Downloading files to {output_dir}/...")
    print("="*100)
    
    for charge_type, files in results.items():
        if not files:
            continue
        
        # Create subdirectory
        charge_dir = os.path.join(output_dir, charge_type)
        os.makedirs(charge_dir, exist_ok=True)
        
        print(f"\n{charge_type}:")
        for file in files:
            file_name = file['name']
            output_path = os.path.join(charge_dir, file_name)
            
            # Handle Google Sheets (need to export)
            if file['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                print(f"   📊 Exporting Google Sheet: {file_name}")
                export_google_sheet(service, file['id'], output_path + '.xlsx')
            else:
                print(f"   📄 Downloading: {file_name}")
                download_file(service, file['id'], file_name, output_path)

def main():
    print("🚀 Google Drive OAuth Browser Authentication")
    print("="*100)
    
    # Initialize service
    service = get_drive_service()
    if not service:
        print("\n" + "="*100)
        print("📝 SETUP INSTRUCTIONS")
        print("="*100)
        print("\n1. Go to Google Cloud Console:")
        print("   https://console.cloud.google.com/apis/credentials")
        print("\n2. Select your project (or create a new one)")
        print("\n3. Click 'Create Credentials' → 'OAuth client ID'")
        print("\n4. Application type: 'Desktop app'")
        print("\n5. Download the JSON file")
        print("\n6. Save it as 'credentials.json' in this directory:")
        print(f"   {os.getcwd()}")
        print("\n7. Run this script again")
        print("\n" + "="*100)
        return
    
    print("✅ Connected to Google Drive\n")
    
    # List all accessible files first
    all_items = list_all_accessible_files(service)
    
    # Search for specific charges data
    results = search_charges_data(service)
    
    # Summary
    total_files = sum(len(files) for files in results.values())
    print(f"\n" + "="*100)
    print(f"📊 SUMMARY")
    print("="*100)
    print(f"Total charge files found: {total_files}")
    for charge_type, files in results.items():
        print(f"   {charge_type}: {len(files)} files")
    
    if total_files > 0:
        print("\n❓ Download all charge files? (y/n): ", end="")
        response = input().strip().lower()
        
        if response == 'y':
            download_charges_data(service, results)
            print("\n✅ Download complete!")
            print(f"   Files saved to: google_drive_data/")
            print("\n📁 Next steps:")
            print("   1. Check google_drive_data/ folder for downloaded files")
            print("   2. Parse and ingest data into BigQuery")
            print("   3. Add to dashboard display")
    else:
        print("\n💡 No charge files found. Try:")
        print("   1. Check if files are named differently")
        print("   2. Manually browse your Drive and note file names")
        print("   3. Update search terms in the script")

if __name__ == "__main__":
    main()
