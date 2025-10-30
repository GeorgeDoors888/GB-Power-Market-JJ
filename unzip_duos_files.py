#!/usr/bin/env python3
"""
Selectively unzip DUoS-related ZIP files from Google Drive.

This script:
1. Searches for ZIP files with DUoS/charging keywords
2. Downloads and extracts only relevant ZIPs
3. Catalogs the contents for analysis
"""

import os
import json
import zipfile
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from datetime import datetime

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
TOKEN_FILE = 'token.pickle'
EXTRACT_DIR = 'drive_duos_unzipped'
CATALOG_FILE = 'duos_unzip_catalog.json'

# Keywords to identify DUoS-related ZIPs
DUOS_KEYWORDS = [
    'duos', 'dnuos', 'charging', 'tariff', 'rates', 
    'statement', 'schedule', 'ukpn', 'nged', 'npg', 
    'enwl', 'spen', 'ssen', 'distribution'
]

def get_drive_service():
    """Authenticate and return Drive service."""
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("No valid credentials. Run oauth_with_sheets.py first.")
    
    return build('drive', 'v3', credentials=creds)

def is_duos_related(filename):
    """Check if filename contains DUoS-related keywords."""
    lower_name = filename.lower()
    return any(keyword in lower_name for keyword in DUOS_KEYWORDS)

def download_file(service, file_id, file_name, destination_path):
    """Download a file from Google Drive."""
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"  Download {progress}%", end='\r')
        
        print(f"  Download 100% ✓")
        
        # Write to file
        with open(destination_path, 'wb') as f:
            f.write(fh.getvalue())
        
        return True
    except Exception as e:
        print(f"  ❌ Error downloading: {e}")
        return False

def unzip_file(zip_path, extract_to):
    """Unzip a file and return list of extracted files."""
    try:
        extracted_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of files in zip
            file_list = zip_ref.namelist()
            
            # Extract all
            zip_ref.extractall(extract_to)
            
            for file in file_list:
                extracted_path = os.path.join(extract_to, file)
                if os.path.isfile(extracted_path):
                    size = os.path.getsize(extracted_path)
                    extracted_files.append({
                        'name': file,
                        'size': size,
                        'size_mb': size / (1024 * 1024),
                        'path': extracted_path,
                        'is_duos_related': is_duos_related(file)
                    })
        
        print(f"  ✓ Extracted {len(extracted_files)} files")
        return extracted_files
    except Exception as e:
        print(f"  ❌ Error unzipping: {e}")
        return []

def search_duos_zip_files(service):
    """Search for DUoS-related ZIP files."""
    print("🔍 Searching for DUoS-related ZIP files in Drive...\n")
    
    # Search for ZIP files
    query = "mimeType='application/zip'"
    
    all_zip_files = []
    page_token = None
    
    while True:
        results = service.files().list(
            q=query,
            pageSize=100,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, size, modifiedTime, webViewLink)"
        ).execute()
        
        all_zip_files.extend(results.get('files', []))
        page_token = results.get('nextPageToken')
        
        if not page_token:
            break
    
    print(f"Found {len(all_zip_files)} total ZIP files")
    
    # Filter for DUoS-related
    duos_zips = [f for f in all_zip_files if is_duos_related(f['name'])]
    
    print(f"Found {len(duos_zips)} DUoS-related ZIP files\n")
    
    return duos_zips

def main():
    """Main function to unzip DUoS-related ZIP files."""
    print("=" * 70)
    print("UNZIPPING DUoS-RELATED ZIP FILES FROM GOOGLE DRIVE")
    print("=" * 70)
    print()
    
    # Create extraction directory
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    # Get Drive service
    print("Authenticating with Google Drive...")
    service = get_drive_service()
    print("✓ Authenticated\n")
    
    # Search for DUoS-related ZIP files
    zip_files = search_duos_zip_files(service)
    
    if not zip_files:
        print("No DUoS-related ZIP files found.")
        return
    
    # Sort by size (smallest first to avoid space issues)
    zip_files.sort(key=lambda x: int(x.get('size', 0)))
    
    # Catalog for tracking
    catalog = {
        'extraction_date': datetime.now().isoformat(),
        'total_zips': len(zip_files),
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'files': []
    }
    
    # Process each ZIP file
    for idx, zip_file in enumerate(zip_files, 1):
        file_id = zip_file['id']
        file_name = zip_file['name']
        file_size_mb = int(zip_file.get('size', 0)) / (1024 * 1024)
        
        print(f"[{idx}/{len(zip_files)}] {file_name}")
        print(f"  Size: {file_size_mb:.2f} MB")
        
        # Skip very large files (>100MB) to save space
        if file_size_mb > 100:
            print(f"  ⏭️  Skipping (too large, >100MB)")
            catalog['files'].append({
                'index': idx,
                'name': file_name,
                'drive_id': file_id,
                'size_mb': file_size_mb,
                'skipped': True,
                'reason': 'Too large (>100MB)'
            })
            catalog['processed'] += 1
            print()
            continue
        
        # Create subdirectory for this ZIP
        safe_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name[:100]  # Limit length
        extract_subdir = os.path.join(EXTRACT_DIR, f"{idx:04d}_{safe_name}")
        os.makedirs(extract_subdir, exist_ok=True)
        
        # Download ZIP
        zip_path = os.path.join(extract_subdir, file_name)
        print(f"  Downloading to {extract_subdir}/")
        
        if download_file(service, file_id, file_name, zip_path):
            # Unzip
            print(f"  Extracting...")
            extracted_files = unzip_file(zip_path, extract_subdir)
            
            # Remove ZIP after extraction to save space
            try:
                os.remove(zip_path)
                print(f"  Removed ZIP file (keeping extracted contents)")
            except:
                pass
            
            # Add to catalog
            catalog['files'].append({
                'index': idx,
                'name': file_name,
                'drive_id': file_id,
                'size_mb': file_size_mb,
                'modified': zip_file.get('modifiedTime', ''),
                'link': zip_file.get('webViewLink', ''),
                'extract_dir': extract_subdir,
                'extracted_files': extracted_files,
                'duos_files': [f for f in extracted_files if f['is_duos_related']],
                'success': len(extracted_files) > 0
            })
            
            if extracted_files:
                catalog['successful'] += 1
            else:
                catalog['failed'] += 1
        else:
            catalog['failed'] += 1
            catalog['files'].append({
                'index': idx,
                'name': file_name,
                'drive_id': file_id,
                'size_mb': file_size_mb,
                'error': 'Download failed',
                'success': False
            })
        
        catalog['processed'] += 1
        print()
    
    # Save catalog
    with open(CATALOG_FILE, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print("=" * 70)
    print("UNZIPPING COMPLETE")
    print("=" * 70)
    print()
    print(f"📊 Statistics:")
    print(f"  Total DUoS ZIP files found: {catalog['total_zips']}")
    print(f"  Successfully extracted: {catalog['successful']}")
    print(f"  Failed: {catalog['failed']}")
    print()
    print(f"📁 Extraction directory: {EXTRACT_DIR}/")
    print(f"📋 Catalog saved to: {CATALOG_FILE}")
    print()
    
    # Summary of DUoS-related files
    duos_files = []
    for file_entry in catalog['files']:
        if file_entry.get('success') and 'duos_files' in file_entry:
            for extracted in file_entry.get('duos_files', []):
                duos_files.append({
                    'zip': file_entry['name'],
                    'file': extracted['name'],
                    'path': extracted['path'],
                    'size_mb': extracted['size_mb']
                })
    
    if duos_files:
        print(f"🎯 Found {len(duos_files)} DUoS-related files in extracted ZIPs:")
        for df in duos_files[:30]:  # Show first 30
            print(f"  - {df['file']} ({df['size_mb']:.2f} MB) from {df['zip']}")
        if len(duos_files) > 30:
            print(f"  ... and {len(duos_files) - 30} more")
        print()
        print(f"📄 Full list in catalog: {CATALOG_FILE}")

if __name__ == '__main__':
    main()
