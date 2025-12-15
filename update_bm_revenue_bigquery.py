#!/usr/bin/env python3
"""
BM Revenue Analysis using BigQuery Tables (BOAV + EBOCF)
Much faster than API-based approach - uses pre-ingested settlement data.

New Approach:
- Queries bmrs_boav + bmrs_ebocf from BigQuery (no API calls!)
- Joins with bmu_metadata for technology classification
- Joins with bmrs_disbsad for constraint costs
- Calculates all KPIs in single BigQuery query

Author: George Major  
Date: December 14, 2025
"""

import sys
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

def analyze_bm_revenue(target_date):
    """
    Comprehensive BM revenue analysis using BigQuery tables.
    Single query gets all data - no API calls needed!
    """
    date_str = target_date.strftime('%Y-%m-%d')
    
    print("=" * 80)
    print(f"🔋 BM REVENUE ANALYSIS (BigQuery) - {date_str}")
    print("=" * 80)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Comprehensive query with all KPIs
    query = f"""
    WITH boav_aggregated AS (
      -- Aggregate BOAV volumes by BMU and direction
      SELECT 
        nationalGridBmUnit,
        _direction,
        SUM(totalVolumeAccepted) as total_volume_mwh,
        COUNT(DISTINCT settlementPeriod) as active_sps
      FROM `{PROJECT_ID}.uk_energy_prod.bmrs_boav`
      WHERE DATE(CAST(settlementDate AS STRING)) = '{date_str}'
        AND nationalGridBmUnit IS NOT NULL
      GROUP BY nationalGridBmUnit, _direction
    ),
    
    ebocf_aggregated AS (
      -- Aggregate EBOCF cashflows by BMU and direction
      SELECT 
        nationalGridBmUnit,
        _direction,
        SUM(totalCashflow) as total_cashflow_gbp
      FROM `{PROJECT_ID}.uk_energy_prod.bmrs_ebocf`
      WHERE DATE(CAST(settlementDate AS STRING)) = '{date_str}'
        AND nationalGridBmUnit IS NOT NULL
      GROUP BY nationalGridBmUnit, _direction
    ),
    
    bm_combined AS (
      -- Pivot to get offer/bid columns
      SELECT 
        COALESCE(boav.nationalGridBmUnit, ebocf.nationalGridBmUnit) as bmUnit,
        
        -- Offer metrics
        MAX(CASE WHEN boav._direction = 'offer' THEN boav.total_volume_mwh ELSE 0 END) as offer_mwh,
        MAX(CASE WHEN ebocf._direction = 'offer' THEN ebocf.total_cashflow_gbp ELSE 0 END) as offer_revenue,
        
        -- Bid metrics  
        MAX(CASE WHEN boav._direction = 'bid' THEN ABS(boav.total_volume_mwh) ELSE 0 END) as bid_mwh,
        MAX(CASE WHEN ebocf._direction = 'bid' THEN ABS(ebocf.total_cashflow_gbp) ELSE 0 END) as bid_revenue,
        
        -- Activity
        MAX(CASE WHEN boav._direction = 'offer' THEN boav.active_sps 
                 WHEN boav._direction = 'bid' THEN boav.active_sps 
                 ELSE 0 END) as active_sps
        
      FROM boav_aggregated boav
      FULL OUTER JOIN ebocf_aggregated ebocf 
        ON boav.nationalGridBmUnit = ebocf.nationalGridBmUnit
        AND boav._direction = ebocf._direction
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
        SUM(COALESCE(offer_revenue, 0) + COALESCE(bid_revenue, 0)) as total_market_revenue,
        (SELECT SUM(ABS(cost)) FROM `{PROJECT_ID}.uk_energy_prod.bmrs_disbsad` 
         WHERE DATE(settlementDate) = '{date_str}') as total_market_disbsad
      FROM bm_combined
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
      bm.bmUnit,
      
      -- Revenue KPIs
      COALESCE(bm.offer_revenue, 0) + COALESCE(bm.bid_revenue, 0) as net_revenue,
      COALESCE(bm.offer_revenue, 0) as offer_revenue,
      COALESCE(bm.bid_revenue, 0) as bid_revenue,
      
      -- Volume KPIs
      COALESCE(bm.offer_mwh, 0) as offer_mwh,
      COALESCE(bm.bid_mwh, 0) as bid_mwh,
      COALESCE(bm.offer_mwh, 0) + COALESCE(bm.bid_mwh, 0) as total_mwh,
      
      -- Price KPIs (VWAP = Volume-Weighted Average Price)
      SAFE_DIVIDE(COALESCE(bm.offer_revenue, 0), COALESCE(bm.offer_mwh, 0)) as vwap_offer,
      SAFE_DIVIDE(COALESCE(bm.bid_revenue, 0), COALESCE(bm.bid_mwh, 0)) as vwap_bid,
      SAFE_DIVIDE(
        COALESCE(bm.offer_revenue, 0) + COALESCE(bm.bid_revenue, 0), 
        COALESCE(bm.offer_mwh, 0) + COALESCE(bm.bid_mwh, 0)
      ) as vwap_net,
      
      -- Activity KPIs
      COALESCE(bm.active_sps, 0) as active_sps,
      
      -- Financial Ratios
      SAFE_DIVIDE(ABS(COALESCE(bm.offer_revenue, 0)), ABS(COALESCE(bm.bid_revenue, 0))) as offer_bid_ratio,
      
      -- Constraint KPIs (DISBSAD)
      COALESCE(d.disbsad_cost, 0) as disbsad_cost,
      COALESCE(d.disbsad_actions, 0) as disbsad_actions,
      COALESCE(d.disbsad_volume, 0) as disbsad_volume,
      SAFE_DIVIDE(COALESCE(d.disbsad_cost, 0), mt.total_market_disbsad) * 100 as constraint_share_pct,
      
      -- Combined Revenue (BM + DISBSAD)
      COALESCE(bm.offer_revenue, 0) + COALESCE(bm.bid_revenue, 0) + COALESCE(d.disbsad_cost, 0) as combined_revenue,
      
      -- Technology & Capacity
      COALESCE(meta.technology, 'Unknown') as technology,
      COALESCE(meta.registeredCapacity, 0) as capacity_mw,
      COALESCE(meta.fuelType, 'Unknown') as fuel_type,
      
      -- £/MW-day (revenue normalized by capacity)
      SAFE_DIVIDE(
        COALESCE(bm.offer_revenue, 0) + COALESCE(bm.bid_revenue, 0),
        COALESCE(meta.registeredCapacity, 0)
      ) as revenue_per_mw_day,
      
      -- Market Share %
      SAFE_DIVIDE(
        ABS(COALESCE(bm.offer_revenue, 0) + COALESCE(bm.bid_revenue, 0)),
        mt.total_market_revenue
      ) * 100 as market_share_pct

    FROM bm_combined bm
    LEFT JOIN disbsad_costs d ON bm.bmUnit = d.bmUnit
    LEFT JOIN bmu_metadata meta ON bm.bmUnit = meta.bmUnit
    CROSS JOIN market_totals mt
    
    WHERE ABS(COALESCE(bm.offer_revenue, 0) + COALESCE(bm.bid_revenue, 0)) > 1  -- Filter noise
    
    ORDER BY net_revenue DESC
    LIMIT 100
    """
    
    print("\n⏳ Querying BigQuery...")
    results = client.query(query).result()
    
    bmu_data = []
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
            'constraint_share_pct': row.constraint_share_pct or 0,
            'combined_revenue': row.combined_revenue,
            'technology': row.technology,
            'capacity_mw': row.capacity_mw,
            'fuel_type': row.fuel_type,
            'revenue_per_mw_day': row.revenue_per_mw_day or 0,
            'market_share_pct': row.market_share_pct or 0
        })
    
    print(f"✅ Retrieved {len(bmu_data)} BMUs")
    
    return bmu_data, target_date

def update_google_sheet(bmu_data, analysis_date):
    """Update Google Sheets with BM revenue analysis."""
    print("\n📊 Updating Google Sheets...")
    
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except:
        worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=25)
    
    worksheet.clear()
    
    # Header
    headers = [
        ['MARKET-WIDE BM REVENUE ANALYSIS (BigQuery)'],
        [f'Date: {analysis_date.strftime("%Y-%m-%d")}', '', '', '', '', f'Total BMUs: {len(bmu_data)}'],
        [],
        ['BMU ID', 'Technology', 'Fuel', 'Net Revenue £', 'Offer £', 'Bid £',
         'Offer MWh', 'Bid MWh', 'Total MWh', 'VWAP £/MWh', 'Offer/Bid Ratio',
         'Active SPs', 'Capacity MW', '£/MW-day', 'Market Share %',
         'DISBSAD £', 'Actions', 'Constraint %', 'Combined £']
    ]
    
    # Data rows
    rows = []
    total_revenue = 0
    total_mwh = 0
    total_disbsad = 0
    total_combined = 0
    
    for bmu in bmu_data:
        total_revenue += bmu['net_revenue']
        total_mwh += bmu['total_mwh']
        total_disbsad += bmu['disbsad_cost']
        total_combined += bmu['combined_revenue']
        
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
            f"{bmu['active_sps']}/48",
            f"{bmu['capacity_mw']:.1f}",
            f"£{bmu['revenue_per_mw_day']:.2f}",
            f"{bmu['market_share_pct']:.2f}%",
            f"£{bmu['disbsad_cost']:,.0f}",
            bmu['disbsad_actions'],
            f"{bmu['constraint_share_pct']:.2f}%",
            f"£{bmu['combined_revenue']:,.0f}"
        ])
    
    # Summary row
    summary = [
        'TOTAL', '', '',
        f"£{total_revenue:,.0f}", '', '', '', '',
        f"{total_mwh:.1f}", '', '', '', '', '',
        '100.00%',
        f"£{total_disbsad:,.0f}", '',
        '100.00%',
        f"£{total_combined:,.0f}"
    ]
    
    # Write all data
    all_data = headers + rows + [[]] + [summary]
    worksheet.update('A1', all_data)
    
    # Format header
    worksheet.format('A4:S4', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True},
        'horizontalAlignment': 'CENTER'
    })
    
    print(f"✅ Updated {WORKSHEET_NAME} with {len(bmu_data)} BMUs")
    print(f"   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

def main():
    """Main execution."""
    if len(sys.argv) > 1:
        try:
            target_date = datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        except:
            print(f"Invalid date format. Use YYYY-MM-DD")
            return 1
    else:
        # Default to yesterday (settlement data lags)
        target_date = date.today() - timedelta(days=1)
    
    # Analyze BM revenue from BigQuery
    bmu_data, analysis_date = analyze_bm_revenue(target_date)
    
    if not bmu_data:
        print("❌ No data retrieved")
        return 1
    
    # Update Google Sheets
    update_google_sheet(bmu_data, analysis_date)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
