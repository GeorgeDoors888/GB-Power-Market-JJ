#!/usr/bin/env python3
"""
Market-Wide BM Revenue Analyzer
Discovers ALL active BM units dynamically and analyzes their balancing mechanism revenue.

Data Sources:
- Elexon BMRS API: BOAV (acceptance volumes), EBOCF (cashflows)
- BigQuery: DISBSAD (system actions/costs/constraints)
- Optional: BOD (bid-offer stack analysis)

Author: George Major
Last Updated: December 14, 2025
"""

import sys
import requests
from datetime import datetime, date, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import gspread
from collections import defaultdict

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
WORKSHEET_NAME = 'BM Revenue Analysis'  # New sheet for market-wide view
CREDENTIALS_FILE = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
PROJECT_ID = "inner-cinema-476211-u9"

# Elexon API endpoints
BOAV_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all"
EBOCF_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all"
BOD_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer/all"

def discover_active_bmus(date_str, sample_period=24):
    """
    Discover all BMUs with balancing acceptances by querying Elexon API without bmUnit filter.
    Sample a few settlement periods to find active units (avoid 48 * 2 * 2 = 192 API calls just for discovery).
    
    Returns: set of BMU IDs
    """
    print(f"\n🔍 Discovering active BMUs from Elexon API (sampling SP {sample_period})...")
    
    active_bmus = set()
    
    for direction in ['offer', 'bid']:
        url = f"{BOAV_API}/{direction}/{date_str}/{sample_period}"
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data:
                for item in data['data']:
                    bmu_id = item.get('bmUnit')
                    volume = abs(float(item.get('totalVolumeAccepted', 0)))
                    
                    if bmu_id and volume > 0.1:  # Filter tiny volumes
                        active_bmus.add(bmu_id)
        
        except Exception as e:
            print(f"⚠️  Discovery error for {direction}: {e}")
    
    print(f"✅ Discovered {len(active_bmus)} active BMUs")
    return active_bmus

def fetch_bmu_settlement_data(date_str, bmu_id):
    """
    Fetch full settlement day data for a single BMU across all 48 SPs.
    Returns aggregated revenue, volumes, and activity metrics.
    """
    total_offer_vol = 0
    total_bid_vol = 0
    total_offer_cash = 0
    total_bid_cash = 0
    active_sps = 0
    
    sp_revenues = []  # For settlement period analysis
    
    for sp in range(1, 49):
        # Fetch volumes
        offer_vol_url = f"{BOAV_API}/offer/{date_str}/{sp}?bmUnit={bmu_id}"
        bid_vol_url = f"{BOAV_API}/bid/{date_str}/{sp}?bmUnit={bmu_id}"
        
        # Fetch cashflows
        offer_cash_url = f"{EBOCF_API}/offer/{date_str}/{sp}?bmUnit={bmu_id}"
        bid_cash_url = f"{EBOCF_API}/bid/{date_str}/{sp}?bmUnit={bmu_id}"
        
        sp_offer_vol = 0
        sp_bid_vol = 0
        sp_offer_cash = 0
        sp_bid_cash = 0
        
        try:
            # Offer volumes
            r = requests.get(offer_vol_url, timeout=5)
            if r.status_code == 200:
                for item in r.json().get('data', []):
                    sp_offer_vol += abs(float(item.get('totalVolumeAccepted', 0)))
            
            # Bid volumes
            r = requests.get(bid_vol_url, timeout=5)
            if r.status_code == 200:
                for item in r.json().get('data', []):
                    sp_bid_vol += abs(float(item.get('totalVolumeAccepted', 0)))
            
            # Offer cashflows
            r = requests.get(offer_cash_url, timeout=5)
            if r.status_code == 200:
                for item in r.json().get('data', []):
                    sp_offer_cash += abs(float(item.get('totalCashflow', 0)))
            
            # Bid cashflows
            r = requests.get(bid_cash_url, timeout=5)
            if r.status_code == 200:
                for item in r.json().get('data', []):
                    sp_bid_cash += abs(float(item.get('totalCashflow', 0)))
            
            total_offer_vol += sp_offer_vol
            total_bid_vol += sp_bid_vol
            total_offer_cash += sp_offer_cash
            total_bid_cash += sp_bid_cash
            
            if sp_offer_vol > 0 or sp_bid_vol > 0:
                active_sps += 1
            
            sp_net_revenue = sp_offer_cash - sp_bid_cash
            sp_revenues.append(sp_net_revenue)
        
        except Exception as e:
            print(f"⚠️  Error fetching {bmu_id} SP{sp}: {e}")
            sp_revenues.append(0)
    
    net_revenue = total_offer_cash - total_bid_cash
    total_volume = total_offer_vol + total_bid_vol
    avg_price = net_revenue / total_volume if total_volume > 0 else 0
    
    # VWAP calculations (Volume-Weighted Average Price)
    vwap_offer = abs(total_offer_cash) / abs(total_offer_vol) if total_offer_vol != 0 else 0
    vwap_bid = abs(total_bid_cash) / abs(total_bid_vol) if total_bid_vol != 0 else 0
    vwap_net = abs(net_revenue) / abs(total_volume) if total_volume != 0 else 0
    
    # Offer/Bid Ratio
    offer_bid_ratio = abs(total_offer_cash) / abs(total_bid_cash) if total_bid_cash != 0 else 0
    
    # Determine activity type
    if total_offer_cash > total_bid_cash * 1.5:
        activity = 'Offer'
    elif total_bid_cash > total_offer_cash * 1.5:
        activity = 'Bid'
    else:
        activity = 'Mixed'
    
    return {
        'bmu_id': bmu_id,
        'net_revenue': net_revenue,
        'offer_revenue': total_offer_cash,
        'bid_revenue': total_bid_cash,
        'offer_volume': total_offer_vol,
        'bid_volume': total_bid_vol,
        'total_volume': total_volume,
        'avg_price': avg_price,
        'vwap_offer': vwap_offer,
        'vwap_bid': vwap_bid,
        'vwap_net': vwap_net,
        'offer_bid_ratio': offer_bid_ratio,
        'activity': activity,
        'active_sps': active_sps,
        'sp_revenues': sp_revenues
    }

def fetch_bmu_metadata(bmu_ids):
    """
    Fetch BMU metadata (technology, capacity, fuel type) from BigQuery.
    Returns dict mapping bmUnit -> metadata.
    """
    if not bmu_ids:
        return {}
    
    bmu_list_str = "', '".join(bmu_ids)
    
    query = f"""
    SELECT 
        nationalGridBmUnit,
        technology,
        registeredCapacity,
        fuelType
    FROM `{PROJECT_ID}.uk_energy_prod.bmu_metadata`
    WHERE nationalGridBmUnit IN ('{bmu_list_str}')
    """
    
    try:
        results = bigquery_client.query(query).result()
        
        metadata = {}
        for row in results:
            metadata[row.nationalGridBmUnit] = {
                'technology': row.technology or 'Unknown',
                'capacity_mw': row.registeredCapacity or 0,
                'fuel_type': row.fuelType or 'Unknown'
            }
        
        print(f"✅ Fetched metadata for {len(metadata)} BMUs")
        return metadata
        
    except Exception as e:
        print(f"⚠️  Metadata query error: {e}")
        return {}

def fetch_disbsad_data(date_str, bmu_ids):
    """
    Fetch DISBSAD (system actions/costs/constraints) data from BigQuery for all BMUs.
    Returns dict: {bmu_id: {'cost': X, 'volume': Y, 'actions': N, 'constraints': [...]}}
    """
    print(f"\n📊 Fetching DISBSAD data from BigQuery...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    bmu_list_str = "', '".join(bmu_ids)
    
    query = f"""
    SELECT 
        assetId,
        SUM(ABS(cost)) as total_cost,
        SUM(ABS(volume)) as total_volume,
        COUNT(*) as action_count,
        ARRAY_AGG(STRUCT(settlementPeriod, cost, volume, service) ORDER BY settlementPeriod) as actions
    FROM `{PROJECT_ID}.uk_energy_prod.bmrs_disbsad`
    WHERE DATE(settlementDate) = '{date_str}'
      AND assetId IN ('{bmu_list_str}')
    GROUP BY assetId
    """
    
    disbsad_data = {}
    
    try:
        results = client.query(query).result()
        
        for row in results:
            disbsad_data[row.assetId] = {
                'cost': row.total_cost or 0,
                'volume': row.total_volume or 0,
                'actions': row.action_count or 0,
                'details': [
                    {
                        'sp': a.settlementPeriod,
                        'cost': a.cost,
                        'volume': a.volume,
                        'service': a.service
                    } for a in (row.actions or [])
                ]
            }
        
        print(f"✅ Found DISBSAD data for {len(disbsad_data)} BMUs")
    
    except Exception as e:
        print(f"⚠️  DISBSAD query error: {e}")
    
    return disbsad_data

def analyze_market(date_str, max_units=100):
    """
    Main market analysis: discover BMUs, fetch settlement data, analyze.
    """
    print(f"\n{'='*80}")
    print(f"🔋 MARKET-WIDE BM REVENUE ANALYSIS - {date_str}")
    print(f"{'='*80}")
    
    # Step 1: Discover active BMUs
    active_bmus = discover_active_bmus(date_str)
    
    if not active_bmus:
        print("❌ No active BMUs found")
        return []
    
    # Limit to top N for performance (can remove for full market)
    bmu_list = sorted(list(active_bmus))[:max_units]
    print(f"\n📈 Analyzing {len(bmu_list)} BMUs (limited to {max_units} for performance)")
    
    # Step 2: Fetch settlement data for each BMU
    print(f"\n⏳ Fetching settlement data (this will take a few minutes)...")
    
    bmu_results = []
    
    for i, bmu_id in enumerate(bmu_list, 1):
        print(f"  [{i}/{len(bmu_list)}] {bmu_id}...", end=' ')
        
        try:
            data = fetch_bmu_settlement_data(date_str, bmu_id)
            
            if data['total_volume'] > 0.1:  # Filter out zero-volume units
                bmu_results.append(data)
                print(f"£{data['net_revenue']:,.0f} | {data['total_volume']:.1f} MWh | {data['activity']}")
            else:
                print("(no volume)")
        
        except Exception as e:
            print(f"ERROR: {e}")
    
    # Step 3: Fetch DISBSAD data
    if bmu_results:
        bmu_ids_with_data = [b['bmu_id'] for b in bmu_results]
        disbsad_data = fetch_disbsad_data(date_str, bmu_ids_with_data)
        
        # Merge DISBSAD into results
        for bmu in bmu_results:
            if bmu['bmu_id'] in disbsad_data:
                bmu['disbsad'] = disbsad_data[bmu['bmu_id']]
            else:
                bmu['disbsad'] = {'cost': 0, 'volume': 0, 'actions': 0, 'details': []}
        
        # Step 4: Fetch BMU metadata (technology, capacity)
        print(f"\n⏳ Fetching BMU metadata...")
        metadata = fetch_bmu_metadata(bmu_ids_with_data)
        
        # Calculate market totals for share percentages
        total_market_revenue = sum(abs(b['net_revenue']) for b in bmu_results)
        total_market_disbsad = sum(b['disbsad']['cost'] for b in bmu_results)
        
        # Merge metadata and calculate additional KPIs
        for bmu in bmu_results:
            # Add metadata
            if bmu['bmu_id'] in metadata:
                bmu['metadata'] = metadata[bmu['bmu_id']]
            else:
                bmu['metadata'] = {'technology': 'Unknown', 'capacity_mw': 0, 'fuel_type': 'Unknown'}
            
            # Calculate £/MW-day (revenue normalized by capacity)
            if bmu['metadata']['capacity_mw'] > 0:
                bmu['revenue_per_mw_day'] = bmu['net_revenue'] / bmu['metadata']['capacity_mw']
            else:
                bmu['revenue_per_mw_day'] = 0
            
            # Calculate market share percentages
            bmu['market_share_pct'] = (abs(bmu['net_revenue']) / total_market_revenue * 100) if total_market_revenue > 0 else 0
            bmu['constraint_share_pct'] = (bmu['disbsad']['cost'] / total_market_disbsad * 100) if total_market_disbsad > 0 else 0
    
    # Sort by revenue
    bmu_results.sort(key=lambda x: abs(x['net_revenue']), reverse=True)
    
    return bmu_results

def update_sheet(bmu_results, date_str):
    """
    Write market-wide analysis to Google Sheets.
    Creates comprehensive view with revenue, volumes, DISBSAD actions, and SP-level detail.
    """
    print(f"\n📝 Updating Google Sheets...")
    
    # Authenticate
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    
    gc = gspread.authorize(creds)
    
    # Try to get existing sheet, create if doesn't exist
    try:
        ss = gc.open_by_key(SPREADSHEET_ID)
        try:
            ws = ss.worksheet(WORKSHEET_NAME)
            ws.clear()  # Clear existing data
        except gspread.WorksheetNotFound:
            ws = ss.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=30)
    except Exception as e:
        print(f"❌ Error accessing spreadsheet: {e}")
        return
    
    # Prepare data
    headers = [
        ['MARKET-WIDE BM REVENUE ANALYSIS (ENHANCED)'],
        [f'Date: {date_str}', '', '', '', '', '', f'Total BMUs: {len(bmu_results)}'],
        [],
        ['BMU ID', 'Technology', 'Fuel Type', 'Net Revenue £', 'Offer £', 'Bid £',
         'Offer MWh', 'Bid MWh', 'Total MWh', 'VWAP £/MWh', 'Offer/Bid Ratio',
         'Activity', 'Active SPs', 'Capacity MW', '£/MW-day', 'Market Share %',
         'DISBSAD Cost £', 'DISBSAD Actions', 'Constraint Share %', 'Combined Revenue £']
    ]
    
    data_rows = []
    
    total_net_revenue = 0
    total_volume = 0
    total_disbsad_cost = 0
    
    for bmu in bmu_results:
        combined_revenue = bmu['net_revenue'] + bmu['disbsad']['cost']
        total_net_revenue += bmu['net_revenue']
        total_volume += bmu['total_volume']
        total_disbsad_cost += bmu['disbsad']['cost']
        
        data_rows.append([
            bmu['bmu_id'],
            bmu['metadata']['technology'],
            bmu['metadata']['fuel_type'],
            f"£{bmu['net_revenue']:,.0f}",
            f"£{bmu['offer_revenue']:,.0f}",
            f"£{bmu['bid_revenue']:,.0f}",
            f"{bmu['offer_volume']:.1f}",
            f"{bmu['bid_volume']:.1f}",
            f"{bmu['total_volume']:.1f}",
            f"£{bmu['vwap_net']:.2f}",
            f"{bmu['offer_bid_ratio']:.2f}",
            bmu['activity'],
            f"{bmu['active_sps']}/48",
            f"{bmu['metadata']['capacity_mw']:.1f}",
            f"£{bmu['revenue_per_mw_day']:.2f}",
            f"{bmu['market_share_pct']:.2f}%",
            f"£{bmu['disbsad']['cost']:,.0f}",
            bmu['disbsad']['actions'],
            f"{bmu['constraint_share_pct']:.2f}%",
            f"£{combined_revenue:,.0f}"
        ])
    
    # Summary row
    summary = [
        'TOTAL',
        '',
        '',
        f"£{total_net_revenue:,.0f}",
        '',
        '',
        '',
        '',
        f"{total_volume:,.1f}",
        '',
        '',
        '',
        '',
        '',
        '',
        '100.00%',
        f"£{total_disbsad_cost:,.0f}",
        '',
        '100.00%',
        f"£{total_net_revenue + total_disbsad_cost:,.0f}"
    ]
    
    # Combine all data
    all_data = headers + data_rows + [[]] + [summary]
    
    # Write to sheet
    ws.update(values=all_data, range_name='A1')
    
    # Format header
    ws.format('A4:T4', {
        'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    ws.format('A4:K4', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'bold': True},
        'horizontalAlignment': 'CENTER'
    })
    
    print(f"✅ Updated {WORKSHEET_NAME} sheet")
    print(f"📊 Total Market Revenue: £{total_net_revenue:,.0f}")
    print(f"⚡ Total Volume: {total_volume:,.1f} MWh")
    print(f"💰 Total DISBSAD Cost: £{total_disbsad_cost:,.0f}")
    print(f"🎯 Combined Revenue: £{total_net_revenue + total_disbsad_cost:,.0f}")
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

def main():
    """Main execution"""
    # Get date from command line or use yesterday
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        yesterday = date.today() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    
    # Optional: limit number of BMUs for testing
    max_units = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    try:
        # Analyze market
        bmu_results = analyze_market(date_str, max_units=max_units)
        
        if not bmu_results:
            print("❌ No BM revenue data found")
            sys.exit(1)
        
        # Update Google Sheets
        update_sheet(bmu_results, date_str)
        
        print(f"\n{'='*80}")
        print("✅ MARKET-WIDE ANALYSIS COMPLETE")
        print(f"{'='*80}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
