#!/bin/bash
# Guide to share Apps Script with service account for automated deployment

echo "🔧 Apps Script API - Grant Service Account Access"
echo "=================================================="
echo ""
echo "📧 Service Account Email:"
echo "   all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com"
echo ""
echo "🔗 Apps Script Editor:"
echo "   https://script.google.com/d/1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx/edit"
echo ""
echo "=================================================="
echo "OPTION 1: Share via Apps Script Editor"
echo "=================================================="
echo ""
echo "Steps:"
echo "1. Open the Apps Script editor link above"
echo "2. Look for one of these options:"
echo "   - Click the 3-dot menu (⋮) in top right"
echo "   - Click 'Project Settings' (gear icon on left)"
echo "   - Click 'Share' or 'Permissions'"
echo ""
echo "3. Add collaborator:"
echo "   - Click 'Add people' or 'Share with others'"
echo "   - Email: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com"
echo "   - Role: Editor"
echo "   - Uncheck 'Notify people' (service accounts don't get emails)"
echo "   - Click 'Send' or 'Share'"
echo ""
echo "=================================================="
echo "OPTION 2: Share via Google Drive"
echo "=================================================="
echo ""
echo "The Apps Script file also exists in Google Drive."
echo "Let me find it for you..."
echo ""

# Try to find the script in Drive using the API
python3 - << 'PYTHON'
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SA_PATH = "inner-cinema-credentials.json"
SCRIPT_ID = "1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx"

try:
    creds = Credentials.from_service_account_file(
        SA_PATH, 
        scopes=['https://www.googleapis.com/auth/drive']
    )
    drive = build('drive', 'v3', credentials=creds)
    
    # Search for the script file
    query = f"mimeType='application/vnd.google-apps.script'"
    results = drive.files().list(q=query, fields='files(id, name, webViewLink, owners)').execute()
    
    files = results.get('files', [])
    print("📁 Found Apps Script files in Drive:")
    for f in files:
        if f['id'] == SCRIPT_ID:
            print(f"\n✅ FOUND YOUR SCRIPT:")
            print(f"   Name: {f.get('name', 'Unknown')}")
            print(f"   ID: {f['id']}")
            if 'webViewLink' in f:
                print(f"   Link: {f['webViewLink']}")
            if 'owners' in f:
                print(f"   Owner: {f['owners'][0].get('emailAddress', 'Unknown')}")
            print(f"\n🔧 Share this file in Google Drive:")
            print(f"   1. Right-click the file")
            print(f"   2. Click 'Share'")
            print(f"   3. Add: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com")
            print(f"   4. Role: Editor")
            
except Exception as e:
    print(f"⚠️  Could not access Drive: {e}")
    print(f"\nAlternative: Share directly from Apps Script editor")

PYTHON

echo ""
echo "=================================================="
echo "OPTION 3: Use clasp (Google's CLI tool)"
echo "=================================================="
echo ""
echo "1. Install clasp:"
echo "   npm install -g @google/clasp"
echo ""
echo "2. Login:"
echo "   clasp login"
echo ""
echo "3. Open your project:"
echo "   clasp open 1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx"
echo ""
echo "4. Share from web interface that opens"
echo ""
echo "=================================================="
echo "After sharing, test with:"
echo "=================================================="
echo ""
echo "python3 update_existing_script.py"
echo ""
echo "✅ If successful, you'll see:"
echo "   'Successfully updated script content!'"
echo ""
