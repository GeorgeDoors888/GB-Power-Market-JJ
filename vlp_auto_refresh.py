#!/usr/bin/env python3
"""
VLP Dashboard Auto-Refresh
Runs vlp_dashboard_python.py on a schedule with error handling and logging
"""

import subprocess
import sys
import os
from datetime import datetime
import traceback

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_SCRIPT = os.path.join(SCRIPT_DIR, 'vlp_dashboard_python.py')
LOG_DIR = os.path.join(SCRIPT_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'vlp_auto_refresh.log')

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def log_message(message, level="INFO"):
    """Write message to log file with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
    
    print(log_entry.strip())

def run_dashboard_refresh():
    """Execute the dashboard refresh script"""
    try:
        log_message("=" * 80)
        log_message("Starting VLP dashboard refresh")
        
        # Run the dashboard script
        result = subprocess.run(
            [sys.executable, DASHBOARD_SCRIPT],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            log_message("Dashboard refresh completed successfully")
            log_message(f"Output: {result.stdout[:500]}")  # First 500 chars
            return True
        else:
            log_message(f"Dashboard refresh failed with exit code {result.returncode}", "ERROR")
            log_message(f"Error output: {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        log_message("Dashboard refresh timed out after 5 minutes", "ERROR")
        return False
        
    except Exception as e:
        log_message(f"Unexpected error: {str(e)}", "ERROR")
        log_message(traceback.format_exc(), "ERROR")
        return False

def main():
    """Main execution"""
    log_message("VLP Auto-Refresh started")
    
    # Check if dashboard script exists
    if not os.path.exists(DASHBOARD_SCRIPT):
        log_message(f"Dashboard script not found: {DASHBOARD_SCRIPT}", "ERROR")
        sys.exit(1)
    
    # Run the refresh
    success = run_dashboard_refresh()
    
    if success:
        log_message("Auto-refresh cycle completed successfully")
        sys.exit(0)
    else:
        log_message("Auto-refresh cycle failed", "ERROR")
        sys.exit(1)

if __name__ == '__main__':
    main()
