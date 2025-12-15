#!/usr/bin/env python3
"""
BMU Capacity Market Revenue Over Time
Analyzes CM revenue by settlement period to understand revenue patterns
when BMUs turn up/down in response to demand/price signals
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

# CM clearing price (£/kW/year)
CM_PRICE = 54.00

# De-rating factors by technology
DERATING_FACTORS = {
    'WIND': 0.088, 'CCGT': 0.93, 'OCGT': 0.94, 'COAL': 0.90,
    'NUCLEAR': 0.85, 'BIOMASS': 0.90, 'NPSHYD': 0.24, 'PS': 0.24,
    'OIL': 0.94, 'OTHER': 0.50
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def analyze_cm_revenue_timeline():
    """Analyze CM revenue patterns over time and by settlement period"""
    
    logging.info("="*80)
    logging.info("🔋 CAPACITY MARKET REVENUE - TIME SERIES ANALYSIS")
    logging.info("="*80)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Step 1: Daily CM revenue potential by technology
    logging.info("📊 Step 1: Calculating daily CM revenue by technology...")
    
    daily_query = """
    WITH daily_bmu_activity AS (
        SELECT 
            DATE(CAST(boav.settlementDate AS STRING)) as date,
            meta.fuelType,
            boav.nationalGridBmUnit,
            -- Infer capacity from peak volume that day
            MAX(CASE WHEN boav._direction = 'offer' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) * 2 as peak_offer_mw,
            MAX(CASE WHEN boav._direction = 'bid' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) * 2 as peak_bid_mw,
            -- Count activations
            SUM(CASE WHEN boav._direction = 'offer' AND ABS(boav.totalVolumeAccepted) > 0 THEN 1 ELSE 0 END) as offer_activations,
            SUM(CASE WHEN boav._direction = 'bid' AND ABS(boav.totalVolumeAccepted) > 0 THEN 1 ELSE 0 END) as bid_activations,
            -- Total volumes
            SUM(CASE WHEN boav._direction = 'offer' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) as total_offer_mwh,
            SUM(CASE WHEN boav._direction = 'bid' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) as total_bid_mwh
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav` boav
        LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_metadata` meta
            ON boav.nationalGridBmUnit = meta.nationalGridBmUnit
        WHERE DATE(CAST(boav.settlementDate AS STRING)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY date, meta.fuelType, boav.nationalGridBmUnit
    ),
    daily_tech_summary AS (
        SELECT 
            date,
            fuelType,
            COUNT(DISTINCT nationalGridBmUnit) as active_bmus,
            SUM(GREATEST(peak_offer_mw, peak_bid_mw)) as total_capacity_mw,
            SUM(offer_activations) as total_offer_activations,
            SUM(bid_activations) as total_bid_activations,
            SUM(total_offer_mwh) as total_offer_mwh,
            SUM(total_bid_mwh) as total_bid_mwh
        FROM daily_bmu_activity
        GROUP BY date, fuelType
    )
    SELECT 
        date,
        fuelType,
        active_bmus,
        total_capacity_mw,
        total_offer_activations,
        total_bid_activations,
        total_offer_mwh,
        total_bid_mwh
    FROM daily_tech_summary
    ORDER BY date DESC, total_capacity_mw DESC
    """
    
    df_daily = client.query(daily_query).to_dataframe()
    logging.info(f"   ✅ Retrieved {len(df_daily)} daily technology records")
    
    # Apply de-rating and calculate CM revenue
    df_daily['derating_factor'] = df_daily['fuelType'].apply(
        lambda x: DERATING_FACTORS.get(x, DERATING_FACTORS['OTHER'])
    )
    df_daily['derated_capacity_mw'] = df_daily['total_capacity_mw'] * df_daily['derating_factor']
    df_daily['cm_revenue_daily'] = df_daily['derated_capacity_mw'] * 1000 * CM_PRICE / 365
    
    # Step 2: Settlement period patterns (intraday revenue timing)
    logging.info("📊 Step 2: Analyzing settlement period patterns...")
    
    sp_query = """
    WITH sp_activity AS (
        SELECT 
            boav.settlementPeriod,
            meta.fuelType,
            COUNT(DISTINCT boav.nationalGridBmUnit) as active_bmus,
            COUNT(DISTINCT DATE(CAST(boav.settlementDate AS STRING))) as days_active,
            -- Offer = turn up generation
            SUM(CASE WHEN boav._direction = 'offer' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) as total_offer_mwh,
            COUNT(CASE WHEN boav._direction = 'offer' AND ABS(boav.totalVolumeAccepted) > 0 THEN 1 END) as offer_count,
            -- Bid = turn down generation
            SUM(CASE WHEN boav._direction = 'bid' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) as total_bid_mwh,
            COUNT(CASE WHEN boav._direction = 'bid' AND ABS(boav.totalVolumeAccepted) > 0 THEN 1 END) as bid_count,
            -- Peak capacity per SP
            AVG(CASE WHEN boav._direction = 'offer' THEN ABS(boav.totalVolumeAccepted) * 2 ELSE 0 END) as avg_offer_mw,
            AVG(CASE WHEN boav._direction = 'bid' THEN ABS(boav.totalVolumeAccepted) * 2 ELSE 0 END) as avg_bid_mw
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav` boav
        LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_metadata` meta
            ON boav.nationalGridBmUnit = meta.nationalGridBmUnit
        WHERE DATE(CAST(boav.settlementDate AS STRING)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY boav.settlementPeriod, meta.fuelType
    )
    SELECT 
        settlementPeriod,
        fuelType,
        active_bmus,
        days_active,
        total_offer_mwh,
        offer_count,
        total_bid_mwh,
        bid_count,
        avg_offer_mw,
        avg_bid_mw
    FROM sp_activity
    ORDER BY settlementPeriod, fuelType
    """
    
    df_sp = client.query(sp_query).to_dataframe()
    logging.info(f"   ✅ Retrieved {len(df_sp)} settlement period records")
    
    # Calculate average CM-eligible capacity by SP
    df_sp['derating_factor'] = df_sp['fuelType'].apply(
        lambda x: DERATING_FACTORS.get(x, DERATING_FACTORS['OTHER'])
    )
    df_sp['avg_capacity_mw'] = df_sp[['avg_offer_mw', 'avg_bid_mw']].max(axis=1)
    df_sp['avg_derated_mw'] = df_sp['avg_capacity_mw'] * df_sp['derating_factor']
    df_sp['cm_revenue_per_sp'] = df_sp['avg_derated_mw'] * 1000 * CM_PRICE / (365 * 48)
    
    # Step 3: Technology summary
    logging.info("📊 Step 3: Summarizing by technology...")
    
    tech_summary = df_daily.groupby('fuelType').agg({
        'active_bmus': 'mean',
        'total_capacity_mw': 'mean',
        'derated_capacity_mw': 'mean',
        'cm_revenue_daily': 'mean',
        'total_offer_activations': 'sum',
        'total_bid_activations': 'sum',
        'total_offer_mwh': 'sum',
        'total_bid_mwh': 'sum'
    }).sort_values('cm_revenue_daily', ascending=False)
    
    logging.info("\n   Average Daily CM Revenue by Technology:")
    for tech, row in tech_summary.iterrows():
        logging.info(f"   {tech:<15} £{row['cm_revenue_daily']:>12,.0f}/day  "
                    f"({row['active_bmus']:>5.0f} BMUs, {row['total_capacity_mw']:>8,.0f} MW)")
    
    # Step 4: Peak demand periods (identify when BMUs turn up most)
    logging.info("\n📊 Step 4: Identifying peak demand periods...")
    
    sp_totals = df_sp.groupby('settlementPeriod').agg({
        'total_offer_mwh': 'sum',
        'total_bid_mwh': 'sum',
        'offer_count': 'sum',
        'bid_count': 'sum',
        'avg_derated_mw': 'sum',
        'cm_revenue_per_sp': 'sum'
    })
    
    # Add time labels
    sp_totals['time'] = sp_totals.index.map(lambda sp: f"{(sp-1)//2:02d}:{30 if sp%2==0 else '00'}")
    sp_totals['net_direction'] = sp_totals['total_offer_mwh'] - sp_totals['total_bid_mwh']
    
    logging.info("\n   Top 10 Settlement Periods by Offer Volume (Turn Up Generation):")
    top_offer = sp_totals.nlargest(10, 'total_offer_mwh')
    for sp, row in top_offer.iterrows():
        logging.info(f"   SP{sp:2d} ({row['time']}) - {row['total_offer_mwh']:>10,.0f} MWh turned up, "
                    f"£{row['cm_revenue_per_sp']:>8,.0f} CM revenue")
    
    logging.info("\n   Top 10 Settlement Periods by Bid Volume (Turn Down Generation):")
    top_bid = sp_totals.nlargest(10, 'total_bid_mwh')
    for sp, row in top_bid.iterrows():
        logging.info(f"   SP{sp:2d} ({row['time']}) - {row['total_bid_mwh']:>10,.0f} MWh turned down, "
                    f"£{row['cm_revenue_per_sp']:>8,.0f} CM revenue")
    
    # Step 5: Update Google Sheets with time series
    logging.info("\n📊 Step 5: Updating Google Sheets...")
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    
    # Create or update sheet
    try:
        worksheet = spreadsheet.worksheet("CM Revenue Timeline")
        worksheet.clear()
    except:
        worksheet = spreadsheet.add_worksheet("CM Revenue Timeline", rows=2000, cols=20)
    
    # Prepare daily data
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    sheet_data = [
        ['🔋 CAPACITY MARKET REVENUE - TIME SERIES ANALYSIS'],
        [f'Updated: {date_str}', '', '', 'Period: Last 90 days', '', 'Clearing: £54/kW/year'],
        [''],
        ['📊 DAILY REVENUE BY TECHNOLOGY'],
        ['Date', 'Technology', 'Active BMUs', 'Capacity (MW)', 'De-rated (MW)', 
         'CM Revenue (£/day)', 'Offer Acts', 'Bid Acts', 'Offer MWh', 'Bid MWh']
    ]
    
    for _, row in df_daily.head(500).iterrows():
        sheet_data.append([
            row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else '',
            row['fuelType'] or 'Unknown',
            int(row['active_bmus']) if pd.notna(row['active_bmus']) else 0,
            f"{row['total_capacity_mw']:.1f}" if pd.notna(row['total_capacity_mw']) else '0',
            f"{row['derated_capacity_mw']:.1f}" if pd.notna(row['derated_capacity_mw']) else '0',
            f"{row['cm_revenue_daily']:.0f}" if pd.notna(row['cm_revenue_daily']) else '0',
            int(row['total_offer_activations']) if pd.notna(row['total_offer_activations']) else 0,
            int(row['total_bid_activations']) if pd.notna(row['total_bid_activations']) else 0,
            f"{row['total_offer_mwh']:.1f}" if pd.notna(row['total_offer_mwh']) else '0',
            f"{row['total_bid_mwh']:.1f}" if pd.notna(row['total_bid_mwh']) else '0'
        ])
    
    # Add settlement period analysis
    current_row = len(sheet_data) + 2
    sheet_data.append([''])
    sheet_data.append(['📊 SETTLEMENT PERIOD PATTERNS (Last 90 days)'])
    sheet_data.append(['SP', 'Time', 'Technology', 'Active BMUs', 'Offer MWh', 'Bid MWh', 
                       'Net MWh', 'Avg CM MW', 'CM Revenue (£/SP)'])
    
    for _, row in df_sp.head(500).iterrows():
        sp = int(row['settlementPeriod'])
        time_str = f"{(sp-1)//2:02d}:{30 if sp%2==0 else '00'}"
        net_mwh = row['total_offer_mwh'] - row['total_bid_mwh']
        
        sheet_data.append([
            int(sp),
            time_str,
            row['fuelType'] or 'Unknown',
            int(row['active_bmus']) if pd.notna(row['active_bmus']) else 0,
            f"{row['total_offer_mwh']:.1f}" if pd.notna(row['total_offer_mwh']) else '0',
            f"{row['total_bid_mwh']:.1f}" if pd.notna(row['total_bid_mwh']) else '0',
            f"{net_mwh:.1f}" if pd.notna(net_mwh) else '0',
            f"{row['avg_derated_mw']:.1f}" if pd.notna(row['avg_derated_mw']) else '0',
            f"{row['cm_revenue_per_sp']:.2f}" if pd.notna(row['cm_revenue_per_sp']) else '0'
        ])
    
    # Update sheet
    worksheet.update(range_name='A1', values=sheet_data)
    
    # Format headers
    worksheet.format('A1:J1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 14}
    })
    
    worksheet.format('A5:J5', {
        'backgroundColor': {'red': 0.4, 'green': 0.4, 'blue': 0.4},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
    })
    
    sp_header_row = len(sheet_data) - len(df_sp.head(500)) - 1
    worksheet.format(f'A{sp_header_row}:I{sp_header_row}', {
        'backgroundColor': {'red': 0.4, 'green': 0.4, 'blue': 0.4},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
    })
    
    # Number formatting
    worksheet.format('D6:E1000', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.0'}})
    worksheet.format('F6:F1000', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'}})
    worksheet.format('I6:J1000', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.0'}})
    
    logging.info(f"   ✅ Updated 'CM Revenue Timeline' with {len(df_daily.head(500))} daily records")
    logging.info(f"   ✅ Added {len(df_sp.head(500))} settlement period records")
    logging.info(f"   🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    
    # Step 6: Summary
    logging.info("\n" + "="*80)
    logging.info("✅ CM REVENUE TIMELINE ANALYSIS COMPLETE")
    logging.info("="*80)
    
    total_daily_revenue = tech_summary['cm_revenue_daily'].sum()
    total_annual_revenue = total_daily_revenue * 365
    
    logging.info(f"\nKey Findings:")
    logging.info(f"  • Average daily CM revenue: £{total_daily_revenue:,.0f}")
    logging.info(f"  • Projected annual revenue: £{total_annual_revenue:,.0f}")
    logging.info(f"  • Top technology: {tech_summary.index[0]} (£{tech_summary.iloc[0]['cm_revenue_daily']:,.0f}/day)")
    logging.info(f"  • Peak offer period: SP{top_offer.index[0]} ({top_offer.iloc[0]['time']})")
    logging.info(f"  • Peak bid period: SP{top_bid.index[0]} ({top_bid.iloc[0]['time']})")
    
    return df_daily, df_sp, tech_summary

if __name__ == "__main__":
    try:
        df_daily, df_sp, tech_summary = analyze_cm_revenue_timeline()
    except Exception as e:
        logging.error(f"❌ Error: {e}", exc_info=True)
        raise
