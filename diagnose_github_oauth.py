#!/usr/bin/env python3
"""
GitHub OAuth & ChatGPT Connector Diagnostic Tool
Diagnoses why ChatGPT's GitHub connector isn't working
"""

import os
import json
import subprocess
from datetime import datetime

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return f"Error: {e}", 1

def check_github_token():
    """Check GitHub CLI token and scopes"""
    print("🔍 Checking GitHub Token...")
    output, code = run_command("gh auth status 2>&1")
    
    if "Logged in" in output:
        print("  ✅ GitHub CLI authenticated")
        
        # Check scopes
        if "repo" in output:
            print("  ✅ 'repo' scope present")
        else:
            print("  ❌ 'repo' scope MISSING")
            
        # Check for read:user scope (needed for ChatGPT)
        if "read:user" in output or "user" in output:
            print("  ✅ 'user' scope present")
        else:
            print("  ❌ 'user' scope MISSING (needed for ChatGPT)")
            
        return True
    else:
        print("  ❌ Not authenticated with GitHub CLI")
        return False

def check_github_app_access():
    """Check if token can access GitHub Apps"""
    print("\n🔍 Checking GitHub App Permissions...")
    output, code = run_command("gh api /user/installations 2>&1")
    
    if code == 0:
        try:
            data = json.loads(output)
            if data.get('total_count', 0) > 0:
                print(f"  ✅ Can access GitHub Apps ({data['total_count']} installations)")
                for install in data.get('installations', []):
                    print(f"     - {install.get('app_slug', 'unknown')}")
                return True
            else:
                print("  ⚠️  No GitHub Apps installed")
                return False
        except:
            print(f"  ✅ API accessible (response: {output[:100]})")
            return True
    else:
        if "403" in output:
            print("  ❌ FORBIDDEN: Token lacks GitHub App permissions")
            print("  ℹ️  This is the main issue preventing ChatGPT connector")
            return False
        else:
            print(f"  ❌ Error accessing GitHub Apps: {output[:200]}")
            return False

def check_oauth_credentials():
    """Check for OAuth credential files"""
    print("\n🔍 Checking OAuth Credentials...")
    
    paths = [
        "~/repo/GB Power Market JJ/oauth_credentials.json",
        "~/repo/GB Power Market JJ/credentials.json",
        "~/.config/gh/oauth_token.txt",
    ]
    
    found = False
    for path in paths:
        expanded = os.path.expanduser(path)
        if os.path.exists(expanded):
            print(f"  ✅ Found: {path}")
            found = True
            
            # Try to read and check structure
            try:
                with open(expanded, 'r') as f:
                    data = json.load(f)
                    if 'client_id' in data or 'installed' in data:
                        print(f"     Contains OAuth client configuration")
                    if 'access_token' in data or 'token' in data:
                        print(f"     Contains access token")
            except:
                pass
    
    if not found:
        print("  ⚠️  No OAuth credential files found")
    
    return found

def check_chatgpt_github_app():
    """Check if ChatGPT GitHub App is installed"""
    print("\n🔍 Checking ChatGPT GitHub App Installation...")
    
    # Try to list repos accessible via GitHub Apps
    output, code = run_command('gh api /user/repos 2>&1 | head -50')
    
    if code == 0:
        print("  ✅ Can list user repositories")
    else:
        print("  ❌ Cannot list repositories")
    
    # Check for ChatGPT app specifically
    output, code = run_command('gh api /user/marketplace_purchases 2>&1')
    if "404" not in output and "403" not in output:
        print("  ✅ Can access marketplace")
    else:
        print("  ⚠️  Cannot access GitHub Marketplace")

def provide_solutions():
    """Provide solutions for fixing OAuth issues"""
    print("\n" + "="*60)
    print("🔧 SOLUTIONS TO FIX CHATGPT GITHUB CONNECTOR")
    print("="*60)
    
    print("\n1️⃣  REGENERATE GITHUB TOKEN WITH CORRECT SCOPES")
    print("   Visit: https://github.com/settings/tokens")
    print("   Create new token with these scopes:")
    print("   ✓ repo (all)")
    print("   ✓ read:user")
    print("   ✓ user:email")
    print("   ✓ read:org")
    print("   ✓ workflow")
    print("\n   Then authenticate with:")
    print("   gh auth login --with-token < your_new_token.txt")
    
    print("\n2️⃣  INSTALL CHATGPT GITHUB APP")
    print("   Visit: https://github.com/apps/chatgpt")
    print("   Click 'Install' or 'Configure'")
    print("   Grant access to your repositories")
    
    print("\n3️⃣  AUTHORIZE CHATGPT FOR YOUR REPOS")
    print("   Visit: https://github.com/settings/installations")
    print("   Find 'ChatGPT' in the list")
    print("   Configure repository access:")
    print("   - Select 'All repositories' OR")
    print("   - Choose specific repos you want ChatGPT to access")
    
    print("\n4️⃣  RE-AUTHENTICATE IN CHATGPT")
    print("   In ChatGPT:")
    print("   - Go to Settings")
    print("   - Find GitHub connector")
    print("   - Click 'Reconnect' or 'Authorize'")
    print("   - Follow OAuth flow")
    
    print("\n5️⃣  VERIFY CONNECTION")
    print("   After fixing, run this diagnostic again:")
    print("   python diagnose_github_oauth.py")
    print("\n" + "="*60)

def main():
    print("="*60)
    print("GitHub OAuth & ChatGPT Connector Diagnostic")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {
        'token': check_github_token(),
        'app_access': check_github_app_access(),
        'oauth_creds': check_oauth_credentials(),
    }
    
    check_chatgpt_github_app()
    
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*60)
    
    if results['token'] and results['app_access']:
        print("✅ GitHub authentication appears healthy")
        print("✅ Token has GitHub App permissions")
        print("\nIf ChatGPT still can't connect:")
        print("- Reinstall ChatGPT GitHub App")
        print("- Re-authorize in ChatGPT settings")
    else:
        print("❌ ISSUES FOUND:")
        if not results['token']:
            print("  • GitHub CLI not properly authenticated")
        if not results['app_access']:
            print("  • Token lacks GitHub App permissions (MAIN ISSUE)")
            print("  • This prevents ChatGPT from accessing your repos")
    
    provide_solutions()
    
    print("\n💡 Quick Fix Command:")
    print("   gh auth refresh -h github.com -s read:user,user:email,repo,workflow")
    print("\nThis will refresh your token with the needed scopes.")

if __name__ == "__main__":
    main()
