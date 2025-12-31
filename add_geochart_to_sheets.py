#!/usr/bin/env python3
"""
Add Google Geo Chart to Dashboard
Creates interactive geographic visualization IN Google Sheets using Geo Chart
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def get_constraint_data_for_geochart():
    """Get constraint data formatted for Google Geo Chart"""

    print("\n📊 Querying constraint data by region...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Query last 7 days by GSP region with Google-compatible naming
    sql = f"""
    WITH recent_constraints AS (
      SELECT
        b.acceptanceTime,
        b.bmUnit,
        ABS(b.levelTo - b.levelFrom) as volume_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris` b
      WHERE b.acceptanceTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
    ),

    by_region AS (
      SELECT
        r.gsp_group,
        COUNT(*) as acceptance_count,
        SUM(c.volume_mw) as total_volume_mw,
        COUNT(DISTINCT c.bmUnit) as bmu_count
      FROM recent_constraints c
      JOIN `{PROJECT_ID}.{DATASET}.ref_bmu_canonical` r
        ON c.bmUnit = r.bmu_id
      WHERE r.gsp_group IS NOT NULL
      GROUP BY r.gsp_group
    )

    SELECT
      -- Map GSP groups to Google Geo Chart province names with UK prefix
      CASE
        WHEN gsp_group = 'Eastern' THEN 'GB-ENG-East of England'
        WHEN gsp_group = 'East Midlands' THEN 'GB-ENG-East Midlands'
        WHEN gsp_group = 'London' THEN 'GB-ENG-London'
        WHEN gsp_group = 'Merseyside and Northern Wales' THEN 'GB-WLS'
        WHEN gsp_group = 'Midlands' THEN 'GB-ENG-West Midlands'
        WHEN gsp_group = 'North Eastern' THEN 'GB-ENG-North East'
        WHEN gsp_group = 'North Western' THEN 'GB-ENG-North West'
        WHEN gsp_group = 'Northern' THEN 'GB-ENG-North East'
        WHEN gsp_group = 'North Scotland' THEN 'GB-SCT'
        WHEN gsp_group = 'South Eastern' THEN 'GB-ENG-South East'
        WHEN gsp_group = 'Southern' THEN 'GB-ENG-South East'
        WHEN gsp_group = 'South Wales' THEN 'GB-WLS'
        WHEN gsp_group = 'South Western' THEN 'GB-ENG-South West'
        WHEN gsp_group = 'Yorkshire' THEN 'GB-ENG-Yorkshire and the Humber'
        WHEN gsp_group = 'South Scotland' THEN 'GB-SCT'
        ELSE CONCAT('GB-', gsp_group)
      END as region,
      total_volume_mw,
      acceptance_count,
      bmu_count,
      gsp_group as original_gsp_name
    FROM by_region
    ORDER BY total_volume_mw DESC
    """

    df = client.query(sql).to_dataframe()
    print(f"✅ Retrieved {len(df)} regions")

    return df

def add_geochart_to_sheets(df):
    """Add constraint data to Google Sheets in format for Geo Chart"""

    print("\n📊 Adding Geo Chart data to Google Sheets...")

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'inner-cinema-credentials.json', scope)

    client = gspread.authorize(creds)

    # Try to create new sheet or use existing
    try:
        spreadsheet = client.open_by_key(SHEET_ID)
        try:
            sheet = spreadsheet.worksheet('Constraint Geo Map')
            print("  Using existing 'Constraint Geo Map' sheet")
        except:
            sheet = spreadsheet.add_worksheet(title='Constraint Geo Map', rows=100, cols=10)
            print("  ✅ Created new sheet: 'Constraint Geo Map'")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return

    # Prepare data for Geo Chart (needs specific format)
    # Google Geo Chart requires: Region, Value, [optional tooltip]

    print("\n  Formatting data for Geo Chart...")

    # Header
    data = [
        ['Region', 'Constraint Volume (MW)', 'Acceptances', 'BMUs', 'GSP Group'],
    ]

    # Data rows - aggregate by Google region name (multiple GSP groups may map to same region)
    region_totals = {}
    for _, row in df.iterrows():
        region = str(row['region'])
        if region not in region_totals:
            region_totals[region] = {
                'volume': 0,
                'acceptances': 0,
                'bmus': 0,
                'gsp_names': []
            }
        region_totals[region]['volume'] += float(row['total_volume_mw'])
        region_totals[region]['acceptances'] += int(row['acceptance_count'])
        region_totals[region]['bmus'] += int(row['bmu_count'])
        region_totals[region]['gsp_names'].append(str(row['original_gsp_name']))

    # Add aggregated rows
    for region, totals in sorted(region_totals.items(), key=lambda x: x[1]['volume'], reverse=True):
        data.append([
            region,
            totals['volume'],
            totals['acceptances'],
            totals['bmus'],
            ', '.join(totals['gsp_names'])
        ])

    # Clear sheet and write data
    sheet.clear()
    sheet.update(values=data, range_name='A1')

    print(f"  ✅ Added {len(data)-1} regions to sheet")

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
        [''],
        ['📊 INSTRUCTIONS: How to Create Geo Chart'],
        [''],
        ['1. Select cells A1:B' + str(len(data))],
        ['2. Click: Insert → Chart'],
        ['3. Chart type: Geo chart'],
        ['4. Chart editor → Setup → Geo:'],
        ['   - Region: Type "826" (UK ISO code) OR "GB"'],
        ['   - Display mode: Regions'],
        ['5. Customize → Chart style:'],
        ['   - Color gradient: White → Red'],
        ['   - Title: "GB Constraint Costs by Region (Last 7 Days)"'],
        ['5. Move chart to desired location on dashboard'],
        [''],
        ['💡 Tip: The map will show constraint intensity by color'],
        ['   Darker red = Higher constraint volume'],
    ]

    sheet.update(values=instructions, range_name='F1')

    # Format instructions
    sheet.format('F2', {
        'textFormat': {'bold': True, 'fontSize': 11},
        'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.8}
    })

    sheet.format('F4:F12', {
        'textFormat': {'fontSize': 9},
        'wrapStrategy': 'WRAP'
    })

    print("  ✅ Added chart instructions")

    return sheet

def create_apps_script_geochart():
    """Generate Apps Script code to automatically create Geo Chart"""

    print("\n📜 Creating Apps Script for automatic Geo Chart...")

    script = """
/**
 * Automatically create Google Geo Chart from constraint data
 * Run this function once to add chart to dashboard
 */
function createConstraintGeoChart() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dataSheet = ss.getSheetByName('Constraint Geo Map');
  var dashboardSheet = ss.getSheetByName('Live Dashboard v2');

  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('Error: "Constraint Geo Map" sheet not found');
    return;
  }

  if (!dashboardSheet) {
    SpreadsheetApp.getUi().alert('Error: "Live Dashboard v2" sheet not found');
    return;
  }

  // Get data range (adjust if needed)
  var lastRow = dataSheet.getLastRow();
  var dataRange = dataSheet.getRange('A1:B' + lastRow);

  // Create chart
  var chart = dataSheet.newChart()
    .setChartType(Charts.ChartType.GEO)
    .addRange(dataRange)
    .setPosition(1, 6, 0, 0)  // Position on data sheet first
    .setOption('region', 'GB')  // United Kingdom
    .setOption('displayMode', 'regions')
    .setOption('resolution', 'provinces')  // Show regions/counties
    .setOption('colorAxis', {
      colors: ['#ffffff', '#ffcccc', '#ff9999', '#ff6666', '#ff0000']
    })
    .setOption('datalessRegionColor', '#f5f5f5')
    .setOption('defaultColor', '#cccccc')
    .setOption('tooltip', {isHtml: true})
    .setOption('legend', 'none')
    .setOption('title', 'GB Constraint Costs by Region (Last 7 Days)')
    .setOption('titleTextStyle', {
      fontSize: 14,
      bold: true
    })
    .setOption('backgroundColor', '#ffffff')
    .setOption('width', 500)
    .setOption('height', 600)
    .build();

  // Insert chart on data sheet
  dataSheet.insertChart(chart);

  Logger.log('✅ Geo Chart created on "Constraint Geo Map" sheet');
  Logger.log('💡 Manually move chart to "Live Dashboard v2" if desired');

  SpreadsheetApp.getUi().alert(
    'Chart Created!',
    'Geo Chart created on "Constraint Geo Map" sheet.\\n\\n' +
    'You can now move it to the dashboard sheet if desired.',
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

    with open('geochart_apps_script.gs', 'w') as f:
        f.write(script)

    print("  ✅ Created: geochart_apps_script.gs")
    print("\n  📋 Installation:")
    print("     1. Open dashboard → Extensions → Apps Script")
    print("     2. Create new file 'GeoChart.gs'")
    print("     3. Paste code from geochart_apps_script.gs")
    print("     4. Save and refresh spreadsheet")
    print("     5. Use menu: 🗺️ Constraint Maps → Create Geo Chart")

def main():
    print("="*80)
    print("GOOGLE SHEETS GEO CHART - CONSTRAINT VISUALIZATION")
    print("="*80)

    # Get data
    df = get_constraint_data_for_geochart()

    if len(df) == 0:
        print("\n⚠️  No constraint data available")
        return

    # Show summary
    print("\n📈 Top 5 Regions by Constraint Volume:")
    print("="*80)
    for _, row in df.head(5).iterrows():
        print(f"  {row['region']:<30} {row['total_volume_mw']:>10,.0f} MW  ({row['acceptance_count']:>5} acceptances)")

    # Add to Sheets
    sheet = add_geochart_to_sheets(df)

    # Create Apps Script
    create_apps_script_geochart()

    print("\n" + "="*80)
    print("✅ GEO CHART DATA ADDED TO GOOGLE SHEETS")
    print("="*80)
    print(f"\nSheet: 'Constraint Geo Map' in dashboard")
    print(f"URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("\n📊 Next Steps:")
    print("  1. Open the 'Constraint Geo Map' sheet")
    print("  2. Follow instructions in column F to create chart")
    print("  OR")
    print("  3. Install Apps Script (geochart_apps_script.gs) for automatic creation")
    print("\n💡 The Geo Chart will show UK map with regions colored by constraint intensity")

if __name__ == "__main__":
    main()
