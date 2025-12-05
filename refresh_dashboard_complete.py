#!/usr/bin/env python3
"""
Complete Dashboard Refresh Pipeline
Orchestrates: BESS data update → Dashboard layout → Timestamp refresh
"""

import subprocess
import sys
from datetime import datetime

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*70}")
    print(f"▶️  {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print("Error output:", e.stderr)
        return False

def main():
    """Execute complete dashboard refresh"""
    print("\n" + "="*70)
    print("🚀 GB ENERGY DASHBOARD - COMPLETE REFRESH")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    steps = [
        {
            'cmd': 'python3 populate_bess_enhanced.py',
            'desc': 'Step 1/2: Populate BESS data with battery calculations'
        },
        {
            'cmd': 'python3 build_dashboard_python.py',
            'desc': 'Step 2/2: Build dashboard layout and update timestamp'
        }
    ]
    
    results = []
    for step in steps:
        success = run_command(step['cmd'], step['desc'])
        results.append(success)
        
        if not success:
            print(f"\n⚠️  Warning: {step['desc']} failed, continuing...")
    
    # Summary
    print("\n" + "="*70)
    print("📊 REFRESH SUMMARY")
    print("="*70)
    for i, (step, success) in enumerate(zip(steps, results), 1):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {step['desc']}")
    
    success_count = sum(results)
    print(f"\nCompleted: {success_count}/{len(steps)} steps successful")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == len(steps):
        print("\n✅ DASHBOARD FULLY REFRESHED")
        print("🌐 View: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit")
        return 0
    else:
        print("\n⚠️  DASHBOARD PARTIALLY REFRESHED")
        print("   Check errors above and retry failed steps")
        return 1

if __name__ == '__main__':
    sys.exit(main())
