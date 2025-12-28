#!/usr/bin/env python3
"""
Clasp Deployer - Automate Apps Script deployment via clasp CLI
Monitors Code.gs changes and auto-deploys to target spreadsheets
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

CLASP_DIR = Path(__file__).parent
CODE_FILE = CLASP_DIR / 'Code.gs'
PACKAGE_CODE = Path.home() / 'Downloads' / 'Upower_GB_Power_Dashboard' / 'apps_script_code.gs'

class ClaspDeployer:
    def __init__(self):
        self.clasp_dir = CLASP_DIR
        
    def check_clasp_installed(self):
        """Verify clasp CLI is available"""
        try:
            result = subprocess.run(['clasp', '--version'], 
                                  capture_output=True, text=True)
            print(f"✅ clasp version: {result.stdout.strip()}")
            return True
        except FileNotFoundError:
            print("❌ clasp not found. Install with: npm install -g @railway/clasp")
            return False
    
    def get_current_config(self):
        """Read .clasp.json configuration"""
        clasp_json = self.clasp_dir / '.clasp.json'
        if clasp_json.exists():
            config = json.loads(clasp_json.read_text())
            print(f"📋 Current script: {config.get('scriptId')}")
            print(f"📊 Spreadsheet: {config.get('parentId', ['N/A'])[0]}")
            return config
        return None
    
    def update_code_with_config(self, spreadsheet_id, webhook_url=None):
        """Update Code.gs with new spreadsheet ID"""
        print(f"📝 Updating Code.gs with spreadsheet ID...")
        
        code = CODE_FILE.read_text()
        
        # Replace spreadsheet ID
        code = code.replace(
            "SPREADSHEET_ID: 'YOUR_SPREADSHEET_ID_HERE'",
            f"SPREADSHEET_ID: '{spreadsheet_id}'"
        )
        
        # Replace webhook URL if provided
        if webhook_url:
            code = code.replace(
                "WEBHOOK_URL: 'YOUR_WEBHOOK_URL_HERE'",
                f"WEBHOOK_URL: '{webhook_url}'"
            )
        
        CODE_FILE.write_text(code)
        print("✅ Code.gs updated")
    
    def push(self):
        """Push code to Apps Script"""
        if not self.check_clasp_installed():
            return False
        
        print("⚡ Pushing to Apps Script...")
        
        result = subprocess.run(
            ['clasp', 'push'],
            cwd=self.clasp_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Code pushed successfully")
            print(result.stdout)
            return True
        else:
            print("❌ Push failed")
            print(result.stderr)
            return False
    
    def create_new_script(self, title, parent_sheet_id):
        """Create new Apps Script project linked to spreadsheet"""
        print(f"📝 Creating new Apps Script: {title}")
        
        result = subprocess.run(
            ['clasp', 'create', '--title', title, '--type', 'sheets',
             '--parentId', parent_sheet_id],
            cwd=self.clasp_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Script created")
            print(result.stdout)
            return True
        else:
            print("❌ Creation failed")
            print(result.stderr)
            return False
    
    def deploy_to_new_sheet(self, spreadsheet_id, webhook_url=None):
        """Complete deployment to new spreadsheet"""
        print("=" * 80)
        print(f"⚡ DEPLOYING TO NEW SHEET: {spreadsheet_id}")
        print("=" * 80)
        
        # Step 1: Update code with config
        self.update_code_with_config(spreadsheet_id, webhook_url)
        
        # Step 2: Update .clasp.json to point to new sheet
        clasp_json = self.clasp_dir / '.clasp.json'
        if clasp_json.exists():
            config = json.loads(clasp_json.read_text())
            config['parentId'] = [spreadsheet_id]
            clasp_json.write_text(json.dumps(config, indent=2))
            print(f"✅ Updated .clasp.json")
        
        # Step 3: Push code
        if self.push():
            print("\n" + "=" * 80)
            print("✅ DEPLOYMENT COMPLETE!")
            print("=" * 80)
            print(f"\n📊 Open spreadsheet and refresh to see menus")
            print(f"🔗 https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            return True
        
        return False
    
    def watch_and_deploy(self):
        """Watch Code.gs for changes and auto-deploy"""
        print("👀 Watching Code.gs for changes...")
        print("   Ctrl+C to stop")
        
        import time
        from datetime import datetime
        
        last_modified = CODE_FILE.stat().st_mtime
        
        try:
            while True:
                current_modified = CODE_FILE.stat().st_mtime
                
                if current_modified > last_modified:
                    print(f"\n⚡ Change detected at {datetime.now().strftime('%H:%M:%S')}")
                    print("⚡ Auto-deploying...")
                    
                    if self.push():
                        print("✅ Deployed successfully")
                    else:
                        print("❌ Deployment failed")
                    
                    last_modified = current_modified
                
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            print("\n✅ Stopped watching")


def main():
    import sys
    
    deployer = ClaspDeployer()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 clasp_deployer.py check              - Check clasp installation")
        print("  python3 clasp_deployer.py push               - Push current code")
        print("  python3 clasp_deployer.py deploy <sheet_id>  - Deploy to new sheet")
        print("  python3 clasp_deployer.py watch              - Watch and auto-deploy")
        return
    
    command = sys.argv[1]
    
    if command == 'check':
        deployer.check_clasp_installed()
        deployer.get_current_config()
    
    elif command == 'push':
        deployer.push()
    
    elif command == 'deploy':
        if len(sys.argv) < 3:
            print("❌ Error: Provide spreadsheet ID")
            print("   python3 clasp_deployer.py deploy <spreadsheet_id>")
            return
        
        sheet_id = sys.argv[2]
        webhook_url = sys.argv[3] if len(sys.argv) > 3 else None
        deployer.deploy_to_new_sheet(sheet_id, webhook_url)
    
    elif command == 'watch':
        deployer.watch_and_deploy()
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == '__main__':
    main()
