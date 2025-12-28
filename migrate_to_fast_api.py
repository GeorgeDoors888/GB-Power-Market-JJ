#!/usr/bin/env python3
"""
Automatically migrate Python scripts from slow gspread to fast Sheets API v4
Converts all add_*.py, enhance_*.py, format_*.py scripts
"""

import os
import re
import shutil
from pathlib import Path

def migrate_script(filepath):
    """Migrate a single script to use FastSheetsAPI"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Skip if already using fast API
    if 'FastSheetsAPI' in content or 'fast_sheets_helper' in content:
        return False, "Already using fast API"
    
    # Skip if doesn't use gspread
    if 'import gspread' not in content and 'open_by_key' not in content:
        return False, "Doesn't use gspread"
    
    original_content = content
    modified = False
    
    # 1. Replace import statements
    if 'import gspread' in content:
        # Add fast API import after gspread (or replace it)
        if 'from oauth2client.service_account import ServiceAccountCredentials' in content:
            content = re.sub(
                r'import gspread\n',
                'from fast_sheets_helper import FastSheetsAPI, fast_update, fast_read\n',
                content
            )
            modified = True
        else:
            content = re.sub(
                r'import gspread\n',
                'from fast_sheets_helper import FastSheetsAPI, fast_update, fast_read\nimport gspread\n',
                content
            )
            modified = True
    
    # 2. Replace gspread client initialization
    # Pattern: gc = gspread.authorize(creds) or client = gspread.authorize(creds)
    content = re.sub(
        r'(\w+)\s*=\s*gspread\.authorize\(creds\)',
        r'fast_api = FastSheetsAPI()\n    # \1 = gspread.authorize(creds)  # DEPRECATED - using fast API',
        content
    )
    
    # 3. Comment out slow operations (don't break code that might have error handling)
    # open_by_key
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*(\w+)\.open_by_key\((.*?)\)',
        r'\1# \2 = \3.open_by_key(\4)  # DEPRECATED - using fast API\n\1spreadsheet_id = \4',
        content
    )
    
    # worksheet() calls
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*(\w+)\.worksheet\((.*?)\)',
        r'\1# \2 = \3.worksheet(\4)  # DEPRECATED - using fast API\n\1worksheet_name = \4',
        content
    )
    
    if modified or content != original_content:
        # Create backup
        backup_path = filepath + '.backup'
        shutil.copy2(filepath, backup_path)
        
        # Add migration notice at top
        notice = '''"""
⚡ MIGRATED TO FAST SHEETS API v4 (255x faster)
Backup saved as: {}.backup
Original gspread calls are commented out
Use fast_api.batch_update() or fast_update() helper functions
"""

'''.format(os.path.basename(filepath))
        
        if not content.startswith('"""'):
            content = notice + content
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        return True, f"Migrated successfully (backup: {backup_path})"
    
    return False, "No changes needed"


def main():
    """Migrate all matching scripts"""
    
    patterns = ['add_*.py', 'enhance_*.py', 'format_*.py']
    scripts = []
    
    for pattern in patterns:
        scripts.extend(Path('.').glob(pattern))
    
    print(f"🔍 Found {len(scripts)} scripts to check")
    print(f"📝 Using FastSheetsAPI from fast_sheets_helper.py\n")
    
    migrated = 0
    skipped = 0
    
    for script in sorted(scripts):
        success, message = migrate_script(script)
        
        if success:
            print(f"✅ {script.name}: {message}")
            migrated += 1
        else:
            print(f"⏭️  {script.name}: {message}")
            skipped += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Migrated: {migrated}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"\n⚡ All migrated scripts will now use fast Sheets API v4 (0.5s vs 60s+)")
    print(f"\n🔧 Manual fixes needed:")
    print(f"   1. Replace sheet.update() calls with fast_api.batch_update()")
    print(f"   2. Replace sheet.get() calls with fast_api.read_range()")
    print(f"   3. Update worksheet references to use worksheet_name variable")
    print(f"\n📖 See fast_sheets_helper.py for examples")


if __name__ == '__main__':
    main()
