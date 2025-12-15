#!/usr/bin/env python3
"""
Battery BM Revenue Updater v2 - FULL KPI System
Updates battery balancing mechanism revenue with comprehensive KPIs
Targets spreadsheet: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

NEW in v2:
- BOALF integration (acceptance counts, dispatch intensity, granularity)
- BOD integration (stack depth, defensive pricing, spreads)
- Market-wide KPIs (all BMUs total revenue, system direction)
- Time-of-day profiles (3 time bands)
- Stack analysis panel
"""

import sys
import logging
from datetime import datetime, date, time as dt_time
import requests
import gspread
from google.oauth2 import service_account
from collections import defaultdict
import statistics

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'
SA_FILE = 'inner-cinema-credentials.json'

# Battery BMU IDs to track
BATTERIES = [
    {'bmu_id': 'T_LKSDB-1', 'name': 'Lakeside', 'capacity_mw': 50},
    {'bmu_id': 'E_CONTB-1', 'name': 'Tesla Hornsea', 'capacity_mw': 100}, 
    {'bmu_id': 'T_WHLWB-1', 'name': 'Whitelee', 'capacity_mw': 50}
]

# Elexon BMRS API endpoints
BOAV_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all"
EBOCF_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all"
BOALF_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptance/all"
BOD_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer/all"

# Time bands for time-of-day analysis
TIME_BANDS = {
    'night': (0, 6),      # SP 1-12
    'day': (6, 18),       # SP 13-36
    'evening': (18, 24)   # SP 37-48
}

logging.basicConfig(level=logging.INFO, format='%(message)s')

def fetch_boalf_data(target_date, bmu_id):
    """
    Fetch BOALF acceptance-level data for timing and count metrics
    Returns: acceptance count, acceptance times, dispatch pattern
    """
    try:
        url = f"{BOALF_API}/{target_date}"
        params = {'bmUnit': bmu_id}
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code != 200:
            return {'count': 0, 'times': [], 'sp_counts': [0] * 48}
        
        data = resp.json().get('data', [])
        
        acceptance_times = []
        sp_counts = [0] * 48
        
        for item in data:
            # Extract acceptance timing
            time_from = item.get('timeFrom', '')
            if time_from:
                acceptance_times.append(time_from)
            
            # Count by settlement period
            sp = item.get('settlementPeriod', 0)
            if 1 <= sp <= 48:
                sp_counts[sp-1] += 1
        
        return {
            'count': len(data),
            'times': acceptance_times,
            'sp_counts': sp_counts
        }
    except Exception as e:
        logging.warning(f"    BOALF fetch error: {e}")
        return {'count': 0, 'times': [], 'sp_counts': [0] * 48}

def fetch_bod_data(target_date, bmu_id, sp):
    """
    Fetch BOD stack data for pricing and availability metrics
    Returns: pairs, defensive count, spreads, MW available
    """
    try:
        url = f"{BOD_API}/{target_date}/{sp}"
        params = {'bmUnit': bmu_id}
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code != 200:
            return {'pairs': 0, 'defensive': 0, 'spreads': [], 'offer_mw': 0, 'bid_mw': 0}
        
        data = resp.json().get('data', [])
        
        pairs = len(data)
        defensive = 0
        spreads = []
        offer_mw = 0
        bid_mw = 0
        
        for item in data:
            bid_price = float(item.get('bidPrice', 0))
            offer_price = float(item.get('offerPrice', 0))
            level_from = float(item.get('levelFrom', 0))
            level_to = float(item.get('levelTo', 0))
            
            # Check for defensive pricing (extreme prices)
            if abs(bid_price) >= 9999 or abs(offer_price) >= 9999:
                defensive += 1
            else:
                # Only calculate spread for non-defensive pairs
                if offer_price > 0 and bid_price < 0:  # Valid pair
                    spreads.append(offer_price - abs(bid_price))
            
            # Calculate MW available (offer direction = positive, bid = negative)
            mw_band = abs(level_to - level_from)
            if offer_price > 0:
                offer_mw += mw_band
            if bid_price < 0:
                bid_mw += mw_band
        
        median_spread = statistics.median(spreads) if spreads else 0
        
        return {
            'pairs': pairs,
            'defensive': defensive,
            'median_spread': median_spread,
            'offer_mw': offer_mw,
            'bid_mw': bid_mw
        }
    except Exception as e:
        logging.debug(f"    BOD fetch error SP{sp}: {e}")
        return {'pairs': 0, 'defensive': 0, 'median_spread': 0, 'offer_mw': 0, 'bid_mw': 0}

def fetch_battery_revenue(target_date):
    """Fetch comprehensive battery BM revenue with all KPIs"""
    
    logging.info(f"📊 Fetching battery revenue for {target_date}...")
    
    battery_data = []
    
    # Initialize sparkline arrays (48 periods each)
    sp_total_revenue = [0] * 48
    sp_net_mwh = [0] * 48
    sp_total_volume = [0] * 48
    sp_bmu_revenue = {bmu['bmu_id']: [0] * 48 for bmu in BATTERIES}
    
    # Stack analysis arrays
    sp_stack_depth = [0] * 48
    sp_defensive_count = [0] * 48
    sp_total_pairs = [0] * 48
    sp_spreads = [[] for _ in range(48)]
    sp_offer_mw = [0] * 48
    sp_bid_mw = [0] * 48
    
    for battery in BATTERIES:
        bmu_id = battery['bmu_id']
        name = battery['name']
        
        logging.info(f"  Processing {name} ({bmu_id})...")
        
        # Fetch BOALF data (acceptance-level)
        boalf_data = fetch_boalf_data(target_date, bmu_id)
        acceptance_count = boalf_data['count']
        
        # Aggregate across all 48 settlement periods
        total_offer_cash = 0
        total_bid_cash = 0
        total_offer_vol = 0
        total_bid_vol = 0
        active_sps = 0
        
        # Time-of-day tracking
        time_band_revenue = {'night': 0, 'day': 0, 'evening': 0}
        time_band_volume = {'night': 0, 'day': 0, 'evening': 0}
        
        for sp in range(1, 49):  # 48 settlement periods
            sp_offer_cash = 0
            sp_bid_cash = 0
            sp_offer_vol = 0
            sp_bid_vol = 0
            
            # Determine time band
            hour = (sp - 1) // 2  # Convert SP to hour (0-23)
            band = None
            for band_name, (start_hour, end_hour) in TIME_BANDS.items():
                if start_hour <= hour < end_hour:
                    band = band_name
                    break
            
            try:
                # Get offer acceptances (discharge)
                offer_vol_url = f"{BOAV_API}/offer/{target_date}/{sp}?bmUnit={bmu_id}"
                offer_cash_url = f"{EBOCF_API}/offer/{target_date}/{sp}?bmUnit={bmu_id}"
                
                # Get bid acceptances (charge)
                bid_vol_url = f"{BOAV_API}/bid/{target_date}/{sp}?bmUnit={bmu_id}"
                bid_cash_url = f"{EBOCF_API}/bid/{target_date}/{sp}?bmUnit={bmu_id}"
                
                # Fetch volumes
                offer_vol_resp = requests.get(offer_vol_url, timeout=5)
                bid_vol_resp = requests.get(bid_vol_url, timeout=5)
                offer_cash_resp = requests.get(offer_cash_url, timeout=5)
                bid_cash_resp = requests.get(bid_cash_url, timeout=5)
                
                # Sum offer volumes/cashflows
                if offer_vol_resp.status_code == 200:
                    offer_vol_data = offer_vol_resp.json().get('data', [])
                    for item in offer_vol_data:
                        vol = abs(float(item.get('totalVolumeAccepted', 0)))
                        total_offer_vol += vol
                        sp_offer_vol += vol
                
                if offer_cash_resp.status_code == 200:
                    offer_cash_data = offer_cash_resp.json().get('data', [])
                    for item in offer_cash_data:
                        cash_value = abs(float(item.get('totalCashflow', 0)))
                        total_offer_cash += cash_value
                        sp_offer_cash += cash_value
                
                # Sum bid volumes/cashflows
                if bid_vol_resp.status_code == 200:
                    bid_vol_data = bid_vol_resp.json().get('data', [])
                    for item in bid_vol_data:
                        vol = abs(float(item.get('totalVolumeAccepted', 0)))
                        total_bid_vol += vol
                        sp_bid_vol += vol
                
                if bid_cash_resp.status_code == 200:
                    bid_cash_data = bid_cash_resp.json().get('data', [])
                    for item in bid_cash_data:
                        cash_value = abs(float(item.get('totalCashflow', 0)))
                        total_bid_cash += cash_value
                        sp_bid_cash += cash_value
                
                # Calculate SP-level metrics
                sp_net_revenue = sp_offer_cash - sp_bid_cash
                sp_net_vol = sp_offer_vol - sp_bid_vol
                
                # Update sparkline arrays
                sp_total_revenue[sp-1] += sp_net_revenue
                sp_net_mwh[sp-1] += sp_net_vol
                sp_total_volume[sp-1] += (sp_offer_vol + sp_bid_vol)
                sp_bmu_revenue[bmu_id][sp-1] = sp_net_revenue
                
                # Time-of-day tracking
                if band:
                    time_band_revenue[band] += sp_net_revenue
                    time_band_volume[band] += (sp_offer_vol + sp_bid_vol)
                
                # Track if this SP had activity
                if sp_offer_cash > 0 or sp_bid_cash > 0:
                    active_sps += 1
                
                # Fetch BOD stack data for this SP (sampled - every 4th SP to reduce API load)
                if sp % 4 == 1:  # Sample SPs 1, 5, 9, 13... (12 samples)
                    bod_data = fetch_bod_data(target_date, bmu_id, sp)
                    sp_stack_depth[sp-1] = bod_data['pairs']
                    sp_defensive_count[sp-1] = bod_data['defensive']
                    sp_total_pairs[sp-1] = bod_data['pairs']
                    if bod_data['median_spread'] > 0:
                        sp_spreads[sp-1].append(bod_data['median_spread'])
                    sp_offer_mw[sp-1] += bod_data['offer_mw']
                    sp_bid_mw[sp-1] += bod_data['bid_mw']
                    
            except Exception as e:
                logging.debug(f"    SP{sp}: {e}")
        
        # Calculate metrics
        net_revenue = total_offer_cash - total_bid_cash
        total_volume = total_offer_vol + total_bid_vol
        avg_price = (net_revenue / total_volume) if total_volume > 0 else 0
        granularity = (total_volume / acceptance_count) if acceptance_count > 0 else 0
        
        # Determine activity type
        if total_offer_cash > total_bid_cash:
            activity_type = 'Discharge'
        elif total_bid_cash > total_offer_cash:
            activity_type = 'Charge'
        else:
            activity_type = 'Idle'
        
        # Calculate time-of-day percentages
        total_time_revenue = sum(time_band_revenue.values())
        time_pct = {}
        if total_time_revenue > 0:
            for band in ['night', 'day', 'evening']:
                time_pct[band] = (time_band_revenue[band] / total_time_revenue) * 100
        else:
            time_pct = {'night': 0, 'day': 0, 'evening': 0}
        
        battery_data.append({
            'bmu_id': bmu_id,
            'name': name,
            'revenue': net_revenue,
            'volume_mwh': total_volume,
            'avg_price': avg_price,
            'type': activity_type,
            'active_sps': active_sps,
            'acceptance_count': acceptance_count,
            'granularity': granularity,
            'time_pct': time_pct
        })
        
        logging.info(f"    ✅ {name}: £{net_revenue:,.0f} | {total_volume:.1f} MWh | {acceptance_count} accepts | {activity_type}")
    
    # Calculate derived sparkline arrays
    sp_ewap = []
    sp_top_bmu = []
    sp_defensive_share = []
    sp_median_spread = []
    
    for sp_idx in range(48):
        # EWAP
        ewap = sp_total_revenue[sp_idx] / sp_total_volume[sp_idx] if sp_total_volume[sp_idx] > 0 else 0
        sp_ewap.append(ewap)
        
        # Top BMU
        max_revenue = max([sp_bmu_revenue[bmu['bmu_id']][sp_idx] for bmu in BATTERIES])
        sp_top_bmu.append(max_revenue)
        
        # Defensive share
        if sp_total_pairs[sp_idx] > 0:
            def_share = (sp_defensive_count[sp_idx] / sp_total_pairs[sp_idx]) * 100
        else:
            def_share = 0
        sp_defensive_share.append(def_share)
        
        # Median spread
        median_spread = statistics.median(sp_spreads[sp_idx]) if sp_spreads[sp_idx] else 0
        sp_median_spread.append(median_spread)
    
    # Calculate market-wide dispatch intensity (acceptances per hour)
    total_acceptances = sum([b['acceptance_count'] for b in battery_data])
    # Assume we're looking at completed SPs - calculate hours elapsed
    current_sp = max([b['active_sps'] for b in battery_data])
    hours_elapsed = current_sp / 2 if current_sp > 0 else 1
    dispatch_intensity = total_acceptances / hours_elapsed if hours_elapsed > 0 else 0
    
    # Package sparkline data
    sparkline_data = {
        'total_revenue': sp_total_revenue,
        'net_mwh': sp_net_mwh,
        'ewap': sp_ewap,
        'top_bmu': sp_top_bmu,
        'stack_depth': sp_stack_depth,
        'defensive_share': sp_defensive_share,
        'median_spread': sp_median_spread,
        'offer_mw': sp_offer_mw,
        'bid_mw': sp_bid_mw
    }
    
    market_kpis = {
        'dispatch_intensity': dispatch_intensity,
        'total_acceptances': total_acceptances
    }
    
    return battery_data, sparkline_data, market_kpis

def update_sheet(battery_data, sparkline_data, market_kpis, target_date):
    """Update Google Sheets with comprehensive battery revenue data"""
    
    logging.info(f"📝 Updating Google Sheets...")
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(SA_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SHEET_NAME)
    data_hidden = sh.worksheet('Data_Hidden')
    
    # Calculate totals
    total_revenue = sum([b['revenue'] for b in battery_data])
    total_discharge = sum([b['revenue'] for b in battery_data if b['type'] == 'Discharge'])
    total_charge = sum([-b['revenue'] for b in battery_data if b['type'] == 'Charge'])
    max_active_sps = max([b['active_sps'] for b in battery_data]) if battery_data else 0
    
    # Prepare battery table data (extended columns K-U)
    battery_rows = []
    for b in battery_data:
        share = (b['revenue'] / total_revenue * 100) if total_revenue != 0 else 0
        
        # Status emoji
        if share > 50:
            status = f"🔥 {share:.0f}%"
        elif share > 10:
            status = f"✅ {share:.0f}%"
        else:
            status = f"⚪ {share:.0f}%"
        
        row = [
            b['bmu_id'],                           # K: BMU ID
            b['name'],                             # L: Name
            f"£{b['revenue']:,.0f}",              # M: Net Revenue
            f"{b['volume_mwh']:.1f}",             # N: Volume MWh
            f"£{b['avg_price']:.2f}",             # O: £/MWh
            b['type'],                             # P: Type
            f"{b['active_sps']}/48",              # Q: Active SPs
            status,                                # R: Status
            b['acceptance_count'],                 # S: Acceptance Count (NEW)
            f"{b['granularity']:.2f}",            # T: MWh/Accept (NEW)
            f"{market_kpis['dispatch_intensity']:.1f}/hr"  # U: Dispatch Intensity (NEW)
        ]
        battery_rows.append(row)
    
    # Prepare all battery section updates (batch them)
    header_text = f"🔋 BATTERY BM REVENUE - {target_date} (48 SPs) | 📊 Dispatch: {market_kpis['dispatch_intensity']:.1f}/hr"
    discharge_pct = (total_discharge / (total_discharge + total_charge) * 100) if (total_discharge + total_charge) > 0 else 0
    charge_pct = 100 - discharge_pct
    summary = f"Total: £{total_revenue:,.0f} | Discharge: £{total_discharge:,.0f} ({discharge_pct:.0f}%) | Charge: -£{total_charge:,.0f} ({charge_pct:.0f}%) | SPs: {max_active_sps}/48 | Accepts: {market_kpis['total_acceptances']}"
    headers = [['BMU ID', 'Name', 'Net £', 'Vol MWh', '£/MWh', 'Type', 'SPs', 'Status', 'Accepts', 'MWh/Accept', 'Intensity']]
    
    # Single batch update for battery section
    ws.batch_update([
        {'range': 'K24', 'values': [[header_text]]},
        {'range': 'K25', 'values': [[summary]]},
        {'range': 'K26:U26', 'values': headers},
        {'range': 'K27:U29', 'values': battery_rows}
    ])
    
    # Write sparkline data to Data_Hidden (rows 21-29)
    logging.info("📊 Writing sparkline data to Data_Hidden...")
    
    sparkline_updates = [
        {'range': 'A21:AV21', 'values': [[round(v, 2) for v in sparkline_data['total_revenue']]]},
        {'range': 'A22:AV22', 'values': [[round(v, 2) for v in sparkline_data['net_mwh']]]},
        {'range': 'A23:AV23', 'values': [[round(v, 2) for v in sparkline_data['ewap']]]},
        {'range': 'A24:AV24', 'values': [[round(v, 2) for v in sparkline_data['top_bmu']]]},
        {'range': 'A25:AV25', 'values': [[round(v, 0) for v in sparkline_data['stack_depth']]]},
        {'range': 'A26:AV26', 'values': [[round(v, 1) for v in sparkline_data['defensive_share']]]},
        {'range': 'A27:AV27', 'values': [[round(v, 2) for v in sparkline_data['median_spread']]]},
        {'range': 'A28:AV28', 'values': [[round(v, 0) for v in sparkline_data['offer_mw']]]},
        {'range': 'A29:AV29', 'values': [[round(v, 0) for v in sparkline_data['bid_mw']]]}
    ]
    
    data_hidden.batch_update(sparkline_updates)
    logging.info("✅ Written 9 sparkline arrays to Data_Hidden rows 21-29")
    
    # Add battery revenue sparklines (S30-T34) - batch labels and formulas separately
    sparkline_labels_batch = [
        {'range': 'S30', 'values': [['📊 BM Revenue Trends (by Settlement Period)']]},
        {'range': 'S31', 'values': [['Total £:']]},
        {'range': 'S32', 'values': [['Net MWh:']]},
        {'range': 'S33', 'values': [['EWAP £/MWh:']]},
        {'range': 'S34', 'values': [['Top BMU £:']]}
    ]
    ws.batch_update(sparkline_labels_batch)
    
    # Formulas must be written individually with USER_ENTERED
    sparkline_formulas = [
        ('T31', '=SPARKLINE(Data_Hidden!A21:AV21, {"charttype","line";"color1","#f39c12";"linewidth",2})'),
        ('T32', '=SPARKLINE(Data_Hidden!A22:AV22, {"charttype","column";"color1","#3498db"})'),
        ('T33', '=SPARKLINE(Data_Hidden!A23:AV23, {"charttype","line";"color1","#2ecc71";"linewidth",2})'),
        ('T34', '=SPARKLINE(Data_Hidden!A24:AV24, {"charttype","line";"color1","#e74c3c";"linewidth",2})')
    ]
    
    for cell, formula in sparkline_formulas:
        ws.update(values=[[formula]], range_name=cell, value_input_option='USER_ENTERED')
    
    logging.info("✅ Added 4 battery revenue sparklines at S30-T34")
    
    # Add time-of-day profiles (S35-S38) - single batch
    avg_night = sum([b['time_pct']['night'] for b in battery_data]) / len(battery_data)
    avg_day = sum([b['time_pct']['day'] for b in battery_data]) / len(battery_data)
    avg_evening = sum([b['time_pct']['evening'] for b in battery_data]) / len(battery_data)
    
    time_band_batch = [
        {'range': 'S35', 'values': [['🕐 Revenue by Time Band']]},
        {'range': 'S36', 'values': [[f'Night (00-06): {avg_night:.1f}%']]},
        {'range': 'S37', 'values': [[f'Day (06-18): {avg_day:.1f}%']]},
        {'range': 'S38', 'values': [[f'Evening (18-24): {avg_evening:.1f}%']]}
    ]
    ws.batch_update(time_band_batch)
    
    logging.info("✅ Added time-of-day profiles at S35-S38")
    
    # Add stack analysis panel (V30-X35) - single batch for labels
    avg_stack_depth = statistics.mean([v for v in sparkline_data['stack_depth'] if v > 0]) if any(sparkline_data['stack_depth']) else 0
    avg_defensive = statistics.mean([v for v in sparkline_data['defensive_share'] if v > 0]) if any(sparkline_data['defensive_share']) else 0
    avg_offer_mw = statistics.mean([v for v in sparkline_data['offer_mw'] if v > 0]) if any(sparkline_data['offer_mw']) else 0
    avg_bid_mw = statistics.mean([v for v in sparkline_data['bid_mw'] if v > 0]) if any(sparkline_data['bid_mw']) else 0
    avg_spread = statistics.mean([v for v in sparkline_data['median_spread'] if v > 0]) if any(sparkline_data['median_spread']) else 0
    
    stack_labels_batch = [
        {'range': 'V30', 'values': [['📚 BM STACK ANALYSIS']]},
        {'range': 'V31:X31', 'values': [[f'Stack Depth (pairs)', '', f'{avg_stack_depth:.0f} avg']]},
        {'range': 'V32:X32', 'values': [[f'Defensive Share (%)', '', f'{avg_defensive:.1f}% avg']]},
        {'range': 'V33:X33', 'values': [[f'Offer MW Available', '', f'{avg_offer_mw:.0f} MW avg']]},
        {'range': 'V34:X34', 'values': [[f'Bid MW Available', '', f'{avg_bid_mw:.0f} MW avg']]},
        {'range': 'V35:X35', 'values': [[f'Median Spread (£/MWh)', '', f'£{avg_spread:.2f} avg']]}
    ]
    ws.batch_update(stack_labels_batch)
    
    # Add stack sparklines (W31-W35) - formulas individually
    stack_sparkline_formulas = [
        ('W31', '=SPARKLINE(Data_Hidden!A25:AV25, {"charttype","column";"color1","#3498db"})'),
        ('W32', '=SPARKLINE(Data_Hidden!A26:AV26, {"charttype","line";"color1","#e74c3c";"linewidth",2})'),
        ('W33', '=SPARKLINE(Data_Hidden!A28:AV28, {"charttype","column";"color1","#2ecc71"})'),
        ('W34', '=SPARKLINE(Data_Hidden!A29:AV29, {"charttype","column";"color1","#f39c12"})'),
        ('W35', '=SPARKLINE(Data_Hidden!A27:AV27, {"charttype","line";"color1","#9b59b6";"linewidth",2})')
    ]
    
    for cell, formula in stack_sparkline_formulas:
        ws.update(values=[[formula]], range_name=cell, value_input_option='USER_ENTERED')
    
    logging.info("✅ Added stack analysis panel at V30-X35 (5 sparklines)")
    
    total_revenue_display = f"£{total_revenue:,.0f}"
    logging.info(f"✅ Updated 3 batteries at K24:U29")
    logging.info(f"   Total Revenue: {total_revenue_display}")
    logging.info(f"   View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

def main():
    print("=" * 80)
    print(f"🔋 BATTERY BM REVENUE UPDATE v2 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Get target date from args or use today
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = date.today().strftime('%Y-%m-%d')
    
    try:
        battery_data, sparkline_data, market_kpis = fetch_battery_revenue(target_date)
        update_sheet(battery_data, sparkline_data, market_kpis, target_date)
        
        print("=" * 80)
        print("✅ BATTERY REVENUE UPDATE COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
