#!/usr/bin/env python3
"""
Grant BigQuery Data Editor permissions to service account
Fixes: 403 Permission bigquery.tables.updateData denied
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import json

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
SERVICE_ACCOUNT_EMAIL = "all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com"
SERVICE_ACCOUNT_FILE = "smart_grid_credentials.json"  # Or service_account.json
ROLE = "roles/bigquery.dataEditor"  # Grants bigquery.tables.updateData permission

def grant_bigquery_permissions():
    """Grant BigQuery Data Editor role to service account"""
    
    print("🔐 Granting BigQuery permissions...")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Service Account: {SERVICE_ACCOUNT_EMAIL}")
    print(f"   Role: {ROLE}")
    print()
    
    try:
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Initialize Resource Manager API
        service = build('cloudresourcemanager', 'v1', credentials=credentials)
        
        # Get current IAM policy
        print("📋 Fetching current IAM policy...")
        policy = service.projects().getIamPolicy(
            resource=PROJECT_ID,
            body={}
        ).execute()
        
        # Check if binding already exists
        member = f"serviceAccount:{SERVICE_ACCOUNT_EMAIL}"
        binding_exists = False
        
        bindings = policy.get('bindings', [])
        
        for binding in bindings:
            if binding['role'] == ROLE:
                if member in binding['members']:
                    print(f"✅ Permission already exists!")
                    print(f"   {SERVICE_ACCOUNT_EMAIL} already has {ROLE}")
                    return True
                else:
                    # Add member to existing role binding
                    binding['members'].append(member)
                    binding_exists = True
                    print(f"➕ Adding to existing {ROLE} binding...")
                    break
        
        # Create new binding if role doesn't exist
        if not binding_exists:
            print(f"➕ Creating new {ROLE} binding...")
            bindings.append({
                'role': ROLE,
                'members': [member]
            })
            policy['bindings'] = bindings
        
        # Update IAM policy
        print("💾 Updating IAM policy...")
        result = service.projects().setIamPolicy(
            resource=PROJECT_ID,
            body={
                'policy': policy
            }
        ).execute()
        
        print()
        print("✅ SUCCESS! Permissions granted:")
        print(f"   ✓ {SERVICE_ACCOUNT_EMAIL}")
        print(f"   ✓ Can now insert/update BigQuery tables")
        print(f"   ✓ bigquery.tables.updateData permission active")
        print()
        print("🔄 Note: May take 1-2 minutes to propagate")
        print()
        
        return True
        
    except HttpError as e:
        print()
        print(f"❌ ERROR: {e}")
        print()
        print("📝 Manual steps required:")
        print(f"   1. Open: https://console.cloud.google.com/iam-admin/iam?project={PROJECT_ID}")
        print(f"   2. Find: {SERVICE_ACCOUNT_EMAIL}")
        print(f"   3. Click: Edit (pencil icon)")
        print(f"   4. Click: ADD ANOTHER ROLE")
        print(f"   5. Select: BigQuery Data Editor")
        print(f"   6. Click: SAVE")
        print()
        return False
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        print()
        return False

def verify_permissions():
    """Verify service account has required permissions"""
    
    print("🔍 Verifying permissions...")
    print()
    
    try:
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Initialize Resource Manager API
        service = build('cloudresourcemanager', 'v1', credentials=credentials)
        
        # Get current IAM policy
        policy = service.projects().getIamPolicy(
            resource=PROJECT_ID,
            body={}
        ).execute()
        
        member = f"serviceAccount:{SERVICE_ACCOUNT_EMAIL}"
        roles = []
        
        for binding in policy.get('bindings', []):
            if member in binding.get('members', []):
                roles.append(binding['role'])
        
        print(f"📋 Roles for {SERVICE_ACCOUNT_EMAIL}:")
        for role in sorted(roles):
            marker = "✅" if role == ROLE else "  "
            print(f"   {marker} {role}")
        
        if ROLE in roles:
            print()
            print("✅ All required permissions present!")
            return True
        else:
            print()
            print(f"❌ Missing: {ROLE}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying: {e}")
        return False

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("  BigQuery Permissions Grant Tool")
    print("=" * 70)
    print()
    
    # Try to grant permissions
    success = grant_bigquery_permissions()
    
    if success:
        print()
        print("-" * 70)
        verify_permissions()
    
    print()
    print("=" * 70)
    print()
