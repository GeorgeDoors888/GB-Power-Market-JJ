#!/usr/bin/env python3
"""
Create Live Outages sheet with filtering, search, and visualization
"""

import sys
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from gspread_formatting import *

# Configuration
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Manual asset name mappings
MANUAL_ASSET_NAMES = {
    'T_PEHE-1': 'Peterhead Power Station',
    'T_KEAD-1': 'Keadby Power Station Unit 1',
    'T_KEAD-2': 'Keadby Power Station Unit 2',
    'I_IEG-IFA2': 'IFA2 Interconnector (Export)',
    'I_IED-IFA2': 'IFA2 Interconnector (Import)',
    'I_IEG-VKL1': 'Viking Link Interconnector (Export)',
    'I_IED-VKL1': 'Viking Link Interconnector (Import)',
    'RYHPS-1': 'Rye House Power Station'
}

def main():
    print("🔄 Creating Live Outages Sheet...")
    
    # Connect to Google Sheets
    creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Create or get the sheet
    try:
        sheet = spreadsheet.worksheet('Live Outages')
        print("✅ Found existing 'Live Outages' sheet - will update")
        sheet.clear()
    except:
        sheet = spreadsheet.add_worksheet(title='Live Outages', rows=500, cols=15)
        print("✅ Created new 'Live Outages' sheet")
    
    # Connect to BigQuery
    bq_creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json'
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location='US')
    
    # ===== HEADER SECTION =====
    print("📋 Creating header section...")
    
    # Title and timestamp
    sheet.update('A1', [['⚠️ LIVE OUTAGES - COMPLETE VIEW']])
    sheet.update('A2', [[f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])
    
    # Filter controls
    sheet.update('A4', [['FILTERS:']])
    sheet.update('A5', [['Search by BM Unit:', '', 'Search by Asset:', '', 'Start Date:', '', 'End Date:']])
    sheet.update('A6', [['(Enter below)', '', '(Enter below)', '', '(YYYY-MM-DD)', '', '(YYYY-MM-DD)']])
    
    # Summary stats
    sheet.update('J5', [['SUMMARY STATISTICS']])
    sheet.update('J6', [['Total Active Outages:']])
    sheet.update('J7', [['Total Unavailable (MW):']])
    sheet.update('J8', [['Avg Outage Size (MW):']])
    
    # ===== GET ALL OUTAGES DATA =====
    print("📊 Fetching all outages data...")
    
    query = f"""
    WITH latest_outages AS (
        SELECT 
            affectedUnit,
            assetName,
            fuelType,
            normalCapacity,
            unavailableCapacity,
            cause,
            eventStartTime,
            eventEndTime,
            eventStatus,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', eventStartTime) as start_time,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', eventEndTime) as end_time,
            ROW_NUMBER() OVER (PARTITION BY affectedUnit ORDER BY revisionNumber DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND unavailableCapacity >= 50
    )
    SELECT 
        lo.affectedUnit,
        COALESCE(bmu.bmunitname, lo.assetName, lo.affectedUnit) as assetName,
        lo.fuelType,
        lo.normalCapacity,
        lo.unavailableCapacity,
        lo.cause,
        lo.start_time,
        lo.end_time,
        lo.eventStatus
    FROM latest_outages lo
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
        ON lo.affectedUnit = bmu.nationalgridbmunit
    WHERE lo.rn = 1
    ORDER BY lo.unavailableCapacity DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    
    if df.empty:
        print("⚠️ No outages data found")
        return
    
    print(f"✅ Retrieved {len(df)} outages")
    
    # Calculate summary stats
    total_outages = len(df)
    total_mw = df['unavailableCapacity'].sum()
    avg_mw = df['unavailableCapacity'].mean()
    
    # Update summary stats
    sheet.update('K6', [[total_outages]])
    sheet.update('K7', [[f'{total_mw:,.0f}']])
    sheet.update('K8', [[f'{avg_mw:,.0f}']])
    
    # ===== OUTAGES TABLE =====
    print("📋 Creating outages table...")
    
    # Table header at row 10
    header = [['Asset Name', 'BM Unit', 'Fuel Type', 'Normal (MW)', 'Unavail (MW)', 
               'Visual', 'Cause', 'Start Time', 'End Time', 'Status']]
    sheet.update('A10', header)
    
    # Fuel type emojis
    fuel_emoji = {
        'NUCLEAR': '⚛️', 'CCGT': '🔥', 'WIND OFFSHORE': '💨',
        'WIND ONSHORE': '💨', 'HYDRO PUMPED STORAGE': '⚡',
        'BIOMASS': '🌱', 'COAL': '⛏️', 'FOSSIL GAS': '🔥'
    }
    
    # Build data rows
    data_rows = []
    for _, row in df.iterrows():
        bmu_id = row['affectedUnit']
        asset_name = MANUAL_ASSET_NAMES.get(bmu_id) or row['assetName'] or bmu_id
        fuel = row['fuelType'] or 'Unknown'
        emoji = fuel_emoji.get(fuel.upper(), '🔥')
        mw = row['unavailableCapacity']
        
        pct = (mw / row['normalCapacity'] * 100) if row['normalCapacity'] > 0 else 0
        filled = int(pct / 10)
        bar = '��' * filled + '⬜' * (10 - filled) + f' {pct:.1f}%'
        
        data_rows.append([
            f"{emoji} {asset_name}",
            bmu_id,
            fuel,
            f"{row['normalCapacity']:,.0f}",
            f"{mw:,.0f}",
            bar,
            row['cause'] or 'Unknown',
            row['start_time'] or 'N/A',
            row['end_time'] or 'Ongoing',
            row['eventStatus']
        ])
    
    # Update data (starting at row 11)
    if data_rows:
        sheet.update('A11', data_rows)
        print(f"✅ Added {len(data_rows)} outage records")
    
    # ===== HISTORICAL TREND DATA =====
    print("📈 Fetching historical trend data...")
    
    trend_query = f"""
    WITH daily_generation AS (
        SELECT 
            CAST(settlementDate AS DATE) as date,
            SUM(generation) / 1000.0 as generation_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY date
        UNION ALL
        SELECT 
            CAST(settlementDate AS DATE) as date,
            SUM(generation) / 1000.0 as generation_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
          AND settlementDate < CURRENT_DATE()
        GROUP BY date
    ),
    daily_demand AS (
        SELECT 
            CAST(settlementDate AS DATE) as date,
            AVG(initialDemandOutturn) / 1000.0 as demand_gw
        FROM `{PROJECT_ID}.{DATASET}.demand_outturn`
        WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY date
    ),
    daily_outages AS (
        SELECT 
            CAST(eventStartTime AS DATE) as date,
            SUM(unavailableCapacity) / 1000.0 as outages_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStartTime >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
          AND eventStatus = 'Active'
        GROUP BY date
    )
    SELECT 
        COALESCE(g.date, d.date) as date,
        AVG(d.demand_gw) as demand_gw,
        AVG(g.generation_gw) as generation_gw,
        AVG(COALESCE(o.outages_gw, 0)) as outages_gw
    FROM daily_generation g
    FULL OUTER JOIN daily_demand d ON g.date = d.date
    LEFT JOIN daily_outages o ON COALESCE(g.date, d.date) = o.date
    GROUP BY date
    ORDER BY date
    """
    
    trend_df = bq_client.query(trend_query).to_dataframe()
    
    # Add chart data section (column M onwards)
    chart_start_row = 10
    sheet.update(f'M{chart_start_row}', [['CHART DATA - Last 30 Days']])
    sheet.update(f'M{chart_start_row + 1}', [['Date', 'Demand (GW)', 'Generation (GW)', 'Outages (GW)']])
    
    if not trend_df.empty:
        chart_data = []
        for _, row in trend_df.iterrows():
            chart_data.append([
                row['date'].strftime('%Y-%m-%d'),
                f"{row['demand_gw']:.2f}",
                f"{row['generation_gw']:.2f}",
                f"{row['outages_gw']:.2f}"
            ])
        sheet.update(f'M{chart_start_row + 2}', chart_data)
        print(f"✅ Added {len(chart_data)} days of chart data")
    
    # ===== FORMATTING =====
    print("🎨 Applying formatting...")
    
    # Title formatting
    fmt_title = CellFormat(
        backgroundColor=Color(0.2, 0.2, 0.2),
        textFormat=TextFormat(bold=True, fontSize=16, foregroundColor=Color(1, 1, 1)),
        horizontalAlignment='CENTER'
    )
    format_cell_range(sheet, 'A1:O1', fmt_title)
    sheet.merge_cells('A1:O1')
    
    # Timestamp
    fmt_timestamp = CellFormat(
        backgroundColor=Color(0.95, 0.95, 0.95),
        textFormat=TextFormat(italic=True, fontSize=10),
        horizontalAlignment='CENTER'
    )
    format_cell_range(sheet, 'A2:O2', fmt_timestamp)
    sheet.merge_cells('A2:O2')
    
    # Filter section header
    fmt_filter_header = CellFormat(
        backgroundColor=Color(0.3, 0.5, 0.8),
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
        horizontalAlignment='LEFT'
    )
    format_cell_range(sheet, 'A4:O4', fmt_filter_header)
    
    # Summary stats header
    fmt_summary = CellFormat(
        backgroundColor=Color(0.8, 0.5, 0.2),
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
        horizontalAlignment='CENTER'
    )
    format_cell_range(sheet, 'J5:K5', fmt_summary)
    sheet.merge_cells('J5:K5')
    
    # Table header
    fmt_table_header = CellFormat(
        backgroundColor=Color(0.2, 0.2, 0.2),
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE'
    )
    format_cell_range(sheet, 'A10:J10', fmt_table_header)
    
    # Chart data header
    format_cell_range(sheet, 'M10:P10', fmt_table_header)
    format_cell_range(sheet, 'M11:P11', fmt_table_header)
    
    # Freeze header rows
    sheet.freeze(rows=10, cols=2)
    
    # Set column widths
    sheet.format('A:A', {'columnWidth': 300})
    sheet.format('B:B', {'columnWidth': 120})
    sheet.format('C:C', {'columnWidth': 120})
    sheet.format('D:E', {'columnWidth': 100})
    sheet.format('F:F', {'columnWidth': 180})
    sheet.format('G:G', {'columnWidth': 200})
    sheet.format('H:I', {'columnWidth': 140})
    sheet.format('J:J', {'columnWidth': 100})
    
    print("=" * 80)
    print("✅ LIVE OUTAGES SHEET CREATED SUCCESSFULLY")
    print(f"   - {len(data_rows)} outages listed")
    print(f"   - {len(chart_data) if not trend_df.empty else 0} days of trend data")
    print(f"   - Total unavailable: {total_mw:,.0f} MW")
    print("=" * 80)
    print("\n📊 Next steps:")
    print("   1. Open the sheet in Google Sheets")
    print("   2. Select chart data (M11:P40) and Insert → Chart")
    print("   3. Choose Line Chart with Date as X-axis")
    print("   4. Add data validation for filter dropdowns (A6, C6, E6, G6)")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
