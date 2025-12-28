#!/usr/bin/env python3
"""
Generate reports based on Analysis sheet dropdown selections
Fixed: Date format parsing + CCGT filter
"""

from google.cloud import bigquery
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'

print("📊 Reading Analysis sheet selections...\n")

creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
sheets_service = build('sheets', 'v4', credentials=creds)
bq_client = bigquery.Client(project=PROJECT_ID, location='US')

# Read user selections
selections = sheets_service.spreadsheets().values().batchGet(
    spreadsheetId=SPREADSHEET_ID,
    ranges=['Analysis!B4', 'Analysis!D4', 'Analysis!B5:B9', 'Analysis!B11:B13']
).execute()

from_date_raw = selections['valueRanges'][0]['values'][0][0] if selections['valueRanges'][0].get('values') else None
to_date_raw = selections['valueRanges'][1]['values'][0][0] if selections['valueRanges'][1].get('values') else None
filters = [row[0] if row else 'All' for row in selections['valueRanges'][2].get('values', [['All']]*5)]
report_options = [row[0] if row else '' for row in selections['valueRanges'][3].get('values', [['']]*3)]

# Parse dates - handle DD/MM/YYYY from Google Sheets
def parse_date(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()

    # Try DD/MM/YYYY format
    if '/' in date_str:
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    # Already in YYYY-MM-DD format
    return date_str

from_date = parse_date(from_date_raw)
to_date = parse_date(to_date_raw)

party_role, bmu_id, unit_name, gen_type, lead_party = filters
report_category, report_type, graph_type = report_options

print(f"📅 Date Range: {from_date} → {to_date}")
print(f"🔍 Filters: Party={party_role}, BMU={bmu_id}, GenType={gen_type}")
print(f"📊 Report: {report_category}\n")

# Build query with filters
def get_query_with_filters(category, from_dt, to_dt, gen_type='All'):
    if '⚡ Generation' in category:
        where_clauses = [
            f"settlementDate >= '{from_dt}'",
            f"settlementDate <= '{to_dt}'",
            "generation > 0"
        ]

        if gen_type and gen_type != 'All':
            where_clauses.append(f"fuelType = '{gen_type}'")

        where_clause = " AND ".join(where_clauses)

        return f"""
        SELECT
            CAST(settlementDate AS DATE) as date,
            settlementPeriod,
            fuelType,
            generation as generation_mw
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_iris`
        WHERE {where_clause}
        ORDER BY settlementDate, settlementPeriod, fuelType
        LIMIT 10000
        """

    # Default query
    return f"""
    SELECT * FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_iris`
    WHERE settlementDate >= '{from_dt}' AND settlementDate <= '{to_dt}'
    LIMIT 1000
    """

# Execute query
print("🔄 Querying BigQuery...\n")
query = get_query_with_filters(report_category, from_date, to_date, gen_type)

try:
    df = bq_client.query(query).to_dataframe()

    print(f"✅ Retrieved {len(df)} rows\n")

    # Convert dates to strings
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        elif hasattr(df[col].dtype, 'name') and 'date' in df[col].dtype.name:
            df[col] = df[col].astype(str)

    df = df.fillna('')

    # Write to sheets
    print("📝 Writing results to Google Sheets...\n")

    # Limit to 1000 rows for display
    df_display = df.head(1000)

    # Clear old results
    sheets_service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range='Analysis!A18:Z10000'
    ).execute()

    # Prepare data
    values = [df_display.columns.tolist()] + df_display.values.tolist()

    # Write new results
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Analysis!A18',
        valueInputOption='RAW',
        body={'values': values}
    ).execute()

    print(f"✅ Written {len(df_display)} rows to Analysis sheet")
    print(f"   Location: Row 18+")
    print(f"   Columns: {', '.join(df_display.columns)}")

    print(f"\n📈 Data Summary:")
    print(f"   Total Rows: {len(df):,}")
    if 'date' in df.columns:
        print(f"   Date Range: {df['date'].min()} → {df['date'].max()}")
    print(f"   Category: {report_category}")

    print(f"\n✅ Report generation complete!")

except Exception as e:
    error_msg = str(e)
    print(f"❌ Error: {error_msg}\n")
    print(f"Query attempted:\n{query}")

    # Write error to sheet
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Analysis!A18',
        valueInputOption='RAW',
        body={'values': [[f'❌ Error: {error_msg[:200]}']]}
    ).execute()

