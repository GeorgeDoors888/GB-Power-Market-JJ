#!/usr/bin/env python3
"""Search for PDFs recursively in Drive, including inside folders."""
import sys
sys.path.insert(0, '/app')

from dotenv import load_dotenv
load_dotenv('/app/.env')

from src.auth.google_auth import drive_client

print("Searching for PDFs in Drive (including inside folders)...\n")

client = drive_client()

# Get all folders first
print("Step 1: Finding folders...")
folders_result = client.files().list(
    q="mimeType='application/vnd.google-apps.folder' and trashed=false",
    pageSize=20,
    fields="files(id, name)"
).execute()
folders = folders_result.get('files', [])
print(f"  Found {len(folders)} folders")
for folder in folders[:5]:
    print(f"    - {folder['name']}")

# Search for PDFs in each folder
print("\nStep 2: Searching for PDFs in folders...")
total_pdfs = 0
for folder in folders[:10]:  # Check first 10 folders
    query = f"'{folder['id']}' in parents and mimeType='application/pdf' and trashed=false"
    try:
        results = client.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType)"
        ).execute()
        pdfs = results.get('files', [])
        if pdfs:
            print(f"  Folder '{folder['name']}': {len(pdfs)} PDFs")
            total_pdfs += len(pdfs)
            for pdf in pdfs[:3]:
                print(f"    - {pdf['name']}")
    except Exception as e:
        print(f"  Error checking folder '{folder['name']}': {e}")

print(f"\nTotal PDFs found in first 10 folders: {total_pdfs}")

# Try searching ALL Drive for PDFs (not just top-level)
print("\nStep 3: Searching entire Drive for PDFs...")
try:
    all_pdfs = client.files().list(
        q="mimeType='application/pdf' and trashed=false",
        pageSize=100,
        fields="files(id, name, parents)"
    ).execute()
    pdfs = all_pdfs.get('files', [])
    print(f"  Total PDFs in entire Drive: {len(pdfs)}")
    if pdfs:
        print("  First 5 PDFs:")
        for pdf in pdfs[:5]:
            print(f"    - {pdf['name']}")
except Exception as e:
    print(f"  Error: {e}")
