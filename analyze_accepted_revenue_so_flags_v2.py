#!/usr/bin/env python3
"""
BM Accepted Revenue Analysis with SO Flags - CORRECTED VERSION

Analyzes ESTIMATED accepted balancing mechanism revenue (not actual settlement) by querying:
- BOAV: Accepted volumes by BMU/SP/direction (aggregated settlement volumes)
- EBOCF: Indicative cashflows for accepted actions  
- BOALF: Acceptance-level data with SO flags (system operator action reasons)

⚠️ DATA GRADE DISCLAIMER:
All revenue figures are ESTIMATES from Elexon BMRS transparency data.
These are NOT settlement-grade cashflows. Actual BOA energy payments are
determined through BSC settlement and may vary ±10-20% from these estimates.

For settlement-grade data, BSC Parties must refer to SAA settlement reports.
See BOA_ENERGY_PAYMENTS_EXPLAINED.md for full explanation.

IMPORTANT CORRECTIONS:
1. BOAV rows are BMU×SP×direction records, NOT individual acceptances
2. Use proper VWAP: SUM(cashflow)/SUM(mwh), not AVG(cashflow/mwh)
3. BOALF: Historical (to 2025-11-04) + IRIS (2025-10-30+) for full coverage
4. SO flags are boolean: True=Energy balancing, False=System/constraint action
5. MWh proxy from BOALF: avg(levelFrom,levelTo) × duration_hours
6. EBOCF is "indicative cashflow" - not final settled amounts (BMRS transparency)

Author: Generated for GB Power Market Analysis
Date: 2025-12-15 (Updated with data grade disclaimers)
"""

import logging
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def main(analysis_days=30):
    """
    Main analysis function
    
    Args:
        analysis_days: Number of days to analyze (default: 30)
                      Use 0 for all available data
    """
    
    logging.info("=" * 80)
    logging.info("💰 BM ACTUAL REVENUE - ACCEPTED ACTIONS WITH SO FLAGS (CORRECTED)")
    logging.info("=" * 80)
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Calculate analysis period
    if analysis_days == 0:
        analysis_start_date = '2022-01-01'  # All available data
        period_label = 'All available data'
    else:
        analysis_start_date = (datetime.now() - timedelta(days=analysis_days)).strftime('%Y-%m-%d')
        period_label = f'Last {analysis_days} days'
    
    logging.info(f"📊 Analysis period: {analysis_start_date} to present ({period_label})")
    logging.info(f"   Data sources:")
    logging.info(f"   - BOAV/EBOCF: Settlement volumes and cashflows")
    logging.info(f"   - BOALF: Historical (to Nov 4) + IRIS streaming (Oct 30+)")
    
    # ============================================================================
    # STEP 1: ACCEPTED REVENUE WITH PROPER VWAP (BOAV + EBOCF)
    # ============================================================================
    
    logging.info("\n📊 Step 1: Calculating accepted revenue with proper VWAP...")
    
    revenue_query = f"""
    WITH accepted_with_cash AS (
      SELECT
        CAST(boav.settlementDate AS DATE) AS date,
        boav.settlementPeriod,
        boav.nationalGridBmUnit,
        meta.fuelType,
        boav._direction,
        ABS(boav.totalVolumeAccepted) AS accepted_mwh,
        ebocf.totalCashflow AS cashflow_gbp
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boav` boav
      LEFT JOIN `{PROJECT_ID}.{DATASET}.bmrs_ebocf` ebocf
        ON boav.nationalGridBmUnit = ebocf.nationalGridBmUnit
       AND boav.settlementDate = ebocf.settlementDate
       AND boav.settlementPeriod = ebocf.settlementPeriod
       AND boav._direction = ebocf._direction
      LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_metadata` meta
        ON boav.nationalGridBmUnit = meta.nationalGridBmUnit
      WHERE CAST(boav.settlementDate AS DATE) >= '{analysis_start_date}'
        AND ABS(boav.totalVolumeAccepted) > 0
        AND ebocf.totalCashflow IS NOT NULL
    ),
    daily_summary AS (
      SELECT
        date,
        fuelType,
        _direction,
        COUNT(*) AS record_count,              -- BMU×SP×direction records (NOT acceptances)
        SUM(accepted_mwh) AS total_mwh,
        SUM(cashflow_gbp) AS total_revenue_gbp,
        SAFE_DIVIDE(SUM(cashflow_gbp), NULLIF(SUM(accepted_mwh),0)) AS vwap_gbp_per_mwh,
        COUNT(DISTINCT nationalGridBmUnit) AS unique_bmus
      FROM accepted_with_cash
      GROUP BY date, fuelType, _direction
    )
    SELECT *
    FROM daily_summary
    ORDER BY date DESC, total_revenue_gbp DESC
    """
    
    df_revenue = client.query(revenue_query).to_dataframe()
    
    logging.info(f"   ✅ Retrieved {len(df_revenue)} daily records (BMU×SP×direction aggregates)")
    
    # ============================================================================
    # STEP 2: TECHNOLOGY SUMMARY WITH PROPER VWAP
    # ============================================================================
    
    logging.info("\n📊 Step 2: Summarizing by technology with proper VWAP...")
    
    tech_summary = df_revenue.groupby(['fuelType', '_direction']).agg({
        'record_count': 'sum',
        'total_mwh': 'sum',
        'total_revenue_gbp': 'sum',
        'unique_bmus': 'max'
    }).reset_index()
    
    # Recalculate VWAP at technology level
    tech_summary['vwap_gbp_per_mwh'] = (
        tech_summary['total_revenue_gbp'] / tech_summary['total_mwh']
    )
    
    tech_summary = tech_summary.sort_values('total_revenue_gbp', ascending=False)
    
    logging.info(f"\n   Accepted Revenue by Technology & Direction (Last 30 days):")
    logging.info(f"   {'Technology':<15} {'Direction':<8} {'Records':>10} {'MWh':>12} {'Revenue (£)':>15} {'VWAP £/MWh':>12}")
    
    for _, row in tech_summary.head(15).iterrows():
        tech = row['fuelType'] or 'Unknown'
        logging.info(
            f"   {tech:<15} {row['_direction']:<8} {row['record_count']:>10,.0f} "
            f"{row['total_mwh']:>12,.0f} £{row['total_revenue_gbp']:>14,.0f} "
            f"£{row['vwap_gbp_per_mwh']:>11,.2f}"
        )
    
    # ============================================================================
    # STEP 3: SO FLAG DISTRIBUTION FROM BOALF (COMBINED HISTORICAL + IRIS)
    # ============================================================================
    
    logging.info(f"\n📊 Step 3: Analyzing SO Flag distribution from BOALF (last 30 days)...")
    logging.info(f"   Using UNION of bmrs_boalf (historical) + bmrs_boalf_iris (real-time)")
    
    so_flag_query = f"""
    WITH combined_boalf AS (
      -- Historical BOALF (Jan 2022 - Nov 4, 2025)
      SELECT
        settlementDate,
        nationalGridBmUnit,
        soFlag,
        levelFrom,
        levelTo,
        CAST(timeFrom AS TIMESTAMP) as timeFrom,
        CAST(timeTo AS TIMESTAMP) as timeTo
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) >= '{analysis_start_date}'
      
      UNION ALL
      
      -- IRIS BOALF (Oct 30, 2025 - present)
      SELECT
        settlementDate,
        nationalGridBmUnit,
        soFlag,
        levelFrom,
        levelTo,
        CAST(timeFrom AS TIMESTAMP) as timeFrom,
        CAST(timeTo AS TIMESTAMP) as timeTo
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) >= '{analysis_start_date}'
    )
    SELECT
      soFlag,
      COUNT(*) AS acceptance_count,
      COUNT(DISTINCT nationalGridBmUnit) AS unique_bmus,
      
      -- MWh proxy: average absolute MW level over the window × duration (hours)
      SUM(
        ABS( (CAST(levelFrom AS FLOAT64) + CAST(levelTo AS FLOAT64)) / 2.0 )
        * (TIMESTAMP_DIFF(timeTo, timeFrom, SECOND) / 3600.0)
      ) AS total_mwh_proxy
    
    FROM combined_boalf
    GROUP BY soFlag
    ORDER BY acceptance_count DESC
    """
    
    df_so_flags = client.query(so_flag_query).to_dataframe()
    
    if not df_so_flags.empty:
        logging.info(f"\n   SO Flag Distribution (acceptance-level data):")
        logging.info(f"   {'SO Flag':<10} {'Acceptances':>12} {'MWh proxy':>12} {'BMUs':>8}")
        
        total_acceptances = df_so_flags['acceptance_count'].sum()
        
        for _, row in df_so_flags.iterrows():
            flag_value = row['soFlag']
            if pd.isna(flag_value):
                flag_name = 'NULL'
            elif flag_value:
                flag_name = 'True'
            else:
                flag_name = 'False'
            
            pct = (row['acceptance_count'] / total_acceptances * 100) if total_acceptances > 0 else 0
            
            logging.info(
                f"   {flag_name:<10} {row['acceptance_count']:>12,.0f} ({pct:>5.1f}%) "
                f"{row['total_mwh_proxy']:>12,.1f} {row['unique_bmus']:>8,.0f}"
            )
        
        logging.info(f"\n   Total acceptances (BOALF): {total_acceptances:,}")
    else:
        logging.info("   ⚠️  No SO Flag data available")
        df_so_flags = pd.DataFrame()
    
    # ============================================================================
    # STEP 4: DAILY TOTALS
    # ============================================================================
    
    logging.info("\n📊 Step 4: Daily revenue totals...")
    
    daily_totals = df_revenue.groupby('date').agg({
        'record_count': 'sum',
        'total_mwh': 'sum',
        'total_revenue_gbp': 'sum'
    }).reset_index().sort_values('date', ascending=False)
    
    logging.info(f"\n   Last 10 Days - Actual BM Revenue:")
    for _, row in daily_totals.head(10).iterrows():
        logging.info(
            f"   {row['date']} - {row['record_count']:>6,.0f} records, "
            f"{row['total_mwh']:>10,.0f} MWh, £{row['total_revenue_gbp']:>12,.0f}"
        )
    
    # ============================================================================
    # STEP 5: UPDATE GOOGLE SHEETS
    # ============================================================================
    
    logging.info("\n📊 Step 5: Updating Google Sheets...")
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    
    # Create or update sheet
    try:
        worksheet = spreadsheet.worksheet("BM Accepted Revenue - SO Flags")
        worksheet.clear()
    except:
        worksheet = spreadsheet.add_worksheet("BM Accepted Revenue - SO Flags", rows=2000, cols=15)
    
    # Prepare sheet data
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    sheet_data = [
        ['💰 BM ACTUAL REVENUE - ACCEPTED ACTIONS WITH SO FLAGS (CORRECTED)'],
        [f'Updated: {date_str}', '', '', f'Period: {period_label} ({analysis_start_date} to present)'],
        ['', '', '', '⚠️ Note: BOAV records are BMU×SP×direction aggregates, NOT individual acceptances'],
        ['', '', '', '✅ SO Flags from combined BOALF (historical + IRIS streaming)'],
        [''],
        ['📊 DAILY ACCEPTED REVENUE BY TECHNOLOGY (Proper VWAP Calculation)'],
        ['Date', 'Technology', 'Direction', 'Records', 'MWh Accepted', 
         'Indicative Revenue (£)', 'VWAP £/MWh', 'Unique BMUs']
    ]
    
    for _, row in df_revenue.head(500).iterrows():
        sheet_data.append([
            row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else '',
            row['fuelType'] or 'Unknown',
            row['_direction'],
            int(row['record_count']) if pd.notna(row['record_count']) else 0,
            f"{row['total_mwh']:.1f}" if pd.notna(row['total_mwh']) else '0',
            f"{row['total_revenue_gbp']:.2f}" if pd.notna(row['total_revenue_gbp']) else '0',
            f"{row['vwap_gbp_per_mwh']:.2f}" if pd.notna(row['vwap_gbp_per_mwh']) else '0',
            int(row['unique_bmus']) if pd.notna(row['unique_bmus']) else 0
        ])
    
    # Add SO Flag analysis if available
    if not df_so_flags.empty:
        sheet_data.append([''])
        sheet_data.append(['📊 SO FLAG DISTRIBUTION (System Operator Action Reasons)'])
        sheet_data.append([f'Period: {period_label} - Combined BOALF (historical + IRIS streaming)'])
        sheet_data.append(['SO Flag', 'Acceptance Count', 'MWh Proxy', 'Unique BMUs', 'Description'])
        
        # SO Flag descriptions
        flag_descriptions = {
            True: 'True - Energy balancing action (system short of energy)',
            False: 'False - System action (constraints, security)',
            None: 'NULL - Flag not set'
        }
        
        total_count = df_so_flags['acceptance_count'].sum()
        
        for _, row in df_so_flags.iterrows():
            flag = row['soFlag']
            if pd.isna(flag):
                flag_display = 'NULL'
                flag_key = None
            elif flag:
                flag_display = 'True'
                flag_key = True
            else:
                flag_display = 'False'
                flag_key = False
            
            description = flag_descriptions.get(flag_key, 'Other')
            count = int(row['acceptance_count']) if pd.notna(row['acceptance_count']) else 0
            percentage = (count / total_count * 100) if total_count > 0 else 0
            
            sheet_data.append([
                flag_display,
                f"{count:,} ({percentage:.1f}%)",
                f"{row['total_mwh_proxy']:.1f}" if pd.notna(row['total_mwh_proxy']) else '0',
                int(row['unique_bmus']) if pd.notna(row['unique_bmus']) else 0,
                description
            ])
    
    # Add technology summary section
    sheet_data.append([''])
    sheet_data.append(['📊 TECHNOLOGY SUMMARY (Last 30 days - Proper VWAP)'])
    sheet_data.append(['Technology', 'Direction', 'Records', 'Total MWh', 
                       'Indicative Revenue (£)', 'VWAP £/MWh', 'BMUs'])
    
    for _, row in tech_summary.iterrows():
        sheet_data.append([
            row['fuelType'] or 'Unknown',
            row['_direction'],
            int(row['record_count']) if pd.notna(row['record_count']) else 0,
            f"{row['total_mwh']:.1f}" if pd.notna(row['total_mwh']) else '0',
            f"{row['total_revenue_gbp']:.2f}" if pd.notna(row['total_revenue_gbp']) else '0',
            f"{row['vwap_gbp_per_mwh']:.2f}" if pd.notna(row['vwap_gbp_per_mwh']) else '0',
            int(row['unique_bmus']) if pd.notna(row['unique_bmus']) else 0
        ])
    
    # Add methodology notes
    sheet_data.append([''])
    sheet_data.append(['📝 METHODOLOGY NOTES'])
    sheet_data.append(['1. Records', 'BOAV rows are BMU×SP×direction aggregates, NOT individual acceptance counts'])
    sheet_data.append(['2. VWAP', 'Proper volume-weighted average: SUM(cashflow) / SUM(mwh)'])
    sheet_data.append(['3. Revenue', 'EBOCF indicative cashflows - not final settled amounts'])
    sheet_data.append(['4. SO Flags', 'True=Energy balancing, False=System/constraint action'])
    sheet_data.append(['5. MWh Proxy', 'BOALF: avg(levelFrom,levelTo) × duration_hours'])
    sheet_data.append(['6. Data Coverage', 'BOALF: Historical (Jan 2022-Nov 4) + IRIS streaming (Oct 30-present)'])
    
    # Update sheet
    worksheet.update(range_name='A1', values=sheet_data)
    
    # Format headers
    worksheet.format('A1:H1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 14}
    })
    
    worksheet.format('A5:H5', {
        'backgroundColor': {'red': 0.3, 'green': 0.3, 'blue': 0.3},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
    })
    
    logging.info(f"   ✅ Updated 'BM Accepted Revenue - SO Flags' with {len(df_revenue)} records")
    logging.info(f"   🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    
    # ============================================================================
    # FINAL SUMMARY
    # ============================================================================
    
    logging.info("\n" + "=" * 80)
    logging.info("✅ BM ACCEPTED REVENUE ANALYSIS COMPLETE")
    logging.info("=" * 80)
    
    total_records = df_revenue['record_count'].sum()
    total_mwh = df_revenue['total_mwh'].sum()
    total_revenue = df_revenue['total_revenue_gbp'].sum()
    vwap = total_revenue / total_mwh if total_mwh > 0 else 0
    
    logging.info(f"\nActual Accepted Revenue ({period_label}):")
    logging.info(f"  • Total BOAV records (BMU×SP×direction): {total_records:,.0f}")
    logging.info(f"  • Total volume accepted: {total_mwh:,.0f} MWh")
    logging.info(f"  • Total indicative revenue: £{total_revenue:,.2f}")
    logging.info(f"  • Overall VWAP: £{vwap:.2f}/MWh")
    
    if not df_so_flags.empty:
        total_acceptances = df_so_flags['acceptance_count'].sum()
        true_count = df_so_flags[df_so_flags['soFlag'] == True]['acceptance_count'].sum() if True in df_so_flags['soFlag'].values else 0
        false_count = df_so_flags[df_so_flags['soFlag'] == False]['acceptance_count'].sum() if False in df_so_flags['soFlag'].values else 0
        
        logging.info(f"\nSO Flag Distribution ({period_label} - combined BOALF):")
        logging.info(f"  • Total BOALF acceptances: {total_acceptances:,.0f}")
        if true_count > 0:
            logging.info(f"  • Energy balancing (True): {true_count:,.0f} ({true_count/total_acceptances*100:.1f}%)")
        if false_count > 0:
            logging.info(f"  • System/constraint (False): {false_count:,.0f} ({false_count/total_acceptances*100:.1f}%)")

if __name__ == "__main__":
    import sys
    
    # Allow command-line argument for analysis period
    # Usage: python3 analyze_accepted_revenue_so_flags_v2.py [days]
    # Examples:
    #   python3 analyze_accepted_revenue_so_flags_v2.py 30   # Last 30 days (default)
    #   python3 analyze_accepted_revenue_so_flags_v2.py 90   # Last 90 days
    #   python3 analyze_accepted_revenue_so_flags_v2.py 365  # Last year
    #   python3 analyze_accepted_revenue_so_flags_v2.py 0    # All available data
    
    days = 30  # Default
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            logging.error(f"Invalid days argument: {sys.argv[1]}. Using default (30 days).")
    
    main(analysis_days=days)
