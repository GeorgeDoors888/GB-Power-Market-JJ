# BtM Calculate 2 Button - Setup Guide

**Purpose**: Assign the "Calculate 2" button in BtM sheet to automatically calculate DNO and DUoS rates

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Open Apps Script

1. Open the BtM spreadsheet: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/edit
2. Click **Extensions → Apps Script**
3. Apps Script editor will open in new tab

### Step 2: Add the Code

1. In Apps Script editor, click the **+** next to "Files"
2. Select **Script**
3. Name it: `BtM_Calculate`
4. Delete any default code
5. Copy all code from: `/home/george/GB-Power-Market-JJ/btm_calculate_button.gs`
6. Paste into the editor
7. Click **Save** (💾 icon or Ctrl+S)
8. Close Apps Script editor

### Step 3: Assign Button to Script

1. Go back to BtM sheet in Google Sheets
2. Find the "Calculate 2" button (drawing/shape)
3. **Right-click** the button
4. Select **"Assign script"** from menu
5. In the dialog that appears, type: `calculateDuos`
6. Click **OK**

### Step 4: Test the Button

1. Enter test data:
   - **A6** (Postcode): `LS1 2TW`
   - **B6** (MPAN): `23`
   - **B9** (Voltage): `HV`

2. Click the **"Calculate 2"** button

3. You should see a dialog showing:
   ```
   📊 DNO & DUoS Calculation

   📍 Postcode (A6): LS1 2TW
   🆔 MPAN (B6): 23
   ⚡ Voltage (B9): HV

   🖥️  Run this command:

   python3 btm_dno_lookup.py
   ```

4. Open terminal and run:
   ```bash
   cd /home/george/GB-Power-Market-JJ
   python3 btm_dno_lookup.py
   ```

5. Check BtM sheet - cells C6:D6 and B9:D10 should now be populated with DNO details and DUoS rates!

---

## 📋 What the Button Does

### Input Cells (Read)
- **A6**: Postcode (e.g., "LS1 2TW")
- **B6**: MPAN ID or full MPAN (e.g., "23" or "1405566778899")
- **B9**: Voltage level (LV/HV/EHV)

### Output Cells (Written by Python Script)
- **C6**: DNO Key (e.g., "NPg-Y")
- **D6**: DNO Name (e.g., "Northern Powergrid (Yorkshire)")
- **B9**: Red rate (p/kWh)
- **C9**: Amber rate (p/kWh)
- **D9**: Green rate (p/kWh)
- **B10**: Red time schedule
- **C10**: Amber time schedule
- **D10**: Green time schedule

---

## 🎯 Usage Examples

### Example 1: Lookup by Postcode
```
A6: LS1 2TW
B6: (leave empty)
B9: HV

→ Click "Calculate 2"
→ Run: python3 btm_dno_lookup.py
→ Result: NPg-Y (Yorkshire) HV rates
```

### Example 2: Lookup by MPAN ID
```
A6: (leave empty)
B6: 14
B9: LV

→ Click "Calculate 2"
→ Run: python3 btm_dno_lookup.py
→ Result: NGED-WM (West Midlands) LV rates
```

### Example 3: Lookup by Full MPAN
```
A6: (leave empty)
B6: 1405566778899
B9: HV

→ Click "Calculate 2"
→ Run: python3 btm_dno_lookup.py
→ Result: Parses MPAN → ID 14 → NGED-WM HV rates
```

---

## 🔧 Additional Features

### Menu Items

The script also adds a **"🔌 DNO Tools"** menu with:

- **🔄 Calculate DUoS Rates** - Same as button (alternative trigger)
- **📖 View Documentation** - Shows usage guide
- **ℹ️ About** - Shows version and info

### Test Function

To verify setup, run `testBtmAccess()` in Apps Script:

1. Open Apps Script editor
2. Select `testBtmAccess` from function dropdown
3. Click **Run** (▶️)
4. Check logs for success message

### Clear Results

To reset output cells, run `clearDuosResults()`:
- Clears C6:D6 (DNO details)
- Clears C9:D9 (DUoS rates, keeps voltage in B9)
- Clears B10:D10 (time schedules)

---

## 🐛 Troubleshooting

### Issue: "Script function calculateDuos could not be found"

**Solution**:
1. Verify code is saved in Apps Script editor
2. Refresh Google Sheets page
3. Try assigning button again

### Issue: Button shows wrong function name

**Solution**:
1. Right-click button → **Remove script**
2. Right-click button → **Assign script** → Type `calculateDuos`

### Issue: "BtM sheet not found"

**Solution**:
- Verify sheet is named exactly "BtM" (case-sensitive)
- Check you're in the right spreadsheet

### Issue: Python script not updating sheet

**Solution**:
```bash
# Check credentials
ls -la inner-cinema-credentials.json

# Test BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected')"

# Test Sheets API
python3 -c "import gspread; print('✅ gspread installed')"

# Run with verbose output
python3 btm_dno_lookup.py
```

---

## 📊 Expected Output Example

After running `python3 btm_dno_lookup.py` with MPAN 23 HV:

```
================================================================================
BtM SHEET DNO LOOKUP - DUoS Rate Calculator
================================================================================

📊 Reading from BtM sheet:
   Postcode (A6): LS1 2TW
   MPAN (B6): 23
   Voltage (B9): HV

✅ Simple MPAN ID: 23

🎯 Using MPAN ID: 23

🔍 Querying BigQuery for MPAN ID 23...
   ✅ Found: Northern Powergrid (Yorkshire)

✅ DNO Details:
   Key: NPg-Y
   Name: Northern Powergrid (Yorkshire)
   Region: Yorkshire

💰 Looking up DUoS rates for NPg-Y HV...
   ✅ Found 3 rate bands

💰 DUoS Rates (HV):
   Red:   5.0000 p/kWh - 16:00-19:30
   Amber: 1.6000 p/kWh - 08:00-16:00, 19:30-22:00
   Green: 0.4000 p/kWh - 00:00-08:00, All Weekend

📝 Updating BtM sheet...
   ✅ Updated DNO: NPg-Y
   ✅ Updated rates: Red=5.000, Amber=1.600, Green=0.400 p/kWh
   ✅ Updated time schedules

================================================================================
✅ BtM SHEET UPDATED SUCCESSFULLY
================================================================================

🔗 View sheet: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
```

**Sheet cells updated**:
- C6: `NPg-Y`
- D6: `Northern Powergrid (Yorkshire)`
- B9: `5.0000`
- C9: `1.6000`
- D9: `0.4000`
- B10: `16:00-19:30`
- C10: `08:00-16:00 | 19:30-22:00`
- D10: `00:00-08:00 | All Weekend`

---

## 🚀 Future Enhancement: Auto-Execution

Currently requires manual command execution. Future webhook integration will enable:

1. Click "Calculate 2" button
2. ✅ Results appear automatically (no terminal command needed)

**Setup** (when ready):
```bash
# Start webhook server
python3 btm_webhook_server.py &

# Or use systemd service
sudo systemctl start btm-webhook
```

See: `dno_webhook_server.py` for webhook implementation

---

## 📚 Related Documentation

- **Complete System**: `DNO_MPAN_DUOS_LOOKUP_SYSTEM.md`
- **MPAN Parsing**: `mpan_generator_validator.py`
- **DNO Reference**: `.github/copilot-instructions.md` (DNO section)
- **DUoS Rates**: BigQuery tables `gb_power.duos_unit_rates` + `duos_time_bands`

---

## ✅ Checklist

- [ ] Apps Script code added and saved
- [ ] Button assigned to `calculateDuos` function
- [ ] Test data entered (A6, B6, B9)
- [ ] Button clicked - dialog appears
- [ ] Python script executed: `python3 btm_dno_lookup.py`
- [ ] Results appear in cells C6:D6, B9:D10
- [ ] Verified DNO name and rates are correct

---

**Created**: December 22, 2025
**Status**: ✅ Ready to use
**Maintainer**: George Major
