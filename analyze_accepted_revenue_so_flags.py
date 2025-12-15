#!/usr/bin/env python3
"""
BM Actual Revenue Analysis - Accepted Actions with SO Flags
Shows definite revenue from accepted BOA/BOALF actions with SO Flag categorization
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def analyze_accepted_revenue_with_flags():
    """Analyze actual accepted BM actions with SO flags and definite revenue"""
    
    logging.info("="*80)
    logging.info("💰 BM ACTUAL REVENUE - ACCEPTED ACTIONS WITH SO FLAGS")
    logging.info("="*80)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Step 1: Get accepted volumes with SO flags from BOALF (acceptance level)
    logging.info("📊 Step 1: Analyzing accepted actions with SO flags...")
    
    # Check if we have BOALF data
    check_query = """
    SELECT COUNT(*) as count
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
    LIMIT 1
    """
    
    try:
        result = client.query(check_query).to_dataframe()
        if result.iloc[0]['count'] == 0:
            logging.warning("   ⚠️  BOALF table is empty, using BOAV instead")
            use_boalf = False
        else:
            use_boalf = True
            logging.info(f"   ✅ Found {result.iloc[0]['count']:,} BOALF records")
    except:
        logging.warning("   ⚠️  BOALF table not found, using BOAV")
        use_boalf = False
    
    # Step 2: Analyze accepted volumes and revenue with cashflows
    logging.info("📊 Step 2: Calculating actual accepted revenue...")
    
    accepted_query = """
    WITH accepted_with_cash AS (
        SELECT 
            DATE(CAST(boav.settlementDate AS STRING)) as date,
            boav.settlementPeriod,
            boav.nationalGridBmUnit,
            meta.fuelType,
            boav._direction,
            ABS(boav.totalVolumeAccepted) as accepted_mwh,
            ebocf.totalCashflow as cashflow_gbp
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav` boav
        LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf` ebocf
            ON boav.nationalGridBmUnit = ebocf.nationalGridBmUnit
            AND boav.settlementDate = ebocf.settlementDate
            AND boav.settlementPeriod = ebocf.settlementPeriod
            AND boav._direction = ebocf._direction
        LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_metadata` meta
            ON boav.nationalGridBmUnit = meta.nationalGridBmUnit
        WHERE DATE(CAST(boav.settlementDate AS STRING)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
          AND ABS(boav.totalVolumeAccepted) > 0
    ),
    daily_summary AS (
        SELECT 
            date,
            fuelType,
            _direction,
            COUNT(*) as acceptance_count,
            SUM(accepted_mwh) as total_mwh,
            SUM(cashflow_gbp) as total_revenue_gbp,
            AVG(cashflow_gbp / NULLIF(accepted_mwh, 0)) as avg_price_per_mwh,
            COUNT(DISTINCT nationalGridBmUnit) as unique_bmus
        FROM accepted_with_cash
        WHERE cashflow_gbp IS NOT NULL
        GROUP BY date, fuelType, _direction
    )
    SELECT 
        date,
        fuelType,
        _direction,
        acceptance_count,
        total_mwh,
        total_revenue_gbp,
        avg_price_per_mwh,
        unique_bmus
    FROM daily_summary
    ORDER BY date DESC, total_revenue_gbp DESC
    """
    
    df_accepted = client.query(accepted_query).to_dataframe()
    logging.info(f"   ✅ Retrieved {len(df_accepted)} daily acceptance records")
    
    # Step 3: Technology summary
    logging.info("📊 Step 3: Summarizing by technology...")
    
    tech_summary = df_accepted.groupby(['fuelType', '_direction']).agg({
        'acceptance_count': 'sum',
        'total_mwh': 'sum',
        'total_revenue_gbp': 'sum',
        'avg_price_per_mwh': 'mean',
        'unique_bmus': 'max'
    }).sort_values('total_revenue_gbp', ascending=False)
    
    logging.info("\n   Accepted Revenue by Technology & Direction (Last 30 days):")
    logging.info(f"   {'Technology':<15} {'Direction':<8} {'Acceptances':>12} {'MWh':>12} {'Revenue (£)':>15} {'£/MWh':>10}")
    
    for (tech, direction), row in tech_summary.head(20).iterrows():
        logging.info(f"   {tech or 'Unknown':<15} {direction:<8} {row['acceptance_count']:>12,.0f} "
                    f"{row['total_mwh']:>12,.0f} £{row['total_revenue_gbp']:>13,.0f} "
                    f"£{row['avg_price_per_mwh']:>9,.2f}")
    
    # Step 4: Daily revenue totals
    logging.info("\n📊 Step 4: Daily revenue totals...")
    
    daily_totals = df_accepted.groupby('date').agg({
        'acceptance_count': 'sum',
        'total_mwh': 'sum',
        'total_revenue_gbp': 'sum'
    }).sort_values('date', ascending=False)
    
    logging.info(f"\n   Last 10 Days - Actual BM Revenue:")
    for date, row in daily_totals.head(10).iterrows():
        logging.info(f"   {date} - {row['acceptance_count']:>6,.0f} acceptances, "
                    f"{row['total_mwh']:>10,.0f} MWh, £{row['total_revenue_gbp']:>12,.0f}")
    
    # Step 5: Check for SO Flag data in BOALF
    logging.info("\n📊 Step 5: Checking SO Flag distribution...")
    
    # Note: SO Flag indicates reason for acceptance (Energy, System, etc)
    # We'll try to get this from BOALF if available
    
    try:
        flag_query = """
        SELECT 
            soFlag,
            COUNT(*) as count,
            COUNT(DISTINCT nationalGridBmUnit) as unique_bmus
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
        WHERE DATE(CAST(settlementDate AS STRING)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY soFlag
        ORDER BY count DESC
        """
        
        df_flags = client.query(flag_query).to_dataframe()
        
        if not df_flags.empty:
            logging.info(f"\n   SO Flag Distribution (Last 30 days):")
            logging.info(f"   {'SO Flag':<20} {'Acceptances':>12} {'BMUs':>8}")
            for _, row in df_flags.iterrows():
                flag_name = row['soFlag'] or 'NULL/Unknown'
                logging.info(f"   {flag_name:<20} {row['count']:>12,.0f} {row['unique_bmus']:>8,.0f}")
        else:
            logging.info("   ⚠️  No SO Flag data available in BOALF")
            df_flags = pd.DataFrame()
            
    except Exception as e:
        logging.warning(f"   ⚠️  Could not query SO Flags: {e}")
        df_flags = pd.DataFrame()
    
    # Step 6: Update Google Sheets
    logging.info("\n📊 Step 6: Updating Google Sheets...")
    
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
        ['💰 BM ACTUAL REVENUE - ACCEPTED ACTIONS WITH SO FLAGS'],
        [f'Updated: {date_str}', '', '', 'Period: Last 30 days', '', 'Definite Revenue Only'],
        [''],
        ['📊 DAILY ACCEPTED REVENUE BY TECHNOLOGY'],
        ['Date', 'Technology', 'Direction', 'Acceptances', 'MWh Accepted', 
         'Revenue (£)', '£/MWh', 'Unique BMUs']
    ]
    
    for _, row in df_accepted.head(500).iterrows():
        sheet_data.append([
            row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else '',
            row['fuelType'] or 'Unknown',
            row['_direction'],
            int(row['acceptance_count']) if pd.notna(row['acceptance_count']) else 0,
            f"{row['total_mwh']:.1f}" if pd.notna(row['total_mwh']) else '0',
            f"{row['total_revenue_gbp']:.2f}" if pd.notna(row['total_revenue_gbp']) else '0',
            f"{row['avg_price_per_mwh']:.2f}" if pd.notna(row['avg_price_per_mwh']) else '0',
            int(row['unique_bmus']) if pd.notna(row['unique_bmus']) else 0
        ])
    
    # Add SO Flag analysis if available
    if not df_flags.empty:
        current_row = len(sheet_data) + 2
        sheet_data.append([''])
        sheet_data.append(['📊 SO FLAG DISTRIBUTION (System Operator Action Reasons)'])
        sheet_data.append(['SO Flag', 'Acceptance Count', 'Unique BMUs', 'Description'])
        
        # SO Flag descriptions
        flag_descriptions = {
            'T': 'True - Energy balancing action',
            'F': 'False - System action (constraints, etc)',
            'NIL': 'No flag set',
            None: 'Unknown/NULL'
        }
        
        total_count = sum(row['count'] for _, row in df_flags.iterrows())
        
        for _, row in df_flags.iterrows():
            flag = row['soFlag'] if pd.notna(row['soFlag']) else None
            description = flag_descriptions.get(flag, 'Other')
            count = int(row['count']) if pd.notna(row['count']) else 0
            percentage = (count / total_count * 100) if total_count > 0 else 0
            
            sheet_data.append([
                str(flag) if flag is not None else 'NULL',
                f"{count:,} ({percentage:.1f}%)",
                int(row['unique_bmus']) if pd.notna(row['unique_bmus']) else 0,
                description
            ])
    
    # Add summary section
    sheet_data.append([''])
    sheet_data.append(['📊 TECHNOLOGY SUMMARY (Last 30 days)'])
    sheet_data.append(['Technology', 'Direction', 'Total Acceptances', 'Total MWh', 
                       'Total Revenue (£)', 'Avg £/MWh', 'BMUs'])
    
    for (tech, direction), row in tech_summary.iterrows():
        sheet_data.append([
            tech or 'Unknown',
            direction,
            int(row['acceptance_count']) if pd.notna(row['acceptance_count']) else 0,
            f"{row['total_mwh']:.1f}" if pd.notna(row['total_mwh']) else '0',
            f"{row['total_revenue_gbp']:.2f}" if pd.notna(row['total_revenue_gbp']) else '0',
            f"{row['avg_price_per_mwh']:.2f}" if pd.notna(row['avg_price_per_mwh']) else '0',
            int(row['unique_bmus']) if pd.notna(row['unique_bmus']) else 0
        ])
    
    # Update sheet
    worksheet.update(range_name='A1', values=sheet_data)
    
    # Format headers
    worksheet.format('A1:H1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 14}
    })
    
    worksheet.format('A5:H5', {
        'backgroundColor': {'red': 0.4, 'green': 0.4, 'blue': 0.4},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
    })
    
    # Number formatting
    worksheet.format('E6:F1000', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'}})
    worksheet.format('F6:F1000', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0.00'}})
    worksheet.format('G6:G1000', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0.00'}})
    
    logging.info(f"   ✅ Updated 'BM Accepted Revenue - SO Flags' with {len(df_accepted.head(500))} records")
    logging.info(f"   🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    
    # Step 7: Summary
    logging.info("\n" + "="*80)
    logging.info("✅ BM ACCEPTED REVENUE ANALYSIS COMPLETE")
    logging.info("="*80)
    
    total_acceptances = df_accepted['acceptance_count'].sum()
    total_mwh = df_accepted['total_mwh'].sum()
    total_revenue = df_accepted['total_revenue_gbp'].sum()
    avg_price = total_revenue / total_mwh if total_mwh > 0 else 0
    
    logging.info(f"\nActual Accepted Revenue (Last 30 days):")
    logging.info(f"  • Total acceptances: {total_acceptances:,.0f}")
    logging.info(f"  • Total volume accepted: {total_mwh:,.0f} MWh")
    logging.info(f"  • Total revenue paid: £{total_revenue:,.0f}")
    logging.info(f"  • Average price: £{avg_price:.2f}/MWh")
    
    if not df_flags.empty:
        logging.info(f"\nSO Flag Breakdown:")
        for _, row in df_flags.iterrows():
            flag = row['soFlag'] if pd.notna(row['soFlag']) else 'NULL'
            pct = (row['count'] / df_flags['count'].sum() * 100) if df_flags['count'].sum() > 0 else 0
            logging.info(f"  • {flag}: {row['count']:,.0f} acceptances ({pct:.1f}%)")
    
    return df_accepted, df_flags, tech_summary

if __name__ == "__main__":
    try:
        df_accepted, df_flags, tech_summary = analyze_accepted_revenue_with_flags()
    except Exception as e:
        logging.error(f"❌ Error: {e}", exc_info=True)
        raise
