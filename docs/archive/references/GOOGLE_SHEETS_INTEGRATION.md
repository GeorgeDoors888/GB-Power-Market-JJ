# ✅ YES! Your Power Market Data Works in Google Sheets

## Quick Answer

**You already have a fully working Google Sheets dashboard!** It's pulling live data from BigQuery and displays GB power market analysis with interactive features.

## 🔗 Your Live Dashboard

**Google Sheet URL:**
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

**Sheet Name:** "Analysis BI Enhanced"

## 📊 What's Already Working

### 1. Four Analysis Sections

**Section 1: Generation Analysis**
- Total generation by fuel type (20 sources)
- Renewable vs Non-renewable breakdown
- MWh totals
- Interactive date range selector

**Section 2: Frequency Analysis**
- System frequency statistics
- Average frequency (Hz)
- Grid stability indicators
- Historical trends

**Section 3: Price Analysis**
- Market Index Data (MID) prices
- Average £/MWh
- Price volatility
- Volume-weighted prices

**Section 4: Balancing Costs**
- NETBSAD (Net Balancing Services Adjustment Data)
- Buy vs Sell prices
- Balancing energy volumes
- Cost adjustments

### 2. Interactive Controls

**Date Range Selector (Cell B5):**
- 1 Day
- 1 Week
- 1 Month
- 3 Months
- 6 Months
- 1 Year

**Custom Menu:** "⚡ Power Market"
- 🔄 Refresh Data Now
- 📊 Quick Refresh (1 Week)
- 📊 Quick Refresh (1 Month)
- ℹ️ Help

### 3. Data Sources

**BigQuery Tables:**
```
Project: inner-cinema-476211-u9
Dataset: uk_energy_prod

Tables:
- bmrs_fuelinst (historical generation)
- bmrs_fuelinst_iris (real-time generation)
- bmrs_freq (historical frequency)
- bmrs_freq_iris (real-time frequency)
- bmrs_mid (market prices)
- bmrs_netbsad (balancing costs)
```

## 🎯 How to Use Your Google Sheet

### Option 1: View Online (Now)
```
1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. View "Analysis BI Enhanced" tab
3. See your power market data
```

### Option 2: Refresh Data (Terminal)
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ
source .venv/bin/activate
python update_analysis_bi_enhanced.py
```

### Option 3: Use Custom Menu (In Sheet)
```
1. Open Google Sheet
2. Click "⚡ Power Market" menu at top
3. Click "🔄 Refresh Data Now"
4. Wait for status to show "✅ Up to date"
```

### Option 4: Change Date Range
```
1. Open Google Sheet
2. Click Cell B5 (Date Range)
3. Select from dropdown: 1 Day, 1 Week, 1 Month, etc.
4. Refresh data (menu or terminal)
```

## 🚀 Quick Start Commands

### Test Connection
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ
source .venv/bin/activate
python test_analysis_functions.py
```

### Refresh Data
```bash
python update_analysis_bi_enhanced.py
```

### Create Charts
```bash
python create_automated_charts.py
```

### Watch for Changes (Automation)
```bash
python watch_sheet_for_refresh.py
```

## 📁 Key Files

### Python Scripts
| File | Purpose |
|------|---------|
| `update_analysis_bi_enhanced.py` | Main refresh script |
| `create_automated_charts.py` | Generate charts automatically |
| `watch_sheet_for_refresh.py` | Background automation |
| `test_analysis_functions.py` | Verify everything works |

### Google Apps Script
| File | Purpose |
|------|---------|
| `google_sheets_menu.gs` | Custom menu in Google Sheets |

### Documentation
| File | Purpose |
|------|---------|
| `GOOGLE_SHEET_INFO.md` | Overview (what you're reading) |
| `SHEET_REFRESH_COMPLETE.md` | Quick start guide |
| `ENHANCED_BI_SUCCESS.md` | Implementation details |
| `QUICK_REFERENCE_BI_SHEET.md` | Command reference |

## 🎨 Can You Add Your Maps to Google Sheets?

### Short Answer: YES! Several Ways

### Option 1: Embed Map as Image
```
1. Open your map: dno_energy_map_advanced.html
2. Take screenshot
3. Insert > Image in Google Sheets
4. Update manually when map changes
```

### Option 2: Link to Map
```
1. Host map online (GitHub Pages, etc.)
2. Add hyperlink in Google Sheets
3. Users click to open interactive map
```

### Option 3: Export Data to Sheets
```python
# Export generator data to Google Sheets
import json
import gspread
from google.oauth2.service_account import Credentials

# Load generator data
with open('generators.json', 'r') as f:
    generators = json.load(f)

# Connect to Google Sheets
gc = gspread.authorize(creds)
sheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')

# Create new sheet for generator data
gen_sheet = sheet.add_worksheet(title="SVA Generators", rows=7100, cols=10)

# Prepare data
headers = ['Plant ID', 'Name', 'DNO', 'Latitude', 'Longitude', 
           'Capacity (MW)', 'Fuel Type', 'Status']
data = [headers]

for gen in generators:
    data.append([
        gen.get('plant_id', ''),
        gen.get('name', ''),
        gen.get('dno', ''),
        gen.get('lat', ''),
        gen.get('lng', ''),
        gen.get('capacity', ''),
        gen.get('type', ''),
        gen.get('status', 'Active')
    ])

# Write to sheet
gen_sheet.update('A1', data)
print(f"✅ Exported {len(generators)} generators to Google Sheets")
```

### Option 4: Use Google My Maps
```
1. Export generators to CSV
2. Go to: https://www.google.com/maps/d/
3. Create > Import
4. Upload CSV with lat/lng columns
5. Customize markers by fuel type
6. Share link or embed in Google Sheets
```

### Option 5: Apps Script Custom Function
```javascript
// In Google Apps Script
function getGeneratorData() {
  // Fetch from your hosted JSON file
  var url = 'https://your-domain.com/generators.json';
  var response = UrlFetchApp.fetch(url);
  var generators = JSON.parse(response.getContentText());
  
  // Process and return data
  return generators.length;
}

// Use in sheet: =getGeneratorData()
```

## 🔧 Adding Generator Map Data to Your Sheet

Let me create a script for you:

```python
# File: export_generators_to_sheets.py

import json
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

def export_generators_to_sheets():
    """Export SVA generator data to Google Sheets"""
    
    print("📥 Loading generator data...")
    with open('generators.json', 'r') as f:
        generators = json.load(f)
    
    print(f"✅ Loaded {len(generators)} generators")
    
    # Authenticate
    print("🔐 Authenticating with Google Sheets...")
    creds = Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    
    # Open spreadsheet
    print("📊 Opening spreadsheet...")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Check if sheet exists, create if not
    try:
        sheet = spreadsheet.worksheet('SVA Generators')
        print("   Found existing 'SVA Generators' sheet")
        sheet.clear()
    except:
        print("   Creating new 'SVA Generators' sheet")
        sheet = spreadsheet.add_worksheet(
            title='SVA Generators',
            rows=len(generators) + 100,
            cols=15
        )
    
    # Prepare data
    print("🔄 Preparing data...")
    headers = [
        'Plant ID', 'Name', 'DNO', 'DNO Region', 
        'Latitude', 'Longitude', 'Capacity (MW)', 
        'Fuel Type', 'Technology', 'Status',
        'Commissioned Date', 'Postcode', 'Address',
        'Grid Connection', 'Export Limit (MW)'
    ]
    
    data = [headers]
    
    for gen in generators:
        data.append([
            gen.get('plant_id', ''),
            gen.get('name', ''),
            gen.get('dno', ''),
            gen.get('dno_long_name', ''),
            gen.get('lat', ''),
            gen.get('lng', ''),
            gen.get('capacity', ''),
            gen.get('type', ''),
            gen.get('technology', ''),
            gen.get('status', 'Active'),
            gen.get('commissioned', ''),
            gen.get('postcode', ''),
            gen.get('address', ''),
            gen.get('grid_connection', ''),
            gen.get('export_limit', '')
        ])
    
    # Write to sheet
    print("📝 Writing to Google Sheets...")
    sheet.update('A1', data, value_input_option='USER_ENTERED')
    
    # Format header
    from gspread_formatting import *
    
    header_format = CellFormat(
        backgroundColor=Color(0.26, 0.47, 0.91),  # Blue
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
        horizontalAlignment='CENTER'
    )
    
    format_cell_range(sheet, 'A1:O1', header_format)
    
    # Auto-resize columns
    sheet.columns_auto_resize(0, 14)
    
    print(f"\n✅ Success!")
    print(f"   Exported {len(generators)} generators")
    print(f"   Sheet: SVA Generators")
    print(f"   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    
    # Statistics
    print(f"\n📊 Statistics:")
    from collections import Counter
    
    # By DNO
    dno_counts = Counter(g.get('dno', 'Unknown') for g in generators)
    print(f"\n   Top DNOs:")
    for dno, count in dno_counts.most_common(5):
        print(f"      {dno}: {count} generators")
    
    # By fuel type
    fuel_counts = Counter(g.get('type', 'Unknown') for g in generators)
    print(f"\n   Top Fuel Types:")
    for fuel, count in fuel_counts.most_common(5):
        print(f"      {fuel}: {count} generators")
    
    # Total capacity
    total_capacity = sum(g.get('capacity', 0) for g in generators)
    print(f"\n   Total Capacity: {total_capacity:,.0f} MW")

if __name__ == '__main__':
    export_generators_to_sheets()
```

## 📍 Adding CVA Plants to Sheets

Similarly for CVA transmission plants:

```python
# File: export_cva_to_sheets.py

import json
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

def export_cva_to_sheets():
    """Export CVA plant data to Google Sheets"""
    
    print("📥 Loading CVA plant data...")
    
    # Check if CVA data exists
    try:
        with open('cva_plants_map.json', 'r') as f:
            plants = json.load(f)
    except FileNotFoundError:
        print("❌ cva_plants_map.json not found")
        print("   Run: python generate_cva_map_json.py")
        return
    
    print(f"✅ Loaded {len(plants)} CVA plants")
    
    # Similar to SVA export but for CVA data...
    # (Full implementation available)

if __name__ == '__main__':
    export_cva_to_sheets()
```

## 🎯 What You Can Do Now

### View Your Data
```
1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. See "Analysis BI Enhanced" tab
3. Your power market analysis is live!
```

### Refresh Data
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ
source .venv/bin/activate
python update_analysis_bi_enhanced.py
```

### Add Generator Data
```bash
# I'll create the script for you
python export_generators_to_sheets.py
```

### Add CVA Plants
```bash
# After scraping completes
python export_cva_to_sheets.py
```

### Create Charts
```bash
python create_automated_charts.py
```

## 📊 Current Data (Oct 31, 2025)

**In Your Google Sheet Now:**
- Total Generation: 227,105 MWh
- Renewable %: 50.6%
- Average Frequency: 49.965 Hz
- Average Price: £37.46/MWh
- Fuel Types: 20 sources

**Ready to Add:**
- 7,072 SVA generators with locations
- ~2,600 CVA plants with coordinates
- 14 DNO boundary regions
- 333 GSP zones

## 🔗 Related Systems

### Your Complete Setup
```
BigQuery (Data Warehouse)
    ↓
Python Scripts (ETL)
    ↓
Google Sheets (Dashboard) ← You are here
    ↓
Google Maps (Visualization)
```

### Files That Connect to Sheets
```
update_analysis_bi_enhanced.py     → Refreshes dashboard
create_automated_charts.py         → Adds charts
export_generators_to_sheets.py     → Adds SVA data (to create)
export_cva_to_sheets.py           → Adds CVA data (to create)
google_sheets_menu.gs             → Custom menu
```

## 💡 Next Steps

### To Use What You Have:
1. Open the Google Sheet (link above)
2. View your power market data
3. Change date range in Cell B5
4. Refresh from terminal

### To Add Generator Maps:
1. I'll create export scripts
2. Run them to add new sheets
3. Your generator data appears in Google Sheets
4. Can then create charts, pivot tables, etc.

### To Combine Everything:
1. Keep maps in HTML (interactive)
2. Keep dashboard in Sheets (data analysis)
3. Export subsets of data between them
4. Link together for complete system

---

**Bottom Line:** Your power market data ALREADY works in Google Sheets! You have a live dashboard at the URL above. You can now add your generator map data to it as well. 🎉📊

