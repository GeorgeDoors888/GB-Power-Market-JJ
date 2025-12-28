#!/usr/bin/env python3
"""
Automatically update Google My Maps with latest DNO boundary data
Uses Google Drive API to upload KML, then reference in My Maps
"""

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pickle
from datetime import datetime

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_drive():
    """Authenticate with Google Drive API"""
    creds = None
    token_file = 'drive_token.pickle'
    
    # Load existing credentials
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def upload_kml_to_drive(service, kml_file, folder_id=None):
    """Upload KML file to Google Drive"""
    print(f'📤 Uploading {kml_file} to Google Drive...')
    
    file_metadata = {
        'name': f'DNO_Boundaries_{datetime.now().strftime("%Y%m%d_%H%M")}.kml',
        'mimeType': 'application/vnd.google-earth.kml+xml'
    }
    
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(kml_file, mimetype='application/vnd.google-earth.kml+xml')
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    print(f'✅ Uploaded to Drive: {file.get("name")}')
    print(f'   ID: {file.get("id")}')
    print(f'   Link: {file.get("webViewLink")}')
    
    return file

def update_my_maps():
    """Main function to update Google My Maps"""
    kml_file = 'dno_boundaries.kml'
    
    if not os.path.exists(kml_file):
        print(f'❌ KML file not found: {kml_file}')
        print('   Run: python3 export_dno_for_google_maps.py')
        return
    
    try:
        # Authenticate
        service = authenticate_drive()
        
        # Upload KML to Drive
        file = upload_kml_to_drive(service, kml_file)
        
        print('\n📍 Next steps:')
        print('1. Go to: https://www.google.com/maps/d/u/1/edit?mid=1gdoE5utNiBKNznH-j4v58-Zjg19SAwc')
        print('2. Click "Add layer" → "Import"')
        print('3. Select "Google Drive" tab')
        print(f'4. Find file: {file.get("name")}')
        print('5. Import and replace old layer')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        print('\n⚙️  First-time setup required:')
        print('1. Go to: https://console.cloud.google.com/apis/credentials')
        print('2. Create OAuth 2.0 Client ID (Desktop app)')
        print('3. Download as client_credentials.json')
        print('4. Re-run this script')

if __name__ == '__main__':
    update_my_maps()
