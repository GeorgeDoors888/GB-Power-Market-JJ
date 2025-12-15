#!/usr/bin/env python3
"""
BMU Capacity Market Analysis
Analyzes all BMUs for capacity market eligibility and potential revenue
Uses BOAV data + BMU metadata to calculate CM revenue by technology
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

# Capacity Market clearing prices (£/kW/year) - historical actuals
CM_CLEARING_PRICES = {
    '2024-25': 45.00,   # T-1 2024
    '2025-26': 63.00,   # T-4 2021 delivery 2025
    'Average': 54.00    # Conservative estimate
}

# De-rating factors by technology (% of registered capacity eligible for CM)
# Source: National Grid ESO Capacity Market rules
DERATING_FACTORS = {
    'WIND': 0.088,      # 8.8% (offshore wind)
    'CCGT': 0.93,       # 93% (gas turbines)
    'OCGT': 0.94,       # 94% (open cycle gas)
    'COAL': 0.90,       # 90% (coal plants)
    'NUCLEAR': 0.85,    # 85% (nuclear)
    'BIOMASS': 0.90,    # 90% (biomass)
    'NPSHYD': 0.24,     # 24% (pumped storage)
    'PS': 0.24,         # 24% (pumped storage)
    'BATTERY': 0.46,    # 46% (1-2hr batteries)
    'BATTERY_4H': 0.96, # 96% (4hr+ batteries)
    'OIL': 0.94,        # 94% (oil turbines)
    'OTHER': 0.50       # 50% (unknown/mixed)
}

# CM participation eligibility criteria
MIN_CAPACITY_MW = 2.0  # Minimum 2 MW to participate
CM_DURATION_REQUIRED = 4  # Hours (for full de-rating)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def analyze_capacity_market():
    """Analyze all BMUs for capacity market eligibility and revenue"""
    
    logging.info("="*80)
    logging.info("🔋 CAPACITY MARKET ANALYSIS - ALL BMUs")
    logging.info("="*80)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Step 1: Get all BMUs with inferred capacity from BM participation
    logging.info("📊 Step 1: Fetching BMU data and inferring capacity from BM volumes...")
    
    query = """
    WITH bmu_activity AS (
        SELECT 
            boav.nationalGridBmUnit,
            COUNT(DISTINCT DATE(CAST(boav.settlementDate AS STRING))) as active_days,
            COUNT(DISTINCT boav.settlementPeriod) as active_sps,
            SUM(CASE WHEN boav._direction = 'offer' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) as total_offer_mwh,
            SUM(CASE WHEN boav._direction = 'bid' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) as total_bid_mwh,
            -- Infer capacity from peak accepted volume (MW = MWh / 0.5h per settlement period)
            MAX(CASE WHEN boav._direction = 'offer' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) * 2 as peak_offer_mw,
            MAX(CASE WHEN boav._direction = 'bid' THEN ABS(boav.totalVolumeAccepted) ELSE 0 END) * 2 as peak_bid_mw
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav` boav
        GROUP BY boav.nationalGridBmUnit
    ),
    bmu_with_meta AS (
        SELECT 
            COALESCE(meta.nationalGridBmUnit, activity.nationalGridBmUnit) as nationalGridBmUnit,
            meta.fuelType,
            meta.bmUnitType,
            activity.active_days,
            activity.active_sps,
            activity.total_offer_mwh,
            activity.total_bid_mwh,
            activity.peak_offer_mw,
            activity.peak_bid_mw,
            -- Use peak from either offer or bid direction as capacity estimate
            GREATEST(
                COALESCE(activity.peak_offer_mw, 0),
                COALESCE(activity.peak_bid_mw, 0),
                2.0  -- Minimum to be eligible for CM
            ) as inferred_capacity_mw
        FROM bmu_activity activity
        LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_metadata` meta
            ON activity.nationalGridBmUnit = meta.nationalGridBmUnit
    )
    SELECT 
        nationalGridBmUnit,
        fuelType,
        inferred_capacity_mw as capacity_mw,
        bmUnitType,
        active_days,
        active_sps,
        total_offer_mwh,
        total_bid_mwh,
        peak_offer_mw,
        peak_bid_mw,
        CASE 
            WHEN inferred_capacity_mw >= 2.0 THEN 'ELIGIBLE'
            WHEN inferred_capacity_mw > 0 AND inferred_capacity_mw < 2.0 THEN 'TOO_SMALL'
            ELSE 'NO_CAPACITY_DATA'
        END as cm_eligibility
    FROM bmu_with_meta
    WHERE nationalGridBmUnit IS NOT NULL
    ORDER BY inferred_capacity_mw DESC
    """
    
    df = client.query(query).to_dataframe()
    logging.info(f"   ✅ Retrieved {len(df)} BMUs")
    
    # Step 2: Calculate CM revenue for each BMU
    logging.info("📊 Step 2: Calculating capacity market revenue...")
    
    # Apply de-rating factors
    df['derating_factor'] = df['fuelType'].apply(
        lambda x: DERATING_FACTORS.get(x, DERATING_FACTORS['OTHER'])
    )
    
    # Calculate de-rated capacity (MW)
    df['derated_capacity_mw'] = df['capacity_mw'] * df['derating_factor']
    
    # Calculate annual CM revenue (£/year)
    cm_price = CM_CLEARING_PRICES['Average']  # £54/kW/year
    df['cm_revenue_annual'] = df['derated_capacity_mw'] * 1000 * cm_price  # Convert MW to kW
    
    # Calculate monthly CM revenue
    df['cm_revenue_monthly'] = df['cm_revenue_annual'] / 12
    
    # Calculate revenue per MW-day
    df['cm_revenue_per_mw_day'] = df['cm_revenue_annual'] / (df['capacity_mw'] * 365)
    
    # Filter to eligible BMUs only
    df_eligible = df[df['cm_eligibility'] == 'ELIGIBLE'].copy()
    
    logging.info(f"   ✅ {len(df_eligible)} BMUs eligible for CM (>= 2 MW)")
    logging.info(f"   ⚠️  {len(df[df['cm_eligibility'] == 'TOO_SMALL'])} BMUs too small (< 2 MW)")
    logging.info(f"   ⚠️  {len(df[df['cm_eligibility'] == 'NO_CAPACITY_DATA'])} BMUs missing capacity data")
    
    # Step 3: Technology summary
    logging.info("📊 Step 3: Capacity Market by Technology...")
    
    tech_summary = df_eligible.groupby('fuelType').agg({
        'nationalGridBmUnit': 'count',
        'capacity_mw': 'sum',
        'derated_capacity_mw': 'sum',
        'cm_revenue_annual': 'sum',
        'derating_factor': 'mean'
    }).sort_values('cm_revenue_annual', ascending=False)
    
    logging.info("\n   Technology Summary:")
    logging.info(f"   {'Technology':<15} {'BMUs':>6} {'Capacity':>10} {'De-rated':>10} {'CM Revenue/yr':>15} {'De-rating'}")
    for tech, row in tech_summary.iterrows():
        logging.info(f"   {tech:<15} {row['nationalGridBmUnit']:>6.0f} {row['capacity_mw']:>9.1f} MW {row['derated_capacity_mw']:>9.1f} MW £{row['cm_revenue_annual']:>13,.0f}  {row['derating_factor']*100:>5.1f}%")
    
    # Step 4: Market totals
    total_capacity = df_eligible['capacity_mw'].sum()
    total_derated = df_eligible['derated_capacity_mw'].sum()
    total_revenue = df_eligible['cm_revenue_annual'].sum()
    
    logging.info(f"\n   📊 Market Totals:")
    logging.info(f"      Total BMUs:           {len(df_eligible):,}")
    logging.info(f"      Total Capacity:       {total_capacity:,.1f} MW")
    logging.info(f"      Total De-rated:       {total_derated:,.1f} MW")
    logging.info(f"      Total CM Revenue:     £{total_revenue:,.0f}/year")
    logging.info(f"      Avg De-rating:        {(total_derated/total_capacity)*100:.1f}%")
    
    # Step 5: Top BMUs by CM revenue
    logging.info("\n📊 Step 5: Top 20 BMUs by Capacity Market Revenue...")
    
    top_20 = df_eligible.nlargest(20, 'cm_revenue_annual')
    
    logging.info(f"\n   {'BMU ID':<12} {'Technology':<10} {'Capacity':>10} {'De-rated':>10} {'CM Revenue/yr':>15}")
    for _, row in top_20.iterrows():
        logging.info(f"   {row['nationalGridBmUnit']:<12} {row['fuelType']:<10} {row['capacity_mw']:>9.1f} MW {row['derated_capacity_mw']:>9.1f} MW £{row['cm_revenue_annual']:>13,.0f}")
    
    # Step 6: Update Google Sheets
    logging.info("\n📊 Step 6: Updating Google Sheets...")
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    
    # Create or update "Capacity Market Analysis" sheet
    try:
        worksheet = spreadsheet.worksheet("Capacity Market Analysis")
        worksheet.clear()
    except:
        worksheet = spreadsheet.add_worksheet("Capacity Market Analysis", rows=1000, cols=20)
    
    # Prepare sheet data
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    sheet_data = [
        ['🔋 CAPACITY MARKET ANALYSIS - ALL BMUs'],
        [f'Updated: {date_str}', '', '', '', f'Clearing Price: £{cm_price}/kW/year'],
        [f'{len(df_eligible):,} Eligible BMUs', '', '', '', f'Total Revenue: £{total_revenue:,.0f}/year'],
        [''],
        ['BMU ID', 'Technology', 'Capacity (MW)', 'De-rated (MW)', 'De-rating %', 
         'CM Revenue (£/year)', 'CM Revenue (£/month)', '£/MW-day', 'Active Days', 'Eligibility']
    ]
    
    # Add data rows (top 200 BMUs)
    for _, row in df.nlargest(200, 'cm_revenue_annual').iterrows():
        sheet_data.append([
            row['nationalGridBmUnit'],
            row['fuelType'] or 'Unknown',
            f"{row['capacity_mw']:.1f}" if pd.notna(row['capacity_mw']) else 'N/A',
            f"{row['derated_capacity_mw']:.1f}" if pd.notna(row['derated_capacity_mw']) else 'N/A',
            f"{row['derating_factor']*100:.1f}%" if pd.notna(row['derating_factor']) else 'N/A',
            f"{row['cm_revenue_annual']:.0f}" if pd.notna(row['cm_revenue_annual']) else '0',
            f"{row['cm_revenue_monthly']:.0f}" if pd.notna(row['cm_revenue_monthly']) else '0',
            f"{row['cm_revenue_per_mw_day']:.2f}" if pd.notna(row['cm_revenue_per_mw_day']) and row['capacity_mw'] > 0 else 'N/A',
            int(row['active_days']) if pd.notna(row['active_days']) else 0,
            row['cm_eligibility']
        ])
    
    # Add technology summary section
    sheet_data.append([''])
    sheet_data.append(['📊 TECHNOLOGY SUMMARY'])
    sheet_data.append(['Technology', 'BMU Count', 'Total Capacity (MW)', 'Total De-rated (MW)', 
                       'Total CM Revenue (£/year)', 'Avg De-rating %'])
    
    for tech, row in tech_summary.iterrows():
        sheet_data.append([
            tech or 'Unknown',
            int(row['nationalGridBmUnit']),
            f"{row['capacity_mw']:.1f}",
            f"{row['derated_capacity_mw']:.1f}",
            f"{row['cm_revenue_annual']:.0f}",
            f"{row['derating_factor']*100:.1f}%"
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
    
    # Number formatting
    worksheet.format('C6:D300', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.0'}})
    worksheet.format('F6:G300', {'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0'}})
    worksheet.format('H6:H300', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'}})
    
    logging.info(f"   ✅ Updated 'Capacity Market Analysis' with {len(df.nlargest(200, 'cm_revenue_annual'))} BMUs")
    logging.info(f"   🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    
    # Step 7: Summary
    logging.info("\n" + "="*80)
    logging.info("✅ CAPACITY MARKET ANALYSIS COMPLETE")
    logging.info("="*80)
    logging.info(f"\nKey Findings:")
    logging.info(f"  • {len(df_eligible):,} BMUs eligible for Capacity Market")
    logging.info(f"  • Total eligible capacity: {total_capacity:,.1f} MW")
    logging.info(f"  • Total de-rated capacity: {total_derated:,.1f} MW")
    logging.info(f"  • Total annual CM revenue: £{total_revenue:,.0f}")
    if len(tech_summary) > 0:
        logging.info(f"  • Top technology: {tech_summary.index[0]} (£{tech_summary.iloc[0]['cm_revenue_annual']:,.0f}/year)")
    
    return df_eligible, tech_summary

if __name__ == "__main__":
    try:
        df_eligible, tech_summary = analyze_capacity_market()
    except Exception as e:
        logging.error(f"❌ Error: {e}", exc_info=True)
        raise
