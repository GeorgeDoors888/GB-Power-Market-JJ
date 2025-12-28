#!/usr/bin/env python3
"""
Unified Dashboard Refresh Script
Master script to update all systems: BESS + Arbitrage + IRIS + Stats
"""

import subprocess
import sys
from datetime import datetime

SCRIPTS = [
    ('BESS DUoS Tracker', 'bess_live_duos_tracker.py'),
    ('BESS Cost Tracking', 'bess_cost_tracking.py'),
    ('Battery Arbitrage Enhanced', 'battery_arbitrage_enhanced.py'),
    ('Revenue Stack Analyzer', 'bess_revenue_stack_analyzer.py'),
    ('Seasonal Arbitrage Analysis', 'analyze_seasonal_arbitrage.py'),
    ('IRIS Data Quality Monitor', 'iris_data_quality_monitor.py'),
]

def run_script(name, script_path):
    """Run a single script and report status"""
    print(f'\n{"="*80}')
    print(f'🔄 Running: {name}')
    print(f'{"="*80}')
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f'✅ {name} completed successfully')
            return True
        else:
            print(f'❌ {name} failed with exit code {result.returncode}')
            print(f'Error: {result.stderr[:500]}')
            return False
            
    except subprocess.TimeoutExpired:
        print(f'⏰ {name} timed out after 5 minutes')
        return False
    except Exception as e:
        print(f'❌ {name} failed with error: {e}')
        return False

def main():
    print('\n⚡ UNIFIED DASHBOARD REFRESH')
    print('='*80)
    print(f'Start time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Scripts to run: {len(SCRIPTS)}')
    print('='*80)
    
    results = {}
    
    for name, script in SCRIPTS:
        success = run_script(name, script)
        results[name] = success
    
    # Summary
    print('\n\n' + '='*80)
    print('📊 REFRESH SUMMARY')
    print('='*80)
    
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    
    print(f'\n✅ Successful: {successful}/{len(SCRIPTS)}')
    print(f'❌ Failed: {failed}/{len(SCRIPTS)}')
    
    print('\nDetailed Results:')
    for name, success in results.items():
        status = '✅' if success else '❌'
        print(f'   {status} {name}')
    
    print(f'\n⏰ End time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*80 + '\n')
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
