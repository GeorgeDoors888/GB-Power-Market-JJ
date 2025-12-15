#!/usr/bin/env python3
"""
Automatic Map Image Uploader for Google Sheets
===============================================
This script:
1. Generates map images from BigQuery data
2. Uploads them to Google Drive with proper permissions
3. Updates Dashboard sheet with IMAGE formulas
4. Handles all authentication properly

Run this manually or via cron for automatic updates.
"""

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.cloud import bigquery
import os
import subprocess

# ============================================================================
# Configuration
# ============================================================================
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
DASHBOARD_SHEET = 'Dashboard'

# Google Drive folder ID (create a folder and get its ID from the URL)
# Format: https://drive.google.com/drive/folders/FOLDER_ID_HERE
DRIVE_FOLDER_ID = None  # Upload to root (no folder) for OAuth compatibility

# Map positions in Dashboard
MAP_POSITIONS = {
    'generators': {'row': 20, 'col': 'J', 'title': '🗺️ Generators Map'},
    'gsp': {'row': 36, 'col': 'J', 'title': '🗺️ GSP Regions'},
    'transmission': {'row': 52, 'col': 'J', 'title': '⚡ Transmission Zones'},
    'dno_boundaries': {'row': 68, 'col': 'J', 'title': '⚡ DNO Boundaries'},
    'combined': {'row': 84, 'col': 'J', 'title': '🗺️ Combined Infrastructure'},
    'wind_capacity': {'row': 100, 'col': 'J', 'title': '🌬️ Wind Farm Capacity Map'}
}

# ============================================================================
# Authentication Setup
# ============================================================================

def get_credentials():
    """Get credentials with all required scopes - use OAuth for Drive uploads"""
    
    # For BigQuery, use service account
    bq_creds = service_account.Credentials.from_service_account_file(
        'arbitrage-bq-key.json',
        scopes=['https://www.googleapis.com/auth/bigquery.readonly']
    )
    
    # For Sheets and Drive, use OAuth user credentials
    try:
        import pickle
        
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        # Check if token.pickle exists
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                oauth_creds = pickle.load(token)
        else:
            # Need to generate OAuth credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            print("\n⚠️ OAuth credentials not found.")
            print("Run this command first:")
            print("   python3 -c 'import gspread; gspread.oauth()'")
            raise Exception("OAuth token not found")
        
        return {
            'bigquery': bq_creds,
            'sheets': oauth_creds,
            'drive': oauth_creds
        }
        
    except Exception as e:
        print(f"❌ OAuth error: {e}")
        raise


def get_sheets_client():
    """Get authenticated Google Sheets client"""
    creds_dict = get_credentials()
    gc = gspread.authorize(creds_dict['sheets'])
    return gc


def get_drive_client():
    """Get authenticated Google Drive client"""
    creds_dict = get_credentials()
    return build('drive', 'v3', credentials=creds_dict['drive'])


def get_bq_client():
    """Get BigQuery client"""
    creds_dict = get_credentials()
    return bigquery.Client(
        project=PROJECT_ID,
        location='US',
        credentials=creds_dict['bigquery']
    )


# ============================================================================
# Map Generation (reuses existing script)
# ============================================================================

def generate_maps():
    """Generate all map files"""
    print("🎨 Generating maps...")
    
    try:
        # Generate simple maps for sheets
        result1 = subprocess.run(
            ['python3', 'create_maps_for_sheets.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Generate boundary maps with GeoJSON
        result2 = subprocess.run(
            ['python3', 'create_boundary_maps.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Generate wind farm capacity map
        result3 = subprocess.run(
            ['python3', 'create_wind_farm_maps.py'],
            capture_output=True,
            text=True,
            timeout=90
        )
        
        if result1.returncode == 0 and result2.returncode == 0 and result3.returncode == 0:
            print("✅ All maps generated successfully")
            return True
        else:
            print(f"❌ Map generation failed")
            if result1.returncode != 0:
                print(f"   Sheets maps: {result1.stderr[:200]}")
            if result2.returncode != 0:
                print(f"   Boundary maps: {result2.stderr[:200]}")
            if result3.returncode != 0:
                print(f"   Wind maps: {result3.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating maps: {e}")
        return False


# ============================================================================
# Google Drive Upload
# ============================================================================

def upload_or_update_file(drive_service, file_path, file_name, folder_id=None):
    """Upload file to Drive or update if exists"""
    
    try:
        # Search for existing file
        query = f"name='{file_name}' and trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        results = drive_service.files().list(
            q=query,
            fields="files(id, name, webViewLink)"
        ).execute()
        
        files = results.get('files', [])
        
        media = MediaFileUpload(file_path, mimetype='image/png', resumable=True)
        
        if files:
            # Update existing file
            file_id = files[0]['id']
            print(f"   Updating: {file_name}")
            
            file = drive_service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            
        else:
            # Create new file
            print(f"   Uploading: {file_name}")
            
            file_metadata = {
                'name': file_name,
                'mimeType': 'image/png'
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            file_id = file.get('id')
            
            # Make publicly accessible
            drive_service.permissions().create(
                fileId=file_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
        
        # Get the direct image URL
        image_url = f"https://drive.google.com/uc?id={file_id}"
        
        print(f"   ✅ {file_name}: {image_url}")
        
        return {
            'id': file_id,
            'url': image_url,
            'name': file_name
        }
        
    except Exception as e:
        print(f"   ❌ Upload failed for {file_name}: {e}")
        return None


def upload_all_maps(drive_service, folder_id=None):
    """Upload all map PNG files to Drive"""
    
    map_files = {
        'generators': 'sheets_generators_map.png',
        'gsp': 'sheets_gsp_regions_map.png',
        'transmission': 'sheets_transmission_map.png',
        'dno_boundaries': 'map_dno_boundaries.png',
        'combined': 'map_combined_boundaries.png',
        'wind_capacity': 'map_wind_capacity.png'
    }
    
    uploaded = {}
    
    print("\n📤 Uploading maps to Google Drive...")
    
    for key, filename in map_files.items():
        if os.path.exists(filename):
            result = upload_or_update_file(drive_service, filename, filename, folder_id)
            if result:
                uploaded[key] = result
        else:
            print(f"   ⚠️ File not found: {filename}")
    
    return uploaded


# ============================================================================
# Google Sheets Update
# ============================================================================

def update_dashboard_with_maps(gc, uploaded_maps):
    """Update Dashboard sheet with IMAGE formulas"""
    
    print("\n📊 Updating Dashboard sheet...")
    
    try:
        sheet = gc.open_by_key(SPREADSHEET_ID)
        dashboard = sheet.worksheet(DASHBOARD_SHEET)
        
        for map_type, position in MAP_POSITIONS.items():
            if map_type in uploaded_maps:
                map_data = uploaded_maps[map_type]
                row = position['row']
                col_letter = position['col']
                
                # Convert column letter to index
                col = ord(col_letter) - ord('A') + 1
                
                # Add title (column I)
                dashboard.update_cell(row, col - 1, position['title'])
                
                # Add IMAGE formula (column J)
                image_formula = f'=IMAGE("{map_data["url"]}", 4, 500, 350)'
                dashboard.update_cell(row, col, image_formula)
                
                # Add metadata (column K)
                from datetime import datetime
                metadata = f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                dashboard.update_cell(row, col + 1, metadata)
                
                print(f"   ✅ Updated {map_type} map at {col_letter}{row}")
        
        print("✅ Dashboard updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Setup Helper
# ============================================================================

def create_drive_folder():
    """Create a folder in Google Drive for map images"""
    
    try:
        drive_service = get_drive_client()
        
        folder_metadata = {
            'name': 'GB Power Market Maps',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = drive_service.files().create(
            body=folder_metadata,
            fields='id, webViewLink'
        ).execute()
        
        folder_id = folder.get('id')
        folder_link = folder.get('webViewLink')
        
        print(f"✅ Folder created!")
        print(f"   ID: {folder_id}")
        print(f"   Link: {folder_link}")
        print(f"\n💡 Add this to your script:")
        print(f"   DRIVE_FOLDER_ID = '{folder_id}'")
        
        return folder_id
        
    except Exception as e:
        print(f"❌ Failed to create folder: {e}")
        return None


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution flow"""
    
    print("=" * 80)
    print("🗺️ AUTOMATIC MAP UPDATER FOR GOOGLE SHEETS")
    print("=" * 80)
    
    # Step 1: Generate maps
    if not generate_maps():
        print("\n❌ Failed to generate maps. Exiting.")
        return False
    
    # Step 2: Initialize clients
    print("\n🔐 Authenticating with Google services...")
    
    try:
        drive_service = get_drive_client()
        gc = get_sheets_client()
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Make sure arbitrage-bq-key.json has these APIs enabled:")
        print("   • Google Sheets API")
        print("   • Google Drive API")
        print("   • BigQuery API")
        return False
    
    # Step 3: Upload maps to Drive
    uploaded = upload_all_maps(drive_service, DRIVE_FOLDER_ID)
    
    if not uploaded:
        print("\n❌ No maps uploaded. Exiting.")
        return False
    
    # Step 4: Update Dashboard
    success = update_dashboard_with_maps(gc, uploaded)
    
    if success:
        print("\n" + "=" * 80)
        print("✅ COMPLETE - Maps updated in Dashboard!")
        print("=" * 80)
        print(f"\n📊 View dashboard: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        return True
    else:
        print("\n❌ Failed to update dashboard")
        return False


def setup_only():
    """Run first-time setup"""
    
    print("=" * 80)
    print("🔧 FIRST-TIME SETUP")
    print("=" * 80)
    
    print("\n1️⃣ Creating Google Drive folder...")
    folder_id = create_drive_folder()
    
    if folder_id:
        print(f"\n2️⃣ Edit this script and set:")
        print(f"   DRIVE_FOLDER_ID = '{folder_id}'")
        print("\n3️⃣ Then run: python3 auto_update_maps.py")
    else:
        print("\n❌ Setup failed")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--setup':
        setup_only()
    else:
        main()
