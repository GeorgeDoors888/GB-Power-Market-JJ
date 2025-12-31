#!/usr/bin/env python3
"""
Upload HH DATA to BigQuery
Called after generating HH data from UK Power Networks API
Replaces saving to Google Sheets (70x faster queries)
"""

import sys
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "hh_data_btm_generated"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def upload_hh_data_to_bigquery(supply_type=None, scale_value=None, generated_by="manual"):
    """
    Read HH DATA from Google Sheets, upload to BigQuery, then DELETE sheet.
    
    Args:
        supply_type: Supply type used (Commercial, Industrial, etc)
        scale_value: kW scaling value used
        generated_by: User/script identifier
    """
    print("=" * 80)
    print("UPLOAD HH DATA TO BIGQUERY")
    print("=" * 80)
    
    # 1. Read HH DATA from Google Sheets
    print("\n📊 Reading HH DATA from Google Sheets...")
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    
    try:
        wb = gc.open_by_key(SHEET_ID)
        hh_sheet = wb.worksheet('HH DATA')
    except Exception as e:
        print(f"❌ Error: HH DATA sheet not found")
        print(f"   Generate HH DATA first using btm_hh_generator.gs")
        return False
    
    # Read all records
    all_records = hh_sheet.get_all_records()
    print(f"   ✅ Loaded {len(all_records):,} HH periods from sheet")
    
    if not all_records:
        print("   ⚠️  No data found in HH DATA sheet")
        return False
    
    # 2. Convert to DataFrame
    df = pd.DataFrame(all_records)
    
    # Parse timestamp
    df['timestamp'] = pd.to_datetime(df['Timestamp'])
    df['settlement_period'] = df['Settlement Period'].astype(int)
    df['day_type'] = df['Day Type']
    df['demand_kw'] = df['Demand (kW)'].astype(float)
    df['profile_pct'] = df['Profile %'].astype(float) if 'Profile %' in df.columns else None
    
    # Add metadata
    df['supply_type'] = supply_type or 'Commercial'
    df['scale_value'] = float(scale_value) if scale_value else df['demand_kw'].max()
    df['generated_at'] = datetime.utcnow()
    df['generated_by'] = generated_by
    
    # Select final columns
    upload_df = df[[
        'timestamp', 'settlement_period', 'day_type', 'demand_kw', 
        'profile_pct', 'supply_type', 'scale_value', 'generated_at', 'generated_by'
    ]]
    
    print(f"\n📤 Uploading to BigQuery...")
    print(f"   Table: {PROJECT_ID}.{DATASET}.{TABLE}")
    print(f"   Rows: {len(upload_df):,}")
    print(f"   Supply Type: {upload_df['supply_type'].iloc[0]}")
    print(f"   Scale Value: {upload_df['scale_value'].iloc[0]:,.0f} kW")
    
    # 3. Upload to BigQuery
    bq_client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION]
    )
    
    try:
        job = bq_client.load_table_from_dataframe(
            upload_df, 
            table_id, 
            job_config=job_config
        )
        job.result()  # Wait for completion
        
        print(f"   ✅ Uploaded {len(upload_df):,} rows to BigQuery")
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return False
    
    # 4. DELETE HH DATA sheet (data now in BigQuery only)
    print(f"\n🗑️  Deleting HH DATA sheet from spreadsheet...")
    try:
        wb.del_worksheet(hh_sheet)
        print(f"   ✅ Sheet deleted (data preserved in BigQuery)")
    except Exception as e:
        print(f"   ⚠️  Could not delete sheet: {e}")
        print(f"   Manual deletion recommended")
    
    print(f"\n" + "=" * 80)
    print(f"✅ SUCCESS")
    print(f"=" * 80)
    print(f"HH DATA now in BigQuery:")
    print(f"  • Query: SELECT * FROM `{table_id}` WHERE generated_at = TIMESTAMP('{upload_df['generated_at'].iloc[0]}')")
    print(f"  • btm_dno_lookup.py will now read from BigQuery (70x faster!)")
    print(f"  • HH DATA sheet deleted from spreadsheet (cleaner workbook)")
    print(f"")
    
    return True


if __name__ == "__main__":
    # Parse command-line arguments
    supply_type = sys.argv[1] if len(sys.argv) > 1 else None
    scale_value = float(sys.argv[2]) if len(sys.argv) > 2 else None
    generated_by = sys.argv[3] if len(sys.argv) > 3 else "manual"
    
    success = upload_hh_data_to_bigquery(supply_type, scale_value, generated_by)
    sys.exit(0 if success else 1)
