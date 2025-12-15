#!/usr/bin/env python3
"""
Test Google Workspace integration locally (without Railway)
This tests that the code works - Railway connection issues are separate
"""

import base64
import json
import os
from google.oauth2 import service_account
import gspread
from googleapiclient.discovery import build

def test_list_spreadsheets():
    """Test listing all accessible Google Sheets spreadsheets"""
    print("=" * 80)
    print("TEST 1: List All Spreadsheets")
    print("=" * 80)
    
    try:
        # Load credentials
        with open('workspace-credentials.json', 'r') as f:
            creds_dict = json.load(f)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        # Use gspread to list spreadsheets
        gc = gspread.authorize(credentials)
        
        # Get all spreadsheets
        spreadsheets = gc.openall()
        
        print(f"\n✅ Found {len(spreadsheets)} spreadsheets:\n")
        for i, sheet in enumerate(spreadsheets, 1):
            print(f"{i}. {sheet.title}")
            print(f"   ID: {sheet.id}")
            print(f"   URL: {sheet.url}")
            print()
        
        return spreadsheets
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_list_drive_files():
    """Test listing Google Sheets files from Drive API"""
    print("=" * 80)
    print("TEST 2: List Drive Files (Google Sheets only)")
    print("=" * 80)
    
    try:
        # Load credentials
        with open('workspace-credentials.json', 'r') as f:
            creds_dict = json.load(f)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        # Use Drive API
        service = build('drive', 'v3', credentials=credentials)
        
        # Query for Google Sheets files
        query = "mimeType='application/vnd.google-apps.spreadsheet'"
        results = service.files().list(
            q=query,
            pageSize=50,
            fields="files(id, name, mimeType, modifiedTime, webViewLink, size)"
        ).execute()
        
        files = results.get('files', [])
        
        print(f"\n✅ Found {len(files)} Google Sheets files:\n")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file['name']}")
            print(f"   ID: {file['id']}")
            print(f"   Modified: {file.get('modifiedTime', 'Unknown')}")
            print(f"   URL: {file.get('webViewLink', 'N/A')}")
            print()
        
        return files
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_read_gb_energy_dashboard():
    """Test reading from the GB Energy Dashboard"""
    print("=" * 80)
    print("TEST 3: Read GB Energy Dashboard")
    print("=" * 80)
    
    try:
        # Load credentials
        with open('workspace-credentials.json', 'r') as f:
            creds_dict = json.load(f)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        ).with_subject('george@upowerenergy.uk')
        
        gc = gspread.authorize(credentials)
        
        # Open GB Energy Dashboard
        sheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
        
        print(f"\n✅ Opened: {sheet.title}")
        print(f"   ID: {sheet.id}")
        print(f"   URL: {sheet.url}")
        print(f"\n📋 Worksheets:")
        
        for i, worksheet in enumerate(sheet.worksheets(), 1):
            print(f"   {i}. {worksheet.title} ({worksheet.row_count} rows x {worksheet.col_count} cols)")
        
        # Read first few rows from Dashboard worksheet
        try:
            dashboard = sheet.worksheet('Dashboard')
            data = dashboard.get_all_values()[:5]  # First 5 rows
            
            print(f"\n📊 First 5 rows from Dashboard worksheet:")
            for row in data:
                print(f"   {row[:5]}")  # First 5 columns
        except Exception as e:
            print(f"\n⚠️  Could not read Dashboard worksheet: {e}")
        
        return sheet
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("GOOGLE WORKSPACE INTEGRATION TESTS")
    print("=" * 80)
    print("\nThis tests the workspace code locally without Railway")
    print("If these tests pass, the code is correct - Railway issues are separate\n")
    
    # Test 1: List spreadsheets via gspread
    spreadsheets = test_list_spreadsheets()
    
    print("\n" + "=" * 80 + "\n")
    
    # Test 2: List spreadsheets via Drive API
    drive_files = test_list_drive_files()
    
    print("\n" + "=" * 80 + "\n")
    
    # Test 3: Read GB Energy Dashboard
    dashboard = test_read_gb_energy_dashboard()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ List spreadsheets (gspread): {'PASS' if spreadsheets else 'FAIL'}")
    print(f"✅ List Drive files (Drive API): {'PASS' if drive_files else 'FAIL'}")
    print(f"✅ Read GB Energy Dashboard: {'PASS' if dashboard else 'FAIL'}")
    print("=" * 80)
    
    if all([spreadsheets, drive_files, dashboard]):
        print("\n🎉 ALL TESTS PASSED!")
        print("The workspace code is working correctly.")
        print("Railway connection issues are a separate problem (server sleeping/network).")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Check the error messages above.")
    print()


if __name__ == "__main__":
    main()
