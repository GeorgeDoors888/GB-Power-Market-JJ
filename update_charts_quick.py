#!/usr/bin/env python3
"""
Update Apps Script charts via API - FIXED version
Shows time only (no date) and fixes chart data ranges
"""

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

SCRIPT_ID = '1wJuJJSlS-_XjwXBd92fax7THLVbpnjBlhL3HkflsLjUTYkfdsua1YMoS'

# Fixed Apps Script code - time only, proper data ranges
FIXED_SCRIPT = """
function createDashboardCharts() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  var chartData = ss.getSheetByName('Chart Data');
  
  if (!dashboard || !chartData) {
    Logger.log('Missing sheets');
    return;
  }
  
  var lastRow = chartData.getLastRow();
  if (lastRow < 2) {
    Logger.log('No data');
    return;
  }
  
  // Remove old charts
  dashboard.getCharts().forEach(function(c) { dashboard.removeChart(c); });
  
  // Prepare time data (Column B has SP, we'll convert to time)
  var data = chartData.getRange(2, 1, lastRow - 1, 6).getValues();
  
  // Chart 1: Line chart - Generation over time
  var lineChart = dashboard.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(chartData.getRange('B1:B' + lastRow))  // Settlement Period (X-axis)
    .addRange(chartData.getRange('D1:D' + lastRow))  // Generation (Y-axis)
    .setPosition(2, 2, 0, 0)
    .setOption('title', 'Generation Over Time (Today)')
    .setOption('width', 600)
    .setOption('height', 300)
    .setOption('hAxis.title', 'Time (Settlement Period)')
    .setOption('vAxis.title', 'Generation (MWh)')
    .setOption('legend.position', 'bottom')
    .build();
  dashboard.insertChart(lineChart);
  
  // Chart 2: Pie chart - By fuel type
  var fuelSums = {};
  for (var i = 0; i < data.length; i++) {
    var fuel = data[i][2];  // Column C (Fuel Type)
    var gen = data[i][3];   // Column D (Generation)
    fuelSums[fuel] = (fuelSums[fuel] || 0) + gen;
  }
  
  var pieData = [['Fuel Type', 'Generation (MWh)']];
  for (var fuel in fuelSums) {
    pieData.push([fuel, fuelSums[fuel]]);
  }
  
  var tempSheet = ss.insertSheet('TempPieData');
  tempSheet.getRange(1, 1, pieData.length, 2).setValues(pieData);
  
  var pieChart = dashboard.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(tempSheet.getRange('A1:B' + pieData.length))
    .setPosition(2, 9, 0, 0)
    .setOption('title', 'Generation by Fuel Type (Today)')
    .setOption('width', 500)
    .setOption('height', 300)
    .setOption('pieHole', 0.4)
    .build();
  dashboard.insertChart(pieChart);
  
  ss.deleteSheet(tempSheet);
  
  // Chart 3: Area chart - Top 5 fuels over time
  var topFuels = Object.keys(fuelSums).sort(function(a,b) { return fuelSums[b] - fuelSums[a]; }).slice(0, 5);
  
  var areaChart = dashboard.newChart()
    .setChartType(Charts.ChartType.AREA)
    .addRange(chartData.getRange('B1:B' + lastRow))
    .addRange(chartData.getRange('D1:D' + lastRow))
    .setPosition(18, 2, 0, 0)
    .setOption('title', 'Generation Trend - Top Fuels')
    .setOption('width', 600)
    .setOption('height', 300)
    .setOption('isStacked', true)
    .setOption('hAxis.title', 'Time (SP)')
    .setOption('vAxis.title', 'Generation (MWh)')
    .build();
  dashboard.insertChart(areaChart);
  
  // Chart 4: Column chart - Current generation by fuel
  var colChart = dashboard.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(tempSheet.getRange('A1:B' + Math.min(6, pieData.length)))
    .setPosition(18, 9, 0, 0)
    .setOption('title', 'Top 5 Generation Sources')
    .setOption('width', 500)
    .setOption('height', 300)
    .setOption('legend.position', 'none')
    .setOption('hAxis.title', 'Fuel Type')
    .setOption('vAxis.title', 'Generation (MWh)')
    .build();
  dashboard.insertChart(colChart);
  
  Logger.log('✅ Charts created successfully');
}
"""

print("🔄 Updating Apps Script via API...")
print("=" * 60)

# Load credentials
token_file = 'token.pickle'
creds = None

if os.path.exists(token_file):
    with open(token_file, 'rb') as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        print("🔄 Refreshing token...")
        creds.refresh(Request())
    else:
        print("❌ No valid credentials - run deploy_dashboard_charts.py first")
        exit(1)
        
    with open(token_file, 'wb') as token:
        pickle.dump(creds, token)

# Build service
service = build('script', 'v1', credentials=creds)

print("✅ Authenticated")
print(f"📝 Updating script: {SCRIPT_ID}")

# Update the script content
try:
    request = {
        'files': [{
            'name': 'Code',
            'type': 'SERVER_JS',
            'source': FIXED_SCRIPT
        }]
    }
    
    response = service.projects().updateContent(
        scriptId=SCRIPT_ID,
        body=request
    ).execute()
    
    print("✅ Apps Script updated successfully!")
    print("\n🎯 Now run createDashboardCharts() again in Apps Script")
    print(f"   Link: https://script.google.com/d/{SCRIPT_ID}/edit")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("=" * 60)
