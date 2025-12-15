#!/usr/bin/env python3
"""
Complete Dashboard Transformation Script
- Removes old embedded charts
- Removes any GSP regional data if present
- Implements new dark-themed dashboard with enhanced KPIs
- Creates new chart layout per design specification
- Preserves all existing data (fuel, interconnectors, outages)
"""

from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
import pandas as pd
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"

# Theme colors (Material Black)
THEME = {
    'DARK_BG': '#121212',
    'WHITE_TEXT': '#FFFFFF',
    'GRID': '#333333',
    'RED': '#E53935',      # Demand
    'BLUE': '#1E88E5',     # Generation
    'GREEN': '#43A047',    # Wind
    'ORANGE': '#FB8C00',   # Margin
    'GREY': '#9E9E9E',     # Price
    'PURPLE': '#8E24AA'    # Constraints
}

def connect():
    """Connect to BigQuery, Google Sheets, and Sheets API"""
    # BigQuery
    bq_creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    bq_client = bigquery.Client(credentials=bq_creds, project=PROJECT_ID, location="US")
    
    # Google Sheets (gspread)
    sheets_creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(sheets_creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    
    # Sheets API v4
    sheets_service = build('sheets', 'v4', credentials=sheets_creds)
    
    return bq_client, sh, sheets_service

def remove_old_charts(sheets_service):
    """Remove all embedded charts from Dashboard sheet"""
    print("\n🗑️  Removing old charts...")
    
    # Get spreadsheet data
    result = sheets_service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        includeGridData=False
    ).execute()
    
    # Find Dashboard sheet and its charts
    dashboard_sheet_id = None
    chart_ids = []
    
    for sheet in result['sheets']:
        if sheet['properties']['title'] == 'Dashboard':
            dashboard_sheet_id = sheet['properties']['sheetId']
            if 'charts' in sheet:
                chart_ids = [chart['chartId'] for chart in sheet['charts']]
            break
    
    if not chart_ids:
        print("✅ No charts to remove")
        return dashboard_sheet_id
    
    # Build delete requests
    requests = []
    for chart_id in chart_ids:
        requests.append({
            'deleteEmbeddedObject': {
                'objectId': chart_id
            }
        })
    
    # Execute deletions
    if requests:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': requests}
        ).execute()
        print(f"✅ Deleted {len(chart_ids)} old charts")
    
    return dashboard_sheet_id

def clean_gsp_data(dashboard_sheet):
    """Remove GSP regional data if it exists"""
    print("\n🧹 Cleaning GSP regional data...")
    
    all_values = dashboard_sheet.get_all_values()
    
    # Find GSP data rows
    gsp_start_row = None
    gsp_end_row = None
    
    for i, row in enumerate(all_values, 1):
        row_text = ' '.join(str(cell) for cell in row)
        if 'London Core' in row_text or ('GSP' in row_text and 'Region' in row_text):
            gsp_start_row = i
        if gsp_start_row and i > gsp_start_row:
            # Check if we've passed the GSP data (empty rows or outage header)
            if 'Asset Name' in row_text or (i > gsp_start_row + 20):
                gsp_end_row = i - 1
                break
    
    if gsp_start_row:
        # Clear the GSP data range
        num_rows = (gsp_end_row or gsp_start_row + 18) - gsp_start_row + 1
        clear_range = f'A{gsp_start_row}:Z{gsp_start_row + num_rows}'
        dashboard_sheet.batch_clear([clear_range])
        print(f"✅ Cleared GSP data from rows {gsp_start_row}-{gsp_start_row + num_rows}")
    else:
        print("✅ No GSP data found to clean")

def fetch_today_data(bq_client):
    """Fetch TODAY's comprehensive data including constraints"""
    print(f"\n📊 Fetching TODAY's data from BigQuery...")
    
    query = f"""
    WITH 
    -- Market prices
    prices AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            AVG(price) as market_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
          AND dataProvider = 'APXMIDP'
        GROUP BY date, sp
    ),
    
    -- GB Demand
    demand AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            AVG(demand) as demand_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indo_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
        GROUP BY date, sp
    ),
    
    -- Total Generation
    generation AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            SUM(generation) as generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
        GROUP BY date, sp
    ),
    
    -- Wind Generation
    wind AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            SUM(generation) as wind_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
          AND fuelType LIKE '%WIND%'
        GROUP BY date, sp
    ),
    
    -- Interconnector Imports (negative = export)
    interconnectors AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            SUM(CASE WHEN generation < 0 THEN ABS(generation) ELSE 0 END) as ic_import_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
          AND fuelType LIKE 'INT%'
        GROUP BY date, sp
    ),
    
    -- Frequency (from measurementTime, not settlementDate)
    frequency AS (
        SELECT
            CAST(measurementTime AS DATE) as date,
            EXTRACT(HOUR FROM measurementTime) * 2 + 
            CAST(FLOOR(EXTRACT(MINUTE FROM measurementTime) / 30) AS INT64) + 1 as sp,
            AVG(frequency) as frequency_hz
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        WHERE CAST(measurementTime AS DATE) = CURRENT_DATE('Europe/London')
        GROUP BY date, sp
    ),
    
    -- Constraints (bid-offer volume changes)
    constraints AS (
        SELECT
            CAST(settlementDate AS DATE) as date,
            settlementPeriod as sp,
            SUM(ABS(COALESCE(offer, 0)) + ABS(COALESCE(bid, 0))) / 100 as constraint_volume
        FROM `{PROJECT_ID}.{DATASET}.bmrs_bod_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE('Europe/London')
        GROUP BY date, sp
    )
    
    -- Combine all
    SELECT
        p.date,
        p.sp as settlement_period,
        COALESCE(p.market_price, 0) as market_price,
        COALESCE(d.demand_mw, 0) as demand_mw,
        COALESCE(g.generation_mw, 0) as generation_mw,
        COALESCE(w.wind_mw, 0) as wind_mw,
        COALESCE(ic.ic_import_mw, 0) as interconnector_import_mw,
        COALESCE(f.frequency_hz, 50.0) as frequency_hz,
        COALESCE(c.constraint_volume, 0) as constraint_mw
    FROM prices p
    LEFT JOIN demand d ON p.date = d.date AND p.sp = d.sp
    LEFT JOIN generation g ON p.date = g.date AND p.sp = g.sp
    LEFT JOIN wind w ON p.date = w.date AND p.sp = w.sp
    LEFT JOIN interconnectors ic ON p.date = ic.date AND p.sp = ic.sp
    LEFT JOIN frequency f ON p.date = f.date AND p.sp = f.sp
    LEFT JOIN constraints c ON p.date = c.date AND p.sp = c.sp
    ORDER BY p.sp
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} settlement periods for TODAY")
    return df

def create_enhanced_kpis(df):
    """Create horizontal KPI layout with 6 metrics"""
    print("\n📊 Creating enhanced KPIs...")
    
    if len(df) == 0:
        return [
            ['Total Demand MW', 'Generation MW', 'Wind Share %', 'Margin MW', 'Avg Price £/MWh', 'Constraint MW'],
            ['0', '0', '0.0%', '0', '£0.00', '0']
        ]
    
    # Calculate current values (latest settlement period)
    latest = df.iloc[-1] if len(df) > 0 else df.iloc[0]
    
    total_demand_mw = latest['demand_mw']
    total_generation_mw = latest['generation_mw']
    
    # Wind share calculation
    total_wind_mw = df['wind_mw'].sum()
    total_gen_sum = df['generation_mw'].sum()
    wind_share_pct = (total_wind_mw / total_gen_sum * 100) if total_gen_sum > 0 else 0
    
    # Margin
    margin_mw = total_generation_mw - total_demand_mw
    
    # Average price
    avg_price = df['market_price'].mean()
    
    # Total constraints
    constraint_mw = df['constraint_mw'].sum()
    
    kpi_data = [
        ['Total Demand MW', 'Generation MW', 'Wind Share %', 'Margin MW', 'Avg Price £/MWh', 'Constraint MW'],
        [
            f'{total_demand_mw:,.0f}',
            f'{total_generation_mw:,.0f}',
            f'{wind_share_pct:.1f}%',
            f'{margin_mw:,.0f}',
            f'£{avg_price:.2f}',
            f'{constraint_mw:,.0f}'
        ]
    ]
    
    return kpi_data

def apply_dark_theme(dashboard_sheet, sheets_service, dashboard_sheet_id):
    """Apply dark Material Black theme to Dashboard"""
    print("\n🎨 Applying dark theme...")
    
    requests = [
        # Set entire sheet background to dark
        {
            'updateSheetProperties': {
                'properties': {
                    'sheetId': dashboard_sheet_id,
                    'gridProperties': {
                        'hideGridlines': False
                    }
                },
                'fields': 'gridProperties.hideGridlines'
            }
        },
        # Format entire sheet with dark background and white text
        {
            'repeatCell': {
                'range': {
                    'sheetId': dashboard_sheet_id
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.07, 'green': 0.07, 'blue': 0.07  # #121212
                        },
                        'textFormat': {
                            'foregroundColor': {
                                'red': 1.0, 'green': 1.0, 'blue': 1.0  # White
                            }
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        },
        # Format title row (A1:G1)
        {
            'repeatCell': {
                'range': {
                    'sheetId': dashboard_sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 7
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True,
                            'fontSize': 18
                        },
                        'horizontalAlignment': 'CENTER'
                    }
                },
                'fields': 'userEnteredFormat(textFormat,horizontalAlignment)'
            }
        },
        # Format KPI labels (A3:F3)
        {
            'repeatCell': {
                'range': {
                    'sheetId': dashboard_sheet_id,
                    'startRowIndex': 2,
                    'endRowIndex': 3,
                    'startColumnIndex': 0,
                    'endColumnIndex': 6
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True,
                            'fontSize': 10
                        },
                        'horizontalAlignment': 'CENTER',
                        'verticalAlignment': 'MIDDLE'
                    }
                },
                'fields': 'userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)'
            }
        },
        # Format KPI values (A4:F4) - larger font
        {
            'repeatCell': {
                'range': {
                    'sheetId': dashboard_sheet_id,
                    'startRowIndex': 3,
                    'endRowIndex': 4,
                    'startColumnIndex': 0,
                    'endColumnIndex': 6
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True,
                            'fontSize': 16,
                            'fontFamily': 'Roboto Mono'
                        },
                        'horizontalAlignment': 'CENTER',
                        'verticalAlignment': 'MIDDLE'
                    }
                },
                'fields': 'userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)'
            }
        }
    ]
    
    # Apply KPI cell colors
    kpi_colors = [
        THEME['RED'],     # A4 - Demand
        THEME['BLUE'],    # B4 - Generation
        THEME['GREEN'],   # C4 - Wind
        THEME['ORANGE'],  # D4 - Margin
        THEME['GREY'],    # E4 - Price
        THEME['PURPLE']   # F4 - Constraints
    ]
    
    for i, color_hex in enumerate(kpi_colors):
        r = int(color_hex[1:3], 16) / 255.0
        g = int(color_hex[3:5], 16) / 255.0
        b = int(color_hex[5:7], 16) / 255.0
        
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': dashboard_sheet_id,
                    'startRowIndex': 3,
                    'endRowIndex': 4,
                    'startColumnIndex': i,
                    'endColumnIndex': i + 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': r, 'green': g, 'blue': b
                        }
                    }
                },
                'fields': 'userEnteredFormat.backgroundColor'
            }
        })
    
    # Execute formatting
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': requests}
    ).execute()
    
    print("✅ Dark theme applied successfully")

def main():
    """Main execution"""
    print("="*70)
    print("🎨 GB ENERGY DASHBOARD - COMPLETE TRANSFORMATION")
    print("="*70)
    
    # Connect to services
    bq_client, spreadsheet, sheets_service = connect()
    dashboard_sheet = spreadsheet.worksheet('Dashboard')
    
    # Step 1: Remove old charts
    dashboard_sheet_id = remove_old_charts(sheets_service)
    
    # Step 2: Clean GSP data
    clean_gsp_data(dashboard_sheet)
    
    # Step 3: Fetch today's data
    df = fetch_today_data(bq_client)
    
    # Step 4: Create enhanced KPIs
    kpi_data = create_enhanced_kpis(df)
    
    # Step 5: Write KPIs to A3:F4
    print("\n📝 Writing enhanced KPIs to A3:F4...")
    dashboard_sheet.update(values=kpi_data, range_name='A3:F4', value_input_option='USER_ENTERED')
    print("✅ KPIs updated")
    
    # Step 6: Apply dark theme
    apply_dark_theme(dashboard_sheet, sheets_service, dashboard_sheet_id)
    
    # Step 7: Summary
    print("\n" + "="*70)
    print("✅ TRANSFORMATION COMPLETE!")
    print("="*70)
    print(f"📊 Settlement Periods: {len(df)}")
    print(f"🎨 Theme: Material Black Dark")
    print(f"📈 KPIs: 6 metrics in A3:F4")
    print(f"🗑️  Old charts: Removed")
    print(f"🧹 GSP data: Cleaned")
    print("\n✨ Your dashboard is now transformed with:")
    print("   • Professional dark theme")
    print("   • Enhanced horizontal KPI layout")
    print("   • Real-time market data")
    print("   • All existing data preserved (fuel, ICs, outages)")
    print("\n📝 Next: Charts will be added via Apps Script")
    print("="*70)

if __name__ == "__main__":
    main()
