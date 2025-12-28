#!/usr/bin/env python3
"""
Complete Deployment Pipeline
Combines template_manager + clasp_deployer for full automation
"""

from template_manager import TemplateManager
from clasp_deployer import ClaspDeployer
from pathlib import Path
import gspread
from google.oauth2 import service_account

SA_FILE = Path(__file__).parent.parent / 'inner-cinema-credentials.json'

def deploy_new_dashboard(name, include_apps_script=True, webhook_url=None):
    """
    Complete deployment: Create sheet + Apply template + Deploy Apps Script
    """
    print("=" * 80)
    print(f"⚡ DEPLOYING NEW DASHBOARD: {name}")
    print("=" * 80)
    
    # Step 1: Create new spreadsheet
    print("\n📊 Step 1: Creating new spreadsheet...")
    creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE),
        scopes=['https://www.googleapis.com/auth/spreadsheets', 
                'https://www.googleapis.com/auth/drive']
    )
    gc = gspread.authorize(creds)
    
    new_sheet = gc.create(name)
    new_sheet.share('george@upowerenergy.uk', perm_type='user', role='writer')
    
    print(f"✅ Created: {new_sheet.title}")
    print(f"   ID: {new_sheet.id}")
    print(f"   URL: {new_sheet.url}")
    
    # Step 2: Apply template from Dashboard V2
    print("\n📋 Step 2: Applying template...")
    template_mgr = TemplateManager()
    template_mgr.apply_template(new_sheet.id)
    
    # Step 3: Deploy Apps Script
    if include_apps_script:
        print("\n⚡ Step 3: Deploying Apps Script...")
        deployer = ClaspDeployer()
        deployer.deploy_to_new_sheet(new_sheet.id, webhook_url)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Spreadsheet: {new_sheet.url}")
    print(f"📝 ID: {new_sheet.id}")
    print(f"\n🎯 Next steps:")
    print(f"1. Open spreadsheet and refresh (F5)")
    print(f"2. Check for 4 menus: Maps, Data, Format, Tools")
    print(f"3. Test constraint map and formatting")
    
    return new_sheet


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("=" * 80)
        print("COMPLETE DEPLOYMENT PIPELINE")
        print("=" * 80)
        print("\nCommands:")
        print("\n1. Capture current template:")
        print("   python3 deployment_pipeline.py capture")
        print("\n2. Detect changes in Dashboard V2:")
        print("   python3 deployment_pipeline.py detect")
        print("\n3. Deploy complete new dashboard:")
        print("   python3 deployment_pipeline.py deploy 'Dashboard Name'")
        print("\n4. Watch Dashboard V2 for changes:")
        print("   python3 deployment_pipeline.py watch")
        print("\n5. Apply template only (no Apps Script):")
        print("   python3 deployment_pipeline.py apply <sheet_id>")
        return
    
    command = sys.argv[1]
    
    if command == 'capture':
        manager = TemplateManager()
        manager.capture_template()
    
    elif command == 'detect':
        manager = TemplateManager()
        changes = manager.detect_changes()
        if changes:
            print("\n💡 Run 'python3 deployment_pipeline.py apply <sheet_id>' to apply changes")
    
    elif command == 'deploy':
        if len(sys.argv) < 3:
            print("❌ Error: Provide dashboard name")
            print("   python3 deployment_pipeline.py deploy 'My Dashboard'")
            return
        
        name = sys.argv[2]
        webhook_url = sys.argv[3] if len(sys.argv) > 3 else None
        deploy_new_dashboard(name, include_apps_script=True, webhook_url=webhook_url)
    
    elif command == 'apply':
        if len(sys.argv) < 3:
            print("❌ Error: Provide spreadsheet ID")
            return
        
        manager = TemplateManager()
        manager.apply_template(sys.argv[2])
    
    elif command == 'watch':
        manager = TemplateManager()
        manager.watch_changes()
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == '__main__':
    main()
