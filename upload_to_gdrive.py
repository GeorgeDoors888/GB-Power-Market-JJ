#!/usr/bin/env python3
"""Upload CSV to Google Drive"""

import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FILE_PATH = "/home/george/Downloads/property_directors_crm_20251211_1131.csv"

def upload_to_drive():
    creds = None
    token_path = '/home/shared/FullMacBackup/Knowledge Jibber Jabber Bash/token.pickle'
    credentials_path = '/home/shared/FullMacBackup/Knowledge Jibber Jabber Bash/credentials_2.json'
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists(credentials_path):
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        else:
            print(f"❌ Credentials not found at {credentials_path}")
            return None
    
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {'name': 'property_directors_crm_20251211_1131.csv'}
    media = MediaFileUpload(FILE_PATH, mimetype='text/csv', resumable=True)
    
    print("📤 Uploading to Google Drive...")
    file = service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
    
    print(f"\n✅ SUCCESS! File uploaded to Google Drive")
    print(f"📁 File ID: {file.get('id')}")
    print(f"🔗 Link: {file.get('webViewLink')}")
    print(f"\n👉 Open this link on your Mac to download the file!")
    
    return file.get('webViewLink')

if __name__ == '__main__':
    upload_to_drive()
