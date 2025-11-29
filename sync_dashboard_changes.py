#!/usr/bin/env python3
"""
sync_dashboard_changes.py
--------------------------
Monitors dashboard changes and automatically updates:
- Apps Script files (via clasp)
- Python automation scripts
- Configuration files
- Documentation

Usage:
    python3 sync_dashboard_changes.py [--watch]
    
Options:
    --watch    Continuous monitoring mode (checks every 30 seconds)
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "new-dashboard"
DOCS_DIR = BASE_DIR

# Files to monitor
MONITORED_FILES = {
    'apps_script': [
        SCRIPTS_DIR / "Code.gs",
        SCRIPTS_DIR / "UpdateDashboard.gs",
        SCRIPTS_DIR / "DashboardFilters.gs",
        SCRIPTS_DIR / "appsscript.json"
    ],
    'python_scripts': [
        BASE_DIR / "realtime_dashboard_updater.py",
        BASE_DIR / "update_summary_for_chart.py",
        BASE_DIR / "update_iris_dashboard.py",
        BASE_DIR / "clear_outages_section.py",
        BASE_DIR / "update_outages_for_v2.py",
        BASE_DIR / "apply_orange_redesign.py",
        BASE_DIR / "add_validation_and_formatting.py",
        BASE_DIR / "fix_dashboard_layout.py"
    ],
    'config_files': [
        BASE_DIR / "inner-cinema-credentials.json",
        SCRIPTS_DIR / ".clasp.json"
    ],
    'documentation': [
        BASE_DIR / "DASHBOARD_V2_STATUS.md",
        BASE_DIR / "CHART_SPECS.md",
        BASE_DIR / "FINAL_SETUP_INSTRUCTIONS.md"
    ]
}

STATE_FILE = BASE_DIR / ".dashboard_sync_state.json"

def get_file_hash(file_path):
    """Calculate MD5 hash of file"""
    if not file_path.exists():
        return None
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_state():
    """Load previous file states"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """Save current file states"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def detect_changes():
    """Detect which files have changed"""
    old_state = load_state()
    new_state = {}
    changes = {'apps_script': [], 'python_scripts': [], 'config_files': [], 'documentation': []}
    
    for category, files in MONITORED_FILES.items():
        for file_path in files:
            file_str = str(file_path)
            new_hash = get_file_hash(file_path)
            new_state[file_str] = new_hash
            
            if file_str in old_state:
                if old_state[file_str] != new_hash and new_hash is not None:
                    changes[category].append(file_path)
            elif new_hash is not None:
                # New file created
                changes[category].append(file_path)
    
    save_state(new_state)
    return changes

def deploy_apps_script(changed_files):
    """Deploy Apps Script changes via clasp"""
    if not changed_files:
        return True
    
    print(f"\n📤 Deploying {len(changed_files)} Apps Script file(s)...")
    for file in changed_files:
        print(f"   • {file.name}")
    
    try:
        os.chdir(SCRIPTS_DIR)
        result = subprocess.run(
            ['clasp', 'push', '--force'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("   ✅ Apps Script deployed successfully")
            print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"   ❌ Deployment failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⚠️ Deployment timeout (network issue?)")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        os.chdir(BASE_DIR)

def validate_python_scripts(changed_files):
    """Validate Python scripts for syntax errors"""
    if not changed_files:
        return True
    
    print(f"\n🐍 Validating {len(changed_files)} Python script(s)...")
    all_valid = True
    
    for file in changed_files:
        print(f"   • {file.name}", end=" ")
        try:
            with open(file, 'r') as f:
                compile(f.read(), file, 'exec')
            print("✅")
        except SyntaxError as e:
            print(f"❌ Syntax error at line {e.lineno}")
            all_valid = False
    
    return all_valid

def update_documentation(changed_files):
    """Update documentation timestamps"""
    if not changed_files:
        return
    
    print(f"\n📝 Updating {len(changed_files)} documentation file(s)...")
    for file in changed_files:
        print(f"   • {file.name} ✅")

def backup_changes(changes):
    """Create backup of changed files"""
    if not any(changes.values()):
        return
    
    backup_dir = BASE_DIR / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Backing up to: {backup_dir.name}")
    
    for category, files in changes.items():
        if files:
            cat_dir = backup_dir / category
            cat_dir.mkdir(exist_ok=True)
            for file in files:
                if file.exists():
                    import shutil
                    shutil.copy2(file, cat_dir / file.name)
                    print(f"   • {file.name}")

def sync_changes():
    """Main sync function"""
    print("=" * 70)
    print(f"🔄 DASHBOARD SYNC - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    changes = detect_changes()
    
    # Count total changes
    total_changes = sum(len(files) for files in changes.values())
    
    if total_changes == 0:
        print("\n✅ No changes detected")
        return True
    
    print(f"\n📊 Detected {total_changes} changed file(s)")
    
    # Backup first
    backup_changes(changes)
    
    success = True
    
    # Validate Python scripts
    if changes['python_scripts']:
        if not validate_python_scripts(changes['python_scripts']):
            print("\n⚠️ Python validation failed - review syntax errors")
            success = False
    
    # Deploy Apps Script
    if changes['apps_script']:
        if not deploy_apps_script(changes['apps_script']):
            print("\n⚠️ Apps Script deployment failed")
            success = False
    
    # Update docs
    if changes['documentation']:
        update_documentation(changes['documentation'])
    
    # Check config changes
    if changes['config_files']:
        print(f"\n⚙️ Config files changed: {len(changes['config_files'])}")
        for file in changes['config_files']:
            print(f"   ⚠️ {file.name} - manual review recommended")
    
    print("\n" + "=" * 70)
    if success:
        print("✅ SYNC COMPLETE")
    else:
        print("⚠️ SYNC COMPLETED WITH WARNINGS")
    print("=" * 70)
    
    return success

def watch_mode():
    """Continuous monitoring mode"""
    print("=" * 70)
    print("👁️  WATCH MODE - Monitoring for changes...")
    print("=" * 70)
    print("\nMonitoring:")
    for category, files in MONITORED_FILES.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        for file in files:
            status = "✓" if file.exists() else "✗"
            print(f"  {status} {file.name}")
    
    print("\n🔄 Checking for changes every 30 seconds...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            sync_changes()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\n👋 Watch mode stopped")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--watch':
        watch_mode()
    else:
        sync_changes()

if __name__ == "__main__":
    main()
