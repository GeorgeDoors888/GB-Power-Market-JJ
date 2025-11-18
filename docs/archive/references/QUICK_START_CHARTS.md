# Quick Start: Chart Automation

## 🚀 Create Your First Automated Chart (2 minutes)

### Step 1: Ensure Authentication
```bash
# Check if token exists
ls -lh token.pickle

# If not, or if expired, refresh it:
python refresh_token.py
```

### Step 2: Run Simple Example
```bash
# Creates a single SSP vs Date chart
python simple_chart_example.py
```

**Expected Output**:
```
📊 Simple Chart Creator
==================================================
🔑 Loading credentials...
✅ Connected to Google Sheets API

📈 Creating SSP vs Date chart...
✅ Chart created successfully!

📄 View at: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit
```

### Step 3: View Result
Open your spreadsheet - you'll see a new chart at **Row 3, Column M**

---

## 📊 Create Multiple Charts

### Run Full Chart Suite
```bash
# Creates 4 charts: Line, Pie, Column, Area
python create_automated_charts.py
```

**Charts Created**:
1. ✅ Bid-Offer Spread Trend (Line chart)
2. ✅ Generation Mix Distribution (Pie chart)
3. ✅ Intraday Spread Pattern (Column chart)
4. ✅ Demand Profile (Area chart)

---

## 🛠️ Customize Charts

### Edit Chart Configuration

Open `create_automated_charts.py` and modify the `charts_to_create` list:

```python
charts_to_create = [
    {
        "name": "My Custom Chart",
        "type": "LINE",  # Options: LINE, PIE, COLUMN, AREA
        "data_range": {
            "dates": {
                "startRow": 10,    # Your data start row
                "endRow": 100,     # Your data end row
                "startCol": 0,     # Column index (A=0, B=1, C=2...)
                "endCol": 1
            },
            "values": {
                "startRow": 10,
                "endRow": 100,
                "startCol": 3,     # Your value column
                "endCol": 4
            }
        },
        "axes": {
            "bottom": "Date",
            "left": "Price (£/MWh)"
        }
    }
]
```

### Column Index Reference
```
A = 0   (Date/Time)
B = 1   (Settlement Period)
C = 2   (Bid Price)
D = 3   (Offer Price)
E = 4   (Spread)
F = 5   (Fuel Type)
G = 6   (Generation)
H = 7   (Frequency)
I = 8   (SBP)
J = 9   (SSP)
K = 10
L = 11
M = 12  (where charts start)
```

---

## 🔍 Common Use Cases

### Use Case 1: Daily Price Trend
```python
{
    "name": "Daily SBP Trend",
    "type": "LINE",
    "data_range": {
        "dates": {"startRow": 10, "endRow": 100, "startCol": 0},
        "values": {"startRow": 10, "endRow": 100, "startCol": 8}  # Column I (SBP)
    },
    "axes": {"bottom": "Date", "left": "SBP (£/MWh)"}
}
```

### Use Case 2: Generation Mix Breakdown
```python
{
    "name": "Fuel Mix Today",
    "type": "PIE",
    "data_range": {
        "labels": {"startRow": 10, "endRow": 26, "startCol": 5},   # Column F (Fuel)
        "values": {"startRow": 10, "endRow": 26, "startCol": 6}    # Column G (MW)
    }
}
```

### Use Case 3: Settlement Period Pattern
```python
{
    "name": "Intraday Spread Pattern",
    "type": "COLUMN",
    "data_range": {
        "categories": {"startRow": 10, "endRow": 58, "startCol": 1},  # Column B (Periods)
        "values": {"startRow": 10, "endRow": 58, "startCol": 4}       # Column E (Spread)
    },
    "axes": {"bottom": "Settlement Period", "left": "Spread (£/MWh)"}
}
```

### Use Case 4: Frequency Stability
```python
{
    "name": "System Frequency",
    "type": "AREA",
    "data_range": {
        "time": {"startRow": 10, "endRow": 100, "startCol": 0},      # Column A (Time)
        "values": {"startRow": 10, "endRow": 100, "startCol": 7}     # Column H (Hz)
    },
    "axes": {"bottom": "Time", "left": "Frequency (Hz)"}
}
```

---

## 🎨 Chart Positioning

### Default Positions
Charts are stacked vertically starting at **Column M** (beyond your data):

- Chart 1: Row 2, Column M
- Chart 2: Row 22, Column M
- Chart 3: Row 42, Column M
- Chart 4: Row 62, Column M

### Customize Position
In `create_automated_charts.py`, modify:

```python
anchor_row = 2 + (position_index * 20)  # Change spacing here
anchor_col = 12  # Column M (change to move horizontally)
```

---

## ⚡ Quick Commands

```bash
# Refresh authentication
python refresh_token.py

# Create single test chart
python simple_chart_example.py

# Create full chart suite
python create_automated_charts.py

# View your spreadsheet
open "https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit"
```

---

## 🔧 Troubleshooting

### Charts Not Visible
**Cause**: Data range doesn't contain data  
**Fix**: Check your startRow/endRow values match where your data is

### "Invalid sheetId"
**Cause**: Wrong sheet ID  
**Fix**: Get correct sheet ID from spreadsheet:
```python
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
for sheet in spreadsheet['sheets']:
    print(f"{sheet['properties']['title']}: {sheet['properties']['sheetId']}")
```

### Authentication Error
**Cause**: Expired token  
**Fix**: Run `python refresh_token.py`

### Charts Overlapping
**Cause**: Position conflict  
**Fix**: Adjust `anchor_row` and `anchor_col` values

---

## 📚 Next Steps

1. ✅ **Create basic charts** using examples above
2. 📊 **Customize** for your specific data columns
3. 🔄 **Automate** with cron jobs (daily refresh)
4. 📧 **Add email** reports (see AUTOMATION_FRAMEWORK.md)
5. 🎯 **Build alerts** for extreme values

---

## 📖 Full Documentation

- **[AUTOMATION_FRAMEWORK.md](AUTOMATION_FRAMEWORK.md)** - Complete automation guide
- **[GOOGLE_DOCS_REPORT_SUMMARY.md](GOOGLE_DOCS_REPORT_SUMMARY.md)** - Report generation
- **[ENHANCED_BI_ANALYSIS_README.md](ENHANCED_BI_ANALYSIS_README.md)** - Dashboard guide

---

**Time to first chart**: 2 minutes  
**Difficulty**: Beginner  
**Prerequisites**: Python, token.pickle, Google Sheets API enabled
