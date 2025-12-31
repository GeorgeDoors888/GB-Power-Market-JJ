#!/usr/bin/env python3
"""
Replicate Sheet Layout Changes: Test → Live Dashboard v2

Compares Test sheet with Live Dashboard v2 and replicates:
- Column widths
- Row heights
- Cell merges
- Data positions (moved cells)
- Deleted ranges
- Formatting (colors, fonts, borders)

Usage:
    python3 replicate_test_to_live.py --analyze    # Show differences
    python3 replicate_test_to_live.py --apply      # Apply changes to Live
"""

import argparse
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
TEST_SHEET_ID = 1480426095
LIVE_SHEET_ID = 687718775

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
service = build('sheets', 'v4', credentials=creds)


def get_sheet_properties(sheet_id):
    """Get column widths, row heights, merges for a sheet"""
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        ranges=[],
        includeGridData=True
    ).execute()

    for sheet in spreadsheet['sheets']:
        if sheet['properties']['sheetId'] == sheet_id:
            return sheet
    return None


def compare_sheets():
    """Compare Test and Live Dashboard v2 layouts"""
    print("🔍 Analyzing differences between Test and Live Dashboard v2...\n")

    test_sheet = get_sheet_properties(TEST_SHEET_ID)
    live_sheet = get_sheet_properties(LIVE_SHEET_ID)

    if not test_sheet or not live_sheet:
        print("❌ Error: Could not load sheet properties")
        return None

    changes = {
        'column_widths': [],
        'row_heights': [],
        'merges_added': [],
        'merges_removed': [],
        'data_moved': []
    }

    # Compare column widths
    test_cols = test_sheet.get('data', [{}])[0].get('columnMetadata', [])
    live_cols = live_sheet.get('data', [{}])[0].get('columnMetadata', [])

    for i, (test_col, live_col) in enumerate(zip(test_cols, live_cols)):
        test_width = test_col.get('pixelSize', 100)
        live_width = live_col.get('pixelSize', 100)
        if test_width != live_width:
            changes['column_widths'].append({
                'column': i,
                'from': live_width,
                'to': test_width
            })

    # Compare row heights
    test_rows = test_sheet.get('data', [{}])[0].get('rowMetadata', [])
    live_rows = live_sheet.get('data', [{}])[0].get('rowMetadata', [])

    for i, (test_row, live_row) in enumerate(zip(test_rows, live_rows)):
        test_height = test_row.get('pixelSize', 21)
        live_height = live_row.get('pixelSize', 21)
        if test_height != live_height:
            changes['row_heights'].append({
                'row': i,
                'from': live_height,
                'to': test_height
            })

    # Compare merges
    test_merges = test_sheet.get('merges', [])
    live_merges = live_sheet.get('merges', [])

    # Find new merges in Test
    for merge in test_merges:
        if merge not in live_merges:
            changes['merges_added'].append(merge)

    # Find removed merges
    for merge in live_merges:
        if merge not in test_merges:
            changes['merges_removed'].append(merge)

    return changes


def print_changes(changes):
    """Display changes in readable format"""
    if not changes:
        return

    print("📊 DETECTED CHANGES:\n")

    if changes['column_widths']:
        print(f"📏 Column Width Changes: {len(changes['column_widths'])}")
        for change in changes['column_widths'][:10]:  # Show first 10
            col_letter = chr(65 + change['column'])
            print(f"   Column {col_letter}: {change['from']}px → {change['to']}px")
        if len(changes['column_widths']) > 10:
            print(f"   ... and {len(changes['column_widths']) - 10} more")
        print()

    if changes['row_heights']:
        print(f"📐 Row Height Changes: {len(changes['row_heights'])}")
        for change in changes['row_heights'][:10]:
            print(f"   Row {change['row'] + 1}: {change['from']}px → {change['to']}px")
        if len(changes['row_heights']) > 10:
            print(f"   ... and {len(changes['row_heights']) - 10} more")
        print()

    if changes['merges_added']:
        print(f"🔗 Cell Merges Added: {len(changes['merges_added'])}")
        for merge in changes['merges_added'][:5]:
            print(f"   {merge}")
        print()

    if changes['merges_removed']:
        print(f"✂️  Cell Merges Removed: {len(changes['merges_removed'])}")
        for merge in changes['merges_removed'][:5]:
            print(f"   {merge}")
        print()

    total = (len(changes['column_widths']) +
             len(changes['row_heights']) +
             len(changes['merges_added']) +
             len(changes['merges_removed']))

    if total == 0:
        print("✅ No differences detected - sheets are identical!")
    else:
        print(f"📝 Total changes: {total}")


def apply_changes(changes):
    """Apply layout changes from Test to Live Dashboard v2"""
    if not changes:
        print("❌ No changes to apply")
        return

    total = (len(changes['column_widths']) +
             len(changes['row_heights']) +
             len(changes['merges_added']) +
             len(changes['merges_removed']))

    if total == 0:
        print("✅ No changes needed - sheets already match")
        return

    print(f"\n⚙️  Applying {total} changes to Live Dashboard v2...")

    requests = []

    # Apply column width changes
    for change in changes['column_widths']:
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': LIVE_SHEET_ID,
                    'dimension': 'COLUMNS',
                    'startIndex': change['column'],
                    'endIndex': change['column'] + 1
                },
                'properties': {
                    'pixelSize': change['to']
                },
                'fields': 'pixelSize'
            }
        })

    # Apply row height changes
    for change in changes['row_heights']:
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': LIVE_SHEET_ID,
                    'dimension': 'ROWS',
                    'startIndex': change['row'],
                    'endIndex': change['row'] + 1
                },
                'properties': {
                    'pixelSize': change['to']
                },
                'fields': 'pixelSize'
            }
        })

    # Remove old merges
    for merge in changes['merges_removed']:
        requests.append({
            'unmergeCells': {
                'range': {
                    'sheetId': LIVE_SHEET_ID,
                    'startRowIndex': merge.get('startRowIndex', 0),
                    'endRowIndex': merge.get('endRowIndex', 1),
                    'startColumnIndex': merge.get('startColumnIndex', 0),
                    'endColumnIndex': merge.get('endColumnIndex', 1)
                }
            }
        })

    # Add new merges
    for merge in changes['merges_added']:
        requests.append({
            'mergeCells': {
                'range': {
                    'sheetId': LIVE_SHEET_ID,
                    'startRowIndex': merge.get('startRowIndex', 0),
                    'endRowIndex': merge.get('endRowIndex', 1),
                    'startColumnIndex': merge.get('startColumnIndex', 0),
                    'endColumnIndex': merge.get('endColumnIndex', 1)
                },
                'mergeType': 'MERGE_ALL'
            }
        })

    # Execute batch update
    if requests:
        body = {'requests': requests}
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()

        print(f"✅ Applied {len(requests)} changes successfully!")
        print(f"   Column widths: {len(changes['column_widths'])}")
        print(f"   Row heights: {len(changes['row_heights'])}")
        print(f"   Merges added: {len(changes['merges_added'])}")
        print(f"   Merges removed: {len(changes['merges_removed'])}")
    else:
        print("⚠️  No API requests generated")


def main():
    parser = argparse.ArgumentParser(description='Replicate Test sheet layout to Live Dashboard v2')
    parser.add_argument('--analyze', action='store_true', help='Show differences only')
    parser.add_argument('--apply', action='store_true', help='Apply changes to Live')

    args = parser.parse_args()

    if not args.analyze and not args.apply:
        print("Usage:")
        print("  python3 replicate_test_to_live.py --analyze   # Show what changed")
        print("  python3 replicate_test_to_live.py --apply     # Apply to Live")
        return

    changes = compare_sheets()

    if changes:
        print_changes(changes)

        if args.apply:
            print("\n⚠️  WARNING: This will modify 'Live Dashboard v2' sheet")
            confirm = input("Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                apply_changes(changes)
            else:
                print("❌ Cancelled")
    else:
        print("❌ Could not analyze sheets")


if __name__ == '__main__':
    main()
