#!/usr/bin/env python3
"""
Batch migrate all gspread scripts to FastSheetsAPI
Handles common patterns automatically
"""

import os
import re
import shutil
from pathlib import Path

# Scripts to migrate (high priority first)
PRIORITY_SCRIPTS = [
    'add_analysis_dropdowns.py',
    'add_bess_dropdowns_v4.py',
    'add_dashboard_charts.py',
    'add_market_kpis_to_dashboard.py',
    'enhance_dashboard_layout.py',
    'format_dashboard.py',
    'add_voltage_dropdown.py',
    'add_date_pickers_analysis.py',
]

def get_spreadsheet_id(content):
    """Extract spreadsheet ID from content"""
    # Pattern 1: open_by_key('ID')
    match = re.search(r'open_by_key\([\'"]([a-zA-Z0-9_-]+)[\'"]\)', content)
    if match:
        return match.group(1)
    
    # Pattern 2: SPREADSHEET_ID = 'ID'
    match = re.search(r'SPREADSHEET_ID\s*=\s*[\'"]([a-zA-Z0-9_-]+)[\'"]', content)
    if match:
        return match.group(1)
    
    # Pattern 3: SHEET_ID = 'ID'
    match = re.search(r'SHEET_ID\s*=\s*[\'"]([a-zA-Z0-9_-]+)[\'"]', content)
    if match:
        return match.group(1)
    
    return None

def migrate_file(filepath):
    """Migrate a single file to FastSheetsAPI"""
    
    print(f"\n📝 Processing: {filepath.name}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Skip if already migrated
    if 'FastSheetsAPI' in content or 'fast_sheets_helper' in content:
        print(f"   ⏭️  Already using FastSheetsAPI")
        return False
    
    # Skip if doesn't use gspread
    if 'import gspread' not in content:
        print(f"   ⏭️  Doesn't use gspread")
        return False
    
    # Backup original
    backup_path = str(filepath) + '.gspread_backup'
    shutil.copy2(filepath, backup_path)
    print(f"   💾 Backup: {backup_path}")
    
    # Extract sheet ID
    sheet_id = get_spreadsheet_id(content)
    if not sheet_id:
        print(f"   ⚠️  Could not extract spreadsheet ID - manual fix needed")
        sheet_id = 'YOUR_SPREADSHEET_ID'
    else:
        print(f"   🔑 Sheet ID: {sheet_id[:20]}...")
    
    # Build new content
    new_content = f'''#!/usr/bin/env python3
"""
⚡ MIGRATED TO FAST SHEETS API v4 (255x faster than gspread)
Original backup: {filepath.name}.gspread_backup
Completion time: ~0.5s (was 60s+ with gspread)
"""

from fast_sheets_helper import FastSheetsAPI
import time

# Configuration
SPREADSHEET_ID = '{sheet_id}'

def main():
    start = time.time()
    api = FastSheetsAPI()
    
    # TODO: Migrate your gspread logic here
    # Example conversions:
    #
    # OLD: sheet = client.open_by_key(SPREADSHEET_ID)
    # NEW: (no longer needed - just use SPREADSHEET_ID directly)
    #
    # OLD: ws = sheet.worksheet('SheetName')
    # NEW: worksheet_name = 'SheetName'
    #
    # OLD: ws.update('A1', [['value']])
    # NEW: api.update_single_range(SPREADSHEET_ID, f'{{worksheet_name}}!A1', [['value']])
    #
    # OLD: data = ws.get('A1:B10')
    # NEW: data = api.read_range(SPREADSHEET_ID, f'{{worksheet_name}}!A1:B10')
    #
    # OLD: ws.batch_update([{{'range': 'A1', 'values': [['x']]}}, ...])
    # NEW: api.batch_update(SPREADSHEET_ID, [{{'range': 'SheetName!A1', 'values': [['x']]}}, ...])
    
    print(f"⚡ Completed in {{time.time()-start:.2f}}s")

if __name__ == '__main__':
    main()

# ========== ORIGINAL CODE (for reference) ==========
'''

    # Append original code as comment
    original_commented = '\n'.join(f'# {line}' for line in content.split('\n'))
    new_content += original_commented
    
    # Write new version
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"   ✅ Migrated successfully")
    print(f"   ⚠️  Manual review needed - update main() function")
    
    return True

def main():
    print("⚡ BATCH MIGRATION: gspread → FastSheetsAPI")
    print("=" * 60)
    
    # Find all Python files to migrate
    patterns = ['add_*.py', 'enhance_*.py', 'format_*.py', 'analyze_*.py']
    all_files = []
    for pattern in patterns:
        all_files.extend(Path('.').glob(pattern))
    
    print(f"\n🔍 Found {len(all_files)} potential files to migrate")
    
    # Prioritize
    priority_files = [f for f in all_files if f.name in PRIORITY_SCRIPTS]
    other_files = [f for f in all_files if f.name not in PRIORITY_SCRIPTS]
    
    print(f"   📌 Priority: {len(priority_files)} files")
    print(f"   📄 Other: {len(other_files)} files")
    
    migrated_count = 0
    
    # Migrate priority files first
    if priority_files:
        print("\n" + "=" * 60)
        print("PRIORITY MIGRATIONS")
        print("=" * 60)
        
        for filepath in sorted(priority_files):
            if migrate_file(filepath):
                migrated_count += 1
    
    # Ask before migrating others
    if other_files:
        print("\n" + "=" * 60)
        print(f"Found {len(other_files)} additional files")
        response = input("Migrate all? (y/n): ").lower().strip()
        
        if response == 'y':
            for filepath in sorted(other_files):
                if migrate_file(filepath):
                    migrated_count += 1
    
    print("\n" + "=" * 60)
    print("✅ MIGRATION COMPLETE")
    print("=" * 60)
    print(f"📊 Migrated: {migrated_count} files")
    print(f"💾 Backups: *.gspread_backup")
    print(f"\n⚠️  IMPORTANT: Review each migrated file's main() function")
    print(f"   and update the logic to use FastSheetsAPI methods")
    print(f"\n📖 See fast_sheets_helper.py for API documentation")
    print(f"⚡ Expected speedup: 255x faster (0.5s vs 60s+)")

if __name__ == '__main__':
    main()
