#!/usr/bin/env python3
"""
Set up Application Default Credentials for BigQuery access
This allows BigQuery to use your OAuth credentials automatically
"""

import subprocess
import sys

print("=" * 60)
print("🔐 Setting up Application Default Credentials")
print("=" * 60)
print()
print("This will open a browser to authorize BigQuery access")
print("⚠️  IMPORTANT: Use your SMART GRID Google account")
print()

# Use gcloud auth application-default login
# This creates credentials that BigQuery Client can use automatically
try:
    result = subprocess.run(
        ['gcloud', 'auth', 'application-default', 'login'],
        check=True
    )
    print()
    print("✅ Application Default Credentials set!")
    print()
    print("Now BigQuery will automatically use these credentials")
    print("You can run automated_iris_dashboard.py")
except FileNotFoundError:
    print()
    print("❌ gcloud CLI not installed")
    print()
    print("Alternative: Use the Smart Grid service account file")
    print("  Location: service-account-key.json (needs to be found)")
    print()
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"\n❌ Authentication failed: {e}")
    sys.exit(1)
