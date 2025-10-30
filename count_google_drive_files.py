#!/usr/bin/env python3
"""
Count files in a Google Drive folder using the Google Drive API
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_google_drive():
    """Authenticate and return the Google Drive service"""
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
    
    return build('drive', 'v3', credentials=creds)

def extract_folder_id_from_url(url):
    """Extract folder ID from Google Drive URL"""
    # URL format: https://drive.google.com/drive/folders/1DEaLxhIcJ_Mvb6AOno6ZhzbHu6cUh1E4?usp=share_link
    if '/folders/' in url:
        folder_id = url.split('/folders/')[1].split('?')[0]
        return folder_id
    return None

def count_files_in_folder(service, folder_id, include_subfolders=True):
    """Count files in a Google Drive folder"""
    try:
        file_count = 0
        folder_count = 0
        total_size = 0
        file_types = {}
        
        # Get all items in the folder
        query = f"'{folder_id}' in parents and trashed=false"
        
        page_token = None
        while True:
            results = service.files().list(
                q=query,
                pageSize=1000,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)",
                pageToken=page_token
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                mime_type = item.get('mimeType', '')
                
                if mime_type == 'application/vnd.google-apps.folder':
                    folder_count += 1
                    print(f"📁 Folder: {item['name']}")
                    
                    if include_subfolders:
                        # Recursively count files in subfolders
                        sub_count, sub_folders, sub_size, sub_types = count_files_in_folder(
                            service, item['id'], include_subfolders
                        )
                        file_count += sub_count
                        folder_count += sub_folders
                        total_size += sub_size
                        
                        # Merge file types
                        for file_type, count in sub_types.items():
                            file_types[file_type] = file_types.get(file_type, 0) + count
                else:
                    file_count += 1
                    size = int(item.get('size', 0)) if item.get('size') else 0
                    total_size += size
                    
                    # Categorize by file type
                    file_extension = item['name'].split('.')[-1].lower() if '.' in item['name'] else 'no_extension'
                    file_types[file_extension] = file_types.get(file_extension, 0) + 1
                    
                    print(f"📄 File: {item['name']} ({format_size(size)})")
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        return file_count, folder_count, total_size, file_types
        
    except HttpError as error:
        print(f"An error occurred: {error}")
        return 0, 0, 0, {}

def format_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def get_folder_info(service, folder_id):
    """Get basic information about the folder"""
    try:
        folder = service.files().get(fileId=folder_id, fields='name, createdTime, modifiedTime').execute()
        return folder
    except HttpError as error:
        print(f"Error getting folder info: {error}")
        return None

def main():
    # Google Drive folder URL
    drive_url = "https://drive.google.com/drive/folders/1DEaLxhIcJ_Mvb6AOno6ZhzbHu6cUh1E4?usp=share_link"
    
    # Extract folder ID
    folder_id = extract_folder_id_from_url(drive_url)
    if not folder_id:
        print("❌ Could not extract folder ID from URL")
        return
    
    print(f"🔍 Folder ID: {folder_id}")
    
    try:
        # Authenticate with Google Drive
        print("🔐 Authenticating with Google Drive...")
        service = authenticate_google_drive()
        
        # Get folder information
        folder_info = get_folder_info(service, folder_id)
        if folder_info:
            print(f"📁 Folder Name: {folder_info['name']}")
            print(f"📅 Created: {folder_info.get('createdTime', 'Unknown')}")
            print(f"📅 Modified: {folder_info.get('modifiedTime', 'Unknown')}")
        
        print("\n" + "="*50)
        print("📊 COUNTING FILES...")
        print("="*50)
        
        # Count files in the folder
        file_count, folder_count, total_size, file_types = count_files_in_folder(service, folder_id)
        
        print("\n" + "="*50)
        print("📈 SUMMARY REPORT")
        print("="*50)
        print(f"📄 Total Files: {file_count:,}")
        print(f"📁 Total Folders: {folder_count:,}")
        print(f"💾 Total Size: {format_size(total_size)}")
        
        if file_types:
            print("\n📋 File Types:")
            sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
            for file_type, count in sorted_types:
                print(f"   {file_type}: {count:,} files")
        
    except FileNotFoundError:
        print("❌ client_secrets.json file not found!")
        print("💡 Please download your Google Drive API credentials and save as 'client_secrets.json'")
        print("   Get credentials from: https://console.cloud.google.com/apis/credentials")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()