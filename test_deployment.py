#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, "/app")

print("📋 Environment Configuration:")
admin_email = os.environ.get("GOOGLE_WORKSPACE_ADMIN_EMAIL", "NOT SET")
drive_sa = os.environ.get("DRIVE_SERVICE_ACCOUNT", "NOT SET")
print(f"  GOOGLE_WORKSPACE_ADMIN_EMAIL: {admin_email}")
print(f"  DRIVE_SERVICE_ACCOUNT: {drive_sa}")

try:
    from src.utils.drive_safety import DRY_RUN, ENABLE_WRITE_OPERATIONS, MAX_FILES_PER_RUN, PROTECTED_FOLDERS
    print("\n🔒 Safety Settings:")
    print(f"  DRY_RUN: {DRY_RUN}")
    print(f"  WRITE_OPERATIONS: {ENABLE_WRITE_OPERATIONS}")
    print(f"  MAX_FILES: {MAX_FILES_PER_RUN}")
    print(f"  PROTECTED: {PROTECTED_FOLDERS}")
except Exception as e:
    print(f"\n⚠️  Safety module error: {e}")

try:
    from src.auth.google_auth import drive_client
    drive = drive_client()
    print("\n✅ Drive client created successfully")
    print("   Domain-wide delegation will be used if configured in Admin Console")
except Exception as e:
    print(f"\n❌ Drive client error: {e}")
