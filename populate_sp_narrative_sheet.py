#!/usr/bin/env python3
"""
Populate Google Sheets with SP-by-SP Market Narrative Data
Updates the detailed settlement period breakdown with battery BM activity

Date: December 12, 2025
Author: GB Power Market JJ
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

print(f"Connected to: {sh.title}")
print(f"URL: {sh.url}")

# Create or get the SP Market Timeline sheet
try:
    ws = sh.worksheet('SP_Market_Timeline')
    print("Found existing 'SP_Market_Timeline' sheet")
except:
    print("Creating new 'SP_Market_Timeline' sheet...")
    ws = sh.add_worksheet(title='SP_Market_Timeline', rows=100, cols=20)

# Setup headers
headers = [
    'SP', 'Time', 'Actual_GW', 'Forecast_GW', 'Delta_GW', 'Tightness', 'Shortage',
    'BM_Intensity', 'Offer_MWh', 'Bid_MWh', 'Net_MWh', 'Offer_£_MWh', 'Bid_£_MWh',
    'Net_Cash_£', 'Top_BMU', 'Top_BMU_£', 'Top_BMU_Share_%', 'Headline'
]

ws.update(values=[headers], range_name='A1:R1')
ws.format('A1:R1', {
    'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
})

# Battery list
batteries = [
    ('T_LKSDB-1', 'Lakeside'),
    ('E_CONTB-1', 'Tesla'),
    ('T_WHLWB-1', 'Whitelee'),
    ('T_CAMLB-1', 'Camlan'),
    ('E_CLEBL-1', 'Cleator'),
    ('T_DRAXX-2', 'Drax'),
    ('E_CELRB-1', 'Cellarhead'),
    ('T_GRIFW-1', 'Grindon'),
    ('E_LNCSB-1', 'Landes'),
    ('T_NEDHB-1', 'Nedham')
]

date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
print(f"\nProcessing date: {date}")

# Collect all SP data
all_rows = []
total_volumes = []

for sp in range(1, 49):
    # Calculate time window
    hour = (sp - 1) // 2
    minute = 0 if (sp % 2 == 1) else 30
    time_start = f"{hour:02d}:{minute:02d}"
    time_end = f"{hour:02d}:{minute+30:02d}" if minute == 0 else f"{(hour+1):02d}:00"
    
    sp_offer_vol = 0
    sp_offer_cash = 0
    sp_bid_vol = 0
    sp_bid_cash = 0
    sp_batteries = []
    
    for bmu_id, name in batteries:
        bmu_offer_vol = 0
        bmu_offer_cash = 0
        bmu_bid_vol = 0
        bmu_bid_cash = 0
        
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
                            bmu_bid_cash += abs(val)
            
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
                            bmu_offer_cash += abs(val)
            
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
            
            time.sleep(0.05)
            
        except:
            continue
        
        sp_offer_vol += bmu_offer_vol
        sp_offer_cash += bmu_offer_cash
        sp_bid_vol += bmu_bid_vol
        sp_bid_cash += bmu_bid_cash
        
        total_cash = bmu_offer_cash + bmu_bid_cash
        if total_cash > 0:
            sp_batteries.append({
                'name': name,
                'cash': total_cash,
                'offer_cash': bmu_offer_cash,
                'bid_cash': bmu_bid_cash
            })
    
    # Calculate metrics
    offer_ewap = (sp_offer_cash / sp_offer_vol) if sp_offer_vol > 0 else 0
    bid_ewap = (sp_bid_cash / sp_bid_vol) if sp_bid_vol > 0 else 0
    net_mwh = sp_offer_vol - sp_bid_vol
    net_cash = sp_offer_cash - sp_bid_cash
    
    total_volumes.append(abs(sp_offer_vol) + abs(sp_bid_vol))
    
    # Find top battery
    top_bmu = '-'
    top_bmu_cash = 0
    top_bmu_share = 0
    if sp_batteries:
        sp_batteries.sort(key=lambda x: x['cash'], reverse=True)
        top_bmu = sp_batteries[0]['name']
        top_bmu_cash = sp_batteries[0]['cash']
        sp_total_cash = sp_offer_cash + sp_bid_cash
        top_bmu_share = (top_bmu_cash / sp_total_cash * 100) if sp_total_cash > 0 else 0
    
    # Classify market state
    if net_mwh > 50:
        tightness = "Tight"
        shortage = "Short power"
    elif net_mwh < -50:
        tightness = "Long"
        shortage = "Surplus power"
    else:
        tightness = "Balanced"
        shortage = "Matched"
    
    # Generate headline
    if tightness == "Tight" and net_mwh > 50:
        headline = "NESO buying power: discharge utilization"
    elif tightness == "Long" and net_mwh < -50:
        headline = "NESO absorbing surplus: charging dominant"
    elif top_bmu_cash > 1000:
        action = "discharge" if sp_batteries[0]['offer_cash'] > sp_batteries[0]['bid_cash'] else "charge"
        headline = f"{top_bmu} {action} dominant: £{top_bmu_cash:,.0f}"
    else:
        headline = "Standard balancing: mixed actions"
    
    # Build row
    row = [
        sp,
        f"{time_start}-{time_end}",
        0,  # Actual_GW (would need demand data)
        0,  # Forecast_GW (would need forecast data)
        0,  # Delta_GW
        tightness,
        shortage,
        '',  # BM_Intensity (will calculate after percentiles)
        round(sp_offer_vol, 2),
        round(sp_bid_vol, 2),
        round(net_mwh, 2),
        round(offer_ewap, 2),
        round(bid_ewap, 2),
        round(net_cash, 2),
        top_bmu,
        round(top_bmu_cash, 2),
        round(top_bmu_share, 1),
        headline
    ]
    
    all_rows.append(row)
    
    if sp % 10 == 0:
        print(f"  Processed SP {sp}/48...")

# Calculate BM intensity percentiles
import numpy as np
sorted_vols = sorted(total_volumes)
p33 = sorted_vols[int(len(sorted_vols) * 0.33)]
p66 = sorted_vols[int(len(sorted_vols) * 0.66)]

for i, row in enumerate(all_rows):
    vol = total_volumes[i]
    if vol < p33:
        intensity = "Low"
    elif vol < p66:
        intensity = "Med"
    else:
        intensity = "High"
    all_rows[i][7] = intensity  # Update BM_Intensity column

# Update sheet with all data
print(f"\nWriting {len(all_rows)} rows to Google Sheets...")
ws.update(values=all_rows, range_name='A2:R49')

# Apply formatting
ws.format('A2:R49', {
    'numberFormat': {
        'type': 'NUMBER',
        'pattern': '#,##0.00'
    }
})

# Format currency columns
ws.format('L2:L49', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0.00'}})
ws.format('M2:M49', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0.00'}})
ws.format('N2:N49', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0.00'}})
ws.format('P2:P49', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0.00'}})

# Conditional formatting for tightness
ws.format('F2:F49', {
    'textFormat': {'bold': True}
})

print("\n✅ Sheet updated successfully!")
print(f"   Sheet: SP_Market_Timeline")
print(f"   Data: {date} (48 settlement periods)")
print(f"   URL: {sh.url}")

# Summary stats
total_offer = sum(row[8] for row in all_rows)
total_bid = sum(row[9] for row in all_rows)
total_revenue = sum(row[13] for row in all_rows)

print(f"\nSummary:")
print(f"   Total Discharge (Offer): {total_offer:.2f} MWh")
print(f"   Total Charge (Bid): {total_bid:.2f} MWh")
print(f"   Net Revenue: £{total_revenue:,.2f}")
print(f"   Avg Offer Price: £{sum(row[11] for row in all_rows if row[11] > 0)/len([r for r in all_rows if r[11] > 0]):.2f}/MWh")
print(f"   Avg Bid Price: £{sum(row[12] for row in all_rows if row[12] > 0)/len([r for r in all_rows if r[12] > 0]):.2f}/MWh")
