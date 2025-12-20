#!/usr/bin/env python3
"""
Upload VTP Revenue Simulation Results to Google Sheets
Adds VTP revenue analysis to GB Energy Dashboard
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client():
    """Initialize Google Sheets client"""
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=SCOPES
    )
    return gspread.authorize(creds)

def create_or_clear_worksheet(gc, spreadsheet, sheet_name, rows=1000, cols=26):
    """Create new worksheet or clear existing one"""
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        worksheet.clear()
        print(f"   Cleared existing sheet: {sheet_name}")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=rows, cols=cols)
        print(f"   Created new sheet: {sheet_name}")
    return worksheet

def format_currency(worksheet, range_str):
    """Apply currency formatting to range"""
    worksheet.format(range_str, {
        "numberFormat": {
            "type": "CURRENCY",
            "pattern": "£#,##0.00"
        }
    })

def format_header(worksheet, range_str):
    """Apply header formatting"""
    worksheet.format(range_str, {
        "backgroundColor": {"red": 0.2, "green": 0.3, "blue": 0.5},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        "horizontalAlignment": "CENTER"
    })

def upload_daily_data(gc, spreadsheet):
    """Upload daily VTP revenue data"""
    print("\n📊 Uploading daily VTP revenue data...")

    # Read CSV
    df_daily = pd.read_csv('vtp_revenue_daily.csv')

    # Create/clear worksheet
    ws = create_or_clear_worksheet(gc, spreadsheet, "VTP_Revenue_Daily", rows=100, cols=10)

    # Add title and metadata
    ws.update('A1', [['VIRTUAL TRADING POSITION (VTP) REVENUE - DAILY ANALYSIS']])
    ws.update('A2', [[f'Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])
    ws.update('A3', [['']])
    ws.update('A4', [['Analysis Period: November 2025 | SCRP: £98.00/MWh | ΔQ: 5.0 MWh | Efficiency: 90%']])
    ws.update('A5', [['']])

    # Add column headers
    headers = [
        'Settlement Date',
        'System State',
        'Avg SBP (£/MWh)',
        'Avg SSP (£/MWh)',
        'Avg MID (£/MWh)',
        'Gross VTP Revenue (£)',
        'Net Revenue (£)'
    ]
    ws.update('A6', [headers])

    # Format data for upload
    data = []
    for _, row in df_daily.iterrows():
        data.append([
            row['settlementDate'],
            row['system_state'],
            round(row['avg_SBP'], 2),
            round(row['avg_SSP'], 2),
            round(row['avg_MID'], 2),
            round(row['total_vtp_revenue'], 2),
            round(row['net_revenue'], 2)
        ])

    # Upload data
    ws.update('A7', data)

    # Apply formatting
    format_header(ws, 'A1:G1')
    format_header(ws, 'A6:G6')
    format_currency(ws, 'C7:G' + str(6 + len(data)))

    # Add summary statistics at bottom
    summary_row = 6 + len(data) + 2
    ws.update(f'A{summary_row}', [['SUMMARY STATISTICS']])
    ws.update(f'A{summary_row+1}', [
        ['Total Gross Revenue:', f'=SUM(F7:F{6+len(data)})'],
        ['Total Net Revenue:', f'=SUM(G7:G{6+len(data)})'],
        ['Average Daily Net Revenue:', f'=AVERAGE(G7:G{6+len(data)})'],
        ['Peak Daily Revenue:', f'=MAX(G7:G{6+len(data)})'],
        ['Lowest Daily Revenue:', f'=MIN(G7:G{6+len(data)})']
    ])

    format_header(ws, f'A{summary_row}:B{summary_row}')
    format_currency(ws, f'B{summary_row+1}:B{summary_row+5}')

    print(f"   ✅ Uploaded {len(data)} days of VTP revenue data")
    return ws

def upload_weekly_data(gc, spreadsheet):
    """Upload weekly VTP revenue data"""
    print("\n📊 Uploading weekly VTP revenue data...")

    # Read CSV
    df_weekly = pd.read_csv('vtp_revenue_weekly.csv')

    # Create/clear worksheet
    ws = create_or_clear_worksheet(gc, spreadsheet, "VTP_Revenue_Weekly", rows=50, cols=8)

    # Add title and metadata
    ws.update('A1', [['VIRTUAL TRADING POSITION (VTP) REVENUE - WEEKLY AGGREGATION']])
    ws.update('A2', [[f'Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])
    ws.update('A3', [['']])
    ws.update('A4', [['Analysis Period: November 2025 | SCRP: £98.00/MWh | Efficiency: 90%']])
    ws.update('A5', [['']])

    # Add column headers
    headers = [
        'Week Starting',
        'Gross VTP Revenue (£)',
        'Net Revenue (£)',
        'Daily Average (£)'
    ]
    ws.update('A6', [headers])

    # Format data for upload
    data = []
    for _, row in df_weekly.iterrows():
        net = round(row['net_revenue'], 2)
        data.append([
            row['settlementDate'],
            round(row['total_vtp_revenue'], 2),
            net,
            round(net / 7, 2)  # Average per day
        ])

    # Upload data
    ws.update('A7', data)

    # Apply formatting
    format_header(ws, 'A1:D1')
    format_header(ws, 'A6:D6')
    format_currency(ws, 'B7:D' + str(6 + len(data)))

    # Add summary statistics
    summary_row = 6 + len(data) + 2
    ws.update(f'A{summary_row}', [['SUMMARY STATISTICS']])
    ws.update(f'A{summary_row+1}', [
        ['Total Month Gross Revenue:', f'=SUM(B7:B{6+len(data)})'],
        ['Total Month Net Revenue:', f'=SUM(C7:C{6+len(data)})'],
        ['Average Weekly Net Revenue:', f'=AVERAGE(C7:C{6+len(data)})'],
        ['Peak Week Revenue:', f'=MAX(C7:C{6+len(data)})']
    ])

    format_header(ws, f'A{summary_row}:B{summary_row}')
    format_currency(ws, f'B{summary_row+1}:B{summary_row+4}')

    print(f"   ✅ Uploaded {len(data)} weeks of VTP revenue data")
    return ws

def create_vtp_summary(gc, spreadsheet):
    """Create VTP summary sheet with key metrics and explanation"""
    print("\n📊 Creating VTP summary sheet...")

    ws = create_or_clear_worksheet(gc, spreadsheet, "VTP_Revenue_Summary", rows=50, cols=10)

    # Title
    ws.update('A1', [['VIRTUAL TRADING POSITION (VTP) REVENUE ANALYSIS']])
    format_header(ws, 'A1:J1')

    # Executive Summary
    ws.update('A3', [['EXECUTIVE SUMMARY - NOVEMBER 2025']])
    ws.update('A4', [
        ['Metric', 'Value', 'Notes'],
        ['Total Net Revenue', "=VTP_Revenue_Daily!B" + str(len(pd.read_csv('vtp_revenue_daily.csv')) + 9), 'After 90% efficiency'],
        ['Days Analyzed', str(len(pd.read_csv('vtp_revenue_daily.csv'))), 'Full November 2025'],
        ['Average Daily Revenue', "=VTP_Revenue_Daily!B" + str(len(pd.read_csv('vtp_revenue_daily.csv')) + 11), 'Mean daily net'],
        ['Peak Single Day', "=VTP_Revenue_Daily!B" + str(len(pd.read_csv('vtp_revenue_daily.csv')) + 12), 'Maximum daily revenue'],
        ['SCRP Used', '£98.00/MWh', 'Elexon v2.0 standard'],
        ['Deviation (ΔQ)', '5.0 MWh per SP', 'Settlement period volume'],
        ['Round-trip Efficiency', '90%', 'Battery/trading losses']
    ])
    format_header(ws, 'A3:C3')
    format_header(ws, 'A4:C4')
    format_currency(ws, 'B5:B8')

    # Methodology
    ws.update('A12', [['VTP REVENUE METHODOLOGY']])
    ws.update('A13', [
        ['Component', 'Description'],
        ['System State Detection', 'Short when SBP > SSP (offer > bid), Long otherwise'],
        ['Short Position Revenue', 'ΔQ × ((SBP - MID) - SCRP)'],
        ['Long Position Revenue', 'ΔQ × ((MID - SSP) + SCRP)'],
        ['Net Revenue', 'Gross Revenue × 90% efficiency factor'],
        ['Data Sources', 'bmrs_mid (Market Index) ⨝ bmrs_bod (Bid-Offer Data)'],
        ['Period Analyzed', 'November 2025 (30 days, 1,440 settlement periods)']
    ])
    format_header(ws, 'A12:B12')
    format_header(ws, 'A13:B13')

    # Key Insights
    df_daily = pd.read_csv('vtp_revenue_daily.csv')
    peak_day = df_daily.loc[df_daily['net_revenue'].idxmax()]
    low_day = df_daily.loc[df_daily['net_revenue'].idxmin()]

    ws.update('A20', [['KEY INSIGHTS']])
    ws.update('A21', [
        ['Observation', 'Detail'],
        ['Highest Revenue Day', f"{peak_day['settlementDate']}: £{peak_day['net_revenue']:,.2f}"],
        ['Lowest Revenue Day', f"{low_day['settlementDate']}: £{low_day['net_revenue']:,.2f}"],
        ['Revenue Volatility', f"Range: £{(peak_day['net_revenue'] - low_day['net_revenue']):,.2f}"],
        ['System State', 'All days showed SHORT system state (offer > bid)'],
        ['Price Spread Impact', 'Higher SBP-MID spreads = higher VTP revenue opportunities']
    ])
    format_header(ws, 'A20:B20')
    format_header(ws, 'A21:B21')

    # Navigation
    ws.update('A28', [['📊 RELATED SHEETS']])
    ws.update('A29', [
        ['Sheet Name', 'Description'],
        ['VTP_Revenue_Daily', 'Daily breakdown with system state and price components'],
        ['VTP_Revenue_Weekly', 'Weekly aggregations for trend analysis'],
        ['SCRP_VLP_Revenue', 'Related: VLP battery revenue vs market prices'],
        ['SCRP_MID_vs_BOALF', 'Related: Market index vs balancing mechanism comparison']
    ])
    format_header(ws, 'A28:B28')
    format_header(ws, 'A29:B29')

    print("   ✅ Created VTP summary sheet")
    return ws

def main():
    print("=" * 70)
    print("UPLOADING VTP REVENUE SIMULATION TO GOOGLE SHEETS")
    print("=" * 70)

    # Initialize clients
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)

    # Upload data
    ws_daily = upload_daily_data(gc, spreadsheet)
    ws_weekly = upload_weekly_data(gc, spreadsheet)
    ws_summary = create_vtp_summary(gc, spreadsheet)

    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print("\nCreated/Updated Sheets:")
    print("  1. VTP_Revenue_Summary - Executive summary and methodology")
    print("  2. VTP_Revenue_Daily - 30 days of detailed daily analysis")
    print("  3. VTP_Revenue_Weekly - 5 weeks of aggregated totals")
    print("\nDashboard URL:")
    print(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print("\n💡 Recommendation: Add VTP sheets after 'SCRP_VLP_Revenue' (sheet #12)")
    print("   for logical grouping with SCRP-related analyses.")

if __name__ == "__main__":
    main()
