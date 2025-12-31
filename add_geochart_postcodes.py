#!/usr/bin/env python3
"""
Add Google Geo Chart to Sheets using UK Postcodes
Uses postcode prefixes from BMU data for unambiguous UK location
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def get_constraint_data_by_postcode():
    """Get constraint data by postcode prefix"""

    print("\n📊 Querying constraint data by postcode...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Query using postcode prefixes joined with SVA generator coordinates
    sql = f"""
    WITH recent_constraints AS (
      SELECT
        b.acceptanceTime,
        b.bmUnit,
        ABS(b.levelTo - b.levelFrom) as volume_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris` b
      WHERE b.acceptanceTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
    ),

    bmu_with_coords AS (
      SELECT
        r.bmu_id,
        r.gsp_group,
        s.postcode,
        s.lat,
        s.lng,
        -- Extract postcode district (first 3-4 chars before space)
        SPLIT(s.postcode, ' ')[OFFSET(0)] as postcode_district
      FROM `{PROJECT_ID}.{DATASET}.ref_bmu_canonical` r
      LEFT JOIN `{PROJECT_ID}.{DATASET}.sva_generators_with_coords` s
        ON UPPER(r.bmu_name) = UPPER(s.name)
      WHERE s.postcode IS NOT NULL
    ),

    by_postcode AS (
      SELECT
        COALESCE(b.postcode_district, LEFT(b.postcode, 3)) as postcode_prefix,
        b.gsp_group,
        AVG(b.lat) as lat,
        AVG(b.lng) as lng,
        COUNT(*) as acceptance_count,
        SUM(c.volume_mw) as total_volume_mw,
        COUNT(DISTINCT c.bmUnit) as bmu_count
      FROM recent_constraints c
      JOIN bmu_with_coords b
        ON c.bmUnit = b.bmu_id
      WHERE b.postcode_district IS NOT NULL
      GROUP BY postcode_prefix, b.gsp_group
    )

    SELECT
      UPPER(postcode_prefix) as postcode,
      gsp_group as region_name,
      lat,
      lng,
      total_volume_mw,
      acceptance_count,
      bmu_count
    FROM by_postcode
    ORDER BY total_volume_mw DESC
    LIMIT 100
    """

    df = client.query(sql).to_dataframe()
    print(f"✅ Retrieved {len(df)} postcode areas")

    if len(df) > 0:
        print(f"\n📈 Top 5 Postcode Areas by Constraint Volume:")
        print("="*80)
        for _, row in df.head(5).iterrows():
            region = row['region_name'] if row['region_name'] else 'Unknown'
            print(f"  {row['postcode']:6} ({region:30}) {row['total_volume_mw']:>8,.0f} MW  ({row['acceptance_count']:>4.0f} acceptances)")

    return df


def add_geochart_to_sheets(df):
    """Add postcode-based data to Google Sheets for Geo Chart"""

    print(f"\n📊 Adding Geo Chart data to Google Sheets...")

    # Authenticate with Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    client = gspread.authorize(creds)

    # Open spreadsheet
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    # Check if sheet exists
    try:
        sheet = spreadsheet.worksheet('Constraint Geo Map')
        print(f"  Using existing 'Constraint Geo Map' sheet")
        sheet.clear()
    except:
        sheet = spreadsheet.add_worksheet(title='Constraint Geo Map', rows=100, cols=10)
        print(f"  Created new 'Constraint Geo Map' sheet")

    print(f"\n  Formatting data for Geo Chart...")

    # Header - Google Geo Chart needs: Location (postcode), Value (numeric)
    data = [
        ['Postcode', 'Constraint Volume (MW)', 'Acceptances', 'BMUs', 'Region'],
    ]

    # Data rows - use UK postcode format
    for _, row in df.iterrows():
        # Format postcode with space if needed (e.g., "AB1" -> "AB1")
        postcode = str(row['postcode']).upper().strip()
        # Add "UK" suffix to ensure Google recognizes it as UK
        postcode_uk = f"{postcode}, UK"

        data.append([
            postcode_uk,
            float(row['total_volume_mw']),
            int(row['acceptance_count']),
            int(row['bmu_count']),
            str(row['region_name'])
        ])

    # Write to sheet
    sheet.update(values=data, range_name='A1')
    print(f"  ✅ Added {len(data)-1} postcode areas to sheet")

    # Format header
    sheet.format('A1:E1', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True
        },
        'horizontalAlignment': 'CENTER'
    })

    # Add instructions
    instructions = [
        ['📊 INSTRUCTIONS: How to Create Geo Chart'],
        [''],
        ['1. Select cells A1:B' + str(len(data))],
        ['2. Click: Insert → Chart'],
        ['3. Chart type: Geo chart'],
        ['4. Chart editor → Setup:'],
        ['   - Chart type: Geo chart'],
        ['   - Location: Column A (Postcode)'],
        ['   - Color: Column B (Volume)'],
        ['5. Customize → Chart style:'],
        ['   - Color gradient: White → Red'],
        ['   - Map should auto-detect UK from postcodes'],
        [''],
        ['💡 Postcodes are UK-specific and unambiguous'],
        ['💡 Chart will show heat map of constraint costs'],
    ]

    sheet.update(values=instructions, range_name='G1')
    print(f"  ✅ Added chart instructions")


def create_apps_script_geochart():
    """Generate Apps Script code for automatic Geo Chart creation"""

    script = """/**
 * Automatically create Google Geo Chart from postcode constraint data
 * Run this function once to add chart to dashboard
 */
function createConstraintGeoChart() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dataSheet = ss.getSheetByName('Constraint Geo Map');

  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('Error: "Constraint Geo Map" sheet not found');
    return;
  }

  // Get data range
  var lastRow = dataSheet.getLastRow();

  // Remove any existing charts first
  var charts = dataSheet.getCharts();
  for (var i = 0; i < charts.length; i++) {
    dataSheet.removeChart(charts[i]);
  }

  // Create geo chart with UK postcodes
  var range = dataSheet.getRange('A1:B' + lastRow);
  var chart = dataSheet.newChart()
    .setChartType(Charts.ChartType.GEO)
    .addRange(range)
    .setPosition(2, 7, 0, 0)
    .setOption('region', 'GB')
    .setOption('displayMode', 'markers')
    .setOption('colorAxis', {
      colors: ['#ffffff', '#ffcccc', '#ff6666', '#ff0000']
    })
    .setOption('title', 'GB Constraint Costs by Postcode (Last 7 Days)')
    .build();

  dataSheet.insertChart(chart);

  SpreadsheetApp.getUi().alert(
    'Chart Created!',
    'Geo Chart created using UK postcodes.\\n\\n' +
    'The map shows constraint locations across GB.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Add menu item to easily create chart
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ Constraint Maps')
    .addItem('Create Geo Chart', 'createConstraintGeoChart')
    .addToUi();
}
"""

    with open('geochart_postcodes_apps_script.gs', 'w') as f:
        f.write(script)

    print(f"\n📜 Creating Apps Script for automatic Geo Chart...")
    print(f"  ✅ Created: geochart_postcodes_apps_script.gs")
    print(f"\n  📋 Installation:")
    print(f"     1. Open dashboard → Extensions → Apps Script")
    print(f"     2. Create new file 'GeoChart.gs'")
    print(f"     3. Paste code from geochart_postcodes_apps_script.gs")
    print(f"     4. Save and refresh spreadsheet")
    print(f"     5. Use menu: 🗺️ Constraint Maps → Create Geo Chart")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("GOOGLE SHEETS GEO CHART - UK POSTCODE-BASED VISUALIZATION")
    print("="*80)

    # Get constraint data by postcode
    df = get_constraint_data_by_postcode()

    if len(df) == 0:
        print("\n❌ No postcode data found in ref_bmu_canonical")
        print("   Run: python3 add_postcode_to_canonical.py")
        exit(1)

    # Add to Google Sheets
    add_geochart_to_sheets(df)

    # Create Apps Script
    create_apps_script_geochart()

    print("\n" + "="*80)
    print("✅ GEO CHART DATA ADDED TO GOOGLE SHEETS (POSTCODE-BASED)")
    print("="*80)
    print(f"\nSheet: 'Constraint Geo Map' in dashboard")
    print(f"URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print(f"\n📊 Next Steps:")
    print(f"  1. Open the 'Constraint Geo Map' sheet")
    print(f"  2. Follow instructions in column G to create chart")
    print(f"  OR")
    print(f"  3. Install Apps Script (geochart_postcodes_apps_script.gs) for automatic creation")
    print(f"\n💡 Postcodes are UK-specific - no ambiguity with other countries!")
