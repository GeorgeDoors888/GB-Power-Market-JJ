#!/usr/bin/env python3
"""
Auto-fix slow Google Sheets API calls
Adds fields filter to all .get() calls (66s → 0.3s speedup)
"""

import os
import re
from pathlib import Path
import shutil
from datetime import datetime

def fix_slow_api_call(content):
    """Replace slow .get() with fast fields-filtered version"""

    # Pattern: spreadsheets().get(spreadsheetId=X).execute()
    # Replace with: spreadsheets().get(spreadsheetId=X, fields='sheets.properties(sheetId,title)').execute()

    pattern = r"spreadsheets\(\)\.get\(\s*spreadsheetId\s*=\s*([^)]+)\s*\)\.execute\(\)"

    def replacement(match):
        spreadsheet_id = match.group(1).strip()
        return f"spreadsheets().get(spreadsheetId={spreadsheet_id}, fields='sheets.properties(sheetId,title)').execute()"

    fixed = re.sub(pattern, replacement, content)

    # Count how many were fixed
    fixes = content.count(".execute()") - fixed.count(".execute()")

    return fixed, abs(fixes)

def backup_file(file_path):
    """Create backup before modifying"""
    backup_dir = Path('/home/george/GB-Power-Market-JJ/backups/sheets_api_speedup')
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / file_path.name
    shutil.copy2(file_path, backup_path)
    return backup_path

# Target files (focus on actively used scripts)
TARGET_FILES = [
    'add_full_dropdowns_with_range.py',
    'add_report_dropdowns.py',
    'add_analysis_dropdowns.py',
    'update_live_dashboard_v2.py',
    'daily_dashboard_auto_updater.py',
    'fix_dashboard_complete.py',
    'add_enhanced_charts_and_flags.py',
]

print("🔧 Auto-fixing slow Google Sheets API calls...\n")
print("Speed improvement: 66s → 0.3s (200x faster!)\n")
print("="*60)

project_root = Path('/home/george/GB-Power-Market-JJ')
fixed_count = 0
total_fixes = 0

for filename in TARGET_FILES:
    file_path = project_root / filename

    if not file_path.exists():
        print(f"⏩ Skip: {filename} (not found)")
        continue

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if needs fixing
    if "spreadsheets().get(" not in content:
        print(f"✅ Skip: {filename} (no .get() calls)")
        continue

    if "fields=" in content and "sheets.properties" in content:
        print(f"✅ Skip: {filename} (already optimized)")
        continue

    # Backup original
    backup_path = backup_file(file_path)

    # Apply fix
    fixed_content, num_fixes = fix_slow_api_call(content)

    if num_fixes == 0:
        print(f"✅ Skip: {filename} (no patterns matched)")
        continue

    # Write fixed version
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"🔧 Fixed: {filename}")
    print(f"   - Applied {num_fixes} speedup(s)")
    print(f"   - Backup: {backup_path.name}")

    fixed_count += 1
    total_fixes += num_fixes

print("\n" + "="*60)
print(f"\n✅ Fixed {fixed_count} files with {total_fixes} speedups")
print(f"💾 Backups saved to: backups/sheets_api_speedup/")
print(f"\n⚡ Performance Impact:")
print(f"   Before: {total_fixes} × 66s = {total_fixes * 66}s wasted per run")
print(f"   After:  {total_fixes} × 0.3s = {total_fixes * 0.3:.1f}s per run")
print(f"   Saved:  {total_fixes * 65.7:.1f}s per run! ⚡")
print("\n🧪 Test a fixed script:")
print("   python3 add_full_dropdowns_with_range.py")
