#!/usr/bin/env python3
"""
BESS Sheet Auto-Monitor for UpCloud Server
==========================================
Monitors cells A6, B6, I6, J6 and auto-triggers DNO lookup

Features:
- Monitors 4 cells: A6 (postcode), B6 (MPAN), I6, J6
- Auto-triggers DNO lookup when any cell changes
- In-memory caching (1-hour TTL)
- Data freshness indicators
- Systemd service compatible

Usage: python3 bess_auto_monitor_upcloud.py [--daemon|--stats|--help]
"""

import gspread
from google.oauth2.service_account import Credentials
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import sys
import subprocess
import os

# Configuration
SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
CHECK_INTERVAL = 30  # seconds
CACHE_TTL = 3600  # 1 hour
CREDENTIALS_PATH = "/root/.google-credentials/inner-cinema-credentials.json"
PROJECT_DIR = "/opt/bess"

# Simple in-memory cache
CACHE = {}

# Google Sheets scope
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def get_cache_key(a6: str, b6: str, i6: str, j6: str) -> str:
    """Generate cache key from all monitored inputs"""
    combined = f"{a6}_{b6}_{i6}_{j6}".lower().strip()
    return hashlib.md5(combined.encode()).hexdigest()


def get_cached_data(key: str) -> Optional[Dict]:
    """Retrieve cached data if still valid"""
    if key in CACHE:
        cached = CACHE[key]
        if datetime.now() < cached['expires']:
            age_seconds = (datetime.now() - cached['created']).seconds
            print(f"  ✅ Cache hit (age: {age_seconds}s)")
            return cached['data']
        else:
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
    print(f"  💾 Data cached (TTL: {CACHE_TTL}s)")


def connect_to_sheets():
    """Connect to Google Sheets"""
    try:
        creds = Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet('BESS')
        print("✅ Connected to BESS sheet")
        return sheet
    except Exception as e:
        print(f"❌ Failed to connect to sheets: {e}")
        return None


def get_monitored_cells(sheet: gspread.Worksheet) -> Tuple[str, str, str, str]:
    """Read all monitored cells: A6, B6, I6, J6"""
    try:
        a6 = str(sheet.acell('A6').value or '').strip()
        b6 = str(sheet.acell('B6').value or '').strip()
        i6 = str(sheet.acell('I6').value or '').strip()
        j6 = str(sheet.acell('J6').value or '').strip()
        return a6, b6, i6, j6
    except Exception as e:
        print(f"⚠️ Error reading cells: {e}")
        return '', '', '', ''


def calculate_data_freshness(last_update: datetime) -> str:
    """Calculate how fresh the data is"""
    age = datetime.now() - last_update
    age_minutes = age.seconds // 60
    
    if age_minutes < 10:
        return f"✅ FRESH ({age_minutes}min ago)"
    elif age_minutes < 60:
        return f"⚠️ {age_minutes}min ago"
    else:
        hours = age_minutes // 60
        return f"🔴 {hours}h ago"


def update_status_bar(sheet: gspread.Worksheet, message: str, color: str = '#4CAF50'):
    """Update status bar in A4"""
    try:
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_message = f"{message} | Updated: {timestamp}"
        sheet.update('A4', [[full_message]])
        sheet.format('A4:H4', {
            'backgroundColor': {'red': int(color[1:3], 16)/255, 
                               'green': int(color[3:5], 16)/255, 
                               'blue': int(color[5:7], 16)/255},
            'textFormat': {'bold': True}
        })
        print(f"  📊 Status: {message}")
    except Exception as e:
        print(f"  ⚠️ Failed to update status: {e}")


def trigger_dno_lookup(a6: str, b6: str, i6: str, j6: str, sheet: gspread.Worksheet):
    """Trigger DNO lookup Python script"""
    print(f"\n🔄 Triggering DNO lookup...")
    print(f"   A6 (Postcode): {a6}")
    print(f"   B6 (MPAN): {b6}")
    print(f"   I6: {i6}")
    print(f"   J6: {j6}")
    
    try:
        # Update status to "Loading"
        update_status_bar(sheet, "🔄 Refreshing DNO data...", '#FFEB3B')
        
        # Build command - pass MPAN and voltage from B6 and A10
        voltage = str(sheet.acell('A10').value or 'HV').strip()
        
        cmd = [
            'python3',
            os.path.join(PROJECT_DIR, 'dno_lookup_python.py'),
            b6 if b6 else '14',  # Default MPAN
            voltage
        ]
        
        # Run the DNO lookup script
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            update_status_bar(sheet, "✅ DNO data updated successfully", '#4CAF50')
            print("  ✅ DNO lookup completed successfully")
            return True
        else:
            update_status_bar(sheet, f"❌ Error: {result.stderr[:50]}", '#FF5252')
            print(f"  ❌ DNO lookup failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        update_status_bar(sheet, "❌ Timeout - DNO lookup took too long", '#FF5252')
        print("  ❌ DNO lookup timeout (>60s)")
        return False
    except Exception as e:
        update_status_bar(sheet, f"❌ Error: {str(e)[:50]}", '#FF5252')
        print(f"  ❌ Error triggering lookup: {e}")
        return False


def monitor_loop(daemon_mode: bool = False):
    """Main monitoring loop"""
    print("\n🔋 BESS AUTO-MONITOR STARTING")
    print("="*50)
    print(f"📍 Monitoring cells: A6, B6, I6, J6")
    print(f"⏰ Check interval: {CHECK_INTERVAL} seconds")
    print(f"💾 Cache TTL: {CACHE_TTL} seconds")
    print(f"📊 Sheet ID: {SHEET_ID}")
    print("="*50)
    
    sheet = connect_to_sheets()
    if not sheet:
        print("❌ Cannot start - failed to connect to sheets")
        sys.exit(1)
    
    last_values = None
    last_update = None
    
    print("\n👀 Monitoring started. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            # Read current values
            current = get_monitored_cells(sheet)
            a6, b6, i6, j6 = current
            
            # Check if any value changed
            if last_values != current:
                print(f"\n🔔 CHANGE DETECTED at {datetime.now().strftime('%H:%M:%S')}")
                print(f"   Previous: {last_values}")
                print(f"   Current:  {current}")
                
                # Check cache
                cache_key = get_cache_key(a6, b6, i6, j6)
                cached = get_cached_data(cache_key)
                
                if cached:
                    print("  ✅ Using cached data")
                    if last_update:
                        freshness = calculate_data_freshness(last_update)
                        update_status_bar(sheet, f"✅ Cached data ({freshness})", '#81C784')
                else:
                    print("  🔄 Cache miss - triggering lookup")
                    success = trigger_dno_lookup(a6, b6, i6, j6, sheet)
                    
                    if success:
                        # Cache the result
                        data = {'a6': a6, 'b6': b6, 'i6': i6, 'j6': j6}
                        set_cached_data(cache_key, data)
                        last_update = datetime.now()
                
                last_values = current
            else:
                # No change, show heartbeat in daemon mode
                if daemon_mode and datetime.now().second % 60 == 0:
                    print(f"💓 Heartbeat: {datetime.now().strftime('%H:%M:%S')} - No changes")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitor stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Monitor crashed: {e}")
        sys.exit(1)


def show_cache_stats():
    """Display cache statistics"""
    print("\n📊 CACHE STATISTICS")
    print("="*50)
    print(f"Total entries: {len(CACHE)}")
    
    if CACHE:
        print("\nCached entries:")
        for key, cached in CACHE.items():
            age = datetime.now() - cached['created']
            ttl_remaining = (cached['expires'] - datetime.now()).seconds
            print(f"  • {key[:8]}... (age: {age.seconds}s, TTL: {ttl_remaining}s)")
    else:
        print("  (no cached data)")
    
    print("="*50)


def show_help():
    """Display help message"""
    print("""
BESS Auto-Monitor Usage:
  python3 bess_auto_monitor_upcloud.py          # Run interactively
  python3 bess_auto_monitor_upcloud.py --daemon # Run as daemon
  python3 bess_auto_monitor_upcloud.py --stats  # Show cache stats
  python3 bess_auto_monitor_upcloud.py --help   # Show this help

Monitored Cells:
  A6 - Postcode
  B6 - MPAN ID
  I6 - Additional field 1
  J6 - Additional field 2

Configuration:
  Check Interval: {CHECK_INTERVAL} seconds
  Cache TTL: {CACHE_TTL} seconds
  Credentials: {CREDENTIALS_PATH}
  Project Dir: {PROJECT_DIR}
""")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--daemon':
            monitor_loop(daemon_mode=True)
        elif sys.argv[1] == '--stats':
            show_cache_stats()
        elif sys.argv[1] == '--help':
            show_help()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            show_help()
    else:
        monitor_loop(daemon_mode=False)
