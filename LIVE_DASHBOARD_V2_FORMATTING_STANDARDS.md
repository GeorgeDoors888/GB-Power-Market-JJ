# Live Dashboard v2 - Formatting Standards
**Last Updated**: December 17, 2025

## ✅ CORRECT Configuration

### Spreadsheet Details
- **Spreadsheet ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
- **Sheet Name**: `Live Dashboard v2`
- **Sheet gid**: `687718775`
- **URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid=687718775

### Layout (Rows 10-23)

**Row 10**: Section header "🔋 Generation Mix"
**Row 11**: Blank spacer
**Row 12**: Column headers (gray background)
- A12: "🛢️ Fuel Type"
- B12: "⚡ GW"
- C12: "📊 Share"
- D12: (Interconnector header)

**Rows 13-22**: Data rows (white background)

| Row | Column A (Fuel) | Column B (GW) | Column D (Interconnector) | Column E (MW) |
|-----|-----------------|---------------|---------------------------|---------------|
| 13  | 🌬️ WIND        | 16.5          | 🇳🇴 Norway                | 1397          |
| 14  | ⚛️ NUCLEAR     | 3.6           | 🇩🇰 Denmark               | 1356          |
| 15  | 🏭 CCGT         | 5.9           | 🇫🇷 France                | 1332          |
| 16  | 🌿 BIOMASS      | 1.0           | 🇫🇷 IFA2                  | 766           |
| 17  | 💧 NPSHYD       | 0.8           | ⚡ ElecLink               | 739           |
| 18  | ❓ OTHER        | 1.4           | 🇬🇱 Greenlink             | 200           |
| 19  | 🛢️ OCGT        | 0.0           | 🇮🇪 Ireland               | 164           |
| 20  | ⛏️ COAL        | 0.0           | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 E-W                 | 0             |
| 21  | 🛢️ OIL         | 0.0           | 🇧🇪 Belgium               | 302           |
| 22  | 💧 PS           | 1.2           | 🇳🇱 Netherlands           | 398           |

### Color Scheme (User-Defined, MUST PRESERVE)

**Header Row (12)**:
- Background: `RGB(0.93, 0.94, 0.95)` (light gray)
- Text: `RGB(0.20, 0.20, 0.20)` (dark gray)

**Data Rows (13-22)**:
- Background: `RGB(1.00, 1.00, 1.00)` (white)
- Text: `RGB(0.20, 0.20, 0.20)` (dark gray)

### Automated Updates

**Active Script**: `update_gb_live_complete.py`
- Runs every 5 minutes via `bg_live_cron.sh`
- Updates columns A-B (fuel), D-E (interconnectors)
- Uses `value_input_option='USER_ENTERED'` to preserve formatting

**Disabled Scripts** (prevent conflicts):
- ❌ `auto_update_dashboard_v2.sh` - DISABLED in cron
- ❌ `update_bg_live_dashboard.py` - Manual use only
- ❌ `update_live_dashboard_v2.py` - Legacy

## 🚫 Common Mistakes to Avoid

1. **Wrong Sheet Name**: Using `'GB Live'` instead of `'Live Dashboard v2'`
2. **Wrong Spreadsheet ID**: Using `1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I` (old)
3. **Overwriting Formatting**: Not using `USER_ENTERED` value input option
4. **Multiple Scripts**: Running conflicting update scripts simultaneously
5. **Wrong gid**: Confusing gid (687718775) with spreadsheet ID

## 📝 Script Update Checklist

When writing to Live Dashboard v2:

```python
# ✅ Correct configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
sheet = spreadsheet.worksheet('Live Dashboard v2')

# ✅ Preserve formatting when updating
sheet.batch_update(updates, value_input_option='USER_ENTERED')
```

```javascript
// ✅ Apps Script configuration
const ss = SpreadsheetApp.openById('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA');
const sheet = ss.getSheetByName('Live Dashboard v2');
```

## 🔧 Troubleshooting

**"I don't see updates"**:
1. Hard refresh browser: Ctrl+Shift+R
2. Check timestamp in row 2
3. Verify correct sheet: "Live Dashboard v2" not "GB Live"
4. Check cron is running: `crontab -l`

**"Formatting is lost"**:
- Scripts must use `value_input_option='USER_ENTERED'`
- Never use RAW mode for formatted cells
- Batch updates preserve formatting better than individual cell updates

**"Data in wrong rows"**:
- Fuel types: rows 13-22, columns A-B
- Interconnectors: rows 13-22, columns D-E
- Don't mix up row offsets (common with old scripts)

---

*This document reflects the CURRENT working configuration as of Dec 17, 2025*
