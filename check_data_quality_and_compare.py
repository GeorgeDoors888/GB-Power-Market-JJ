#!/usr/bin/env python3
"""
Check BigQuery data quality: duplicates and gaps
Generate comparison report for specific settlement periods
"""

import os
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"

# Initialize clients
bq_client = bigquery.Client(project=PROJECT_ID)

def get_gspread_client():
    """Initialize Google Sheets client"""
    import pickle
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    return gspread.authorize(creds)

def check_duplicates(table_name, key_fields):
    """Check for duplicate records in a table"""
    key_fields_str = ', '.join(key_fields)
    query = f"""
    SELECT
      {key_fields_str},
      COUNT(*) AS num_records
    FROM
      `{PROJECT_ID}.{DATASET_ID}.{table_name}`
    GROUP BY
      {key_fields_str}
    HAVING
      COUNT(*) > 1
    ORDER BY
      num_records DESC
    LIMIT 100
    """
    
    df = bq_client.query(query).to_dataframe()
    return df

def check_gaps(table_name, start_date, end_date):
    """Check for missing settlement periods"""
    query = f"""
    WITH all_periods AS (
      SELECT
        d AS settlementDate,
        p AS settlementPeriod
      FROM
        UNNEST(GENERATE_DATE_ARRAY('{start_date}', '{end_date}')) AS d,
        UNNEST(GENERATE_ARRAY(1, 48)) AS p
    )
    SELECT
      a.settlementDate,
      a.settlementPeriod
    FROM
      all_periods a
    LEFT JOIN
      `{PROJECT_ID}.{DATASET_ID}.{table_name}` b
    ON
      a.settlementDate = b.settlementDate
      AND a.settlementPeriod = b.settlementPeriod
    WHERE
      b.settlementDate IS NULL
    ORDER BY
      a.settlementDate, a.settlementPeriod
    """
    
    df = bq_client.query(query).to_dataframe()
    return df

def get_settlement_period_data(date_str, settlement_period):
    """Get all data for a specific settlement period"""
    
    # Query for multiple tables (using camelCase BigQuery column names)
    queries = {
        'fuelinst': f"""
        SELECT 
          settlementDate,
          settlementPeriod,
          publishTime,
          ccgt AS gas_ccgt_mw,
          oil AS oil_mw,
          coal AS coal_mw,
          nuclear AS nuclear_mw,
          wind AS wind_mw,
          ps AS pumped_storage_mw,
          npshyd AS hydro_mw,
          ocgt AS ocgt_mw,
          other AS other_mw,
          intfr AS france_import_mw,
          intirl AS ireland_import_mw,
          intned AS netherlands_import_mw,
          intew AS eastwest_import_mw,
          biomass AS biomass_mw,
          intem AS moyle_import_mw,
          intifa2 AS ifa2_import_mw,
          intnsl AS nsl_import_mw
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
        WHERE settlementDate = '{date_str}'
          AND settlementPeriod = {settlement_period}
        ORDER BY publishTime DESC
        LIMIT 1
        """,
        
        'freq': f"""
        SELECT
          settlementDate,
          settlementPeriod,
          timeFrom,
          frequency
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_freq`
        WHERE settlementDate = '{date_str}'
          AND settlementPeriod = {settlement_period}
        ORDER BY timeFrom
        LIMIT 10
        """,
        
        'mid': f"""
        SELECT
          settlementDate,
          settlementPeriod,
          systemSellPrice,
          systemBuyPrice,
          netImbalanceVolume
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid`
        WHERE settlementDate = '{date_str}'
          AND settlementPeriod = {settlement_period}
        LIMIT 1
        """,
        
        'remit': f"""
        SELECT
          COUNT(*) as outage_count,
          STRING_AGG(DISTINCT fuelType, ', ') as affected_fuel_types,
          SUM(CAST(availableCapacity AS FLOAT64)) as total_unavailable_mw
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_remit_unavailability`
        WHERE eventStart <= TIMESTAMP('{date_str}')
          AND eventEnd >= TIMESTAMP('{date_str}')
        """
    }
    
    results = {}
    for name, query in queries.items():
        try:
            df = bq_client.query(query).to_dataframe()
            results[name] = df
        except Exception as e:
            print(f"Error querying {name}: {e}")
            results[name] = pd.DataFrame()
    
    return results

def create_comparison_sheet(gc, date1, sp1, date2, sp2):
    """Create Google Sheets comparison for two settlement periods"""
    
    print(f"Fetching data for {date1} SP{sp1}...")
    data1 = get_settlement_period_data(date1, sp1)
    
    print(f"Fetching data for {date2} SP{sp2}...")
    data2 = get_settlement_period_data(date2, sp2)
    
    # Open spreadsheet and create new sheet
    sh = gc.open_by_key(SPREADSHEET_ID)
    
    sheet_name = f"SP Comparison {date1} vs {date2}"
    try:
        worksheet = sh.worksheet(sheet_name)
        sh.del_worksheet(worksheet)  # Delete if exists
    except:
        pass
    
    worksheet = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
    
    # Build comparison data
    rows = []
    rows.append(['SETTLEMENT PERIOD COMPARISON', '', '', ''])
    rows.append(['', date1, date2, 'Difference'])
    rows.append(['Settlement Period', sp1, sp2, ''])
    rows.append(['', '', '', ''])
    
    # Generation data
    rows.append(['GENERATION (MW)', '', '', ''])
    if not data1['fuelinst'].empty and not data2['fuelinst'].empty:
        fuel_cols = ['gas_ccgt_mw', 'nuclear_mw', 'wind_mw', 'coal_mw', 'biomass_mw', 
                     'hydro_mw', 'pumped_storage_mw', 'ocgt_mw', 'oil_mw', 'other_mw']
        for col in fuel_cols:
            val1 = data1['fuelinst'][col].iloc[0] if col in data1['fuelinst'].columns else 0
            val2 = data2['fuelinst'][col].iloc[0] if col in data2['fuelinst'].columns else 0
            diff = val2 - val1
            label = col.replace('_mw', '').replace('_', ' ').title()
            rows.append([label, val1, val2, diff])
    
    rows.append(['', '', '', ''])
    rows.append(['INTERCONNECTORS (MW)', '', '', ''])
    if not data1['fuelinst'].empty and not data2['fuelinst'].empty:
        ic_cols = ['france_import_mw', 'ireland_import_mw', 'netherlands_import_mw', 
                   'eastwest_import_mw', 'moyle_import_mw', 'ifa2_import_mw', 'nsl_import_mw']
        for col in ic_cols:
            val1 = data1['fuelinst'][col].iloc[0] if col in data1['fuelinst'].columns else 0
            val2 = data2['fuelinst'][col].iloc[0] if col in data2['fuelinst'].columns else 0
            diff = val2 - val1
            label = col.replace('_import_mw', '').replace('_', ' ').title()
            rows.append([label, val1, val2, diff])
    
    rows.append(['', '', '', ''])
    rows.append(['MARKET PRICES (£/MWh)', '', '', ''])
    if not data1['mid'].empty and not data2['mid'].empty:
        val1 = data1['mid']['systemSellPrice'].iloc[0]
        val2 = data2['mid']['systemSellPrice'].iloc[0]
        diff = val2 - val1
        rows.append(['System Sell Price', val1, val2, diff])
        
        val1 = data1['mid']['systemBuyPrice'].iloc[0]
        val2 = data2['mid']['systemBuyPrice'].iloc[0]
        diff = val2 - val1
        rows.append(['System Buy Price', val1, val2, diff])
    
    rows.append(['', '', '', ''])
    rows.append(['FREQUENCY (Hz)', '', '', ''])
    if not data1['freq'].empty and not data2['freq'].empty:
        avg1 = data1['freq']['frequency'].mean()
        avg2 = data2['freq']['frequency'].mean()
        diff = avg2 - avg1
        rows.append(['Average Frequency', f"{avg1:.3f}", f"{avg2:.3f}", f"{diff:.3f}"])
        
        min1 = data1['freq']['frequency'].min()
        min2 = data2['freq']['frequency'].min()
        rows.append(['Min Frequency', f"{min1:.3f}", f"{min2:.3f}", ''])
        
        max1 = data1['freq']['frequency'].max()
        max2 = data2['freq']['frequency'].max()
        rows.append(['Max Frequency', f"{max1:.3f}", f"{max2:.3f}", ''])
    
    rows.append(['', '', '', ''])
    rows.append(['OUTAGES', '', '', ''])
    if not data1['remit'].empty and not data2['remit'].empty:
        count1 = data1['remit']['outage_count'].iloc[0]
        count2 = data2['remit']['outage_count'].iloc[0]
        rows.append(['Number of Outages', count1, count2, count2 - count1])
        
        cap1 = data1['remit']['total_unavailable_mw'].iloc[0] or 0
        cap2 = data2['remit']['total_unavailable_mw'].iloc[0] or 0
        rows.append(['Unavailable Capacity (MW)', cap1, cap2, cap2 - cap1])
    
    # Write to sheet
    worksheet.update('A1', rows)
    
    # Format header
    worksheet.format('A1:D1', {
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.8},
        'textFormat': {'bold': True, 'fontSize': 14},
        'horizontalAlignment': 'CENTER'
    })
    
    # Format section headers
    for i, row in enumerate(rows):
        if row[0] in ['GENERATION (MW)', 'INTERCONNECTORS (MW)', 'MARKET PRICES (£/MWh)', 
                      'FREQUENCY (Hz)', 'OUTAGES']:
            worksheet.format(f'A{i+1}:D{i+1}', {
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                'textFormat': {'bold': True}
            })
    
    print(f"✅ Created sheet: {sheet_name}")
    return worksheet

def run_data_quality_checks():
    """Run all data quality checks"""
    
    print("\n" + "="*60)
    print("BIGQUERY DATA QUALITY CHECKS")
    print("="*60 + "\n")
    
    # Check duplicates in key tables (using correct BigQuery column names)
    tables_to_check = {
        'bmrs_boalf': ['settlementDate', 'settlementPeriod', 'bmUnit', 'acceptanceNumber'],
        'bmrs_bod': ['settlementDate', 'settlementPeriod', 'bmUnit', 'levelFrom', 'timeFrom'],
        'bmrs_fuelinst': ['settlementDate', 'settlementPeriod', 'fuelType', 'publishTime'],
        # Skip bmrs_freq - different schema (spotTime-based, not settlement periods)
        'bmrs_mid': ['settlementDate', 'settlementPeriod']
    }
    
    for table, keys in tables_to_check.items():
        print(f"\nChecking duplicates in {table}...")
        try:
            duplicates = check_duplicates(table, keys)
            if duplicates.empty:
                print(f"  ✅ No duplicates found")
            else:
                print(f"  ⚠️  Found {len(duplicates)} duplicate groups:")
                print(duplicates.head(10))
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Check for gaps in last 7 days
    print("\n" + "="*60)
    print("CHECKING FOR DATA GAPS (Last 7 days)")
    print("="*60 + "\n")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    # Skip bmrs_freq - it uses spotTime timestamps, not settlement periods
    for table in ['bmrs_fuelinst', 'bmrs_mid']:
        print(f"\nChecking gaps in {table}...")
        try:
            gaps = check_gaps(table, start_date.isoformat(), end_date.isoformat())
            if gaps.empty:
                print(f"  ✅ No gaps found")
            else:
                print(f"  ⚠️  Found {len(gaps)} missing settlement periods")
                print(gaps.head(20))
        except Exception as e:
            print(f"  ❌ Error: {e}")

def main():
    """Main execution"""
    
    # Run data quality checks
    run_data_quality_checks()
    
    # Create Google Sheets comparison
    print("\n" + "="*60)
    print("CREATING GOOGLE SHEETS COMPARISON")
    print("="*60 + "\n")
    
    try:
        gc = get_gspread_client()
        
        # Compare July 16, 2025 SP 00 vs October 9, 2025 SP 10
        worksheet = create_comparison_sheet(
            gc,
            date1='2025-07-16',
            sp1=0,
            date2='2025-10-09',
            sp2=10
        )
        
        print(f"\n✅ Comparison sheet created successfully!")
        print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        
    except Exception as e:
        print(f"\n❌ Error creating comparison sheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
