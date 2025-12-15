#!/usr/bin/env python3
"""
Simple DNO Map Deployment - Creates HTML map accessible via URL
Adds instructions to DNO sheet for accessing the map
"""

import os
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'

def create_standalone_map():
    """Create a standalone HTML map file"""
    
    print("🗺️  Creating standalone DNO map...")
    
    # Read the Apps Script code to extract the HTML
    with open('dno_map_apps_script.gs', 'r') as f:
        script_content = f.read()
    
    # Extract the HTML content (between the backticks)
    html_start = script_content.find('var html = HtmlService.createHtmlOutput(`')
    html_end = script_content.find('`;', html_start)
    
    if html_start == -1 or html_end == -1:
        print("❌ Could not extract HTML from script")
        return None
    
    # Get the HTML content
    html_content = script_content[html_start:html_end]
    # Remove the JavaScript wrapper
    html_content = html_content.replace('var html = HtmlService.createHtmlOutput(`', '')
    html_content = html_content.replace('` + getGeoJSONData() + `', '')
    
    # Read the GeoJSON data
    import json
    with open('uk_dno_license_areas.geojson', 'r') as f:
        geojson_data = json.load(f)
    
    # Create complete HTML file
    complete_html = html_content.replace(
        'var dnoData = ',
        f'var dnoData = {json.dumps(geojson_data, indent=2)}'
    )
    
    # Save to file
    with open('dno_map.html', 'w') as f:
        f.write(complete_html)
    
    print("   ✅ Created dno_map.html")
    return 'dno_map.html'

def add_instructions_to_sheet():
    """Add instructions to the DNO sheet"""
    
    print("\n📝 Adding instructions to DNO sheet...")
    
    # Authenticate
    cred_paths = [
        'inner-cinema-credentials.json',
        os.path.expanduser('~/inner-cinema-credentials.json')
    ]
    
    creds_file = None
    for path in cred_paths:
        if os.path.exists(path):
            creds_file = path
            break
    
    if not creds_file:
        print("❌ Credentials not found")
        return
    
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open sheet
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet('DNO')
    
    # Add instructions at the top
    instructions = [
        ["🗺️ INTERACTIVE DNO MAP - TWO OPTIONS:"],
        [""],
        ["OPTION 1: Apps Script (Best - Interactive in Sheet)"],
        ["1. Go to: Extensions → Apps Script"],
        ["2. Replace Code.gs with content from: dno_map_apps_script.gs"],
        ["3. Save (Ctrl+S) and refresh this sheet"],
        ["4. New menu appears: 🗺️ DNO Map → View Interactive Map"],
        [""],
        ["OPTION 2: Standalone HTML (Works Now)"],
        [f"1. Open file: {os.path.abspath('dno_map.html')}"],
        ["2. Or host online and share URL"],
        [""],
        ["", "", "", "", "", "", ""],  # Spacer
    ]
    
    # Insert at top
    sheet.insert_rows(instructions, 1)
    
    # Format the instructions
    from gspread_formatting import *
    
    # Header formatting
    fmt_header = cellFormat(
        backgroundColor=color(1, 0.6, 0),  # Orange
        textFormat=textFormat(bold=True, fontSize=12, foregroundColor=color(1, 1, 1))
    )
    format_cell_range(sheet, 'A1', fmt_header)
    
    # Option headers
    fmt_option = cellFormat(
        textFormat=textFormat(bold=True, fontSize=11)
    )
    format_cell_range(sheet, 'A3', fmt_option)
    format_cell_range(sheet, 'A8', fmt_option)
    
    print("   ✅ Instructions added to sheet")

def main():
    print("=" * 80)
    print("DNO MAP DEPLOYMENT")
    print("=" * 80)
    
    # Create standalone HTML
    html_file = create_standalone_map()
    
    if html_file:
        print(f"\n✅ Created: {os.path.abspath(html_file)}")
        print("\n🌐 You can open this file in your browser now!")
    
    # Add instructions to sheet
    try:
        add_instructions_to_sheet()
    except Exception as e:
        print(f"\n⚠️  Could not update sheet: {e}")
    
    # Final instructions
    print("\n" + "=" * 80)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 80)
    print("\n📋 NEXT STEPS:")
    print("\n🗺️  IMMEDIATE ACCESS (No Apps Script needed):")
    print(f"   Open in browser: file://{os.path.abspath('dno_map.html')}")
    print("\n🔧 FOR APPS SCRIPT INTEGRATION (Better UX):")
    print(f"   1. Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print("   2. Extensions → Apps Script")
    print("   3. Paste content from: dno_map_apps_script.gs")
    print("   4. Save and refresh spreadsheet")
    print("   5. Use menu: 🗺️ DNO Map → View Interactive Map")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
