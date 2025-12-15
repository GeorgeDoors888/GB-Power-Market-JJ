#!/usr/bin/env python3
"""
BM Revenue Analysis - Full History Auto-Updater
Runs daily to update comprehensive BM revenue analysis with charts
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "BM Revenue Analysis - Full History"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def update_bm_revenue_analysis():
    """Update BM Revenue Analysis with latest data and charts"""
    
    logging.info("="*80)
    logging.info("🔋 BM REVENUE ANALYSIS - FULL HISTORY AUTO-UPDATE")
    logging.info("="*80)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Step 1: Get data coverage
    logging.info("📊 Fetching data coverage...")
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
    
    logging.info(f"   ✅ {coverage.unique_bmus:,} unique BMUs")
    logging.info(f"   ✅ {coverage.days_coverage:,} days: {coverage.min_date} to {coverage.max_date}")
    logging.info(f"   ✅ {coverage.total_records:,} BOAV records")
    
    # Step 2: Get comprehensive BMU analysis
    logging.info("📊 Analyzing all BMUs...")
    analysis_query = """
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
            WHEN offer_mwh + bid_mwh != 0 
            THEN net_revenue / (offer_mwh + bid_mwh)
            ELSE 0 
        END as vwap
    FROM bmu_totals
    ORDER BY net_revenue DESC
    LIMIT 200
    """
    
    df = client.query(analysis_query).to_dataframe()
    logging.info(f"   ✅ Retrieved {len(df)} BMUs")
    
    # Step 3: Prepare sheet data
    logging.info("📊 Preparing sheet data...")
    
    # Header with metadata
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    headers = [
        [f'🔋 BM REVENUE ANALYSIS - FULL HISTORY'],
        [f'Updated: {date_str}', '', '', '', f'Period: {coverage.min_date} to {coverage.max_date}'],
        [f'{coverage.unique_bmus:,} BMUs', '', '', '', f'{coverage.days_coverage:,} days', '', '', f'{coverage.total_records:,} records'],
        [''],
        ['BMU ID', 'Technology', 'Capacity (MW)', 
         'Net Revenue (£)', 'Offer Revenue (£)', 'Bid Revenue (£)',
         'Offer MWh', 'Bid MWh', 'Total MWh',
         'Active Days', 'Active SPs', 
         'VWAP (£/MWh)', '£/MW-day', 'Bar Chart']
    ]
    
    sheet_data = headers.copy()
    
    # Data rows with bar chart formulas
    for _, row in df.iterrows():
        total_mwh = row['offer_mwh'] + row['bid_mwh']
        bar_formula = f'=REPT("█",MIN(INT({row["net_revenue"]}/10000000),50))'  # Scale to fit
        
        sheet_data.append([
            row['nationalGridBmUnit'],
            row['technology'] or 'Unknown',
            f"{row['capacity_mw']:.1f}" if pd.notna(row['capacity_mw']) else 'N/A',
            f"{row['net_revenue']:.2f}",
            f"{row['offer_revenue']:.2f}",
            f"{row['bid_revenue']:.2f}",
            f"{row['offer_mwh']:.2f}",
            f"{row['bid_mwh']:.2f}",
            f"{total_mwh:.2f}",
            int(row['active_days']),
            int(row['active_sps']),
            f"{row['vwap']:.2f}",
            f"{row['revenue_per_mw_day']:.2f}",
            bar_formula
        ])
    
    # Step 4: Update Google Sheets
    logging.info("📊 Updating Google Sheets...")
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)
    
    # Clear and update
    worksheet.clear()
    worksheet.update(range_name='A1', values=sheet_data)
    
    # Format headers
    worksheet.format('A1:N1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 14}
    })
    
    worksheet.format('A5:N5', {
        'backgroundColor': {'red': 0.4, 'green': 0.4, 'blue': 0.4},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
    })
    
    # Format bar chart column
    worksheet.format('N6:N300', {
        'textFormat': {'foregroundColor': {'red': 0, 'green': 0.6, 'blue': 1}, 'bold': True}
    })
    
    # Number formatting
    worksheet.format('D6:F300', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'}})
    worksheet.format('G6:I300', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.0'}})
    worksheet.format('L6:M300', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'}})
    
    logging.info(f"   ✅ Updated '{SHEET_NAME}' with {len(df)} BMUs")
    logging.info(f"   📊 Date range: {coverage.min_date} to {coverage.max_date}")
    logging.info(f"   🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    
    # Step 5: Summary
    tech_summary = df.groupby('technology').agg({
        'net_revenue': 'sum',
        'nationalGridBmUnit': 'count'
    }).sort_values('net_revenue', ascending=False)
    
    logging.info("\n📊 Top 5 Technologies:")
    for tech, row in tech_summary.head(5).iterrows():
        logging.info(f"   {tech or 'Unknown':15s}: £{row['net_revenue']:>14,.0f}  ({row['nationalGridBmUnit']:>3.0f} BMUs)")
    
    logging.info("\n" + "="*80)
    logging.info("✅ BM REVENUE ANALYSIS UPDATE COMPLETE")
    logging.info("="*80)

if __name__ == "__main__":
    try:
        update_bm_revenue_analysis()
    except Exception as e:
        logging.error(f"❌ Error: {e}", exc_info=True)
        raise
