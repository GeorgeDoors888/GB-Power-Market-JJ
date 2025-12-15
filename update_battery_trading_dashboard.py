#!/usr/bin/env python3
"""
Battery Trading Dashboard Updater
Updates Google Sheets with battery BM revenue data from BOAV + EBOCF endpoints

Date: December 12, 2025
Author: GB Power Market JJ

CRITICAL: Uses config.py for spreadsheet ID (single source of truth)
"""

import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEETS_CONFIG, validate_spreadsheet_connection
import requests
from datetime import datetime, timedelta
import time
import sys

# Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
WORKSHEET_NAME = 'Live Dashboard v2'
INSERT_ROW = 32  # Battery section starts at row 32 (after Viking Link at row 30)

# Battery units to track
BATTERIES = [
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

def get_battery_revenue_data(date_str, batteries):
    """
    Query BOAV + EBOCF endpoints for battery revenue data
    
    Args:
        date_str: Date in YYYY-MM-DD format
        batteries: List of (bmu_id, name) tuples
    
    Returns:
        Tuple: (battery_data list, metrics dict with totals)
    """
    battery_data = []
    total_bid_revenue = 0  # Charging (battery pays grid)
    total_offer_revenue = 0  # Discharging (grid pays battery)
    active_periods = set()  # Track which SPs had activity
    
    for bmu_id, name in batteries:
        bmu_bid_rev = 0
        bmu_offer_rev = 0
        total_volume = 0
        revenue_by_sp = [0] * 48  # Initialize all 48 settlement periods
        
        print(f"  Querying {name} ({bmu_id})...", end='', flush=True)
        
        for sp in range(1, 49):
            sp_revenue = 0
            try:
                # Query BID cashflows (CHARGING - battery pays grid)
                url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/bid/{date_str}/{sp}?bmUnit={bmu_id}"
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    data_json = r.json()
                    if 'data' in data_json and len(data_json['data']) > 0:
                        cf = data_json['data'][0].get('bidOfferPairCashflows', {})
                        # Sum all pair cashflows (exclude totalCashflow key)
                        for key, val in cf.items():
                            if val is not None and key != 'totalCashflow' and val != 0:
                                sp_revenue += abs(val)
                                bmu_bid_rev += abs(val)
                                active_periods.add(sp)
                
                # Query OFFER cashflows (DISCHARGING - grid pays battery)
                url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/offer/{date_str}/{sp}?bmUnit={bmu_id}"
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    data_json = r.json()
                    if 'data' in data_json and len(data_json['data']) > 0:
                        cf = data_json['data'][0].get('bidOfferPairCashflows', {})
                        for key, val in cf.items():
                            if val is not None and key != 'totalCashflow' and val != 0:
                                sp_revenue += abs(val)
                                bmu_offer_rev += abs(val)
                                active_periods.add(sp)
                
                # Query BID volumes
                url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/bid/{date_str}/{sp}?bmUnit={bmu_id}"
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    data_json = r.json()
                    if 'data' in data_json and len(data_json['data']) > 0:
                        pv = data_json['data'][0].get('pairVolumes', {})
                        for key, val in pv.items():
                            if val is not None and key != 'totalVolume':
                                total_volume += abs(val)
                
                # Query OFFER volumes
                url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/offer/{date_str}/{sp}?bmUnit={bmu_id}"
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    data_json = r.json()
                    if 'data' in data_json and len(data_json['data']) > 0:
                        pv = data_json['data'][0].get('pairVolumes', {})
                        for key, val in pv.items():
                            if val is not None and key != 'totalVolume':
                                total_volume += abs(val)
                
                revenue_by_sp[sp-1] = sp_revenue
                time.sleep(0.05)  # Rate limiting
                
            except Exception as e:
                continue
        
        # Calculate metrics
        total_revenue = bmu_bid_rev + bmu_offer_rev
        total_bid_revenue += bmu_bid_rev
        total_offer_revenue += bmu_offer_rev
        
        avg_price = (total_revenue / total_volume) if total_volume > 0 else 0
        status = '✅ Active' if total_revenue > 100 else '⚪ Low'
        
        # Determine primary revenue type
        revenue_type = "Discharge" if bmu_offer_rev > bmu_bid_rev else "Charge"
        
        # Create sparkline formula for Google Sheets
        sparkline_data = ','.join([str(round(x, 2)) for x in revenue_by_sp])
        sparkline = f'=SPARKLINE({{{sparkline_data}}}, {{"charttype","line"; "linewidth",2; "color","#4285F4"}})'
        
        battery_data.append({
            'bmu_id': bmu_id,
            'name': name,
            'revenue': total_revenue,
            'bid_rev': bmu_bid_rev,
            'offer_rev': bmu_offer_rev,
            'volume': total_volume,
            'avg_price': avg_price,
            'revenue_type': revenue_type,
            'sparkline': sparkline,
            'status': status
        })
        
        print(f" £{total_revenue:,.2f} ({revenue_type}: Offer £{bmu_offer_rev:,.0f} - Bid £{bmu_bid_rev:,.0f})")
    
    metrics = {
        'total_bid': total_bid_revenue,
        'total_offer': total_offer_revenue,
        'active_sp_count': len(active_periods)
    }
    
    return battery_data, metrics


def update_google_sheets(battery_data, metrics, date_str):
    """
    Update Google Sheets with battery trading data
    
    Args:
        battery_data: List of battery data dictionaries
        metrics: Dict with total_bid, total_offer, active_sp_count
        date_str: Date string for header
    """
    # Authenticate
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    
    # Get spreadsheet and validate
    sheet_id = GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_ID']
    sh = validate_spreadsheet_connection(gc, sheet_id)
    ws = sh.worksheet(WORKSHEET_NAME)
    
    print(f"\n✅ Connected to: {sh.title}")
    print(f"   Worksheet: {WORKSHEET_NAME}")
    
    # Calculate totals
    total_revenue = sum(b['revenue'] for b in battery_data)
    total_volume = sum(b['volume'] for b in battery_data)
    total_avg = (total_revenue / total_volume) if total_volume > 0 else 0
    active_count = sum(1 for b in battery_data if b['revenue'] > 100)
    
    total_bid = metrics['total_bid']
    total_offer = metrics['total_offer']
    active_sp = metrics['active_sp_count']
    
    # Update header with enhanced metrics
    header_text = f'🔋 BATTERY BM REVENUE — {date_str} | {active_sp}/48 Active SPs | Discharge: £{total_offer:,.0f} | Charge: £{total_bid:,.0f}'
    ws.update(
        values=[[header_text, '', '', '', '', '', '', '']],
        range_name=f'A{INSERT_ROW}:H{INSERT_ROW}'
    )
    
    # Update column headers with Type column
    ws.update(
        values=[['BMU ID', 'Name', 'Total (£)', 'Volume (MWh)', 'Avg £/MWh', 'Type', 'Trend', 'Status']],
        range_name=f'A{INSERT_ROW+1}:H{INSERT_ROW+1}'
    )
    
    # Update battery rows (only top 3 for display)
    top_batteries = sorted(battery_data, key=lambda x: x['revenue'], reverse=True)[:3]
    for i, b in enumerate(top_batteries, start=INSERT_ROW+2):
        ws.update(
            values=[[b['bmu_id'], b['name'], f"£{b['revenue']:,.2f}", f"{b['volume']:.2f}", 
                    f"£{b['avg_price']:.2f}", b['revenue_type'], '', b['status']]],
            range_name=f'A{i}:H{i}'
        )
        ws.update(values=[[b['sparkline']]], range_name=f'G{i}', raw=False)
    
    # Update total row with net revenue
    net_revenue = total_offer - total_bid
    total_type = f"Net: £{net_revenue:+,.0f}"
    ws.update(
        values=[['TOTAL (BMU)', '', f"£{total_revenue:,.2f}", f"{total_volume:.2f}", 
                f"£{total_avg:.2f}", total_type, '', f"📊 {active_count} Active"]],
        range_name=f'A{INSERT_ROW+5}:H{INSERT_ROW+5}'
    )
    
    # Add VTP note
    vtp_note = "⚠️ VTP aggregated revenue data not available via BMRS API (proprietary settlement)"
    ws.update(values=[[vtp_note, '', '', '', '', '', '', '']], range_name=f'A{INSERT_ROW+6}:H{INSERT_ROW+6}')
    ws.format(f'A{INSERT_ROW+6}:H{INSERT_ROW+6}', {
        'textFormat': {'italic': True, 'fontSize': 9},
    # Get battery data
    print("Collecting battery revenue data from BOAV + EBOCF endpoints...")
    battery_data, metrics = get_battery_revenue_data(date, BATTERIES)
    
    # Update Google Sheets
    print("\nUpdating Google Sheets dashboard...")
    update_google_sheets(battery_data, metrics, date).2f}")
    print(f"     Net Revenue: £{net_revenue:+,.2f}")
    print(f"   Total Volume: {total_volume:.2f} MWh")
    print(f"   Active SPs: {active_sp}/{48} ({active_sp*100/48:.0f}%)")
    print(f"   Active Batteries: {active_count}")


def main():
    """Main execution"""
    # Use yesterday's date (settlement data has 1-2 day lag)
    date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    
    if len(sys.argv) > 1:
        date = sys.argv[1]  # Allow manual date override
    
    print(f"{'='*80}")
    print(f"Battery Trading Dashboard Updater")
    print(f"Date: {date}")
    print(f"{'='*80}\n")
    
    # Get battery data
    print("Collecting battery revenue data from BOAV + EBOCF endpoints...")
    battery_data = get_battery_revenue_data(date, BATTERIES)
    
    # Update Google Sheets
    print("\nUpdating Google Sheets dashboard...")
    update_google_sheets(battery_data, date)
    
    print(f"\n{'='*80}")
    print("✅ Update complete!")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
