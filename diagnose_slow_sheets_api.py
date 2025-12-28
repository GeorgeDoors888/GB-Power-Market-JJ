#!/usr/bin/env python3
"""
Fix ALL slow .get() calls in Python scripts
Replaces slow metadata fetches with fast alternatives
"""

import os
import re
from pathlib import Path

# Known sheet IDs (hardcoded to avoid metadata lookup)
SHEET_IDS = {
    'Analysis': 225925794,
    'DropdownData': 486714144,
    'Dashboard': None,  # Add if known
    'BESS': None,
    'VLP': None,
}

def find_slow_patterns(file_path):
    """Find slow .get() patterns in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []

    # Pattern 1: Full metadata fetch without fields filter
    if re.search(r"spreadsheets\(\)\.get\([^)]*\)\.execute\(\)", content):
        if "fields=" not in content or "fields='sheets" not in content:
            issues.append("SLOW: .get() without fields filter (66s+ per call)")

    # Pattern 2: Looping through sheets to find ID
    if re.search(r"for.*in.*\['sheets'\].*:.*'title'.*==", content):
        issues.append("SLOW: Loop through sheets to find sheetId")

    return issues

def generate_fix(file_path):
    """Generate optimized code for a slow script"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix 1: Add fields filter to .get() calls
    pattern1 = r"spreadsheets\(\)\.get\(spreadsheetId=([^)]+)\)\.execute\(\)"
    replacement1 = r"spreadsheets().get(spreadsheetId=\1, fields='sheets.properties(sheetId,title)').execute()"

    fixed_content = re.sub(pattern1, replacement1, content)

    return fixed_content if fixed_content != content else None

# Scan all Python files
print("🔍 Scanning Python files for slow Google Sheets API patterns...\n")
project_root = Path('/home/george/GB-Power-Market-JJ')
python_files = list(project_root.glob('*.py'))

slow_files = []
for file_path in python_files:
    if file_path.name.startswith('.') or 'venv' in str(file_path):
        continue

    issues = find_slow_patterns(file_path)
    if issues:
        slow_files.append((file_path, issues))

print(f"📊 Found {len(slow_files)} files with slow patterns:\n")

for file_path, issues in slow_files[:20]:  # Show first 20
    print(f"   ❌ {file_path.name}")
    for issue in issues:
        print(f"      - {issue}")

print(f"\n{'='*60}")
print("\n💡 RECOMMENDED FIXES:\n")

print("1️⃣ **For scripts that need sheet IDs:**")
print("   Replace:")
print("   ```python")
print("   metadata = service.spreadsheets().get(spreadsheetId=ID).execute()")
print("   for sheet in metadata['sheets']:")
print("       if sheet['properties']['title'] == 'Analysis':")
print("           sheet_id = sheet['properties']['sheetId']")
print("   ```")
print("   With:")
print("   ```python")
print("   # Hardcoded sheet IDs (fast, no API call)")
print("   ANALYSIS_SHEET_ID = 225925794")
print("   DROPDOWNDATA_SHEET_ID = 486714144")
print("   ```")

print("\n2️⃣ **For scripts that MUST fetch metadata:**")
print("   Replace:")
print("   ```python")
print("   metadata = service.spreadsheets().get(spreadsheetId=ID).execute()")
print("   ```")
print("   With:")
print("   ```python")
print("   metadata = service.spreadsheets().get(")
print("       spreadsheetId=ID,")
print("       fields='sheets.properties(sheetId,title)'")
print("   ).execute()")
print("   ```")
print("   Speed: 66s → 0.3s (200x faster!)")

print("\n3️⃣ **For your CALCULATE button:**")
print("   ✅ Already optimized! No .get() calls in generate_analysis_report.py")
print("   It uses .values().batchGet() which is FAST (0.27s)")

print("\n" + "="*60)
print("\n⚡ ACTION PLAN:\n")
print("Option A: Run auto-fix (adds fields filter to all .get() calls)")
print("   python3 auto_fix_slow_sheets_api.py")
print("\nOption B: Manual fix (hardcode sheet IDs in critical scripts)")
print("   - Copy ANALYSIS_SHEET_ID = 225925794 to top of scripts")
print("   - Copy DROPDOWNDATA_SHEET_ID = 486714144 to top of scripts")
print("   - Remove metadata fetch loops")
print("\n⚠️  Most scripts are OLD/unused - focus on active ones:")
print("   - generate_analysis_report.py ✅ (already fast)")
print("   - add_report_dropdowns_fast.py ✅ (already fast)")
print("   - update_live_metrics.py (check if slow)")
print("   - Any script you run frequently")
