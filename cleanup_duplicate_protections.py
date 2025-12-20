#!/usr/bin/env python3
"""
Cleanup script for duplicate protection ranges in Google Sheets.

ROOT CAUSE DIAGNOSED:
- 200+ duplicate protection ranges all targeting cell E7 (row 6, column 4)
- All marked "KPI Sparkline: 💓 Frequency"
- warningOnly=True (don't technically block writes)
- BUT massive duplication causes API 500 errors when writing to M14/Q14/M16

SOLUTION:
- Remove all duplicate protections for each unique range
- Keep only 1 protection per unique cell/range
- This should fix API 500 errors
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict
import time

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'
CREDS_FILE = 'inner-cinema-credentials.json'

def main():
    print("🔧 CLEANING UP DUPLICATE PROTECTION RANGES")
    print("=" * 70)

    # Connect to Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    client = gspread.authorize(creds)
    ss = client.open_by_key(SPREADSHEET_ID)

    print(f"\n✅ Opened spreadsheet: {ss.title}")

    # Fetch full metadata
    metadata = ss.fetch_sheet_metadata()

    # Find our sheet
    sheet_data = None
    for s in metadata['sheets']:
        if s['properties']['title'] == SHEET_NAME:
            sheet_data = s
            break

    if not sheet_data:
        print(f"❌ Sheet '{SHEET_NAME}' not found!")
        return

    sheet_id = sheet_data['properties']['sheetId']
    print(f"✅ Found sheet: {SHEET_NAME} (ID: {sheet_id})")

    # Get protected ranges
    protected_ranges = sheet_data.get('protectedRanges', [])
    print(f"\n📊 Total protected ranges found: {len(protected_ranges)}")

    if not protected_ranges:
        print("✅ No protected ranges to clean up!")
        return

    # Group by unique range (row/column indices)
    range_groups = defaultdict(list)
    for pr in protected_ranges:
        # Create unique key from range coordinates
        r = pr.get('range', {})
        key = (
            r.get('sheetId'),
            r.get('startRowIndex'),
            r.get('endRowIndex'),
            r.get('startColumnIndex'),
            r.get('endColumnIndex'),
            pr.get('description', '')
        )
        range_groups[key].append(pr['protectedRangeId'])

    print(f"\n📋 Analysis:")
    print(f"   Unique ranges: {len(range_groups)}")

    # Find duplicates
    duplicates_to_remove = []
    for key, protection_ids in range_groups.items():
        if len(protection_ids) > 1:
            sheet_id, start_row, end_row, start_col, end_col, desc = key
            print(f"\n   ⚠️ Range: Row {start_row}-{end_row}, Col {start_col}-{end_col}")
            print(f"      Description: {desc[:50]}...")
            print(f"      Duplicates: {len(protection_ids)} protections (keeping 1, removing {len(protection_ids)-1})")

            # Keep first, remove rest
            duplicates_to_remove.extend(protection_ids[1:])

    if not duplicates_to_remove:
        print("\n✅ No duplicates found!")
        return

    print(f"\n🗑️ Total protections to remove: {len(duplicates_to_remove)}")
    print(f"\n⚠️ WARNING: This will make {len(duplicates_to_remove)} API calls!")
    print(f"   Expected time: ~{len(duplicates_to_remove) * 2} seconds (2s delay per call)")

    confirm = input("\nProceed with cleanup? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return

    print("\n🚀 Starting cleanup...")
    print("=" * 70)

    # Remove duplicates in batches
    BATCH_SIZE = 10
    success_count = 0
    error_count = 0

    for i in range(0, len(duplicates_to_remove), BATCH_SIZE):
        batch = duplicates_to_remove[i:i+BATCH_SIZE]

        # Create batch request
        requests = []
        for protection_id in batch:
            requests.append({
                'deleteProtectedRange': {
                    'protectedRangeId': protection_id
                }
            })

        try:
            # Execute batch
            ss.batch_update({'requests': requests})
            success_count += len(batch)
            print(f"   ✅ Batch {i//BATCH_SIZE + 1}: Removed {len(batch)} protections ({success_count}/{len(duplicates_to_remove)})")

            # Rate limiting
            if i + BATCH_SIZE < len(duplicates_to_remove):
                time.sleep(2)

        except Exception as e:
            error_count += len(batch)
            print(f"   ❌ Batch {i//BATCH_SIZE + 1}: Failed - {e}")

    print("\n" + "=" * 70)
    print("✅ CLEANUP COMPLETE!")
    print(f"   Removed: {success_count}/{len(duplicates_to_remove)} duplicate protections")
    if error_count > 0:
        print(f"   ⚠️ Errors: {error_count}")

    # Verify
    print("\n🔍 Verifying cleanup...")
    metadata = ss.fetch_sheet_metadata()
    for s in metadata['sheets']:
        if s['properties']['title'] == SHEET_NAME:
            remaining = len(s.get('protectedRanges', []))
            print(f"   Remaining protections: {remaining}")
            print(f"   Removed: {len(protected_ranges) - remaining}")
            break

    print("\n" + "=" * 70)
    print("✅ You can now retry: python3 deploy_kpis_with_timeout.py")
    print("=" * 70)

if __name__ == '__main__':
    main()
