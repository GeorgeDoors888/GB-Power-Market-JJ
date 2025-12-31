#!/usr/bin/env python3
"""
Generate reports based on Analysis sheet dropdown selections
Version 3 - Fixed VTP/VLP definitions and party role filtering

Features:
- Proper VTP (Virtual Trading Party) and VLP (Virtual Lead Party) definitions
- Lookup from dim_party table for accurate party filtering
- Multiple selection support (comma-separated)
- Enhanced party roles with proper BSC categorization
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
print(f"🔍 Lead Party: {lead_party if lead_party else 'All'}")
print(f"🔍 Generation Type: {gen_type}")
print(f"📊 Report: {report_category}\n")

# Build query with enhanced filters
def get_query_with_filters(category, from_dt, to_dt, party_roles, gen_type='All', bmu_id='All', lead_party='All'):
    """Build BigQuery query for 12 data categories with multi-select BMU support"""
    
    # Parse multi-select BMU IDs (comma-separated)
    bmu_list = []
    if bmu_id and bmu_id != 'All':
        bmu_list = [b.strip() for b in bmu_id.split(',') if b.strip()]
    
    # Build BMU filter for single or multiple IDs
    bmu_filter = ""
    if bmu_list:
        if len(bmu_list) == 1:
            bmu_filter = f"AND bmUnit LIKE '%{bmu_list[0]}%'"
        else:
            bmu_in_clause = "', '".join(bmu_list)
            bmu_filter = f"AND bmUnit IN ('{bmu_in_clause}')"
    
    # Build lead party filter
    lead_party_filter = ""
    if lead_party and lead_party != 'All':
        lead_party_filter = f"AND party_name LIKE '%{lead_party}%'"
    
    # Build party role filter
    party_filter = ""
    if 'All' not in party_roles and party_roles:
        party_conditions = []
        for role in party_roles:
            if role == 'VTP':
                party_conditions.append("is_vtp = TRUE")
            elif role == 'VLP':
                party_conditions.append("is_vlp = TRUE")
            elif role == 'Production':
                party_conditions.append("(bmUnit LIKE 'E_%' OR bmUnit LIKE 'M_%')")
            elif role == 'Consumption':
                party_conditions.append("bmUnit LIKE 'D_%'")
            elif role == 'Supplier':
                party_conditions.append("bmUnit LIKE '2__%'")
            elif role == 'Interconnector':
                party_conditions.append("bmUnit LIKE 'I_%'")
            elif role == 'Storage':
                party_conditions.append("(bmUnit LIKE '%STORAGE%' OR bmUnit LIKE '%BESS%')")
        
        if party_conditions:
            party_filter = f"AND ({' OR '.join(party_conditions)})"
    
    # ==========================
    # CATEGORY 1: Analytics & Derived (Balancing with Prices)
    # ==========================
    if '📊 Analytics' in category or 'Analytics & Derived' in category:
        # Need party lookup for VTP/VLP filtering
        needs_party = any(role in ['VTP', 'VLP'] for role in party_roles) or lead_party != 'All'
        
        if needs_party:
            bmu_filter_joined = bmu_filter.replace("bmUnit", "b.bmUnit")
            party_filter_joined = party_filter.replace("is_vtp", "bp.is_vtp").replace("is_vlp", "bp.is_vlp").replace("bmUnit", "b.bmUnit")
            
            return f"""
            WITH bmu_parties AS (
                SELECT DISTINCT r.elexonbmunit as bmUnit, p.party_name, p.is_vlp, p.is_vtp
                FROM `{PROJECT_ID}.uk_energy_prod.bmu_registration_data` r
                JOIN `{PROJECT_ID}.uk_energy_prod.dim_party` p ON r.leadpartyname = p.party_name
            )
            SELECT
                CAST(b.settlementDate AS DATE) as date, b.settlementPeriod, b.bmUnit,
                bp.party_name, SUM(b.acceptanceVolume) as volume_mwh,
                AVG(b.acceptancePrice) as price_gbp_mwh, COUNT(*) as acceptance_count
            FROM `{PROJECT_ID}.uk_energy_prod.bmrs_boalf_complete` b
            LEFT JOIN bmu_parties bp ON b.bmUnit = bp.bmUnit
            WHERE CAST(b.settlementDate AS DATE) >= '{from_dt}' AND CAST(b.settlementDate AS DATE) <= '{to_dt}'
            AND b.validation_flag = 'Valid' {bmu_filter_joined} {party_filter_joined} {lead_party_filter.replace("party_name", "bp.party_name")}
            GROUP BY date, settlementPeriod, b.bmUnit, bp.party_name
            ORDER BY date, settlementPeriod LIMIT 10000
            """
        else:
            return f"""
            SELECT
                CAST(settlementDate AS DATE) as date, settlementPeriod, bmUnit,
                SUM(acceptanceVolume) as volume_mwh, AVG(acceptancePrice) as price_gbp_mwh, COUNT(*) as acceptance_count
            FROM `{PROJECT_ID}.uk_energy_prod.bmrs_boalf_complete`
            WHERE CAST(settlementDate AS DATE) >= '{from_dt}' AND CAST(settlementDate AS DATE) <= '{to_dt}'
            AND validation_flag = 'Valid' {bmu_filter} {party_filter}
            GROUP BY date, settlementPeriod, bmUnit
            ORDER BY date, settlementPeriod LIMIT 10000
            """
    
    # ==========================
    # CATEGORY 2: Generation & Fuel Mix (Aggregated)
    # ==========================
    elif '⚡ Generation' in category or 'Generation & Fuel Mix' in category:
        fuel_filter = f"AND fuelType = '{gen_type}'" if gen_type and gen_type != 'All' else ""
        
        return f"""
        SELECT
            CAST(settlementDate AS DATE) as date, settlementPeriod, fuelType, SUM(generation) as generation_mw
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_iris`
        WHERE settlementDate >= '{from_dt}' AND settlementDate <= '{to_dt}' {fuel_filter}
        GROUP BY date, settlementPeriod, fuelType
        ORDER BY date, settlementPeriod LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 3: Individual BMU Generation (B1610)
    # ==========================
    elif '🔋 Individual BMU' in category:
        # Use bmrs_boalf_complete for individual BMU volumes (acceptance data)
        # Note: bmrs_indgen is regional aggregate, not per-BMU
        return f"""
        SELECT
            CAST(settlementDate AS DATE) as date, settlementPeriod, bmUnit,
            SUM(acceptanceVolume) as generation_mwh, COUNT(*) as acceptances
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_boalf_complete`
        WHERE CAST(settlementDate AS DATE) >= '{from_dt}' AND CAST(settlementDate AS DATE) <= '{to_dt}'
        AND validation_flag = 'Valid' {bmu_filter}
        GROUP BY date, settlementPeriod, bmUnit
        ORDER BY date, settlementPeriod LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 4: Balancing Actions (MELs/MILs)
    # ==========================
    elif '💰 Balancing' in category or 'Balancing Actions' in category:
        return f"""
        SELECT
            CAST(timeFrom AS DATE) as date, settlementPeriod, bmUnit, levelFrom, levelTo
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_mels_iris`
        WHERE CAST(timeFrom AS DATE) >= '{from_dt}' AND CAST(timeFrom AS DATE) <= '{to_dt}' {bmu_filter}
        UNION ALL
        SELECT
            CAST(timeFrom AS DATE) as date, settlementPeriod, bmUnit, levelFrom, levelTo
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_mils_iris`
        WHERE CAST(timeFrom AS DATE) >= '{from_dt}' AND CAST(timeFrom AS DATE) <= '{to_dt}' {bmu_filter}
        ORDER BY date, settlementPeriod LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 5: System Operations (Frequency/Prices)
    # ==========================
    elif '📡 System' in category or 'System Operations' in category:
        return f"""
        WITH freq AS (
            SELECT CAST(spotTime AS DATE) as date, AVG(frequency) as avg_freq
            FROM `{PROJECT_ID}.uk_energy_prod.bmrs_freq`
            WHERE CAST(spotTime AS DATE) >= '{from_dt}' AND CAST(spotTime AS DATE) <= '{to_dt}'
            GROUP BY date
        ),
        prices AS (
            SELECT CAST(settlementDate AS DATE) as date, settlementPeriod,
            AVG(systemSellPrice) as ssp, AVG(systemBuyPrice) as sbp
            FROM `{PROJECT_ID}.uk_energy_prod.bmrs_costs`
            WHERE CAST(settlementDate AS DATE) >= '{from_dt}' AND CAST(settlementDate AS DATE) <= '{to_dt}'
            GROUP BY date, settlementPeriod
        )
        SELECT p.date, p.settlementPeriod, p.ssp, p.sbp, f.avg_freq
        FROM prices p LEFT JOIN freq f ON p.date = f.date
        ORDER BY p.date, p.settlementPeriod LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 6: Physical Constraints (NESO Regional)
    # ==========================
    elif '🚧 Physical' in category or 'Physical Constraints' in category:
        # Use NESO breakdown table (Date is STRING format)
        return f"""
        SELECT
            CAST(Date AS DATE) as date,
            SUM(`Reducing largest loss cost`) as largest_loss_cost,
            SUM(`Increasing system inertia cost`) as inertia_cost,
            SUM(`Voltage constraints cost`) as voltage_cost,
            SUM(`Thermal constraints cost`) as thermal_cost
        FROM `{PROJECT_ID}.uk_energy_prod.neso_constraint_breakdown_2024_2025`
        WHERE CAST(Date AS DATE) >= '{from_dt}' AND CAST(Date AS DATE) <= '{to_dt}'
        GROUP BY date
        ORDER BY date DESC LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 7: Interconnectors (Cross-Border)
    # ==========================
    elif '🔌 Interconnectors' in category or 'Interconnector' in category:
        return f"""
        SELECT
            CAST(settlementDate AS DATE) as date, settlementPeriod, fuelType, SUM(generation) as flow_mw
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_iris`
        WHERE settlementDate >= '{from_dt}' AND settlementDate <= '{to_dt}'
        AND fuelType LIKE 'INT%'
        GROUP BY date, settlementPeriod, fuelType
        ORDER BY date, settlementPeriod LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 8: Market Prices (MID/SSP/SBP)
    # ==========================
    elif '📈 Market' in category or 'Market Prices' in category:
        return f"""
        SELECT
            CAST(settlementDate AS DATE) as date, settlementPeriod,
            AVG(price) as mid_price_gbp_mwh, SUM(volume) as volume_mwh
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_mid`
        WHERE CAST(settlementDate AS DATE) >= '{from_dt}' AND CAST(settlementDate AS DATE) <= '{to_dt}'
        GROUP BY date, settlementPeriod
        ORDER BY date, settlementPeriod LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 9: Demand Forecasts (NESO)
    # ==========================
    elif '📉 Demand' in category or 'Demand Forecasts' in category:
        return f"""
        SELECT
            CAST(settlementDate AS DATE) as date, settlementPeriod,
            AVG(transmissionSystemDemand) as demand_mw
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_inddem`
        WHERE CAST(settlementDate AS DATE) >= '{from_dt}' AND CAST(settlementDate AS DATE) <= '{to_dt}'
        GROUP BY date, settlementPeriod
        ORDER BY date, settlementPeriod LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 10: Wind Forecasts (Generation)
    # ==========================
    elif '🌬️ Wind' in category or 'Wind Forecasts' in category:
        return f"""
        SELECT
            CAST(publishTime AS DATE) as date, settlementPeriod, AVG(generation) as forecast_wind_mw
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_windfor`
        WHERE CAST(publishTime AS DATE) >= '{from_dt}' AND CAST(publishTime AS DATE) <= '{to_dt}'
        GROUP BY date, settlementPeriod
        ORDER BY date, settlementPeriod LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 11: REMIT Messages (Unavailability)
    # ==========================
    elif '⚠️ REMIT' in category or 'REMIT Messages' in category:
        # Note: Use registrationCode (BMU ID) instead of bmUnit
        bmu_filter_remit = bmu_filter.replace("bmUnit", "registrationCode")
        
        return f"""
        SELECT
            CAST(eventStartTime AS DATE) as date, registrationCode as bmUnit, unavailabilityType, fuelType,
            affectedUnit, CAST(availableCapacity AS FLOAT64) as availableCapacity, 
            CAST(unavailableCapacity AS FLOAT64) as unavailableCapacity
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_remit_unavailability`
        WHERE CAST(eventStartTime AS DATE) >= '{from_dt}' AND CAST(eventStartTime AS DATE) <= '{to_dt}' {bmu_filter_remit}
        ORDER BY date, registrationCode LIMIT 10000
        """
    
    # ==========================
    # CATEGORY 12: Party Analysis (VTP/VLP Performance)
    # ==========================
    elif '🔍 Party' in category or 'Party Analysis' in category:
        vtp_filter = "AND is_vtp = TRUE" if 'VTP' in party_roles else ""
        vlp_filter = "AND is_vlp = TRUE" if 'VLP' in party_roles else ""
        role_filter = vtp_filter or vlp_filter
        
        return f"""
        WITH party_bmus AS (
            SELECT r.elexonbmunit as bmUnit, p.party_name, p.is_vtp, p.is_vlp
            FROM `{PROJECT_ID}.uk_energy_prod.bmu_registration_data` r
            JOIN `{PROJECT_ID}.uk_energy_prod.dim_party` p ON r.leadpartyname = p.party_name
            WHERE 1=1 {role_filter} {lead_party_filter}
        )
        SELECT
            CAST(b.settlementDate AS DATE) as date, pb.party_name,
            COUNT(DISTINCT b.bmUnit) as bmu_count, SUM(b.acceptanceVolume) as total_volume_mwh,
            AVG(b.acceptancePrice) as avg_price_gbp_mwh, COUNT(*) as acceptance_count
        FROM `{PROJECT_ID}.uk_energy_prod.bmrs_boalf_complete` b
        JOIN party_bmus pb ON b.bmUnit = pb.bmUnit
        WHERE CAST(b.settlementDate AS DATE) >= '{from_dt}' AND CAST(b.settlementDate AS DATE) <= '{to_dt}'
        AND b.validation_flag = 'Valid'
        GROUP BY date, pb.party_name
        ORDER BY date, total_volume_mwh DESC LIMIT 10000
        """
    
    # Default fallback: Return aggregated fuel type data
    return f"""
    SELECT
        CAST(settlementDate AS DATE) as date, settlementPeriod, fuelType, SUM(generation) as generation_mw
    FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_iris`
    WHERE settlementDate >= '{from_dt}' AND settlementDate <= '{to_dt}'
    GROUP BY date, settlementPeriod, fuelType
    ORDER BY date, settlementPeriod LIMIT 10000
    """

# Execute query
print("🔄 Querying BigQuery...\n")
query = get_query_with_filters(report_category, from_date, to_date, party_roles, gen_type, bmu_id, lead_party)

try:
    df = bq_client.query(query).to_dataframe()

    print(f"✅ Retrieved {len(df)} rows\n")

    # Convert ALL columns to strings for Google Sheets
    for col in df.columns:
        df[col] = df[col].astype(str)

    # Limit display rows
    df_display = df.head(1000)

    print("📝 Writing results to Google Sheets...\n")

    # Create summary indicator for row 16
    date_min = df['date'].min() if 'date' in df.columns else 'N/A'
    date_max = df['date'].max() if 'date' in df.columns else 'N/A'
    bmu_display = bmu_id if bmu_id and bmu_id != 'All' else 'All BMUs'
    summary_text = f"📊 {len(df)} ROWS BELOW ({date_min} → {date_max}) | Filter: {bmu_display} | ⬇️ SCROLL DOWN TO SEE ALL DATA ⬇️"
    
    # Write summary indicator at row 16
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Analysis!A16:F16',
        body={'values': [[summary_text, '', '', '', '', '']]},
        valueInputOption='RAW'
    ).execute()
    
    # Format summary with yellow background and bold text
    try:
        # Get Analysis sheet ID
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        analysis_sheet_id = None
        for sheet in sheet_metadata.get('sheets', []):
            if sheet['properties']['title'] == 'Analysis':
                analysis_sheet_id = sheet['properties']['sheetId']
                break
        
        if analysis_sheet_id:
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={
                    'requests': [{
                        'repeatCell': {
                            'range': {
                                'sheetId': analysis_sheet_id,
                                'startRowIndex': 15,
                                'endRowIndex': 16,
                                'startColumnIndex': 0,
                                'endColumnIndex': 6
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.2},
                                    'textFormat': {'bold': True, 'fontSize': 11},
                                    'horizontalAlignment': 'LEFT'
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                        }
                    }]
                }
            ).execute()
    except Exception as format_error:
        print(f"⚠️  Could not apply formatting: {format_error}")

    # Create visual separator
    separator_row = ['━━━━━━━━━━━━━━'] * len(df_display.columns)
    header_row = df_display.columns.tolist()
    data_rows = df_display.values.tolist()

    # Combine separator + headers + data
    values = [separator_row, header_row] + data_rows

    # Write starting at row 17
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Analysis!A17',
        body={'values': values},
        valueInputOption='RAW'
    ).execute()

    print(f"✅ Written {len(df_display)} rows to Analysis sheet")
    print(f"   Location: Row 19+ (data starts at row 19)")
    print(f"   Summary indicator at row 16")
    print(f"   Visual separator at row 17")
    print(f"   Header at row 18")
    print(f"   Columns: {', '.join(df_display.columns.tolist())}")

    # Summary stats
    print(f"\n📈 Data Summary:")
    print(f"   Total Rows: {len(df):,}")
    if len(df) > 0:
        if 'date' in df.columns:
            print(f"   Date Range: {df['date'].min()} → {df['date'].max()}")
            last_row = 18 + len(df_display)
            print(f"   Last Row: {last_row}")
    print(f"   Category: {report_category}")
    print(f"   Party Roles: {', '.join(party_roles)}")
    if bmu_id and bmu_id != 'All':
        print(f"   BMU Filter: {bmu_id}")

    print(f"\n🎯 FILTERS APPLIED SUCCESSFULLY!")
    print(f"👀 CHECK ROW 16 for summary, then SCROLL DOWN to row {18 + len(df_display)} to see all data!")
    print("✅ Report generation complete!")

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"\nQuery attempted:")
    print(query)
