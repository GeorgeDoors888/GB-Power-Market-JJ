#!/usr/bin/env python3
"""
Download ZIP files from Google Drive one at a time, extract them,
upload extracted contents back to Drive, then delete local copies.
"""

import os
import pickle
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# Configuration
MAX_ZIP_SIZE_MB = 500  # Don't process ZIPs larger than this
MIN_FREE_SPACE_GB = 5  # Stop if free space drops below this
DRIVE_EXTRACTED_FOLDER = "Extracted ZIP Contents"
TEMP_DIR = "temp_unzip"

def get_drive_service():
    """Authenticate and return Drive service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
    
    return build('drive', 'v3', credentials=creds)

def get_free_space_gb():
    """Get free disk space in GB."""
    stat = os.statvfs('.')
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    return free_gb

def find_zip_files(service):
    """Find all ZIP files in Drive."""
    print("🔍 Searching for ZIP files in Drive...")
    
    query = "mimeType='application/zip' or name contains '.zip'"
    results = service.files().list(
        q=query,
        fields="files(id, name, size, webViewLink)",
        pageSize=1000
    ).execute()
    
    zip_files = results.get('files', [])
    
    # Filter by size
    filtered_zips = []
    for zf in zip_files:
        size_mb = int(zf.get('size', 0)) / (1024 * 1024)
        if size_mb <= MAX_ZIP_SIZE_MB:
            zf['size_mb'] = size_mb
            filtered_zips.append(zf)
    
    print(f"  Found {len(zip_files)} ZIP files")
    print(f"  Filtered to {len(filtered_zips)} files (under {MAX_ZIP_SIZE_MB}MB)")
    
    return sorted(filtered_zips, key=lambda x: x['size_mb'])

def create_drive_folder(service, folder_name):
    """Create or get a folder in Drive."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    
    if folders:
        return folders[0]['id']
    
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def download_file(service, file_id, destination):
    """Download a file from Drive."""
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    with open(destination, 'wb') as f:
        f.write(fh.getvalue())

def upload_file(service, filepath, filename, folder_id):
    """Upload a file to Drive."""
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(filepath, resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    return file

def extract_and_upload_zip(service, zip_info, folder_id, temp_dir):
    """Download, extract, upload contents, and cleanup."""
    zip_name = zip_info['name']
    zip_id = zip_info['id']
    size_mb = zip_info['size_mb']
    
    print(f"\n{'='*80}")
    print(f"Processing: {zip_name} ({size_mb:.2f} MB)")
    print(f"{'='*80}")
    
    # Check free space
    free_space = get_free_space_gb()
    print(f"💾 Free space: {free_space:.2f} GB")
    
    if free_space < MIN_FREE_SPACE_GB:
        print(f"⚠️  LOW DISK SPACE! Stopping (need at least {MIN_FREE_SPACE_GB}GB free)")
        return False
    
    # Create temp directory
    os.makedirs(temp_dir, exist_ok=True)
    zip_path = os.path.join(temp_dir, zip_name)
    
    try:
        # Download ZIP
        print(f"⬇️  Downloading from Drive...")
        download_file(service, zip_id, zip_path)
        print(f"✓ Downloaded")
        
        # Extract ZIP
        print(f"📦 Extracting...")
        extract_dir = os.path.join(temp_dir, Path(zip_name).stem)
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        extracted_files = list(Path(extract_dir).rglob('*'))
        file_count = len([f for f in extracted_files if f.is_file()])
        print(f"✓ Extracted {file_count} files")
        
        # Upload extracted files
        print(f"⬆️  Uploading to Drive folder: {DRIVE_EXTRACTED_FOLDER}")
        uploaded_count = 0
        
        for file_path in extracted_files:
            if file_path.is_file():
                relative_path = file_path.relative_to(extract_dir)
                upload_file(service, str(file_path), str(relative_path), folder_id)
                uploaded_count += 1
                if uploaded_count % 10 == 0:
                    print(f"  Uploaded {uploaded_count}/{file_count} files...")
        
        print(f"✓ Uploaded {uploaded_count} files")
        
        # Cleanup
        print(f"🗑️  Cleaning up local files...")
        os.remove(zip_path)
        shutil.rmtree(extract_dir)
        print(f"✓ Cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {zip_name}: {e}")
        # Cleanup on error
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        return True  # Continue with next file

def main():
    print("=" * 80)
    print("SEQUENTIAL ZIP EXTRACTION TO GOOGLE DRIVE")
    print("=" * 80)
    print()
    print(f"⚙️  Configuration:")
    print(f"  Max ZIP size: {MAX_ZIP_SIZE_MB} MB")
    print(f"  Min free space: {MIN_FREE_SPACE_GB} GB")
    print(f"  Temp directory: {TEMP_DIR}")
    print()
    
    # Check initial free space
    free_space = get_free_space_gb()
    print(f"💾 Current free space: {free_space:.2f} GB")
    
    if free_space < MIN_FREE_SPACE_GB + 2:
        print(f"⚠️  WARNING: Low disk space! This might not work well.")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled")
            return
    
    print()
    
    # Get Drive service
    print("🔐 Authenticating with Google Drive...")
    service = get_drive_service()
    print("✓ Authenticated")
    print()
    
    # Create destination folder
    folder_id = create_drive_folder(service, DRIVE_EXTRACTED_FOLDER)
    print(f"✓ Using Drive folder: {DRIVE_EXTRACTED_FOLDER}")
    print()
    
    # Find ZIP files
    zip_files = find_zip_files(service)
    
    if not zip_files:
        print("No ZIP files found to process")
        return
    
    print()
    print(f"📋 Will process {len(zip_files)} ZIP files")
    print()
    
    # Process each ZIP
    processed = 0
    errors = 0
    
    for i, zip_info in enumerate(zip_files, 1):
        print(f"\n[{i}/{len(zip_files)}]")
        success = extract_and_upload_zip(service, zip_info, folder_id, TEMP_DIR)
        
        if not success:
            print("Stopped due to low disk space")
            break
        
        processed += 1
    
    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ Processed: {processed}/{len(zip_files)} ZIP files")
    print(f"💾 Final free space: {get_free_space_gb():.2f} GB")
    print(f"📁 Extracted files in Drive folder: {DRIVE_EXTRACTED_FOLDER}")

if __name__ == '__main__':
    main()
