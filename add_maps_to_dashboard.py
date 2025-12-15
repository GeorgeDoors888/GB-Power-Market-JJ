#!/usr/bin/env python3
"""
Upload map images to Google Drive and add to Dashboard sheet
"""

import gspread
from google.oauth2.service_account import Credentials as ServiceCreds
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

# ============================================================================
# Configuration
# ============================================================================
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Dashboard'

# Map files
MAP_FILES = {
    'Generators Map': 'sheets_generators_map.png',
    'GSP Regions Map': 'sheets_gsp_regions_map.png',
    'Transmission Map': 'sheets_transmission_map.png'
}

# ============================================================================
# Google Drive Upload
# ============================================================================

def upload_to_drive(file_path, file_name):
    """Upload image to Google Drive and get shareable link"""
    try:
        # Use existing credentials
        SCOPES = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        
        creds = ServiceCreds.from_service_account_file(
            'arbitrage-bq-key.json',
            scopes=SCOPES
        )
        
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Check if file already exists
        query = f"name='{file_name}' and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if files:
            # Update existing file
            file_id = files[0]['id']
            print(f"   Updating existing file: {file_name}")
            media = MediaFileUpload(file_path, mimetype='image/png')
            file = drive_service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
        else:
            # Create new file
            print(f"   Uploading new file: {file_name}")
            file_metadata = {
                'name': file_name,
                'mimeType': 'image/png'
            }
            media = MediaFileUpload(file_path, mimetype='image/png')
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = file.get('id')
        
        # Make file publicly accessible
        drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        # Get shareable link
        link = f"https://drive.google.com/uc?id={file_id}"
        print(f"   ✅ Uploaded: {link}")
        
        return link, file_id
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return None, None


# ============================================================================
# Google Sheets Integration
# ============================================================================

def add_maps_to_dashboard():
    """Add map images and links to Dashboard sheet"""
    print("\n📊 Adding maps to Dashboard sheet...")
    
    try:
        # Connect to Google Sheets
        gc = gspread.oauth(
            credentials_filename='arbitrage-bq-key.json',
            authorized_user_filename='token.pickle'
        )
        sheet = gc.open_by_key(SPREADSHEET_ID)
        dashboard = sheet.worksheet(SHEET_NAME)
        
        # Find empty space for maps (right side of dashboard)
        # Add to columns J-L starting at row 20
        start_row = 20
        start_col = 10  # Column J
        
        print(f"   Adding maps starting at row {start_row}, column J")
        
        row = start_row
        uploaded_maps = []
        
        for map_name, file_path in MAP_FILES.items():
            if os.path.exists(file_path):
                print(f"\n   Processing: {map_name}")
                
                # Upload to Drive
                drive_link, file_id = upload_to_drive(file_path, file_path)
                
                if drive_link:
                    uploaded_maps.append({
                        'name': map_name,
                        'link': drive_link,
                        'file_id': file_id,
                        'row': row
                    })
                    
                    # Add map title
                    dashboard.update_cell(row, start_col, f"🗺️ {map_name}")
                    
                    # Add IMAGE formula
                    image_formula = f'=IMAGE("{drive_link}", 4, 400, 300)'
                    dashboard.update_cell(row, start_col + 1, image_formula)
                    
                    # Add clickable link to interactive HTML
                    html_file = file_path.replace('.png', '.html')
                    abs_html = os.path.abspath(html_file)
                    link_formula = f'=HYPERLINK("file://{abs_html}", "📂 Open Interactive")'
                    dashboard.update_cell(row, start_col + 2, link_formula)
                    
                    row += 15  # Space between maps
                    
        print(f"\n   ✅ Added {len(uploaded_maps)} maps to Dashboard")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📋 MAP SUMMARY")
        print("=" * 80)
        for m in uploaded_maps:
            print(f"\n{m['name']}:")
            print(f"   Row: {m['row']}")
            print(f"   Drive ID: {m['file_id']}")
            print(f"   URL: {m['link']}")
        
        return uploaded_maps
        
    except Exception as e:
        print(f"❌ Failed to add maps to sheet: {e}")
        return []


# ============================================================================
# Alternative: Just print formulas
# ============================================================================

def print_manual_instructions():
    """Print manual instructions for adding maps"""
    print("\n" + "=" * 80)
    print("📝 MANUAL SETUP INSTRUCTIONS")
    print("=" * 80)
    
    print("\n1️⃣ Upload PNG files to Google Drive:")
    print("   • Open drive.google.com")
    print("   • Upload these files:")
    for name, file in MAP_FILES.items():
        if os.path.exists(file):
            print(f"     - {file}")
    
    print("\n2️⃣ Get shareable links:")
    print("   • Right-click each file → Share → Change to 'Anyone with link'")
    print("   • Copy the link (looks like: https://drive.google.com/file/d/FILE_ID/view)")
    print("   • Extract FILE_ID from the link")
    
    print("\n3️⃣ Add to Google Sheets:")
    print("   • Open your Dashboard sheet")
    print("   • In an empty cell, paste this formula:")
    print('     =IMAGE("https://drive.google.com/uc?id=YOUR_FILE_ID", 4, 400, 300)')
    print("   • Replace YOUR_FILE_ID with the actual ID from step 2")
    print("   • Repeat for each map")
    
    print("\n4️⃣ Add interactive map links:")
    print("   • In adjacent cells, add hyperlinks to HTML files:")
    for name, file in MAP_FILES.items():
        html_file = file.replace('.png', '.html')
        abs_path = os.path.abspath(html_file)
        print(f'     =HYPERLINK("file://{abs_path}", "🗺️ {name}")')


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("🗺️ ADDING MAPS TO GOOGLE SHEETS DASHBOARD")
    print("=" * 80)
    
    # Check if map files exist
    print("\n📂 Checking for map files...")
    missing = []
    for name, file in MAP_FILES.items():
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - NOT FOUND")
            missing.append(file)
    
    if missing:
        print("\n⚠️ Some map files are missing. Run create_maps_for_sheets.py first!")
        return
    
    # Try automatic upload
    print("\n🚀 Attempting automatic upload to Google Drive...")
    try:
        uploaded = add_maps_to_dashboard()
        
        if uploaded:
            print("\n✅ Maps successfully added to Dashboard!")
            print("\n💡 View your dashboard:")
            print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        else:
            print("\n⚠️ Automatic upload failed. Using manual method...")
            print_manual_instructions()
    
    except Exception as e:
        print(f"\n⚠️ Automatic upload failed: {e}")
        print("\nℹ️ No problem! Here's how to do it manually:")
        print_manual_instructions()


if __name__ == '__main__':
    main()
