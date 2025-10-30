#!/usr/bin/env python3
"""
Search Google Drive for DUoS/DNUoS related files.

This script searches the user's Google Drive for any files containing
"DUoS" or "DNUoS" in their name, and lists them with details.

Author: GB Power Market JJ
Date: 2025-10-29
"""

import os
import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

def get_drive_service():
    """Get authenticated Google Drive service."""
    creds = None
    
    # Load credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh if needed
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    if not creds:
        raise Exception("No valid credentials found. Run oauth_with_sheets.py first.")
    
    return build('drive', 'v3', credentials=creds)

def search_drive_for_duos():
    """Search Google Drive for DUoS/DNUoS files."""
    service = get_drive_service()
    
    print("=" * 70)
    print("SEARCHING GOOGLE DRIVE FOR DUoS/DNUoS FILES")
    print("=" * 70)
    print()
    
    # Search queries
    search_terms = [
        "name contains 'DUoS'",
        "name contains 'DNUoS'",
        "name contains 'duos'",
        "name contains 'dnuos'",
        "fullText contains 'DUoS'",
        "fullText contains 'DNUoS'"
    ]
    
    all_files = {}
    
    for query in search_terms:
        print(f"🔍 Searching: {query}")
        
        try:
            # Search with pagination
            page_token = None
            while True:
                response = service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink, parents)',
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                files = response.get('files', [])
                
                # Add to results (use ID as key to avoid duplicates)
                for file in files:
                    file_id = file.get('id')
                    if file_id not in all_files:
                        all_files[file_id] = file
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            print(f"  Found {len(files)} results\n")
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}\n")
    
    print("=" * 70)
    print(f"TOTAL UNIQUE FILES FOUND: {len(all_files)}")
    print("=" * 70)
    print()
    
    if not all_files:
        print("❌ No files found containing 'DUoS' or 'DNUoS'\n")
        return []
    
    # Sort by name
    sorted_files = sorted(all_files.values(), key=lambda x: x.get('name', '').lower())
    
    # Display results
    print("\n📁 FILES FOUND:\n")
    
    for idx, file in enumerate(sorted_files, 1):
        name = file.get('name', 'Unknown')
        file_id = file.get('id', 'N/A')
        mime_type = file.get('mimeType', 'Unknown')
        size = file.get('size', 'N/A')
        modified = file.get('modifiedTime', 'N/A')
        link = file.get('webViewLink', 'N/A')
        
        # Format size
        if size != 'N/A' and size:
            size_int = int(size)
            if size_int < 1024:
                size_str = f"{size_int} B"
            elif size_int < 1024 * 1024:
                size_str = f"{size_int / 1024:.1f} KB"
            else:
                size_str = f"{size_int / (1024 * 1024):.1f} MB"
        else:
            size_str = "N/A"
        
        # Determine file type icon
        if 'spreadsheet' in mime_type:
            icon = "📊"
        elif 'document' in mime_type:
            icon = "📄"
        elif 'pdf' in mime_type:
            icon = "📕"
        elif 'excel' in mime_type or 'sheet' in mime_type.lower():
            icon = "📗"
        elif 'folder' in mime_type:
            icon = "📁"
        elif 'json' in mime_type or name.endswith('.json'):
            icon = "🗂️"
        else:
            icon = "📎"
        
        print(f"{idx}. {icon} {name}")
        print(f"   ID: {file_id}")
        print(f"   Type: {mime_type.split('.')[-1]}")
        print(f"   Size: {size_str}")
        print(f"   Modified: {modified[:10] if len(modified) >= 10 else modified}")
        print(f"   Link: {link}")
        print()
    
    # Summary by file type
    print("=" * 70)
    print("SUMMARY BY FILE TYPE")
    print("=" * 70)
    print()
    
    type_counts = {}
    for file in sorted_files:
        mime_type = file.get('mimeType', 'Unknown')
        type_name = mime_type.split('.')[-1] if '.' in mime_type else mime_type.split('/')[-1]
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
    
    for file_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {file_type}: {count} files")
    
    print()
    
    return sorted_files

def main():
    """Main entry point."""
    try:
        files = search_drive_for_duos()
        
        print("=" * 70)
        print("✅ SEARCH COMPLETE")
        print("=" * 70)
        print()
        
        if files:
            print(f"💡 Found {len(files)} files containing 'DUoS' or 'DNUoS'")
            print()
            print("Next steps:")
            print("  1. Review the files listed above")
            print("  2. Identify which are DUoS charging statements")
            print("  3. Download relevant files for parsing")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure token.pickle exists (run oauth_with_sheets.py)")
        print("  2. Check Drive API is enabled")
        print("  3. Verify OAuth scopes include Drive access")

if __name__ == '__main__':
    main()
