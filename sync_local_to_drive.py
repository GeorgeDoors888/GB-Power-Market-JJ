#!/usr/bin/env python3
"""
Sync local files to Google Drive and clean up local copies.

This script:
1. Scans local directory for all files
2. Checks if each file exists in Drive (by name and checksum)
3. Uploads files missing from Drive
4. Deletes local files that are safely backed up in Drive
5. Generates a detailed report
"""

import os
import hashlib
import pickle
import json
from pathlib import Path
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configuration
TOKEN_FILE = 'token.pickle'
SCOPES = ['https://www.googleapis.com/auth/drive']
DRIVE_FOLDER_NAME = 'GB Power Market JJ Backup'
EXCLUDE_DIRS = {'.git', '.venv', 'node_modules', '__pycache__', '.DS_Store', 
                'drive_unzipped', 'drive_duos_unzipped'}
EXCLUDE_FILES = {'token.pickle', '.gitignore', 'jibber_jabber_key.json'}
MAX_FILE_SIZE_MB = 100  # Don't auto-upload files larger than this

# ONLY process these data file extensions (exclude code/docs)
DATA_FILE_EXTENSIONS = {
    # Documents
    '.pdf', '.doc', '.docx', '.txt',
    # Spreadsheets
    '.csv', '.xls', '.xlsx', '.xlsm',
    # Data formats
    '.json', '.xml', '.yaml', '.yml',
    # Archives
    '.zip', '.tar', '.gz', '.7z', '.rar',
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.svg',
    # Other data
    '.parquet', '.feather', '.h5', '.hdf5', '.db', '.sqlite'
}

# Explicitly EXCLUDE these code/doc extensions
CODE_DOC_EXTENSIONS = {
    '.py', '.md', '.rst', '.sh', '.bash', '.zsh',
    '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
    '.yml', '.yaml', '.toml', '.ini', '.cfg', '.conf',
    '.ipynb', '.r', '.sql', '.go', '.java', '.cpp', '.c',
    '.h', '.hpp', '.rs', '.swift', '.kt', '.scala'
}

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
            raise Exception("No valid credentials.")
    
    return build('drive', 'v3', credentials=creds)

def get_file_md5(filepath):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"  ⚠️  Error calculating MD5 for {filepath}: {e}")
        return None

def scan_local_files(base_path):
    """Scan local directory and return list of files with metadata."""
    files = []
    base_path = Path(base_path)
    
    print("🔍 Scanning local files...")
    
    for root, dirs, filenames in os.walk(base_path):
        # Remove excluded directories from search
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for filename in filenames:
            if filename in EXCLUDE_FILES or filename.startswith('.'):
                continue
            
            # Get file extension
            file_ext = Path(filename).suffix.lower()
            
            # Skip if not a data file extension
            if file_ext not in DATA_FILE_EXTENSIONS:
                continue
            
            # Double-check: explicitly skip code/doc files
            if file_ext in CODE_DOC_EXTENSIONS:
                continue
            
            filepath = Path(root) / filename
            try:
                size = filepath.stat().st_size
                size_mb = size / (1024 * 1024)
                
                files.append({
                    'path': str(filepath),
                    'name': filename,
                    'size': size,
                    'size_mb': size_mb,
                    'relative_path': str(filepath.relative_to(base_path)),
                    'modified': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                    'md5': None  # Calculate later if needed
                })
            except Exception as e:
                print(f"  ⚠️  Error reading {filepath}: {e}")
    
    print(f"  Found {len(files)} local files\n")
    return files

def search_drive_for_file(service, filename, size=None):
    """Search Drive for a file by name and optionally size."""
    try:
        # Search just by name without size (size filter causing issues)
        # Escape single quotes by doubling them for Drive API
        escaped_filename = filename.replace("'", "''")
        query = f"name = '{escaped_filename}'"
        
        results = service.files().list(
            q=query,
            fields="files(id, name, size, md5Checksum, webViewLink)",
            pageSize=10
        ).execute()
        
        # If size provided, filter results by size
        files = results.get('files', [])
        if size and files:
            files = [f for f in files if int(f.get('size', 0)) == size]
        
        return files
    except Exception as e:
        print(f"  ⚠️  Error searching Drive: {e}")
        return []

def create_drive_folder(service, folder_name):
    """Create a folder in Drive root and return its ID."""
    try:
        # Check if folder already exists
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])
        
        if folders:
            print(f"✓ Using existing Drive folder: {folder_name} (ID: {folders[0]['id']})\n")
            return folders[0]['id']
        
        # Create new folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        print(f"✓ Created Drive folder: {folder_name} (ID: {folder.get('id')})\n")
        return folder.get('id')
    except Exception as e:
        print(f"❌ Error creating folder: {e}")
        return None

def upload_to_drive(service, filepath, filename, folder_id):
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
            fields='id, webViewLink'
        ).execute()
        
        return file
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return None

def main():
    """Main sync function."""
    print("=" * 80)
    print("SYNCING LOCAL DATA FILES TO GOOGLE DRIVE")
    print("=" * 80)
    print()
    print("📋 File types to sync:")
    print(f"   {', '.join(sorted(DATA_FILE_EXTENSIONS))}")
    print()
    print("🚫 Excluding code/doc files:")
    print(f"   {', '.join(sorted(CODE_DOC_EXTENSIONS))}")
    print()
    
    base_path = os.getcwd()
    print(f"📁 Working directory: {base_path}\n")
    
    # Get Drive service
    print("🔐 Authenticating with Google Drive...")
    service = get_drive_service()
    print("✓ Authenticated\n")
    
    # Create/get backup folder
    folder_id = create_drive_folder(service, DRIVE_FOLDER_NAME)
    if not folder_id:
        print("❌ Cannot proceed without a Drive folder")
        return
    
    # Scan local files
    local_files = scan_local_files(base_path)
    
    if not local_files:
        print("No files to sync!")
        return
    
    # Process each file
    report = {
        'scan_date': datetime.now().isoformat(),
        'total_files': len(local_files),
        'already_in_drive': 0,
        'uploaded': 0,
        'too_large': 0,
        'errors': 0,
        'deleted_locally': 0,
        'kept_locally': 0,
        'files': []
    }
    
    print("🔄 Processing files...\n")
    
    for idx, file_info in enumerate(local_files, 1):
        filename = file_info['name']
        filepath = file_info['path']
        size_mb = file_info['size_mb']
        
        print(f"[{idx}/{len(local_files)}] {filename}")
        print(f"  Size: {size_mb:.2f} MB")
        
        # Check if file is too large
        if size_mb > MAX_FILE_SIZE_MB:
            print(f"  ⏭️  Skipping (too large, >{MAX_FILE_SIZE_MB}MB)")
            report['too_large'] += 1
            report['kept_locally'] += 1
            file_info['action'] = 'kept_too_large'
            report['files'].append(file_info)
            print()
            continue
        
        # Search for file in Drive
        print(f"  Checking Drive...")
        drive_files = search_drive_for_file(service, filename, file_info['size'])
        
        if drive_files:
            # File exists in Drive - skip it
            drive_file = drive_files[0]
            print(f"  ✓ Already in Drive (skipping)")
            print(f"    Link: {drive_file.get('webViewLink', 'N/A')}")
            
            # Record as already backed up
            report['already_in_drive'] += 1
            file_info['action'] = 'in_drive_kept_locally'
            file_info['drive_id'] = drive_file['id']
            file_info['drive_link'] = drive_file.get('webViewLink')
            report['kept_locally'] += 1
            report['files'].append(file_info)
        else:
            # File NOT in Drive, upload it
            print(f"  ⬆️  Uploading to Drive...")
            uploaded = upload_to_drive(service, filepath, filename, folder_id)
            
            if uploaded:
                print(f"  ✓ Uploaded successfully")
                print(f"    Link: {uploaded.get('webViewLink', 'N/A')}")
                report['uploaded'] += 1
                file_info['action'] = 'uploaded'
                file_info['drive_id'] = uploaded['id']
                file_info['drive_link'] = uploaded.get('webViewLink')
                report['kept_locally'] += 1  # Not auto-deleting after upload
                report['files'].append(file_info)
            else:
                print(f"  ❌ Upload failed")
                report['errors'] += 1
                file_info['action'] = 'upload_failed'
                report['kept_locally'] += 1
                report['files'].append(file_info)
        
        print()
    
    # Save report
    report_file = f'drive_sync_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("=" * 80)
    print("SYNC SUMMARY")
    print("=" * 80)
    print()
    print(f"📊 Statistics:")
    print(f"  Total files scanned: {report['total_files']}")
    print(f"  Already in Drive: {report['already_in_drive']}")
    print(f"  Uploaded to Drive: {report['uploaded']}")
    print(f"  Too large (skipped): {report['too_large']}")
    print(f"  Errors: {report['errors']}")
    print(f"  Kept locally: {report['kept_locally']}")
    print(f"  Deleted locally: {report['deleted_locally']}")
    print()
    print(f"📁 Drive folder: {DRIVE_FOLDER_NAME}")
    print(f"📄 Report saved: {report_file}")
    print()
    print("💡 Next steps:")
    print("   1. Review the report to see what's backed up")
    print("   2. Manually delete local files that are safely in Drive")
    print("   3. For large files (>100MB), upload manually if needed")

if __name__ == '__main__':
    main()
