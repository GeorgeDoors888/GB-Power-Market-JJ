#!/usr/bin/env python3
"""
Comprehensive BM Revenue Analysis - ALL BMUs, Full Historical Period
Analyzes all ingested data with market-wide statistics and BMU-level details
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def analyze_full_dataset():
    """Run comprehensive analysis on ALL ingested BM settlement data"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("=" * 80)
    print("🔋 COMPREHENSIVE BM REVENUE ANALYSIS - ALL BMUS, FULL HISTORY")
    print("=" * 80)
    print()
    
    # Step 1: Get data coverage
    print("📊 Step 1: Analyzing data coverage...")
    coverage_query = """
    SELECT 
        COUNT(DISTINCT nationalGridBmUnit) as unique_bmus,
        COUNT(DISTINCT DATE(CAST(settlementDate AS STRING))) as days_coverage,
        MIN(DATE(CAST(settlementDate AS STRING))) as min_date,
        MAX(DATE(CAST(settlementDate AS STRING))) as max_date,
        COUNT(*) as total_records
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav`
    """
    coverage = list(client.query(coverage_query).result())[0]
    
    print(f"   ✅ {coverage.unique_bmus:,} unique BMUs")
    print(f"   ✅ {coverage.days_coverage:,} days covered")
    print(f"   ✅ {coverage.total_records:,} BOAV records")
    print(f"   ✅ Date range: {coverage.min_date} to {coverage.max_date}")
    print()
    
    # Step 2: Market-wide summary
    print("📊 Step 2: Calculating market-wide statistics...")
    market_query = """
    WITH daily_totals AS (
        SELECT 
            DATE(CAST(boav.settlementDate AS STRING)) as date,
            SUM(CASE WHEN boav._direction = 'offer' THEN ebocf.totalCashflow ELSE 0 END) as total_offer_revenue,
            SUM(CASE WHEN boav._direction = 'bid' THEN ebocf.totalCashflow ELSE 0 END) as total_bid_revenue,
            SUM(CASE WHEN boav._direction = 'offer' THEN boav.totalVolumeAccepted ELSE 0 END) as total_offer_mwh,
            SUM(CASE WHEN boav._direction = 'bid' THEN boav.totalVolumeAccepted ELSE 0 END) as total_bid_mwh,
            COUNT(DISTINCT boav.nationalGridBmUnit) as active_bmus
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav` boav
        LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf` ebocf
            ON boav.nationalGridBmUnit = ebocf.nationalGridBmUnit
            AND boav.settlementDate = ebocf.settlementDate
            AND boav.settlementPeriod = ebocf.settlementPeriod
            AND boav._direction = ebocf._direction
        GROUP BY date
    )
    SELECT 
        COUNT(*) as trading_days,
        SUM(total_offer_revenue + total_bid_revenue) as total_revenue,
        AVG(total_offer_revenue + total_bid_revenue) as avg_daily_revenue,
        SUM(total_offer_mwh + total_bid_mwh) as total_volume_mwh,
        AVG(active_bmus) as avg_active_bmus_per_day
    FROM daily_totals
    """
    market = list(client.query(market_query).result())[0]
    
    print(f"   💰 Total BM Revenue: £{market.total_revenue:,.0f}")
    print(f"   💰 Average Daily Revenue: £{market.avg_daily_revenue:,.0f}")
    print(f"   ⚡ Total Volume: {market.total_volume_mwh:,.0f} MWh")
    print(f"   📊 Trading Days: {market.trading_days}")
    print(f"   🏭 Avg Active BMUs/Day: {market.avg_active_bmus_per_day:.0f}")
    print()
    
    # Step 3: Top BMUs by technology
    print("📊 Step 3: Analyzing top BMUs by technology...")
    top_bmus_query = """
    WITH bmu_totals AS (
        SELECT 
            boav.nationalGridBmUnit,
            meta.fuelType as technology,
            meta.registeredCapacity as capacity_mw,
            SUM(CASE WHEN boav._direction = 'offer' THEN ebocf.totalCashflow ELSE 0 END) as offer_revenue,
            SUM(CASE WHEN boav._direction = 'bid' THEN ebocf.totalCashflow ELSE 0 END) as bid_revenue,
            SUM(CASE WHEN boav._direction = 'offer' THEN ebocf.totalCashflow ELSE 0 END) +
            SUM(CASE WHEN boav._direction = 'bid' THEN ebocf.totalCashflow ELSE 0 END) as net_revenue,
            SUM(CASE WHEN boav._direction = 'offer' THEN boav.totalVolumeAccepted ELSE 0 END) as offer_mwh,
            SUM(CASE WHEN boav._direction = 'bid' THEN boav.totalVolumeAccepted ELSE 0 END) as bid_mwh,
            COUNT(DISTINCT DATE(CAST(boav.settlementDate AS STRING))) as active_days,
            COUNT(DISTINCT boav.settlementPeriod) as active_sps
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav` boav
        LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf` ebocf
            ON boav.nationalGridBmUnit = ebocf.nationalGridBmUnit
            AND boav.settlementDate = ebocf.settlementDate
            AND boav.settlementPeriod = ebocf.settlementPeriod
            AND boav._direction = ebocf._direction
        LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_metadata` meta
            ON boav.nationalGridBmUnit = meta.nationalGridBmUnit
        GROUP BY boav.nationalGridBmUnit, meta.fuelType, meta.registeredCapacity
    )
    SELECT 
        nationalGridBmUnit,
        technology,
        capacity_mw,
        net_revenue,
        offer_revenue,
        bid_revenue,
        offer_mwh,
        bid_mwh,
        active_days,
        active_sps,
        CASE 
            WHEN capacity_mw > 0 AND active_days > 0 
            THEN net_revenue / (capacity_mw * active_days)
            ELSE 0 
        END as revenue_per_mw_day,
        CASE 
            WHEN offer_mwh + bid_mwh > 0 
            THEN net_revenue / (offer_mwh + bid_mwh)
            ELSE 0 
        END as vwap
    FROM bmu_totals
    ORDER BY net_revenue DESC
    LIMIT 200
    """
    
    df = client.query(top_bmus_query).to_dataframe()
    print(f"   ✅ Retrieved {len(df)} BMUs")
    print()
    
    # Technology breakdown
    tech_summary = df.groupby('technology').agg({
        'net_revenue': 'sum',
        'offer_mwh': 'sum',
        'bid_mwh': 'sum',
        'nationalGridBmUnit': 'count'
    }).sort_values('net_revenue', ascending=False)
    
    print("📊 Revenue by Technology:")
    for tech, row in tech_summary.head(10).iterrows():
        print(f"   {tech or 'Unknown':20s}: £{row['net_revenue']:>12,.0f}  ({row['nationalGridBmUnit']:>3.0f} BMUs)")
    print()
    
    # Step 4: Update Google Sheets
    print("📊 Step 4: Updating Google Sheets...")
    
    # Prepare data for sheets
    headers = [
        'BMU ID', 'Technology', 'Capacity (MW)', 
        'Net Revenue (£)', 'Offer Revenue (£)', 'Bid Revenue (£)',
        'Offer MWh', 'Bid MWh', 'Total MWh',
        'Active Days', 'Active SPs', 
        'VWAP (£/MWh)', '£/MW-day'
    ]
    
    sheet_data = [headers]
    for _, row in df.iterrows():
        sheet_data.append([
            row['nationalGridBmUnit'],
            row['technology'] or 'Unknown',
            f"{row['capacity_mw']:.1f}" if pd.notna(row['capacity_mw']) else 'N/A',
            f"{row['net_revenue']:.2f}",
            f"{row['offer_revenue']:.2f}",
            f"{row['bid_revenue']:.2f}",
            f"{row['offer_mwh']:.2f}",
            f"{row['bid_mwh']:.2f}",
            f"{row['offer_mwh'] + row['bid_mwh']:.2f}",
            int(row['active_days']),
            int(row['active_sps']),
            f"{row['vwap']:.2f}",
            f"{row['revenue_per_mw_day']:.2f}"
        ])
    
    # Connect to Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gc = gspread.authorize(creds)
    
    # Update "BM Revenue Analysis - Full History" sheet
    spreadsheet = gc.open_by_key(SHEET_ID)
    try:
        worksheet = spreadsheet.worksheet("BM Revenue Analysis - Full History")
        worksheet.clear()
    except:
        worksheet = spreadsheet.add_worksheet("BM Revenue Analysis - Full History", rows=1000, cols=20)
    
    worksheet.update(range_name='A1', values=sheet_data)
    
    print(f"   ✅ Updated 'BM Revenue Analysis - Full History' with {len(df)} BMUs")
    print(f"   📊 Date range: {coverage.min_date} to {coverage.max_date}")
    print(f"   🔗 URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print()
    
    # Step 5: Generate summary statistics
    print("📊 Step 5: Summary Statistics")
    print("=" * 80)
    print(f"Dataset Coverage:")
    print(f"  • {coverage.unique_bmus:,} unique BMUs")
    print(f"  • {coverage.days_coverage:,} days ({coverage.min_date} to {coverage.max_date})")
    print(f"  • {coverage.total_records:,} BOAV records")
    print()
    print(f"Market Totals:")
    print(f"  • Total Revenue: £{market.total_revenue:,.0f}")
    print(f"  • Total Volume: {market.total_volume_mwh:,.0f} MWh")
    print(f"  • Avg Daily Revenue: £{market.avg_daily_revenue:,.0f}")
    print()
    print(f"Top 5 BMUs by Revenue:")
    for i, (_, row) in enumerate(df.head(5).iterrows(), 1):
        print(f"  {i}. {row['nationalGridBmUnit']:12s} ({row['technology'] or 'Unknown':15s}): £{row['net_revenue']:>12,.0f}")
    print()
    
    print("=" * 80)
    print("✅ COMPREHENSIVE ANALYSIS COMPLETE")
    print("=" * 80)
    
    return df, coverage, market

if __name__ == "__main__":
    df, coverage, market = analyze_full_dataset()
