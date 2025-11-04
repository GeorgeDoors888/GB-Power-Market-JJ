#!/usr/bin/env python3
"""Debug Drive access - test without query."""
import sys
sys.path.insert(0, '/app')

from dotenv import load_dotenv
load_dotenv('/app/.env')

from src.auth.google_auth import drive_client

print("Testing Drive access without query filter...")

client = drive_client()

# Test 1: List ANY files
print("\nTest 1: List ANY files (no filter)")
results = client.files().list(
    pageSize=10,
    fields="files(id, name, mimeType, parents, trashed)"
).execute()
files = results.get('files', [])
print(f"  Found: {len(files)} files")
for f in files[:5]:
    print(f"    - {f['name']} ({f.get('mimeType', '?')})")

# Test 2: List PDFs only
print("\nTest 2: PDFs only")
results = client.files().list(
    q="mimeType='application/pdf'",
    pageSize=10,
    fields="files(id, name, mimeType)"
).execute()
files = results.get('files', [])
print(f"  Found: {len(files)} PDFs")

# Test 3: List documents
print("\nTest 3: Word documents")
results = client.files().list(
    q="mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
    pageSize=10,
    fields="files(id, name, mimeType)"
).execute()
files = results.get('files', [])
print(f"  Found: {len(files)} Word docs")

# Test 4: Full configured query
print("\nTest 4: Full configured query")
query = "mimeType='application/pdf' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation' and trashed=false"
try:
    results = client.files().list(
        q=query,
        pageSize=10,
        fields="files(id, name, mimeType)"
    ).execute()
    files = results.get('files', [])
    print(f"  Found: {len(files)} files")
except Exception as e:
    print(f"  Error: {e}")
