# Dashboard Formatting Standards

## Capacity Formatting

### GW (Gigawatts)
- **Format**: `X.XX GW`
- **When to use**: Values ≥ 100 MW (0.1 GW)
- **Examples**:
  - 12,813 MW = **12.81 GW**
  - 666 MW = **0.67 GW**
  - 585 MW = **0.58 GW**

### MW (Megawatts)
- **Format**: `X,XXX MW`
- **When to use**: All capacity values
- **Examples**:
  - **12,813 MW**
  - **666 MW**
  - **50 MW**

### Combined GW/MW
- **Format**: `X,XXX MW (X.XX GW)`
- **When to use**: Large capacity values in main display
- **Examples**:
  - **12,813 MW (12.81 GW)**
  - **666 MW (0.67 GW)**
  - **50 MW** (don't show GW for small values < 100 MW)

## Percentage Formatting

### Standard Format
- **Format**: `XX.X%`
- **Precision**: 1 decimal place
- **Examples**:
  - **94.2%**
  - **100.0%**
  - **15.5%**

### Visual Progress Bars
- **Format**: `🟥🟥🟥⬜⬜⬜⬜⬜⬜⬜`
- **Scale**: 10 blocks total
- **Red blocks**: Filled proportion (🟥)
- **White blocks**: Unfilled proportion (⬜)
- **Examples**:
  - 100% = `🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥`
  - 50% = `🟥🟥🟥🟥🟥⬜⬜⬜⬜⬜`
  - 25% = `🟥🟥🟥⬜⬜⬜⬜⬜⬜⬜`

## Currency Formatting (£)

### Standard Format
- **Format**: `£X,XXX` or `£X,XXX.XX`
- **Examples**:
  - **£1,500**
  - **£250,000**
  - **£1,500.50** (with pence)

### Large Values
- **Format**: `£X.XX million` or `£X.XX billion`
- **When to use**: Values > £1 million
- **Examples**:
  - **£1.5 million**
  - **£250 million**
  - **£1.2 billion**

## Emojis for Fuel Types

| Fuel Type | Emoji | Usage |
|-----------|-------|-------|
| Nuclear | ⚛️ | Nuclear power stations |
| CCGT/Gas | 🔥 | Gas-fired combined cycle |
| OCGT | 🔥 | Open cycle gas turbine |
| Wind Offshore | 💨 | Offshore wind farms |
| Wind Onshore | 💨 | Onshore wind farms |
| Hydro Pumped Storage | 💧 | Pumped storage hydro |
| Hydro Run-of-River | 💧 | Run-of-river hydro |
| Biomass | 🌱 | Biomass power stations |
| Coal | ⛏️ | Coal-fired stations |
| Battery Storage | 🔋 | Battery energy storage |
| Interconnector | 🔌 | Cross-border links |
| Solar | ☀️ | Solar PV farms |
| Other | ⚡ | Generic electricity |

## Status Indicators

### Severity Levels (Individual Items)
- **🔴 Critical**: > 500 MW or critical issue
- **⚠️ Warning**: > 200 MW or warning level
- **🟡 Moderate**: > 100 MW or moderate concern
- **🟢 Low**: < 100 MW or normal operation
- **✅ All Clear**: No issues

### Overall System Status
- **🔴 Critical**: Total > 5,000 MW
- **⚠️ High**: Total > 3,000 MW
- **🟡 Moderate**: Total > 1,000 MW
- **🟢 Low**: Total < 1,000 MW

## Date and Time Formatting

### Standard Format
- **Format**: `DD/MM/YYYY HH:MM`
- **Timezone**: UK time (GMT/BST)
- **Examples**:
  - **26/11/2025 11:54**
  - **01/01/2025 00:00**
  - **15/08/2025 14:30**

### Alternative Format (ISO)
- **Format**: `YYYY-MM-DD HH:MM:SS`
- **When to use**: Technical logs, exports
- **Examples**:
  - **2025-11-26 11:54:01**
  - **2025-01-01 00:00:00**

## Color Scheme

### Background Colors
- **Red Header**: `#e43835` (RGB: 0.89, 0.22, 0.21)
  - Used for: Main section headers, totals row
  - Text color: White (#ffffff)
  - Font: Bold, 12pt

- **Dark Theme**: `#111111` (RGB: 0.07, 0.07, 0.07)
  - Used for: Map sections, dark mode headers
  - Text color: White (#ffffff)
  - Font: Bold, 11pt

- **Light Gray**: `#f3f3f3` (RGB: 0.95, 0.95, 0.95)
  - Used for: Alternate rows, subtle backgrounds
  - Text color: Black (#000000)

### Text Colors
- **White**: `#ffffff` - On dark/red backgrounds
- **Black**: `#000000` - On light backgrounds
- **Dark Gray**: `#666666` - Secondary text
- **Red**: `#e43835` - Critical values, warnings

## Row 44 - Total Outages Format

### Standard Format
```
📊 TOTAL OUTAGES: X,XXX MW (X.XX GW) | Count: XX | Status: 🔴 Critical | +XX more
```

### Components
1. **Icon**: 📊 (chart/analytics)
2. **Total MW**: Comma-separated
3. **Total GW**: 2 decimal places in parentheses
4. **Count**: Number of active outages
5. **Status**: Emoji + text based on severity
6. **Additional**: If more than 12 outages exist

### Examples
- `📊 TOTAL OUTAGES: 12,813 MW (12.81 GW) | Count: 50 | Status: 🔴 Critical | +38 more`
- `📊 TOTAL OUTAGES: 2,450 MW (2.45 GW) | Count: 15 | Status: 🟡 Moderate`
- `📊 TOTAL OUTAGES: 0 MW (0 GW) | Count: 0 | Status: ✅ All Clear`

## Number Formatting Rules

### Thousand Separators
- **Always use commas**: `1,000` not `1000`
- **Examples**:
  - 1,500 MW
  - 12,813 MW
  - 250,000 MW

### Decimal Places
- **GW**: 2 decimal places (`12.81 GW`)
- **MW**: No decimals (`12813 MW`) unless < 1 MW
- **Percentages**: 1 decimal place (`94.5%`)
- **Currency**: 2 decimal places for pence (`£1,500.50`)

### Scientific Notation
- **Avoid for user-facing displays**
- **Use for**: Technical exports, data files
- **Example**: 1.28e4 → **12,800 MW**

## Text Formatting

### Headers
- **Font**: Bold, 12pt
- **Case**: Title Case or UPPER CASE
- **Alignment**: Left or Center
- **Example**: `📊 LIVE ANALYTICS & VISUALIZATION`

### Body Text
- **Font**: Regular, 10-11pt
- **Case**: Sentence case
- **Alignment**: Left (text), Right (numbers)

### Unit Names
- **Max length**: 40 characters
- **Truncate with**: `...` if needed
- **Include emoji**: For quick identification
- **Example**: `🔴 Heysham 2 Generator 7`

## Code Implementation

### Python Format Strings
```python
# GW/MW formatting
mw = 12813
gw = mw / 1000
capacity = f"{mw:,} MW ({gw:.2f} GW)"  # "12,813 MW (12.81 GW)"

# Percentage
pct = 94.2
pct_display = f"{pct:.1f}%"  # "94.2%"

# Currency
price = 1500.50
currency = f"£{price:,.2f}"  # "£1,500.50"

# Date/time
from datetime import datetime
now = datetime.now()
date_str = now.strftime('%d/%m/%Y %H:%M')  # "26/11/2025 11:54"
```

### Google Sheets API
```python
# Update with formatting
dashboard.update(range_name='A44', values=[[total_text]], value_input_option='USER_ENTERED')

# Apply formatting
dashboard.format('A44:I44', {
    'backgroundColor': {'red': 0.89, 'green': 0.22, 'blue': 0.21},
    'textFormat': {
        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
        'fontSize': 12,
        'bold': True
    },
    'horizontalAlignment': 'LEFT'
})
```

## Consistency Checklist

When updating the dashboard, ensure:

- [ ] All capacities show both MW and GW (if ≥ 100 MW)
- [ ] Percentages have 1 decimal place
- [ ] Currency values use £ symbol and commas
- [ ] Dates use DD/MM/YYYY HH:MM format
- [ ] Fuel types have appropriate emojis
- [ ] Status indicators match severity levels
- [ ] Row 44 totals are accurate and formatted
- [ ] Visual progress bars are correct (10 blocks)
- [ ] Color scheme matches standards
- [ ] Text is readable against backgrounds

---
**Reference**: This formatting is used across all GB Power Market JJ dashboards
**Updated**: 26 November 2025
