#!/usr/bin/env python3
"""
Energy Tariff Data Ingestion - Google Sheets to BigQuery

Ingests 6 critical UK energy tariff datasets from Google Sheets into BigQuery:
1. TNUoS TDR Bands (2024-25 & 2025-26)
2. FiT Levelisation Rates
3. RO (Renewables Obligation) Rates
4. BSUoS (Balancing Services) Rates
5. CCL (Climate Change Levy) Rates

Source: GB Energy Dashboard Google Sheet
Target: inner-cinema-476211-u9.uk_energy_prod

Author: George Major
Date: 21 November 2025
"""

import pickle
import gspread
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, date
import os

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"
SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"

# Ensure credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

def parse_date(date_str, fiscal_year=None):
    """Parse various date formats to DATE object."""
    if not date_str or date_str == '':
        return None
    
    # Handle DD/MM/YYYY
    if '/' in date_str:
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except:
            pass
    
    # Handle YYYY-MM-DD
    if '-' in date_str:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            pass
    
    # Handle fiscal year format (2024/25)
    if fiscal_year:
        year = int(fiscal_year.split('/')[0])
        if 'april' in date_str.lower() or date_str == '':
            return date(year, 4, 1)
        if 'march' in date_str.lower():
            return date(year + 1, 3, 31)
    
    return None

def clean_currency(value):
    """Remove £ and commas from currency strings."""
    if not value or value == '':
        return None
    return float(str(value).replace('£', '').replace(',', '').strip())

def clean_percentage(value):
    """Convert percentage strings to decimal."""
    if not value or value == '':
        return None
    val = str(value).replace('%', '').strip()
    try:
        return float(val) / 100 if float(val) > 1 else float(val)
    except:
        return None

def ingest_tnuos_tdr_bands(gc, bq_client):
    """Ingest TNUoS TDR Bands for 2024-25 and 2025-26."""
    print("\n🔧 INGESTING TNUoS TDR BANDS...")
    
    sheet = gc.open_by_key(SHEET_ID)
    
    all_data = []
    
    for year, sheet_name in [('2024-25', 'TNUos_TDR_Bands_2024-25'), 
                              ('2025-26', 'TNUoS_TDR_Bands_2025-26')]:
        ws = sheet.worksheet(sheet_name)
        data = ws.get_all_values()
        
        # Skip header
        for row in data[1:]:
            if not row[0] or row[0] == '':  # Skip empty rows
                continue
            
            all_data.append({
                'tariff_year': year,
                'band': row[0],
                'rate_gbp_per_site_day': clean_currency(row[1]),
                'unit': row[2] if len(row) > 2 else '£/site/day',
                'notes': row[3] if len(row) > 3 else '',
                'rate_gbp_per_site_year': clean_currency(row[4]) if len(row) > 4 else None,
                'rate_gbp_per_site_month': clean_currency(row[5]) if len(row) > 5 else None,
                'effective_from': date(int(year.split('-')[0]), 4, 1),
                'effective_to': date(int(year.split('-')[1]) + 2000, 3, 31),
                'data_source': 'Google Sheets GB Energy Dashboard'
            })
    
    df = pd.DataFrame(all_data)
    
    # Create table
    table_id = f"{PROJECT_ID}.{DATASET}.tnuos_tdr_bands"
    
    schema = [
        bigquery.SchemaField("tariff_year", "STRING"),
        bigquery.SchemaField("band", "STRING"),
        bigquery.SchemaField("rate_gbp_per_site_day", "FLOAT64"),
        bigquery.SchemaField("unit", "STRING"),
        bigquery.SchemaField("notes", "STRING"),
        bigquery.SchemaField("rate_gbp_per_site_year", "FLOAT64"),
        bigquery.SchemaField("rate_gbp_per_site_month", "FLOAT64"),
        bigquery.SchemaField("effective_from", "DATE"),
        bigquery.SchemaField("effective_to", "DATE"),
        bigquery.SchemaField("data_source", "STRING"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table = bq_client.create_table(table, exists_ok=True)
    
    # Upload data
    job = bq_client.load_table_from_dataframe(df, table_id)
    job.result()
    
    print(f"✅ Loaded {len(df)} rows into {table_id}")
    return len(df)

def ingest_fit_rates(gc, bq_client):
    """Ingest FiT Levelisation Rates."""
    print("\n🔧 INGESTING FiT LEVELISATION RATES...")
    
    sheet = gc.open_by_key(SHEET_ID)
    ws = sheet.worksheet('Copy of FiT_Rates_Pa')
    data = ws.get_all_values()
    
    all_data = []
    
    for row in data[1:]:  # Skip header
        if not row[0] or row[0] == '':
            continue
        
        fiscal_year = row[1]  # e.g., '2018/19'
        year_start = int(fiscal_year.split('/')[0])
        
        all_data.append({
            'scheme_year': row[0],  # SY9, SY10, etc.
            'fiscal_year': fiscal_year,
            'levelisation_fund_gbp': int(row[2].replace(',', '')),
            'total_relevant_electricity_mwh': int(row[3].replace(',', '')),
            'implied_rate_p_per_kwh': float(row[4]),
            'effective_from': date(year_start, 4, 1),
            'effective_to': date(year_start + 1, 3, 31),
            'data_source': 'Ofgem FiT Annual Reports',
            'notes': 'FiT scheme closed to new applicants 31 March 2019'
        })
    
    df = pd.DataFrame(all_data)
    
    table_id = f"{PROJECT_ID}.{DATASET}.fit_levelisation_rates"
    
    schema = [
        bigquery.SchemaField("scheme_year", "STRING"),
        bigquery.SchemaField("fiscal_year", "STRING"),
        bigquery.SchemaField("levelisation_fund_gbp", "INT64"),
        bigquery.SchemaField("total_relevant_electricity_mwh", "INT64"),
        bigquery.SchemaField("implied_rate_p_per_kwh", "FLOAT64"),
        bigquery.SchemaField("effective_from", "DATE"),
        bigquery.SchemaField("effective_to", "DATE"),
        bigquery.SchemaField("data_source", "STRING"),
        bigquery.SchemaField("notes", "STRING"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table = bq_client.create_table(table, exists_ok=True)
    
    job = bq_client.load_table_from_dataframe(df, table_id)
    job.result()
    
    print(f"✅ Loaded {len(df)} rows into {table_id}")
    return len(df)

def ingest_ro_rates(gc, bq_client):
    """Ingest RO (Renewables Obligation) Rates."""
    print("\n🔧 INGESTING RO RATES...")
    
    sheet = gc.open_by_key(SHEET_ID)
    ws = sheet.worksheet('Ro_Rates')
    data = ws.get_all_values()
    
    all_data = []
    
    for row in data[1:]:  # Skip header
        if not row[0] or row[0] == '':
            continue
        
        # Skip non-year rows (descriptions, etc.)
        if '/' not in str(row[0]) or len(str(row[0]).split('/')) != 2:
            continue
        
        obligation_year = row[0]  # e.g., '2016/17'
        try:
            year_start = int(obligation_year.split('/')[0])
        except ValueError:
            continue  # Skip invalid rows
        
        all_data.append({
            'obligation_year': obligation_year,
            'buyout_gbp_per_roc': float(row[1]) if row[1] else None,
            'obligation_roc_per_mwh': float(row[2]) if row[2] else None,
            'recycle_gbp_per_roc': float(row[3]) if row[3] else 0.0,
            'override_p_per_kwh': float(row[4]) if len(row) > 4 and row[4] else None,
            'notes': row[5] if len(row) > 5 else '',
            'effective_from': date(year_start, 4, 1),
            'effective_to': date(year_start + 1, 3, 31),
            'data_source': 'Ofgem RO Publications'
        })
    
    df = pd.DataFrame(all_data)
    
    table_id = f"{PROJECT_ID}.{DATASET}.ro_rates"
    
    schema = [
        bigquery.SchemaField("obligation_year", "STRING"),
        bigquery.SchemaField("buyout_gbp_per_roc", "FLOAT64"),
        bigquery.SchemaField("obligation_roc_per_mwh", "FLOAT64"),
        bigquery.SchemaField("recycle_gbp_per_roc", "FLOAT64"),
        bigquery.SchemaField("override_p_per_kwh", "FLOAT64"),
        bigquery.SchemaField("notes", "STRING"),
        bigquery.SchemaField("effective_from", "DATE"),
        bigquery.SchemaField("effective_to", "DATE"),
        bigquery.SchemaField("data_source", "STRING"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table = bq_client.create_table(table, exists_ok=True)
    
    job = bq_client.load_table_from_dataframe(df, table_id)
    job.result()
    
    print(f"✅ Loaded {len(df)} rows into {table_id}")
    return len(df)

def ingest_bsuos_rates(gc, bq_client):
    """Ingest BSUoS (Balancing Services) Rates."""
    print("\n🔧 INGESTING BSUoS RATES...")
    
    sheet = gc.open_by_key(SHEET_ID)
    ws = sheet.worksheet('BSUoS_Rates')
    data = ws.get_all_values()
    
    all_data = []
    
    for row in data[1:]:  # Skip header
        if not row[0] or row[0] == '':
            continue
        
        all_data.append({
            'publication_status': row[0],
            'tariff_title': row[1],
            'published_date': parse_date(row[2]),
            'effective_from': parse_date(row[3]),
            'effective_to': parse_date(row[4]),
            'rate_gbp_per_mwh': float(row[5]) if row[5] else None,
            'data_source': 'National Grid ESO (NESO)',
            'notes': 'Changed to fixed 6-month tariffs from April 2023'
        })
    
    df = pd.DataFrame(all_data)
    
    table_id = f"{PROJECT_ID}.{DATASET}.bsuos_rates"
    
    schema = [
        bigquery.SchemaField("publication_status", "STRING"),
        bigquery.SchemaField("tariff_title", "STRING"),
        bigquery.SchemaField("published_date", "DATE"),
        bigquery.SchemaField("effective_from", "DATE"),
        bigquery.SchemaField("effective_to", "DATE"),
        bigquery.SchemaField("rate_gbp_per_mwh", "FLOAT64"),
        bigquery.SchemaField("data_source", "STRING"),
        bigquery.SchemaField("notes", "STRING"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table = bq_client.create_table(table, exists_ok=True)
    
    job = bq_client.load_table_from_dataframe(df, table_id)
    job.result()
    
    print(f"✅ Loaded {len(df)} rows into {table_id}")
    return len(df)

def ingest_ccl_rates(gc, bq_client):
    """Ingest CCL (Climate Change Levy) Rates."""
    print("\n🔧 INGESTING CCL RATES...")
    
    sheet = gc.open_by_key(SHEET_ID)
    ws = sheet.worksheet('CCL_Rates')
    data = ws.get_all_values()
    
    all_data = []
    
    for row in data[1:]:  # Skip header
        if not row[0] or row[0] == '':
            continue
        
        electricity_rate = float(row[2]) if row[2] else None
        cca_discount_elec = clean_percentage(row[6]) if len(row) > 6 else None
        
        all_data.append({
            'fiscal_year': row[0],
            'effective_from': parse_date(row[1]),
            'electricity_gbp_per_kwh': electricity_rate,
            'gas_gbp_per_kwh': float(row[3]) if len(row) > 3 and row[3] else None,
            'lpg_gbp_per_kg': float(row[4]) if len(row) > 4 and row[4] else None,
            'other_gbp_per_kg': float(row[5]) if len(row) > 5 and row[5] else None,
            'cca_discount_electricity_pct': cca_discount_elec,
            'cca_discount_gas_pct': clean_percentage(row[7]) if len(row) > 7 else None,
            'cca_electricity_gbp_per_kwh': electricity_rate * (1 - cca_discount_elec) if electricity_rate and cca_discount_elec else None,
            'cca_gas_gbp_per_kwh': float(row[3]) * (1 - clean_percentage(row[7])) if len(row) > 7 and row[3] and row[7] else None,
            'data_source': 'HMRC',
            'notes': 'CCA = Climate Change Agreement (reduced rates for eligible businesses)'
        })
    
    df = pd.DataFrame(all_data)
    
    table_id = f"{PROJECT_ID}.{DATASET}.ccl_rates"
    
    schema = [
        bigquery.SchemaField("fiscal_year", "STRING"),
        bigquery.SchemaField("effective_from", "DATE"),
        bigquery.SchemaField("electricity_gbp_per_kwh", "FLOAT64"),
        bigquery.SchemaField("gas_gbp_per_kwh", "FLOAT64"),
        bigquery.SchemaField("lpg_gbp_per_kg", "FLOAT64"),
        bigquery.SchemaField("other_gbp_per_kg", "FLOAT64"),
        bigquery.SchemaField("cca_discount_electricity_pct", "FLOAT64"),
        bigquery.SchemaField("cca_discount_gas_pct", "FLOAT64"),
        bigquery.SchemaField("cca_electricity_gbp_per_kwh", "FLOAT64"),
        bigquery.SchemaField("cca_gas_gbp_per_kwh", "FLOAT64"),
        bigquery.SchemaField("data_source", "STRING"),
        bigquery.SchemaField("notes", "STRING"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table = bq_client.create_table(table, exists_ok=True)
    
    job = bq_client.load_table_from_dataframe(df, table_id)
    job.result()
    
    print(f"✅ Loaded {len(df)} rows into {table_id}")
    return len(df)

def validate_data(bq_client):
    """Validate ingested data."""
    print("\n🔍 VALIDATING DATA...")
    
    tables = [
        'tnuos_tdr_bands',
        'fit_levelisation_rates',
        'ro_rates',
        'bsuos_rates',
        'ccl_rates'
    ]
    
    total_rows = 0
    
    for table_name in tables:
        query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET}.{table_name}`"
        result = bq_client.query(query).to_dataframe()
        count = result['count'][0]
        total_rows += count
        print(f"   ✅ {table_name}: {count} rows")
    
    print(f"\n📊 Total rows ingested: {total_rows}")
    print(f"   Expected: ~141 rows")
    print(f"   Match: {'✅ YES' if 130 <= total_rows <= 150 else '⚠️  CHECK DATA'}")
    
    return total_rows

def main():
    """Main execution function."""
    print("="*80)
    print("🚀 ENERGY TARIFF DATA INGESTION")
    print("="*80)
    print(f"\nSource: Google Sheets (ID: {SHEET_ID})")
    print(f"Target: {PROJECT_ID}.{DATASET}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize clients
    print("\n📡 Connecting to Google Sheets...")
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    gc = gspread.authorize(creds)
    print("✅ Google Sheets connected")
    
    print("\n📡 Connecting to BigQuery...")
    bq_client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    print("✅ BigQuery connected")
    
    # Ingest all tariff data
    row_counts = {}
    
    try:
        row_counts['tnuos'] = ingest_tnuos_tdr_bands(gc, bq_client)
        row_counts['fit'] = ingest_fit_rates(gc, bq_client)
        row_counts['ro'] = ingest_ro_rates(gc, bq_client)
        row_counts['bsuos'] = ingest_bsuos_rates(gc, bq_client)
        row_counts['ccl'] = ingest_ccl_rates(gc, bq_client)
        
        # Validate
        total = validate_data(bq_client)
        
        print("\n" + "="*80)
        print("✅ INGESTION COMPLETE")
        print("="*80)
        print(f"\nSummary:")
        print(f"   • TNUoS TDR Bands: {row_counts['tnuos']} rows")
        print(f"   • FiT Levelisation: {row_counts['fit']} rows")
        print(f"   • RO Rates: {row_counts['ro']} rows")
        print(f"   • BSUoS Rates: {row_counts['bsuos']} rows")
        print(f"   • CCL Rates: {row_counts['ccl']} rows")
        print(f"   • TOTAL: {total} rows")
        
        print("\n📋 Next Steps:")
        print("   1. Create views: vw_current_tariffs")
        print("   2. Create views: vw_battery_arbitrage_costs")
        print("   3. Update battery_arbitrage.py with tariff costs")
        print("   4. Recalculate historical P&L with true costs")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
