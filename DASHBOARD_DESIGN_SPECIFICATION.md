# GB Energy Dashboard - Current Design Specification

**Last Captured**: 23 November 2025 23:20  
**Source**: Google Sheets Dashboard  
**Purpose**: Complete format preservation specification

---

## 🎨 Global Design Theme

### Color Palette
```
Primary Background:  #111111 (Dark grey/black - Material Black Dark)
Secondary Background: #f3f3f3 (Light grey - for headers)
Text Primary:        #ffffff (White)
Text Secondary:      #000000 (Black)
Alert Background:    #d8eaf6 (Light blue - for status bar)
Alert Accent:        #e43835 (Red - for metrics header)
Alert Text:          #ff0000 (Red - for warnings)
```

### Typography
```
Primary Font:   Arial
Title Size:     18pt, Bold
Section Header: 16-21pt, Bold
Body Text:      10pt
Metric Values:  Standard, Left/Right aligned
```

---

## 📐 Dashboard Layout Structure

### Row 1: File Title
**Range**: A1  
**Content**: "File: Dashboard"  
**Formatting**:
- Background: `#f3f3f3` (Light grey)
- Text: `#000000` (Black)
- Font: Bold, 18pt
- Alignment: CENTER

---

### Row 2: Status Bar
**Range**: A2:B2  
**Content**: "⏰ Last Updated: [TIMESTAMP] | ✅ [STATUS]"  
**Formatting**:
- Background: `#d8eaf6` (Light blue)
- Text: `#000000` (Black)
- Font: Bold, 10pt
- Alignment: LEFT

**Dynamic Values**:
- Last Updated: Timestamp in format `YYYY-MM-DD HH:MM:SS`
- Status: "Auto-refresh ON" or "FRESH" indicator

---

### Row 3: Data Freshness Indicator
**Range**: A3  
**Content**: "Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min"  
**Formatting**:
- Background: `#111111` (Dark)
- Text: `#ffffff` (White)
- Font: Bold, 10pt
- Alignment: LEFT

---

### Row 4: System Metrics Header
**Range**: A4  
**Content**: "📊 SYSTEM METRICS"  
**Formatting**:
- Background: `#e43835` (Red accent)
- Text: `#000000` (Black)
- Font: 16pt
- Alignment: LEFT

---

### Row 5: Summary Metrics
**Range**: A5  
**Content**: "Total Generation: [XX.X] GW | Supply: [XX.X] GW | Renewable: [XX]%"  
**Formatting**:
- Background: `#111111` (Dark)
- Text: `#ffffff` (White)
- Font: 10pt
- Alignment: LEFT

**Dynamic Values**:
- Total Generation in GW (1 decimal)
- Total Supply in GW (1 decimal)
- Renewable percentage (integer)

---

### Row 6: (Empty separator)

---

### Row 7: Section Headers (Fuel & Interconnectors)
**Range**: A7 (Fuel), D7 (Interconnectors)

#### Column A7: "🔥 Fuel Breakdown"
**Formatting**:
- Background: `#111111` (Dark)
- Text: `#ffffff` (White)
- Font: 10pt
- Alignment: LEFT

#### Column D7: "🌍 Interconnectors"
**Formatting**:
- Background: `#111111` (Dark)
- Text: `#ffffff` (White)
- Font: 10pt
- Alignment: LEFT

---

### Rows 8-17: Fuel Breakdown & Interconnectors (Side-by-Side)

**Structure**: Two-column layout
- **Columns A-B**: Fuel Type + Generation
- **Columns D-E**: Interconnector + Flow

#### Fuel Breakdown (A8:B17)

**Format Pattern**:
```
A: [EMOJI] [FUEL_TYPE]
B: [VALUE] GW
```

**All Formatting**:
- Background: `#111111` (Dark)
- Text: `#ffffff` (White)
- Font: 10pt
- Column A Alignment: LEFT
- Column B Alignment: LEFT

**Fuel Types (in order)**:
1. Row 8:  💨 WIND
2. Row 9:  ⚛️ NUCLEAR
3. Row 10: 🌱 BIOMASS
4. Row 11: 🔥 CCGT
5. Row 12: 💧 NPSHYD
6. Row 13: ⚡ OTHER
7. Row 14: 🔥 OCGT
8. Row 15: 🛢️ OIL (not currently used - shows "OIL")
9. Row 16: ⛏️ COAL
10. Row 17: 🔋 PS (Pumped Storage - can be negative)

**Value Format**: `X.X GW` or `-X.X GW` (1 decimal place)

---

#### Interconnectors (D8:E17)

**Format Pattern**:
```
D: [FLAG_EMOJI] [IC_NAME] ([COUNTRY])
E: [VALUE] MW [DIRECTION]
```

**All Formatting**:
- Background: `#111111` (Dark)
- Text: `#ffffff` (White)
- Font: 10pt
- Column D Alignment: LEFT
- Column E Alignment: LEFT

**Interconnectors (in order)**:
1. Row 8:  🇫 ElecLink (France)
2. Row 9:  🇮 East-West (Ireland)
3. Row 10: 🇫 IFA (France)
4. Row 11: 🇮 Greenlink (Ireland)
5. Row 12: 🇫 IFA2 (France)
6. Row 13: 🇮 Moyle (N.Ireland)
7. Row 14: 🇳 BritNed (Netherlands)
8. Row 15: 🇧 Nemo (Belgium)
9. Row 16: 🇳 NSL (Norway)
10. Row 17: 🇩 Viking Link (Denmark)

**Flow Directions**:
- `Import` = Power flowing into GB
- `Export` = Power flowing out of GB
- `Balanced` = Net zero flow

**Value Format**: `XXXX MW [Direction]`

---

### Rows 18-27: (Empty - reserved for charts if needed)

---

### Row 28: Outages Section Header
**Range**: A28  
**Content**: "LIVE OUTAGES "  
**Formatting**:
- Background: `#111111` (Dark)
- Text: `#ff0000` (Red)
- Font: Bold, 21pt
- Alignment: LEFT

---

### Row 29: (Empty separator)

---

### Row 30: Outages Table Header
**Range**: A30:H30

**Column Headers**:
- A30: "Asset Name"
- B30: "BM Unit"
- C30: "Fuel Type"
- D30: "Normal (MW)"
- E30: "Unavail (MW)"
- F30: "Capacity Offline"
- G30: "Cause"
- H30: "Start Time"

**All Formatting**:
- Background: `#111111` (Dark)
- Text: `#ffffff` (White)
- Font: 10pt
- Alignment: LEFT (except D30: RIGHT)

---

### Rows 31+: Outages Data

**Format Pattern** (per row):
```
A: [EMOJI] [ASSET_NAME]
B: [BM_UNIT_ID]
C: [FUEL_TYPE]
D: [NORMAL_CAPACITY_MW]
E: [UNAVAILABLE_MW]
F: [VISUAL_BAR] [PERCENTAGE]%
G: [OUTAGE_CAUSE]
H: [START_TIMESTAMP]
```

**All Formatting**:
- Background: `#111111` (Dark)
- Text: `#ffffff` (White)
- Font: 10pt
- Alignment: LEFT (except D, E, H: RIGHT)

**Emojis by Fuel Type**:
- 🔥 CCGT
- ⚛️ NUCLEAR
- 🌱 BIOMASS
- 💧 NPSHYD
- 🔌 Interconnector
- ⚡ WIND OFFSHORE
- ⛏️ COAL

**Capacity Offline Visual Bar**:
- Uses emoji blocks: `🟥` (red square) and `⬜` (white square)
- 10 blocks total representing 0-100%
- Example: `🟥🟥🟥🟥🟥🟥🟥🟥🟥⬜ 99.3%`
- Red blocks show percentage offline
- White blocks show remaining capacity

**Timestamp Format**: `YYYY-MM-DD HH:MM:SS`

---

## 📊 Charts Configuration

**Current State**: No embedded charts on Dashboard sheet

**Charts Location**: Separate "Charts" sheet

**Important**: All charts must be created on the **"Charts" sheet**, NOT on the Dashboard sheet, to avoid overlaying data.

---

## 🔄 Dynamic Data Requirements

### Must Update Automatically:
1. **Row 2**: Last Updated timestamp
2. **Row 2**: Status indicator (✅/⚠️/🔴)
3. **Row 5**: Generation, Supply, Renewable percentage
4. **Rows 8-17, Column B**: Fuel generation values
5. **Rows 8-17, Column E**: Interconnector flow values and directions
6. **Rows 31+**: Complete outages table (add/remove rows as needed)

### Must NOT Change:
1. Background colors (`#111111` for all data rows)
2. Text color (`#ffffff` white on dark background)
3. Font sizes (10pt body, larger for headers)
4. Column layout (A-B for fuel, D-E for ICs, A-H for outages)
5. Section headers and emojis
6. Alignment (LEFT for text, RIGHT for numbers)
7. Visual capacity bars format (10 blocks)

---

## 🚫 Critical Preservation Rules

### ❌ DO NOT:
1. Change background color from `#111111` (dark theme)
2. Change text color from `#ffffff` (white on dark)
3. Add charts to Dashboard sheet (use Charts sheet instead)
4. Modify column widths without explicit instruction
5. Remove emojis from headers or data rows
6. Change fuel type order (Wind → Nuclear → Biomass → CCGT, etc.)
7. Modify the visual capacity bar format
8. Add or remove columns from existing sections
9. Change font family from Arial
10. Modify header styling (bold, font sizes)

### ✅ DO:
1. Update all dynamic values with latest data
2. Add/remove rows in outages table as needed
3. Maintain exact spacing and layout
4. Preserve all emojis exactly as shown
5. Keep timestamps in exact format
6. Update interconnector flags correctly
7. Maintain visual capacity bars (10 blocks)
8. Keep alignment consistent (LEFT for text, RIGHT for numbers)
9. Update Charts sheet separately (never overlay Dashboard)
10. Preserve all formatting when updating data

---

## 📝 Update Script Requirements

When creating update scripts, they MUST:

1. **Preserve Formatting**:
   ```python
   # Always use update with value_input_option='USER_ENTERED'
   sheet.update(range_name='A8:B17', values=data, value_input_option='USER_ENTERED')
   
   # Never clear and rewrite formatted sections
   # Update values only, not formatting
   ```

2. **Maintain Color Scheme**:
   ```python
   # Background: #111111 (Dark)
   bg_color = {'red': 0.067, 'green': 0.067, 'blue': 0.067}
   
   # Text: #ffffff (White)
   text_color = {'red': 1.0, 'green': 1.0, 'blue': 1.0}
   ```

3. **Keep Emojis Intact**:
   ```python
   fuel_emojis = {
       'WIND': '💨',
       'NUCLEAR': '⚛️',
       'BIOMASS': '🌱',
       'CCGT': '🔥',
       'NPSHYD': '💧',
       'OTHER': '⚡',
       'OCGT': '🔥',
       'OIL': '🛢️',
       'COAL': '⛏️',
       'PS': '🔋'
   }
   ```

4. **Update Outages Table**:
   ```python
   # Calculate visual bar
   def create_capacity_bar(percentage):
       red_blocks = int(percentage / 10)
       white_blocks = 10 - red_blocks
       return f"{'🟥' * red_blocks}{'⬜' * white_blocks} {percentage:.1f}%"
   ```

5. **Charts Handling**:
   ```python
   # ALWAYS create charts on Charts sheet, NEVER on Dashboard
   charts_sheet = spreadsheet.worksheet('Charts')
   
   # If chart doesn't exist, create it on Charts sheet
   # Never use Dashboard sheet for chart positioning
   ```

---

## 🎯 Test Checklist

Before deploying any update, verify:

- [ ] Background colors are `#111111` (dark)
- [ ] Text colors are `#ffffff` (white)
- [ ] All emojis present and correct
- [ ] Fuel breakdown order unchanged
- [ ] Interconnector flags correct
- [ ] Outages visual bars have 10 blocks
- [ ] No charts overlaying Dashboard data
- [ ] Timestamps in correct format
- [ ] Alignment preserved (LEFT/RIGHT)
- [ ] Font sizes unchanged
- [ ] Headers bold and sized correctly
- [ ] No extra columns or rows added to sections
- [ ] Spacing between sections preserved

---

## 📄 Example Data Snapshot

### Fuel Breakdown (A8:B17)
```
💨 WIND       | 13.4 GW
⚛️ NUCLEAR    | 4.1 GW
🌱 BIOMASS    | 3.3 GW
🔥 CCGT       | 2.3 GW
💧 NPSHYD     | 0.4 GW
⚡ OTHER      | 0.3 GW
🔥 OCGT       | 0.0 GW
🛢️ OIL        | 0.0 GW
⛏️ COAL       | 0.0 GW
🔋 PS         | -0.7 GW
```

### Interconnectors (D8:E17)
```
🇫 ElecLink (France)        | 999 MW Import
🇮 East-West (Ireland)      | 0 MW Balanced
🇫 IFA (France)             | 1509 MW Import
🇮 Greenlink (Ireland)      | 513 MW Export
🇫 IFA2 (France)            | 1 MW Export
🇮 Moyle (N.Ireland)        | 201 MW Export
🇳 BritNed (Netherlands)    | 833 MW Export
🇧 Nemo (Belgium)           | 378 MW Export
🇳 NSL (Norway)             | 1397 MW Import
🇩 Viking Link (Denmark)    | 1090 MW Export
```

### Outages Example (Row 31)
```
🔥 Little Barford | LBAR-1 | CCGT | 735 | 730 | 🟥🟥🟥🟥🟥🟥🟥🟥🟥⬜ 99.3% | Turbine / Generator | 2025-11-20 22:29:01
```

---

## 🔒 Version Control

**Design Version**: 1.0  
**Last Updated**: 23 November 2025  
**Approved By**: User  
**Changes from Previous**: Initial specification capture  

**Change Log**:
- 2025-11-23: Initial design specification captured from live dashboard

---

**⚠️ CRITICAL**: This design specification must be followed EXACTLY for all dashboard updates. Any deviation must be explicitly approved by the user.

