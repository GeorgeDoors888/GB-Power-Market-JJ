#!/usr/bin/env python3
"""
Add Wind Event Summary to Google Sheets Dashboard

Purpose: Create event summary table in Google Sheets with:
- Last 30 days event counts by farm and type
- Lost generation estimates (MWh)
- Sparkline trend visualization
- Hyperlink to Streamlit Event Explorer

Updates: Daily via cron at 04:00
Target: Google Sheets "Live Dashboard v2" or new "Wind Events" sheet
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Wind Events'  # New sheet for event summary
STREAMLIT_URL = 'http://localhost:8501'  # Update after deploying to cloud

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_event_summary_data():
    """Query BigQuery for last 30 days wind farm events."""
    logging.info("📊 Querying wind event data from BigQuery...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    WITH farm_events AS (
        SELECT 
            farm_name,
            hour,
            is_calm_event,
            is_storm_event,
            is_turbulence_event,
            is_icing_event,
            is_curtailment_event,
            actual_mw,
            capacity_factor_pct
        FROM `{PROJECT_ID}.{DATASET}.wind_unified_features`
        WHERE CAST(hour AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
          AND has_any_event = TRUE
    ),
    farm_totals AS (
        SELECT 
            farm_name,
            SUM(CASE WHEN is_calm_event = 1 THEN 1 ELSE 0 END) as calm_hours,
            SUM(CASE WHEN is_storm_event = 1 THEN 1 ELSE 0 END) as storm_hours,
            SUM(CASE WHEN is_turbulence_event = 1 THEN 1 ELSE 0 END) as turbulence_hours,
            SUM(CASE WHEN is_icing_event = 1 THEN 1 ELSE 0 END) as icing_hours,
            SUM(CASE WHEN is_curtailment_event = 1 THEN 1 ELSE 0 END) as curtailment_hours,
            ROUND(AVG(CASE WHEN is_calm_event = 1 OR is_storm_event = 1 THEN capacity_factor_pct ELSE NULL END), 1) as avg_event_cf,
            COUNT(*) as total_event_hours
        FROM farm_events
        GROUP BY farm_name
    ),
    daily_events AS (
        SELECT 
            farm_name,
            DATE(hour) as event_date,
            COUNT(*) as daily_event_count
        FROM farm_events
        GROUP BY farm_name, event_date
        ORDER BY farm_name, event_date
    )
    SELECT 
        ft.farm_name,
        COALESCE(ft.calm_hours, 0) as calm_hours,
        COALESCE(ft.storm_hours, 0) as storm_hours,
        COALESCE(ft.turbulence_hours, 0) as turbulence_hours,
        COALESCE(ft.icing_hours, 0) as icing_hours,
        COALESCE(ft.curtailment_hours, 0) as curtailment_hours,
        COALESCE(ft.avg_event_cf, 0) as avg_event_cf,
        COALESCE(ft.total_event_hours, 0) as total_event_hours,
        ARRAY_AGG(de.daily_event_count ORDER BY de.event_date) as daily_trend
    FROM farm_totals ft
    LEFT JOIN daily_events de ON ft.farm_name = de.farm_name
    GROUP BY 
        ft.farm_name,
        ft.calm_hours,
        ft.storm_hours,
        ft.turbulence_hours,
        ft.icing_hours,
        ft.curtailment_hours,
        ft.avg_event_cf,
        ft.total_event_hours
    ORDER BY ft.total_event_hours DESC
    """
    
    df = client.query(query).to_dataframe()
    logging.info(f"✅ Retrieved data for {len(df)} farms")
    
    return df

def generate_sparkline_formula(trend_data):
    """Generate Google Sheets SPARKLINE formula from daily trend array."""
    if not trend_data or len(trend_data) == 0:
        return ""
    
    # Format as comma-separated values
    values = ','.join(str(int(x)) for x in trend_data if x is not None)
    
    # Create SPARKLINE formula with options
    formula = f'=SPARKLINE({{{values}}}, {{"charttype","line"; "linewidth",2; "color","#FF6B6B"}})'
    
    return formula

def create_or_update_sheet(gc, spreadsheet):
    """Create Wind Events sheet if it doesn't exist, or clear if it does."""
    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
        logging.info(f"📄 Found existing '{SHEET_NAME}' sheet, clearing...")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        logging.info(f"📄 Creating new '{SHEET_NAME}' sheet...")
        sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=50, cols=15)
    
    return sheet

def format_sheet_header(sheet):
    """Apply formatting to sheet header."""
    logging.info("🎨 Formatting sheet header...")
    
    # Title
    sheet.update('A1', '⚡ Wind Farm Events - Last 30 Days')
    sheet.format('A1:H1', {
        'textFormat': {'fontSize': 14, 'bold': True},
        'horizontalAlignment': 'LEFT',
        'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5}
    })
    
    # Subtitle with last update timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.update('A2', f'Last Updated: {timestamp}')
    sheet.format('A2:H2', {
        'textFormat': {'fontSize': 10, 'italic': True},
        'horizontalAlignment': 'LEFT'
    })
    
    # Hyperlink button to Streamlit app
    sheet.update('J1', f'=HYPERLINK("{STREAMLIT_URL}", "🌊 Explore Events →")')
    sheet.format('J1', {
        'textFormat': {'fontSize': 12, 'bold': True, 'foregroundColor': {'red': 0, 'green': 0.4, 'blue': 0.8}},
        'horizontalAlignment': 'CENTER',
        'verticalAlignment': 'MIDDLE',
        'borders': {
            'top': {'style': 'SOLID', 'width': 2},
            'bottom': {'style': 'SOLID', 'width': 2},
            'left': {'style': 'SOLID', 'width': 2},
            'right': {'style': 'SOLID', 'width': 2}
        }
    })
    
    # Column headers
    headers = [
        'Farm Name',
        'CALM',
        'STORM',
        'TURBULENCE',
        'ICING',
        'CURTAILMENT',
        'Avg CF %',
        'Trend (30d)'
    ]
    
    sheet.update('A4:H4', [headers])
    sheet.format('A4:H4', {
        'textFormat': {'fontSize': 11, 'bold': True},
        'horizontalAlignment': 'CENTER',
        'verticalAlignment': 'MIDDLE',
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'borders': {
            'bottom': {'style': 'SOLID', 'width': 2}
        }
    })
    
    # Set column widths
    sheet.format('A:A', {'columnWidth': 180})  # Farm name
    sheet.format('B:F', {'columnWidth': 90})   # Event counts
    sheet.format('G:G', {'columnWidth': 140})  # Lost generation
    sheet.format('H:H', {'columnWidth': 150})  # Sparkline
    sheet.format('J:J', {'columnWidth': 180})  # Button

def update_event_data(sheet, df):
    """Update sheet with event summary data."""
    logging.info("📝 Writing event data to sheet...")
    
    if len(df) == 0:
        logging.warning("⚠️  No event data found for last 30 days")
        sheet.update('A5', 'No events detected in the last 30 days')
        return
    
    # Prepare data rows
    data_rows = []
    sparkline_formulas = []
    
    for idx, row in df.iterrows():
        # Data row (values only)
        data_row = [
            row['farm_name'],
            int(row['calm_hours']),
            int(row['storm_hours']),
            int(row['turbulence_hours']),
            int(row['icing_hours']),
            int(row['curtailment_hours']),
            f"{row['avg_event_cf']:.1f}%"
        ]
        data_rows.append(data_row)
        
        # Sparkline formula (separate list)
        sparkline = generate_sparkline_formula(row['daily_trend'])
        sparkline_formulas.append([sparkline])
    
    # Write data (A5 to G...)
    start_row = 5
    end_row = start_row + len(data_rows) - 1
    sheet.update(f'A{start_row}:G{end_row}', data_rows)
    
    # Write sparkline formulas (H5 to H...)
    sheet.update(f'H{start_row}:H{end_row}', sparkline_formulas, value_input_option='USER_ENTERED')
    
    # Format data rows
    sheet.format(f'A{start_row}:H{end_row}', {
        'horizontalAlignment': 'CENTER',
        'verticalAlignment': 'MIDDLE'
    })
    
    # Left-align farm names
    sheet.format(f'A{start_row}:A{end_row}', {
        'horizontalAlignment': 'LEFT'
    })
    
    # Format lost generation with thousands separator
    sheet.format(f'G{start_row}:G{end_row}', {
        'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0'}
    })
    
    # Add alternating row colors
    for i in range(len(data_rows)):
        row_num = start_row + i
        if i % 2 == 0:
            sheet.format(f'A{row_num}:H{row_num}', {
                'backgroundColor': {'red': 0.97, 'green': 0.97, 'blue': 0.97}
            })
    
    # Add totals row
    total_row = end_row + 2
    sheet.update(f'A{total_row}', 'TOTAL')
    sheet.format(f'A{total_row}:H{total_row}', {
        'textFormat': {'bold': True},
        'borders': {
            'top': {'style': 'SOLID', 'width': 2}
        }
    })
    
    # Sum formulas for totals
    sheet.update(f'B{total_row}', f'=SUM(B{start_row}:B{end_row})')
    sheet.update(f'C{total_row}', f'=SUM(C{start_row}:C{end_row})')
    sheet.update(f'D{total_row}', f'=SUM(D{start_row}:D{end_row})')
    sheet.update(f'E{total_row}', f'=SUM(E{start_row}:E{end_row})')
    sheet.update(f'F{total_row}', f'=SUM(F{start_row}:F{end_row})')
    sheet.update(f'G{total_row}', f'=SUM(G{start_row}:G{end_row})')
    
    logging.info(f"✅ Wrote {len(data_rows)} rows of event data")

def add_usage_instructions(sheet):
    """Add usage instructions at bottom of sheet."""
    logging.info("📖 Adding usage instructions...")
    
    instructions = [
        [''],
        ['How to Use This Dashboard:'],
        ['1. View event counts for each farm over the last 30 days'],
        ['2. Check "Lost Gen (MWh)" to identify farms with highest revenue impact'],
        ['3. Review sparkline trends to see event frequency patterns'],
        ['4. Click "🌊 Explore Events" button (top right) for detailed interactive timeline'],
        ['5. In Streamlit app: Select farm → Pick date range → Zoom into specific events'],
        [''],
        ['Event Types:'],
        ['  • CALM: Wind speed < 4 m/s for 3+ consecutive hours (lost generation)'],
        ['  • STORM: Wind speed > 25 m/s (curtailment risk, safety cutoff)'],
        ['  • TURBULENCE: Gust factor > 1.4 (mechanical stress, transient losses)'],
        ['  • ICING: Temperature < 0°C + high humidity (blade icing, rare in UK)'],
        ['  • CURTAILMENT: Grid constraint or manual curtailment instruction'],
    ]
    
    start_row = 30  # Below data table
    sheet.update(f'A{start_row}:A{start_row + len(instructions) - 1}', instructions)
    
    # Format instructions
    sheet.format(f'A{start_row + 1}', {
        'textFormat': {'bold': True, 'fontSize': 11}
    })
    sheet.format(f'A{start_row + 8}', {
        'textFormat': {'bold': True, 'fontSize': 11}
    })

def main():
    """Main execution function."""
    try:
        logging.info("="*70)
        logging.info("WIND EVENT SUMMARY → GOOGLE SHEETS")
        logging.info("="*70)
        
        # Step 1: Get event data from BigQuery
        df = get_event_summary_data()
        
        if df.empty:
            logging.warning("⚠️  No event data available")
            return
        
        # Step 2: Connect to Google Sheets
        logging.info("🔗 Connecting to Google Sheets...")
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'inner-cinema-credentials.json', scope
        )
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        
        # Step 3: Create/update sheet
        sheet = create_or_update_sheet(gc, spreadsheet)
        
        # Step 4: Format and populate
        format_sheet_header(sheet)
        update_event_data(sheet, df)
        add_usage_instructions(sheet)
        
        logging.info("="*70)
        logging.info("✅ SUCCESS - Wind Events sheet updated!")
        logging.info("="*70)
        logging.info(f"📊 Summary:")
        logging.info(f"  - Farms with events: {len(df)}")
        logging.info(f"  - Total event hours: {df['total_event_hours'].sum():.0f}")
        logging.info(f"  - Most events: {df.iloc[0]['farm_name']} ({df.iloc[0]['total_event_hours']:.0f} hours)")
        logging.info(f"  - View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        
    except Exception as e:
        logging.error(f"❌ Error updating sheet: {e}")
        raise

if __name__ == "__main__":
    main()
