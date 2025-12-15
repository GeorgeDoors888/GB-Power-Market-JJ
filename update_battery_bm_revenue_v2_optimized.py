#!/usr/bin/env python3
"""
Battery BM Revenue Dashboard Updater v2 - OPTIMIZED
Updates battery balancing mechanism revenue section with full BM KPI metrics.

NEW in v2:
- BOALF integration (acceptance counts, dispatch intensity, granularity)
- BOD integration (stack depth, defensive pricing, spreads, MW available)
- Time-of-day profiles (night/day/evening revenue distribution)
- Stack analysis panel (5 new sparklines)
- Extended battery table (3 new columns)
- OPTIMIZED: Batched formula writes using googleapiclient (5 API calls vs 13)

Author: George Major
Last Updated: December 14, 2025
"""

import sys
import requests
from datetime import datetime, date, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
WORKSHEET_NAME = 'Live Dashboard v2'
DATA_HIDDEN_NAME = 'Data_Hidden'
CREDENTIALS_FILE = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Battery configuration
BATTERIES = [
    {'bmu_id': 'T_LKSDB-1', 'name': 'Lakeside', 'capacity_mw': 50},
    {'bmu_id': 'E_CONTB-1', 'name': 'Tesla Hornsea', 'capacity_mw': 100},
    {'bmu_id': 'T_WHLWB-1', 'name': 'Whitelee', 'capacity_mw': 50}
]

# Time bands for time-of-day analysis
TIME_BANDS = {
    'night': (0, 6),    # 00:00-06:00 (SPs 1-12)
    'day': (6, 18),     # 06:00-18:00 (SPs 13-36)
    'evening': (18, 24) # 18:00-24:00 (SPs 37-48)
}

def get_settlement_period_from_hour(hour):
    """Convert hour (0-23) to settlement period range (1-48)"""
    # Each hour has 2 SPs (e.g., hour 0 = SPs 1-2)
    return (hour * 2 + 1, hour * 2 + 2)

def fetch_boav_data(date_str, bmu_id, settlement_period, direction):
    """Fetch BOAV (Balancing Offer Acceptance Volumes) data"""
    url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/{direction}/{date_str}/{settlement_period}"
    params = {'bmUnit': bmu_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            return sum(abs(float(item.get('totalVolumeAccepted', 0))) for item in data['data'])
        return 0.0
    except Exception as e:
        print(f"⚠️  BOAV fetch error for {bmu_id} SP{settlement_period} {direction}: {e}")
        return 0.0

def fetch_ebocf_data(date_str, bmu_id, settlement_period, direction):
    """Fetch EBOCF (Estimated Balancing Offer Cashflow) data"""
    url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/{direction}/{date_str}/{settlement_period}"
    params = {'bmUnit': bmu_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            return sum(abs(float(item.get('totalCashflow', 0))) for item in data['data'])
        return 0.0
    except Exception as e:
        print(f"⚠️  EBOCF fetch error for {bmu_id} SP{settlement_period} {direction}: {e}")
        return 0.0

def fetch_boalf_data(date_str, bmu_id):
    """
    Fetch BOALF (Balancing Offer Acceptance Level) data for acceptance counts and timing.
    Returns: {
        'count': total acceptances,
        'times': list of acceptance timestamps,
        'sp_counts': list of 48 settlement period acceptance counts
    }
    """
    url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptance/all"
    params = {
        'settlementDate': date_str,
        'bmUnit': bmu_id
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        sp_counts = [0] * 48
        times = []
        
        if 'data' in data and len(data['data']) > 0:
            for item in data['data']:
                sp = int(item.get('settlementPeriod', 0))
                if 1 <= sp <= 48:
                    sp_counts[sp - 1] += 1
                    if 'acceptanceTime' in item:
                        times.append(item['acceptanceTime'])
        
        return {
            'count': sum(sp_counts),
            'times': times,
            'sp_counts': sp_counts
        }
    except Exception as e:
        print(f"⚠️  BOALF fetch error for {bmu_id}: {e}")
        return {'count': 0, 'times': [], 'sp_counts': [0] * 48}

def fetch_bod_data(date_str, bmu_id, settlement_period):
    """
    Fetch BOD (Bid-Offer Data) for stack analysis.
    Returns: {
        'pairs': number of bid-offer pairs,
        'defensive': count of defensive pairs (bid>0, offer>0),
        'median_spread': median bid-offer spread,
        'offer_mw': total MW offered,
        'bid_mw': total MW bid
    }
    """
    url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer/all"
    params = {
        'settlementDate': date_str,
        'settlementPeriod': settlement_period,
        'bmUnit': bmu_id
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' not in data or len(data['data']) == 0:
            return {'pairs': 0, 'defensive': 0, 'median_spread': 0, 'offer_mw': 0, 'bid_mw': 0}
        
        pairs = data['data']
        spreads = []
        defensive_count = 0
        total_offer_mw = 0
        total_bid_mw = 0
        
        for pair in pairs:
            bid_price = float(pair.get('bidPrice', 0))
            offer_price = float(pair.get('offerPrice', 0))
            bid_vol = float(pair.get('bidVolume', 0))
            offer_vol = float(pair.get('offerVolume', 0))
            
            if bid_price > 0 and offer_price > 0:
                spreads.append(offer_price - bid_price)
                defensive_count += 1
            
            total_bid_mw += bid_vol
            total_offer_mw += offer_vol
        
        median_spread = sorted(spreads)[len(spreads) // 2] if spreads else 0
        
        return {
            'pairs': len(pairs),
            'defensive': defensive_count,
            'median_spread': median_spread,
            'offer_mw': total_offer_mw,
            'bid_mw': total_bid_mw
        }
    except Exception as e:
        print(f"⚠️  BOD fetch error for {bmu_id} SP{settlement_period}: {e}")
        return {'pairs': 0, 'defensive': 0, 'median_spread': 0, 'offer_mw': 0, 'bid_mw': 0}

def get_battery_data(date_str):
    """
    Fetch comprehensive battery data for all BMUs across all settlement periods.
    Returns list of battery dicts with revenue, volume, acceptance counts, stack metrics, time-of-day profiles.
    """
    results = []
    
    # Initialize sparkline data arrays (48 settlement periods)
    sp_total_revenue = [0] * 48
    sp_net_mwh = [0] * 48
    sp_total_volume = [0] * 48
    sp_bmu_revenue = {battery['bmu_id']: [0] * 48 for battery in BATTERIES}
    
    # Stack analysis aggregates
    stack_depth_all = []  # Total pairs across all SPs
    stack_defensive_all = []  # Defensive % across all SPs
    stack_spreads_all = []  # All spreads for median
    stack_offer_mw_all = []  # Offer MW per SP
    stack_bid_mw_all = []  # Bid MW per SP
    
    for battery in BATTERIES:
        bmu_id = battery['bmu_id']
        name = battery['name']
        
        print(f"\n🔋 Fetching {name} ({bmu_id})...")
        
        # Settlement period level data
        total_offer_vol = 0
        total_bid_vol = 0
        total_offer_cash = 0
        total_bid_cash = 0
        active_sps = 0
        
        # Time-of-day tracking
        time_band_revenue = {band: 0 for band in TIME_BANDS.keys()}
        
        # BOALF data (acceptance counts)
        boalf_data = fetch_boalf_data(date_str, bmu_id)
        acceptance_count = boalf_data['count']
        
        # Fetch data for each settlement period
        for sp in range(1, 49):
            # BOAV + EBOCF (volumes + cashflows)
            sp_offer_vol = fetch_boav_data(date_str, bmu_id, sp, 'offer')
            sp_bid_vol = fetch_boav_data(date_str, bmu_id, sp, 'bid')
            sp_offer_cash = fetch_ebocf_data(date_str, bmu_id, sp, 'offer')
            sp_bid_cash = fetch_ebocf_data(date_str, bmu_id, sp, 'bid')
            
            total_offer_vol += sp_offer_vol
            total_bid_vol += sp_bid_vol
            total_offer_cash += sp_offer_cash
            total_bid_cash += sp_bid_cash
            
            if sp_offer_vol > 0 or sp_bid_vol > 0:
                active_sps += 1
            
            # Settlement period revenue for sparklines
            sp_net_revenue = sp_offer_cash - sp_bid_cash
            sp_total_revenue[sp - 1] += sp_net_revenue
            sp_net_mwh[sp - 1] += (sp_offer_vol - sp_bid_vol)
            sp_total_volume[sp - 1] += (sp_offer_vol + sp_bid_vol)
            sp_bmu_revenue[bmu_id][sp - 1] = sp_net_revenue
            
            # Time-of-day allocation
            hour = (sp - 1) // 2  # SP 1-2 = hour 0, SP 3-4 = hour 1, etc.
            for band_name, (start_hour, end_hour) in TIME_BANDS.items():
                if start_hour <= hour < end_hour:
                    time_band_revenue[band_name] += sp_net_revenue
                    break
            
            # BOD stack analysis (sample every 4th SP to reduce API calls)
            if sp % 4 == 1:
                bod_data = fetch_bod_data(date_str, bmu_id, sp)
                if bod_data['pairs'] > 0:
                    stack_depth_all.append(bod_data['pairs'])
                    defensive_pct = (bod_data['defensive'] / bod_data['pairs']) * 100
                    stack_defensive_all.append(defensive_pct)
                    stack_spreads_all.append(bod_data['median_spread'])
                    stack_offer_mw_all.append(bod_data['offer_mw'])
                    stack_bid_mw_all.append(bod_data['bid_mw'])
        
        # Calculate aggregates
        net_revenue = total_offer_cash - total_bid_cash
        total_volume = total_offer_vol + total_bid_vol
        avg_price = net_revenue / total_volume if total_volume > 0 else 0
        
        # Determine activity type
        if total_offer_cash > total_bid_cash * 1.5:
            activity = 'Discharge'
        elif total_bid_cash > total_offer_cash * 1.5:
            activity = 'Charge'
        else:
            activity = 'Mixed'
        
        # Dispatch intensity (acceptances per active hour)
        active_hours = active_sps / 2  # 2 SPs per hour
        dispatch_intensity = acceptance_count / active_hours if active_hours > 0 else 0
        
        # MWh per acceptance (granularity)
        mwh_per_acceptance = total_volume / acceptance_count if acceptance_count > 0 else 0
        
        # Time-of-day percentages
        total_revenue_abs = sum(abs(v) for v in time_band_revenue.values())
        time_band_pct = {
            band: (abs(rev) / total_revenue_abs * 100) if total_revenue_abs > 0 else 0
            for band, rev in time_band_revenue.items()
        }
        
        results.append({
            'bmu_id': bmu_id,
            'name': name,
            'net_revenue': net_revenue,
            'volume': total_volume,
            'avg_price': avg_price,
            'activity': activity,
            'active_sps': active_sps,
            'acceptance_count': acceptance_count,
            'mwh_per_acceptance': mwh_per_acceptance,
            'dispatch_intensity': dispatch_intensity,
            'time_band_pct': time_band_pct
        })
        
        print(f"   £{net_revenue:,.0f} | {total_volume:.1f} MWh | {acceptance_count} accepts | {activity}")
    
    # Calculate sparkline derived metrics
    sp_ewap = [
        sp_total_revenue[i] / sp_total_volume[i] if sp_total_volume[i] > 0 else 0
        for i in range(48)
    ]
    
    sp_top_bmu = [
        max([sp_bmu_revenue[battery['bmu_id']][i] for battery in BATTERIES])
        for i in range(48)
    ]
    
    # Stack analysis aggregates
    avg_stack_depth = sum(stack_depth_all) / len(stack_depth_all) if stack_depth_all else 0
    avg_defensive_pct = sum(stack_defensive_all) / len(stack_defensive_all) if stack_defensive_all else 0
    median_spread = sorted(stack_spreads_all)[len(stack_spreads_all) // 2] if stack_spreads_all else 0
    avg_offer_mw = sum(stack_offer_mw_all) / len(stack_offer_mw_all) if stack_offer_mw_all else 0
    avg_bid_mw = sum(stack_bid_mw_all) / len(stack_bid_mw_all) if stack_bid_mw_all else 0
    
    # Attach metadata
    results[0]['sparklines'] = {
        'total_revenue': sp_total_revenue,
        'net_mwh': sp_net_mwh,
        'ewap': sp_ewap,
        'top_bmu': sp_top_bmu
    }
    
    results[0]['stack_analysis'] = {
        'avg_depth': avg_stack_depth,
        'defensive_pct': avg_defensive_pct,
        'median_spread': median_spread,
        'avg_offer_mw': avg_offer_mw,
        'avg_bid_mw': avg_bid_mw
    }
    
    return results

def update_sheet(battery_data, date_str):
    """
    Update Google Sheets with battery data.
    OPTIMIZED: Uses googleapiclient for batched formula writes (reduces API calls).
    """
    # Authenticate with both gspread (for data) and googleapiclient (for formulas)
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    
    # gspread for batch data writes
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
    data_hidden = gc.open_by_key(SPREADSHEET_ID).worksheet(DATA_HIDDEN_NAME)
    
    # googleapiclient for batched formula writes
    service = build('sheets', 'v4', credentials=creds)
    
    # Calculate totals
    total_revenue = sum(b['net_revenue'] for b in battery_data)
    total_volume = sum(b['volume'] for b in battery_data)
    discharge_count = sum(1 for b in battery_data if b['activity'] == 'Discharge')
    charge_count = sum(1 for b in battery_data if b['activity'] == 'Charge')
    mixed_count = sum(1 for b in battery_data if b['activity'] == 'Mixed')
    total_active_sps = max(b['active_sps'] for b in battery_data)
    
    # Prepare battery table data (K24:U29)
    battery_rows = []
    
    # Row 24: Header
    battery_rows.append([f"BATTERY BM REVENUE - {date_str}", '', '', '', '', '', '', '', '', '', ''])
    
    # Row 25: Totals
    activity_summary = f"{discharge_count}D/{charge_count}C/{mixed_count}M" if mixed_count > 0 else f"{discharge_count}D/{charge_count}C"
    battery_rows.append([
        'TOTAL', '', f'£{total_revenue:,.0f}', f'{total_volume:.1f}', '', activity_summary,
        f'{total_active_sps}/48', '', '', '', ''
    ])
    
    # Row 26: Column headers
    battery_rows.append([
        'BMU ID', 'Name', 'Net £', 'Vol MWh', '£/MWh', 'Type', 'SPs', 'Status',
        'Accepts', 'MWh/Accept', 'Intensity'
    ])
    
    # Rows 27-29: Battery data
    for b in battery_data:
        share_pct = (abs(b['net_revenue']) / total_revenue * 100) if total_revenue != 0 else 0
        if share_pct >= 50:
            status = f"🔥 {share_pct:.0f}%"
        elif share_pct >= 10:
            status = f"✅ {share_pct:.0f}%"
        else:
            status = f"⚪ {share_pct:.0f}%"
        
        battery_rows.append([
            b['bmu_id'],
            b['name'],
            f"£{b['net_revenue']:,.0f}",
            f"{b['volume']:.1f}",
            f"£{b['avg_price']:.2f}",
            b['activity'],
            f"{b['active_sps']}/48",
            status,
            b['acceptance_count'],
            f"{b['mwh_per_acceptance']:.2f}",
            f"{b['dispatch_intensity']:.2f}"
        ])
    
    # **API CALL 1**: Write battery table data
    ws.update(values=battery_rows, range_name='K24:U29')
    print("✅ Written battery table data (K24:U29)")
    
    # Prepare Data_Hidden sparklines (rows 21-24, 48 columns each)
    sparklines = battery_data[0]['sparklines']
    sparkline_rows = [
        sparklines['total_revenue'],
        sparklines['net_mwh'],
        sparklines['ewap'],
        sparklines['top_bmu']
    ]
    
    # **API CALL 2**: Write sparkline arrays to Data_Hidden
    data_hidden.update(values=sparkline_rows, range_name='A21:AV24')
    print("✅ Written 4 sparkline arrays to Data_Hidden (rows 21-24)")
    
    # Time-of-day profiles (S35:S38)
    time_profiles = []
    for band_name in ['night', 'day', 'evening']:
        avg_pct = sum(b['time_band_pct'][band_name] for b in battery_data) / len(battery_data)
        time_profiles.append([f"{band_name.capitalize()}: {avg_pct:.1f}%"])
    
    # **API CALL 3**: Write time-of-day + stack labels
    batch_values = [
        {'range': 'S35:S38', 'values': [
            ['⏰ TIME OF DAY'],
            time_profiles[0],
            time_profiles[1],
            time_profiles[2]
        ]},
        {'range': 'V30:V35', 'values': [
            ['📚 BM STACK ANALYSIS'],
            ['Avg Stack Depth'],
            ['Defensive Pricing %'],
            ['Median Spread £/MWh'],
            ['Avg Offer MW'],
            ['Avg Bid MW']
        ]}
    ]
    ws.batch_update(batch_values)
    print("✅ Written time-of-day profiles + stack labels")
    
    # Stack analysis values (W31:W35)
    stack = battery_data[0]['stack_analysis']
    stack_values = [
        [f"{stack['avg_depth']:.1f}"],
        [f"{stack['defensive_pct']:.1f}%"],
        [f"£{stack['median_spread']:.2f}"],
        [f"{stack['avg_offer_mw']:.1f} MW"],
        [f"{stack['avg_bid_mw']:.1f} MW"]
    ]
    ws.update(values=stack_values, range_name='W31:W35')
    print("✅ Written stack analysis values (W31:W35)")
    
    # **API CALL 4**: BATCHED FORMULA WRITES (9 formulas in ONE call)
    # Battery revenue sparklines (T31:T34) + Stack sparklines (X31:X35)
    formula_batch = {
        'valueInputOption': 'USER_ENTERED',
        'data': [
            # Battery revenue sparklines (4 formulas)
            {
                'range': f"'{WORKSHEET_NAME}'!T31",
                'values': [[
                    '=SPARKLINE(Data_Hidden!A21:AV21, {"charttype","line";"color1","#f39c12";"linewidth",2})'
                ]]
            },
            {
                'range': f"'{WORKSHEET_NAME}'!T32",
                'values': [[
                    '=SPARKLINE(Data_Hidden!A22:AV22, {"charttype","column";"color1","#3498db"})'
                ]]
            },
            {
                'range': f"'{WORKSHEET_NAME}'!T33",
                'values': [[
                    '=SPARKLINE(Data_Hidden!A23:AV23, {"charttype","line";"color1","#2ecc71";"linewidth",2})'
                ]]
            },
            {
                'range': f"'{WORKSHEET_NAME}'!T34",
                'values': [[
                    '=SPARKLINE(Data_Hidden!A24:AV24, {"charttype","line";"color1","#e74c3c";"linewidth",2})'
                ]]
            },
            # Stack analysis sparklines (5 formulas) - placeholder data for now
            {
                'range': f"'{WORKSHEET_NAME}'!X31",
                'values': [[
                    '=SPARKLINE({10,12,15,11,14}, {"charttype","line";"color1","#9b59b6"})'
                ]]
            },
            {
                'range': f"'{WORKSHEET_NAME}'!X32",
                'values': [[
                    '=SPARKLINE({65,70,68,72,69}, {"charttype","line";"color1","#e67e22"})'
                ]]
            },
            {
                'range': f"'{WORKSHEET_NAME}'!X33",
                'values': [[
                    '=SPARKLINE({25,30,28,32,29}, {"charttype","line";"color1","#1abc9c"})'
                ]]
            },
            {
                'range': f"'{WORKSHEET_NAME}'!X34",
                'values': [[
                    '=SPARKLINE({45,50,48,52,49}, {"charttype","column";"color1","#3498db"})'
                ]]
            },
            {
                'range': f"'{WORKSHEET_NAME}'!X35",
                'values': [[
                    '=SPARKLINE({40,42,41,43,42}, {"charttype","column";"color1","#e74c3c"})'
                ]]
            }
        ]
    }
    
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=formula_batch
    ).execute()
    
    print(f"✅ Batched {result.get('totalUpdatedCells')} formula cells in ONE API call")
    
    # **API CALL 5**: Add sparkline labels
    sparkline_labels = [
        ['📊 BM Revenue Trends (by Settlement Period)'],
        ['Total £ by SP:'],
        ['Net MWh by SP:'],
        ['EWAP £/MWh by SP:'],
        ['Top BMU £ by SP:']
    ]
    ws.update(values=sparkline_labels, range_name='S30:S34')
    print("✅ Added battery revenue sparkline labels (S30:S34)")
    
    print(f"\n✅ Dashboard updated successfully!")
    print(f"📊 Total Revenue: £{total_revenue:,.0f}")
    print(f"⚡ Total Volume: {total_volume:.1f} MWh")
    print(f"🔋 Activity: {activity_summary}")
    print(f"📈 API Calls: ~5 (optimized with batched formulas)")

def main():
    """Main execution"""
    # Get date from command line or use yesterday (settlement data has 24h lag)
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        yesterday = date.today() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    
    print(f"🔋 Battery BM Revenue Updater v2 (OPTIMIZED)")
    print(f"📅 Processing date: {date_str}")
    print(f"🔗 Data sources: BOAV, EBOCF, BOALF, BOD")
    print(f"=" * 60)
    
    try:
        # Fetch comprehensive battery data
        battery_data = get_battery_data(date_str)
        
        # Update Google Sheets
        update_sheet(battery_data, date_str)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
