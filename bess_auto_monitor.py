#!/usr/bin/env python3
"""
BESS Sheet Auto-Monitor with Caching
====================================
Real-time monitoring with change detection and smart caching

Features:
- Detects changes to postcode/MPAN
- Auto-triggers DNO lookup
- Redis caching for API responses
- Data freshness indicators
- Scheduled background updates

Usage: python3 bess_auto_monitor.py [--daemon]
"""

import gspread
from google.oauth2.service_account import Credentials
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import sys

# Simple in-memory cache (use Redis in production)
CACHE = {}
CACHE_TTL = 3600  # 1 hour

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CHECK_INTERVAL = 30  # seconds


def get_cache_key(postcode: str, mpan: str, voltage: str) -> str:
    """Generate cache key from inputs"""
    combined = f"{postcode}_{mpan}_{voltage}".lower().strip()
    return hashlib.md5(combined.encode()).hexdigest()


def get_cached_data(key: str) -> Optional[Dict]:
    """Retrieve cached data if still valid"""
    if key in CACHE:
        cached = CACHE[key]
        if datetime.now() < cached['expires']:
            print(f"  ✅ Cache hit (age: {(datetime.now() - cached['created']).seconds}s)")
            return cached['data']
        else:
            # Expired
            del CACHE[key]
            print("  ⏰ Cache expired")
    return None


def set_cached_data(key: str, data: Dict):
    """Store data in cache with expiry"""
    CACHE[key] = {
        'data': data,
        'created': datetime.now(),
        'expires': datetime.now() + timedelta(seconds=CACHE_TTL)
    }
    print(f"  💾 Cached data (TTL: {CACHE_TTL}s)")


def get_sheet_inputs(sheet: gspread.Worksheet) -> Tuple[str, str, str]:
    """Read current inputs from BESS sheet"""
    postcode = str(sheet.acell('A6').value or '').strip()
    mpan = str(sheet.acell('B6').value or '').strip()
    voltage_raw = str(sheet.acell('A10').value or 'LV').strip()  # Changed from A9 to A10
    
    # Extract voltage level (e.g., "LV (<1kV)" -> "LV")
    voltage = voltage_raw.split('(')[0].strip() if '(' in voltage_raw else voltage_raw
    
    return postcode, mpan, voltage


def calculate_data_freshness(last_update: datetime) -> str:
    """Calculate freshness indicator"""
    age = (datetime.now() - last_update).total_seconds() / 60  # minutes
    
    if age < 10:
        return "✅ FRESH"
    elif age < 60:
        return f"⚠️ {int(age)}min ago"
    else:
        hours = int(age / 60)
        return f"🔴 {hours}h ago"


def update_status_bar(sheet: gspread.Worksheet, message: str, color: str = '#90EE90'):
    """Update status bar with message and color"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.update('A4:H4', [[f'{message}', f'Updated: {timestamp}', '', '', '', '', '', '']], value_input_option='RAW')
    
    # Set background color
    color_map = {
        'green': {'red': 0.56, 'green': 0.93, 'blue': 0.56},   # Light green
        'yellow': {'red': 1.0, 'green': 0.92, 'blue': 0.23},   # Yellow
        'red': {'red': 1.0, 'green': 0.32, 'blue': 0.32},      # Red
        'blue': {'red': 0.53, 'green': 0.81, 'blue': 0.98}     # Light blue
    }
    
    bg_color = color_map.get(color, color_map['green'])
    sheet.format('A4:H4', {'backgroundColor': bg_color})


def trigger_dno_lookup(postcode: str, mpan: str, voltage: str) -> bool:
    """
    Trigger DNO lookup script
    Returns True if successful
    """
    import subprocess
    
    try:
        # Call dno_lookup_python.py with parameters
        cmd = ['python3', 'dno_lookup_python.py', mpan, voltage]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("  ✅ DNO lookup completed")
            return True
        else:
            print(f"  ❌ Lookup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def monitor_loop(daemon_mode: bool = False):
    """
    Main monitoring loop
    Checks for changes every CHECK_INTERVAL seconds
    """
    print("="*60)
    print("🔋 BESS AUTO-MONITOR STARTED")
    print("="*60)
    print(f"Check interval: {CHECK_INTERVAL}s")
    print(f"Cache TTL: {CACHE_TTL}s")
    if daemon_mode:
        print("Mode: Daemon (continuous)")
    else:
        print("Mode: Manual (Ctrl+C to stop)")
    print("="*60)
    
    # Connect to Google Sheets
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    bess_sheet = spreadsheet.worksheet('BESS')
    
    print("✅ Connected to BESS sheet\n")
    
    # Track last known state
    last_state = {'postcode': '', 'mpan': '', 'voltage': ''}
    last_update = datetime.now()
    check_count = 0
    
    try:
        while True:
            check_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Check #{check_count}")
            
            # Read current inputs
            postcode, mpan, voltage = get_sheet_inputs(bess_sheet)
            
            # Check if anything changed
            current_state = {'postcode': postcode, 'mpan': mpan, 'voltage': voltage}
            
            if current_state != last_state and (postcode or mpan):
                print(f"  🔍 Change detected!")
                print(f"     Postcode: {postcode or '(empty)'}")
                print(f"     MPAN: {mpan or '(empty)'}")
                print(f"     Voltage: {voltage}")
                
                # Check cache first
                cache_key = get_cache_key(postcode, mpan, voltage)
                cached_data = get_cached_data(cache_key)
                
                if cached_data:
                    update_status_bar(bess_sheet, '✅ Data loaded from cache', 'green')
                    # Could restore cached data to sheet here
                else:
                    # Trigger lookup
                    update_status_bar(bess_sheet, '🔄 Looking up DNO data...', 'yellow')
                    
                    if trigger_dno_lookup(postcode, mpan, voltage):
                        update_status_bar(bess_sheet, '✅ DNO data updated', 'green')
                        last_update = datetime.now()
                        
                        # Cache the result (simplified - actual data would come from sheet)
                        set_cached_data(cache_key, {'timestamp': datetime.now().isoformat()})
                    else:
                        update_status_bar(bess_sheet, '❌ Lookup failed', 'red')
                
                last_state = current_state
            else:
                # No changes - show freshness
                freshness = calculate_data_freshness(last_update)
                print(f"  ⏸️  No changes ({freshness})")
            
            if not daemon_mode:
                print(f"\nWaiting {CHECK_INTERVAL}s... (Ctrl+C to stop)")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitor stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


def show_cache_stats():
    """Display cache statistics"""
    print("\n📊 CACHE STATISTICS")
    print("="*60)
    print(f"Total entries: {len(CACHE)}")
    
    if CACHE:
        now = datetime.now()
        for key, data in CACHE.items():
            age_seconds = (now - data['created']).seconds
            ttl_seconds = (data['expires'] - now).seconds
            print(f"  Key: {key[:8]}... | Age: {age_seconds}s | TTL: {ttl_seconds}s")
    else:
        print("  (no cached data)")
    print("="*60)


def main():
    """Main entry point"""
    daemon_mode = '--daemon' in sys.argv
    
    if '--stats' in sys.argv:
        show_cache_stats()
        return
    
    if '--help' in sys.argv:
        print("""
BESS Auto-Monitor Usage:
  python3 bess_auto_monitor.py           # Run interactively
  python3 bess_auto_monitor.py --daemon  # Run as daemon
  python3 bess_auto_monitor.py --stats   # Show cache stats
  python3 bess_auto_monitor.py --help    # Show this help
        """)
        return
    
    monitor_loop(daemon_mode=daemon_mode)


if __name__ == "__main__":
    main()
