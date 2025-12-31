#!/usr/bin/env python3
"""
Add DNO Boundaries Geo Chart to Sheets using UK Postcodes
Shows Distribution Network Operator coverage areas across GB
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def get_dno_data_by_postcode():
    """Get DNO coverage by postcode from SVA generators"""

    print("\n📊 Querying DNO coverage by postcode...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Query DNO coverage using SVA generator postcodes
    sql = f"""
    WITH postcode_districts AS (
      SELECT
        dno,
        gsp,
        postcode,
        -- Extract postcode district (first part before space)
        SPLIT(postcode, ' ')[OFFSET(0)] as postcode_district,
        lat,
        lng,
        capacity_mw
      FROM `{PROJECT_ID}.{DATASET}.sva_generators_with_coords`
      WHERE postcode IS NOT NULL
        AND dno IS NOT NULL
        AND status = 'Operational'
    ),

    by_dno_postcode AS (
      SELECT
        dno,
        postcode_district,
        gsp,
        AVG(lat) as avg_lat,
        AVG(lng) as avg_lng,
        COUNT(*) as generator_count,
        SUM(capacity_mw) as total_capacity_mw
      FROM postcode_districts
      GROUP BY dno, postcode_district, gsp
    ),

    dno_summary AS (
      SELECT
        dno,
        COUNT(DISTINCT postcode_district) as postcode_count,
        COUNT(DISTINCT gsp) as gsp_count,
        SUM(generator_count) as total_generators,
        SUM(total_capacity_mw) as total_capacity_mw
      FROM by_dno_postcode
      GROUP BY dno
    )

    SELECT
      p.postcode_district as postcode,
      p.dno,
      p.gsp,
      p.avg_lat as lat,
      p.avg_lng as lng,
      p.generator_count,
      p.total_capacity_mw,
      s.total_generators as dno_total_generators,
      s.total_capacity_mw as dno_total_capacity_mw,
      s.postcode_count as dno_postcode_count
    FROM by_dno_postcode p
    JOIN dno_summary s ON p.dno = s.dno
    ORDER BY p.dno, p.total_capacity_mw DESC
    """

    df = client.query(sql).to_dataframe()
    print(f"✅ Retrieved {len(df)} postcode areas across DNOs")

    if len(df) > 0:
        # DNO summary
        dno_summary = df.groupby('dno').agg({
            'postcode': 'count',
            'total_capacity_mw': 'sum',
            'generator_count': 'sum'
        }).sort_values('total_capacity_mw', ascending=False)

        print(f"\n📈 DNO Coverage Summary:")
        print("="*100)
        print(f"{'DNO':40} {'Postcodes':>10} {'Capacity (MW)':>15} {'Generators':>12}")
        print("="*100)
        for dno, row in dno_summary.head(10).iterrows():
            print(f"{dno:40} {row['postcode']:>10.0f} {row['total_capacity_mw']:>15,.1f} {row['generator_count']:>12.0f}")

    return df


def add_dno_geochart_to_sheets(df):
    """Add DNO postcode data to Google Sheets for Geo Chart"""

    print(f"\n📊 Adding DNO Geo Chart data to Google Sheets...")

    # Authenticate with Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    client = gspread.authorize(creds)

    # Open spreadsheet
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    # Check if sheet exists
    try:
        sheet = spreadsheet.worksheet('DNO Boundaries Map')
        print(f"  Using existing 'DNO Boundaries Map' sheet")
        sheet.clear()
    except:
        sheet = spreadsheet.add_worksheet(title='DNO Boundaries Map', rows=500, cols=12)
        print(f"  Created new 'DNO Boundaries Map' sheet")

    print(f"\n  Formatting data for Geo Chart...")

    # Header - Google Geo Chart needs: Location (postcode), Value (numeric), DNO name
    data = [
        ['Postcode', 'Capacity (MW)', 'Generators', 'DNO', 'GSP', 'DNO Total (MW)', 'Lat', 'Lng'],
    ]

    # Data rows - use UK postcode format with ", UK" suffix
    for _, row in df.iterrows():
        postcode = str(row['postcode']).upper().strip()
        postcode_uk = f"{postcode}, UK"

        # Handle NaN/None values
        capacity = float(row['total_capacity_mw']) if pd.notna(row['total_capacity_mw']) else 0.0
        generators = int(row['generator_count']) if pd.notna(row['generator_count']) else 0
        dno_total = float(row['dno_total_capacity_mw']) if pd.notna(row['dno_total_capacity_mw']) else 0.0
        lat = float(row['lat']) if pd.notna(row['lat']) else 0.0
        lng = float(row['lng']) if pd.notna(row['lng']) else 0.0

        data.append([
            postcode_uk,
            capacity,
            generators,
            str(row['dno']),
            str(row['gsp']),
            dno_total,
            lat,
            lng
        ])

    # Write to sheet
    sheet.update(values=data, range_name='A1')
    print(f"  ✅ Added {len(data)-1} postcode areas to sheet")

    # Format header
    sheet.format('A1:H1', {
        'backgroundColor': {'red': 0.1, 'green': 0.6, 'blue': 0.3},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True
        },
        'horizontalAlignment': 'CENTER'
    })

    # Add instructions
    instructions = [
        ['📊 INSTRUCTIONS: DNO Boundary Visualization'],
        [''],
        ['METHOD 1: Create Geo Chart (Recommended)'],
        ['1. Select cells A1:B' + str(len(data))],
        ['2. Click: Insert → Chart'],
        ['3. Chart type: Geo chart'],
        ['4. Map will show DNO coverage by postcode'],
        ['5. Color intensity = Generation capacity'],
        [''],
        ['METHOD 2: Manual Analysis'],
        ['• Column D shows DNO name'],
        ['• Column E shows GSP group'],
        ['• Filter by DNO to see their coverage area'],
        ['• Postcodes are UK-specific (no ambiguity)'],
        [''],
        ['📍 DNO Coverage Areas:'],
        ['• Scottish Power = Scotland + parts of Wales/England'],
        ['• Northern Powergrid = North East & Yorkshire'],
        ['• Electricity North West = Lancashire & Cumbria'],
        ['• UKPN (UK Power Networks) = London, South East, East'],
        ['• SSE (SSEN) = Southern England & North Scotland'],
        ['• Western Power = South West & Wales'],
        [''],
        ['💡 Data shows operational generators only'],
        ['💡 Each postcode colored by total MW capacity'],
    ]

    sheet.update(values=instructions, range_name='J1')
    print(f"  ✅ Added instructions and DNO reference")


def create_dno_apps_script():
    """Generate Apps Script code for automatic DNO Geo Chart"""

    script = """/**
 * Automatically create DNO Boundaries Geo Chart from postcode data
 * Shows Distribution Network Operator coverage areas across GB
 */
function createDnoBoundariesChart() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dataSheet = ss.getSheetByName('DNO Boundaries Map');

  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('Error: "DNO Boundaries Map" sheet not found');
    return;
  }

  // Get data range
  var lastRow = dataSheet.getLastRow();

  // Remove any existing charts first
  var charts = dataSheet.getCharts();
  for (var i = 0; i < charts.length; i++) {
    dataSheet.removeChart(charts[i]);
  }

  // Create geo chart with UK postcodes - colored by capacity
  var range = dataSheet.getRange('A1:B' + lastRow);
  var chart = dataSheet.newChart()
    .setChartType(Charts.ChartType.GEO)
    .addRange(range)
    .setPosition(2, 10, 0, 0)
    .setOption('region', 'GB')
    .setOption('displayMode', 'markers')
    .setOption('colorAxis', {
      colors: ['#90EE90', '#32CD32', '#228B22', '#006400']  // Light to dark green
    })
    .setOption('sizeAxis', {minValue: 0, maxSize: 10})
    .setOption('title', 'DNO Coverage by Generation Capacity (MW)')
    .setOption('width', 700)
    .setOption('height', 600)
    .build();

  dataSheet.insertChart(chart);

  SpreadsheetApp.getUi().alert(
    'DNO Map Created!',
    'Geo Chart shows DNO boundaries via UK postcodes.\\n\\n' +
    'Each marker represents a postcode area.\\n' +
    'Color intensity = Generation capacity in that area.\\n\\n' +
    'Filter column D to see individual DNO coverage.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Create comparison chart showing DNO total capacities
 */
function createDnoComparisonChart() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dataSheet = ss.getSheetByName('DNO Boundaries Map');

  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('Error: "DNO Boundaries Map" sheet not found');
    return;
  }

  // Aggregate by DNO
  var data = dataSheet.getDataRange().getValues();
  var dnoTotals = {};

  // Skip header row
  for (var i = 1; i < data.length; i++) {
    var dno = data[i][3];  // Column D
    var capacity = data[i][1];  // Column B

    if (dno && capacity) {
      if (!dnoTotals[dno]) {
        dnoTotals[dno] = 0;
      }
      dnoTotals[dno] += capacity;
    }
  }

  // Create summary sheet
  var summarySheet;
  try {
    summarySheet = ss.getSheetByName('DNO Summary');
    summarySheet.clear();
  } catch(e) {
    summarySheet = ss.insertSheet('DNO Summary');
  }

  // Write summary data
  var summaryData = [['DNO', 'Total Capacity (MW)']];
  for (var dno in dnoTotals) {
    summaryData.push([dno, dnoTotals[dno]]);
  }
  summarySheet.getRange(1, 1, summaryData.length, 2).setValues(summaryData);

  // Create bar chart
  var summaryRange = summarySheet.getRange('A1:B' + summaryData.length);
  var barChart = summarySheet.newChart()
    .setChartType(Charts.ChartType.BAR)
    .addRange(summaryRange)
    .setPosition(2, 4, 0, 0)
    .setOption('title', 'DNO Generation Capacity Comparison')
    .setOption('hAxis', {title: 'Capacity (MW)'})
    .setOption('vAxis', {title: 'DNO'})
    .setOption('legend', {position: 'none'})
    .setOption('width', 600)
    .setOption('height', 400)
    .build();

  summarySheet.insertChart(barChart);

  SpreadsheetApp.getUi().alert('DNO comparison chart created on "DNO Summary" sheet!');
}

/**
 * Add menu items
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ DNO Maps')
    .addItem('Create Boundary Map', 'createDnoBoundariesChart')
    .addItem('Create Comparison Chart', 'createDnoComparisonChart')
    .addToUi();
}
"""

    with open('dno_boundaries_apps_script.gs', 'w') as f:
        f.write(script)

    print(f"\n📜 Creating Apps Script for DNO visualizations...")
    print(f"  ✅ Created: dno_boundaries_apps_script.gs")
    print(f"\n  📋 Installation:")
    print(f"     1. Open dashboard → Extensions → Apps Script")
    print(f"     2. Create new file 'DnoBoundaries.gs'")
    print(f"     3. Paste code from dno_boundaries_apps_script.gs")
    print(f"     4. Save and refresh spreadsheet")
    print(f"     5. Use menu: 🗺️ DNO Maps → Create Boundary Map")


if __name__ == "__main__":
    print("\n" + "="*100)
    print("GOOGLE SHEETS - DNO BOUNDARIES VIA UK POSTCODES")
    print("="*100)

    # Get DNO data by postcode
    df = get_dno_data_by_postcode()

    if len(df) == 0:
        print("\n❌ No DNO postcode data found")
        exit(1)

    # Add to Google Sheets
    add_dno_geochart_to_sheets(df)

    # Create Apps Script
    create_dno_apps_script()

    print("\n" + "="*100)
    print("✅ DNO BOUNDARY DATA ADDED TO GOOGLE SHEETS")
    print("="*100)
    print(f"\nSheet: 'DNO Boundaries Map' in dashboard")
    print(f"URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print(f"\n📊 Visualization Options:")
    print(f"  1. Geo Chart: Shows DNO coverage via UK postcode markers")
    print(f"  2. Bar Chart: Compares total capacity by DNO")
    print(f"  3. Filter column D: View individual DNO coverage areas")
    print(f"\n💡 All data remains in BigQuery - Sheets is just visualization layer")
