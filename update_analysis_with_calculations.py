#!/usr/bin/env python3
"""
Enhanced Analysis BI Sheet with Advanced Calculations
Adds calculations from BOD analysis script including:
- Volume-weighted prices
- Wind curtailment metrics
- Balancing statistics
- Data quality scores
"""

import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from gspread_formatting import *

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SHEET_NAME = 'Analysis BI Enhanced'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET_ID = 'uk_energy_prod'

# Date range mapping
DATE_RANGES = {
    '1 Day': 1,
    '1 Week': 7,
    '1 Month': 30,
    '3 Months': 90,
    '6 Months': 180,
    '1 Year': 365
}

def get_credentials():
    """Load Google Sheets credentials"""
    with open('token.pickle', 'rb') as token:
        return pickle.load(token)

def get_date_range(sheet):
    """Get date range from dropdown"""
    quick_select = sheet.acell('B5').value
    if quick_select in DATE_RANGES:
        days = DATE_RANGES[quick_select]
        return days
    return 7  # default

def calculate_volume_weighted_price(df):
    """Calculate volume-weighted average price"""
    if df.empty or 'price' not in df.columns or 'volume' not in df.columns:
        return None
    
    df = df.dropna(subset=['price', 'volume'])
    if df.empty:
        return None
    
    # Volume-weighted average
    total_value = (df['price'] * df['volume'].abs()).sum()
    total_volume = df['volume'].abs().sum()
    
    if total_volume == 0:
        return None
    
    return total_value / total_volume

def calculate_wind_curtailment(bq_client, days):
    """
    Calculate wind curtailment proxy from BOD data
    NOTE: Your bmrs_bod has different schema (bid/offer pairs, not acceptances)
    Using bid values as proxy for curtailment
    """
    query = f"""
    SELECT
        COUNT(*) as bid_count,
        AVG(bid) as avg_bid_price,
        SUM(CASE WHEN bid > 0 THEN 1 ELSE 0 END) as positive_bids
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_bod`
    WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        AND bid IS NOT NULL
        AND bid > 0
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty or df['bid_count'].isna().all():
            return None, None, 0
        return (
            None,  # No volume data in this schema
            float(df['avg_bid_price'].iloc[0]) if not pd.isna(df['avg_bid_price'].iloc[0]) else 0,
            int(df['positive_bids'].iloc[0]) if not pd.isna(df['positive_bids'].iloc[0]) else 0
        )
    except Exception as e:
        print(f"  ⚠️  Wind curtailment calc failed: {e}")
        return None, None, 0

def calculate_balancing_statistics(bq_client, days):
    """Calculate balancing volume statistics using actual schema"""
    query = f"""
    SELECT
        COUNT(*) as total_records,
        AVG(bid) as avg_bid_price,
        AVG(offer) as avg_offer_price,
        SUM(CASE WHEN bid IS NOT NULL AND bid > 0 THEN 1 ELSE 0 END) as bid_count,
        SUM(CASE WHEN offer IS NOT NULL AND offer > 0 THEN 1 ELSE 0 END) as offer_count
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_bod`
    WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            return None
        
        row = df.iloc[0]
        stats = {
            'B': {  # Bids
                'volume': int(row['bid_count']) if not pd.isna(row['bid_count']) else 0,
                'avg_price': float(row['avg_bid_price']) if not pd.isna(row['avg_bid_price']) else 0,
                'count': int(row['bid_count']) if not pd.isna(row['bid_count']) else 0
            },
            'O': {  # Offers
                'volume': int(row['offer_count']) if not pd.isna(row['offer_count']) else 0,
                'avg_price': float(row['avg_offer_price']) if not pd.isna(row['avg_offer_price']) else 0,
                'count': int(row['offer_count']) if not pd.isna(row['offer_count']) else 0
            }
        }
        return stats
    except Exception as e:
        print(f"  ⚠️  Balancing stats calc failed: {e}")
        return None

def calculate_capacity_factors(gen_df):
    """Calculate capacity factors for each fuel type"""
    if gen_df.empty or 'fuelType' not in gen_df.columns:
        return {}
    
    # Assumed capacity by fuel type (MW) - rough estimates
    CAPACITIES = {
        'NUCLEAR': 9000,
        'CCGT': 30000,
        'COAL': 2000,
        'WIND': 25000,
        'SOLAR': 14000,
        'HYDRO': 2500,
        'BIOMASS': 5000,
        'OIL': 1000,
        'OCGT': 2000,
        'PS': 3000  # Pumped storage
    }
    
    # Group by fuel type
    grouped = gen_df.groupby('fuelType')['generation'].mean()
    
    capacity_factors = {}
    for fuel, avg_gen in grouped.items():
        fuel_upper = fuel.upper()
        if fuel_upper in CAPACITIES:
            capacity_mw = CAPACITIES[fuel_upper]
            # Capacity factor = actual generation / capacity
            cf = (avg_gen / capacity_mw) * 100 if capacity_mw > 0 else 0
            capacity_factors[fuel] = min(cf, 100)  # Cap at 100%
    
    return capacity_factors

def calculate_data_quality_score(df, required_cols):
    """Calculate data quality score based on NULL rates"""
    if df.empty:
        return 0.0
    
    null_scores = []
    for col in required_cols:
        if col in df.columns:
            null_rate = df[col].isna().sum() / len(df)
            # Score: 100% - null_rate
            score = (1 - null_rate) * 100
            null_scores.append(score)
    
    return np.mean(null_scores) if null_scores else 0.0

def update_advanced_metrics(sheet, bq_client, days):
    """Update sheet with advanced calculations"""
    
    print("📊 Calculating advanced metrics...")
    
    # Wind Curtailment
    print("  • Wind curtailment proxy...")
    curtail_mwh, curtail_price, curtail_events = calculate_wind_curtailment(bq_client, days)
    
    # Balancing Statistics
    print("  • Balancing statistics...")
    bal_stats = calculate_balancing_statistics(bq_client, days)
    
    # Write Advanced Metrics Section (starting at row 112)
    row = 112
    
    # Header
    sheet.update_acell(f'A{row}', '🔬 ADVANCED CALCULATIONS')
    sheet.format(f'A{row}:H{row}', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'fontSize': 14}
    })
    
    row += 2
    
    # Wind Curtailment Metrics
    sheet.update_acell(f'A{row}', 'Wind Curtailment Analysis')
    sheet.format(f'A{row}', {'textFormat': {'bold': True}})
    row += 1
    
    if curtail_mwh is not None:
        sheet.update(f'A{row}:B{row+2}', [
            ['Total Curtailment', f'{curtail_mwh:,.0f} MWh'],
            ['Avg Curtailment Price', f'£{curtail_price:.2f}/MWh'],
            ['Curtailment Events', f'{curtail_events:,}']
        ])
        row += 3
    else:
        sheet.update_acell(f'A{row}', 'No curtailment data available')
        row += 2
    
    # Balancing Statistics
    sheet.update_acell(f'A{row}', 'Balancing Volume Breakdown')
    sheet.format(f'A{row}', {'textFormat': {'bold': True}})
    row += 1
    
    if bal_stats:
        for flag, stats in bal_stats.items():
            flag_name = 'Bids' if flag == 'B' else 'Offers'
            sheet.update(f'A{row}:C{row}', [[
                flag_name,
                f"{stats['volume']:,.0f} MWh",
                f"£{stats['avg_price']:.2f}/MWh avg"
            ]])
            row += 1
        
        # Calculate bid/offer ratio
        if 'B' in bal_stats and 'O' in bal_stats:
            bid_vol = bal_stats['B']['volume']
            offer_vol = bal_stats['O']['volume']
            ratio = bid_vol / offer_vol if offer_vol > 0 else 0
            sheet.update_acell(f'A{row}', f'Bid/Offer Ratio: {ratio:.2f}')
            row += 1
    else:
        sheet.update_acell(f'A{row}', 'No balancing data available')
        row += 2
    
    row += 1
    
    # Capacity Factors (calculate from generation data)
    print("  • Capacity factors...")
    gen_query = f"""
    SELECT fuelType, generation
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
    WHERE DATE(publishTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    UNION ALL
    SELECT fuelType, generation
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_iris`
    WHERE DATE(publishTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    """
    
    try:
        gen_df = bq_client.query(gen_query).to_dataframe()
        capacity_factors = calculate_capacity_factors(gen_df)
        
        if capacity_factors:
            sheet.update_acell(f'A{row}', 'Capacity Factors (%)')
            sheet.format(f'A{row}', {'textFormat': {'bold': True}})
            row += 1
            
            # Write top 5 capacity factors
            sorted_cf = sorted(capacity_factors.items(), key=lambda x: x[1], reverse=True)[:5]
            for fuel, cf in sorted_cf:
                sheet.update(f'A{row}:B{row}', [[fuel, f'{cf:.1f}%']])
                
                # Color code: >80% green, 50-80% yellow, <50% red
                if cf >= 80:
                    color = {'red': 0.7, 'green': 1, 'blue': 0.7}
                elif cf >= 50:
                    color = {'red': 1, 'green': 1, 'blue': 0.7}
                else:
                    color = {'red': 1, 'green': 0.7, 'blue': 0.7}
                
                sheet.format(f'B{row}', {'backgroundColor': color})
                row += 1
    except Exception as e:
        print(f"  ⚠️  Capacity factor calc failed: {e}")
    
    row += 1
    
    # Data Quality Score
    print("  • Data quality scores...")
    sheet.update_acell(f'A{row}', 'Data Quality Scores')
    sheet.format(f'A{row}', {'textFormat': {'bold': True}})
    row += 1
    
    quality_checks = [
        ('Generation', 'bmrs_fuelinst', ['fuelType', 'generation', 'publishTime']),
        ('Frequency', 'bmrs_freq', ['frequency', 'measurementTime']),
        ('Prices', 'bmrs_mid', ['price', 'settlementDate']),
        ('Balancing', 'bmrs_netbsad', ['settlementDate', 'settlementPeriod'])
    ]
    
    for name, table, cols in quality_checks:
        try:
            check_query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{table}` WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY) LIMIT 1000"
            if 'settlementDate' not in cols:
                # Use appropriate date column
                if table == 'bmrs_fuelinst':
                    check_query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{table}` WHERE DATE(publishTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY) LIMIT 1000"
                elif table == 'bmrs_freq':
                    check_query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{table}` WHERE DATE(measurementTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY) LIMIT 1000"
            
            df_check = bq_client.query(check_query).to_dataframe()
            score = calculate_data_quality_score(df_check, cols)
            
            sheet.update(f'A{row}:B{row}', [[name, f'{score:.1f}%']])
            
            # Color code quality
            if score >= 95:
                color = {'red': 0.7, 'green': 1, 'blue': 0.7}
            elif score >= 85:
                color = {'red': 1, 'green': 1, 'blue': 0.7}
            else:
                color = {'red': 1, 'green': 0.7, 'blue': 0.7}
            
            sheet.format(f'B{row}', {'backgroundColor': color})
            row += 1
        except Exception as e:
            print(f"  ⚠️  Quality check failed for {name}: {e}")
            sheet.update(f'A{row}:B{row}', [[name, 'N/A']])
            row += 1
    
    print("✅ Advanced metrics updated!")

def main():
    print("🚀 Updating Analysis BI Enhanced with Advanced Calculations...")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to Google Sheets
    creds = get_credentials()
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    # Connect to BigQuery
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    # Get date range
    days = get_date_range(sheet)
    print(f"📊 Date range: {days} days")
    
    # Update advanced metrics
    update_advanced_metrics(sheet, bq_client, days)
    
    # Update timestamp
    sheet.update_acell('A140', f'Advanced calculations updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    print("\n✅ Update complete!")
    print(f"🔗 View sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")

if __name__ == '__main__':
    main()
