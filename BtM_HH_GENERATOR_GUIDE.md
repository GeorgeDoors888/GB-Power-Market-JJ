# BtM HH Data Generator - Apps Script Installation

## 📋 Quick Setup (5 minutes)

### Step 1: Open Apps Script Editor
1. Open your Google Sheet: [GB Power Market Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)
2. Click **Extensions** > **Apps Script**
3. A new tab will open with the Apps Script editor

### Step 2: Add the Code
1. **Delete** any existing code in the editor
2. **Copy** the entire contents of `btm_hh_generator.gs`
3. **Paste** into the Apps Script editor
4. **Save** (Ctrl+S or File > Save)
5. Name the project: "BtM HH Generator"

### Step 3: Test It
1. **Close** the Apps Script tab
2. **Refresh** your Google Sheet (F5)
3. You should see a new menu: **⚡ BtM Tools**
4. Click **⚡ BtM Tools** > **🔄 Generate HH Data**
5. Confirm the popup (it will take 10-15 seconds)
6. Success! Check the "HH DATA" sheet

## 🎯 How It Works

### Menu Options

**🔄 Generate HH Data** (`produceHHData` function)
- Reads parameters from BtM sheet:
  - B17: Min kW
  - B18: Avg kW
  - B19: Max kW
  - B20: Supply Type
- Deletes old HH DATA (if exists)
- Generates 17,520 periods (365 days × 48 SP)
- Creates formatted sheet with headers

**📊 View HH DATA Sheet** (`viewHHDataSheet` function)
- Navigates to HH DATA sheet
- Jumps to cell A1

### Generated Data Structure

| Column | Description |
|--------|-------------|
| A: Timestamp | Date + time (YYYY-MM-DD HH:MM) |
| B: Settlement Period | 1-48 (SP number) |
| C: Day Type | "Weekday" or "Weekend" |
| D: Demand (kW) | Scaled demand based on profile |
| E: Profile % | Base profile percentage (0-100%) |

### Profile Types (from B20 dropdown)

1. **Domestic** - Residential: Peak 60-65% at 6-8pm
2. **Commercial** - Office/retail: Peak 75-78% at 10am-3pm
3. **Industrial** - Manufacturing: Steady 70-78% during day
4. **Network Rail** - Rail infrastructure: Peak 48-50% at 3-4pm
5. **EV Charging** - Charging stations: Peak 83% at 7pm
6. **Datacentre** - Server farms: Constant 84% baseload
7. **Non-Variable** - Constant: Flat 100% 24/7
8. **Solar and Storage** - Solar+battery: 25-50% variable
9. **Storage** - Pure battery: 25-50% variable
10. **Solar and Wind and Storage** - Multi-gen+storage: 25-50% variable

## ⚙️ How Parameters Work

The system scales profiles from **Min kW** to **Max kW**:

```
Demand (kW) = Min kW + (Profile % / 100) × (Max kW - Min kW)
```

**Example** (Commercial profile):
- Min kW: 500
- Max kW: 1500
- Profile at 3pm: 75%
- **Result**: 500 + (75/100) × (1500-500) = **1,250 kW**

## 🔧 Troubleshooting

### Error: "Function produceHHData could not be found"
**Cause**: Apps Script code not installed or saved correctly

**Solution**:
1. Go to Extensions > Apps Script
2. Check if `btm_hh_generator.gs` code is present
3. Click Save (disk icon)
4. Refresh your Google Sheet
5. Menu should appear

### Error: "Script timeout"
**Cause**: Apps Script has 6-minute execution limit

**Solution**: This shouldn't happen (generation takes ~10-15 seconds), but if it does:
1. Reduce the number of days from 365 to 180
2. Or use the Python script instead: `python3 generate_hh_data.py`

### Menu "⚡ BtM Tools" doesn't appear
**Solution**:
1. Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
2. Check Apps Script: Make sure `onOpen()` function exists
3. Close and reopen the spreadsheet

### Data looks wrong
**Check**:
1. B17-B20 values are correct
2. B20 matches one of the 10 profile types exactly (case-sensitive)
3. Min kW < Max kW

## 🚀 Alternative: Python Script

If you prefer running locally (faster, no timeout limits):

```bash
cd ~/GB-Power-Market-JJ
python3 generate_hh_data.py
```

**Advantages**:
- 10x faster (1-2 seconds vs 10-15 seconds)
- No timeout limits
- Can process multiple years
- Better logging

**Disadvantages**:
- Requires terminal access
- Need Python environment configured

## 📊 Usage Workflow

### Typical Workflow:
1. **Adjust Parameters** in BtM sheet
   - B17: Min kW (e.g., 300)
   - B18: Avg kW (e.g., 800)
   - B19: Max kW (e.g., 1200)
   - B20: Supply Type (e.g., "Industrial")

2. **Generate Data**
   - Click **⚡ BtM Tools** > **🔄 Generate HH Data**
   - Wait 10-15 seconds
   - Click OK on success message

3. **View Results**
   - Click **⚡ BtM Tools** > **📊 View HH DATA Sheet**
   - Or manually navigate to "HH DATA" tab

4. **Analyze**
   - Use HH DATA for battery arbitrage modeling
   - Calculate DUoS charge savings
   - Model VLP revenue opportunities

## 🎓 Technical Details

### Apps Script Limitations
- **Execution time**: 6 minutes max
- **Write operations**: 10,000 cells max per batch
- **Batching**: Data written in 1,000-row chunks
- **Random variation**: ±5% added to profile percentages

### Performance
- **Generation time**: 10-15 seconds (17,520 rows)
- **Sheet size**: ~1.5 MB (5 columns × 17,520 rows)
- **Memory**: Efficient batching prevents timeout

### Data Quality
- **Profiles**: Based on real UK HH settlement data
- **Variation**: Random ±5% mimics real-world volatility
- **Weekday/Weekend**: Different patterns for each
- **Settlement Periods**: Correct 48 SP per day
- **Timestamps**: Half-hourly (00:00, 00:30, 01:00...)

## 📝 Files Created

1. **btm_hh_generator.gs** - Apps Script code (230 lines)
2. **generate_hh_data.py** - Python alternative (180 lines)
3. **BtM_HH_GENERATOR_GUIDE.md** - This guide

## 🆘 Support

If you encounter issues:
1. Check this guide's Troubleshooting section
2. Check Apps Script logs: View > Logs (in Apps Script editor)
3. Run Python version for detailed error messages
4. Verify BtM sheet parameter cells exist and have values

---

**Last Updated**: December 30, 2025  
**Version**: 1.0  
**Status**: ✅ Production Ready
