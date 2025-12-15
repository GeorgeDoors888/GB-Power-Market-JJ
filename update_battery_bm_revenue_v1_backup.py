#!/usr/bin/env python3
"""
Battery BM Revenue Updater - Live Dashboard v2
Updates battery balancing mechanism revenue in real-time
Targets spreadsheet: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
Placement: Row 32 (between Interconnectors and Wind Chart)
"""

import sys
import logging
from datetime import datetime, date
import requests
import gspread
from google.oauth2 import service_account

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'
SA_FILE = 'inner-cinema-credentials.json'
BATTERY_ROW_START = 24  # Start row for battery section (between ICs and Wind section)
BATTERY_COL_START = 'K'  # Column K (columns K-R are empty in rows 24-29)

# Battery BMU IDs to track
BATTERIES = [
    {'bmu_id': 'T_LKSDB-1', 'name': 'Lakeside', 'capacity_mw': 50},
    {'bmu_id': 'E_CONTB-1', 'name': 'Tesla Hornsea', 'capacity_mw': 100}, 
    {'bmu_id': 'T_WHLWB-1', 'name': 'Whitelee', 'capacity_mw': 50}
]

# Elexon BMRS API endpoints
BOAV_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all"
EBOCF_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all"

logging.basicConfig(level=logging.INFO, format='%(message)s')

def fetch_battery_revenue(target_date):
    """Fetch battery BM revenue for today (all 48 settlement periods)"""
    
    logging.info(f"📊 Fetching battery revenue for {target_date}...")
    
    battery_data = []
    
    # Initialize sparkline arrays (48 periods each)
    sp_total_revenue = [0] * 48  # Total £ by SP
    sp_net_mwh = [0] * 48        # Net MWh by SP
    sp_total_volume = [0] * 48   # Total volume for EWAP calc
    sp_bmu_revenue = {bmu['bmu_id']: [0] * 48 for bmu in BATTERIES}  # Per-BMU revenue by SP
    
    for battery in BATTERIES:
        bmu_id = battery['bmu_id']
        name = battery['name']
        
        logging.info(f"  Processing {name} ({bmu_id})...")
        
        # Aggregate across all 48 settlement periods
        total_offer_cash = 0
        total_bid_cash = 0
        total_offer_vol = 0
        total_bid_vol = 0
        active_sps = 0
        
        for sp in range(1, 49):  # 48 settlement periods
            sp_offer_cash = 0
            sp_bid_cash = 0
            sp_offer_vol = 0
            sp_bid_vol = 0
            
            try:
                # Get offer acceptances (discharge = battery generating)
                offer_vol_url = f"{BOAV_API}/offer/{target_date}/{sp}?bmUnit={bmu_id}"
                offer_cash_url = f"{EBOCF_API}/offer/{target_date}/{sp}?bmUnit={bmu_id}"
                
                # Get bid acceptances (charge = battery consuming)
                bid_vol_url = f"{BOAV_API}/bid/{target_date}/{sp}?bmUnit={bmu_id}"
                bid_cash_url = f"{EBOCF_API}/bid/{target_date}/{sp}?bmUnit={bmu_id}"
                
                # Fetch volumes
                offer_vol_resp = requests.get(offer_vol_url, timeout=5)
                bid_vol_resp = requests.get(bid_vol_url, timeout=5)
                
                # Fetch cashflows
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
                
                # Calculate SP-level metrics for sparklines
                sp_net_revenue = sp_offer_cash - sp_bid_cash
                sp_net_vol = sp_offer_vol - sp_bid_vol
                
                # Update sparkline arrays (sp index = sp-1)
                sp_total_revenue[sp-1] += sp_net_revenue
                sp_net_mwh[sp-1] += sp_net_vol
                sp_total_volume[sp-1] += (sp_offer_vol + sp_bid_vol)
                sp_bmu_revenue[bmu_id][sp-1] = sp_net_revenue
                
                # Track if this SP had activity
                if sp_offer_cash > 0 or sp_bid_cash > 0:
                    active_sps += 1
                    
            except Exception as e:
                logging.debug(f"    SP{sp}: {e}")
        
        # Calculate net revenue and type
        net_revenue = total_offer_cash - total_bid_cash  # Positive = net earning
        total_volume = total_offer_vol + total_bid_vol
        avg_price = (net_revenue / total_volume) if total_volume > 0 else 0
        
        # Determine primary activity type
        if total_offer_cash > total_bid_cash:
            activity_type = 'Discharge'
        elif total_bid_cash > total_offer_cash:
            activity_type = 'Charge'
        else:
            activity_type = 'Idle'
        
        battery_data.append({
            'bmu_id': bmu_id,
            'name': name,
            'revenue': net_revenue,
            'volume_mwh': total_volume,
            'avg_price': avg_price,
            'type': activity_type,
            'active_sps': active_sps
        })
        
        logging.info(f"    ✅ {name}: £{net_revenue:,.0f} | {total_volume:.1f} MWh | {activity_type}")
    
    # Calculate derived sparkline arrays
    sp_ewap = []  # EWAP £/MWh by SP
    sp_top_bmu = []  # Top BMU revenue by SP
    
    for sp_idx in range(48):
        # EWAP calculation
        if sp_total_volume[sp_idx] > 0:
            ewap = sp_total_revenue[sp_idx] / sp_total_volume[sp_idx]
        else:
            ewap = 0
        sp_ewap.append(ewap)
        
        # Top BMU revenue
        max_revenue = max([sp_bmu_revenue[bmu['bmu_id']][sp_idx] for bmu in BATTERIES])
        sp_top_bmu.append(max_revenue)
    
    # Package sparkline data
    sparkline_data = {
        'total_revenue': sp_total_revenue,
        'net_mwh': sp_net_mwh,
        'ewap': sp_ewap,
        'top_bmu': sp_top_bmu
    }
    
    return battery_data, sparkline_data

def update_sheet(battery_data, sparkline_data, target_date):
    """Update Google Sheets with battery revenue data"""
    
    logging.info(f"📝 Updating Google Sheets...")
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(SA_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SHEET_NAME)
    data_hidden = sh.worksheet('Data_Hidden')  # For sparkline data
    
    # Calculate totals
    total_revenue = sum([b['revenue'] for b in battery_data])
    total_discharge = sum([b['revenue'] for b in battery_data if b['type'] == 'Discharge'])
    total_charge = sum([-b['revenue'] for b in battery_data if b['type'] == 'Charge'])  # Make positive for display
    max_active_sps = max([b['active_sps'] for b in battery_data]) if battery_data else 0
    
    # Build data array (COMPACT: Max 6 rows to fit in 24-29)
    data = [
        # Row 1: Header with date  
        ['🔋 BATTERY BM REVENUE - ' + target_date.strftime('%Y-%m-%d') + ' (48 SPs)', '', '', '', '', '', '', ''],
        
        # Row 2: Totals only (compact)
        [f'Total: £{total_revenue:,.0f} | Discharge: £{total_discharge:,.0f} ({total_discharge/total_revenue*100 if total_revenue else 0:.0f}%) | Charge: -£{total_charge:,.0f} | SPs: {max_active_sps}/48', '', '', '', '', '', '', ''],
        
        # Row 3: Column headers (no blank spacer to save space)
        ['BMU ID', 'Name', 'Net Revenue £', 'Volume MWh', '£/MWh', 'Type', 'Active SPs', 'Status']
    ]
    
    # Add battery rows with % share (ONLY TOP 3 to fit in rows 24-29)
    batteries_sorted = sorted(battery_data, key=lambda x: abs(x['revenue']), reverse=True)[:3]
    for b in batteries_sorted:
        pct_share = (abs(b['revenue']) / total_revenue * 100) if total_revenue else 0
        
        # Status emoji based on share
        if pct_share >= 50:
            status = f'🔥 {pct_share:.0f}% of total'
        elif pct_share >= 10:
            status = f'✅ {pct_share:.0f}% of total'
        else:
            status = f'⚪ {pct_share:.1f}%'
        
        data.append([
            b['bmu_id'],
            b['name'],
            f"£{b['revenue']:,.0f}",
            f"{b['volume_mwh']:.1f}",
            f"£{b['avg_price']:.0f}",
            b['type'],
            f"{b['active_sps']}/48",
            status
        ])
    
    # Write to sheet (Rows 24-29, columns K-R)
    range_name = f'K{BATTERY_ROW_START}:R{BATTERY_ROW_START + len(data) - 1}'
    ws.update(values=data, range_name=range_name)
    
    # Write sparkline data to Data_Hidden rows 21-24
    logging.info(f"📊 Writing sparkline data to Data_Hidden...")
    
    sparkline_rows = [
        [round(v, 2) for v in sparkline_data['total_revenue']],  # Row 21: Total £
        [round(v, 2) for v in sparkline_data['net_mwh']],         # Row 22: Net MWh
        [round(v, 2) for v in sparkline_data['ewap']],            # Row 23: EWAP
        [round(v, 2) for v in sparkline_data['top_bmu']]          # Row 24: Top BMU £
    ]
    
    data_hidden.batch_update([
        {'range': 'A21:AV21', 'values': [sparkline_rows[0]]},
        {'range': 'A22:AV22', 'values': [sparkline_rows[1]]},
        {'range': 'A23:AV23', 'values': [sparkline_rows[2]]},
        {'range': 'A24:AV24', 'values': [sparkline_rows[3]]}
    ])
    
    logging.info(f"✅ Written 4 sparkline arrays to Data_Hidden rows 21-24")
    
    # Add sparkline section header and formulas (rows 30-34, columns S-T)
    # Using columns S-T to avoid conflicts with wind/outages sections
    
    # Add section header
    ws.update(values=[['📊 BM Revenue Trends (by Settlement Period)']], range_name='S30')
    
    # Add sparkline labels
    ws.batch_update([
        {'range': 'S31', 'values': [['Total £:']]},
        {'range': 'S32', 'values': [['Net MWh:']]},
        {'range': 'S33', 'values': [['EWAP £/MWh:']]},
        {'range': 'S34', 'values': [['Top BMU £:']]}
    ])
    
    # Add sparkline formulas (must be done individually with USER_ENTERED)
    sparkline_formulas = [
        ('T31', '=SPARKLINE(Data_Hidden!A21:AV21, {"charttype","line";"color1","#f39c12";"linewidth",2})'),
        ('T32', '=SPARKLINE(Data_Hidden!A22:AV22, {"charttype","column";"color1","#3498db"})'),
        ('T33', '=SPARKLINE(Data_Hidden!A23:AV23, {"charttype","line";"color1","#2ecc71";"linewidth",2})'),
        ('T34', '=SPARKLINE(Data_Hidden!A24:AV24, {"charttype","line";"color1","#e74c3c";"linewidth",2})')
    ]
    
    for cell, formula in sparkline_formulas:
        ws.update(values=[[formula]], range_name=cell, value_input_option='USER_ENTERED')
    
    logging.info(f"✅ Added sparkline section at S30-T34 (4 sparklines)")
    
    logging.info(f"✅ Updated {len(battery_data)} batteries at {range_name}")
    logging.info(f"   Total Revenue: £{total_revenue:,.0f}")
    logging.info(f"   View: {sh.url}")

def main():
    """Main execution"""
    try:
        # Use today's date (or override for testing)
        import sys
        if len(sys.argv) > 1:
            target_date = datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        logging.info("=" * 80)
        logging.info(f"🔋 BATTERY BM REVENUE UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 80)
        
        # Fetch battery revenue
        battery_data, sparkline_data = fetch_battery_revenue(target_date)
        
        if not battery_data:
            logging.warning("⚠️  No battery data retrieved")
            return
        
        # Update sheet
        update_sheet(battery_data, sparkline_data, target_date)
        
        logging.info("=" * 80)
        logging.info("✅ BATTERY REVENUE UPDATE COMPLETE")
        logging.info("=" * 80)
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
