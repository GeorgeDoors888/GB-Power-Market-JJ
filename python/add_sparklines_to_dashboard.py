#!/usr/bin/env python3
"""
Add Monthly Sparklines to Dashboard V3

Adds sparkline trend visualizations showing:
- Net Revenue (£M) - Last 12 months
- Net Margin (£/MWh) - Max, Min, Avg
- Active Units - Monthly trend
- Volume (MWh) - Monthly trend

Combines historical + IRIS data for complete 12-month coverage
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"  # BESS Dashboard V3
WORKSHEET_NAME = "Dashboard V3"  # Correct sheet name

# Sparkline placement in Dashboard V3
SPARKLINE_START_ROW = 14  # Below KPI row (F9:L9)
SPARKLINE_START_COL = 6   # Column F

def get_sheets_client():
    """Initialize Google Sheets API client"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'inner-cinema-credentials.json', scope
    )
    return gspread.authorize(creds)

def get_monthly_sparkline_data(client):
    """Query 12-month sparkline data from BigQuery"""
    query = """
    SELECT 
      month_label,
      total_net_revenue_monthly,
      avg_margin,
      max_margin,
      min_margin,
      total_volume_monthly,
      active_units,
      total_acceptances
    FROM `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_monthly_sparklines`
    WHERE breakdown = 'GB_total'
    ORDER BY month_start ASC  -- Oldest to newest for sparkline
    LIMIT 12
    """
    
    df = client.query(query).to_dataframe()
    return df

def create_sparkline_formulas(df):
    """Generate Google Sheets SPARKLINE formulas from data"""
    
    # Revenue sparkline (£M)
    revenue_values = [f"{v/1e6:.1f}" for v in df['total_net_revenue_monthly'].values]
    revenue_sparkline = f"=SPARKLINE({{{','.join(revenue_values)}}}," + \
                       "{\"charttype\",\"line\";\"color\",\"#34A853\";\"linewidth\",2})"
    
    # Net Margin sparkline (£/MWh) - Average
    margin_values = [f"{v:.1f}" for v in df['avg_margin'].values if pd.notna(v)]
    margin_sparkline = f"=SPARKLINE({{{','.join(margin_values)}}}," + \
                      "{\"charttype\",\"line\";\"color\",\"#4285F4\";\"linewidth\",2})"
    
    # Volume sparkline (MWh)
    volume_values = [f"{abs(v):.0f}" for v in df['total_volume_monthly'].values]
    volume_sparkline = f"=SPARKLINE({{{','.join(volume_values)}}}," + \
                      "{\"charttype\",\"column\";\"color\",\"#FBBC04\"})"
    
    # Active Units sparkline
    units_values = [f"{int(v)}" for v in df['active_units'].values]
    units_sparkline = f"=SPARKLINE({{{','.join(units_values)}}}," + \
                     "{\"charttype\",\"line\";\"color\",\"#EA4335\";\"linewidth\",2})"
    
    return {
        'revenue': revenue_sparkline,
        'margin': margin_sparkline,
        'volume': volume_sparkline,
        'units': units_sparkline,
        'month_labels': df['month_label'].tolist()
    }

def add_sparklines_to_dashboard(sheet, formulas, stats):
    """Add sparkline visualizations to Dashboard V3"""
    
    row = SPARKLINE_START_ROW
    col = SPARKLINE_START_COL
    
    # Section header
    sheet.update_cell(row, col, "📊 12-MONTH TRENDS (Dec 2024 - Oct 2025)")
    sheet.format(f"{chr(64+col)}{row}", {
        "textFormat": {"bold": True, "fontSize": 11},
        "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95}
    })
    row += 1
    
    # Revenue sparkline
    sheet.update_cell(row, col, "Net Revenue (£M):")
    sheet.update_cell(row, col+1, formulas['revenue'])
    sheet.update_cell(row, col+3, f"Total: £{stats['total_revenue']:.0f}M")
    sheet.update_cell(row, col+4, f"Avg: £{stats['avg_revenue']:.0f}M/mo")
    row += 1
    
    # Margin sparkline
    sheet.update_cell(row, col, "Net Margin (£/MWh):")
    sheet.update_cell(row, col+1, formulas['margin'])
    sheet.update_cell(row, col+3, f"Avg: £{stats['avg_margin']:.2f}/MWh")
    sheet.update_cell(row, col+4, f"Peak: £{stats['max_margin']:.2f}/MWh")
    row += 1
    
    # Volume sparkline
    sheet.update_cell(row, col, "Volume (MWh):")
    sheet.update_cell(row, col+1, formulas['volume'])
    sheet.update_cell(row, col+3, f"Total: {stats['total_volume']:,.0f} MWh")
    row += 1
    
    # Active Units sparkline
    sheet.update_cell(row, col, "Active Units:")
    sheet.update_cell(row, col+1, formulas['units'])
    sheet.update_cell(row, col+3, f"Avg: {stats['avg_units']:.0f} BMUs/mo")
    row += 1
    
    # Month labels (horizontal)
    row += 1
    sheet.update_cell(row, col, "Months:")
    for i, month in enumerate(formulas['month_labels'][:6]):  # First 6 months
        sheet.update_cell(row, col+1+i, month)
    row += 1
    for i, month in enumerate(formulas['month_labels'][6:]):  # Last 6 months
        sheet.update_cell(row, col+1+i, month)
    
    print(f"✅ Sparklines added to rows {SPARKLINE_START_ROW}-{row}")

def main():
    print("🚀 Adding Monthly Sparklines to Dashboard V3\n")
    
    # Connect to BigQuery
    print("📊 Connecting to BigQuery...")
    bq_client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get sparkline data
    print("📈 Fetching 12-month trend data...")
    df = get_monthly_sparkline_data(bq_client)
    
    if len(df) == 0:
        print("❌ No data available")
        return 1
    
    print(f"✅ Retrieved {len(df)} months of data")
    
    # Calculate summary statistics
    stats = {
        'total_revenue': df['total_net_revenue_monthly'].sum() / 1e6,
        'avg_revenue': df['total_net_revenue_monthly'].mean() / 1e6,
        'avg_margin': df['avg_margin'].mean(),
        'max_margin': df['max_margin'].max(),
        'total_volume': df['total_volume_monthly'].sum(),
        'avg_units': df['active_units'].mean()
    }
    
    print(f"\n💰 12-Month Summary:")
    print(f"   Total Revenue: £{stats['total_revenue']:.0f}M")
    print(f"   Avg Margin: £{stats['avg_margin']:.2f}/MWh")
    print(f"   Total Volume: {stats['total_volume']:,.0f} MWh")
    print(f"   Avg Active Units: {stats['avg_units']:.0f} BMUs")
    
    # Generate sparkline formulas
    print("\n✨ Generating sparkline formulas...")
    formulas = create_sparkline_formulas(df)
    
    # Connect to Google Sheets
    print("\n📝 Connecting to Google Sheets...")
    sheets_client = get_sheets_client()
    spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    
    # Add sparklines
    print(f"📊 Adding sparklines to '{WORKSHEET_NAME}'...")
    add_sparklines_to_dashboard(worksheet, formulas, stats)
    
    print("\n✅ Dashboard V3 updated with 12-month sparklines!")
    print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
