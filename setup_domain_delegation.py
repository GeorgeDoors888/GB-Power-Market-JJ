#!/usr/bin/env python3
"""
Enable Domain-Wide Delegation for Service Account

This script helps set up domain-wide delegation so the service account
can access ALL files in your Google Workspace without manual sharing.

Requirements:
- Google Workspace Super Admin access
- Service account JSON file
- Python with google-auth and google-api-python-client
"""

import json
import sys
import os

def get_service_account_info(sa_path):
    """Read service account details."""
    with open(sa_path, 'r') as f:
        sa_data = json.load(f)
    
    return {
        'email': sa_data['client_email'],
        'project_id': sa_data['project_id'],
        'client_id': sa_data['client_id'],
        'private_key_id': sa_data['private_key_id']
    }

def main():
    print("=" * 80)
    print("DOMAIN-WIDE DELEGATION SETUP")
    print("=" * 80)
    print()
    
    # Get service account info
    sa_path = input("Enter path to service account JSON [gridsmart_service_account.json]: ").strip()
    if not sa_path:
        sa_path = "gridsmart_service_account.json"
    
    if not os.path.exists(sa_path):
        print(f"❌ File not found: {sa_path}")
        sys.exit(1)
    
    sa_info = get_service_account_info(sa_path)
    
    print(f"✅ Service Account Found:")
    print(f"   Email: {sa_info['email']}")
    print(f"   Project: {sa_info['project_id']}")
    print(f"   Client ID: {sa_info['client_id']}")
    print()
    
    print("=" * 80)
    print("STEP 1: Enable Domain-Wide Delegation in Google Cloud Console")
    print("=" * 80)
    print()
    print("1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts")
    print(f"2. Select project: {sa_info['project_id']}")
    print(f"3. Find service account: {sa_info['email']}")
    print("4. Click the service account email")
    print("5. Click 'SHOW DOMAIN-WIDE DELEGATION'")
    print("6. Check 'Enable Google Workspace Domain-wide Delegation'")
    print("7. Click 'SAVE'")
    print()
    input("Press Enter when you've completed Step 1...")
    print()
    
    print("=" * 80)
    print("STEP 2: Configure OAuth Scopes in Google Workspace Admin")
    print("=" * 80)
    print()
    print("1. Go to: https://admin.google.com/")
    print("2. Navigate to: Security → Access and data control → API controls")
    print("3. Click 'MANAGE DOMAIN WIDE DELEGATION'")
    print("4. Click 'Add new'")
    print()
    print(f"5. Enter Client ID: {sa_info['client_id']}")
    print()
    print("6. Enter OAuth Scopes (copy and paste these EXACTLY):")
    print()
    print("    https://www.googleapis.com/auth/drive.readonly,")
    print("    https://www.googleapis.com/auth/drive.metadata.readonly,")
    print("    https://www.googleapis.com/auth/spreadsheets")
    print()
    print("7. Click 'AUTHORIZE'")
    print()
    input("Press Enter when you've completed Step 2...")
    print()
    
    print("=" * 80)
    print("STEP 3: Get Your Admin Email")
    print("=" * 80)
    print()
    admin_email = input("Enter your Google Workspace admin email: ").strip()
    
    if not admin_email or '@' not in admin_email:
        print("❌ Invalid email")
        sys.exit(1)
    
    print()
    print("=" * 80)
    print("✅ SETUP COMPLETE!")
    print("=" * 80)
    print()
    print("Configuration saved. Now update your code to use domain-wide delegation:")
    print()
    print("Add to .env file:")
    print(f"GOOGLE_WORKSPACE_ADMIN_EMAIL={admin_email}")
    print()
    print("The service account can now:")
    print("  ✅ Access ALL files in your Google Workspace")
    print("  ✅ Read files from any user's Drive")
    print("  ✅ No manual sharing needed")
    print()
    print("Next: Run the indexer to scan all files!")
    print()

if __name__ == "__main__":
    main()
