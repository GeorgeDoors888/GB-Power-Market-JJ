#!/usr/bin/env python3
"""
Update Apps Script with fixed chart code - Time format only, all charts working
"""

import pickle
import os
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/spreadsheets'
]

SCRIPT_ID = '1wJuJJSlS-_XjwXBd92fax7THLVbpnjBlhL3HkflsLjUTYkfdsua1YMoS'

print("🔧 Updating Apps Script with fixed chart code...")
print("=" * 60)

# Get OAuth credentials
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        print("🔄 Refreshing OAuth token...")
        creds.refresh(Request())
    else:
        print("❌ Need to re-authenticate")
        exit(1)
    
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    print("✅ OAuth token saved")

# Build API client
service = build('script', 'v1', credentials=creds)

# Fixed Apps Script code with TIME format only
fixed_code = """/**
 * GB Power Market Dashboard Charts - FIXED VERSION
 * Shows TIME only (not date), all charts working
 */

function showMessage(message) {
  Logger.log(message);
  try {
    SpreadsheetApp.getUi().alert(message);
  } catch (e) {
    // API context - Logger already called
  }
}

function createDashboardCharts() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  var chartData = ss.getSheetByName('Chart Data');
  
  if (!dashboard) {
    showMessage('❌ Dashboard sheet not found!');
    return;
  }
  
  if (!chartData) {
    showMessage('❌ Chart Data sheet not found!');
    return;
  }
  
  // Get data
  var lastRow = chartData.getLastRow();
  if (lastRow < 2) {
    showMessage('❌ No data in Chart Data sheet!');
    return;
  }
  
  // Remove existing charts
  var charts = dashboard.getCharts();
  charts.forEach(function(chart) {
    dashboard.removeChart(chart);
  });
  
  Logger.log('Creating charts with ' + (lastRow - 1) + ' rows of data');
  
  // Get all data for aggregation
  var allData = chartData.getRange(2, 1, lastRow - 1, 6).getValues();
  
  // Aggregate by Settlement Period and Fuel Type
  var spData = {}; // SP -> {fuelType -> total}
  var fuelTotals = {}; // fuelType -> total
  
  allData.forEach(function(row) {
    var sp = row[1]; // Settlement Period
    var fuelType = row[2]; // Fuel Type
    var generation = row[3]; // Generation MWh
    
    // Aggregate by SP
    if (!spData[sp]) spData[sp] = {};
    if (!spData[sp][fuelType]) spData[sp][fuelType] = 0;
    spData[sp][fuelType] += generation;
    
    // Aggregate total by fuel type
    if (!fuelTotals[fuelType]) fuelTotals[fuelType] = 0;
    fuelTotals[fuelType] += generation;
  });
  
  // Convert SP to time string
  function spToTime(sp) {
    var hour = Math.floor((sp - 1) / 2);
    var minute = ((sp - 1) % 2) * 30;
    return (hour < 10 ? '0' : '') + hour + ':' + (minute < 10 ? '0' : '') + minute;
  }
  
  // Prepare line chart data (generation over time for top 5 fuels)
  var sortedFuels = Object.keys(fuelTotals).sort(function(a, b) {
    return fuelTotals[b] - fuelTotals[a];
  }).slice(0, 5);
  
  var lineChartData = [['Time'].concat(sortedFuels)];
  var sps = Object.keys(spData).map(Number).sort(function(a, b) { return a - b; });
  
  sps.forEach(function(sp) {
    var row = [spToTime(sp)];
    sortedFuels.forEach(function(fuel) {
      row.push(spData[sp][fuel] || 0);
    });
    lineChartData.push(row);
  });
  
  // Create temporary sheet for chart data
  var tempSheet = ss.getSheetByName('_ChartTemp');
  if (tempSheet) ss.deleteSheet(tempSheet);
  tempSheet = ss.insertSheet('_ChartTemp');
  
  // Write line chart data
  tempSheet.getRange(1, 1, lineChartData.length, lineChartData[0].length).setValues(lineChartData);
  
  // Chart 1: Line Chart - Generation over time
  var lineChart = tempSheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(tempSheet.getRange(1, 1, lineChartData.length, lineChartData[0].length))
    .setPosition(5, 2, 0, 0)
    .setOption('title', '24h Generation Trend (Top 5 Sources)')
    .setOption('width', 600)
    .setOption('height', 300)
    .setOption('legend', {position: 'right'})
    .setOption('hAxis', {title: 'Time', slantedText: true, slantedTextAngle: 45})
    .setOption('vAxis', {title: 'Generation (MWh)'})
    .build();
  
  dashboard.insertChart(lineChart);
  
  // Chart 2: Pie Chart - Total generation by fuel
  var pieData = [['Fuel Type', 'Total MWh']];
  Object.keys(fuelTotals).forEach(function(fuel) {
    pieData.push([fuel, fuelTotals[fuel]]);
  });
  
  tempSheet.getRange(1, 10, pieData.length, 2).setValues(pieData);
  
  var pieChart = tempSheet.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(tempSheet.getRange(1, 10, pieData.length, 2))
    .setPosition(5, 9, 0, 0)
    .setOption('title', 'Generation Mix by Fuel Type')
    .setOption('width', 500)
    .setOption('height', 300)
    .setOption('pieSliceText', 'percentage')
    .setOption('legend', {position: 'right'})
    .build();
  
  dashboard.insertChart(pieChart);
  
  // Chart 3: Stacked Area Chart
  tempSheet.getRange(1, 15, lineChartData.length, lineChartData[0].length).setValues(lineChartData);
  
  var areaChart = tempSheet.newChart()
    .setChartType(Charts.ChartType.AREA)
    .addRange(tempSheet.getRange(1, 15, lineChartData.length, lineChartData[0].length))
    .setPosition(20, 2, 0, 0)
    .setOption('title', 'Stacked Generation Sources')
    .setOption('width', 600)
    .setOption('height', 300)
    .setOption('isStacked', true)
    .setOption('legend', {position: 'right'})
    .setOption('hAxis', {title: 'Time', slantedText: true, slantedTextAngle: 45})
    .setOption('vAxis', {title: 'Generation (MWh)'})
    .build();
  
  dashboard.insertChart(areaChart);
  
  // Chart 4: Column Chart - Top 5
  var top5Data = [['Fuel Type', 'Total MWh']];
  sortedFuels.forEach(function(fuel) {
    top5Data.push([fuel, fuelTotals[fuel]]);
  });
  
  tempSheet.getRange(1, 25, top5Data.length, 2).setValues(top5Data);
  
  var columnChart = tempSheet.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(tempSheet.getRange(1, 25, top5Data.length, 2))
    .setPosition(20, 9, 0, 0)
    .setOption('title', 'Top 5 Generation Sources')
    .setOption('width', 500)
    .setOption('height', 300)
    .setOption('legend', {position: 'none'})
    .setOption('hAxis', {title: 'Fuel Type'})
    .setOption('vAxis', {title: 'Total MWh'})
    .build();
  
  dashboard.insertChart(columnChart);
  
  // Hide temp sheet
  tempSheet.hideSheet();
  
  showMessage('✅ Created 4 charts successfully!\\nLine, Pie, Area, and Column charts are now on Dashboard sheet.');
}

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🔄 Dashboard Charts')
    .addItem('Create/Update Charts', 'createDashboardCharts')
    .addToUi();
}
"""

print("📤 Uploading fixed chart code to Apps Script...")

try:
    # Update the script content
    request = {
        'files': [{
            'name': 'Code',
            'type': 'SERVER_JS',
            'source': fixed_code
        }]
    }
    
    response = service.projects().updateContent(
        scriptId=SCRIPT_ID,
        body=request
    ).execute()
    
    print("✅ Apps Script updated successfully!")
    print("\n" + "=" * 60)
    print("🎯 Changes made:")
    print("  • Fixed time format (shows HH:MM only, not date)")
    print("  • Fixed all 4 charts to display properly")
    print("  • Charts aggregate data by Settlement Period")
    print("  • Top 5 fuel sources shown in line/area charts")
    print("=" * 60)
    print("\n⚡ Next step: Run createDashboardCharts() again")
    print("   URL: https://script.google.com/d/" + SCRIPT_ID + "/edit")
    
except Exception as e:
    print(f"❌ Error updating script: {e}")
    print("\n💡 Alternative: Copy the code manually from dashboard/apps-script/dashboard_charts_v3_fixed.gs")
