#!/usr/bin/env python3
"""
Google Drive Duplicate File Finder - FAST VERSION
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

# If modifying these scopes, delete the file token.json.
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

def get_all_files(service):
    """Retrieve all files from Google Drive."""
    print("🔍 Scanning Google Drive for all files...")
    
    all_files = []
    page_token = None
    total_files = 0
    
    fields = "nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, owners, md5Checksum, webViewLink)"
    
    while True:
        try:
            results = service.files().list(
                pageSize=1000,
                fields=fields,
                pageToken=page_token,
                q="trashed=false"
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
    
    by_name = defaultdict(list)
    by_size = defaultdict(list)
    by_md5 = defaultdict(list)
    
    for file in files:
        # Skip folders
        if file.get('mimeType') == 'application/vnd.google-apps.folder':
            continue
            
        name = file.get('name', '').lower()
        size = file.get('size')
        md5 = file.get('md5Checksum')
        
        if name:
            by_name[name].append(file)
        if size:
            by_size[size].append(file)
        if md5:
            by_md5[md5].append(file)
    
    name_duplicates = {name: files for name, files in by_name.items() if len(files) > 1}
    size_duplicates = {size: files for size, files in by_size.items() if len(files) > 1}
    md5_duplicates = {md5: files for md5, files in by_md5.items() if len(files) > 1}
    
    print(f"  📝 Files with duplicate names: {len(name_duplicates)}")
    print(f"  📏 Files with same size: {len(size_duplicates)}")
    print(f"  🎯 Exact duplicates (same MD5): {len(md5_duplicates)}")
    
    return name_duplicates, size_duplicates, md5_duplicates

def create_spreadsheet(sheets_service, all_files, name_duplicates, size_duplicates, md5_duplicates):
    """Create a Google Spreadsheet with the file analysis - FAST VERSION."""
    print("\n📊 Creating analysis spreadsheet...")
    
    # Create spreadsheet
    spreadsheet = {
        'properties': {
            'title': f'Google Drive Duplicate Analysis - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        },
        'sheets': [
            {'properties': {'title': 'Summary', 'gridProperties': {'frozenRowCount': 1}}},
            {'properties': {'title': 'Exact Duplicates (MD5)', 'gridProperties': {'frozenRowCount': 1}}},
            {'properties': {'title': 'Same Name', 'gridProperties': {'frozenRowCount': 1}}},
            {'properties': {'title': 'Same Size', 'gridProperties': {'frozenRowCount': 1}}}
        ]
    }
    
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    print(f"  ✅ Created spreadsheet: {spreadsheet_id}")
    
    # Prepare SUMMARY data
    print("  📝 Writing Summary sheet...")
    total_duplicate_files = sum(len(files) for files in md5_duplicates.values())
    potential_space_savings = 0
    
    for md5, files in md5_duplicates.items():
        if len(files) > 1 and files[0].get('size'):
            size_bytes = int(files[0].get('size', 0))
            potential_space_savings += size_bytes * (len(files) - 1)
    
    summary_data = [
        ['Metric', 'Count', 'Details'],
        ['Total Files Scanned', len(all_files), 'All files in your Google Drive'],
        ['', '', ''],
        ['EXACT DUPLICATES (Same MD5 Hash)', '', ''],
        ['Duplicate Groups', len(md5_duplicates), 'Files that are 100% identical'],
        ['Total Duplicate Files', total_duplicate_files, 'Can be safely deleted'],
        ['Potential Space Savings (MB)', round(potential_space_savings / (1024*1024), 2), 'By deleting duplicates'],
        ['', '', ''],
        ['POTENTIAL DUPLICATES', '', ''],
        ['Same Name Groups', len(name_duplicates), 'Files with identical names'],
        ['Same Size Groups', len(size_duplicates), 'Files with same size'],
        ['', '', ''],
        ['RECOMMENDATION', '', ''],
        ['Action', 'Check "Exact Duplicates" sheet', 'These can be safely deleted'],
        ['Caution', 'Review "Same Name" sheet', 'May be duplicates or different versions']
    ]
    
    # Prepare EXACT DUPLICATES data
    print("  🎯 Writing Exact Duplicates sheet...")
    exact_dupes_data = [['Group', 'File Name', 'Size (MB)', 'Created Date', 'Modified Date', 'Link', 'Owner', 'MD5 Hash']]
    
    group_num = 1
    for md5, files in sorted(md5_duplicates.items(), key=lambda x: len(x[1]), reverse=True):
        for file in files:
            size_bytes = int(file.get('size', 0)) if file.get('size') else 0
            size_mb = round(size_bytes / (1024 * 1024), 2)
            
            owners = file.get('owners', [])
            owner_email = owners[0].get('emailAddress', 'Unknown') if owners else 'Unknown'
            
            created = file.get('createdTime', 'Unknown')[:10] if file.get('createdTime') else 'Unknown'
            modified = file.get('modifiedTime', 'Unknown')[:10] if file.get('modifiedTime') else 'Unknown'
            
            exact_dupes_data.append([
                f"Group {group_num}",
                file.get('name', 'Unknown'),
                size_mb,
                created,
                modified,
                file.get('webViewLink', ''),
                owner_email,
                md5[:16] + '...'  # Truncate MD5 for readability
            ])
        group_num += 1
    
    # Prepare SAME NAME data
    print("  📝 Writing Same Name sheet...")
    same_name_data = [['Group', 'File Name', 'Size (MB)', 'Created Date', 'Modified Date', 'Link', 'Owner']]
    
    group_num = 1
    for name, files in sorted(name_duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:500]:  # Limit to 500 groups
        for file in files:
            size_bytes = int(file.get('size', 0)) if file.get('size') else 0
            size_mb = round(size_bytes / (1024 * 1024), 2)
            
            owners = file.get('owners', [])
            owner_email = owners[0].get('emailAddress', 'Unknown') if owners else 'Unknown'
            
            created = file.get('createdTime', 'Unknown')[:10] if file.get('createdTime') else 'Unknown'
            modified = file.get('modifiedTime', 'Unknown')[:10] if file.get('modifiedTime') else 'Unknown'
            
            same_name_data.append([
                f"Group {group_num}",
                file.get('name', 'Unknown'),
                size_mb,
                created,
                modified,
                file.get('webViewLink', ''),
                owner_email
            ])
        group_num += 1
    
    # Prepare SAME SIZE data
    print("  📏 Writing Same Size sheet...")
    same_size_data = [['Group', 'File Name', 'Size (MB)', 'Created Date', 'Modified Date', 'Link', 'Owner']]
    
    group_num = 1
    for size, files in sorted(size_duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:500]:  # Limit to 500 groups
        size_mb = round(int(size) / (1024 * 1024), 2) if size else 0
        
        for file in files:
            owners = file.get('owners', [])
            owner_email = owners[0].get('emailAddress', 'Unknown') if owners else 'Unknown'
            
            created = file.get('createdTime', 'Unknown')[:10] if file.get('createdTime') else 'Unknown'
            modified = file.get('modifiedTime', 'Unknown')[:10] if file.get('modifiedTime') else 'Unknown'
            
            same_size_data.append([
                f"Group {group_num}",
                file.get('name', 'Unknown'),
                size_mb,
                created,
                modified,
                file.get('webViewLink', ''),
                owner_email
            ])
        group_num += 1
    
    # Write all data in batch
    print("  💾 Writing all data to spreadsheet...")
    
    data = [
        {'range': 'Summary!A1', 'values': summary_data},
        {'range': 'Exact Duplicates (MD5)!A1', 'values': exact_dupes_data},
        {'range': 'Same Name!A1', 'values': same_name_data},
        {'range': 'Same Size!A1', 'values': same_size_data}
    ]
    
    body = {'valueInputOption': 'RAW', 'data': data}
    sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    
    # Format headers
    print("  🎨 Formatting spreadsheet...")
    format_requests = []
    
    for sheet_id in range(4):
        format_requests.append({
            'repeatCell': {
                'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1},
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.8},
                        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                        'horizontalAlignment': 'CENTER'
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
            }
        })
        
        # Auto-resize columns
        format_requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 10
                }
            }
        })
    
    body = {'requests': format_requests}
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    
    print(f"  ✅ Spreadsheet complete!")
    return spreadsheet_id

def main():
    """Main execution function."""
    try:
        print("=" * 80)
        print("🔍 GOOGLE DRIVE DUPLICATE FILE FINDER - FAST VERSION")
        print("=" * 80)
        
        creds = get_credentials()
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        all_files = get_all_files(drive_service)
        
        if not all_files:
            print("❌ No files found in Google Drive")
            return
        
        name_duplicates, size_duplicates, md5_duplicates = analyze_duplicates(all_files)
        
        spreadsheet_id = create_spreadsheet(
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
        print(f"\n📊 Spreadsheet: {spreadsheet_url}")
        print(f"\n📈 Summary:")
        print(f"  • Total files: {len(all_files)}")
        print(f"  • Exact duplicate groups: {len(md5_duplicates)}")
        print(f"  • Same name groups: {len(name_duplicates)}")
        print(f"  • Same size groups: {len(size_duplicates)}")
        print("\n💡 Check the 'Exact Duplicates (MD5)' sheet first - these are")
        print("   confirmed identical files that can be safely deleted.\n")
        
    except HttpError as error:
        print(f"❌ An error occurred: {error}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
