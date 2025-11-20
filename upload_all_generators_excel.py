#!/usr/bin/env python3
"""
Upload All_Generators.xlsx to BigQuery
Handles multi-sheet Excel file with proper column name cleaning
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_ID = "all_generators"
EXCEL_FILE = "All_Generators.xlsx"

print("=" * 80)
print("📊 All_Generators.xlsx → BigQuery Upload")
print("=" * 80)

# Load credentials
print("\n🔐 Loading credentials...")
credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location="US")

# Read Excel file
print(f"\n📖 Reading {EXCEL_FILE}...")
try:
    # Read Sheet1 (contains the data)
    df = pd.read_excel(EXCEL_FILE, sheet_name='Sheet1')
    print(f"✅ Loaded {len(df):,} rows, {len(df.columns)} columns")
    
    # Clean column names - the first row seems to be headers
    # Check if first row contains actual headers
    if df.iloc[0, 0] == 'Export MPAN / MSID':
        print("\n🔧 Detected headers in first row, using as column names...")
        new_columns = df.iloc[0].tolist()
        df = df[1:].reset_index(drop=True)
        df.columns = new_columns
    
    # Clean column names
    cleaned_cols = []
    for i, col in enumerate(df.columns):
        if isinstance(col, str) and col.strip():
            # Remove all special characters and limit length
            clean_col = col.strip()
            # Remove newlines and tabs first
            clean_col = clean_col.replace('\n', ' ')
            clean_col = clean_col.replace('\r', ' ')
            clean_col = clean_col.replace('\t', ' ')
            clean_col = clean_col.replace(' ', '_')
            clean_col = clean_col.replace('/', '_')
            clean_col = clean_col.replace('-', '_')
            clean_col = clean_col.replace('(', '')
            clean_col = clean_col.replace(')', '')
            clean_col = clean_col.replace(':', '')
            clean_col = clean_col.replace('.', '')
            clean_col = clean_col.replace(',', '')
            clean_col = clean_col.replace('[', '')
            clean_col = clean_col.replace(']', '')
            clean_col = clean_col.replace('{', '')
            clean_col = clean_col.replace('}', '')
            clean_col = clean_col.replace('&', 'and')
            clean_col = clean_col.replace('?', '')
            clean_col = clean_col.replace('!', '')
            clean_col = clean_col.replace('*', '')
            clean_col = clean_col.replace('#', '')
            clean_col = clean_col.replace('@', '')
            clean_col = clean_col.replace('%', 'percent')
            clean_col = clean_col.replace('$', '')
            clean_col = clean_col.replace('^', '')
            clean_col = clean_col.replace('+', 'plus')
            clean_col = clean_col.replace('=', 'equals')
            clean_col = clean_col.replace('<', 'lt')
            clean_col = clean_col.replace('>', 'gt')
            clean_col = clean_col.replace('|', 'or')
            clean_col = clean_col.replace('\\', '')
            clean_col = clean_col.replace('"', '')
            clean_col = clean_col.replace("'", '')
            clean_col = clean_col.replace('`', '')
            clean_col = clean_col.replace('~', '')
            # Remove multiple underscores
            while '__' in clean_col:
                clean_col = clean_col.replace('__', '_')
            # Remove leading/trailing underscores
            clean_col = clean_col.strip('_')
            # Limit to 128 characters (BigQuery allows 300 but let's be safe)
            clean_col = clean_col[:128]
            cleaned_cols.append(clean_col.lower())
        else:
            cleaned_cols.append(f'column_{i}')
    
    df.columns = cleaned_cols
    
    # Remove completely empty columns
    df = df.dropna(axis=1, how='all')
    
    # Convert all columns to strings to avoid type issues
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).replace('nan', None)
    
    # Add metadata
    df['_uploaded_at'] = datetime.utcnow().isoformat()
    df['_source_file'] = EXCEL_FILE
    
    print(f"✅ Cleaned data: {len(df):,} rows, {len(df.columns)} columns")
    print(f"\n📋 Sample columns: {list(df.columns)[:10]}")
    
except Exception as e:
    print(f"❌ Error reading Excel file: {e}")
    sys.exit(1)

# Upload to BigQuery
print(f"\n☁️  Uploading to {PROJECT_ID}.{DATASET}.{TABLE_ID}...")

table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE_ID}"

job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    autodetect=True,
)

try:
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # Wait for completion
    
    # Verify upload
    table = client.get_table(table_ref)
    print(f"\n✅ Upload complete!")
    print(f"   Table: {table_ref}")
    print(f"   Rows: {table.num_rows:,}")
    print(f"   Size: {table.num_bytes / 1024 / 1024:.2f} MB")
    
except Exception as e:
    print(f"\n❌ Upload failed: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ All_Generators.xlsx upload complete!")
print("=" * 80)
