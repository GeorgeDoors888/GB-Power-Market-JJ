#!/usr/bin/env python3
"""
Simple Battery BM Revenue Updater - NO FORMATTING, JUST DATA
"""
import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEETS_CONFIG
import requests
from datetime import datetime, timedelta
import time

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
gc = gspread.authorize(Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES))

sh = gc.open_by_key(GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_ID'])
ws = sh.worksheet('Live Dashboard v2')

BATTERIES = [
    ('T_LKSDB-1', 'Lakeside'),
    ('E_CONTB-1', 'Tesla'),
    ('T_WHLWB-1', 'Whitelee')
]

date = '2025-12-10'
print(f"Getting battery data for {date}...")

# Collect data
all_batteries = []
for bmu_id, name in BATTERIES:
    offer_cash = 0
    bid_cash = 0
    offer_vol = 0
    bid_vol = 0
    
    for sp in range(1, 49):
        try:
            # Get cashflows
            r = requests.get(f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/offer/{date}/{sp}?bmUnit={bmu_id}", timeout=5)
            if r.status_code == 200 and 'data' in r.json() and r.json()['data']:
                cf = r.json()['data'][0].get('bidOfferPairCashflows', {})
                for k, v in cf.items():
                    if v and k != 'totalCashflow':
                        offer_cash += abs(v)
            
            r = requests.get(f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/bid/{date}/{sp}?bmUnit={bmu_id}", timeout=5)
            if r.status_code == 200 and 'data' in r.json() and r.json()['data']:
                cf = r.json()['data'][0].get('bidOfferPairCashflows', {})
                for k, v in cf.items():
                    if v and k != 'totalCashflow':
                        bid_cash += abs(v)
            
            # Get volumes
            r = requests.get(f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/offer/{date}/{sp}?bmUnit={bmu_id}", timeout=5)
            if r.status_code == 200 and 'data' in r.json() and r.json()['data']:
                pv = r.json()['data'][0].get('pairVolumes', {})
                for k, v in pv.items():
                    if v and k != 'totalVolume':
                        offer_vol += abs(v)
            
            r = requests.get(f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/bid/{date}/{sp}?bmUnit={bmu_id}", timeout=5)
            if r.status_code == 200 and 'data' in r.json() and r.json()['data']:
                pv = r.json()['data'][0].get('pairVolumes', {})
                for k, v in pv.items():
                    if v and k != 'totalVolume':
                        bid_vol += abs(v)
            
            time.sleep(0.05)
        except:
            continue
    
    total_rev = offer_cash + bid_cash
    total_vol = offer_vol + bid_vol
    all_batteries.append({
        'id': bmu_id,
        'name': name,
        'revenue': total_rev,
        'volume': total_vol,
        'price': total_rev/total_vol if total_vol > 0 else 0,
        'type': 'Discharge' if offer_cash > bid_cash else 'Charge'
    })
    print(f"  {name}: £{total_rev:,.0f}")

# Sort by revenue
all_batteries.sort(key=lambda x: x['revenue'], reverse=True)

# Simple data rows - NO FANCY FORMATTING  
data = [
    ['', '', '', '🔋 Battery BM Revenue', date, '', '', ''],
    ['', '', '', 'BMU', 'Name', 'Revenue £', 'MWh', 'Type'],
    ['', '', '', all_batteries[0]['id'], all_batteries[0]['name'], f"£{all_batteries[0]['revenue']:,.0f}", f"{all_batteries[0]['volume']:.1f}", all_batteries[0]['type']],
    ['', '', '', all_batteries[1]['id'], all_batteries[1]['name'], f"£{all_batteries[1]['revenue']:,.0f}", f"{all_batteries[1]['volume']:.1f}", all_batteries[1]['type']],
    ['', '', '', all_batteries[2]['id'], all_batteries[2]['name'], f"£{all_batteries[2]['revenue']:,.0f}", f"{all_batteries[2]['volume']:.1f}", all_batteries[2]['type']]
]

# Write to row 32 (after Viking Link)
print("\nWriting to Google Sheets row 32...")
ws.update(values=data, range_name='D32:K36')

print(f"\n✅ Done! View: {sh.url}")
