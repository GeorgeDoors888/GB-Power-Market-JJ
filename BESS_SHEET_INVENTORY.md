# BESS Sheet - Complete Code Inventory

**Date:** 29 November 2025  
**Sheet Location:** Dashboard V2 (1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc)  
**Sheet Name:** `BESS`  
**Purpose:** Battery Energy Storage System - DNO Lookup & DUoS Tariff Calculator

---

## 📊 BESS Sheet Structure

**Dimensions:** 997 rows x 24 columns

### Key Sections:
- **Row 1:** Title - "BESS - Battery Energy Storage System"
- **Row 4:** Status bar with update timestamps
- **Row 5:** Headers - Postcode, MPAN ID, DNO Key, DNO Name, Short Code, Market Part., GSP Group ID, GSP Group
- **Row 6:** Data input/output row
- **Row 9:** Tariff headers - Voltage Level, Red/Amber/Green Rates, Profile Class, Meter Registration
- **Row 10:** Tariff data output
- **Row 15+:** Additional data sections

---

## 🐍 Python Scripts (32 files)

### Core Functionality

1. **`add_bess_dropdowns.py`**
   - Adds dropdown menus to BESS sheet
   - Voltage levels, profile classes

2. **`add_bess_dropdowns_v4.py`**
   - Updated version of dropdown handler

3. **`add_voltage_dropdown.py`**
   - Voltage level dropdown (HV, LV, EHV)

4. **`bess_auto_monitor.py`**
   - Monitors BESS sheet for changes
   - Triggers DNO lookups automatically

5. **`bess_auto_monitor_upcloud.py`**
   - Cloud-hosted version of auto-monitor

6. **`bess_export_reports.py`**
   - Exports BESS data to reports
   - Time band analysis

7. **`bigquery_to_sheets_updater.py`**
   - Updates BESS sheet from BigQuery
   - DUoS tariff data

8. **`check_bess_sheet.py`**
   - Quick structure checker
   - Displays first 20 rows (A1:H20)

9. **`check_bess_structure.py`**
   - Validates BESS sheet layout

10. **`create_bess_vlp_sheet.py`**
    - Creates BESS_VLP sheet (Virtual Lead Party)
    - Postcode to DNO lookup tool

11. **`dno_lookup_python.py`**
    - Main DNO lookup logic
    - Queries BigQuery for DNO data

12. **`enhance_bess_sheet_complete.py`**
    - Complete BESS sheet enhancement
    - Adds all features

13. **`enhance_bess_vlp_sheet.py`**
    - Enhances BESS_VLP sheet

14. **`install_dno_lookup.py`**
    - Installs DNO lookup functionality

15. **`link_duos_to_bess_sheet.py`**
    - Links DUoS tariff data to BESS

16. **`manual_update_nged.py`**
    - Manual update for NGED (National Grid Electricity Distribution)

17. **`parse_actual_mpan.py`**
    - Parses MPAN format
    - Updates BESS sheet with correct details

18. **`read_actual_mpan.py`**
    - Reads current BESS sheet data
    - Displays actual MPAN entries

19. **`read_current_mpan.py`**
    - Reads current MPAN data

20. **`reset_bess_layout.py`**
    - Resets BESS sheet to default layout
    - Clears all data

21. **`setup_mpan_details_section.py`**
    - Sets up MPAN details section

22. **`test_bess_vlp_lookup.py`**
    - Tests BESS_VLP lookup functionality

23. **`test_mpan_details.py`**
    - Tests MPAN details display

24. **`test_sheets_api.py`**
    - Tests Google Sheets API with BESS

25. **`verify_bess_dropdowns.py`**
    - Verifies dropdown functionality

26. **`verify_mpan_display.py`**
    - Verifies MPAN display format

27. **`dno_webhook_server_upcloud.py`**
    - Webhook server for DNO lookups
    - Triggers from BESS sheet data

28. **`install_apps_script_auto.py`**
    - Auto-installs Apps Script for BESS

29. **`battery_profit_analysis.py`**
    - Battery profit/arbitrage analysis
    - References UK BESS costs (£200/kWh for 2-hour BESS)

---

## 📜 Apps Script Files (7 files)

### Google Apps Script Integration

1. **`bess_auto_trigger.gs`**
   - Auto-triggers DNO lookup on cell edits

2. **`bess_custom_menu.gs`**
   - Custom menu for BESS sheet
   - "🔋 BESS Tools" menu

3. **`bess_dno_lookup.gs`**
   - Main DNO lookup function
   - Called from menu or trigger

4. **`bess_webapp_api.gs`**
   - Web API for BESS DNO lookups
   - Endpoints:
     * GET /dno-lookup?postcode=XXX
     * GET /info

5. **`generate_hh_button.gs`**
   - HH Profile Generator button handler
   - Uses: Open BESS sheet → Click button

6. **`webapp_api_only.gs`**
   - Standalone web API version

7. **`install_apps_script_auto.py`** (Python deployer)
   - Deploys Apps Script to BESS sheet

---

## 🔑 Key Features

### 1. DNO Lookup
- **Input:** Postcode or MPAN
- **Output:** DNO details (Name, Short Code, GSP Group)
- **Sources:** BigQuery `uk_energy_prod.dno_boundaries_complete`

### 2. DUoS Tariff Calculator
- **Input:** Voltage Level, DNO
- **Output:** Red/Amber/Green rates (p/kWh)
- **Time Bands:** Red (Peak), Amber (Mid), Green (Off-peak)

### 3. MPAN Validation
- **Format:** 13-digit MPAN
- **Checks:** Profile class (00 = HH metered)
- **Meter Registration:** 801 (HH Metered)

### 4. Automation
- **Triggers:** Cell edits in postcode/MPAN fields
- **Actions:** Auto-populate DNO data, tariffs
- **Monitoring:** `bess_auto_monitor.py` (every 30 seconds)

---

## 📁 File Categories

### Setup & Configuration (6 files)
- `create_bess_vlp_sheet.py`
- `install_dno_lookup.py`
- `reset_bess_layout.py`
- `setup_mpan_details_section.py`
- `enhance_bess_sheet_complete.py`
- `install_apps_script_auto.py`

### UI & Dropdowns (4 files)
- `add_bess_dropdowns.py`
- `add_bess_dropdowns_v4.py`
- `add_voltage_dropdown.py`
- `bess_custom_menu.gs`

### Data Processing (8 files)
- `dno_lookup_python.py`
- `parse_actual_mpan.py`
- `link_duos_to_bess_sheet.py`
- `bigquery_to_sheets_updater.py`
- `manual_update_nged.py`
- `bess_dno_lookup.gs`
- `battery_profit_analysis.py`
- `bess_export_reports.py`

### Monitoring & Automation (3 files)
- `bess_auto_monitor.py`
- `bess_auto_monitor_upcloud.py`
- `bess_auto_trigger.gs`

### Testing & Verification (6 files)
- `check_bess_sheet.py`
- `check_bess_structure.py`
- `test_bess_vlp_lookup.py`
- `test_mpan_details.py`
- `verify_bess_dropdowns.py`
- `verify_mpan_display.py`

### Reading & Display (3 files)
- `read_actual_mpan.py`
- `read_current_mpan.py`
- `verify_mpan_display.py`

### Web APIs (3 files)
- `bess_webapp_api.gs`
- `webapp_api_only.gs`
- `dno_webhook_server_upcloud.py`

### Utilities (2 files)
- `generate_hh_button.gs`
- `test_sheets_api.py`

---

## 🔄 Data Flow

```
User Input (Postcode/MPAN)
    ↓
[Cell Edit Trigger]
    ↓
bess_auto_trigger.gs / bess_auto_monitor.py
    ↓
[DNO Lookup]
    ↓
BigQuery: uk_energy_prod.dno_boundaries_complete
    ↓
[Tariff Lookup]
    ↓
BigQuery: DUoS tariff tables
    ↓
[Update BESS Sheet]
    ↓
Rows 4-6: DNO Data
Rows 9-10: Tariff Data
```

---

## 📊 BESS Sheet Current State

### Row 4: Status Bar
```
✅ DNO data updated successfully | Updated: 03:31:26
MPAN 14 | HV
Red: 1.764 p/kWh
Updated: 03:31:25
```

### Row 5-6: DNO Data
```
Headers: Postcode | MPAN ID | DNO Key | DNO Name | Short Code | Market Part. | GSP Group ID | GSP Group
Data:    [blank]  | 14      | NGED-WM | National Grid Electricity Distribution – West Midlands (WMID) | WMID | MIDE | E | West Midlands
```

### Row 9-10: Tariff Data
```
Headers: Voltage Level | Red Rate | Amber Rate | Green Rate | Profile Class | Meter Registration | Voltage Level | DUoS Charging Class
Data:    HV (6.6-33kV) | 1.764    | 0.205      | 0.011      | 00            | 801 (HH Metered)   | HV            | Non-Domestic HH
```

---

## 🎯 Usage Examples

### 1. DNO Lookup by Postcode
```python
python3 dno_lookup_python.py
# Input postcode in BESS sheet
# Auto-populates DNO details
```

### 2. Manual Tariff Update
```python
python3 link_duos_to_bess_sheet.py
# Updates DUoS tariff rates from BigQuery
```

### 3. Reset Sheet
```python
python3 reset_bess_layout.py
# Clears all data, resets to default layout
```

### 4. Monitor Changes
```python
python3 bess_auto_monitor.py
# Runs continuously, watches for cell edits
# Auto-triggers DNO lookups
```

---

## 🔗 Related Sheets

- **BESS_VLP** - Virtual Lead Party lookup (separate sheet)
- **BESS DELETE** - Backup/archive copy
- **DNO_Data** - DNO reference data
- **DUoS_Rates_Lookup** - Tariff rates table

---

## 📝 Notes

- **MPAN Format:** 13 digits, first 2 digits = profile class
- **Voltage Levels:** LV (<1kV), HV (6.6-33kV), EHV (>132kV)
- **Time Bands:** 
  - Red (Peak): 16:00-19:00 weekdays (Nov-Feb)
  - Amber: Various weekday hours
  - Green: Nights, weekends
- **DNO Regions:** 14 regions across GB (NGED, SPEN, UKPN, etc.)

---

## 🚀 Quick Start

1. **View BESS Sheet:**
   ```
   https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit\#gid\=BESS_SHEET_ID
   ```

2. **Check Current Data:**
   ```bash
   cd ~/GB-Power-Market-JJ
   python3 read_actual_mpan.py
   ```

3. **Update DNO Data:**
   ```bash
   python3 dno_lookup_python.py
   ```

4. **Test Functionality:**
   ```bash
   python3 test_bess_vlp_lookup.py
   ```

---

**Total Files:** 32 Python scripts + 7 Apps Script files = **39 files** related to BESS sheet

**All code located in:** `/Users/georgemajor/GB-Power-Market-JJ/`
