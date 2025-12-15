#!/usr/bin/env python3
"""
Ask Gemini to Analyze the Enhanced BI Analysis Sheet
Reads current data from the sheet and asks Gemini for insights
"""

import pickle
import os
from datetime import datetime
import gspread
import google.generativeai as genai

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Analysis BI Enhanced'

print("=" * 80)
print("🤖 ASK GEMINI: ANALYZE POWER MARKET DATA")
print("=" * 80)
print()

# Initialize Google Sheets
print("🔧 Connecting to Google Sheets...")
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet(SHEET_NAME)
print("✅ Connected to sheet")
print()

# Initialize Gemini
print("🤖 Connecting to Gemini AI...")
# Get API key from environment or file
gemini_api_key = os.environ.get('GEMINI_API_KEY')
if not gemini_api_key:
    try:
        with open('gemini_api_key.txt', 'r') as f:
            gemini_api_key = f.read().strip()
    except FileNotFoundError:
        print("❌ ERROR: Gemini API key not found!")
        print()
        print("Please either:")
        print("  1. Set environment variable: export GEMINI_API_KEY='your-key'")
        print("  2. Create file: gemini_api_key.txt with your API key")
        print()
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        exit(1)

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')
print("✅ Connected to Gemini")
print()

# Read current data from sheet
print("📖 Reading current data from sheet...")

# Read summary metrics
metrics = {
    'total_generation': sheet.acell('B10').value,
    'renewable_pct': sheet.acell('B13').value,
    'avg_frequency': sheet.acell('D10').value,
    'avg_price': sheet.acell('F10').value,
    'peak_demand': sheet.acell('D13').value,
    'grid_stability': sheet.acell('F13').value,
}

# Read date range
date_range = sheet.acell('B5').value
custom_from = sheet.acell('D5').value
custom_to = sheet.acell('F5').value

# Read generation mix (top 10 fuel types)
gen_data = sheet.get('A18:G27')  # Top 10 rows
gen_headers = gen_data[0] if gen_data else []
gen_rows = gen_data[1:] if len(gen_data) > 1 else []

# Read frequency data (last 5 records)
freq_data = sheet.get('A38:E42')  # Top 5 rows
freq_headers = freq_data[0] if freq_data else []
freq_rows = freq_data[1:] if len(freq_data) > 1 else []

# Read price data (last 5 records)
price_data = sheet.get('A63:F67')  # Top 5 rows
price_headers = price_data[0] if price_data else []
price_rows = price_data[1:] if len(price_data) > 1 else []

# Read balancing data (last 5 records)
bsad_data = sheet.get('A88:F92')  # Top 5 rows
bsad_headers = bsad_data[0] if bsad_data else []
bsad_rows = bsad_data[1:] if len(bsad_data) > 1 else []

print("✅ Data collected")
print()

# Build prompt for Gemini
print("🧠 Building analysis prompt...")

prompt = f"""You are an expert UK power market analyst. Analyze the following real-time data from the GB power grid and provide actionable insights.

**DATE RANGE**: {date_range} ({custom_from} to {custom_to})

**SUMMARY METRICS**:
- Total Generation: {metrics['total_generation']}
- Renewable %: {metrics['renewable_pct']}
- Average Frequency: {metrics['avg_frequency']}
- Average Market Price: {metrics['avg_price']}
- Peak Demand: {metrics['peak_demand']}
- Grid Stability: {metrics['grid_stability']}

**GENERATION MIX** (Top Fuel Types):
{chr(10).join([f"- {row[0]}: {row[1]} MWh ({row[3]}% share)" for row in gen_rows[:10] if len(row) > 3])}

**RECENT FREQUENCY MEASUREMENTS**:
{chr(10).join([f"- {row[0]}: {row[1]} Hz (deviation: {row[2]} mHz) - {row[3]}" for row in freq_rows[:5] if len(row) > 3])}

**RECENT MARKET PRICES**:
{chr(10).join([f"- {row[0]} SP{row[1]}: £{row[2]}/MWh" for row in price_rows[:5] if len(row) > 2])}

**RECENT BALANCING COSTS**:
{chr(10).join([f"- {row[0]} SP{row[1]}: Net £{row[3]}" for row in bsad_rows[:5] if len(row) > 3])}

Please provide:

1. **Key Observations**: What stands out in the data?
2. **Grid Health Assessment**: How is the grid performing?
3. **Renewable Performance**: How are renewables contributing?
4. **Market Insights**: What do prices and balancing costs tell us?
5. **Concerns & Opportunities**: Any issues or opportunities to note?
6. **Recommendations**: What should operators/traders focus on?

Keep the analysis concise, actionable, and focused on the UK power market context.
"""

print("✅ Prompt ready")
print()

# Ask Gemini
print("🤖 Asking Gemini to analyze data...")
print("   (This may take 10-20 seconds...)")
print()

try:
    response = model.generate_content(prompt)
    analysis = response.text
    
    print("=" * 80)
    print("📊 GEMINI ANALYSIS")
    print("=" * 80)
    print()
    print(analysis)
    print()
    print("=" * 80)
    
    # Write analysis back to sheet
    print()
    print("💾 Writing analysis to sheet...")
    
    # Find a good place for the analysis (after all tables)
    analysis_start_row = 115
    
    # Clear previous analysis
    sheet.update(f'A{analysis_start_row}:O{analysis_start_row+50}', [['' for _ in range(15)] for _ in range(51)])
    
    # Write header
    sheet.update(f'A{analysis_start_row}:O{analysis_start_row}', [['🤖 GEMINI AI ANALYSIS']])
    sheet.format(f'A{analysis_start_row}:O{analysis_start_row}', {
        'backgroundColor': {'red': 0.102, 'green': 0.137, 'blue': 0.494},
        'textFormat': {'bold': True, 'fontSize': 14, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Write timestamp
    sheet.update(f'A{analysis_start_row+2}', [[f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])
    sheet.format(f'A{analysis_start_row+2}', {
        'textFormat': {'italic': True, 'fontSize': 9}
    })
    
    # Write analysis text (split into lines for better readability)
    analysis_lines = analysis.split('\n')
    analysis_data = [[line] for line in analysis_lines[:40]]  # Limit to 40 lines
    
    if analysis_data:
        sheet.update(f'A{analysis_start_row+4}:A{analysis_start_row+4+len(analysis_data)-1}', analysis_data)
        sheet.format(f'A{analysis_start_row+4}:O{analysis_start_row+4+len(analysis_data)-1}', {
            'textFormat': {'fontSize': 10},
            'wrapStrategy': 'WRAP'
        })
    
    print("✅ Analysis written to sheet (starting at row 115)")
    print()
    
    # Update the "Ask Gemini" button cell
    sheet.update('J5', [['🤖 Click to refresh →']])
    sheet.format('J5', {
        'backgroundColor': {'red': 0.2, 'green': 0.8, 'blue': 0.4},
        'textFormat': {'bold': True, 'fontSize': 10},
        'horizontalAlignment': 'CENTER'
    })
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("💡 Tips:")
    print("  - Make sure your Gemini API key is valid")
    print("  - Check your internet connection")
    print("  - Verify you have API quota available")
    exit(1)

print("=" * 80)
print("✅ COMPLETE!")
print("=" * 80)
print()
print("📄 View analysis in sheet:")
print(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print()
print("🔄 To refresh analysis:")
print("  python3 ask_gemini_analysis.py")
print()
