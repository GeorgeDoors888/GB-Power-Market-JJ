#!/usr/bin/env python3
"""
Fix Battery BM Revenue Section Layout in Google Sheets
Properly structures the battery trading data with enhanced analysis

Date: December 13, 2025
"""

import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEETS_CONFIG
import requests
from datetime import datetime, timedelta
import time

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(CREDS)

SHEET_ID = GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_ID']
sh = gc.open_by_key(SHEET_ID)
ws = sh.worksheet('Live Dashboard v2')

print(f"Connected to: {sh.title}")
print(f"URL: {sh.url}")

# Battery list
batteries = [
    ('T_LKSDB-1', 'Lakeside'),
    ('E_CONTB-1', 'Tesla Hornsea'),
    ('T_WHLWB-1', 'Whitelee')
]

date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
print(f"\nCollecting battery data for: {date}")

# Collect data for all batteries
battery_data = []
total_offer_rev = 0
total_bid_rev = 0
total_offer_vol = 0
total_bid_vol = 0
active_sps = set()

for bmu_id, name in batteries:
    bmu_offer_rev = 0
    bmu_offer_vol = 0
    bmu_bid_rev = 0
    bmu_bid_vol = 0
    
    for sp in range(1, 49):
        try:
            # BID cashflows
            url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/bid/{date}/{sp}?bmUnit={bmu_id}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and len(data['data']) > 0:
                    cf = data['data'][0].get('bidOfferPairCashflows', {})
                    for key, val in cf.items():
                        if val is not None and key != 'totalCashflow':
                            bmu_bid_rev += abs(val)
            
            # BID volumes
            url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/bid/{date}/{sp}?bmUnit={bmu_id}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and len(data['data']) > 0:
                    pv = data['data'][0].get('pairVolumes', {})
                    for key, val in pv.items():
                        if val is not None and key != 'totalVolume':
                            bmu_bid_vol += abs(val)
            
            # OFFER cashflows
            url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/offer/{date}/{sp}?bmUnit={bmu_id}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and len(data['data']) > 0:
                    cf = data['data'][0].get('bidOfferPairCashflows', {})
                    for key, val in cf.items():
                        if val is not None and key != 'totalCashflow':
                            bmu_offer_rev += abs(val)
            
            # OFFER volumes
            url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/offer/{date}/{sp}?bmUnit={bmu_id}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and len(data['data']) > 0:
                    pv = data['data'][0].get('pairVolumes', {})
                    for key, val in pv.items():
                        if val is not None and key != 'totalVolume':
                            bmu_offer_vol += abs(val)
            
            # Track active SPs
            if bmu_offer_rev > 0 or bmu_bid_rev > 0:
                active_sps.add(sp)
            
            time.sleep(0.05)
            
        except Exception as e:
            continue
    
    # Calculate metrics for this battery
    total_rev = bmu_offer_rev + bmu_bid_rev
    total_vol = bmu_offer_vol + bmu_bid_vol
    avg_price = (total_rev / total_vol) if total_vol > 0 else 0
    revenue_type = "Discharge" if bmu_offer_rev > bmu_bid_rev else "Charge"
    
    # Determine status
    if total_rev > 50000:
        status = "🔥 High"
    elif total_rev > 10000:
        status = "✅ Active"
    elif total_rev > 0:
        status = "⚪ Low"
    else:
        status = "❌ None"
    
    battery_data.append({
        'bmu_id': bmu_id,
        'name': name,
        'total_rev': total_rev,
        'total_vol': total_vol,
        'avg_price': avg_price,
        'offer_rev': bmu_offer_rev,
        'bid_rev': bmu_bid_rev,
        'offer_vol': bmu_offer_vol,
        'bid_vol': bmu_bid_vol,
        'type': revenue_type,
        'status': status
    })
    
    total_offer_rev += bmu_offer_rev
    total_bid_rev += bmu_bid_rev
    total_offer_vol += bmu_offer_vol
    total_bid_vol += bmu_bid_vol
    
    print(f"  {name}: £{total_rev:,.2f} ({revenue_type})")

# Calculate summary metrics
net_revenue = total_offer_rev - total_bid_rev
total_revenue = total_offer_rev + total_bid_rev
avg_sp_revenue = total_revenue / len(active_sps) if active_sps else 0
discharge_share = (total_offer_rev / total_revenue * 100) if total_revenue > 0 else 0

print(f"\n📊 Summary:")
print(f"  Total Revenue: £{total_revenue:,.2f}")
print(f"  Net Revenue: £{net_revenue:+,.2f}")
print(f"  Active SPs: {len(active_sps)}/48 ({len(active_sps)/48*100:.0f}%)")
print(f"  Avg per SP: £{avg_sp_revenue:,.2f}")
print(f"  Discharge share: {discharge_share:.1f}%")

# Clear existing battery section (rows 38-50)
print("\n🧹 Clearing old battery section...")
ws.batch_clear(['A38:H50'])

# Build new layout
rows_to_update = []

# Row 38: Main header
header = f"🔋 BATTERY BM REVENUE — {date} | {len(active_sps)}/48 Active SPs ({len(active_sps)/48*100:.0f}%) | Net: £{net_revenue:+,.0f}"
rows_to_update.append(['', '', '', header, '', '', '', ''])

# Row 39: Subheader with key metrics
subheader = f"Discharge: £{total_offer_rev:,.0f} ({discharge_share:.0f}%) | Charge: £{total_bid_rev:,.0f} | Avg per SP: £{avg_sp_revenue:,.0f}"
rows_to_update.append(['', '', '', subheader, '', '', '', ''])

# Row 40: Column headers
rows_to_update.append(['', '', '', 'BMU ID', 'Name', 'Revenue (£)', 'Volume (MWh)', 'Avg £/MWh', 'Type', 'Status'])

# Rows 41-43: Battery data (sorted by revenue)
battery_data.sort(key=lambda x: x['total_rev'], reverse=True)
for bat in battery_data:
    rows_to_update.append([
        '', '', '',
        bat['bmu_id'],
        bat['name'],
        round(bat['total_rev'], 2),
        round(bat['total_vol'], 2),
        round(bat['avg_price'], 2),
        bat['type'],
        bat['status']
    ])

# Row 44: Blank spacer
rows_to_update.append(['', '', '', '', '', '', '', '', '', ''])

# Row 45: Market Analysis header
rows_to_update.append(['', '', '', '📊 MARKET ANALYSIS', '', '', '', '', '', ''])

# Row 46: Price analysis
avg_discharge_price = (total_offer_rev / total_offer_vol) if total_offer_vol > 0 else 0
avg_charge_price = (total_bid_rev / total_bid_vol) if total_bid_vol > 0 else 0
price_spread = avg_discharge_price - avg_charge_price

rows_to_update.append([
    '', '', '',
    'Avg Discharge Price:',
    f'£{avg_discharge_price:,.2f}/MWh',
    'Avg Charge Price:',
    f'£{avg_charge_price:,.2f}/MWh',
    'Spread:',
    f'£{price_spread:,.2f}/MWh'
])

# Row 47: Volume analysis
total_volume = total_offer_vol + total_bid_vol
net_volume = total_offer_vol - total_bid_vol
rows_to_update.append([
    '', '', '',
    'Total Volume:',
    f'{total_volume:.2f} MWh',
    'Net Volume:',
    f'{net_volume:+.2f} MWh',
    'Utilization:',
    f'{len(active_sps)/48*100:.0f}%'
])

# Row 48: Revenue efficiency
revenue_per_mwh = total_revenue / total_volume if total_volume > 0 else 0
rows_to_update.append([
    '', '', '',
    'Revenue Efficiency:',
    f'£{revenue_per_mwh:,.2f}/MWh',
    'Revenue per SP:',
    f'£{avg_sp_revenue:,.2f}',
    'Total Active:',
    f'{len(active_sps)} SPs'
])

# Row 49: Market interpretation
if discharge_share > 70:
    market_state = "TIGHT - High discharge demand (system short)"
elif discharge_share < 30:
    market_state = "LONG - High charge activity (system surplus)"
else:
    market_state = "BALANCED - Mixed discharge/charge activity"

rows_to_update.append([
    '', '', '',
    'Market State:',
    market_state,
    '',
    '',
    '',
    ''
])

# Row 50: Data note
rows_to_update.append([
    '', '', '',
    '⚠️ Note: VTP aggregated revenue data not available via BMRS API (proprietary settlement)',
    '',
    '',
    '',
    '',
    ''
])

# Update sheet
print("\n📝 Writing to Google Sheets...")
ws.update(values=rows_to_update, range_name='A38:J50')

# Apply formatting
print("🎨 Applying formatting...")

# Header row (38)
ws.format('D38:H38', {
    'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 11},
    'horizontalAlignment': 'LEFT'
})

# Subheader (39)
ws.format('D39:H39', {
    'backgroundColor': {'red': 0.85, 'green': 0.92, 'blue': 1},
    'textFormat': {'bold': True, 'fontSize': 10},
    'horizontalAlignment': 'LEFT'
})

# Column headers (40)
ws.format('D40:J40', {
    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
    'textFormat': {'bold': True},
    'horizontalAlignment': 'CENTER'
})

# Data rows (41-43) - currency format
ws.format('F41:F43', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0.00'}})
ws.format('G41:G43', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'}})
ws.format('H41:H43', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0.00'}})

# Analysis section header (45)
ws.format('D45:H45', {
    'backgroundColor': {'red': 1, 'green': 0.85, 'blue': 0.4},
    'textFormat': {'bold': True, 'fontSize': 10},
    'horizontalAlignment': 'LEFT'
})

# Analysis data (46-49)
ws.format('E46:E49', {'textFormat': {'bold': True}})
ws.format('G46:G49', {'textFormat': {'bold': True}})
ws.format('I46:I49', {'textFormat': {'bold': True}})

# Note row (50)
ws.format('D50:J50', {
    'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.8},
    'textFormat': {'italic': True, 'fontSize': 9}
})

print("\n✅ Battery section updated successfully!")
print(f"   Rows 38-50 now contain enhanced battery analysis")
print(f"   View at: {sh.url}")
