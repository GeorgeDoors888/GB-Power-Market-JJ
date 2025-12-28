#!/usr/bin/env python3
"""
BESS Cost Analysis - Reads HH demand from spreadsheet
Populates BESS sheet rows 28-37 (Non-BESS cols B-C, BESS cols E-F)
Uses B17 (Min kW), B18 (Avg kW), B19 (Max kW) to calculate HH demand
"""
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
RATES = {'ccl': 0.00775, 'ro': 0.0619, 'fit': 0.0115, 'bsuos': 0.0045, 'tnuos': 0.0125,
         'duos_red': 0.01764, 'duos_amber': 0.00205, 'duos_green': 0.00011}

creds = Credentials.from_service_account_file('inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets'])
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet('BESS')

# Read facility demand (B17-B19), BESS spec (F13-F16), time bands (B13-B15)
config = sheet.batch_get(['B17:B19', 'F13:F16', 'B13:B15'])

# Facility demand (constant 2500 kW)
min_kw = float(config[0][0][0])  # B17
avg_kw = float(config[0][1][0])  # B18
max_kw = float(config[0][2][0])  # B19

# BESS parameters
bess_import_kw = float(config[1][0][0])  # F13
bess_export_kw = float(config[1][1][0])  # F14
bess_duration_hrs = float(config[1][2][0])  # F15
bess_cycles_max = float(config[1][3][0])  # F16
bess_capacity_kwh = bess_import_kw * bess_duration_hrs
efficiency = 0.85  # Round-trip efficiency

# Parse time bands
red_band = config[2][0][0]  # B13
amber_band = config[2][1][0]  # B14

# Calculate HH periods per band (48 HH periods per day)
# RED: 08:00-16:00 = 16 HH (8 hours * 2)
# AMBER: 19:30-22:00 = 5 HH (2.5 hours * 2)
# GREEN: Remaining = 27 HH
red_hh = 16
amber_hh = 5
green_hh = 27

# Calculate daily kWh per band - FACILITY DEMAND (constant 2500 kW load)
# Non-BESS: Facility consumes avg_kw constantly
daily_kwh = avg_kw * 24
red_kwh_nb = avg_kw * (red_hh * 0.5)  # 2500 kW * 8 hours = 20,000 kWh
amber_kwh_nb = avg_kw * (amber_hh * 0.5)  # 2500 kW * 2.5 hours = 6,250 kWh
green_kwh_nb = avg_kw * (green_hh * 0.5)  # 2500 kW * 13.5 hours = 33,750 kWh

# BESS Strategy: Charge in GREEN (cheap), discharge in RED (expensive)
# Charge during GREEN periods (up to battery capacity)
# Discharge during RED periods (reduce grid import)

# Max charge per cycle: bess_capacity_kwh / efficiency
# Max discharge per cycle: bess_capacity_kwh * efficiency
charge_per_cycle = bess_capacity_kwh / efficiency  # 5000 / 0.85 = 5882 kWh needed from grid
discharge_per_cycle = bess_capacity_kwh * efficiency  # 5000 * 0.85 = 4250 kWh supplied to facility

# With 1 cycle per day (charge in GREEN, discharge in RED)
charge_kwh = charge_per_cycle  # Grid import during GREEN
discharge_kwh = discharge_per_cycle  # Reduce grid import during RED

# BESS case: Facility still needs 60,000 kWh/day, but sourced differently
red_kwh_bess = red_kwh_nb - discharge_kwh  # Reduced RED import (20,000 - 4,250 = 15,750)
amber_kwh_bess = amber_kwh_nb  # No change (6,250)
green_kwh_bess = green_kwh_nb + charge_kwh  # Increased GREEN for charging (33,750 + 5,882 = 39,632)

def calc(scenario):
    if scenario == 'non_bess':
        red, amber, green = red_kwh_nb, amber_kwh_nb, green_kwh_nb
    else:
        red, amber, green = red_kwh_bess, amber_kwh_bess, green_kwh_bess
    
    total_kwh = daily_kwh
    
    duos = red*RATES['duos_red'] + amber*RATES['duos_amber'] + green*RATES['duos_green']
    return {
        'red': [red, f"£{red*RATES['duos_red']:.2f}"],
        'amber': [amber, f"£{amber*RATES['duos_amber']:.2f}"],
        'green': [green, f"£{green*RATES['duos_green']:.2f}"],
        'tnuos': [total_kwh, f"£{total_kwh*RATES['tnuos']:.2f}"],
        'bsuos': [total_kwh, f"£{total_kwh*RATES['bsuos']:.2f}"],
        'ccl': [total_kwh, f"£{total_kwh*RATES['ccl']:.2f}"],
        'ro': [total_kwh, f"£{total_kwh*RATES['ro']:.2f}"],
        'fit': [total_kwh, f"£{total_kwh*RATES['fit']:.2f}"]
    }

print(f"📊 Configuration Read:")
print(f"  Facility Demand: Min {min_kw} | Avg {avg_kw} | Max {max_kw} kW")
print(f"  BESS: {bess_import_kw} kW / {bess_capacity_kwh} kWh ({bess_duration_hrs}h duration)")
print(f"  Efficiency: {efficiency*100:.0f}%")
print(f"  RED band: {red_band} ({red_hh} HH = 8 hours)")
print(f"  AMBER band: {amber_band} ({amber_hh} HH = 2.5 hours)")
print(f"  GREEN: Remaining ({green_hh} HH = 13.5 hours)")
print(f"\n  Facility Daily Demand: {daily_kwh:.0f} kWh")
print(f"  Non-BESS Grid Import: RED {red_kwh_nb:.0f} | AMBER {amber_kwh_nb:.0f} | GREEN {green_kwh_nb:.0f} kWh")
print(f"  BESS Grid Import: RED {red_kwh_bess:.0f} | AMBER {amber_kwh_bess:.0f} | GREEN {green_kwh_bess:.0f} kWh")
print(f"  BESS Strategy: Charge {charge_kwh:.0f} kWh in GREEN, Discharge {discharge_kwh:.0f} kWh in RED")
print(f"  DUoS Savings: Shift {discharge_kwh:.0f} kWh from RED (£{RATES['duos_red']*1000:.2f}/MWh) to GREEN (£{RATES['duos_green']*1000:.2f}/MWh)\n")

nb = calc('non_bess')
bess = calc('bess')

# Build data arrays - rows 28-37
# 28: RED, 29: AMBER, 30: GREEN, 31: TNUoS, 32: BSUoS, 33: Empty, 34: Header (skip), 35: CCL, 36: RO, 37: FiT
nb_data_28_33 = [nb['red'], nb['amber'], nb['green'], nb['tnuos'], nb['bsuos'], ['','']]
nb_data_35_37 = [nb['ccl'], nb['ro'], nb['fit']]

bess_data_28_33 = [bess['red'], bess['amber'], bess['green'], bess['tnuos'], bess['bsuos'], ['','']]
bess_data_35_37 = [bess['ccl'], bess['ro'], bess['fit']]

# BATCH UPDATE - split ranges to skip row 34 header
sheet.batch_update([
    {'range': 'B28:C33', 'values': nb_data_28_33},
    {'range': 'B35:C37', 'values': nb_data_35_37},
    {'range': 'E28:F33', 'values': bess_data_28_33},
    {'range': 'E35:F37', 'values': bess_data_35_37}
])

print(f"✅ Updated BESS sheet with cost analysis")
print(f"Non-BESS DUoS: {nb['red'][1]} + {nb['amber'][1]} + {nb['green'][1]}")
print(f"BESS DUoS: {bess['red'][1]} + {bess['amber'][1]} + {bess['green'][1]}")
