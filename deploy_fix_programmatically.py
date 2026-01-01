#!/usr/bin/env python3
"""
Programmatic Apps Script Deployment Fix
Uses Google Apps Script API to diagnose and fix deployment issues
"""

import json
import subprocess
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run shell command and return output"""
    result = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=True, 
        text=True,
        cwd=cwd or "/home/george/GB-Power-Market-JJ"
    )
    return result.stdout, result.stderr, result.returncode

def get_script_id():
    """Get the Apps Script ID from .clasp.json"""
    clasp_path = Path("/home/george/GB-Power-Market-JJ/.clasp.json")
    if clasp_path.exists():
        with open(clasp_path) as f:
            config = json.load(f)
            return config.get('scriptId')
    return None

def pull_current_deployment():
    """Pull current Apps Script files to analyze"""
    print("\n🔍 Pulling current Apps Script deployment...")
    
    # Create temp directory
    temp_dir = "/home/george/GB-Power-Market-JJ/clasp_pull_temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Copy .clasp.json to temp dir
    subprocess.run(
        f"cp /home/george/GB-Power-Market-JJ/.clasp.json {temp_dir}/",
        shell=True
    )
    
    # Pull files
    stdout, stderr, code = run_command("clasp pull", cwd=temp_dir)
    
    if code == 0:
        print(f"✅ Successfully pulled deployment")
        # List files
        files = list(Path(temp_dir).glob("*"))
        print(f"   Files: {[f.name for f in files if f.is_file()]}")
        return temp_dir, files
    else:
        print(f"❌ Failed to pull: {stderr}")
        return None, []

def analyze_manifest(manifest_path):
    """Analyze appsscript.json for missing scopes"""
    print("\n📋 Analyzing appsscript.json manifest...")
    
    required_scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/script.container.ui",
        "https://www.googleapis.com/auth/bigquery",
        "https://www.googleapis.com/auth/script.external_request"
    ]
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    current_scopes = manifest.get('oauthScopes', [])
    
    print(f"   Current scopes ({len(current_scopes)}):")
    for scope in current_scopes:
        print(f"      {scope}")
    
    missing = [s for s in required_scopes if s not in current_scopes]
    
    if missing:
        print(f"\n   ⚠️  Missing scopes ({len(missing)}):")
        for scope in missing:
            print(f"      {scope}")
        return False, missing
    else:
        print(f"\n   ✅ All required scopes present")
        return True, []

def check_files_exist(temp_dir):
    """Check if map sidebar files exist in deployment"""
    print("\n📁 Checking deployed files...")
    
    files_to_check = {
        'map_sidebarh': 'Map HTML file',
        'map_sidebar': 'Map Script file',
        'MASTER_onOpen': 'Menu integration'
    }
    
    found = {}
    for filename, desc in files_to_check.items():
        # Check for .gs or .html extensions
        if Path(f"{temp_dir}/{filename}.gs").exists():
            print(f"   ✅ {desc}: {filename}.gs")
            found[filename] = True
        elif Path(f"{temp_dir}/{filename}.html").exists():
            print(f"   ✅ {desc}: {filename}.html")
            found[filename] = True
        elif Path(f"{temp_dir}/{filename}").exists():
            print(f"   ✅ {desc}: {filename}")
            found[filename] = True
        else:
            print(f"   ❌ {desc}: NOT FOUND")
            found[filename] = False
    
    return found

def push_fixed_manifest(temp_dir):
    """Update manifest with correct OAuth scopes and push"""
    print("\n🔧 Fixing OAuth scopes in manifest...")
    
    manifest_path = Path(f"{temp_dir}/appsscript.json")
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Update scopes
    manifest['oauthScopes'] = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/script.container.ui",
        "https://www.googleapis.com/auth/bigquery",
        "https://www.googleapis.com/auth/script.external_request"
    ]
    
    # Write back
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("   ✅ Updated manifest with 4 OAuth scopes")
    
    # Push changes
    print("\n📤 Pushing fixed manifest to Apps Script...")
    stdout, stderr, code = run_command("clasp push --force", cwd=temp_dir)
    
    if code == 0:
        print("   ✅ Successfully pushed changes")
        return True
    else:
        print(f"   ❌ Push failed: {stderr}")
        return False

def push_missing_files(temp_dir):
    """Copy missing files from local and push"""
    print("\n📤 Preparing to push missing files...")
    
    local_files = {
        'map_sidebarh.html': '/home/george/GB-Power-Market-JJ/map_sidebarh.html',
        'map_sidebar.gs': '/home/george/GB-Power-Market-JJ/map_sidebar.gs',
        'MASTER_onOpen.gs': '/home/george/GB-Power-Market-JJ/MASTER_onOpen.gs'
    }
    
    for dest_name, source_path in local_files.items():
        if Path(source_path).exists():
            dest_path = f"{temp_dir}/{dest_name}"
            subprocess.run(f"cp {source_path} {dest_path}", shell=True)
            print(f"   ✅ Copied {dest_name}")
        else:
            print(f"   ⚠️  {dest_name} not found locally")
    
    # Push all files
    print("\n📤 Pushing all files to Apps Script...")
    stdout, stderr, code = run_command("clasp push --force", cwd=temp_dir)
    
    if code == 0:
        print("   ✅ Successfully pushed all files")
        return True
    else:
        print(f"   ❌ Push failed: {stderr}")
        return False

def check_script_properties():
    """Check if API key is set in Script Properties"""
    print("\n🔑 Checking Script Properties...")
    print("   ⚠️  Cannot check programmatically (requires Apps Script API)")
    print("   Manual verification needed:")
    print("   1. Open Apps Script: Extensions → Apps Script")
    print("   2. File → Project Settings → Script Properties")
    print("   3. Verify GOOGLE_MAPS_API_KEY = AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0")
    return None

def main():
    print("=" * 80)
    print("  PROGRAMMATIC APPS SCRIPT DEPLOYMENT FIX")
    print("=" * 80)
    
    # Step 1: Get Script ID
    script_id = get_script_id()
    if script_id:
        print(f"\n✅ Script ID: {script_id}")
    else:
        print("\n❌ Cannot find .clasp.json - clasp not configured")
        return
    
    # Step 2: Pull current deployment
    temp_dir, files = pull_current_deployment()
    if not temp_dir:
        print("\n⚠️  Cannot pull deployment - may need network access")
        print("   Falling back to local file analysis...")
        temp_dir = "/home/george/GB-Power-Market-JJ"
    
    # Step 3: Analyze manifest
    manifest_path = f"{temp_dir}/appsscript.json"
    if Path(manifest_path).exists():
        scopes_ok, missing = analyze_manifest(manifest_path)
    else:
        # Use local manifest
        manifest_path = "/home/george/GB-Power-Market-JJ/appsscript_v3/appsscript.json"
        if Path(manifest_path).exists():
            scopes_ok, missing = analyze_manifest(manifest_path)
        else:
            print("   ⚠️  Cannot find manifest file")
            scopes_ok, missing = False, []
    
    # Step 4: Check files
    if temp_dir != "/home/george/GB-Power-Market-JJ":
        files_status = check_files_exist(temp_dir)
    else:
        print("\n📁 Checking local files (deployment check skipped)...")
        files_status = {
            'map_sidebarh': Path("/home/george/GB-Power-Market-JJ/map_sidebarh.html").exists(),
            'map_sidebar': Path("/home/george/GB-Power-Market-JJ/map_sidebar.gs").exists(),
            'MASTER_onOpen': Path("/home/george/GB-Power-Market-JJ/MASTER_onOpen.gs").exists()
        }
        for name, exists in files_status.items():
            if exists:
                print(f"   ✅ {name}: exists locally")
            else:
                print(f"   ❌ {name}: missing")
    
    # Step 5: Apply fixes
    print("\n" + "=" * 80)
    print("  APPLYING FIXES")
    print("=" * 80)
    
    fixes_applied = []
    
    # Fix 1: OAuth scopes
    if not scopes_ok:
        print("\n🔧 Fix 1: Update OAuth scopes")
        if temp_dir != "/home/george/GB-Power-Market-JJ":
            success = push_fixed_manifest(temp_dir)
            if success:
                fixes_applied.append("OAuth scopes updated")
        else:
            print("   ⚠️  Cannot push without network - using local fix")
            # Copy fixed manifest to appsscript_v3
            subprocess.run(
                "cp /home/george/GB-Power-Market-JJ/appsscript_v3/appsscript_FIXED.json "
                "/home/george/GB-Power-Market-JJ/appsscript_v3/appsscript.json",
                shell=True
            )
            print("   ✅ Local manifest updated")
            fixes_applied.append("OAuth scopes updated (local)")
    
    # Fix 2: Missing files
    if not all(files_status.values()):
        print("\n🔧 Fix 2: Upload missing files")
        if temp_dir != "/home/george/GB-Power-Market-JJ":
            success = push_missing_files(temp_dir)
            if success:
                fixes_applied.append("Missing files uploaded")
        else:
            print("   ⚠️  Cannot push without network")
            print("   Files ready locally - manual upload needed")
    
    # Fix 3: Script Properties
    check_script_properties()
    
    # Summary
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    
    if fixes_applied:
        print(f"\n✅ Applied {len(fixes_applied)} fix(es):")
        for fix in fixes_applied:
            print(f"   • {fix}")
    else:
        print("\n⚠️  No automated fixes applied (may require network or manual steps)")
    
    print("\n📋 Remaining manual steps:")
    print("   1. If OAuth scopes changed: Reauthorize in Apps Script")
    print("      → Run any function → Review Permissions → Allow")
    print("   2. Verify Script Property GOOGLE_MAPS_API_KEY is set")
    print("   3. Enable BigQuery API in Services")
    print("   4. Test map sidebar: 🗺️ Geographic Map → Show DNO & GSP Boundaries")
    print("   5. Test search: Should no longer show UrlFetchApp.fetch error")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
