#!/usr/bin/env python3
"""
Download ZIP files from Google Drive in batches of 10, extract them,
upload extracted contents back to Drive, then delete local copies.
"""

import os
import pickle
import zipfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import threading

# Configuration
MAX_ZIP_SIZE_MB = 500  # Don't process ZIPs larger than this
MIN_FREE_SPACE_GB = 3  # Stop if free space drops below this
DRIVE_EXTRACTED_FOLDER = "Extracted ZIP Contents"
TEMP_DIR = "temp_unzip"
BATCH_SIZE = 10  # Process 10 at a time

# Thread-safe counter
class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

progress_counter = Counter()

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
    
    # Only find actual ZIP files, not .download files or folders
    query = "mimeType='application/zip' and not name contains '.download'"
    results = service.files().list(
        q=query,
        fields="files(id, name, size, webViewLink, mimeType)",
        pageSize=1000
    ).execute()
    
    zip_files = results.get('files', [])
    
    # Filter by size and ensure it's actually a file
    filtered_zips = []
    for zf in zip_files:
        # Skip if it's a folder or has no size
        if zf.get('mimeType') == 'application/vnd.google-apps.folder':
            continue
        
        size = int(zf.get('size', 0))
        if size == 0:  # Skip empty or invalid files
            continue
            
        size_mb = size / (1024 * 1024)
        if size_mb <= MAX_ZIP_SIZE_MB and size_mb > 0:
            zf['size_mb'] = size_mb
            filtered_zips.append(zf)
    
    print(f"  Found {len(zip_files)} ZIP files")
    print(f"  Filtered to {len(filtered_zips)} valid files (0-{MAX_ZIP_SIZE_MB}MB)")
    
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

def process_single_zip(zip_info, folder_id, temp_dir, total_count):
    """Download, extract, upload contents, and cleanup a single ZIP."""
    service = get_drive_service()  # Each thread gets its own service
    
    zip_name = zip_info['name']
    zip_id = zip_info['id']
    size_mb = zip_info['size_mb']
    
    count = progress_counter.increment()
    
    # Create unique temp directory for this ZIP
    zip_temp_dir = os.path.join(temp_dir, f"zip_{count}")
    os.makedirs(zip_temp_dir, exist_ok=True)
    zip_path = os.path.join(zip_temp_dir, zip_name)
    
    try:
        print(f"[{count}/{total_count}] {zip_name} ({size_mb:.2f} MB) - Downloading...")
        download_file(service, zip_id, zip_path)
        
        print(f"[{count}/{total_count}] {zip_name} - Extracting...")
        extract_dir = os.path.join(zip_temp_dir, Path(zip_name).stem)
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        extracted_files = list(Path(extract_dir).rglob('*'))
        file_count = len([f for f in extracted_files if f.is_file()])
        
        print(f"[{count}/{total_count}] {zip_name} - Uploading {file_count} files...")
        uploaded_count = 0
        
        for file_path in extracted_files:
            if file_path.is_file():
                relative_path = file_path.relative_to(extract_dir)
                upload_file(service, str(file_path), str(relative_path), folder_id)
                uploaded_count += 1
        
        print(f"[{count}/{total_count}] {zip_name} - ✓ Complete ({uploaded_count} files uploaded)")
        
        # Cleanup
        shutil.rmtree(zip_temp_dir)
        
        return {'success': True, 'name': zip_name, 'files': uploaded_count}
        
    except Exception as e:
        print(f"[{count}/{total_count}] {zip_name} - ❌ Error: {e}")
        # Cleanup on error
        if os.path.exists(zip_temp_dir):
            shutil.rmtree(zip_temp_dir)
        return {'success': False, 'name': zip_name, 'error': str(e)}

def main():
    print("=" * 80)
    print("BATCH ZIP EXTRACTION TO GOOGLE DRIVE")
    print("=" * 80)
    print()
    print(f"⚙️  Configuration:")
    print(f"  Batch size: {BATCH_SIZE} ZIPs at a time")
    print(f"  Max ZIP size: {MAX_ZIP_SIZE_MB} MB")
    print(f"  Min free space: {MIN_FREE_SPACE_GB} GB")
    print()
    
    # Check initial free space
    free_space = get_free_space_gb()
    print(f"💾 Current free space: {free_space:.2f} GB")
    
    if free_space < MIN_FREE_SPACE_GB + 2:
        print(f"⚠️  WARNING: Low disk space!")
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
    print(f"📋 Will process {len(zip_files)} ZIP files in batches of {BATCH_SIZE}")
    print()
    
    # Create temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Process in batches
    total_processed = 0
    total_uploaded = 0
    errors = []
    
    for i in range(0, len(zip_files), BATCH_SIZE):
        batch = zip_files[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(zip_files) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n{'='*80}")
        print(f"BATCH {batch_num}/{total_batches} - Processing {len(batch)} ZIPs")
        print(f"{'='*80}")
        
        # Check free space before each batch
        free_space = get_free_space_gb()
        print(f"💾 Free space: {free_space:.2f} GB\n")
        
        if free_space < MIN_FREE_SPACE_GB:
            print(f"⚠️  LOW DISK SPACE! Stopping.")
            break
        
        # Process batch in parallel
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
            futures = []
            for zip_info in batch:
                future = executor.submit(process_single_zip, zip_info, folder_id, TEMP_DIR, len(zip_files))
                futures.append(future)
            
            # Wait for batch to complete
            for future in as_completed(futures):
                result = future.result()
                total_processed += 1
                if result['success']:
                    total_uploaded += result['files']
                else:
                    errors.append(result)
        
        print(f"\n✓ Batch {batch_num} complete")
    
    # Cleanup temp directory
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ Processed: {total_processed}/{len(zip_files)} ZIP files")
    print(f"⬆️ Total files uploaded: {total_uploaded}")
    print(f"❌ Errors: {len(errors)}")
    print(f"💾 Final free space: {get_free_space_gb():.2f} GB")
    print(f"📁 Extracted files in Drive folder: {DRIVE_EXTRACTED_FOLDER}")
    
    if errors:
        print()
        print("Errors:")
        for error in errors[:10]:
            print(f"  - {error['name']}: {error['error']}")

if __name__ == '__main__':
    main()
