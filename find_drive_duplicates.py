#!/usr/bin/env python3
"""
Google Drive Duplicate File Finder
Scans all files in Google Drive and creates a spreadsheet listing files with potential duplicates
"""

import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from collections import defaultdict
import json

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

def get_credentials():
    """Get Google API credentials."""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_all_files(service):
    """Retrieve all files from Google Drive."""
    print("🔍 Scanning Google Drive for all files...")
    
    all_files = []
    page_token = None
    total_files = 0
    
    # Fields to retrieve for each file
    fields = "nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, owners, parents, md5Checksum, webViewLink)"
    
    while True:
        try:
            # Query for all files (not just folders)
            results = service.files().list(
                pageSize=1000,
                fields=fields,
                pageToken=page_token,
                q="trashed=false"  # Exclude trashed files
            ).execute()
            
            files = results.get('files', [])
            all_files.extend(files)
            total_files += len(files)
            
            print(f"  📂 Retrieved {total_files} files so far...")
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
                
        except HttpError as error:
            print(f"❌ Error retrieving files: {error}")
            break
    
    print(f"✅ Total files found: {total_files}")
    return all_files

def analyze_duplicates(files):
    """Analyze files to find potential duplicates."""
    print("\n🔍 Analyzing for duplicates...")
    
    # Group files by name (case-insensitive)
    by_name = defaultdict(list)
    # Group files by size
    by_size = defaultdict(list)
    # Group files by MD5 checksum (exact duplicates)
    by_md5 = defaultdict(list)
    
    for file in files:
        name = file.get('name', '').lower()
        size = file.get('size')
        md5 = file.get('md5Checksum')
        
        # Skip folders
        if file.get('mimeType') == 'application/vnd.google-apps.folder':
            continue
        
        if name:
            by_name[name].append(file)
        
        if size:
            by_size[size].append(file)
        
        if md5:
            by_md5[md5].append(file)
    
    # Find duplicates
    name_duplicates = {name: files for name, files in by_name.items() if len(files) > 1}
    size_duplicates = {size: files for size, files in by_size.items() if len(files) > 1}
    md5_duplicates = {md5: files for md5, files in by_md5.items() if len(files) > 1}
    
    print(f"  📝 Files with duplicate names: {len(name_duplicates)}")
    print(f"  📏 Files with same size: {len(size_duplicates)}")
    print(f"  🎯 Exact duplicates (same MD5): {len(md5_duplicates)}")
    
    return name_duplicates, size_duplicates, md5_duplicates

def get_folder_path(service, file_id, parents):
    """Get the folder path for a file."""
    if not parents:
        return "/"
    
    path_parts = []
    current_id = parents[0]
    
    try:
        while current_id:
            folder = service.files().get(fileId=current_id, fields='id, name, parents').execute()
            path_parts.insert(0, folder.get('name', 'Unknown'))
            current_parents = folder.get('parents', [])
            current_id = current_parents[0] if current_parents else None
    except:
        pass
    
    return "/" + "/".join(path_parts) if path_parts else "/"

def create_spreadsheet(service, sheets_service, all_files, name_duplicates, size_duplicates, md5_duplicates):
    """Create a Google Spreadsheet with the file analysis."""
    print("\n📊 Creating analysis spreadsheet...")
    
    # Create new spreadsheet
    spreadsheet = {
        'properties': {
            'title': f'Google Drive Duplicate Analysis - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        },
        'sheets': [
            {'properties': {'title': 'All Files'}},
            {'properties': {'title': 'Exact Duplicates (MD5)'}},
            {'properties': {'title': 'Same Name'}},
            {'properties': {'title': 'Same Size'}},
            {'properties': {'title': 'Summary'}}
        ]
    }
    
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    
    print(f"  ✅ Created spreadsheet: {spreadsheet_id}")
    
    # Prepare data for "All Files" sheet
    all_files_data = [['File Name', 'Type', 'Size (bytes)', 'Size (MB)', 'Created', 'Modified', 'Owner', 'Path', 'Link', 'MD5']]
    
    for file in all_files:
        size_bytes = int(file.get('size', 0)) if file.get('size') else 0
        size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0
        
        owners = file.get('owners', [])
        owner_email = owners[0].get('emailAddress', 'Unknown') if owners else 'Unknown'
        
        path = get_folder_path(service, file.get('id'), file.get('parents', []))
        
        all_files_data.append([
            file.get('name', 'Unknown'),
            file.get('mimeType', 'Unknown'),
            size_bytes,
            size_mb,
            file.get('createdTime', 'Unknown'),
            file.get('modifiedTime', 'Unknown'),
            owner_email,
            path,
            file.get('webViewLink', ''),
            file.get('md5Checksum', 'N/A')
        ])
    
    # Prepare data for "Exact Duplicates" sheet
    exact_dupes_data = [['Group', 'File Name', 'Size (MB)', 'Created', 'Modified', 'Path', 'Link', 'MD5']]
    group_num = 1
    
    for md5, files in md5_duplicates.items():
        for file in files:
            size_bytes = int(file.get('size', 0)) if file.get('size') else 0
            size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0
            path = get_folder_path(service, file.get('id'), file.get('parents', []))
            
            exact_dupes_data.append([
                f"Group {group_num}",
                file.get('name', 'Unknown'),
                size_mb,
                file.get('createdTime', 'Unknown'),
                file.get('modifiedTime', 'Unknown'),
                path,
                file.get('webViewLink', ''),
                md5
            ])
        group_num += 1
    
    # Prepare data for "Same Name" sheet
    same_name_data = [['Group', 'File Name', 'Size (MB)', 'Created', 'Modified', 'Path', 'Link']]
    group_num = 1
    
    for name, files in name_duplicates.items():
        for file in files:
            size_bytes = int(file.get('size', 0)) if file.get('size') else 0
            size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0
            path = get_folder_path(service, file.get('id'), file.get('parents', []))
            
            same_name_data.append([
                f"Group {group_num}",
                file.get('name', 'Unknown'),
                size_mb,
                file.get('createdTime', 'Unknown'),
                file.get('modifiedTime', 'Unknown'),
                path,
                file.get('webViewLink', '')
            ])
        group_num += 1
    
    # Prepare data for "Same Size" sheet
    same_size_data = [['Group', 'File Name', 'Size (MB)', 'Created', 'Modified', 'Path', 'Link']]
    group_num = 1
    
    for size, files in size_duplicates.items():
        size_mb = round(int(size) / (1024 * 1024), 2) if size else 0
        for file in files:
            path = get_folder_path(service, file.get('id'), file.get('parents', []))
            
            same_size_data.append([
                f"Group {group_num}",
                file.get('name', 'Unknown'),
                size_mb,
                file.get('createdTime', 'Unknown'),
                file.get('modifiedTime', 'Unknown'),
                path,
                file.get('webViewLink', '')
            ])
        group_num += 1
    
    # Prepare summary data
    summary_data = [
        ['Metric', 'Count'],
        ['Total Files', len(all_files)],
        ['Files with Duplicate Names', sum(len(files) for files in name_duplicates.values())],
        ['Files with Same Size', sum(len(files) for files in size_duplicates.values())],
        ['Exact Duplicates (MD5)', sum(len(files) for files in md5_duplicates.values())],
        ['Duplicate Name Groups', len(name_duplicates)],
        ['Duplicate Size Groups', len(size_duplicates)],
        ['Exact Duplicate Groups', len(md5_duplicates)]
    ]
    
    # Write data to sheets
    print("  📝 Writing data to spreadsheet...")
    
    requests = [
        {
            'updateCells': {
                'range': {'sheetId': 0, 'startRowIndex': 0, 'startColumnIndex': 0},
                'rows': [{'values': [{'userEnteredValue': {'stringValue': str(cell)}} for cell in row]} for row in all_files_data],
                'fields': 'userEnteredValue'
            }
        },
        {
            'updateCells': {
                'range': {'sheetId': 1, 'startRowIndex': 0, 'startColumnIndex': 0},
                'rows': [{'values': [{'userEnteredValue': {'stringValue': str(cell)}} for cell in row]} for row in exact_dupes_data],
                'fields': 'userEnteredValue'
            }
        },
        {
            'updateCells': {
                'range': {'sheetId': 2, 'startRowIndex': 0, 'startColumnIndex': 0},
                'rows': [{'values': [{'userEnteredValue': {'stringValue': str(cell)}} for cell in row]} for row in same_name_data],
                'fields': 'userEnteredValue'
            }
        },
        {
            'updateCells': {
                'range': {'sheetId': 3, 'startRowIndex': 0, 'startColumnIndex': 0},
                'rows': [{'values': [{'userEnteredValue': {'stringValue': str(cell)}} for cell in row]} for row in same_size_data],
                'fields': 'userEnteredValue'
            }
        },
        {
            'updateCells': {
                'range': {'sheetId': 4, 'startRowIndex': 0, 'startColumnIndex': 0},
                'rows': [{'values': [{'userEnteredValue': {'stringValue': str(cell)}} for cell in row]} for row in summary_data],
                'fields': 'userEnteredValue'
            }
        }
    ]
    
    body = {'requests': requests}
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    
    # Format headers
    format_requests = [
        {
            'repeatCell': {
                'range': {'sheetId': i, 'startRowIndex': 0, 'endRowIndex': 1},
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.8},
                        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        } for i in range(5)
    ]
    
    body = {'requests': format_requests}
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    
    print(f"  ✅ Data written successfully")
    
    return spreadsheet_id

def main():
    """Main execution function."""
    try:
        print("=" * 80)
        print("🔍 GOOGLE DRIVE DUPLICATE FILE FINDER")
        print("=" * 80)
        
        # Get credentials
        creds = get_credentials()
        
        # Build services
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        # Get all files
        all_files = get_all_files(drive_service)
        
        if not all_files:
            print("❌ No files found in Google Drive")
            return
        
        # Analyze for duplicates
        name_duplicates, size_duplicates, md5_duplicates = analyze_duplicates(all_files)
        
        # Create spreadsheet
        spreadsheet_id = create_spreadsheet(
            drive_service, 
            sheets_service, 
            all_files, 
            name_duplicates, 
            size_duplicates, 
            md5_duplicates
        )
        
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Spreadsheet created: {spreadsheet_url}")
        print(f"\n📈 Summary:")
        print(f"  • Total files: {len(all_files)}")
        print(f"  • Exact duplicate groups: {len(md5_duplicates)}")
        print(f"  • Same name groups: {len(name_duplicates)}")
        print(f"  • Same size groups: {len(size_duplicates)}")
        print("\n💡 Check the 'Exact Duplicates (MD5)' sheet for confirmed duplicates")
        print("   that can be safely deleted.\n")
        
    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == '__main__':
    main()
