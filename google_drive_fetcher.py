#!/usr/bin/env python3
"""
Google Drive Data Fetcher
Downloads UK electricity charges data (TNUoS, FiT, ROC, LEC, BSUoS) from Google Drive
"""

import os
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd

# Scopes for Google Drive API
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

SERVICE_ACCOUNT_FILE = "jibber_jabber_key.json"

def get_drive_service():
    """Initialize Google Drive service"""
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"❌ Error initializing Drive service: {e}")
        return None

def search_files(service, query, mime_types=None):
    """Search for files in Google Drive"""
    try:
        # Build query
        q = f"name contains '{query}'"
        if mime_types:
            mime_queries = [f"mimeType='{m}'" for m in mime_types]
            q += f" and ({' or '.join(mime_queries)})"
        
        # Search
        results = service.files().list(
            q=q,
            pageSize=50,
            fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink)"
        ).execute()
        
        items = results.get('files', [])
        return items
    
    except Exception as e:
        print(f"❌ Error searching files: {e}")
        return []

def list_all_files(service, folder_id=None):
    """List all files (optionally in a specific folder)"""
    try:
        q = f"'{folder_id}' in parents" if folder_id else None
        
        results = service.files().list(
            q=q,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink)"
        ).execute()
        
        items = results.get('files', [])
        return items
    
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []

def download_file(service, file_id, filename):
    """Download a file from Google Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"   Download {int(status.progress() * 100)}%")
        
        # Save to file
        fh.seek(0)
        with open(filename, 'wb') as f:
            f.write(fh.read())
        
        print(f"✅ Downloaded: {filename}")
        return True
    
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return False

def search_charges_data(service):
    """Search for all electricity charges data"""
    
    print("🔍 Searching Google Drive for electricity charges data...")
    print("="*80)
    
    # Search terms for each charge type
    searches = {
        "TNUoS": ["TNUoS", "transmission network", "transmission charges"],
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
            files = search_files(service, term, mime_types=[
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/csv',
                'application/pdf',
                'application/vnd.google-apps.spreadsheet'
            ])
            
            for file in files:
                if file not in found_files:
                    found_files.append(file)
        
        all_results[charge_type] = found_files
        print(f"   Found {len(found_files)} file(s)")
        
        for file in found_files:
            print(f"      • {file['name']} ({file['mimeType']}) - {file.get('size', 'N/A')} bytes")
    
    return all_results

def download_charges_data(service, results, output_dir="google_drive_data"):
    """Download all found charges data"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📥 Downloading files to {output_dir}/...")
    print("="*80)
    
    for charge_type, files in results.items():
        if not files:
            continue
        
        # Create subdirectory
        charge_dir = os.path.join(output_dir, charge_type)
        os.makedirs(charge_dir, exist_ok=True)
        
        print(f"\n{charge_type}:")
        for file in files:
            filename = os.path.join(charge_dir, file['name'])
            
            # Handle Google Sheets (need to export)
            if file['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                print(f"   Exporting Google Sheet: {file['name']}...")
                export_google_sheet(service, file['id'], filename + '.xlsx')
            else:
                print(f"   Downloading: {file['name']}...")
                download_file(service, file['id'], filename)

def export_google_sheet(service, file_id, filename):
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
        with open(filename, 'wb') as f:
            f.write(fh.read())
        
        print(f"✅ Exported: {filename}")
        return True
    
    except Exception as e:
        print(f"❌ Error exporting sheet: {e}")
        return False

def main():
    print("🚀 Google Drive Charges Data Fetcher")
    print("="*80)
    
    # Initialize service
    service = get_drive_service()
    if not service:
        print("❌ Failed to initialize Google Drive service")
        print("\n💡 Make sure your service account has access to the Drive folder:")
        print("   1. Share the folder with the service account email")
        print("   2. The email is in jibber_jabber_key.json ('client_email' field)")
        return
    
    print("✅ Connected to Google Drive")
    
    # Search for charges data
    results = search_charges_data(service)
    
    # Summary
    total_files = sum(len(files) for files in results.values())
    print(f"\n📊 SUMMARY")
    print("="*80)
    print(f"Total files found: {total_files}")
    for charge_type, files in results.items():
        print(f"   {charge_type}: {len(files)} files")
    
    if total_files == 0:
        print("\n⚠️  No files found. Possible reasons:")
        print("   1. Service account doesn't have access to the folder")
        print("   2. Files are named differently than expected")
        print("   3. Files are in a specific folder (try list_all_files)")
        return
    
    # Ask to download
    print("\n❓ Download all files? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        download_charges_data(service, results)
        print("\n✅ Download complete!")
        print(f"   Files saved to: google_drive_data/")
    else:
        print("\n💡 To download specific files, modify the script or run again")

if __name__ == "__main__":
    main()
