#!/usr/bin/env python3
"""
Daily Dashboard Auto-Updater
Fetches data from SP1 (00:00) each day for:
- System Sell Price (SSP)
- System Buy Price (SBP)
- GB Demand
- Total Generation
- Total Interconnector Imports
- Frequency (average per SP)

Updates Google Sheets with data + auto-generates charts
Runs every 30 minutes via cron
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd
from datetime import datetime, timedelta
import sys

# ==================== CONFIGURATION ====================
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"

# Chart data sheet name
CHART_DATA_SHEET = "Daily_Chart_Data"

# ==================== AUTHENTICATION ====================
def connect():
    """Authenticate with BigQuery and Google Sheets"""
    try:
        # BigQuery
        bq_creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        bq_client = bigquery.Client(
            credentials=bq_creds,
            project=PROJECT_ID,
            location="US"
        )
        
        # Google Sheets
        sheets_creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        gc = gspread.authorize(sheets_creds)
        sh = gc.open_by_key(SPREADSHEET_ID)
        
        print("✅ Connected to BigQuery and Google Sheets")
        return bq_client, sh
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None, None

# ==================== DATA QUERIES ====================
def fetch_daily_data(bq_client, days_back=1):
    """
    Fetch TODAY's data only (current day from 00:00, all 48 settlement periods)
    Returns DataFrame with columns:
    - date
    - settlement_period (1-48)
    - market_price (£/MWh)
    - demand_mw
    - generation_mw
    - interconnector_import_mw
    - frequency_hz
    """
    
    # Get today's date only
    today = datetime.now().date()
    
    print(f"📊 Fetching TODAY's data: {today}")
    
    query = f"""
    WITH 
    -- Market prices (APXMIDP from bmrs_mid_iris - TODAY ONLY)
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
    
    -- GB Demand (TODAY ONLY)
    demand AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            AVG(demand) as demand_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indo_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
        GROUP BY date, sp
    ),
    
    -- Total Generation (TODAY ONLY)
    generation AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            SUM(generation) as generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
        GROUP BY date, sp
    ),
    
    -- Interconnector Flows (negative = import, TODAY ONLY)
    interconnectors AS (
        SELECT
            settlementDate as date,
            settlementPeriod as sp,
            SUM(CASE WHEN generation < 0 THEN ABS(generation) ELSE 0 END) as import_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE fuelType LIKE 'INT%'
          AND settlementDate = CURRENT_DATE('Europe/London')
        GROUP BY date, sp
    ),
    
    -- Frequency (average per SP, TODAY ONLY)
    frequency AS (
        SELECT
            CAST(measurementTime AS DATE) as date,
            CAST(
                EXTRACT(HOUR FROM measurementTime) * 2 + 
                FLOOR(EXTRACT(MINUTE FROM measurementTime) / 30) + 1 
            AS INT64) as sp,
            AVG(frequency) as frequency_hz
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        WHERE CAST(measurementTime AS DATE) = CURRENT_DATE('Europe/London')
        GROUP BY date, sp
    )
    
    -- Join all data sources (TODAY ONLY)
    SELECT
        COALESCE(p.date, d.date, g.date, i.date, f.date) as date,
        COALESCE(p.sp, d.sp, g.sp, i.sp, f.sp) as settlement_period,
        ROUND(COALESCE(p.market_price, 0), 2) as market_price,
        ROUND(COALESCE(d.demand_mw, 0), 0) as demand_mw,
        ROUND(COALESCE(g.generation_mw, 0), 0) as generation_mw,
        ROUND(COALESCE(i.import_mw, 0), 0) as interconnector_import_mw,
        ROUND(COALESCE(f.frequency_hz, 50.0), 3) as frequency_hz
    FROM prices p
    FULL OUTER JOIN demand d USING (date, sp)
    FULL OUTER JOIN generation g USING (date, sp)
    FULL OUTER JOIN interconnectors i USING (date, sp)
    FULL OUTER JOIN frequency f USING (date, sp)
    WHERE COALESCE(p.date, d.date, g.date, i.date, f.date) = CURRENT_DATE('Europe/London')
    ORDER BY settlement_period
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        print(f"✅ Retrieved {len(df)} settlement periods for TODAY ({today})")
        return df
    except Exception as e:
        print(f"❌ Query error: {e}")
        return pd.DataFrame()

# ==================== SHEETS UPDATER ====================
def update_chart_data_sheet(spreadsheet, df):
    """
    Write data to Daily_Chart_Data sheet
    Format: Date | SP | SSP | SBP | Demand | Generation | IC Import | Frequency
    """
    try:
        # Get or create sheet
        try:
            sheet = spreadsheet.worksheet(CHART_DATA_SHEET)
            print(f"📋 Found existing sheet: {CHART_DATA_SHEET}")
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=CHART_DATA_SHEET, rows=2000, cols=10)
            print(f"📋 Created new sheet: {CHART_DATA_SHEET}")
        
        # Prepare data
        df_sorted = df.sort_values(['date', 'settlement_period'])
        
        # Format date column
        df_sorted['date'] = df_sorted['date'].astype(str)
        
        # Headers
        headers = [
            'Date',
            'SP',
            'Market Price (£/MWh)',
            'Demand (MW)',
            'Generation (MW)',
            'IC Import (MW)',
            'Frequency (Hz)'
        ]
        
        # Convert to list format
        data = [headers]
        for _, row in df_sorted.iterrows():
            data.append([
                row['date'],
                int(row['settlement_period']) if pd.notna(row['settlement_period']) else '',
                float(row['market_price']) if pd.notna(row['market_price']) else '',
                int(row['demand_mw']) if pd.notna(row['demand_mw']) else '',
                int(row['generation_mw']) if pd.notna(row['generation_mw']) else '',
                int(row['interconnector_import_mw']) if pd.notna(row['interconnector_import_mw']) else '',
                float(row['frequency_hz']) if pd.notna(row['frequency_hz']) else ''
            ])
        
        # Clear existing data
        sheet.clear()
        
        # Write data (batch update for efficiency)
        sheet.update('A1', data, value_input_option='USER_ENTERED')
        
        # Format header row
        sheet.format('A1:H1', {
            'textFormat': {'bold': True, 'fontSize': 11},
            'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
            'horizontalAlignment': 'CENTER'
        })
        
        # Freeze header row
        sheet.freeze(rows=1)
        
        print(f"✅ Updated {CHART_DATA_SHEET} with {len(data)-1} rows")
        
        # Calculate summary stats (TODAY ONLY)
        total_sp = len(df)
        avg_price = df['market_price'].mean()
        max_price = df['market_price'].max()
        min_price = df['market_price'].min()
        
        print(f"📊 Summary Stats (TODAY):")
        print(f"   • Settlement Periods: {total_sp}")
        print(f"   • Avg Market Price: £{avg_price:.2f}/MWh")
        print(f"   • Max Market Price: £{max_price:.2f}/MWh")
        print(f"   • Min Market Price: £{min_price:.2f}/MWh")
        
        return True
        
    except Exception as e:
        print(f"❌ Sheets update error: {e}")
        return False

def create_summary_kpis(spreadsheet, df):
    """
    Create KPI summary in Dashboard sheet (F7:G17)
    Shows today's key metrics (current day from 00:00)
    """
    try:
        dashboard = spreadsheet.worksheet('Dashboard')
        
        # Calculate TODAY's KPIs (all data is for today)
        avg_price_today = df['market_price'].mean()
        avg_demand_today = df['demand_mw'].mean()
        avg_generation_today = df['generation_mw'].mean()
        avg_import_today = df['interconnector_import_mw'].mean()
        avg_freq_today = df['frequency_hz'].mean()
        
        # Min/max for today
        max_price_today = df['market_price'].max()
        min_price_today = df['market_price'].min()
        max_demand_today = df['demand_mw'].max()
        
        # Create compact KPI layout (F7:G17) - 11 rows
        kpi_data = [
            ['💰 Market Price', f'£{avg_price_today:.2f}/MWh'],  # F7:G7
            ['⚡ Demand', f'{avg_demand_today:,.0f} MW'],  # F8:G8
            ['⚡ Generation', f'{avg_generation_today:,.0f} MW'],  # F9:G9
            ['🔌 IC Import', f'{avg_import_today:,.0f} MW'],  # F10:G10
            ['📊 Frequency', f'{avg_freq_today:.3f} Hz'],  # F11:G11
            ['', ''],  # F12:G12 - spacing
            ['TODAY\'S RANGES', ''],  # F13:G13 - header
            ['Max Price', f'£{max_price_today:.2f}'],  # F14:G14
            ['Min Price', f'£{min_price_today:.2f}'],  # F15:G15
            ['Max Demand', f'{max_demand_today:,.0f} MW'],  # F16:G16
            [f'Updated: {datetime.now().strftime("%H:%M")}', '']  # F17:G17
        ]
        
        # Write to Dashboard (F7:G17)
        dashboard.update('F7:G17', kpi_data, value_input_option='USER_ENTERED')
        
        # Format labels (column F)
        dashboard.format('F7:F17', {
            'textFormat': {'bold': True, 'fontSize': 10},
            'horizontalAlignment': 'RIGHT'
        })
        
        # Format values (column G)
        dashboard.format('G7:G17', {
            'textFormat': {'fontSize': 10},
            'horizontalAlignment': 'LEFT'
        })
        
        # Format 30-day header
        dashboard.format('F13:G13', {
            'textFormat': {'bold': True, 'fontSize': 10},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        print(f"✅ Updated KPIs in Dashboard (F7:G17)")
        return True
        
    except Exception as e:
        print(f"❌ KPI update error: {e}")
        return False

def create_embedded_charts(spreadsheet, data_sheet_id):
    """
    Create 4 embedded charts in Dashboard A18:H29 using Google Sheets API
    Charts display data from Daily_Chart_Data sheet
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        
        # Get credentials from gspread client
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=creds)
        
        # Get sheet IDs
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        dashboard_id = None
        
        print(f"📋 Looking for Dashboard sheet...")
        for sheet in sheet_metadata['sheets']:
            title = sheet['properties']['title']
            sheet_id = sheet['properties']['sheetId']
            if title == 'Dashboard':
                dashboard_id = sheet_id
                print(f"✅ Found Dashboard sheet (ID: {dashboard_id})")
                break
        
        if dashboard_id is None:
            print("❌ Dashboard sheet not found")
            print(f"Available sheets: {[s['properties']['title'] for s in sheet_metadata['sheets'][:5]]}")
            return False
        
        # Delete existing charts in Dashboard
        delete_requests = []
        for sheet in sheet_metadata['sheets']:
            if sheet['properties']['title'] == 'Dashboard':
                if 'charts' in sheet:
                    for chart in sheet.get('charts', []):
                        delete_requests.append({
                            'deleteEmbeddedObject': {
                                'objectId': chart['chartId']
                            }
                        })
        
        if delete_requests:
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'requests': delete_requests}
            ).execute()
            print(f"🗑️  Deleted {len(delete_requests)} existing charts")
        
        # Chart positions in A18:H29 (12 rows x 8 cols = ~600px x 360px each)
        # Grid: 2x2 layout
        # Chart 1 (Price): A18:D23 (rows 17-22, cols 0-3)
        # Chart 2 (Demand): E18:H23 (rows 17-22, cols 4-7)
        # Chart 3 (Import): A24:D29 (rows 23-28, cols 0-3)
        # Chart 4 (Freq): E24:H29 (rows 23-28, cols 4-7)
        
        requests = [
            # 1. Market Price Chart (A18:D23)
            {
                'addChart': {
                    'chart': {
                        'spec': {
                            'title': '💰 Market Price (30d)',
                            'basicChart': {
                                'chartType': 'LINE',
                                'legendPosition': 'BOTTOM_LEGEND',
                                'axis': [
                                    {'position': 'BOTTOM_AXIS', 'title': 'Date'},
                                    {'position': 'LEFT_AXIS', 'title': '£/MWh'}
                                ],
                                'domains': [{
                                    'domain': {'sourceRange': {'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 1
                                    }]}}
                                }],
                                'series': [{
                                    'series': {'sourceRange': {'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'startColumnIndex': 2,
                                        'endColumnIndex': 3
                                    }]}},
                                    'targetAxis': 'LEFT_AXIS'
                                }]
                            }
                        },
                        'position': {
                            'overlayPosition': {
                                'anchorCell': {
                                    'sheetId': dashboard_id,
                                    'rowIndex': 17,
                                    'columnIndex': 0
                                },
                                'widthPixels': 480,
                                'heightPixels': 240
                            }
                        }
                    }
                }
            },
            # 2. Demand Chart (E18:H23)
            {
                'addChart': {
                    'chart': {
                        'spec': {
                            'title': '⚡ Demand (30d)',
                            'basicChart': {
                                'chartType': 'LINE',
                                'legendPosition': 'BOTTOM_LEGEND',
                                'axis': [
                                    {'position': 'BOTTOM_AXIS', 'title': 'Date'},
                                    {'position': 'LEFT_AXIS', 'title': 'MW'}
                                ],
                                'domains': [{
                                    'domain': {'sourceRange': {'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 1
                                    }]}}
                                }],
                                'series': [{
                                    'series': {'sourceRange': {'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'startColumnIndex': 3,
                                        'endColumnIndex': 4
                                    }]}},
                                    'targetAxis': 'LEFT_AXIS'
                                }]
                            }
                        },
                        'position': {
                            'overlayPosition': {
                                'anchorCell': {
                                    'sheetId': dashboard_id,
                                    'rowIndex': 17,
                                    'columnIndex': 4
                                },
                                'widthPixels': 480,
                                'heightPixels': 240
                            }
                        }
                    }
                }
            },
            # 3. IC Import Chart (A24:D29)
            {
                'addChart': {
                    'chart': {
                        'spec': {
                            'title': '🔌 IC Import (30d)',
                            'basicChart': {
                                'chartType': 'AREA',
                                'legendPosition': 'BOTTOM_LEGEND',
                                'axis': [
                                    {'position': 'BOTTOM_AXIS', 'title': 'Date'},
                                    {'position': 'LEFT_AXIS', 'title': 'MW'}
                                ],
                                'domains': [{
                                    'domain': {'sourceRange': {'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 1
                                    }]}}
                                }],
                                'series': [{
                                    'series': {'sourceRange': {'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'startColumnIndex': 5,
                                        'endColumnIndex': 6
                                    }]}},
                                    'targetAxis': 'LEFT_AXIS'
                                }]
                            }
                        },
                        'position': {
                            'overlayPosition': {
                                'anchorCell': {
                                    'sheetId': dashboard_id,
                                    'rowIndex': 23,
                                    'columnIndex': 0
                                },
                                'widthPixels': 480,
                                'heightPixels': 240
                            }
                        }
                    }
                }
            },
            # 4. Frequency Chart (E24:H29)
            {
                'addChart': {
                    'chart': {
                        'spec': {
                            'title': '📊 Frequency (30d)',
                            'basicChart': {
                                'chartType': 'LINE',
                                'legendPosition': 'BOTTOM_LEGEND',
                                'axis': [
                                    {'position': 'BOTTOM_AXIS', 'title': 'Date'},
                                    {'position': 'LEFT_AXIS', 'title': 'Hz'}
                                ],
                                'domains': [{
                                    'domain': {'sourceRange': {'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 1
                                    }]}}
                                }],
                                'series': [{
                                    'series': {'sourceRange': {'sources': [{
                                        'sheetId': data_sheet_id,
                                        'startRowIndex': 1,
                                        'startColumnIndex': 6,
                                        'endColumnIndex': 7
                                    }]}},
                                    'targetAxis': 'LEFT_AXIS'
                                }]
                            }
                        },
                        'position': {
                            'overlayPosition': {
                                'anchorCell': {
                                    'sheetId': dashboard_id,
                                    'rowIndex': 23,
                                    'columnIndex': 4
                                },
                                'widthPixels': 480,
                                'heightPixels': 240
                            }
                        }
                    }
                }
            }
        ]
        
        # Execute batch update to create all 4 charts
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': requests}
        ).execute()
        
        print(f"✅ Created 4 embedded charts in Dashboard (A18:H29)")
        return True
        
    except Exception as e:
        print(f"❌ Chart creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== MAIN EXECUTION ====================
def main():
    """Main execution"""
    print("=" * 80)
    print("🔄 DAILY DASHBOARD AUTO-UPDATER")
    print("=" * 80)
    print(f"⏰ Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Connect
    bq_client, spreadsheet = connect()
    if not bq_client or not spreadsheet:
        sys.exit(1)
    
    # Fetch data (TODAY ONLY)
    df = fetch_daily_data(bq_client, days_back=1)
    if df.empty:
        print("❌ No data retrieved")
        sys.exit(1)
    
    # Update sheets
    success = update_chart_data_sheet(spreadsheet, df)
    if not success:
        print("❌ Failed to update chart data")
        sys.exit(1)
    
    # Update KPIs
    create_summary_kpis(spreadsheet, df)
    
    # Get Daily_Chart_Data sheet ID for chart creation
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
    
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=creds)
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    
    data_sheet_id = None
    for sheet in sheet_metadata['sheets']:
        if sheet['properties']['title'] == CHART_DATA_SHEET:
            data_sheet_id = sheet['properties']['sheetId']
            break
    
    if data_sheet_id:
        create_embedded_charts(spreadsheet, data_sheet_id)
    else:
        print("⚠️  Could not find data sheet ID for chart creation")
    
    print()
    print("=" * 80)
    print("✅ UPDATE COMPLETE")
    print("=" * 80)
    print(f"📊 TODAY's Data: {datetime.now().date()} | KPIs: F7:G17 | Charts: A18:H29")
    print(f"🔄 Next update: 30 minutes")

if __name__ == "__main__":
    main()
