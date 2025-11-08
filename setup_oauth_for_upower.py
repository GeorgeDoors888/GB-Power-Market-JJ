#!/usr/bin/env python3
"""
Setup OAuth credentials for upowerenergy.uk to deploy Apps Script via API
This script will guide you through the process step-by-step
"""

import os
import json
import webbrowser
from pathlib import Path

def main():
    print("=" * 70)
    print("🔐 APPS SCRIPT API SETUP FOR UPOWERENERGY.UK")
    print("=" * 70)
    print()
    
    # Check if oauth_credentials.json exists
    if os.path.exists('oauth_credentials.json'):
        print("✅ Found oauth_credentials.json")
        print()
        choice = input("Do you want to use existing credentials? (y/n): ").lower()
        if choice == 'y':
            print("✅ Using existing OAuth credentials")
            print()
            print("Next step: Run deployment script")
            print("Command: python3 deploy_apps_script_oauth.py")
            return
    
    print("📋 STEP-BY-STEP GUIDE")
    print("=" * 70)
    print()
    
    print("IMPORTANT: You need to do this in a GCP project where upowerenergy.uk")
    print("has Owner or Editor permissions.")
    print()
    
    print("OPTION A: Use existing project 'jibber-jabber-knowledge' (1090450657636)")
    print("  - This is already linked to your Apps Script")
    print("  - You need to enable Apps Script API in this project")
    print()
    
    print("OPTION B: Create new GCP project under upowerenergy.uk")
    print("  - Full control")
    print("  - Clean setup")
    print()
    
    choice = input("Which option? (a/b): ").lower()
    print()
    
    if choice == 'a':
        print("=" * 70)
        print("OPTION A: Using jibber-jabber-knowledge project")
        print("=" * 70)
        print()
        
        project_id = "jibber-jabber-knowledge"
        project_number = "1090450657636"
        
        print(f"Project ID: {project_id}")
        print(f"Project Number: {project_number}")
        print()
        
        print("STEP 1: Enable Apps Script API")
        print("-" * 70)
        api_url = f"https://console.cloud.google.com/apis/library/script.googleapis.com?project={project_id}"
        print(f"Opening: {api_url}")
        print()
        input("Press ENTER to open the API Library... ")
        webbrowser.open(api_url)
        print()
        print("In the browser:")
        print("  1. Make sure you're logged in as upowerenergy.uk")
        print("  2. Click 'ENABLE' button")
        print("  3. Wait for it to enable (10-20 seconds)")
        print()
        input("Press ENTER after you've enabled the API... ")
        print()
        
        print("STEP 2: Create OAuth Credentials")
        print("-" * 70)
        cred_url = f"https://console.cloud.google.com/apis/credentials?project={project_id}"
        print(f"Opening: {cred_url}")
        print()
        input("Press ENTER to open the Credentials page... ")
        webbrowser.open(cred_url)
        print()
        print("In the browser:")
        print("  1. Click '+ CREATE CREDENTIALS' (top of page)")
        print("  2. Select 'OAuth client ID'")
        print()
        print("  IF PROMPTED TO CONFIGURE CONSENT SCREEN:")
        print("    a. Click 'CONFIGURE CONSENT SCREEN'")
        print("    b. Select 'External' (or 'Internal' if available)")
        print("    c. Click 'CREATE'")
        print("    d. Fill in:")
        print("       - App name: 'UPower Apps Script Deployer'")
        print("       - User support email: (your upowerenergy.uk email)")
        print("       - Developer contact: (your upowerenergy.uk email)")
        print("    e. Click 'SAVE AND CONTINUE' three times")
        print("    f. Click 'BACK TO DASHBOARD'")
        print("    g. Go back to Credentials tab")
        print("    h. Click '+ CREATE CREDENTIALS' → 'OAuth client ID' again")
        print()
        print("  3. Application type: Select 'Desktop app'")
        print("  4. Name: 'Apps Script Deployer'")
        print("  5. Click 'CREATE'")
        print("  6. Click 'DOWNLOAD JSON' (download icon on the right)")
        print()
        input("Press ENTER after you've downloaded the JSON file... ")
        print()
        
    else:  # Option B
        print("=" * 70)
        print("OPTION B: Create new GCP project")
        print("=" * 70)
        print()
        
        print("Opening GCP Console...")
        webbrowser.open("https://console.cloud.google.com/projectcreate")
        print()
        print("In the browser:")
        print("  1. Make sure you're logged in as upowerenergy.uk")
        print("  2. Project name: 'UPower Apps Script Deployer'")
        print("  3. Location: (your organization)")
        print("  4. Click 'CREATE'")
        print("  5. Wait for project creation (20-30 seconds)")
        print()
        project_id = input("Enter the project ID that was created: ").strip()
        print()
        
        print("STEP 1: Enable Apps Script API")
        print("-" * 70)
        api_url = f"https://console.cloud.google.com/apis/library/script.googleapis.com?project={project_id}"
        print(f"Opening: {api_url}")
        print()
        input("Press ENTER to open the API Library... ")
        webbrowser.open(api_url)
        print()
        print("Click 'ENABLE' and wait...")
        input("Press ENTER after API is enabled... ")
        print()
        
        print("STEP 2: Create OAuth Credentials")
        print("-" * 70)
        cred_url = f"https://console.cloud.google.com/apis/credentials?project={project_id}"
        print(f"Opening: {cred_url}")
        print()
        input("Press ENTER to open Credentials page... ")
        webbrowser.open(cred_url)
        print()
        print("Follow the same steps as Option A above...")
        input("Press ENTER after downloading credentials JSON... ")
        print()
    
    print("=" * 70)
    print("STEP 3: Save the credentials file")
    print("=" * 70)
    print()
    print("The file you downloaded is named something like:")
    print("  client_secret_XXXXX.apps.googleusercontent.com.json")
    print()
    print("You need to:")
    print("  1. Rename it to: oauth_credentials.json")
    print("  2. Move it to this folder:")
    print(f"     {os.getcwd()}/oauth_credentials.json")
    print()
    input("Press ENTER after you've moved the file... ")
    print()
    
    # Check if file exists now
    if os.path.exists('oauth_credentials.json'):
        print("✅ Found oauth_credentials.json!")
        print()
        
        # Validate it's a valid OAuth credential file
        try:
            with open('oauth_credentials.json', 'r') as f:
                creds = json.load(f)
                if 'installed' in creds or 'web' in creds:
                    print("✅ Credentials file is valid!")
                    print()
                else:
                    print("⚠️  Warning: This doesn't look like an OAuth credential file")
                    print()
        except:
            print("⚠️  Warning: Could not parse credentials file")
            print()
        
        print("=" * 70)
        print("🎉 SETUP COMPLETE!")
        print("=" * 70)
        print()
        print("Next step: Run the deployment script")
        print()
        print("Command:")
        print("  python3 deploy_apps_script_oauth.py")
        print()
        print("What will happen:")
        print("  1. Browser will open")
        print("  2. Login with upowerenergy.uk account")
        print("  3. Click 'Allow' to authorize")
        print("  4. Script will automatically update your Apps Script")
        print("  5. Done! Future updates take 5 seconds")
        print()
        
    else:
        print("❌ oauth_credentials.json not found")
        print()
        print("Please:")
        print("  1. Find the downloaded JSON file")
        print("  2. Rename it to: oauth_credentials.json")
        print("  3. Move it to: " + os.getcwd())
        print("  4. Run this script again")
        print()

if __name__ == "__main__":
    main()
