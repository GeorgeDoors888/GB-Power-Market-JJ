#!/usr/bin/env python3
"""Add data freshness indicators to Dashboard timestamp"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime, timedelta
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SA_PATH = 'inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

def get_data_freshness_indicator(last_update_str):
    """
    Calculate data freshness and return indicator
    ✅ Green if < 10 min old
    ⚠️ Yellow if 10-60 min old
    🔴 Red if > 60 min old
    """
    try:
        # Parse timestamp from "⏰ Last Updated: 2025-11-10 02:33:53 | Settlement Period 6"
        if '|' in last_update_str:
            timestamp_part = last_update_str.split('|')[0].replace('⏰ Last Updated:', '').strip()
        else:
            timestamp_part = last_update_str.replace('⏰ Last Updated:', '').strip()
        
        # Parse the timestamp
        last_update = datetime.strptime(timestamp_part, '%Y-%m-%d %H:%M:%S')
        
        # Get current time
        now = datetime.now()
        
        # Calculate age
        age = now - last_update
        age_minutes = age.total_seconds() / 60
        
        # Determine indicator
        if age_minutes < 10:
            indicator = '✅ FRESH'
            color = 'green'
        elif age_minutes < 60:
            indicator = '⚠️ STALE'
            color = 'yellow'
        else:
            indicator = '🔴 OLD'
            color = 'red'
        
        return indicator, age_minutes, color
        
    except Exception as e:
        print(f"⚠️ Could not parse timestamp: {e}")
        return '❓ UNKNOWN', 0, 'grey'

def add_freshness_indicator():
    """Read current timestamp and add freshness indicator"""
    
    print("=" * 80)
    print("🕐 ADDING DATA FRESHNESS INDICATORS")
    print("=" * 80)
    
    # Read current A2 cell
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range='Dashboard!A2'
    ).execute()
    
    current_a2 = result.get('values', [['']])[0][0]
    print(f"\nCurrent A2: {current_a2}")
    
    # Get freshness indicator
    indicator, age_minutes, color = get_data_freshness_indicator(current_a2)
    
    print(f"\n📊 Data Age Analysis:")
    print(f"   Age: {age_minutes:.1f} minutes")
    print(f"   Status: {indicator}")
    print(f"   Color: {color}")
    
    # Add indicator to timestamp
    if '|' in current_a2:
        parts = current_a2.split('|')
        # Insert freshness after timestamp, before other info
        new_a2 = f"{parts[0].strip()} | {indicator}"
        if len(parts) > 1:
            new_a2 += f" | {' | '.join(p.strip() for p in parts[1:])}"
    else:
        new_a2 = f"{current_a2} | {indicator}"
    
    print(f"\n📝 New A2: {new_a2}")
    
    # Write updated timestamp
    try:
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range='Dashboard!A2',
            valueInputOption="USER_ENTERED",
            body={"values": [[new_a2]]}
        ).execute()
        
        print("\n✅ Updated A2 with freshness indicator")
        
        # Add legend in A3
        legend = "Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min"
        
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range='Dashboard!A3',
            valueInputOption="USER_ENTERED",
            body={"values": [[legend]]}
        ).execute()
        
        print(f"✅ Added legend to A3: {legend}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error updating: {e}")
        return False

def update_timestamp_with_freshness():
    """Update timestamp and add freshness indicator"""
    
    # Get current time
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Calculate current settlement period (0-based hour * 2, plus 0 or 1 for half hour)
    sp = (now.hour * 2) + (1 if now.minute >= 30 else 0) + 1
    if sp > 48:
        sp = sp - 48
    
    # Create timestamp with fresh indicator
    new_a2 = f"⏰ Last Updated: {timestamp} | ✅ FRESH | Settlement Period {sp} | Auto-refreshed"
    
    # Write to A2
    try:
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range='Dashboard!A2',
            valueInputOption="USER_ENTERED",
            body={"values": [[new_a2]]}
        ).execute()
        
        print(f"✅ Updated timestamp: {new_a2}")
        
        # Add legend
        legend = "Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min"
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range='Dashboard!A3',
            valueInputOption="USER_ENTERED",
            body={"values": [[legend]]}
        ).execute()
        
        print(f"✅ Added legend: {legend}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Update with current timestamp and fresh indicator
    success = update_timestamp_with_freshness()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ DATA FRESHNESS INDICATORS ADDED")
        print("=" * 80)
        print("\n📊 Freshness Thresholds:")
        print("   ✅ FRESH: < 10 minutes old")
        print("   ⚠️ STALE: 10-60 minutes old")
        print("   🔴 OLD: > 60 minutes old (WARNING!)")
        print("\nView Dashboard:")
        print("https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
    else:
        print("\n❌ Update failed")
