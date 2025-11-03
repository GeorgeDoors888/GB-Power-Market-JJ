#!/usr/bin/env python3
"""
Add GB Power Map to Google Sheets Dashboard

This script:
1. Uploads the map HTML to Google Drive
2. Creates a shareable link
3. Adds the link to your Google Sheets dashboard (Sheet1)
4. Optionally creates a new "Maps" sheet with embedded view
"""

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

print("📊 Adding GB Power Map to Dashboard")
print("=" * 50)

# Configuration
SPREADSHEET_ID = '1BaUt8D0v8_nCcH8O4K7XhH4cCXryBfTGHfb0WExI9rE'
MAP_FILE = 'gb_power_complete_map.html'
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Authenticate
print("\n🔐 Authenticating with Google...")

# Try OAuth credentials first
import pickle
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
else:
    print("❌ token.pickle not found!")
    print("Run this first: python3 refresh_token.py")
    exit(1)

# Initialize clients
gc = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

print("✅ Connected to Google Sheets and Drive")

# ============================================================================
# STEP 1: Upload map to Google Drive
# ============================================================================

print(f"\n📤 Step 1: Uploading {MAP_FILE} to Google Drive...")

# Check if file exists
if not os.path.exists(MAP_FILE):
    print(f"❌ Error: {MAP_FILE} not found!")
    print("Run 'python3 create_complete_gb_power_map.py' first")
    exit(1)

file_size_mb = os.path.getsize(MAP_FILE) / (1024 * 1024)
print(f"   File size: {file_size_mb:.1f} MB")

# Check if already uploaded
query = f"name='{MAP_FILE}' and trashed=false"
results = drive_service.files().list(q=query, fields="files(id, name, webViewLink)").execute()
existing_files = results.get('files', [])

if existing_files:
    print(f"   ℹ️  File already exists in Drive, updating...")
    file_id = existing_files[0]['id']
    
    # Update existing file
    media = MediaFileUpload(MAP_FILE, mimetype='text/html', resumable=True)
    updated_file = drive_service.files().update(
        fileId=file_id,
        media_body=media
    ).execute()
    
    web_view_link = existing_files[0].get('webViewLink')
    
else:
    print(f"   📤 Uploading new file...")
    
    # Upload new file
    file_metadata = {
        'name': MAP_FILE,
        'mimeType': 'text/html'
    }
    
    media = MediaFileUpload(MAP_FILE, mimetype='text/html', resumable=True)
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    file_id = uploaded_file.get('id')
    
    # Make file publicly accessible
    drive_service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()
    
    # Get web view link
    file_details = drive_service.files().get(
        fileId=file_id,
        fields='webViewLink'
    ).execute()
    
    web_view_link = file_details.get('webViewLink')

print(f"✅ File uploaded/updated")
print(f"   File ID: {file_id}")
print(f"   Link: {web_view_link}")

# ============================================================================
# STEP 2: Add link to Sheet1
# ============================================================================

print("\n📝 Step 2: Adding map link to Sheet1...")

spreadsheet = None
map_section_row = 40

try:
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet1 = spreadsheet.worksheet('Sheet1')
    
    # Find a good place to add the map link (below existing dashboard content)
    # We'll add it at row 40 to avoid conflicts
    
    map_section_row = 40
    
    # Prepare the data
    map_data = [
        [''],
        ['=== 🗺️ POWER SYSTEM MAPS ==='],
        [''],
        ['GB Power Complete Map', web_view_link],
        ['Description:', 'Interactive map showing:'],
        ['', '• 14 DNO boundaries'],
        ['', '• 18 GSP flow points (live)'],
        ['', '• 35 offshore wind farms (14.3 GW)'],
        ['', '• 8,653 power stations (CVA + SVA)'],
        [''],
        ['Last Updated:', '2 November 2025'],
        ['Regenerate:', 'python3 create_complete_gb_power_map.py'],
    ]
    
    # Write to sheet
    start_cell = f'A{map_section_row}'
    end_cell = f'B{map_section_row + len(map_data) - 1}'
    cell_range = f'{start_cell}:{end_cell}'
    
    sheet1.update(cell_range, map_data)
    
    print(f"✅ Added map section to Sheet1 (rows {map_section_row}-{map_section_row + len(map_data)})")
    
    # Format the header
    from gspread_formatting import (
        format_cell_range,
        CellFormat,
        Color,
        TextFormat
    )
    
    header_format = CellFormat(
        backgroundColor=Color(0.2, 0.7, 0.3),  # Green
        textFormat=TextFormat(bold=True, fontSize=12, foregroundColor=Color(1, 1, 1))
    )
    
    format_cell_range(sheet1, f'A{map_section_row + 1}', header_format)
    
    # Format the hyperlink
    link_format = CellFormat(
        textFormat=TextFormat(underline=True, foregroundColor=Color(0, 0, 1))
    )
    
    format_cell_range(sheet1, f'B{map_section_row + 3}', link_format)
    
    print("✅ Formatted cells")
    
except gspread.exceptions.WorksheetNotFound:
    print("❌ Sheet1 not found in spreadsheet")
except Exception as e:
    print(f"❌ Error updating Sheet1: {e}")

# ============================================================================
# STEP 3: Create dedicated Maps sheet (optional)
# ============================================================================

print("\n📋 Step 3: Creating 'Power Maps' sheet...")

try:
    # Check if sheet exists
    try:
        maps_sheet = spreadsheet.worksheet('Power Maps')
        print("   ℹ️  'Power Maps' sheet already exists, updating...")
        maps_sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print("   📄 Creating new 'Power Maps' sheet...")
        maps_sheet = spreadsheet.add_worksheet(title='Power Maps', rows=100, cols=20)
    
    # Create comprehensive map directory
    maps_content = [
        ['GB POWER SYSTEM MAPS'],
        [''],
        ['📊 Available Maps'],
        [''],
        ['Map Name', 'Description', 'Link', 'Last Updated'],
        [''],
        ['GB Power Complete Map', 
         'Complete view: DNO boundaries, GSP flows, offshore wind, all generators (8,653 sites)',
         web_view_link,
         '2 Nov 2025'],
        [''],
        ['📈 Map Details'],
        [''],
        ['Layer', 'Count', 'Data Source'],
        ['DNO Boundaries', '14 regions', 'dno_regions.geojson'],
        ['GSP Flow Points', '18 points', 'bmrs_indgen + bmrs_inddem (live)'],
        ['Offshore Wind', '35 farms (14.3 GW)', 'offshore_wind_farms table'],
        ['CVA Plants', '1,581 sites', 'cva_plants table'],
        ['SVA Generators', '7,072 sites', 'sva_generators_with_coords table'],
        [''],
        ['🎯 Features'],
        ['• Interactive toggle controls for each layer'],
        ['• Click any element for detailed information'],
        ['• Real-time GSP generation vs demand data'],
        ['• Color-coded by fuel type and flow status'],
        ['• Marker clustering for performance'],
        ['• Dark theme visualization'],
        [''],
        ['🔄 To Update Map'],
        ['1. Run: python3 create_complete_gb_power_map.py'],
        ['2. Re-run this script to upload latest version'],
        [''],
        ['📁 Local Files'],
        ['gb_power_complete_map.html', 'Main map file', '', '3.7 MB'],
        ['create_complete_gb_power_map.py', 'Generator script', '', '15 KB'],
        ['GB_POWER_COMPLETE_MAP_DOCS.md', 'Full documentation', '', '15 KB'],
        ['GB_POWER_MAP_QUICK_REF.md', 'Quick reference', '', '4 KB'],
    ]
    
    maps_sheet.update('A1:D{}'.format(len(maps_content)), maps_content)
    
    # Format the sheet
    from gspread_formatting import (
        format_cell_range,
        CellFormat,
        Color,
        TextFormat
    )
    
    # Title format
    title_format = CellFormat(
        backgroundColor=Color(0.2, 0.4, 0.8),
        textFormat=TextFormat(bold=True, fontSize=16, foregroundColor=Color(1, 1, 1))
    )
    format_cell_range(maps_sheet, 'A1:D1', title_format)
    
    # Section headers
    header_format = CellFormat(
        backgroundColor=Color(0.3, 0.6, 0.3),
        textFormat=TextFormat(bold=True, fontSize=12, foregroundColor=Color(1, 1, 1))
    )
    format_cell_range(maps_sheet, 'A3:D3', header_format)
    format_cell_range(maps_sheet, 'A9:D9', header_format)
    format_cell_range(maps_sheet, 'A18:D18', header_format)
    format_cell_range(maps_sheet, 'A26:D26', header_format)
    format_cell_range(maps_sheet, 'A30:D30', header_format)
    
    # Data headers
    data_header_format = CellFormat(
        backgroundColor=Color(0.9, 0.9, 0.9),
        textFormat=TextFormat(bold=True)
    )
    format_cell_range(maps_sheet, 'A5:D5', data_header_format)
    format_cell_range(maps_sheet, 'A11:C11', data_header_format)
    
    # Hyperlink
    link_format = CellFormat(
        textFormat=TextFormat(underline=True, foregroundColor=Color(0, 0, 1))
    )
    format_cell_range(maps_sheet, 'C7', link_format)
    
    # Set column widths
    maps_sheet.format('A:A', {'columnWidth': 250})
    maps_sheet.format('B:B', {'columnWidth': 400})
    maps_sheet.format('C:C', {'columnWidth': 300})
    maps_sheet.format('D:D', {'columnWidth': 150})
    
    print("✅ 'Power Maps' sheet created and formatted")
    
except Exception as e:
    print(f"❌ Error creating Maps sheet: {e}")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 50)
print("✅ COMPLETE!")
print("=" * 50)
print("\n📍 What was added:")
print(f"   1. Map uploaded to Google Drive")
print(f"      Link: {web_view_link}")
if spreadsheet:
    print(f"   2. Map section added to Sheet1 (row {map_section_row})")
    print(f"   3. New 'Power Maps' sheet created with details")
else:
    print(f"   2. Spreadsheet access failed - add link manually")
print("\n🌐 To view the map:")
print(f"   • Click the link in your Google Sheet")
print(f"   • Or visit: {web_view_link}")
print("\n🔄 To update:")
print("   1. Regenerate map: python3 create_complete_gb_power_map.py")
print("   2. Re-run this script: python3 add_map_to_dashboard.py")
print("\n📚 Documentation:")
print("   • GB_POWER_COMPLETE_MAP_DOCS.md - Full details")
print("   • GB_POWER_MAP_QUICK_REF.md - Quick reference")
print("   • Check 'Power Maps' sheet in your spreadsheet")
