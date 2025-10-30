#!/usr/bin/env python3
"""
SAFE Google Drive Duplicate Finder - Memory Efficient Version
Processes files in batches to avoid overwhelming the system
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime
from collections import defaultdict
import time

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

def get_credentials():
    """Get Google API credentials."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_all_files_simple(service):
    """Retrieve all files with minimal data to avoid memory issues."""
    print("🔍 Scanning Google Drive...")
    
    all_files = []
    page_token = None
    batch_num = 0
    
    # Only get essential fields
    fields = "nextPageToken, files(id, name, mimeType, size, md5Checksum, webViewLink, modifiedTime)"
    
    while True:
        batch_num += 1
        print(f"  Batch {batch_num}... ", end='', flush=True)
        
        try:
            results = service.files().list(
                pageSize=500,  # Smaller batches
                fields=fields,
                pageToken=page_token,
                q="trashed=false"
            ).execute()
            
            files = results.get('files', [])
            all_files.extend(files)
            print(f"✓ {len(files)} files (Total: {len(all_files)})")
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
            
            time.sleep(0.5)  # Rate limiting
                
        except Exception as error:
            print(f"\n❌ Error: {error}")
            break
    
    print(f"\n✅ Scan complete: {len(all_files)} files found")
    return all_files

def find_duplicates_simple(files):
    """Find duplicates by MD5 and name only."""
    print("\n🔍 Analyzing duplicates...")
    
    by_md5 = defaultdict(list)
    by_name = defaultdict(list)
    
    for file in files:
        if file.get('mimeType') == 'application/vnd.google-apps.folder':
            continue
        
        md5 = file.get('md5Checksum')
        name = file.get('name', '').lower()
        
        if md5:
            by_md5[md5].append(file)
        if name:
            by_name[name].append(file)
    
    exact_dupes = {md5: files for md5, files in by_md5.items() if len(files) > 1}
    name_dupes = {name: files for name, files in by_name.items() if len(files) > 1}
    
    print(f"  🎯 Exact duplicates: {len(exact_dupes)} groups")
    print(f"  📝 Same name: {len(name_dupes)} groups")
    
    return exact_dupes, name_dupes

def create_simple_spreadsheet(sheets_service, all_files, exact_dupes, name_dupes):
    """Create spreadsheet with summary and duplicate lists."""
    print("\n📊 Creating spreadsheet...")
    
    spreadsheet = {
        'properties': {
            'title': f'Drive Duplicates - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        },
        'sheets': [
            {'properties': {'title': 'Summary'}},
            {'properties': {'title': 'Exact Duplicates'}},
            {'properties': {'title': 'Same Name'}}
        ]
    }
    
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    
    # Summary data
    total_dupe_files_exact = sum(len(files) for files in exact_dupes.values())
    total_dupe_files_name = sum(len(files) for files in name_dupes.values())
    
    summary_data = [
        ['Metric', 'Count'],
        ['Total Files Scanned', len(all_files)],
        ['Exact Duplicate Groups', len(exact_dupes)],
        ['Exact Duplicate Files', total_dupe_files_exact],
        ['Same Name Groups', len(name_dupes)],
        ['Same Name Files', total_dupe_files_name],
        ['', ''],
        ['💡 Focus on "Exact Duplicates" sheet', ''],
        ['These files are identical and can be safely deleted', '']
    ]
    
    # Exact duplicates data
    exact_data = [['Group #', 'File Name', 'Size (MB)', 'Modified', 'Link', 'MD5']]
    group_num = 1
    for md5, files in exact_dupes.items():
        for file in files:
            size_bytes = int(file.get('size', 0)) if file.get('size') else 0
            size_mb = round(size_bytes / (1024 * 1024), 2)
            
            exact_data.append([
                group_num,
                file.get('name', 'Unknown'),
                size_mb,
                file.get('modifiedTime', 'Unknown'),
                file.get('webViewLink', ''),
                md5[:16] + '...'  # Truncate for readability
            ])
        group_num += 1
    
    # Same name data
    name_data = [['Group #', 'File Name', 'Size (MB)', 'Modified', 'Link']]
    group_num = 1
    for name, files in name_dupes.items():
        for file in files:
            size_bytes = int(file.get('size', 0)) if file.get('size') else 0
            size_mb = round(size_bytes / (1024 * 1024), 2)
            
            name_data.append([
                group_num,
                file.get('name', 'Unknown'),
                size_mb,
                file.get('modifiedTime', 'Unknown'),
                file.get('webViewLink', '')
            ])
        group_num += 1
    
    print("  Writing data...")
    
    # Write data in batches
    def write_data(sheet_id, data):
        rows = [{'values': [{'userEnteredValue': {'stringValue': str(cell)}} for cell in row]} for row in data]
        request = {
            'updateCells': {
                'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'startColumnIndex': 0},
                'rows': rows,
                'fields': 'userEnteredValue'
            }
        }
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [request]}
        ).execute()
    
    write_data(0, summary_data)
    write_data(1, exact_data)
    write_data(2, name_data)
    
    # Format headers
    format_requests = [{
        'repeatCell': {
            'range': {'sheetId': i, 'startRowIndex': 0, 'endRowIndex': 1},
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.8},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                }
            },
            'fields': 'userEnteredFormat'
        }
    } for i in range(3)]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': format_requests}
    ).execute()
    
    print(f"  ✅ Spreadsheet created")
    return spreadsheet_id

def main():
    print("=" * 60)
    print("🔍 SAFE GOOGLE DRIVE DUPLICATE FINDER")
    print("=" * 60)
    
    try:
        creds = get_credentials()
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        all_files = get_all_files_simple(drive_service)
        
        if not all_files:
            print("❌ No files found")
            return
        
        exact_dupes, name_dupes = find_duplicates_simple(all_files)
        
        spreadsheet_id = create_simple_spreadsheet(sheets_service, all_files, exact_dupes, name_dupes)
        
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        
        print("\n" + "=" * 60)
        print("✅ COMPLETE!")
        print("=" * 60)
        print(f"\n📊 Spreadsheet: {url}")
        print(f"\n💡 Check 'Exact Duplicates' sheet for files to delete\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
