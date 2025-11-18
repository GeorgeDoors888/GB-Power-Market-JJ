#!/usr/bin/env python3
"""
Migrate realtime_dashboard_updater.py to use workspace delegation
Creates a backup and updates authentication to use workspace-credentials.json
"""

import shutil
from pathlib import Path
from datetime import datetime

def backup_and_migrate():
    """Backup original script and create delegated version"""
    
    script_path = Path(__file__).parent / 'realtime_dashboard_updater.py'
    backup_path = script_path.with_suffix('.py.backup')
    
    print("=" * 80)
    print("🔄 Migrating realtime_dashboard_updater.py to Workspace Delegation")
    print("=" * 80)
    print()
    
    if not script_path.exists():
        print("❌ realtime_dashboard_updater.py not found")
        return False
    
    # Create backup
    print(f"📦 Creating backup: {backup_path.name}")
    shutil.copy2(script_path, backup_path)
    print("✅ Backup created")
    print()
    
    # Read original
    print("📖 Reading original script...")
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Check if already migrated
    if 'workspace-credentials.json' in content:
        print("ℹ️  Script already uses workspace-credentials.json")
        print("✅ No changes needed")
        return True
    
    # Prepare new authentication section
    old_auth = """        # Google Sheets (uses OAuth token)
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
        
        gc = gspread.authorize(creds)"""
    
    new_auth = """        # Google Sheets (uses workspace delegation)
        WORKSPACE_CREDS = Path(__file__).parent / 'workspace-credentials.json'
        
        if WORKSPACE_CREDS.exists():
            # Use delegation (permanent auth, no expiration)
            sheets_creds = service_account.Credentials.from_service_account_file(
                str(WORKSPACE_CREDS),
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            ).with_subject('george@upowerenergy.uk')
            gc = gspread.authorize(sheets_creds)
            logging.info("✅ Using workspace delegation (permanent auth)")
        else:
            # Fallback to OAuth token if workspace creds not available
            if TOKEN_FILE.exists():
                with open(TOKEN_FILE, 'rb') as f:
                    creds = pickle.load(f)
                gc = gspread.authorize(creds)
                logging.info("⚠️  Using OAuth token (fallback)")
            else:
                logging.error("❌ No credentials available!")
                return False"""
    
    # Check if old pattern exists
    if old_auth not in content:
        print("⚠️  Expected authentication pattern not found")
        print("   Manual update may be needed")
        print()
        print("   Looking for:")
        print("   " + old_auth.split('\n')[0])
        return False
    
    # Replace authentication
    print("🔧 Updating authentication method...")
    updated_content = content.replace(old_auth, new_auth)
    
    # Also update the TOKEN_FILE check to be less strict
    old_check = """        # Check token file exists
        if not TOKEN_FILE.exists():
            logging.error(f"❌ Token file not found: {TOKEN_FILE}")
            logging.error("   Run: python3 update_analysis_bi_enhanced.py manually first")
            return False"""
    
    new_check = """        # Check credentials available (workspace creds preferred, token as fallback)
        WORKSPACE_CREDS = Path(__file__).parent / 'workspace-credentials.json'
        
        if not WORKSPACE_CREDS.exists() and not TOKEN_FILE.exists():
            logging.error(f"❌ No credentials found:")
            logging.error(f"   Need either: {WORKSPACE_CREDS.name} (preferred)")
            logging.error(f"             or: {TOKEN_FILE.name} (fallback)")
            return False"""
    
    if old_check in updated_content:
        updated_content = updated_content.replace(old_check, new_check)
    
    # Write updated version
    print("💾 Writing updated script...")
    with open(script_path, 'w') as f:
        f.write(updated_content)
    
    print("✅ Migration complete!")
    print()
    print("=" * 80)
    print("📋 Changes Made")
    print("=" * 80)
    print()
    print("✅ Backup created:", backup_path.name)
    print("✅ Now uses: workspace-credentials.json (with delegation)")
    print("✅ Fallback to: token.pickle (if workspace creds not available)")
    print("✅ No longer requires OAuth token file")
    print()
    print("=" * 80)
    print("🧪 Testing Recommended")
    print("=" * 80)
    print()
    print("Test the updated script:")
    print("  python3 realtime_dashboard_updater.py")
    print()
    print("If there are issues:")
    print("  cp realtime_dashboard_updater.py.backup realtime_dashboard_updater.py")
    print()
    print("Monitor logs:")
    print("  tail -f logs/dashboard_updater.log")
    print()
    
    return True

if __name__ == '__main__':
    backup_and_migrate()
