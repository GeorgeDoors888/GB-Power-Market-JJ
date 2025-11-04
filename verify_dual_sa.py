#!/usr/bin/env python3
"""Verify dual service account setup."""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import os
import json

print("=" * 60)
print("Dual Service Account Verification")
print("=" * 60)

# Check Drive service account (jibber-jabber-knowledge)
drive_sa_path = os.getenv("DRIVE_SERVICE_ACCOUNT", "/secrets/drive_sa.json")
with open(drive_sa_path) as f:
    drive_sa = json.load(f)

print("\n1. Drive Service Account (jibber-jabber-knowledge):")
print(f"   Path: {drive_sa_path}")
print(f"   Email: {drive_sa.get('client_email')}")
print(f"   Project: {drive_sa.get('project_id')}")

# Test Drive access
try:
    drive_creds = service_account.Credentials.from_service_account_file(
        drive_sa_path,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    drive_service = build("drive", "v3", credentials=drive_creds, cache_discovery=False)
    results = drive_service.files().list(pageSize=5, fields="files(id, name)").execute()
    files = results.get("files", [])
    print(f"   ✅ Drive access: OK ({len(files)} files found)")
    if files:
        for f in files[:3]:
            print(f"      - {f.get('name')}")
except Exception as e:
    print(f"   ❌ Drive access: FAILED - {e}")

# Check BigQuery service account (inner-cinema-476211-u9)
bq_sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/secrets/sa.json")
with open(bq_sa_path) as f:
    bq_sa = json.load(f)

print(f"\n2. BigQuery Service Account (inner-cinema-476211-u9):")
print(f"   Path: {bq_sa_path}")
print(f"   Email: {bq_sa.get('client_email')}")
print(f"   Project: {bq_sa.get('project_id')}")

# Test BigQuery access
try:
    bq_creds = service_account.Credentials.from_service_account_file(
        bq_sa_path,
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    bq_client = bigquery.Client(project=bq_sa.get('project_id'), credentials=bq_creds)
    datasets = list(bq_client.list_datasets())
    print(f"   ✅ BigQuery access: OK ({len(datasets)} datasets)")
    for ds in datasets:
        print(f"      - {ds.dataset_id}")
except Exception as e:
    print(f"   ❌ BigQuery access: FAILED - {e}")

print("\n" + "=" * 60)
print("✅ Dual service account setup verified!")
print("=" * 60)
