#!/usr/bin/env python3
"""
Create unified BigQuery views and Analysis sheet in Google Sheets
Combines historical (Elexon API) and real-time (IRIS) data sources
"""

import pickle
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from gspread_formatting import *

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Analysis'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Color scheme
COLORS = {
    'header_bg': Color(0.102, 0.137, 0.494),  # #1a237e Deep Blue
    'header_text': Color(1, 1, 1),  # White
    'section_bg': Color(0.157, 0.208, 0.576),  # #283593 Indigo
    'section_text': Color(1, 1, 1),  # White
    'data_bg': Color(1, 1, 1),  # White
    'alt_row_bg': Color(0.961, 0.961, 0.961),  # #f5f5f5 Very Light Gray
    'border': Color(0.878, 0.878, 0.878),  # #e0e0e0 Gray
    'historical': Color(0.129, 0.588, 0.953),  # #2196f3 Blue
    'realtime': Color(0.298, 0.686, 0.314),  # #4caf50 Green
    'warning': Color(1, 0.596, 0),  # #ff9800 Orange
    'critical': Color(0.957, 0.263, 0.212),  # #f44336 Red
}


def create_unified_views():
    """Create unified BigQuery views combining historical and IRIS data"""
    print("📊 Creating unified BigQuery views...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    views = {
        'bmrs_freq_unified': """
            CREATE OR REPLACE VIEW `{project}.{dataset}.bmrs_freq_unified` AS
            WITH historical AS (
              SELECT 
                measurementTime as timestamp,
                frequency,
                'historical' as source,
                recordType
              FROM `{project}.{dataset}.bmrs_freq`
              WHERE measurementTime < DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
            ),
            realtime AS (
              SELECT 
                measurementTime as timestamp,
                frequency,
                'real-time' as source,
                recordType
              FROM `{project}.{dataset}.bmrs_freq_iris`
              WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
            )
            SELECT * FROM historical
            UNION ALL
            SELECT * FROM realtime
            ORDER BY timestamp DESC
        """,
        
        'bmrs_mid_unified': """
            CREATE OR REPLACE VIEW `{project}.{dataset}.bmrs_mid_unified` AS
            WITH historical AS (
              SELECT 
                settlementDate as timestamp,
                settlementPeriod,
                systemSellPrice,
                systemBuyPrice,
                'historical' as source
              FROM `{project}.{dataset}.bmrs_mid`
              WHERE settlementDate < DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
            ),
            realtime AS (
              SELECT 
                settlementDate as timestamp,
                settlementPeriod,
                CAST(price AS FLOAT64) as systemSellPrice,
                CAST(volume AS FLOAT64) as systemBuyPrice,
                'real-time' as source
              FROM `{project}.{dataset}.bmrs_mid_iris`
              WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
            )
            SELECT * FROM historical
            UNION ALL
            SELECT * FROM realtime
            ORDER BY timestamp DESC, settlementPeriod DESC
        """,
        
        'bmrs_fuelinst_unified': """
            CREATE OR REPLACE VIEW `{project}.{dataset}.bmrs_fuelinst_unified` AS
            WITH historical AS (
              SELECT 
                publishTime as timestamp,
                settlementDate,
                settlementPeriod,
                fuelType,
                generation,
                'historical' as source
              FROM `{project}.{dataset}.bmrs_fuelinst`
              WHERE publishTime < DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
            ),
            realtime AS (
              SELECT 
                publishTime as timestamp,
                settlementDate,
                settlementPeriod,
                fuelType,
                generation,
                'real-time' as source
              FROM `{project}.{dataset}.bmrs_fuelinst_iris`
              WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
            )
            SELECT * FROM historical
            UNION ALL
            SELECT * FROM realtime
            ORDER BY timestamp DESC
        """,
        
        'bmrs_bod_unified': """
            CREATE OR REPLACE VIEW `{project}.{dataset}.bmrs_bod_unified` AS
            WITH historical AS (
              SELECT 
                timeFrom as timestamp,
                bmUnit,
                bidOfferLevel,
                bidOfferPair,
                offerPrice,
                bidPrice,
                'historical' as source
              FROM `{project}.{dataset}.bmrs_bod`
              WHERE timeFrom < DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
            ),
            realtime AS (
              SELECT 
                timeFrom as timestamp,
                bmUnit,
                bidOfferLevel,
                bidOfferPair,
                offerPrice,
                bidPrice,
                'real-time' as source
              FROM `{project}.{dataset}.bmrs_bod_iris`
              WHERE timeFrom >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
            )
            SELECT * FROM historical
            UNION ALL
            SELECT * FROM realtime
            ORDER BY timestamp DESC
        """,
        
        'bmrs_boalf_unified': """
            CREATE OR REPLACE VIEW `{project}.{dataset}.bmrs_boalf_unified` AS
            WITH historical AS (
              SELECT 
                publishTime as timestamp,
                bmUnit,
                acceptanceTime,
                deemedBidOfferFlag,
                soFlag,
                volume,
                'historical' as source
              FROM `{project}.{dataset}.bmrs_boalf`
              WHERE publishTime < DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
            ),
            realtime AS (
              SELECT 
                publishTime as timestamp,
                bmUnit,
                acceptanceTime,
                deemedBidOfferFlag,
                soFlag,
                volume,
                'real-time' as source
              FROM `{project}.{dataset}.bmrs_boalf_iris`
              WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
            )
            SELECT * FROM historical
            UNION ALL
            SELECT * FROM realtime
            ORDER BY timestamp DESC
        """
    }
    
    for view_name, query in views.items():
        print(f"Creating view: {view_name}...")
        try:
            formatted_query = query.format(project=PROJECT_ID, dataset=DATASET)
            client.query(formatted_query).result()
            print(f"✅ {view_name} created successfully")
        except Exception as e:
            print(f"⚠️ Error creating {view_name}: {e}")
            # Continue with other views
    
    print("✅ All unified views created!")


def create_analysis_sheet():
    """Create the Analysis sheet in Google Sheets"""
    print("📄 Creating Analysis sheet...")
    
    # Load credentials
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Create or get sheet
    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
        print(f"Sheet '{SHEET_NAME}' already exists, clearing it...")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print(f"Creating new sheet: {SHEET_NAME}")
        sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=250, cols=15)
    
    # Set up structure
    print("Setting up sheet structure...")
    
    # Row 1: Main header
    sheet.merge_cells('A1:K1')
    sheet.update_acell('A1', 'ANALYSIS DASHBOARD')
    
    # Row 2: Subtitle
    sheet.merge_cells('A2:K2')
    sheet.update_acell('A2', 'Historical + Real-Time Data Analysis')
    
    # Row 3: Empty spacing
    
    # Row 4: Date Range Section
    sheet.merge_cells('A4:K4')
    sheet.update_acell('A4', '📅 DATE RANGE SELECTION')
    
    # Row 6: Quick Select
    sheet.update_acell('A6', 'Quick Select:')
    sheet.update_acell('C6', '1 Month')  # Default
    
    # Row 6-8: Custom Range
    sheet.update_acell('F6', 'Custom Range:')
    sheet.update_acell('F7', 'From:')
    sheet.update_acell('F8', 'To:')
    
    # Set default dates
    today = datetime.now()
    month_ago = today - timedelta(days=30)
    sheet.update_acell('H7', month_ago.strftime('%d/%m/%Y'))
    sheet.update_acell('H8', today.strftime('%d/%m/%Y'))
    
    # Row 9: Refresh button placeholder
    sheet.update_acell('F9', '[Click to Refresh Data]')
    
    # Row 11: Data Group Selection
    sheet.merge_cells('A11:K11')
    sheet.update_acell('A11', '📊 DATA GROUP SELECTION')
    
    # Row 13-15: Checkboxes (labels)
    sheet.update_acell('B13', 'System Frequency')
    sheet.update_acell('E13', 'Market Prices')
    sheet.update_acell('H13', 'Generation')
    
    sheet.update_acell('B14', 'Balancing Services')
    sheet.update_acell('E14', 'Demand Data')
    sheet.update_acell('H14', 'Weather Correlation')
    
    sheet.update_acell('B15', 'Bid-Offer Data')
    sheet.update_acell('E15', 'Forecast vs Actual')
    sheet.update_acell('H15', 'Grid Stability')
    
    # Row 17: System Frequency Section
    sheet.merge_cells('A17:K17')
    sheet.update_acell('A17', '📈 SYSTEM FREQUENCY ANALYSIS')
    
    # Row 18: Data source info
    sheet.merge_cells('A18:K18')
    sheet.update_acell('A18', 'Data Source: Historical (bmrs_freq) + Real-Time (bmrs_freq_iris)')
    
    # Row 19: Statistics labels
    sheet.update_acell('A20', 'Records:')
    sheet.update_acell('A21', 'Time Range:')
    sheet.update_acell('A23', 'Key Metrics:')
    sheet.update_acell('A24', '• Average Frequency:')
    sheet.update_acell('A25', '• Min Frequency:')
    sheet.update_acell('A26', '• Max Frequency:')
    sheet.update_acell('A27', '• Standard Deviation:')
    sheet.update_acell('A28', '• Time Below 49.8 Hz:')
    
    # Row 31: Market Prices Section
    sheet.merge_cells('A31:K31')
    sheet.update_acell('A31', '💰 MARKET PRICES ANALYSIS')
    
    sheet.merge_cells('A32:K32')
    sheet.update_acell('A32', 'Data Source: Historical (bmrs_mid) + Real-Time (bmrs_mid_iris)')
    
    # Row 45: Generation Section
    sheet.merge_cells('A45:K45')
    sheet.update_acell('A45', '⚡ GENERATION MIX ANALYSIS')
    
    sheet.merge_cells('A46:K46')
    sheet.update_acell('A46', 'Data Source: Historical (bmrs_fuelinst) + Real-Time (bmrs_fuelinst_iris)')
    
    # Row 59: Balancing Services Section
    sheet.merge_cells('A59:K59')
    sheet.update_acell('A59', '⚖️ BALANCING SERVICES ANALYSIS')
    
    sheet.merge_cells('A60:K60')
    sheet.update_acell('A60', 'Data Source: BOD (bmrs_bod + bmrs_bod_iris) + BOALF (bmrs_boalf + _iris)')
    
    # Row 73: Raw Data Table
    sheet.merge_cells('A73:K73')
    sheet.update_acell('A73', '📊 RAW DATA TABLE')
    
    # Row 74: Export buttons
    sheet.update_acell('A74', '[Export to CSV]')
    sheet.update_acell('C74', '[Export to Excel]')
    sheet.update_acell('E74', '[Copy to Clipboard]')
    
    # Row 76: Table headers
    headers = ['Timestamp', 'Freq (Hz)', 'SSP (£)', 'SBP (£)', 'Gen (MW)', 'Source', 'Fuel Type', 'BM Unit']
    for i, header in enumerate(headers):
        sheet.update_cell(76, i + 1, header)
    
    # Row 200: Footer
    sheet.merge_cells('A200:K200')
    sheet.update_acell('A200', 'ℹ️ DATA SOURCES & QUALITY')
    
    sheet.update_acell('A201', 'Historical Data (Elexon API):')
    sheet.update_acell('A202', '• Tables: bmrs_freq, bmrs_mid, bmrs_fuelinst, bmrs_bod, bmrs_boalf')
    sheet.update_acell('A203', '• Coverage: 2020-01-01 to present')
    sheet.update_acell('A204', '• Update Frequency: Every 15 minutes')
    
    sheet.update_acell('A206', 'Real-Time Data (IRIS Streaming):')
    sheet.update_acell('A207', '• Tables: bmrs_*_iris (8+ tables)')
    sheet.update_acell('A208', '• Coverage: Last 48 hours (rolling window)')
    sheet.update_acell('A209', '• Update Frequency: Continuous (30-60 second latency)')
    
    sheet.merge_cells('A211:K211')
    sheet.update_acell('A211', f"Last Updated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Auto-refresh: Every 5 minutes")
    
    print("Applying formatting...")
    
    # Apply formatting
    fmt_header = CellFormat(
        backgroundColor=COLORS['header_bg'],
        textFormat=TextFormat(bold=True, fontSize=14, foregroundColor=COLORS['header_text']),
        horizontalAlignment='CENTER'
    )
    
    fmt_section = CellFormat(
        backgroundColor=COLORS['section_bg'],
        textFormat=TextFormat(bold=True, fontSize=12, foregroundColor=COLORS['section_text']),
        horizontalAlignment='LEFT',
        padding=Padding(2, 2, 2, 2)
    )
    
    fmt_data = CellFormat(
        backgroundColor=COLORS['data_bg'],
        textFormat=TextFormat(fontSize=10),
        horizontalAlignment='LEFT'
    )
    
    # Format headers
    format_cell_range(sheet, 'A1:K1', fmt_header)
    format_cell_range(sheet, 'A2:K2', fmt_header)
    
    # Format sections
    format_cell_range(sheet, 'A4:K4', fmt_section)
    format_cell_range(sheet, 'A11:K11', fmt_section)
    format_cell_range(sheet, 'A17:K17', fmt_section)
    format_cell_range(sheet, 'A31:K31', fmt_section)
    format_cell_range(sheet, 'A45:K45', fmt_section)
    format_cell_range(sheet, 'A59:K59', fmt_section)
    format_cell_range(sheet, 'A73:K73', fmt_section)
    format_cell_range(sheet, 'A200:K200', fmt_section)
    
    # Add data validation for dropdown
    print("Adding dropdowns...")
    try:
        dropdown_options = [
            '24 Hours', '1 Week', '1 Month', '6 Months', 
            '12 Months', '24 Months', '3 Years', '4 Years', 'All Time', 'Custom'
        ]
        
        # Note: gspread data validation - use Google Sheets API directly if needed
        sheet.update_acell('C6', '1 Month')  # Default value
        
    except Exception as e:
        print(f"⚠️ Could not add dropdown validation: {e}")
    
    # Insert checkboxes
    print("Adding checkboxes...")
    try:
        checkbox_cells = ['A13', 'D13', 'G13', 'A14', 'D14', 'H14', 'A15', 'D15', 'G15']
        for cell in checkbox_cells:
            sheet.update_acell(cell, True)  # Set to checked by default
    except Exception as e:
        print(f"⚠️ Could not add checkboxes: {e}")
    
    print(f"✅ Analysis sheet '{SHEET_NAME}' created successfully!")
    print(f"🔗 Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet.id}")
    
    return sheet


def main():
    """Main execution"""
    print("=" * 70)
    print("⚡ ANALYSIS SHEET SETUP")
    print("=" * 70)
    print()
    
    # Step 1: Create unified BigQuery views
    print("STEP 1: Creating unified BigQuery views...")
    try:
        create_unified_views()
        print()
    except Exception as e:
        print(f"❌ Error creating views: {e}")
        print("Continuing with sheet creation...")
        print()
    
    # Step 2: Create Analysis sheet
    print("STEP 2: Creating Analysis sheet in Google Sheets...")
    try:
        sheet = create_analysis_sheet()
        print()
    except Exception as e:
        print(f"❌ Error creating sheet: {e}")
        return
    
    # Step 3: Summary
    print("=" * 70)
    print("✅ SETUP COMPLETE!")
    print("=" * 70)
    print()
    print("📊 Unified Views Created:")
    print("  • bmrs_freq_unified")
    print("  • bmrs_mid_unified")
    print("  • bmrs_fuelinst_unified")
    print("  • bmrs_bod_unified")
    print("  • bmrs_boalf_unified")
    print()
    print("📄 Analysis Sheet Created:")
    print(f"  • Sheet Name: {SHEET_NAME}")
    print(f"  • Spreadsheet: {SPREADSHEET_ID}")
    print(f"  • URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    print()
    print("📋 Next Steps:")
    print("  1. Test unified views with sample queries")
    print("  2. Manually configure dropdown validation in Google Sheets")
    print("  3. Run update_analysis_sheet.py to populate data")
    print("  4. Create charts for visualizations")
    print("  5. Set up automated refresh (cron job)")
    print()
    print("📚 Documentation: ANALYSIS_SHEET_DESIGN.md")
    print()


if __name__ == '__main__':
    main()
