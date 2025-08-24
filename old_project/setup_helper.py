#!/usr/bin/env python3
"""
Google Drive Setup Helper
Creates the necessary credentials and folder structure
"""

import os
import json
from pathlib import Path

def create_credentials_template():
    """Create a template for Google Drive credentials"""
    
    credentials_template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR-PRIVATE-KEY\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
    }
    
    with open('credentials_template.json', 'w') as f:
        json.dump(credentials_template, f, indent=2)
    
    print("📄 Created credentials_template.json")
    print("   Replace with your actual Google Cloud service account credentials")

def setup_google_cloud_instructions():
    """Print Google Cloud setup instructions"""
    
    instructions = """
🚀 GOOGLE CLOUD SETUP INSTRUCTIONS
================================

1. CREATE GOOGLE CLOUD PROJECT (10 minutes)
   → Go to: https://console.cloud.google.com/
   → Click "New Project"
   → Name: "bmrs-data-collection"
   → Note your Project ID

2. ENABLE APIS (5 minutes)
   → Navigation menu → APIs & Services → Library
   → Enable these APIs:
     • Cloud Run API
     • Cloud Storage API
     • Google Drive API
     • Cloud Build API

3. CREATE SERVICE ACCOUNT (10 minutes)
   → Navigation menu → IAM & Admin → Service Accounts
   → Create Service Account
   → Name: "bmrs-collector"
   → Grant roles:
     • Storage Admin
     • Cloud Run Admin
     • Service Account User
   → Create Key → JSON
   → Download and save as 'credentials.json'

4. SETUP GOOGLE DRIVE (5 minutes)
   → Go to: https://console.cloud.google.com/apis/credentials
   → Create Credentials → OAuth 2.0 Client ID
   → Application type: Desktop application
   → Download client configuration
   → Save as 'drive_credentials.json'

5. DEPLOY TO CLOUD RUN (10 minutes)
   → Update PROJECT_ID in deploy_to_cloud.sh
   → Run: ./deploy_to_cloud.sh

TOTAL TIME: ~40 minutes
"""
    
    print(instructions)
    
    # Create environment template
    env_template = """# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
BMRS_API_KEY=your-bmrs-api-key

# Optional: Google Drive folder ID
DRIVE_FOLDER_ID=your-drive-folder-id
"""
    
    with open('cloud.env.template', 'w') as f:
        f.write(env_template)
    
    print("📄 Created cloud.env.template")
    print("   Copy to cloud.env and fill in your values")

def check_current_setup():
    """Check what's already set up"""
    
    print("🔍 CHECKING CURRENT SETUP")
    print("=" * 30)
    
    checks = [
        ("BMRS API Key", "api.env", "BMRS_API_KEY"),
        ("Google Credentials", "credentials.json", None),
        ("Drive Credentials", "drive_credentials.json", None),
        ("Cloud Config", "cloud.env", "GOOGLE_CLOUD_PROJECT")
    ]
    
    for name, filename, env_var in checks:
        if os.path.exists(filename):
            print(f"✅ {name}: Found {filename}")
            if env_var and filename.endswith('.env'):
                # Check if environment variable is set
                from dotenv import load_dotenv
                load_dotenv(filename)
                if os.getenv(env_var):
                    print(f"   ✅ {env_var} is configured")
                else:
                    print(f"   ⚠️  {env_var} not found in {filename}")
        else:
            print(f"❌ {name}: Missing {filename}")
    
    # Check directory structure
    if os.path.exists('bmrs_data'):
        data_dirs = len([d for d in Path('bmrs_data').iterdir() if d.is_dir()])
        print(f"✅ Data directories: {data_dirs} data type folders created")
    else:
        print("❌ Data directories: Not created yet")

def main():
    """Main setup helper"""
    print("🛠️  GOOGLE CLOUD & DRIVE SETUP HELPER")
    print("=" * 50)
    
    check_current_setup()
    
    print("\nWhat would you like to do?")
    print("1. Show Google Cloud setup instructions")
    print("2. Create credentials templates")
    print("3. Test current configuration")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        setup_google_cloud_instructions()
    elif choice == "2":
        create_credentials_template()
    elif choice == "3":
        # Test with current setup
        try:
            from dotenv import load_dotenv
            load_dotenv('api.env')
            api_key = os.getenv('BMRS_API_KEY')
            
            if api_key:
                print("✅ BMRS API key found - ready for data collection")
                
                if os.path.exists('credentials.json'):
                    print("✅ Google credentials found - ready for cloud deployment")
                else:
                    print("⚠️  Google credentials missing - local collection only")
            else:
                print("❌ BMRS API key missing - please check api.env")
                
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")

if __name__ == "__main__":
    main()
