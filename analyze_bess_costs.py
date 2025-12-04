#!/usr/bin/env python3
"""
BESS Cost Analysis - Populates BtM PPA Cost Comparison
Reads from BESS sheet, calculates costs for Non-BESS vs BESS scenarios
Writes to rows 27-37 (columns B-C for Non-BESS, E-F for BESS)
Uses batch reads to avoid API rate limits
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration
DASHBOARD_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

# Fixed levies (2025/26)
RATES = {
    'ccl': 0.00775,      # £/kWh
    'ro': 0.0619,        # £/kWh
    'fit': 0.0115,       # £/kWh
    'bsuos': 0.0045,     # £/kWh (average)
    'tnuos_hv': 0.0125,  # £/kWh (HV rate)
}

def connect():
    """Connect to Google Sheets using batch-friendly methods"""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return gspread.authorize(creds)

def read_bess_config(sheet):
    """Read all BESS configuration in ONE batch call"""
    print("📖 Reading BESS configuration (batch mode)...")
    
    # Single batch read of all needed ranges
    ranges = [
        'B10:D10',   # DUoS rates
        'B13:B15',   # Time bands
        'B17:B19',   # Battery params
        'B21',       # PPA rate (if exists)
        'B39',       # PPA Contract Price
        'A10',       # Voltage level
    ]
    
    batch_data = sheet.batch_get(ranges)
    
    # Parse results
    duos_rates = batch_data[0] if batch_data[0] else [[None, None, None]]
    time_bands = batch_data[1] if batch_data[1] else [[None], [None], [None]]
    battery_params = batch_data[2] if batch_data[2] else [[None], [None], [None]]
    ppa_b21 = batch_data[3][0][0] if batch_data[3] and batch_data[3][0] else None
    ppa_b39 = batch_data[4][0][0] if batch_data[4] and batch_data[4][0] else None
    voltage = batch_data[5][0][0] if batch_data[5] and batch_data[5][0] else 'HV'
    
    config = {
        # DUoS rates (convert p/kWh to £/kWh)
        'duos_red': float(duos_rates[0][0].replace(' p/kWh', '')) / 100 if duos_rates[0][0] else 0.01764,
        'duos_amber': float(duos_rates[0][1].replace(' p/kWh', '')) / 100 if duos_rates[0][1] else 0.00205,
        'duos_green': float(duos_rates[0][2].replace(' p/kWh', '')) / 100 if duos_rates[0][2] else 0.00011,
        
        # Time bands
        'red_hours': time_bands[0][0] if time_bands[0] else '08:00-16:00',
        'amber_hours': time_bands[1][0] if time_bands[1] else '19:30-22:00',
        'green_hours': time_bands[2][0] if time_bands[2] else 'All other',
        
        # Battery
        'capacity_kw': float(battery_params[0][0]) if battery_params[0] and battery_params[0][0] else 2500,
        'capacity_kwh': float(battery_params[1][0]) if battery_params[1] and battery_params[1][0] else 2500,
        'efficiency': 0.85,  # Default to 85% (B19 shows 2500, likely error)
        
        # PPA Rate
        'ppa_rate': float(ppa_b39.replace('£', '')) if ppa_b39 and '£' in str(ppa_b39) else 150.0,
        
        'voltage': voltage
    }
    
    print(f"   ✅ DUoS: RED {config['duos_red']*100:.3f}p | AMBER {config['duos_amber']*100:.3f}p | GREEN {config['duos_green']*100:.3f}p")
    print(f"   ✅ Battery: {config['capacity_kw']}kW / {config['capacity_kwh']}kWh")
    print(f"   ✅ PPA: £{config['ppa_rate']}/MWh")
    
    return config

def calculate_time_band_distribution(red_hours, amber_hours):
    """Calculate proportion of day in each band"""
    # Parse RED hours (e.g., "08:00-16:00")
    if '-' in red_hours:
        start, end = red_hours.split('-')
        red_start = int(start.split(':')[0])
        red_end = int(end.split(':')[0])
        red_pct = (red_end - red_start) / 24.0
    else:
        red_pct = 0.125  # Default ~3 hours
    
    # Parse AMBER hours
    if '-' in amber_hours:
        start, end = amber_hours.split('-')
        amber_start = int(start.split(':')[0])
        amber_end = int(end.split(':')[0])
        if amber_end < amber_start:
            amber_end += 24
        amber_pct = (amber_end - amber_start) / 24.0
    else:
        amber_pct = 0.104  # Default ~2.5 hours
    
    green_pct = 1.0 - red_pct - amber_pct
    
    return {
        'red': red_pct,
        'amber': amber_pct,
        'green': green_pct
    }

def calculate_non_bess_costs(config, daily_kwh=2500):
    """Calculate costs WITHOUT BESS - normal grid consumption"""
    
    # Time band distribution for typical commercial load
    bands = calculate_time_band_distribution(config['red_hours'], config['amber_hours'])
    
    # DUoS costs by time band
    duos_red_kwh = daily_kwh * bands['red']
    duos_amber_kwh = daily_kwh * bands['amber']
    duos_green_kwh = daily_kwh * bands['green']
    
    duos_red_cost = duos_red_kwh * config['duos_red']
    duos_amber_cost = duos_amber_kwh * config['duos_amber']
    duos_green_cost = duos_green_kwh * config['duos_green']
    duos_total = duos_red_cost + duos_amber_cost + duos_green_cost
    
    # Fixed levies (apply to all consumption)
    tnuos_kwh = daily_kwh
    tnuos_cost = tnuos_kwh * RATES['tnuos_hv']
    
    bnuos_kwh = daily_kwh
    bnuos_cost = bnuos_kwh * RATES['bsuos']
    
    ccl_cost = daily_kwh * RATES['ccl']
    ro_cost = daily_kwh * RATES['ro']
    fit_cost = daily_kwh * RATES['fit']
    
    return {
        'duos_red': {'kwh': duos_red_kwh, 'cost': duos_red_cost},
        'duos_amber': {'kwh': duos_amber_kwh, 'cost': duos_amber_cost},
        'duos_green': {'kwh': duos_green_kwh, 'cost': duos_green_cost},
        'duos_total': {'kwh': daily_kwh, 'cost': duos_total},
        'tnuos': {'kwh': tnuos_kwh, 'cost': tnuos_cost},
        'bnuos': {'kwh': bnuos_kwh, 'cost': bnuos_cost},
        'ccl': {'kwh': daily_kwh, 'cost': ccl_cost},
        'ro': {'kwh': daily_kwh, 'cost': ro_cost},
        'fit': {'kwh': daily_kwh, 'cost': fit_cost},
        'total': duos_total + tnuos_cost + bnuos_cost + ccl_cost + ro_cost + fit_cost
    }

def calculate_bess_costs(config, daily_kwh=2500):
    """Calculate costs WITH BESS - optimized time-shifting"""
    
    # BESS Strategy: Charge in GREEN, discharge in RED
    # Net grid consumption is reduced due to efficiency losses
    
    # Assume 1 cycle per day: charge 2.5 MWh, discharge 2.125 MWh (85% efficiency)
    charge_kwh = config['capacity_kwh']
    discharge_kwh = charge_kwh * config['efficiency']
    
    # Net consumption from grid (includes charging losses)
    net_grid_consumption = daily_kwh + (charge_kwh - discharge_kwh)
    
    # BESS charges during GREEN band only
    duos_green_kwh = charge_kwh
    duos_green_cost = duos_green_kwh * config['duos_green']
    
    # BESS discharges during RED band, offsetting RED consumption
    duos_red_kwh = 0  # Avoided by BESS discharge
    duos_red_cost = 0
    
    # Remaining consumption in AMBER/GREEN
    duos_amber_kwh = daily_kwh * 0.1  # Minimal AMBER usage
    duos_amber_cost = duos_amber_kwh * config['duos_amber']
    
    duos_total = duos_red_cost + duos_amber_cost + duos_green_cost
    
    # Fixed levies apply to NET grid consumption (including charging)
    tnuos_kwh = net_grid_consumption
    tnuos_cost = tnuos_kwh * RATES['tnuos_hv']
    
    bnuos_kwh = net_grid_consumption
    bnuos_cost = bnuos_kwh * RATES['bsuos']
    
    ccl_cost = net_grid_consumption * RATES['ccl']
    ro_cost = net_grid_consumption * RATES['ro']
    fit_cost = net_grid_consumption * RATES['fit']
    
    return {
        'duos_red': {'kwh': duos_red_kwh, 'cost': duos_red_cost},
        'duos_amber': {'kwh': duos_amber_kwh, 'cost': duos_amber_cost},
        'duos_green': {'kwh': duos_green_kwh, 'cost': duos_green_cost},
        'duos_total': {'kwh': duos_green_kwh + duos_amber_kwh, 'cost': duos_total},
        'tnuos': {'kwh': tnuos_kwh, 'cost': tnuos_cost},
        'bnuos': {'kwh': bnuos_kwh, 'cost': bnuos_cost},
        'ccl': {'kwh': net_grid_consumption, 'cost': ccl_cost},
        'ro': {'kwh': net_grid_consumption, 'cost': ro_cost},
        'fit': {'kwh': net_grid_consumption, 'cost': fit_cost},
        'total': duos_total + tnuos_cost + bnuos_cost + ccl_cost + ro_cost + fit_cost,
        'ppa_revenue': discharge_kwh * (config['ppa_rate'] / 1000)  # MWh to kWh
    }

def format_cost_data_for_sheet(non_bess, bess):
    """Format data for spreadsheet update (rows 27-37)"""
    
    # Build data rows matching spreadsheet structure
    # Row 27: DUoS header (already exists)
    # Row 28: Red
    # Row 29: Amber
    # Row 30: Green
    # Row 31: TNUoS
    # Row 32: BNUoS
    # Row 33: (blank)
    # Row 34: Environmental Levies header
    # Row 35: CCL
    # Row 36: RO
    # Row 37: FiT
    
    updates = []
    
    # Row 28: Red (Non-BESS: B28-C28, BESS: E28-F28)
    updates.append({
        'range': 'B28:C28',
        'values': [[f"{non_bess['duos_red']['kwh']:.1f}", f"£{non_bess['duos_red']['cost']:.2f}"]]
    })
    updates.append({
        'range': 'E28:F28',
        'values': [[f"{bess['duos_red']['kwh']:.1f}", f"£{bess['duos_red']['cost']:.2f}"]]
    })
    
    # Row 29: Amber
    updates.append({
        'range': 'B29:C29',
        'values': [[f"{non_bess['duos_amber']['kwh']:.1f}", f"£{non_bess['duos_amber']['cost']:.2f}"]]
    })
    updates.append({
        'range': 'E29:F29',
        'values': [[f"{bess['duos_amber']['kwh']:.1f}", f"£{bess['duos_amber']['cost']:.2f}"]]
    })
    
    # Row 30: Green
    updates.append({
        'range': 'B30:C30',
        'values': [[f"{non_bess['duos_green']['kwh']:.1f}", f"£{non_bess['duos_green']['cost']:.2f}"]]
    })
    updates.append({
        'range': 'E30:F30',
        'values': [[f"{bess['duos_green']['kwh']:.1f}", f"£{bess['duos_green']['cost']:.2f}"]]
    })
    
    # Row 31: TNUoS
    updates.append({
        'range': 'B31:C31',
        'values': [[f"{non_bess['tnuos']['kwh']:.1f}", f"£{non_bess['tnuos']['cost']:.2f}"]]
    })
    updates.append({
        'range': 'E31:F31',
        'values': [[f"{bess['tnuos']['kwh']:.1f}", f"£{bess['tnuos']['cost']:.2f}"]]
    })
    
    # Row 32: BNUoS
    updates.append({
        'range': 'B32:C32',
        'values': [[f"{non_bess['bnuos']['kwh']:.1f}", f"£{non_bess['bnuos']['cost']:.2f}"]]
    })
    updates.append({
        'range': 'E32:F32',
        'values': [[f"{bess['bnuos']['kwh']:.1f}", f"£{bess['bnuos']['cost']:.2f}"]]
    })
    
    # Row 35: CCL
    updates.append({
        'range': 'B35:C35',
        'values': [[f"{non_bess['ccl']['kwh']:.1f}", f"£{non_bess['ccl']['cost']:.2f}"]]
    })
    updates.append({
        'range': 'E35:F35',
        'values': [[f"{bess['ccl']['kwh']:.1f}", f"£{bess['ccl']['cost']:.2f}"]]
    })
    
    # Row 36: RO
    updates.append({
        'range': 'B36:C36',
        'values': [[f"{non_bess['ro']['kwh']:.1f}", f"£{non_bess['ro']['cost']:.2f}"]]
    })
    updates.append({
        'range': 'E36:F36',
        'values': [[f"{bess['ro']['kwh']:.1f}", f"£{bess['ro']['cost']:.2f}"]]
    })
    
    # Row 37: FiT
    updates.append({
        'range': 'B37:C37',
        'values': [[f"{non_bess['fit']['kwh']:.1f}", f"£{non_bess['fit']['cost']:.2f}"]]
    })
    updates.append({
        'range': 'E37:F37',
        'values': [[f"{bess['fit']['kwh']:.1f}", f"£{bess['fit']['cost']:.2f}"]]
    })
    
    return updates

def main():
    print("\n💰 BESS COST ANALYSIS - BtM PPA Comparison")
    print("=" * 60)
    
    try:
        # Connect
        gc = connect()
        sh = gc.open_by_key(DASHBOARD_ID)
        bess_sheet = sh.worksheet('BESS')
        
        # Read config (batch mode - only 1-2 API calls)
        config = read_bess_config(bess_sheet)
        
        # Calculate costs
        print("\n📊 Calculating Non-BESS scenario...")
        non_bess = calculate_non_bess_costs(config)
        print(f"   Total daily cost: £{non_bess['total']:.2f}")
        
        print("\n🔋 Calculating BESS scenario...")
        bess = calculate_bess_costs(config)
        print(f"   Total daily cost: £{bess['total']:.2f}")
        print(f"   PPA revenue: £{bess['ppa_revenue']:.2f}")
        print(f"   Net position: £{bess['ppa_revenue'] - bess['total']:.2f}/day")
        
        # Calculate savings
        savings = non_bess['total'] - bess['total']
        print(f"\n💰 BESS Savings: £{savings:.2f}/day (£{savings*365:.2f}/year)")
        
        # Format for spreadsheet
        print("\n📝 Preparing spreadsheet updates...")
        updates = format_cost_data_for_sheet(non_bess, bess)
        
        # Batch update (single API call for all updates)
        print("✍️  Writing to BESS sheet (batch mode)...")
        bess_sheet.batch_update(updates)
        
        # Add summary row (row 38)
        summary_updates = [
            {
                'range': 'C38',
                'values': [[f"£{non_bess['total']:.2f}"]]
            },
            {
                'range': 'F38',
                'values': [[f"£{bess['ppa_revenue'] - bess['total']:.2f}"]]
            }
        ]
        bess_sheet.batch_update(summary_updates)
        
        print("\n✅ ANALYSIS COMPLETE!")
        print(f"   Updated rows 28-37 with cost breakdowns")
        print(f"   Non-BESS total: £{non_bess['total']:.2f}/day")
        print(f"   BESS net: £{bess['ppa_revenue'] - bess['total']:.2f}/day")
        print(f"   Annual benefit: £{(bess['ppa_revenue'] - bess['total'])*365:.2f}")
        
        print(f"\n📊 View results: https://docs.google.com/spreadsheets/d/{DASHBOARD_ID}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
