#!/usr/bin/env python3
"""
Dashboard Complete Fix - Addressing All Issues
1. Remove GSP data from H57:K75
2. Change all charts to TODAY ONLY (intraday, not 48h)
3. Replace pie chart with stacked column chart
4. Move charts to separate "Charts" sheet to not overlay data
5. Clarify chart titles and metrics
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
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"

def connect():
    """Connect to all services"""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/cloud-platform'
        ]
    )
    
    bq_client = bigquery.Client(credentials=creds, project=PROJECT_ID, location="US")
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    return bq_client, sh, sheets_service

def remove_gsp_data_completely(dashboard_sheet, sheets_service, dashboard_sheet_id):
    """Completely remove GSP data from H57:K75"""
    print("\n🧹 Removing GSP data from H57:K75...")
    
    # Clear the range
    dashboard_sheet.batch_clear(['H57:K75'])
    
    # Also clear any formatting
    requests = [{
        'updateCells': {
            'range': {
                'sheetId': dashboard_sheet_id,
                'startRowIndex': 56,  # Row 57 (0-indexed)
                'endRowIndex': 75,    # Row 75
                'startColumnIndex': 7,  # Column H (0-indexed)
                'endColumnIndex': 11    # Column K
            },
            'fields': '*'
        }
    }]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': requests}
    ).execute()
    
    print("✅ GSP data completely removed from H57:K75")

def delete_all_charts(sheets_service, dashboard_sheet_id):
    """Delete all embedded charts from Dashboard"""
    print("\n🗑️  Deleting all existing charts...")
    
    result = sheets_service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        includeGridData=False
    ).execute()
    
    chart_ids = []
    for sheet in result['sheets']:
        if sheet['properties']['sheetId'] == dashboard_sheet_id:
            if 'charts' in sheet:
                chart_ids = [chart['chartId'] for chart in sheet['charts']]
            break
    
    if chart_ids:
        requests = [{'deleteEmbeddedObject': {'objectId': cid}} for cid in chart_ids]
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': requests}
        ).execute()
        print(f"✅ Deleted {len(chart_ids)} charts")
    else:
        print("✅ No charts to delete")

def fetch_intraday_data(bq_client):
    """Fetch TODAY ONLY (intraday) data"""
    print(f"\n📊 Fetching TODAY's intraday data from BigQuery...")
    
    query = f"""
    WITH 
    -- Market prices (TODAY only)
    prices AS (
        SELECT
            settlementDate,
            settlementPeriod,
            AVG(price) as market_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
          AND dataProvider = 'APXMIDP'
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- GB Demand (TODAY only)
    demand AS (
        SELECT
            settlementDate,
            settlementPeriod,
            AVG(demand) as demand_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indo_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- Total Generation (TODAY only)
    generation AS (
        SELECT
            settlementDate,
            settlementPeriod,
            SUM(generation) as generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = CURRENT_DATE('Europe/London')
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- Frequency (TODAY only)
    frequency AS (
        SELECT
            CAST(measurementTime AS DATE) as settlementDate,
            EXTRACT(HOUR FROM measurementTime) * 2 + 
            CAST(FLOOR(EXTRACT(MINUTE FROM measurementTime) / 30) AS INT64) + 1 as settlementPeriod,
            AVG(frequency) as frequency_hz
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        WHERE CAST(measurementTime AS DATE) = CURRENT_DATE('Europe/London')
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- System Balancing Actions (TODAY only)
    balancing AS (
        SELECT
            CAST(settlementDate AS DATE) as settlementDate,
            settlementPeriod,
            COUNT(*) as balancing_actions
        FROM `{PROJECT_ID}.{DATASET}.bmrs_bod_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE('Europe/London')
        GROUP BY settlementDate, settlementPeriod
    )
    
    SELECT
        p.settlementDate as date,
        p.settlementPeriod as sp,
        COALESCE(p.market_price, 0) as market_price,
        COALESCE(d.demand_mw, 0) as demand_mw,
        COALESCE(g.generation_mw, 0) as generation_mw,
        COALESCE(f.frequency_hz, 50.0) as frequency_hz,
        COALESCE(b.balancing_actions, 0) as balancing_actions
    FROM prices p
    LEFT JOIN demand d ON p.settlementDate = d.settlementDate AND p.settlementPeriod = d.settlementPeriod
    LEFT JOIN generation g ON p.settlementDate = g.settlementDate AND p.settlementPeriod = g.settlementPeriod
    LEFT JOIN frequency f ON p.settlementDate = f.settlementDate AND p.settlementPeriod = f.settlementPeriod
    LEFT JOIN balancing b ON p.settlementDate = b.settlementDate AND p.settlementPeriod = b.settlementPeriod
    ORDER BY p.settlementPeriod
    """
    
    df = bq_client.query(query).to_dataframe()
    
    # Fuel type query for TODAY
    fuel_query = f"""
    SELECT
        fuelType,
        SUM(generation) as total_generation_mwh
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE settlementDate = CURRENT_DATE('Europe/London')
    GROUP BY fuelType
    ORDER BY total_generation_mwh DESC
    """
    
    fuel_df = bq_client.query(fuel_query).to_dataframe()
    
    print(f"✅ Retrieved {len(df)} settlement periods for TODAY")
    print(f"✅ Retrieved {len(fuel_df)} fuel types for TODAY")
    return df, fuel_df

def update_chart_data_sheet_intraday(main_df, fuel_df, spreadsheet):
    """Update Daily_Chart_Data with TODAY ONLY data"""
    print("\n📝 Updating Intraday_Chart_Data sheet...")
    
    try:
        chart_sheet = spreadsheet.worksheet('Intraday_Chart_Data')
        chart_sheet.clear()
    except:
        chart_sheet = spreadsheet.add_worksheet('Intraday_Chart_Data', rows=100, cols=15)
    
    # Main time-series data for TODAY
    main_df['datetime'] = pd.to_datetime(main_df['date'].astype(str) + ' ' + 
                                          ((main_df['sp'] - 1) * 0.5).apply(lambda x: f"{int(x):02d}:{int((x % 1) * 60):02d}"))
    
    # Format data
    main_data = [['Datetime', 'Settlement Period', 'Market Price £/MWh', 'Demand MW', 'Generation MW', 'Frequency Hz', 'Balancing Actions']]
    for _, row in main_df.iterrows():
        main_data.append([
            row['datetime'].strftime('%H:%M'),
            int(row['sp']),
            float(row['market_price']) if pd.notna(row['market_price']) else 0,
            float(row['demand_mw']) if pd.notna(row['demand_mw']) else 0,
            float(row['generation_mw']) if pd.notna(row['generation_mw']) else 0,
            float(row['frequency_hz']) if pd.notna(row['frequency_hz']) else 50.0,
            int(row['balancing_actions']) if pd.notna(row['balancing_actions']) else 0
        ])
    
    # Write main data
    chart_sheet.update(values=main_data, range_name=f'A1:G{len(main_data)}')
    
    # Fuel mix data starting at I1
    fuel_data = [['Fuel Type', 'Generation MWh']]
    for _, row in fuel_df.iterrows():
        fuel_data.append([row['fuelType'], float(row['total_generation_mwh'])])
    
    chart_sheet.update(values=fuel_data, range_name=f'I1:J{len(fuel_data)}')
    
    print(f"✅ Updated Intraday_Chart_Data: {len(main_data)-1} periods, {len(fuel_data)-1} fuel types")
    return len(main_data)-1, len(fuel_data)-1

def create_charts_sheet(spreadsheet, sheets_service):
    """Create or get Charts sheet for embedded charts"""
    print("\n📊 Setting up Charts sheet...")
    
    try:
        charts_sheet = spreadsheet.worksheet('Charts')
        print("✅ Using existing Charts sheet")
    except:
        charts_sheet = spreadsheet.add_worksheet('Charts', rows=100, cols=10)
        print("✅ Created new Charts sheet")
    
    # Get sheet ID
    result = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    charts_sheet_id = None
    chart_data_sheet_id = None
    
    for sheet in result['sheets']:
        if sheet['properties']['title'] == 'Charts':
            charts_sheet_id = sheet['properties']['sheetId']
        elif sheet['properties']['title'] == 'Intraday_Chart_Data':
            chart_data_sheet_id = sheet['properties']['sheetId']
    
    return charts_sheet_id, chart_data_sheet_id

def create_intraday_charts(sheets_service, charts_sheet_id, chart_data_sheet_id, num_periods):
    """Create 4 charts using TODAY's intraday data only - NO PIE CHARTS"""
    print("\n📊 Creating intraday charts (TODAY only)...")
    
    requests = []
    
    # Chart 1: Market Price & Frequency (Dual-Axis) - A1:E25
    requests.append({
        'addChart': {
            'chart': {
                'spec': {
                    'title': '💷 Market Price & Grid Frequency (Intraday)',
                    'subtitle': 'Today\'s half-hourly data',
                    'basicChart': {
                        'chartType': 'COMBO',
                        'legendPosition': 'BOTTOM_LEGEND',
                        'axis': [
                            {'position': 'BOTTOM_AXIS', 'title': 'Time'},
                            {'position': 'LEFT_AXIS', 'title': 'Price (£/MWh)'},
                            {'position': 'RIGHT_AXIS', 'title': 'Frequency (Hz)'}
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': chart_data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': num_periods + 1,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 1
                                    }]
                                }
                            }
                        }],
                        'series': [
                            {
                                'series': {
                                    'sourceRange': {
                                        'sources': [{
                                            'sheetId': chart_data_sheet_id,
                                            'startRowIndex': 1,
                                            'endRowIndex': num_periods + 1,
                                            'startColumnIndex': 2,
                                            'endColumnIndex': 3
                                        }]
                                    }
                                },
                                'targetAxis': 'LEFT_AXIS',
                                'type': 'LINE',
                                'color': {'red': 0.58, 'green': 0.61, 'blue': 0.61}
                            },
                            {
                                'series': {
                                    'sourceRange': {
                                        'sources': [{
                                            'sheetId': chart_data_sheet_id,
                                            'startRowIndex': 1,
                                            'endRowIndex': num_periods + 1,
                                            'startColumnIndex': 5,
                                            'endColumnIndex': 6
                                        }]
                                    }
                                },
                                'targetAxis': 'RIGHT_AXIS',
                                'type': 'LINE',
                                'color': {'red': 0.26, 'green': 0.63, 'blue': 0.28}
                            }
                        ]
                    },
                    'backgroundColor': {'red': 0.07, 'green': 0.07, 'blue': 0.07}
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': charts_sheet_id,
                            'rowIndex': 0,
                            'columnIndex': 0
                        }
                    }
                }
            }
        }
    })
    
    # Chart 2: Demand vs Generation (Line Comparison) - F1:J25
    requests.append({
        'addChart': {
            'chart': {
                'spec': {
                    'title': '⚡ GB Demand vs Generation (Intraday)',
                    'subtitle': 'Real-time supply/demand balance',
                    'basicChart': {
                        'chartType': 'LINE',
                        'legendPosition': 'BOTTOM_LEGEND',
                        'axis': [
                            {'position': 'BOTTOM_AXIS', 'title': 'Time'},
                            {'position': 'LEFT_AXIS', 'title': 'MW'}
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': chart_data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': num_periods + 1,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 1
                                    }]
                                }
                            }
                        }],
                        'series': [
                            {
                                'series': {
                                    'sourceRange': {
                                        'sources': [{
                                            'sheetId': chart_data_sheet_id,
                                            'startRowIndex': 1,
                                            'endRowIndex': num_periods + 1,
                                            'startColumnIndex': 3,
                                            'endColumnIndex': 4
                                        }]
                                    }
                                },
                                'type': 'LINE',
                                'color': {'red': 0.90, 'green': 0.22, 'blue': 0.21}
                            },
                            {
                                'series': {
                                    'sourceRange': {
                                        'sources': [{
                                            'sheetId': chart_data_sheet_id,
                                            'startRowIndex': 1,
                                            'endRowIndex': num_periods + 1,
                                            'startColumnIndex': 4,
                                            'endColumnIndex': 5
                                        }]
                                    }
                                },
                                'type': 'LINE',
                                'color': {'red': 0.12, 'green': 0.53, 'blue': 0.90}
                            }
                        ]
                    },
                    'backgroundColor': {'red': 0.07, 'green': 0.07, 'blue': 0.07}
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': charts_sheet_id,
                            'rowIndex': 0,
                            'columnIndex': 5
                        }
                    }
                }
            }
        }
    })
    
    # Chart 3: Fuel Mix (Stacked Column - NO PIE) - A27:E50
    requests.append({
        'addChart': {
            'chart': {
                'spec': {
                    'title': '🔥 Generation by Fuel Type (Intraday)',
                    'subtitle': 'Today\'s total generation mix (MWh)',
                    'basicChart': {
                        'chartType': 'COLUMN',
                        'legendPosition': 'RIGHT_LEGEND',
                        'stackedType': 'STACKED',
                        'axis': [
                            {'position': 'BOTTOM_AXIS', 'title': 'Fuel Type'},
                            {'position': 'LEFT_AXIS', 'title': 'Generation (MWh)'}
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': chart_data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': 25,
                                        'startColumnIndex': 8,
                                        'endColumnIndex': 9
                                    }]
                                }
                            }
                        }],
                        'series': [{
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': chart_data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': 25,
                                        'startColumnIndex': 9,
                                        'endColumnIndex': 10
                                    }]
                                }
                            },
                            'type': 'COLUMN'
                        }]
                    },
                    'backgroundColor': {'red': 0.07, 'green': 0.07, 'blue': 0.07}
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': charts_sheet_id,
                            'rowIndex': 26,
                            'columnIndex': 0
                        }
                    }
                }
            }
        }
    })
    
    # Chart 4: System Balancing Actions (Column) - F27:J50
    requests.append({
        'addChart': {
            'chart': {
                'spec': {
                    'title': '⚖️ Balancing Actions by Period (Intraday)',
                    'subtitle': 'Number of balancing market actions',
                    'basicChart': {
                        'chartType': 'COLUMN',
                        'legendPosition': 'BOTTOM_LEGEND',
                        'axis': [
                            {'position': 'BOTTOM_AXIS', 'title': 'Time'},
                            {'position': 'LEFT_AXIS', 'title': 'Number of Actions'}
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': chart_data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': num_periods + 1,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 1
                                    }]
                                }
                            }
                        }],
                        'series': [{
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': chart_data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': num_periods + 1,
                                        'startColumnIndex': 6,
                                        'endColumnIndex': 7
                                    }]
                                }
                            },
                            'type': 'COLUMN',
                            'color': {'red': 0.56, 'green': 0.14, 'blue': 0.67}
                        }]
                    },
                    'backgroundColor': {'red': 0.07, 'green': 0.07, 'blue': 0.07}
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': charts_sheet_id,
                            'rowIndex': 26,
                            'columnIndex': 5
                        }
                    }
                }
            }
        }
    })
    
    # Execute all chart creation
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': requests}
    ).execute()
    
    print("✅ Created 4 intraday charts on separate Charts sheet")

def main():
    """Main execution"""
    print("=" * 70)
    print("🔧 DASHBOARD COMPLETE FIX")
    print("=" * 70)
    
    # Connect
    bq_client, spreadsheet, sheets_service = connect()
    dashboard_sheet = spreadsheet.worksheet('Dashboard')
    
    # Get Dashboard sheet ID
    result = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    dashboard_sheet_id = None
    for sheet in result['sheets']:
        if sheet['properties']['title'] == 'Dashboard':
            dashboard_sheet_id = sheet['properties']['sheetId']
            break
    
    # Step 1: Remove GSP data from H57:K75
    remove_gsp_data_completely(dashboard_sheet, sheets_service, dashboard_sheet_id)
    
    # Step 2: Delete all existing charts from Dashboard
    delete_all_charts(sheets_service, dashboard_sheet_id)
    
    # Step 3: Fetch TODAY's intraday data
    main_df, fuel_df = fetch_intraday_data(bq_client)
    
    # Step 4: Update chart data sheet with intraday data
    num_periods, num_fuels = update_chart_data_sheet_intraday(main_df, fuel_df, spreadsheet)
    
    # Step 5: Create Charts sheet
    charts_sheet_id, chart_data_sheet_id = create_charts_sheet(spreadsheet, sheets_service)
    
    # Step 6: Create charts on separate sheet (not overlaying data)
    create_intraday_charts(sheets_service, charts_sheet_id, chart_data_sheet_id, num_periods)
    
    print("\n" + "=" * 70)
    print("✅ ALL FIXES COMPLETE!")
    print("=" * 70)
    print(f"🧹 GSP data removed from H57:K75")
    print(f"📊 {num_periods} intraday periods (TODAY only)")
    print(f"🔥 {num_fuels} fuel types")
    print(f"📈 4 charts created on 'Charts' sheet (NO overlap)")
    print(f"🚫 NO pie charts (replaced with column chart)")
    print(f"✅ All charts show INTRADAY data (not 48h)")
    print("=" * 70)

if __name__ == "__main__":
    main()
