# HH Profile Generator - Setup Guide

**Created**: 22 November 2025  
**Status**: ✅ Working and tested

## Overview

Generates synthetic half-hourly (HH) load profiles based on demand parameters and writes them to the BESS sheet. Auto-clears existing data each time new data is generated.

## Features

- ✅ Realistic load profiles with daily, weekly, and seasonal patterns
- ✅ Configurable min/avg/max demand (kW)
- ✅ Auto-clears existing data before generating new profiles
- ✅ Writes to BESS sheet starting at row 19 (headers) and row 20 (data)
- ✅ Google Sheets button trigger integration
- ✅ Generates up to 1 year of data (17,520 HH periods)

## Sheet Setup

### 1. Add Parameter Cells

In the BESS sheet, add these cells (around row 16-19):

```
F16: "HH Profile Parameters:"
F17: "Minimum Demand kW"     G17: 500
F18: "Average Demand kW"     G18: 1500
F19: "Maximum Demand kW"     G19: 2500
```

**Quick Setup**: Run this in Apps Script:
```javascript
function setupHHSection() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  
  sheet.getRange('F17').setValue('Minimum Demand kW');
  sheet.getRange('G17').setValue(500);
  
  sheet.getRange('F18').setValue('Average Demand kW');
  sheet.getRange('G18').setValue(1500);
  
  sheet.getRange('F19').setValue('Maximum Demand kW');
  sheet.getRange('G19').setValue(2500);
  
  // Format
  sheet.getRange('F17:F19').setFontWeight('bold');
  sheet.getRange('G17:G19').setBackground('#E3F2FD');
}
```

### 2. Add "Generate HH Data" Button

1. Open BESS sheet in Google Sheets
2. **Insert** → **Drawing** → Create a button shape with text "Generate HH Data"
3. **Save and Close**
4. Click the three dots on the button → **Assign script**
5. Enter function name: `generateHHDataDirect` (for simple mode) or `generateHHData` (for webhook mode)
6. Click **OK**

### 3. Apps Script Setup

1. **Extensions** → **Apps Script**
2. Create new file: `generate_hh_button.gs`
3. Copy code from `generate_hh_button.gs` in the repo
4. **Save** (Ctrl+S)

## Usage

### Option 1: Direct Generation (Simple, No Backend)

Best for small datasets (7-30 days):

1. Enter demand parameters in cells G17:G19
2. Click "Generate HH Data" button
3. Profile appears immediately in rows 20+

**Pros**: Simple, no webhook needed  
**Cons**: Limited to ~1 week of data (336 HH periods), basic patterns

### Option 2: Webhook Mode (Full Features)

Best for large datasets (up to 365 days):

1. Start webhook server:
   ```bash
   cd "/Users/georgemajor/GB Power Market JJ"
   python3 dno_webhook_server.py
   ```

2. In another terminal, start ngrok:
   ```bash
   ngrok http 5001
   ```

3. Update webhook URL in `generate_hh_button.gs`:
   ```javascript
   const webhookUrl = 'https://YOUR_NGROK_URL/generate-hh-profile';
   ```

4. Enter demand parameters in G17:G19
5. Click "Generate HH Data" button
6. Script calls webhook → Python generates profile → Updates sheet

**Pros**: Realistic patterns, up to 1 year of data, seasonal variation  
**Cons**: Requires webhook server running

## Manual Command Line Usage

Generate HH profile directly from command line:

```bash
cd "/Users/georgemajor/GB Power Market JJ"

# Generate with defaults (500, 1500, 2500 kW, 365 days)
python3 generate_hh_profile.py

# Generate with custom parameters
python3 generate_hh_profile.py 500 1500 2500 7

# Arguments: min_kw avg_kw max_kw days
```

## Output Format

### Sheet Structure

```
Row 16: [Blank or title]
Row 17: "HH Profile Generated:" | <timestamp> | | 
Row 18: "Period:" | "2025-01-01 to 2025-01-07" | "Records: 336" | "Min/Avg/Max"
Row 19: Timestamp | Demand (kW) | Notes | Calculated  [HEADERS]
Row 20: 2025-01-01 00:00:00 | 1234.56 | | 
Row 21: 2025-01-01 00:30:00 | 1245.78 | |
...     [HH data continues]
```

### Data Columns

- **Column A**: Timestamp (YYYY-MM-DD HH:MM:SS format)
- **Column B**: Demand (kW) - Actual load value
- **Column C**: Notes - Empty (user can add notes)
- **Column D**: Calculated - Empty (for formulas/calculations)

## Load Profile Characteristics

The generated profile includes:

### Daily Pattern
- **00:00-06:00**: Low load (60% of average) - Night
- **06:00-09:00**: Ramping up (80-100%) - Morning
- **09:00-16:00**: High load (120% of average) - Daytime
- **16:00-20:00**: Peak load (130-140%) - Evening peak
- **20:00-23:00**: Declining (90-110%) - Late evening

### Weekly Pattern
- **Weekdays**: Full pattern as above
- **Weekends**: Reduced to 70% of weekday levels

### Seasonal Pattern
- **Winter** (Dec-Feb): 115% of base
- **Spring/Autumn**: 100% baseline
- **Summer** (Jun-Aug): 90% of base

### Random Variation
- ±10% random noise added to each HH period
- Ensures realistic variability

## Example Test

```bash
# Test with 7 days of data
python3 generate_hh_profile.py 500 1500 2500 7
```

**Expected Output**:
```
✅ HH PROFILE GENERATION COMPLETE!

📋 Summary:
   Sheet: BESS
   Rows: 19 to 355
   Periods: 336 (half-hourly)
   Duration: 7 days
   Min: 628.83 kW
   Avg: 1569.73 kW
   Max: 2500.00 kW
```

## Verification

### Check in Google Sheets

1. Open BESS sheet
2. Scroll to row 17-20
3. Verify:
   - Row 17: Generation timestamp
   - Row 18: Period summary
   - Row 19: Headers (Timestamp, Demand (kW), Notes, Calculated)
   - Row 20+: HH data

### Verify Data Quality

```python
# Read generated data
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file('inner-cinema-credentials.json')
gc = gspread.authorize(creds)
sh = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
ws = sh.worksheet('BESS')

# Get HH data
data = ws.get('A20:B1000')
print(f"Rows: {len(data)}")
print(f"First: {data[0]}")
print(f"Last: {data[-1]}")
```

## Troubleshooting

### "No data generated"

**Cause**: Script error or parameters invalid  
**Fix**: Check cells G17:G19 have numeric values where Min < Avg < Max

### "Timeout error"

**Cause**: Generating too many days (>365)  
**Fix**: Reduce days parameter or increase webhook timeout

### "Sheet not found"

**Cause**: Sheet name not "BESS"  
**Fix**: Verify sheet name or update `SHEET_ID` in script

### "Rows overlap existing data"

**Cause**: Other data below row 19  
**Fix**: Script auto-clears from row 20 onwards, move other data higher

## Integration with DUoS Calculator

Once HH data is generated, calculate DUoS costs:

```python
import pandas as pd
from duos_cost_calculator import DuosTariff, calculate_duos_costs

# Read HH data from sheet
# (code from verification section above)

# Convert to DataFrame
df = pd.DataFrame(data[1:], columns=['timestamp', 'kw'])
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['kw'] = pd.to_numeric(df['kw'])
df['kwh'] = df['kw'] * 0.5  # HH periods

# Define tariff (from DNO lookup)
tariff = DuosTariff(
    dno_id='14',
    tariff_name='NGED-WM HV',
    voltage_level='HV',
    red_rate=0.01764,
    amber_rate=0.00205,
    green_rate=0.00011
)

# Calculate costs
result = calculate_duos_costs(df, tariff, kva_capacity=2500)

# Annual cost
annual_cost = result['duos_total_cost'].sum() * 52  # Scale to year
print(f"Annual DUoS Cost: £{annual_cost:,.2f}")
```

## Files Created

1. ✅ `generate_hh_profile.py` - Python script (230 lines)
2. ✅ `generate_hh_button.gs` - Apps Script code (200 lines)
3. ✅ `dno_webhook_server.py` - Updated with `/generate-hh-profile` endpoint
4. ✅ `HH_GENERATOR_SETUP.md` - This file

## Next Steps

**Immediate**:
1. ✅ Add parameter cells to BESS sheet (run `setupHHSection()`)
2. ✅ Add "Generate HH Data" button
3. ✅ Test with 7 days: `python3 generate_hh_profile.py 500 1500 2500 7`

**Future Enhancements**:
1. Add profile templates (office, factory, retail, residential)
2. Import real HH data from CSV
3. Add seasonal sensitivity controls
4. Export HH data to CSV for analysis
5. Integrate with clustering features module

## Related Documentation

- `MPAN_DUOS_QUICKSTART.md` - DUoS cost calculator
- `DNO_DUOS_LOOKUP_SYSTEM.md` - DNO lookup system
- `duos_cost_calculator.py` - Apply tariffs to HH data
- `profile_clustering_features.py` - Extract features from profiles

---

**Last Updated**: 22 November 2025  
**Status**: ✅ Tested and working  
**Test Result**: 7-day profile generated successfully (336 HH periods)
