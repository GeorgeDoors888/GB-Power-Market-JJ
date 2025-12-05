#!/usr/bin/env python3
"""
BESS Dashboard Enhanced - Real-time DUoS Rate Display
Adds live time-of-day rate calculations with next band change countdown
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime, timedelta
import pytz

SHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

# DUoS time bands (UK time)
DUOS_BANDS = {
    'RED': {
        'periods': [(16, 0, 19, 30)],  # 16:00-19:30 weekdays
        'weekdays_only': True
    },
    'AMBER': {
        'periods': [(8, 0, 16, 0), (19, 30, 22, 0)],  # 08:00-16:00, 19:30-22:00 weekdays
        'weekdays_only': True
    },
    'GREEN': {
        'periods': [(0, 0, 8, 0), (22, 0, 23, 59)],  # 00:00-08:00, 22:00-23:59 + all weekend
        'weekdays_only': False
    }
}

def get_current_duos_band():
    """Determine current DUoS band based on UK time"""
    uk_tz = pytz.timezone('Europe/London')
    now = datetime.now(uk_tz)
    
    is_weekend = now.weekday() >= 5  # Saturday=5, Sunday=6
    hour = now.hour
    minute = now.minute
    current_mins = hour * 60 + minute
    
    if is_weekend:
        return 'GREEN', 'All day (weekend)'
    
    # Check RED
    if 16 * 60 <= current_mins < 19 * 60 + 30:
        return 'RED', '16:00-19:30'
    
    # Check AMBER
    if (8 * 60 <= current_mins < 16 * 60) or (19 * 60 + 30 <= current_mins < 22 * 60):
        return 'AMBER', '08:00-16:00 or 19:30-22:00'
    
    # Otherwise GREEN
    return 'GREEN', '00:00-08:00 or 22:00-23:59'

def get_next_band_change():
    """Calculate time until next DUoS band change"""
    uk_tz = pytz.timezone('Europe/London')
    now = datetime.now(uk_tz)
    
    is_weekend = now.weekday() >= 5
    hour = now.hour
    minute = now.minute
    
    if is_weekend:
        # Next change is Monday 08:00
        days_until_monday = (7 - now.weekday()) % 7
        next_change = now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
        next_band = 'AMBER'
    elif hour < 8:
        # Next is 08:00 AMBER
        next_change = now.replace(hour=8, minute=0, second=0, microsecond=0)
        next_band = 'AMBER'
    elif hour < 16:
        # Next is 16:00 RED
        next_change = now.replace(hour=16, minute=0, second=0, microsecond=0)
        next_band = 'RED'
    elif hour < 19 or (hour == 19 and minute < 30):
        # Next is 19:30 AMBER
        next_change = now.replace(hour=19, minute=30, second=0, microsecond=0)
        next_band = 'AMBER'
    elif hour < 22:
        # Next is 22:00 GREEN
        next_change = now.replace(hour=22, minute=0, second=0, microsecond=0)
        next_band = 'GREEN'
    else:
        # Next is tomorrow 08:00 AMBER
        next_change = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        next_band = 'AMBER'
    
    time_diff = next_change - now
    hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    
    return next_band, f"{hours}h {minutes}m"

def get_duos_rates_for_dno(dno_name, voltage):
    """Fetch DUoS rates from BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        red_rate_p_kwh,
        amber_rate_p_kwh,
        green_rate_p_kwh
    FROM `{PROJECT_ID}.gb_power.duos_unit_rates`
    WHERE dno_name = '{dno_name}'
      AND voltage_level = '{voltage}'
    LIMIT 1
    """
    
    try:
        result = client.query(query).to_dataframe()
        if not result.empty:
            return {
                'RED': result['red_rate_p_kwh'].iloc[0],
                'AMBER': result['amber_rate_p_kwh'].iloc[0],
                'GREEN': result['green_rate_p_kwh'].iloc[0]
            }
    except Exception as e:
        print(f"   ❌ Error fetching DUoS rates: {e}")
    
    return None

def update_bess_sheet_with_live_rates():
    """Update BESS sheet with current DUoS band and countdown"""
    
    print('\n🔋 BESS DASHBOARD - LIVE DUoS RATE UPDATER')
    print('='*80)
    
    # Connect to sheets
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scope)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SHEET_ID)
    
    try:
        bess_sheet = ss.worksheet('BESS')
    except:
        print('   ❌ BESS sheet not found')
        return
    
    # Get current DNO and voltage from sheet
    try:
        dno_name = bess_sheet.acell('C6').value  # Assuming DNO name in C6
        voltage = bess_sheet.acell('A9').value   # Assuming voltage in A9
        
        if not dno_name or not voltage:
            print('   ⚠️  DNO or voltage not set in BESS sheet')
            return
            
        print(f'\n📋 Current Configuration:')
        print(f'   DNO: {dno_name}')
        print(f'   Voltage: {voltage}')
        
    except Exception as e:
        print(f'   ❌ Error reading BESS sheet: {e}')
        return
    
    # Get current DUoS band
    current_band, band_period = get_current_duos_band()
    next_band, time_until = get_next_band_change()
    
    print(f'\n⏰ Current Time: {datetime.now(pytz.timezone("Europe/London")).strftime("%Y-%m-%d %H:%M:%S %Z")}')
    print(f'   Current Band: {current_band} ({band_period})')
    print(f'   Next Band: {next_band} in {time_until}')
    
    # Get DUoS rates
    rates = get_duos_rates_for_dno(dno_name, voltage)
    
    if rates:
        current_rate = rates[current_band]
        print(f'\n💰 Current DUoS Rate: {current_rate:.3f} p/kWh ({current_band} band)')
        print(f'   RED:   {rates["RED"]:.3f} p/kWh')
        print(f'   AMBER: {rates["AMBER"]:.3f} p/kWh')
        print(f'   GREEN: {rates["GREEN"]:.3f} p/kWh')
        
        # Update sheet with live info (add to new section)
        # Assuming we add this info starting at row 15
        updates = [
            ['LIVE DUoS INFORMATION', ''],
            ['Current Time:', datetime.now(pytz.timezone("Europe/London")).strftime("%Y-%m-%d %H:%M:%S")],
            ['Current Band:', current_band],
            ['Current Rate (p/kWh):', current_rate],
            ['Next Band:', f'{next_band} in {time_until}'],
            ['', ''],
            ['Daily DUoS Profile:', ''],
            ['RED (16:00-19:30):', f'{rates["RED"]:.3f} p/kWh'],
            ['AMBER (08:00-16:00, 19:30-22:00):', f'{rates["AMBER"]:.3f} p/kWh'],
            ['GREEN (Off-peak + Weekend):', f'{rates["GREEN"]:.3f} p/kWh']
        ]
        
        # Write to sheet (starting at A15)
        bess_sheet.update(values=updates, range_name='A15:B24')
        
        # Color code current band
        if current_band == 'RED':
            bess_sheet.format('C15', {'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}})
        elif current_band == 'AMBER':
            bess_sheet.format('C15', {'backgroundColor': {'red': 1.0, 'green': 0.9, 'blue': 0.7}})
        else:
            bess_sheet.format('C15', {'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}})
        
        print('\n✅ BESS sheet updated with live DUoS information')
        
    else:
        print('\n   ❌ Could not fetch DUoS rates')
    
    print(f'\n🔗 View dashboard: https://docs.google.com/spreadsheets/d/{SHEET_ID}/')
    print('='*80 + '\n')

if __name__ == '__main__':
    update_bess_sheet_with_live_rates()
