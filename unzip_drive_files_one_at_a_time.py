#!/usr/bin/env python3
"""
Download ZIP files from Google Drive one at a time, unzip them,
upload extracted contents back to Drive, then delete local copies.
"""

import os
import pickle
import zipfile
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import time

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Authenticate and return Google Drive service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def search_zip_files(service):
    """Search for all ZIP files in Drive."""
    print("🔍 Searching for ZIP files in Google Drive...")
    
    query = "mimeType='application/zip' or name contains '.zip'"
    results = service.files().list(
        q=query,
        fields="files(id, name, size, webViewLink)",
        pageSize=1000
    ).execute()
    
    files = results.get('files', [])
    print(f"  Found {len(files)} ZIP files\n")
    return files

def create_extracted_folder(service):
    """Create or get 'Extracted Files' folder in Drive."""
    query = "name = 'Extracted Files' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    
    if folders:
        print(f"✓ Using existing folder: Extracted Files (ID: {folders[0]['id']})\n")
        return folders[0]['id']
    
    # Create new folder
    file_metadata = {
        'name': 'Extracted Files',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"✓ Created folder: Extracted Files (ID: {folder.get('id')})\n")
    return folder.get('id')

def download_file(service, file_id, filepath):
    """Download a file from Drive."""
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"  Download: {progress}%", end='\r')
    
    print(f"  Download: 100% ✓")
    
    with open(filepath, 'wb') as f:
        fh.seek(0)
        f.write(fh.read())

def unzip_file(zip_path, extract_dir):
    """Unzip a file and return list of extracted files."""
    print(f"  📦 Extracting ZIP...")
    
    extracted_files = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            extracted_files = zip_ref.namelist()
        
        print(f"  ✓ Extracted {len(extracted_files)} files")
        return extracted_files
    except Exception as e:
        print(f"  ❌ Error extracting: {e}")
        return []

def upload_file(service, filepath, filename, folder_id):
    """Upload a file to Google Drive."""
    try:
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        media = MediaFileUpload(filepath, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webViewLink'
        ).execute()
        
        return file
    except Exception as e:
        print(f"    ❌ Error uploading {filename}: {e}")
        return None

def cleanup_local(paths):
    """Delete local files and directories."""
    for path in paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
        except Exception as e:
            print(f"  ⚠️ Error deleting {path}: {e}")

def main():
    print("=" * 80)
    print("UNZIP DRIVE FILES ONE AT A TIME")
    print("=" * 80)
    print()
    
    # Get Drive service
    print("🔐 Authenticating with Google Drive...")
    service = get_drive_service()
    print("✓ Authenticated\n")
    
    # Get or create extraction folder
    extract_folder_id = create_extracted_folder(service)
    
    # Find all ZIP files
    zip_files = search_zip_files(service)
    
    if not zip_files:
        print("No ZIP files found!")
        return
    
    # Sort by size (smallest first to minimize disk usage)
    zip_files.sort(key=lambda x: int(x.get('size', 0)))
    
    print(f"📋 Processing {len(zip_files)} ZIP files")
    print(f"   Strategy: Process smallest first to minimize disk usage")
    print()
    
    # Process each ZIP file
    total_extracted = 0
    total_uploaded = 0
    errors = []
    
    for i, zip_file in enumerate(zip_files, 1):
        zip_name = zip_file['name']
        zip_id = zip_file['id']
        zip_size_mb = int(zip_file.get('size', 0)) / (1024 * 1024)
        
        print(f"[{i}/{len(zip_files)}] {zip_name}")
        print(f"  Size: {zip_size_mb:.2f} MB")
        
        # Skip very large files (>50MB) to avoid disk issues
        if zip_size_mb > 50:
            print(f"  ⚠️ Skipping (too large - would use too much disk space)")
            print()
            continue
        
        # Create temp directory for this ZIP
        temp_dir = Path(f"temp_unzip_{i}")
        temp_dir.mkdir(exist_ok=True)
        zip_path = temp_dir / zip_name
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        try:
            # Download ZIP
            print(f"  ⬇️ Downloading from Drive...")
            download_file(service, zip_id, str(zip_path))
            
            # Unzip
            extracted_files = unzip_file(str(zip_path), str(extract_dir))
            total_extracted += len(extracted_files)
            
            if not extracted_files:
                print(f"  ⚠️ No files extracted, skipping upload")
                cleanup_local([str(temp_dir)])
                print()
                continue
            
            # Upload extracted files
            print(f"  ⬆️ Uploading {len(extracted_files)} files to Drive...")
            uploaded_count = 0
            
            for extracted_file in extracted_files:
                file_path = extract_dir / extracted_file
                
                # Skip directories
                if not file_path.is_file():
                    continue
                
                # Upload to Drive
                result = upload_file(service, str(file_path), extracted_file, extract_folder_id)
                if result:
                    uploaded_count += 1
                    if uploaded_count % 10 == 0:
                        print(f"    Uploaded {uploaded_count}/{len(extracted_files)} files...")
            
            print(f"  ✓ Uploaded {uploaded_count} files to 'Extracted Files' folder")
            total_uploaded += uploaded_count
            
            # Clean up local files
            print(f"  🗑️ Cleaning up local files...")
            cleanup_local([str(temp_dir)])
            print(f"  ✓ Done")
            
        except Exception as e:
            print(f"  ❌ Error processing: {e}")
            errors.append(f"{zip_name}: {e}")
            cleanup_local([str(temp_dir)])
        
        print()
        
        # Small delay to avoid API rate limits
        if i % 10 == 0:
            print("⏸️ Pausing 5 seconds to avoid rate limits...")
            time.sleep(5)
            print()
    
    # Summary
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print()
    print(f"📊 Summary:")
    print(f"  ZIP files processed: {len(zip_files)}")
    print(f"  Total files extracted: {total_extracted}")
    print(f"  Total files uploaded: {total_uploaded}")
    print(f"  Errors: {len(errors)}")
    print()
    
    if errors:
        print("⚠️ Errors:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        print()
    
    print("✅ All extracted files are in Google Drive folder: 'Extracted Files'")
    print("💡 Original ZIP files remain in Drive (not deleted)")

if __name__ == '__main__':
    main()
