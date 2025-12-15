#!/usr/bin/env python3
"""
SO Flag Trend Analysis - Multi-Period Comparison

Analyzes how the split between energy balancing vs system/constraint actions
has changed over different time periods.

Author: Generated for GB Power Market Analysis
Date: 2025-12-15
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

def analyze_period(client, period_name, days):
    """Analyze SO flags for a specific period"""
    
    if days == 0:
        start_date = '2022-01-01'
        date_filter = ''
    else:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        date_filter = f"WHERE CAST(settlementDate AS DATE) >= '{start_date}'"
    
    query = f"""
    WITH combined_boalf AS (
      SELECT 
        soFlag,
        levelFrom,
        levelTo,
        CAST(timeFrom AS TIMESTAMP) as timeFrom,
        CAST(timeTo AS TIMESTAMP) as timeTo
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf` 
      {date_filter}
      
      UNION ALL
      
      SELECT 
        soFlag,
        levelFrom,
        levelTo,
        CAST(timeFrom AS TIMESTAMP) as timeFrom,
        CAST(timeTo AS TIMESTAMP) as timeTo
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris` 
      {date_filter}
    )
    SELECT
      soFlag,
      COUNT(*) AS acceptance_count,
      SUM(
        ABS( (CAST(levelFrom AS FLOAT64) + CAST(levelTo AS FLOAT64)) / 2.0 )
        * (TIMESTAMP_DIFF(timeTo, timeFrom, SECOND) / 3600.0)
      ) AS total_mwh_proxy
    FROM combined_boalf
    GROUP BY soFlag
    """
    
    df = client.query(query).to_dataframe()
    
    total_count = df['acceptance_count'].sum()
    total_mwh = df['total_mwh_proxy'].sum()
    
    energy_count = df[df['soFlag'] == True]['acceptance_count'].sum() if True in df['soFlag'].values else 0
    system_count = df[df['soFlag'] == False]['acceptance_count'].sum() if False in df['soFlag'].values else 0
    
    energy_mwh = df[df['soFlag'] == True]['total_mwh_proxy'].sum() if True in df['soFlag'].values else 0
    system_mwh = df[df['soFlag'] == False]['total_mwh_proxy'].sum() if False in df['soFlag'].values else 0
    
    return {
        'period': period_name,
        'start_date': start_date,
        'days': days if days > 0 else 'All',
        'total_acceptances': int(total_count),
        'energy_count': int(energy_count),
        'system_count': int(system_count),
        'energy_pct': (energy_count / total_count * 100) if total_count > 0 else 0,
        'system_pct': (system_count / total_count * 100) if total_count > 0 else 0,
        'total_mwh': float(total_mwh),
        'energy_mwh': float(energy_mwh),
        'system_mwh': float(system_mwh),
        'energy_mwh_pct': (energy_mwh / total_mwh * 100) if total_mwh > 0 else 0,
        'system_mwh_pct': (system_mwh / total_mwh * 100) if total_mwh > 0 else 0
    }

def main():
    """Main analysis function"""
    
    logging.info("=" * 80)
    logging.info("📊 SO FLAG TREND ANALYSIS - MULTI-PERIOD COMPARISON")
    logging.info("=" * 80)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Define analysis periods
    periods = [
        ('Last 30 days', 30),
        ('Last 90 days', 90),
        ('Last 180 days', 180),
        ('Last 1 year', 365),
        ('Last 2 years', 730),
        ('All data (Jan 2022+)', 0)
    ]
    
    results = []
    
    logging.info("\nAnalyzing SO flag distribution across different time periods...\n")
    
    for period_name, days in periods:
        logging.info(f"Processing: {period_name}...")
        result = analyze_period(client, period_name, days)
        results.append(result)
        
        logging.info(f"  Total: {result['total_acceptances']:>12,} acceptances")
        logging.info(f"  Energy: {result['energy_count']:>11,} ({result['energy_pct']:>5.1f}%)")
        logging.info(f"  System: {result['system_count']:>11,} ({result['system_pct']:>5.1f}%)")
        logging.info(f"  MWh Energy: {result['energy_mwh']:>12,.0f} ({result['energy_mwh_pct']:>5.1f}%)")
        logging.info(f"  MWh System: {result['system_mwh']:>12,.0f} ({result['system_mwh_pct']:>5.1f}%)\n")
    
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # ============================================================================
    # UPDATE GOOGLE SHEETS
    # ============================================================================
    
    logging.info("📊 Updating Google Sheets...")
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    
    # Create or update sheet
    try:
        worksheet = spreadsheet.worksheet("SO Flag Trend Analysis")
        worksheet.clear()
    except:
        worksheet = spreadsheet.add_worksheet("SO Flag Trend Analysis", rows=100, cols=15)
    
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    sheet_data = [
        ['📊 SO FLAG TREND ANALYSIS - ENERGY vs SYSTEM/CONSTRAINT ACTIONS'],
        [f'Updated: {date_str}', '', '', 'Combined BOALF (historical + IRIS streaming)'],
        [''],
        ['🔍 KEY INSIGHT'],
        ['Period', 'Energy Balancing %', 'System/Constraint %', 'Interpretation'],
        ['Last 30 days', f"{df_results.iloc[0]['energy_pct']:.1f}%", f"{df_results.iloc[0]['system_pct']:.1f}%", 'Recent trend'],
        ['Last 1 year', f"{df_results.iloc[3]['energy_pct']:.1f}%", f"{df_results.iloc[3]['system_pct']:.1f}%", 'Annual pattern'],
        ['All data', f"{df_results.iloc[-1]['energy_pct']:.1f}%", f"{df_results.iloc[-1]['system_pct']:.1f}%", 'Historical baseline'],
        [''],
        ['📈 DETAILED BREAKDOWN BY PERIOD'],
        ['Period', 'Start Date', 'Total Acceptances', 'Energy Count', 'Energy %', 'System Count', 'System %', 'Energy MWh', 'System MWh']
    ]
    
    for _, row in df_results.iterrows():
        sheet_data.append([
            row['period'],
            row['start_date'],
            f"{row['total_acceptances']:,}",
            f"{row['energy_count']:,}",
            f"{row['energy_pct']:.1f}%",
            f"{row['system_count']:,}",
            f"{row['system_pct']:.1f}%",
            f"{row['energy_mwh']:,.0f}",
            f"{row['system_mwh']:,.0f}"
        ])
    
    # Add interpretation
    sheet_data.append([''])
    sheet_data.append(['📝 INTERPRETATION'])
    sheet_data.append(['Metric', 'Description'])
    sheet_data.append(['SO Flag = True', 'Energy balancing - System short of energy, generators instructed to increase output'])
    sheet_data.append(['SO Flag = False', 'System action - Constraint management, grid security, or instructed to reduce output'])
    sheet_data.append(['Trend', f"Energy actions: {df_results.iloc[-1]['energy_pct']:.1f}% overall, but only {df_results.iloc[0]['energy_pct']:.1f}% in last 30 days"])
    sheet_data.append(['Implication', '~80-84% of BM actions are for system management, not energy shortfall'])
    
    # Add trend analysis
    sheet_data.append([''])
    sheet_data.append(['📉 TREND OVER TIME'])
    sheet_data.append(['Observation', 'Finding'])
    
    # Compare recent vs historical
    recent_energy = df_results.iloc[0]['energy_pct']
    historical_energy = df_results.iloc[-1]['energy_pct']
    trend = recent_energy - historical_energy
    
    if trend < -2:
        sheet_data.append(['Recent trend', f'Energy balancing DOWN by {abs(trend):.1f}pp - more system actions'])
    elif trend > 2:
        sheet_data.append(['Recent trend', f'Energy balancing UP by {trend:.1f}pp - less system actions'])
    else:
        sheet_data.append(['Recent trend', 'Stable - consistent with historical pattern'])
    
    sheet_data.append(['MWh weighted', f"Energy actions: {df_results.iloc[-1]['energy_mwh_pct']:.1f}% of total MWh (larger actions)"])
    
    # Update sheet
    worksheet.update(range_name='A1', values=sheet_data)
    
    # Format headers
    worksheet.format('A1:I1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 14}
    })
    
    worksheet.format('A5:D5', {
        'backgroundColor': {'red': 0.3, 'green': 0.3, 'blue': 0.3},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
    })
    
    worksheet.format('A10:I10', {
        'backgroundColor': {'red': 0.3, 'green': 0.3, 'blue': 0.3},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
    })
    
    logging.info(f"   ✅ Updated 'SO Flag Trend Analysis' sheet")
    logging.info(f"   🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    
    logging.info("\n" + "=" * 80)
    logging.info("✅ SO FLAG TREND ANALYSIS COMPLETE")
    logging.info("=" * 80)
    
    logging.info("\nKEY FINDINGS:")
    logging.info(f"  • All time (Jan 2022 - present): {df_results.iloc[-1]['energy_pct']:.1f}% energy, {df_results.iloc[-1]['system_pct']:.1f}% system")
    logging.info(f"  • Last year: {df_results.iloc[3]['energy_pct']:.1f}% energy, {df_results.iloc[3]['system_pct']:.1f}% system")
    logging.info(f"  • Last 30 days: {df_results.iloc[0]['energy_pct']:.1f}% energy, {df_results.iloc[0]['system_pct']:.1f}% system")
    logging.info(f"\n  ➡️  Conclusion: {df_results.iloc[-1]['system_pct']:.0f}% of BM actions are for system/constraint management")

if __name__ == "__main__":
    main()
