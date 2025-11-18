#!/usr/bin/env python3
"""Test if Railway environment variable would work"""

import os
import json
import base64

# Simulate what Railway would have
workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")

if not workspace_creds_base64:
    print("❌ GOOGLE_WORKSPACE_CREDENTIALS not found in environment")
    print("\nTo test, run:")
    print('  export GOOGLE_WORKSPACE_CREDENTIALS=$(base64 -i workspace-credentials.json)')
    print('  python3 test_railway_env.py')
    exit(1)

try:
    # Try to decode
    workspace_creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
    workspace_creds = json.loads(workspace_creds_json)
    
    print("✅ Successfully decoded GOOGLE_WORKSPACE_CREDENTIALS")
    print(f"   Service Account: {workspace_creds.get('client_email')}")
    print(f"   Project ID: {workspace_creds.get('project_id')}")
    print(f"   Client ID: {workspace_creds.get('client_id')}")
    
except Exception as e:
    print(f"❌ Failed to decode: {e}")
    print("\nThe variable might be:")
    print("  - Not base64 encoded")
    print("  - Truncated/corrupted")
    print("  - Missing")
