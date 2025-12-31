#!/usr/bin/env python3
"""
Generate reports based on Analysis sheet dropdown selections
Features:
- Multiple selection support (comma-separated)
- Enhanced party roles (VTP, VLP, Consumption, Production)
- Automatic data cleanup before generation
- Date format parsing + filters
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

# ============================================================================
# STEP 0: CLEAR OLD DATA (runs every time) - Clear from row 17 onwards
# ============================================================================
print("🧹 Clearing old report data...\n")

try:
    # Clear from row 17 to remove old headers and data
    sheets_service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range='Analysis!A17:Z10000'
    ).execute()
    print("✅ Cleared previous report data (rows 17+)\n")
except Exception as e:
    print(f"⚠️  Could not clear old data: {e}\n")

# Read user selections
selections = sheets_service.spreadsheets().values().batchGet(
    spreadsheetId=SPREADSHEET_ID,
    ranges=['Analysis!B4', 'Analysis!D4', 'Analysis!B5:B9', 'Analysis!B11:B13']
).execute()

from_date_raw = selections['valueRanges'][0]['values'][0][0] if selections['valueRanges'][0].get('values') else None
to_date_raw = selections['valueRanges'][1]['values'][0][0] if selections['valueRanges'][1].get('values') else None
filters = [row[0] if row else 'All' for row in selections['valueRanges'][2].get('values', [['All']]*5)]
report_options = [row[0] if row else '' for row in selections['valueRanges'][3].get('values', [['']]*3)]

# Parse multiple selections (comma-separated)
def parse_multiple_selections(value):
    """Parse comma-separated values and extract role names"""
    if not value or value == 'All':
        return ['All']
    # Split by comma and clean up
    values = [v.strip() for v in value.split(',')]
    # Extract role name from "Role - Description" format
    roles = []
    for v in values:
        if ' - ' in v:
            roles.append(v.split(' - ')[0].strip())
        else:
            roles.append(v.strip())
    return roles if roles else ['All']

# Parse filters to handle multiple selections
party_roles_raw = filters[0]
party_roles = parse_multiple_selections(party_roles_raw)
bmu_id, unit_name, gen_type, lead_party = filters[1:5]

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

report_category, report_type, graph_type = report_options

print(f"📅 Date Range: {from_date} → {to_date}")
print(f"🔍 Party Roles: {', '.join(party_roles)}")
print(f"🔍 BMU ID: {bmu_id if bmu_id else 'All'}")
print(f"🔍 Other Filters: GenType={gen_type}")
print(f"📊 Report: {report_category}\n")

# Build query with enhanced filters
def get_query_with_filters(category, from_dt, to_dt, party_roles, gen_type='All', bmu_id='All'):
    """Build BigQuery query with party role AND BMU ID filter support"""
    
    # Map party roles to BMU ID patterns
    role_patterns = {
        'Production': "bmUnit LIKE 'E_%' OR bmUnit LIKE 'M_%'",
        'VTP': "bmUnit LIKE 'T_%'",
        'VLP': "bmUnit LIKE '%FBPGM%' OR bmUnit LIKE '%FESEN%' OR bmUnit LIKE '%STORAGE%'",
        'Consumption': "bmUnit LIKE 'D_%'",
        'Supplier': "bmUnit LIKE '2__%'",
        'Interconnector': "bmUnit LIKE 'I_%'",
        'Trader': "1=1",  # No specific pattern
        'Storage': "bmUnit LIKE '%STORAGE%' OR bmUnit LIKE '%BESS%'",
        'All': "1=1"
    }
    
    # Build party role filter
    party_filter = ""
    if 'All' not in party_roles and party_roles:
        role_conditions = [role_patterns.get(role, "1=1") for role in party_roles]
        party_filter = f"AND ({' OR '.join(role_conditions)})"
    
    # Build BMU ID filter (specific BMU takes precedence)
    bmu_filter = ""
    if bmu_id and bmu_id != 'All':
        bmu_filter = f"AND bmUnit LIKE '%{bmu_id}%'"
    
    # Analytics & Derived: Use BMU-level data if BMU ID specified, otherwise aggregated
    if '📊 Analytics' in category or 'Analytics & Derived' in category:
        # Use BMU-level data when specific BMU filtering is needed
        if bmu_id and bmu_id != 'All':
            return f"""
            SELECT
                CAST(settlementDate AS DATE) as date,
                settlementPeriod,
                bmUnit,
                SUM(acceptanceVolume) as total_volume_mwh,
                AVG(acceptancePrice) as avg_price_gbp_mwh,
                COUNT(*) as acceptance_count
            FROM `{PROJECT_ID}.uk_energy_prod.bmrs_boalf_complete`
            WHERE CAST(settlementDate AS DATE) >= '{from_dt}'
            AND CAST(settlementDate AS DATE) <= '{to_dt}'
            AND validation_flag = 'Valid'
            {bmu_filter}
            {party_filter}
            GROUP BY date, settlementPeriod, bmUnit
            ORDER BY date, settlementPeriod, bmUnit
            LIMIT 10000
            """
        else:
            # Use fuel type aggregated data
            where_clauses = [
                f"settlementDate >= '{from_dt}'",
                f"settlementDate <= '{to_dt}'"
            ]

            if gen_type and gen_type != 'All':
                where_clauses.append(f"fuelType = '{gen_type}'")

            where_clause = " AND ".join(where_clauses)

            return f"""
            SELECT
                CAST(settlementDate AS DATE) as date,
                settlementPeriod,
                fuelType,
                SUM(generation) as generation_mw
            FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_iris`
            WHERE {where_clause}
            GROUP BY date, settlementPeriod, fuelType
            ORDER BY date, settlementPeriod, fuelType
            LIMIT 10000
            """
    
    # Generation: Use BMU-level data when BMU ID specified
    if '⚡ Generation' in category or 'Generation' in category:
        if bmu_id and bmu_id != 'All':
            return f"""
            SELECT
                CAST(settlementDate AS DATE) as date,
                settlementPeriod,
                bmUnit,
                acceptanceVolume as volume_mwh,
                acceptancePrice as price_gbp_mwh,
                acceptanceType
            FROM `{PROJECT_ID}.uk_energy_prod.bmrs_boalf_complete`
            WHERE CAST(settlementDate AS DATE) >= '{from_dt}'
            AND CAST(settlementDate AS DATE) <= '{to_dt}'
            AND validation_flag = 'Valid'
            {bmu_filter}
            {party_filter}
            ORDER BY settlementDate, settlementPeriod, bmUnit
            LIMIT 10000
            """
        else:
            # Use fuel type aggregated data
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

    # Default query - returns BMU-level data for debugging
    if bmu_id and bmu_id != 'All':
        return f"""
        SELECT
            CAST(settlementDate AS DATE) as date,
            settlementPeriod,
            bmUnit,
            acceptanceVolume as volume_mwh,
            acceptancePrice as price_gbp_mwh
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_boalf_complete`
        WHERE CAST(settlementDate AS DATE) >= '{from_dt}'
        AND CAST(settlementDate AS DATE) <= '{to_dt}'
        AND validation_flag = 'Valid'
        {bmu_filter}
        {party_filter}
        ORDER BY settlementDate, settlementPeriod, bmUnit
        LIMIT 1000
        """
    else:
        return f"""
        SELECT
            CAST(settlementDate AS DATE) as date,
            settlementPeriod,
            fuelType,
            generation as generation_mw
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_iris`
        WHERE settlementDate >= '{from_dt}' AND settlementDate <= '{to_dt}'
        ORDER BY settlementDate, settlementPeriod, fuelType
        LIMIT 1000
        """

# Execute query
print("🔄 Querying BigQuery...\n")
query = get_query_with_filters(report_category, from_date, to_date, party_roles, gen_type, bmu_id)

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

    # Prepare data with visual separator
    separator_row = ['━━━━━━━━━━━━━━', '━━━━━━━━━━━━━━', '━━━━━━━━━━━━━━', '━━━━━━━━━━━━━━']
    header_row = df_display.columns.tolist()
    data_rows = df_display.values.tolist()
    
    # Combine: separator + header + data
    values = [separator_row, header_row] + data_rows

    # Write new results starting at row 17 (with visual separator)
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Analysis!A17',
        valueInputOption='RAW',
        body={'values': values}
    ).execute()

    print(f"✅ Written {len(df_display)} rows to Analysis sheet")
    print(f"   Location: Row 18+ (header at 18, data starts at 19)")
    print(f"   Visual separator at row 17")
    print(f"   Columns: {', '.join(df_display.columns)}")

    print(f"\n📈 Data Summary:")
    print(f"   Total Rows: {len(df):,}")
    if 'date' in df.columns:
        print(f"   Date Range: {df['date'].min()} → {df['date'].max()}")
    print(f"   Category: {report_category}")
    print(f"   Party Roles: {', '.join(party_roles)}")
    
    print(f"\n👀 SCROLL DOWN to see results below row 17 in the Analysis sheet!")

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
