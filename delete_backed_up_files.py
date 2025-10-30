#!/usr/bin/env python3
"""
Delete local files that are safely backed up in Google Drive.
Uses the sync report to identify which files to delete.
"""

import json
import os
from pathlib import Path

def load_sync_report():
    """Load the most recent sync report."""
    reports = sorted(Path('.').glob('drive_sync_report_*.json'))
    if not reports:
        print("❌ No sync report found!")
        return None
    
    latest_report = reports[-1]
    print(f"📄 Loading report: {latest_report}")
    
    with open(latest_report, 'r') as f:
        return json.load(f)

def get_files_to_delete(report):
    """Get list of files that are safely in Drive and can be deleted."""
    files_to_delete = []
    total_size = 0
    
    for file_info in report['files']:
        # Only delete files that are confirmed in Drive
        if file_info['action'] in ['in_drive_kept_locally', 'uploaded']:
            filepath = file_info['path']
            if os.path.exists(filepath):
                size = file_info['size']
                files_to_delete.append({
                    'path': filepath,
                    'name': file_info['name'],
                    'size': size,
                    'size_mb': file_info['size_mb'],
                    'drive_link': file_info.get('drive_link', 'N/A')
                })
                total_size += size
    
    return files_to_delete, total_size

def main():
    print("=" * 80)
    print("DELETE BACKED UP FILES")
    print("=" * 80)
    print()
    
    # Load sync report
    report = load_sync_report()
    if not report:
        return
    
    print()
    print(f"📊 Report Summary:")
    print(f"  Total files scanned: {report['total_files']}")
    print(f"  Already in Drive: {report['already_in_drive']}")
    print(f"  Uploaded to Drive: {report['uploaded']}")
    print()
    
    # Get files to delete
    files_to_delete, total_size = get_files_to_delete(report)
    
    if not files_to_delete:
        print("✅ No files to delete (all files are safe)")
        return
    
    total_size_mb = total_size / (1024 * 1024)
    total_size_gb = total_size / (1024 * 1024 * 1024)
    
    print(f"🗑️  Files eligible for deletion:")
    print(f"  Count: {len(files_to_delete)} files")
    print(f"  Total size: {total_size_mb:.2f} MB ({total_size_gb:.2f} GB)")
    print()
    
    # Show largest files
    print("📦 Top 10 largest files to delete:")
    sorted_files = sorted(files_to_delete, key=lambda x: x['size'], reverse=True)
    for i, file in enumerate(sorted_files[:10], 1):
        print(f"  {i:2d}. {file['name']:50s} {file['size_mb']:8.2f} MB")
    print()
    
    # Confirmation
    print("⚠️  WARNING: This will permanently delete local files!")
    print("   All files are backed up in Google Drive folder: GB Power Market JJ Backup")
    print()
    response = input("Are you sure you want to delete these files? (type 'yes' to confirm): ")
    
    if response.lower() != 'yes':
        print("❌ Deletion cancelled")
        return
    
    print()
    print("🗑️  Deleting files...")
    deleted_count = 0
    deleted_size = 0
    errors = []
    
    for file in files_to_delete:
        try:
            os.remove(file['path'])
            deleted_count += 1
            deleted_size += file['size']
            if deleted_count % 50 == 0:
                print(f"  Deleted {deleted_count}/{len(files_to_delete)} files...")
        except Exception as e:
            errors.append(f"{file['name']}: {e}")
    
    print()
    print("=" * 80)
    print("DELETION COMPLETE")
    print("=" * 80)
    print()
    print(f"✅ Successfully deleted: {deleted_count} files")
    print(f"💾 Space freed: {deleted_size / (1024*1024):.2f} MB ({deleted_size / (1024*1024*1024):.2f} GB)")
    
    if errors:
        print()
        print(f"⚠️  Errors ({len(errors)}):")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    print()
    print("💡 All deleted files are still available in Google Drive:")
    print("   Folder: GB Power Market JJ Backup")
    print(f"   Report: drive_sync_report_*.json (contains Drive links)")

if __name__ == '__main__':
    main()
