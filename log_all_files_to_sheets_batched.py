#!/usr/bin/env python3
"""
Log ALL detailed file information from Google Drive folder to Google Sheets (with batch processing)
"""

import os
import pickle
import datetime
import time
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

def authenticate_google_services():
    """Authenticate and return Google Drive and Sheets services"""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    return drive_service, sheets_service

def extract_folder_id_from_url(url):
    """Extract folder ID from Google Drive URL"""
    if '/folders/' in url:
        folder_id = url.split('/folders/')[1].split('?')[0]
        return folder_id
    return None

def format_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def extract_title_from_filename(filename):
    """Extract a clean title from filename by removing file extension and common patterns"""
    import re
    
    # Remove file extension
    title = filename
    if '.' in filename:
        title = '.'.join(filename.split('.')[:-1])
    
    # Replace common separators with spaces
    title = re.sub(r'[-_]+', ' ', title)
    
    # Remove common date patterns (YYYYMMDD, YYYY-MM-DD, etc.)
    title = re.sub(r'\b\d{8}\b', '', title)  # Remove 8-digit dates
    title = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', title)  # Remove YYYY-MM-DD
    title = re.sub(r'\b\d{2}\d{2}\d{2}\d{2}\b', '', title)  # Remove DDMMYYYY
    title = re.sub(r'\b\d{6}\b', '', title)  # Remove 6-digit dates
    
    # Remove common suffixes/prefixes
    title = re.sub(r'\b(final|draft|v\d+|version\s*\d+|signed|unsigned)\b', '', title, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Capitalize first letter of each word for better readability
    title = ' '.join(word.capitalize() for word in title.split() if word)
    
    return title if title else filename

def get_file_details(service, folder_id):
    """Get detailed information about ALL files in a Google Drive folder"""
    try:
        files_data = []
        page_token = None
        files_collected = 0
        
        print(f"🔍 Collecting detailed information for ALL files in the folder...")
        
        while True:
            # Request detailed file information
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='nextPageToken, files(id, name, size, mimeType, createdTime, modifiedTime, owners, lastModifyingUser, webViewLink, parents, fileExtension, originalFilename, description)',
                pageSize=1000,
                pageToken=page_token
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                break
            
            for file_info in files:
                filename = file_info.get('name', '')
                
                # Extract detailed information
                file_data = {
                    'id': file_info.get('id', ''),
                    'name': filename,
                    'title': extract_title_from_filename(filename),
                    'size': int(file_info.get('size', 0)) if file_info.get('size') else 0,
                    'size_formatted': format_size(int(file_info.get('size', 0))) if file_info.get('size') else '0 B',
                    'mime_type': file_info.get('mimeType', ''),
                    'file_extension': file_info.get('fileExtension', ''),
                    'created_time': file_info.get('createdTime', ''),
                    'modified_time': file_info.get('modifiedTime', ''),
                    'web_view_link': file_info.get('webViewLink', ''),
                    'original_filename': file_info.get('originalFilename', ''),
                    'description': file_info.get('description', ''),
                    'owners': ', '.join([owner.get('displayName', owner.get('emailAddress', '')) 
                                       for owner in file_info.get('owners', [])]),
                    'last_modifying_user': file_info.get('lastModifyingUser', {}).get('displayName', 
                                         file_info.get('lastModifyingUser', {}).get('emailAddress', '')),
                }
                
                files_data.append(file_data)
                files_collected += 1
                
                if files_collected % 500 == 0:
                    print(f"📁 Collected {files_collected} files...")
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        print(f"✅ Collected detailed information for {len(files_data)} files")
        return files_data
    
    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        return []

def create_spreadsheet(sheets_service, title="Ofgem ALL Files Analysis"):
    """Create a new spreadsheet"""
    try:
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        
        spreadsheet = sheets_service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId'
        ).execute()
        
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        print(f"✅ Created spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        return spreadsheet_id
    
    except HttpError as error:
        print(f"❌ An error occurred creating spreadsheet: {error}")
        return None

def write_to_spreadsheet_in_batches(sheets_service, spreadsheet_id, files_data, batch_size=1000):
    """Write file data to the spreadsheet in batches to avoid timeouts"""
    try:
        # Prepare headers
        headers = [
            'Document Title',
            'File Name',
            'File Extension', 
            'Size (Bytes)',
            'Size (Formatted)',
            'MIME Type',
            'Created Date',
            'Created Date (ISO)',
            'Modified Date',
            'Modified Date (ISO)',
            'Owners',
            'Last Modified By',
            'Web View Link',
            'Original Filename',
            'Description',
            'File ID'
        ]
        
        # First, write headers
        print("📝 Writing headers...")
        header_body = {'values': [headers]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A1',
            valueInputOption='USER_ENTERED',
            body=header_body
        ).execute()
        
        # Process files in batches
        total_files = len(files_data)
        total_batches = (total_files + batch_size - 1) // batch_size
        
        print(f"📝 Writing {total_files} files in {total_batches} batches of {batch_size}...")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_files)
            batch_files = files_data[start_idx:end_idx]
            
            print(f"   📝 Writing batch {batch_num + 1}/{total_batches} (files {start_idx + 1}-{end_idx})...")
            
            # Prepare batch data
            batch_rows = []
            for file_data in batch_files:
                # Format dates to be more readable
                created_date = ''
                created_date_iso = file_data['created_time']
                modified_date = ''
                modified_date_iso = file_data['modified_time']
                
                if file_data['created_time']:
                    try:
                        created_dt = datetime.datetime.fromisoformat(file_data['created_time'].replace('Z', '+00:00'))
                        created_date = created_dt.strftime('%d %B %Y')  # e.g., "15 March 2024"
                    except:
                        created_date = file_data['created_time']
                
                if file_data['modified_time']:
                    try:
                        modified_dt = datetime.datetime.fromisoformat(file_data['modified_time'].replace('Z', '+00:00'))
                        modified_date = modified_dt.strftime('%d %B %Y')  # e.g., "15 March 2024"
                    except:
                        modified_date = file_data['modified_time']
                
                row = [
                    file_data['title'],
                    file_data['name'],
                    file_data['file_extension'],
                    file_data['size'],
                    file_data['size_formatted'],
                    file_data['mime_type'],
                    created_date,
                    created_date_iso,
                    modified_date,
                    modified_date_iso,
                    file_data['owners'],
                    file_data['last_modifying_user'],
                    file_data['web_view_link'],
                    file_data['original_filename'],
                    file_data['description'],
                    file_data['id']
                ]
                batch_rows.append(row)
            
            # Write batch to spreadsheet
            start_row = 2 + start_idx  # +2 because row 1 is headers and we want 1-indexed
            range_name = f'Sheet1!A{start_row}'
            
            batch_body = {'values': batch_rows}
            
            result = sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=batch_body
            ).execute()
            
            print(f"      ✅ {result.get('updatedCells')} cells updated")
            
            # Small delay between batches to avoid rate limits
            if batch_num < total_batches - 1:  # Don't sleep after the last batch
                time.sleep(1)
        
        print(f"✅ All {total_files} files written to spreadsheet")
        
        # Format the spreadsheet
        num_rows = total_files + 1  # +1 for header
        num_cols = len(headers)
        format_spreadsheet(sheets_service, spreadsheet_id, num_rows, num_cols)
        
        return True
    
    except HttpError as error:
        print(f"❌ An error occurred writing to spreadsheet: {error}")
        return False

def format_spreadsheet(sheets_service, spreadsheet_id, num_rows, num_cols):
    """Format the spreadsheet for better readability"""
    try:
        requests = []
        
        # Freeze header row
        requests.append({
            "updateSheetProperties": {
                "properties": {
                    "sheetId": 0,
                    "gridProperties": {
                        "frozenRowCount": 1
                    }
                },
                "fields": "gridProperties.frozenRowCount"
            }
        })
        
        # Bold header row
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {
                            "bold": True
                        },
                        "backgroundColor": {
                            "red": 0.9,
                            "green": 0.9,
                            "blue": 0.9
                        }
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor)"
            }
        })
        
        # Auto-resize columns
        requests.append({
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": num_cols
                }
            }
        })
        
        body = {
            'requests': requests
        }
        
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
        print("✅ Spreadsheet formatted successfully")
    
    except HttpError as error:
        print(f"❌ An error occurred formatting spreadsheet: {error}")

def main():
    # Target folder URL
    folder_url = "https://drive.google.com/drive/folders/1DEaLxhIcJ_Mvb6AOno6ZhzbHu6cUh1E4?usp=share_link"
    folder_id = extract_folder_id_from_url(folder_url)
    
    if not folder_id:
        print("❌ Could not extract folder ID from URL")
        return
    
    print(f"🎯 Target folder ID: {folder_id}")
    
    try:
        # Authenticate services
        print("🔐 Authenticating Google services...")
        drive_service, sheets_service = authenticate_google_services()
        
        # Get file details for ALL files
        files_data = get_file_details(drive_service, folder_id)
        
        if not files_data:
            print("❌ No files found or error occurred")
            return
        
        # Create spreadsheet
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        spreadsheet_title = f"Ofgem ALL Files Complete Analysis - {timestamp}"
        spreadsheet_id = create_spreadsheet(sheets_service, spreadsheet_title)
        
        if not spreadsheet_id:
            print("❌ Failed to create spreadsheet")
            return
        
        # Write data to spreadsheet in batches
        success = write_to_spreadsheet_in_batches(sheets_service, spreadsheet_id, files_data)
        
        if success:
            print(f"🎉 Successfully logged ALL {len(files_data)} files to Google Sheets!")
            print(f"📊 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            
            # Print summary statistics
            total_size = sum(file_data['size'] for file_data in files_data)
            print(f"\n📈 Summary:")
            print(f"   Files logged: {len(files_data)}")
            print(f"   Total size: {format_size(total_size)}")
            
            # File type breakdown
            file_types = {}
            for file_data in files_data:
                ext = file_data['file_extension'].lower() if file_data['file_extension'] else 'no extension'
                file_types[ext] = file_types.get(ext, 0) + 1
            
            print(f"   File types:")
            for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:15]:
                print(f"     {ext}: {count} files")
        
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()