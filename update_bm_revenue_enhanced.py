#!/usr/bin/env python3
"""
Enhanced BM Revenue Analyzer with DISBSAD Constraints
Comprehensive KPI calculations including technology classification, constraint share, and benchmarking.

New Features:
- Technology classification (BESS, Wind, Gas, etc.)
- Constraint Share (% of total DISBSAD cost)
- £/MW-day (revenue normalized by capacity)
- Offer/Bid Ratio
- VWAP (Volume-Weighted Average Price)
- Market share percentages

Author: George Major
Date: December 14, 2025
"""

import sys
import requests
from datetime import datetime, date, timedelta
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
WORKSHEET_NAME = 'BM Revenue Analysis'
CREDENTIALS_FILE = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
PROJECT_ID = "inner-cinema-476211-u9"

# Elexon API endpoints
BOAV_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all"
EBOCF_API = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all"

def get_bm_revenue_with_enhanced_kpis(target_date):
    """
    Fetch comprehensive BM revenue data with DISBSAD constraints and enhanced KPIs.
    Uses BigQuery for efficient data aggregation.
    """
    date_str = target_date.strftime('%Y-%m-%d')
    
    print("=" * 80)
    print(f"🔋 ENHANCED BM REVENUE ANALYSIS - {date_str}")
    print("=" * 80)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Comprehensive query with all KPIs
    query = f"""
    WITH bm_acceptances AS (
      -- BM acceptances from BOALF (acceptance-level data)
      -- Contains both cashflow and volume information
      SELECT 
        bmUnit,
        SUM(CASE WHEN levelFrom LIKE '%OFFER%' THEN acceptedOfferVolume ELSE 0 END) as offer_mwh,
        SUM(CASE WHEN levelFrom LIKE '%BID%' THEN acceptedBidVolume ELSE 0 END) as bid_mwh,
        SUM(CASE WHEN levelFrom LIKE '%OFFER%' THEN cashflow ELSE 0 END) as offer_revenue,
        SUM(CASE WHEN levelFrom LIKE '%BID%' THEN cashflow ELSE 0 END) as bid_revenue,
        COUNT(DISTINCT settlementPeriod) as active_sps
      FROM `{PROJECT_ID}.uk_energy_prod.bmrs_boalf`
      WHERE DATE(settlementDate) = '{date_str}'
        AND (acceptedOfferVolume != 0 OR acceptedBidVolume != 0)
      GROUP BY bmUnit
    ),
    disbsad_costs AS (
      -- DISBSAD constraint costs
      SELECT 
        assetId as bmUnit,
        SUM(ABS(cost)) as disbsad_cost,
        SUM(ABS(volume)) as disbsad_volume,
        COUNT(*) as disbsad_actions
      FROM `{PROJECT_ID}.uk_energy_prod.bmrs_disbsad`
      WHERE DATE(settlementDate) = '{date_str}'
        AND assetId IS NOT NULL
      GROUP BY assetId
    ),
    market_totals AS (
      -- Market-wide totals for share calculations
      SELECT 
        SUM(ABS(cost)) as total_market_disbsad
      FROM `{PROJECT_ID}.uk_energy_prod.bmrs_disbsad`
      WHERE DATE(settlementDate) = '{date_str}'
    ),
    bmu_metadata AS (
      -- Technology classification and capacity
      SELECT 
        nationalGridBmUnit as bmUnit,
        technology,
        registeredCapacity,
        fuelType
      FROM `{PROJECT_ID}.uk_energy_prod.bmu_metadata`
    )
    SELECT 
      a.bmUnit,
      
      -- Revenue KPIs
      COALESCE(a.offer_revenue, 0) + COALESCE(a.bid_revenue, 0) as net_revenue,
      COALESCE(a.offer_revenue, 0) as offer_revenue,
      COALESCE(a.bid_revenue, 0) as bid_revenue,
      
      -- Volume KPIs
      COALESCE(a.offer_mwh, 0) as offer_mwh,
      COALESCE(a.bid_mwh, 0) as bid_mwh,
      COALESCE(a.offer_mwh, 0) + COALESCE(a.bid_mwh, 0) as total_mwh,
      
      -- Price KPIs (VWAP = Volume-Weighted Average Price)
      SAFE_DIVIDE(COALESCE(a.offer_revenue, 0), COALESCE(a.offer_mwh, 0)) as vwap_offer,
      SAFE_DIVIDE(COALESCE(a.bid_revenue, 0), COALESCE(a.bid_mwh, 0)) as vwap_bid,
      SAFE_DIVIDE(
        COALESCE(a.offer_revenue, 0) + COALESCE(a.bid_revenue, 0), 
        COALESCE(a.offer_mwh, 0) + COALESCE(a.bid_mwh, 0)
      ) as vwap_net,
      
      -- Activity KPIs
      COALESCE(a.active_sps, 0) as active_sps,
      
      -- Financial Ratios
      SAFE_DIVIDE(ABS(COALESCE(a.offer_revenue, 0)), ABS(COALESCE(a.bid_revenue, 0))) as offer_bid_ratio,
      
      -- Constraint KPIs (DISBSAD)
      COALESCE(d.disbsad_cost, 0) as disbsad_cost,
      COALESCE(d.disbsad_actions, 0) as disbsad_actions,
      COALESCE(d.disbsad_volume, 0) as disbsad_volume,
      SAFE_DIVIDE(COALESCE(d.disbsad_cost, 0), m.total_market_disbsad) * 100 as constraint_share_pct,
      
      -- Combined Revenue (BM + DISBSAD)
      COALESCE(a.offer_revenue, 0) + COALESCE(a.bid_revenue, 0) + COALESCE(d.disbsad_cost, 0) as combined_revenue,
      
      -- Technology & Capacity
      COALESCE(bmu.technology, 'Unknown') as technology,
      COALESCE(bmu.registeredCapacity, 0) as capacity_mw,
      COALESCE(bmu.fuelType, 'Unknown') as fuel_type,
      
      -- £/MW-day (revenue normalized by capacity)
      SAFE_DIVIDE(
        COALESCE(a.offer_revenue, 0) + COALESCE(a.bid_revenue, 0),
        COALESCE(bmu.registeredCapacity, 0)
      ) as revenue_per_mw_day

    FROM bm_acceptances a
    LEFT JOIN disbsad_costs d ON a.bmUnit = d.bmUnit
    LEFT JOIN bmu_metadata bmu ON a.bmUnit = bmu.bmUnit
    CROSS JOIN market_totals m
    
    WHERE ABS(COALESCE(a.offer_revenue, 0) + COALESCE(a.bid_revenue, 0)) > 1  -- Filter noise
    
    ORDER BY net_revenue DESC
    LIMIT 100
    """
    
    print("\n⏳ Querying BigQuery for comprehensive BM data...")
    results = client.query(query).result()
    
    bmu_data = []
    total_market_revenue = 0
    total_market_disbsad = 0
    
    for row in results:
        bmu_data.append({
            'bmUnit': row.bmUnit,
            'net_revenue': row.net_revenue,
            'offer_revenue': row.offer_revenue,
            'bid_revenue': row.bid_revenue,
            'offer_mwh': row.offer_mwh,
            'bid_mwh': row.bid_mwh,
            'total_mwh': row.total_mwh,
            'vwap_offer': row.vwap_offer or 0,
            'vwap_bid': row.vwap_bid or 0,
            'vwap_net': row.vwap_net or 0,
            'active_sps': row.active_sps,
            'offer_bid_ratio': row.offer_bid_ratio or 0,
            'disbsad_cost': row.disbsad_cost,
            'disbsad_actions': row.disbsad_actions,
            'disbsad_volume': row.disbsad_volume,
            'constraint_share_pct': row.constraint_share_pct or 0,
            'combined_revenue': row.combined_revenue,
            'technology': row.technology,
            'capacity_mw': row.capacity_mw,
            'fuel_type': row.fuel_type,
            'revenue_per_mw_day': row.revenue_per_mw_day or 0
        })
        
        total_market_revenue += row.net_revenue
        total_market_disbsad += row.disbsad_cost
    
    # Calculate market share percentages
    for bmu in bmu_data:
        bmu['market_share_pct'] = (bmu['net_revenue'] / total_market_revenue * 100) if total_market_revenue > 0 else 0
    
    print(f"✅ Retrieved {len(bmu_data)} BMUs")
    print(f"   Total Market Revenue: £{total_market_revenue:,.0f}")
    print(f"   Total DISBSAD Costs: £{total_market_disbsad:,.0f}")
    
    return bmu_data, target_date

def update_google_sheet(bmu_data, analysis_date):
    """
    Update Google Sheets with enhanced BM revenue data including all new KPIs.
    """
    print("\n📊 Updating Google Sheets...")
    
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Get or create worksheet
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except:
        worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=30)
    
    # Clear existing data
    worksheet.clear()
    
    # Header section
    headers = [
        ['MARKET-WIDE BM REVENUE ANALYSIS (ENHANCED)'],
        [f'Date: {analysis_date.strftime("%Y-%m-%d")}', '', '', '', '', '', f'Total BMUs: {len(bmu_data)}'],
        [],
        # Column headers (Row 4)
        [
            'BMU ID', 'Technology', 'Fuel Type',
            'Net Revenue £', 'Offer £', 'Bid £',
            'Offer MWh', 'Bid MWh', 'Total MWh',
            'VWAP £/MWh', 'Offer/Bid Ratio',
            'Active SPs', 'Capacity MW', '£/MW-day',
            'Market Share %',
            'DISBSAD Cost £', 'DISBSAD Actions', 'Constraint Share %',
            'Combined Revenue £'
        ]
    ]
    
    # Data rows
    rows = []
    for bmu in bmu_data:
        activity_str = f"{bmu['active_sps']}/48"
        
        rows.append([
            bmu['bmUnit'],
            bmu['technology'],
            bmu['fuel_type'],
            f"£{bmu['net_revenue']:,.0f}",
            f"£{bmu['offer_revenue']:,.0f}",
            f"£{bmu['bid_revenue']:,.0f}",
            f"{bmu['offer_mwh']:.1f}",
            f"{bmu['bid_mwh']:.1f}",
            f"{bmu['total_mwh']:.1f}",
            f"£{bmu['vwap_net']:.2f}",
            f"{bmu['offer_bid_ratio']:.2f}",
            activity_str,
            f"{bmu['capacity_mw']:.1f}",
            f"£{bmu['revenue_per_mw_day']:.2f}",
            f"{bmu['market_share_pct']:.2f}%",
            f"£{bmu['disbsad_cost']:,.0f}",
            bmu['disbsad_actions'],
            f"{bmu['constraint_share_pct']:.2f}%",
            f"£{bmu['combined_revenue']:,.0f}"
        ])
    
    # Total row
    total_net_revenue = sum(b['net_revenue'] for b in bmu_data)
    total_mwh = sum(b['total_mwh'] for b in bmu_data)
    total_disbsad = sum(b['disbsad_cost'] for b in bmu_data)
    total_combined = sum(b['combined_revenue'] for b in bmu_data)
    
    rows.append([])  # Blank row
    rows.append([
        'TOTAL',
        '',
        '',
        f"£{total_net_revenue:,.0f}",
        '',
        '',
        '',
        '',
        f"{total_mwh:.1f}",
        '',
        '',
        '',
        '',
        '',
        '100.00%',
        f"£{total_disbsad:,.0f}",
        '',
        '100.00%',
        f"£{total_combined:,.0f}"
    ])
    
    # Write all data
    all_data = headers + rows
    worksheet.update('A1', all_data)
    
    # Format header row (row 4)
    worksheet.format('A4:S4', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
        'horizontalAlignment': 'CENTER'
    })
    
    print(f"✅ Updated {WORKSHEET_NAME} with {len(bmu_data)} BMUs")
    print(f"   Sheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

def main():
    """Main execution."""
    
    # Default to yesterday (settlement data lags)
    analysis_date = date.today() - timedelta(days=1)
    
    if len(sys.argv) > 1:
        try:
            analysis_date = datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        except:
            print(f"Invalid date format. Using default: {analysis_date}")
    
    # Fetch enhanced BM revenue data
    bmu_data, analysis_date = get_bm_revenue_with_enhanced_kpis(analysis_date)
    
    if not bmu_data:
        print("❌ No data retrieved - exiting")
        return 1
    
    # Update Google Sheets
    update_google_sheet(bmu_data, analysis_date)
    
    print("\n" + "=" * 80)
    print("✅ ENHANCED BM REVENUE ANALYSIS COMPLETE")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
