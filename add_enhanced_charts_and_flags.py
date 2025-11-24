#!/usr/bin/env python3
"""
Add Enhanced Charts and Interconnector Flags to Dashboard
- Creates 4 professional charts with live data
- Adds flag emojis to interconnector rows
- Sets up proper positioning (A6:G60)
"""

from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"

# Interconnector flag mapping
IC_FLAGS = {
    'IFA': '🇫🇷 France',
    'IFA2': '🇫🇷 France',
    'ELECLINK': '🇫🇷 France',
    'NEMO': '🇧🇪 Belgium',
    'BRITNED': '🇳🇱 Netherlands',
    'MOYLE': '🇮🇪 N. Ireland',
    'EWIC': '🇮🇪 Ireland',
    'NSL': '🇳🇴 Norway',
    'VIKING': '🇩🇰 Denmark'
}

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

def add_interconnector_flags(dashboard_sheet):
    """Add flag emojis to interconnector rows"""
    print("\n🚩 Adding interconnector flags...")
    
    all_values = dashboard_sheet.get_all_values()
    updates = []
    
    for i, row in enumerate(all_values, 1):
        if len(row) > 0:
            cell_text = row[0].upper().strip()
            
            # Check each IC name
            for ic_key, ic_label in IC_FLAGS.items():
                if ic_key in cell_text:
                    # Update the cell with flag
                    original_text = row[0]
                    # Remove existing flags first
                    for flag_label in IC_FLAGS.values():
                        original_text = original_text.replace(flag_label, '').strip()
                    
                    new_text = f"{ic_label} {original_text.replace(ic_key, '').strip()}"
                    updates.append({
                        'range': f'A{i}',
                        'values': [[new_text]]
                    })
                    print(f"   • Row {i}: {ic_key} → {ic_label}")
                    break
    
    if updates:
        dashboard_sheet.batch_update(updates, value_input_option='USER_ENTERED')
        print(f"✅ Added {len(updates)} interconnector flags")
    else:
        print("✅ No interconnector rows found (may be in different sheet)")

def fetch_chart_data(bq_client):
    """Fetch data for all 4 charts"""
    print("\n📊 Fetching chart data from BigQuery...")
    
    query = f"""
    WITH 
    -- Combined historical + real-time data (last 48 hours)
    combined_data AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            price,
            'HISTORICAL' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE('Europe/London'), INTERVAL 2 DAY)
          AND dataProvider = 'APXMIDP'
        
        UNION ALL
        
        SELECT 
            settlementDate,
            settlementPeriod,
            price,
            'IRIS' as source
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE('Europe/London'), INTERVAL 2 DAY)
          AND dataProvider = 'APXMIDP'
    ),
    
    -- Demand
    demand AS (
        SELECT
            settlementDate,
            settlementPeriod,
            AVG(demand) as demand_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indo_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE('Europe/London'), INTERVAL 2 DAY)
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- Generation by fuel type
    generation AS (
        SELECT
            settlementDate,
            settlementPeriod,
            fuelType,
            SUM(generation) as generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE('Europe/London'), INTERVAL 2 DAY)
        GROUP BY settlementDate, settlementPeriod, fuelType
    ),
    
    -- Frequency
    frequency AS (
        SELECT
            CAST(measurementTime AS DATE) as settlementDate,
            EXTRACT(HOUR FROM measurementTime) * 2 + 
            CAST(FLOOR(EXTRACT(MINUTE FROM measurementTime) / 30) AS INT64) + 1 as settlementPeriod,
            AVG(frequency) as frequency_hz
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        WHERE CAST(measurementTime AS DATE) >= DATE_SUB(CURRENT_DATE('Europe/London'), INTERVAL 2 DAY)
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- Constraints
    constraints AS (
        SELECT
            CAST(settlementDate AS DATE) as settlementDate,
            settlementPeriod,
            SUM(ABS(COALESCE(offer, 0)) + ABS(COALESCE(bid, 0))) / 100 as constraint_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_bod_iris`
        WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE('Europe/London'), INTERVAL 2 DAY)
        GROUP BY settlementDate, settlementPeriod
    )
    
    SELECT
        p.settlementDate as date,
        p.settlementPeriod as sp,
        AVG(p.price) as market_price,
        AVG(d.demand_mw) as demand_mw,
        AVG(f.frequency_hz) as frequency_hz,
        AVG(c.constraint_mw) as constraint_mw
    FROM combined_data p
    LEFT JOIN demand d ON p.settlementDate = d.settlementDate AND p.settlementPeriod = d.settlementPeriod
    LEFT JOIN frequency f ON p.settlementDate = f.settlementDate AND p.settlementPeriod = f.settlementPeriod
    LEFT JOIN constraints c ON p.settlementDate = c.settlementDate AND p.settlementPeriod = c.settlementPeriod
    GROUP BY p.settlementDate, p.settlementPeriod
    ORDER BY p.settlementDate, p.settlementPeriod
    """
    
    df = bq_client.query(query).to_dataframe()
    
    # Fuel type query for pie chart
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
    
    print(f"✅ Retrieved {len(df)} settlement periods, {len(fuel_df)} fuel types")
    return df, fuel_df

def update_chart_data_sheet(main_df, fuel_df, spreadsheet):
    """Update Daily_Chart_Data sheet with latest data"""
    print("\n📝 Updating Daily_Chart_Data sheet...")
    
    try:
        chart_sheet = spreadsheet.worksheet('Daily_Chart_Data')
    except:
        chart_sheet = spreadsheet.add_worksheet('Daily_Chart_Data', rows=200, cols=15)
    
    # Clear existing data
    chart_sheet.clear()
    
    # Main time-series data
    main_df['datetime'] = pd.to_datetime(main_df['date'].astype(str) + ' ' + 
                                          ((main_df['sp'] - 1) * 0.5).apply(lambda x: f"{int(x):02d}:{int((x % 1) * 60):02d}"))
    
    main_data = [['Datetime', 'Market Price £/MWh', 'Demand MW', 'Frequency Hz', 'Constraint MW']]
    for _, row in main_df.iterrows():
        main_data.append([
            row['datetime'].strftime('%Y-%m-%d %H:%M'),
            float(row['market_price']) if pd.notna(row['market_price']) else 0,
            float(row['demand_mw']) if pd.notna(row['demand_mw']) else 0,
            float(row['frequency_hz']) if pd.notna(row['frequency_hz']) else 50.0,
            float(row['constraint_mw']) if pd.notna(row['constraint_mw']) else 0
        ])
    
    # Write main data starting at A1
    chart_sheet.update(values=main_data, range_name=f'A1:E{len(main_data)}')
    
    # Fuel mix data starting at G1
    fuel_data = [['Fuel Type', 'Generation MWh']]
    for _, row in fuel_df.iterrows():
        fuel_data.append([row['fuelType'], float(row['total_generation_mwh'])])
    
    chart_sheet.update(values=fuel_data, range_name=f'G1:H{len(fuel_data)}')
    
    print(f"✅ Updated Daily_Chart_Data: {len(main_data)-1} rows, {len(fuel_data)-1} fuel types")

def create_enhanced_charts(sheets_service, dashboard_sheet_id):
    """Create 4 enhanced charts on Dashboard"""
    print("\n📊 Creating enhanced charts...")
    
    # Get Daily_Chart_Data sheet ID
    spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    chart_data_sheet_id = None
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == 'Daily_Chart_Data':
            chart_data_sheet_id = sheet['properties']['sheetId']
            break
    
    if not chart_data_sheet_id:
        print("❌ Daily_Chart_Data sheet not found!")
        return
    
    requests = []
    
    # Chart 1: Price & Frequency (Dual-Axis Combo) - A6:G18
    requests.append({
        'addChart': {
            'chart': {
                'spec': {
                    'title': '💷 Market Price & Grid Frequency (48h)',
                    'basicChart': {
                        'chartType': 'COMBO',
                        'legendPosition': 'BOTTOM_LEGEND',
                        'axis': [
                            {
                                'position': 'BOTTOM_AXIS',
                                'title': 'Time'
                            },
                            {
                                'position': 'LEFT_AXIS',
                                'title': 'Price (£/MWh)'
                            },
                            {
                                'position': 'RIGHT_AXIS',
                                'title': 'Frequency (Hz)'
                            }
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': chart_data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': 200,
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
                                            'endRowIndex': 200,
                                            'startColumnIndex': 1,
                                            'endColumnIndex': 2
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
                                            'endRowIndex': 200,
                                            'startColumnIndex': 3,
                                            'endColumnIndex': 4
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
                            'sheetId': dashboard_sheet_id,
                            'rowIndex': 5,
                            'columnIndex': 0
                        }
                    }
                }
            }
        }
    })
    
    # Chart 2: Demand & Constraints (Stacked Area) - A20:G32
    requests.append({
        'addChart': {
            'chart': {
                'spec': {
                    'title': '⚡ GB Demand & System Constraints (48h)',
                    'basicChart': {
                        'chartType': 'AREA',
                        'legendPosition': 'BOTTOM_LEGEND',
                        'stackedType': 'STACKED',
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
                                        'endRowIndex': 200,
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
                                            'endRowIndex': 200,
                                            'startColumnIndex': 2,
                                            'endColumnIndex': 3
                                        }]
                                    }
                                },
                                'type': 'AREA',
                                'color': {'red': 0.90, 'green': 0.22, 'blue': 0.21}
                            },
                            {
                                'series': {
                                    'sourceRange': {
                                        'sources': [{
                                            'sheetId': chart_data_sheet_id,
                                            'startRowIndex': 1,
                                            'endRowIndex': 200,
                                            'startColumnIndex': 4,
                                            'endColumnIndex': 5
                                        }]
                                    }
                                },
                                'type': 'AREA',
                                'color': {'red': 0.56, 'green': 0.14, 'blue': 0.67}
                            }
                        ]
                    },
                    'backgroundColor': {'red': 0.07, 'green': 0.07, 'blue': 0.07}
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': dashboard_sheet_id,
                            'rowIndex': 19,
                            'columnIndex': 0
                        }
                    }
                }
            }
        }
    })
    
    # Chart 3: Fuel Mix (Pie) - A34:G46
    requests.append({
        'addChart': {
            'chart': {
                'spec': {
                    'title': '🔥 GB Generation Mix (Today)',
                    'pieChart': {
                        'legendPosition': 'RIGHT_LEGEND',
                        'domain': {
                            'sourceRange': {
                                'sources': [{
                                    'sheetId': chart_data_sheet_id,
                                    'startRowIndex': 1,
                                    'endRowIndex': 50,
                                    'startColumnIndex': 6,
                                    'endColumnIndex': 7
                                }]
                            }
                        },
                        'series': {
                            'sourceRange': {
                                'sources': [{
                                    'sheetId': chart_data_sheet_id,
                                    'startRowIndex': 1,
                                    'endRowIndex': 50,
                                    'startColumnIndex': 7,
                                    'endColumnIndex': 8
                                }]
                            }
                        },
                        'threeDimensional': False
                    },
                    'backgroundColor': {'red': 0.07, 'green': 0.07, 'blue': 0.07}
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': dashboard_sheet_id,
                            'rowIndex': 33,
                            'columnIndex': 0
                        }
                    }
                }
            }
        }
    })
    
    # Chart 4: Demand Trend (Line) - A48:G60
    requests.append({
        'addChart': {
            'chart': {
                'spec': {
                    'title': '📈 GB Demand Trend (48h)',
                    'basicChart': {
                        'chartType': 'LINE',
                        'legendPosition': 'BOTTOM_LEGEND',
                        'axis': [
                            {'position': 'BOTTOM_AXIS', 'title': 'Time'},
                            {'position': 'LEFT_AXIS', 'title': 'Demand (MW)'}
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': chart_data_sheet_id,
                                        'startRowIndex': 1,
                                        'endRowIndex': 200,
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
                                        'endRowIndex': 200,
                                        'startColumnIndex': 2,
                                        'endColumnIndex': 3
                                    }]
                                }
                            },
                            'type': 'LINE',
                            'color': {'red': 0.12, 'green': 0.53, 'blue': 0.90}
                        }]
                    },
                    'backgroundColor': {'red': 0.07, 'green': 0.07, 'blue': 0.07}
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': dashboard_sheet_id,
                            'rowIndex': 47,
                            'columnIndex': 0
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
    
    print("✅ Created 4 enhanced charts successfully")

def main():
    """Main execution"""
    print("="*70)
    print("📊 ENHANCED CHARTS & INTERCONNECTOR FLAGS")
    print("="*70)
    
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
    
    # Step 1: Add interconnector flags
    add_interconnector_flags(dashboard_sheet)
    
    # Step 2: Fetch data
    main_df, fuel_df = fetch_chart_data(bq_client)
    
    # Step 3: Update chart data sheet
    update_chart_data_sheet(main_df, fuel_df, spreadsheet)
    
    # Step 4: Create charts
    create_enhanced_charts(sheets_service, dashboard_sheet_id)
    
    print("\n" + "="*70)
    print("✅ ENHANCEMENT COMPLETE!")
    print("="*70)
    print("📊 4 enhanced charts created (A6:G60)")
    print("🚩 Interconnector flags added")
    print("📈 Chart data updated (48h history)")
    print("="*70)

if __name__ == "__main__":
    main()
