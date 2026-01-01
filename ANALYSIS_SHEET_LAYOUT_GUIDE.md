# Analysis Sheet Layout Guide

**Last Updated**: December 31, 2025
**Status**: ✅ Professional layout implemented

## 📊 Overview

The Analysis sheet provides an intelligent interface for querying UK energy market data with:
- **200+ BMU IDs** from BigQuery
- **19 BSC/CUSC party roles** from Categories database
- **18+ lead parties** from Parties database
- **15 generation types** (Solar, Wind, Gas, Nuclear, Battery, etc.)
- **Smart dropdowns** with tooltips
- **Professional visual hierarchy**

## 🎯 Quick Start

### Basic Query Example
```
From Date: 2025-12-01
To Date: 2025-12-15
BMU/Station IDs: All
Party Role: Generator
Generation Type: Battery Storage
Lead Party: All
```

### Advanced Multi-Select Example
```
BMU/Station IDs: E_FARNB-1, T_HUMR-1, V__JZENO001
Party Role: Virtual Lead Party
Generation Type: All
Lead Party: Flexgen Battery Storage
```

## 📋 Field Reference

### Row 4: Date Range
**From Date** | **To Date**
- Format: YYYY-MM-DD
- Default: Last 15 days
- Max range: 365 days
- Tooltip: Hover over cells for examples

### Row 5: 🔍 ENTITY SELECTION (Section Header)
Visual separator for entity filtering section.

### Row 6: BMU/Station IDs
**Label**: `BMU/Station IDs:`
**Input**: `B6`
**Type**: Dropdown + Manual Entry (comma-separated)
**Options**: 200+ BMU IDs from BigQuery

**Examples**:
```
All                                    (no filter, all BMUs)
E_FARNB-1                             (single BMU)
E_FARNB-1, E_HAWKB-1, T_HUMR-1       (multiple BMUs)
```

**BMU ID Patterns**:
- `E_*`: Embedded generation (distribution-connected)
- `T_*`: Transmission-connected generation
- `V__*`: Virtual aggregated units (VLP/batteries)
- `2__*`: Demand/flexible assets
- `M_*`: Market participants

**Tooltip** (hover B6):
> Enter BMU/Station IDs comma-separated.
>
> Examples:
> • E_FARNB-1, E_HAWKB-1
> • T_HUMR-1
> • V__JZENO001
>
> Leave blank or "All" for all units.
>
> 💡 Use dropdown for suggestions.

### Row 7: Party Role
**Label**: `Party Role:`
**Input**: `B7`
**Type**: Dropdown from Categories tab
**Options**: 19 BSC/CUSC roles + "All"

**Available Roles**:
1. **Generator** - Physical electricity generator (power stations)
2. **Supplier** - Licensed electricity supplier (retailers)
3. **Network Operator** - Transmission or distribution network
4. **Interconnector** - Cross-border electricity links
5. **Virtual Lead Party** - Battery/VLP aggregators
6. **Storage Operator** - Energy storage facilities
7. **Distribution System Operator** - DNOs (UKPN, SSEN, NPG)
8. **Transmission System Operator** - NESO
9. **Non-Physical Trader** - Trading without physical assets
10. **Party Agent** - Agent acting on behalf of BSC parties
... and 9 more (see Categories tab)

**Use Cases**:
- **VLP Revenue Analysis**: Select "Virtual Lead Party"
- **Wholesale Trading**: Select "Generator" or "Supplier"
- **Network Analysis**: Select "Distribution System Operator"
- **Cross-border Flow**: Select "Interconnector"

**Tooltip** (hover B7):
> Select BSC party role category.
>
> Examples:
> • Generator - Power stations
> • Virtual Lead Party - Battery/VLP
> • Interconnector - Cross-border links
> • Supplier - Licensed retailers
>
> Filters report to show only units in this category.

### Row 8: Generation Type
**Label**: `Generation Type:`
**Input**: `B8`
**Type**: Dropdown (standard categories)
**Options**: 15 generation types + "All"

**Categories**:
1. All *(default - no filter)*
2. Battery Storage
3. Biomass
4. Coal
5. Gas (CCGT) - Combined Cycle Gas Turbine
6. Gas (OCGT) - Open Cycle Gas Turbine
7. Hydro
8. Interconnector
9. Nuclear
10. Oil
11. Pumped Storage
12. Solar
13. Wind (Offshore)
14. Wind (Onshore)
15. Other

**Example Queries**:
| Goal | Generation Type |
|------|----------------|
| Battery arbitrage analysis | Battery Storage |
| Wind curtailment analysis | Wind (Offshore) |
| Baseload generation trends | Nuclear |
| Peak pricing correlation | Gas (OCGT) |

**Tooltip** (hover B8):
> Select generation technology type.
>
> Examples:
> • Battery Storage
> • Wind (Offshore)
> • Gas (CCGT)
> • Nuclear
> • Solar
>
> Filters report by fuel/technology type.

### Row 9: Lead Party
**Label**: `Lead Party:`
**Input**: `B9`
**Type**: Dropdown from Parties tab
**Options**: 18+ lead parties + "All"

**Available Parties** (see Parties tab for full list):
- **Generators**: Drax Power, EDF Energy, SSE Generation
- **Interconnectors**: BritNed, IFA, IFA2, ElecLink, Nemo Link
- **Suppliers**: Bulb Energy, Octopus Energy, OVO Energy
- **DNOs**: UKPN, SSEN, Northern Powergrid
- **Storage/VLP**: Flexgen Battery Storage, Harmony Energy (Gresham House)
- **TSO**: National Energy System Operator (NESO)

**Use Cases**:
- **Operator Performance**: Filter to specific lead party
- **Multi-Asset Portfolio**: Select party operating multiple BMUs
- **Benchmark Analysis**: Compare party vs market average

**Tooltip** (hover B9):
> Select lead party organization.
>
> Examples:
> • Drax Power Limited
> • Flexgen Battery Storage
> • EDF Energy
> • National Energy System Operator
>
> Filters report to show units operated by this party.

## 🎨 Visual Design

### Section Headers
```
┌─────────────────────────────────────────┐
│ 🔍 ENTITY SELECTION                     │  ← Blue tint (#E8F0FE)
├─────────────────────────────────────────┤     Bold, 9pt
│ BMU/Station IDs: [dropdown]             │
│ Party Role:      [dropdown]             │
│ Generation Type: [dropdown]             │
│ Lead Party:      [dropdown]             │
└─────────────────────────────────────────┘
```

### Label Formatting
- **Column A**: Bold, right-aligned, middle vertical alignment
- **Font**: Standard Google Sheets font
- **Style**: Professional business layout

### Input Cell Formatting
- **Background**: Light gray (#F8F9FA)
- **Border**: 1px solid gray (#CCCCCC)
- **Validation**: Dropdown with manual entry allowed
- **Hover**: Tooltip displays help text

## 📝 Common Query Patterns

### 1. VLP Revenue Analysis (Last 30 Days)
```
From Date: 2025-12-01
To Date: 2025-12-31
BMU/Station IDs: All
Party Role: Virtual Lead Party
Generation Type: Battery Storage
Lead Party: All
Report Category: Analytics & Derived (Balancing with Prices)
Report Type: Trend Analysis (30 days)
```

### 2. Specific Generator Performance
```
From Date: 2025-12-01
To Date: 2025-12-15
BMU/Station IDs: E_FARNB-1, E_HAWKB-1
Party Role: Generator
Generation Type: All
Lead Party: Drax Power Limited
Report Type: Unit Performance Report
```

### 3. Offshore Wind Curtailment
```
From Date: 2025-11-01
To Date: 2025-11-30
BMU/Station IDs: All
Party Role: Generator
Generation Type: Wind (Offshore)
Lead Party: All
Report Category: Curtailment Analysis
```

### 4. Interconnector Flow Analysis
```
From Date: 2025-12-01
To Date: 2025-12-31
BMU/Station IDs: IFA, IFA2, BRITNED, NEMOLINK
Party Role: Interconnector
Generation Type: Interconnector
Lead Party: All
Report Type: Flow Analysis
```

### 5. Multi-Party Comparison
```
From Date: 2025-12-01
To Date: 2025-12-15
BMU/Station IDs: All
Party Role: Generator
Generation Type: Gas (CCGT)
Lead Party: Drax Power Limited
[Then run again with: EDF Energy, SSE Generation]
```

## 🔧 Technical Details

### Cell References (for developers)
```python
# Python script field mapping
FROM_DATE = 'B4'
TO_DATE = 'D4'
BMU_IDS = 'B6'        # Comma-separated
PARTY_ROLE = 'B7'     # Single selection
GEN_TYPE = 'B8'       # Single selection
LEAD_PARTY = 'B9'     # Single selection
REPORT_CATEGORY = 'B11'
REPORT_TYPE = 'B12'
GRAPH_TYPE = 'B13'
```

### Data Validation Rules
All dropdowns use `ONE_OF_RANGE` validation with `strict=False` to allow:
1. **Dropdown selection** - Click to choose from list
2. **Manual entry** - Type custom values
3. **Comma-separated** - Enter multiple values (BMU IDs only)

```javascript
// Apps Script: Read comma-separated BMUs
var bmuIds = sheet.getRange('B6').getValue();
var bmuList = bmuIds.split(',').map(s => s.trim()).filter(s => s && s !== 'All');
```

### DropdownData Sheet Structure
```
Column A: Party Roles (20 options)
Column B: Lead Parties (19 options)
Column C: Generation Types (15 options)
Column D: BMU IDs (200 options)
```

**Note**: BMU IDs limited to 200 for performance. Full list available in BigQuery `bmrs_bod` table.

## 🚀 Workflow Integration

### generate_analysis_report.py
Script reads Analysis sheet fields and generates custom reports:

```python
# Read fields
from_date = analysis.acell('B4').value
bmu_ids = analysis.acell('B6').value.split(',')
party_role = analysis.acell('B7').value
gen_type = analysis.acell('B8').value
lead_party = analysis.acell('B9').value

# Build BigQuery filter
if party_role != 'All':
    filters.append(f"party_role = '{party_role}'")
if gen_type != 'All':
    filters.append(f"fuel_type = '{gen_type}'")
if lead_party != 'All':
    filters.append(f"lead_party = '{lead_party}'")
```

### Apps Script Integration
```javascript
function onEdit(e) {
  var sheet = e.source.getActiveSheet();
  if (sheet.getName() === 'Analysis') {
    // Auto-trigger report generation when fields change
    generateReport();
  }
}
```

## ❓ Troubleshooting

### Issue: Dropdown not showing options
**Solution**: Check DropdownData sheet exists and has data in columns A-D

### Issue: "Invalid validation rule" error
**Solution**: Ensure DropdownData ranges match validation rules (A2:A25, B2:B25, etc.)

### Issue: BMU IDs not recognized
**Solution**: Check BigQuery `bmrs_bod` table for valid BMU IDs. Use dropdown for suggestions.

### Issue: Tooltips not displaying
**Solution**: Hover directly over input cell (B6-B9). Tooltips added as cell notes.

### Issue: Multi-select not working
**Solution**: Enter comma-separated values manually. Dropdown provides single-select only (Google Sheets limitation).

### Issue: generate_analysis_report.py fails
**Solution**: Verify script reads correct cell references (B6-B9). Check for empty/null values.

## 📚 Related Documentation

- **ANALYSIS_SHEET_GUIDE.md** - Database structure (Categories, Parties, Party_Wide)
- **PROJECT_CONFIGURATION.md** - BigQuery configuration
- **STOP_DATA_ARCHITECTURE_REFERENCE.md** - Data schema reference
- **Categories Tab** - Full list of 19 BSC/CUSC roles
- **Parties Tab** - Complete party database (18+ operators)
- **DropdownData Tab** - All dropdown source data

## 🎉 Summary of Improvements

**Before** (Issues):
- ❌ Row 6 & 7 both labeled "Party Roles" (confusing)
- ❌ No dropdowns for Generation Type / Lead Party
- ❌ No tooltips or help text
- ❌ Poor visual hierarchy
- ❌ Manual BMU ID entry only

**After** (Solutions):
- ✅ Clear field separation (BMU IDs vs Party Role vs Lead Party)
- ✅ 4 intelligent dropdowns with 250+ options
- ✅ Tooltips on all input fields
- ✅ Professional section headers and formatting
- ✅ 200+ BMU IDs from BigQuery
- ✅ Integration with Categories & Parties database
- ✅ Comma-separated multi-select support

---

*For support, see: generate_analysis_report.py or improve_analysis_layout.py*
*Spreadsheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit*
