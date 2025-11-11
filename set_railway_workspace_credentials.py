#!/usr/bin/env python3
"""
Set Railway GOOGLE_WORKSPACE_CREDENTIALS environment variable
This fixes the workspace endpoints by uploading the correct credentials
"""

import base64
import json
import subprocess

print("=" * 80)
print("SET RAILWAY WORKSPACE CREDENTIALS")
print("=" * 80)
print()

# Step 1: Read and encode workspace credentials
print("📄 Reading workspace-credentials.json...")
try:
    with open('workspace-credentials.json', 'r') as f:
        creds_json = f.read()
    
    # Verify it's valid JSON
    json.loads(creds_json)
    
    print("✅ Credentials file is valid")
    with open('workspace-credentials.json', 'r') as f:
        creds_dict = json.load(f)
    print(f"   Service Account: {creds_dict['client_email']}")
    print()
except FileNotFoundError:
    print("❌ ERROR: workspace-credentials.json not found!")
    print("   Expected location: ~/GB Power Market JJ/workspace-credentials.json")
    exit(1)
except json.JSONDecodeError:
    print("❌ ERROR: workspace-credentials.json is not valid JSON!")
    exit(1)

# Step 2: Base64 encode
print("🔐 Base64 encoding credentials...")
creds_base64 = base64.b64encode(creds_json.encode()).decode()
print(f"✅ Encoded ({len(creds_base64)} characters)")
print()

# Step 3: Set in Railway
print("🚂 Setting Railway environment variable...")
print("   Running: railway variables set GOOGLE_WORKSPACE_CREDENTIALS=...")
print()

try:
    # Use railway CLI to set the variable
    result = subprocess.run(
        ['railway', 'variables', 'set', f'GOOGLE_WORKSPACE_CREDENTIALS={creds_base64}'],
        cwd='codex-server',
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("✅ SUCCESS! Environment variable set in Railway")
        print()
        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print("1. Railway will auto-redeploy with new credentials")
        print("2. Wait ~30 seconds for deployment to complete")
        print("3. Test the endpoint:")
        print()
        print('   curl -X GET "https://jibber-jabber-production.up.railway.app/workspace/health" \\')
        print('     -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"')
        print()
        print("4. Or test in ChatGPT: 'List all my Google Sheets spreadsheets'")
        print()
    else:
        print("❌ FAILED to set Railway variable")
        print(f"   Error: {result.stderr}")
        print()
        print("=" * 80)
        print("MANUAL FALLBACK")
        print("=" * 80)
        print()
        print("Set the variable manually in Railway dashboard:")
        print()
        print("1. Go to: https://railway.app/project/[your-project]/settings")
        print("2. Click 'Variables' tab")
        print("3. Click '+ New Variable'")
        print("4. Name: GOOGLE_WORKSPACE_CREDENTIALS")
        print("5. Value: (copy the base64 string below)")
        print()
        print("─" * 80)
        print(creds_base64[:100] + "...")
        print("─" * 80)
        print()
        print("Full value saved to: workspace_creds_base64.txt")
        with open('workspace_creds_base64.txt', 'w') as f:
            f.write(creds_base64)
        print()

except FileNotFoundError:
    print("❌ Railway CLI not found or not in correct directory")
    print()
    print("=" * 80)
    print("MANUAL SETUP REQUIRED")
    print("=" * 80)
    print()
    print("Copy this base64 string and add it to Railway manually:")
    print()
    print("1. Go to: https://railway.app/project/[your-project]/settings")
    print("2. Variables tab → + New Variable")
    print("3. Name: GOOGLE_WORKSPACE_CREDENTIALS")
    print("4. Value: (paste the string below)")
    print()
    print("─" * 80)
    print(creds_base64)
    print("─" * 80)
    print()
    print("Also saved to: workspace_creds_base64.txt")
    with open('workspace_creds_base64.txt', 'w') as f:
        f.write(creds_base64)
    print()

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()
    print("Credentials base64 saved to: workspace_creds_base64.txt")
    with open('workspace_creds_base64.txt', 'w') as f:
        f.write(creds_base64)
