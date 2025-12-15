# Google Sheets Date Range Controls - Installation Guide

## Overview

This guide explains how to add interactive date range controls (D55 and E66) to your Google Sheets dashboard for filtering OFR pricing and constraint analysis data.

## Quick Installation

### Step 1: Open Apps Script Editor

1. Open your dashboard: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/edit
2. Click **Extensions** → **Apps Script**
3. Delete any placeholder code in the editor

### Step 2: Add the Code

1. Copy the entire contents of `add_date_range_controls.gs`
2. Paste into the Apps Script editor
3. Click **Save** (💾 icon) or press `Ctrl+S`
4. Name the project: "Date Range Controls"

### Step 3: Run Setup

1. In the Apps Script editor, select function: `setupDateRangeControls`
2. Click **Run** (▶️ icon)
3. **First time only**: Authorize permissions
   - Click "Review permissions"
   - Select your Google account
   - Click "Advanced" → "Go to Date Range Controls (unsafe)"
   - Click "Allow"
4. Wait for "Execution completed" message

### Step 4: Return to Sheets

Your dashboard now has:
- **D55**: "From" date picker (default: 30 days ago)
- **E66**: "To" date picker (default: today)
- **Labels**: "📅 From Date:" (C55) and "📅 To Date:" (D66)
- **New Menu**: "📊 Analysis Controls" in menu bar

## Usage

### Selecting Dates

1. **Click on cell D55** (From date)
   - Click the dropdown arrow that appears
   - Select start date from calendar
   - Or type date in format: YYYY-MM-DD

2. **Click on cell E66** (To date)
   - Click the dropdown arrow
   - Select end date from calendar
   - Or type date in format: YYYY-MM-DD

3. **Automatic Validation**
   - System checks that To date > From date
   - Shows warning if range > 365 days
   - Displays selected range and day count

### Using the Analysis Controls Menu

**📊 Analysis Controls** menu provides:

1. **🔧 Setup Date Range Controls**
   - Re-run setup if cells get deleted
   - Resets to default dates (last 30 days)

2. **🔄 Refresh with Current Dates**
   - Updates analysis data using selected date range
   - Shows progress toast notification

3. **📅 Show Selected Range**
   - Displays current from/to dates
   - Shows number of days in range

4. **📥 Export Date-Filtered Data**
   - Generates filename with date range
   - Instructions for CSV export

### Quick Preset Buttons (Optional)

Run `createDatePresetButtons()` to add one-click presets:
- **Last 7 Days** - Sets D55 to 7 days ago, E66 to today
- **Last 30 Days** - Sets D55 to 30 days ago, E66 to today
- **Last 90 Days** - Sets D55 to 90 days ago, E66 to today
- **YTD** - Sets D55 to Jan 1, E66 to today

## Integration with Existing Dashboard

### Option 1: Manual Refresh (Simplest)

User workflow:
1. Change dates in D55 and E66
2. Click menu: **📊 Analysis Controls → 🔄 Refresh with Current Dates**
3. Data updates automatically

### Option 2: Automatic Refresh on Date Change

Add this trigger:

1. **Apps Script Editor** → **Triggers** (⏰ icon on left)
2. Click **+ Add Trigger**
3. Settings:
   - Function: `onDateRangeChange`
   - Event source: **From spreadsheet**
   - Event type: **On edit**
4. Click **Save**

Now data refreshes automatically when dates change!

### Option 3: Integrate with BigQuery Refresh

Modify your existing BigQuery refresh functions to use date range:

```javascript
function refreshOFRData() {
  // Get date range from controls
  const range = getSelectedDateRange();
  
  // Your existing BigQuery query with date filters
  const sql = `
    SELECT *
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad\`
    WHERE assetId LIKE 'OFR-%'
      AND CAST(settlementDate AS DATE) BETWEEN '${range.fromDateStr}' AND '${range.toDateStr}'
  `;
  
  // Execute query and update sheet
  // ... your existing code ...
}
```

Call this function from `refreshWithCurrentDates()`:

```javascript
function refreshWithCurrentDates() {
  if (!validateDateRange()) return;
  
  refreshOFRData();
  refreshConstraintData();
  // ... other refresh functions ...
}
```

## Cell Layout

```
Row 55:
  C55: "📅 From Date:" (label)
  D55: [Date Picker] (input)
  E55: (empty)
  F55: [Last 7 Days] (optional button)
  G55: [Last 30 Days] (optional button)
  H55: [Last 90 Days] (optional button)

Row 66:
  C66: (empty)
  D66: "📅 To Date:" (label)
  E66: [Date Picker] (input)
  F66: [YTD] (optional button)
```

## Formatting Applied

### Date Input Cells (D55, E66)
- White background
- Blue border (medium weight)
- Center-aligned
- Date format: `yyyy-mm-dd`
- Data validation: Date picker dropdown

### Labels (C55, D66)
- Light blue background (#e8f4f8)
- Bold text
- Right-aligned
- Emoji prefix for visual clarity

## Functions Reference

### User-Facing Functions

| Function | Purpose | Menu Item |
|----------|---------|-----------|
| `setupDateRangeControls()` | Initial setup | 🔧 Setup Date Range Controls |
| `refreshWithCurrentDates()` | Refresh data | 🔄 Refresh with Current Dates |
| `showSelectedDateRange()` | Display range | 📅 Show Selected Range |
| `exportDateFilteredData()` | Export helper | 📥 Export Date-Filtered Data |

### Helper Functions

| Function | Purpose |
|----------|---------|
| `getSelectedDateRange()` | Returns {fromDate, toDate, days} |
| `validateDateRange()` | Checks if To > From |
| `onDateRangeChange(e)` | Auto-refresh on edit |
| `setLastNDays(n)` | Set range to last N days |
| `setYearToDate()` | Set range to YTD |

## Troubleshooting

### "Cannot read property 'getValue' of null"
- Run `setupDateRangeControls()` again
- Ensure you're on correct sheet
- Check cells D55 and E66 exist

### Dates not validating
- Ensure date format is `yyyy-mm-dd`
- Check that data validation is applied (dropdown arrow visible)
- Re-run setup if validation missing

### Changes not refreshing data
- Check if trigger is installed (Apps Script → Triggers)
- Manually run `refreshWithCurrentDates()` from menu
- Verify BigQuery integration functions exist

### Authorization issues
- Apps Script → Run → Review permissions
- Click "Advanced" → "Go to [project name]"
- Grant required permissions:
  - See, edit, create, delete spreadsheets
  - Connect to external services (BigQuery)

## Advanced Customization

### Change Default Date Range

Edit `setupFromDateControl()`:

```javascript
// Change from 30 days to 90 days
const defaultFromDate = new Date();
defaultFromDate.setDate(defaultFromDate.getDate() - 90); // Change -30 to -90
```

### Move Control Cells

Change cell references throughout:

```javascript
// Example: Move from D55/E66 to F10/G10
sheet.getRange('F10') // instead of 'D55'
sheet.getRange('G10') // instead of 'E66'
```

### Custom Date Format

Change number format in setup functions:

```javascript
cell.setNumberFormat('dd/mm/yyyy'); // UK format
cell.setNumberFormat('mm/dd/yyyy'); // US format
cell.setNumberFormat('yyyy-mm-dd'); // ISO format (default)
```

## Example: Complete Integration

```javascript
/**
 * Complete example: Refresh OFR pricing data with date range
 */
function refreshOFRPricingWithDates() {
  const range = getSelectedDateRange();
  
  if (!validateDateRange()) {
    return;
  }
  
  // Show loading
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `📊 Loading OFR data for ${range.days} days...`,
    'Updating',
    -1
  );
  
  // Query BigQuery
  const sql = `
    WITH ofr_data AS (
      SELECT 
        CAST(settlementDate AS DATE) as date,
        assetId,
        ROUND(SUM(cost), 2) as total_cost,
        ROUND(SUM(volume), 2) as total_volume,
        ROUND(SUM(cost) / NULLIF(SUM(volume), 0), 2) as avg_price
      FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad\`
      WHERE assetId LIKE 'OFR-%'
        AND CAST(settlementDate AS DATE) BETWEEN '${range.fromDateStr}' AND '${range.toDateStr}'
        AND cost IS NOT NULL
        AND volume > 0
      GROUP BY date, assetId
      ORDER BY date DESC
    )
    SELECT * FROM ofr_data
  `;
  
  // Execute and write to sheet
  try {
    const result = BigQuery.Jobs.query({
      query: sql,
      useLegacySql: false
    }, 'inner-cinema-476211-u9');
    
    // Write results to sheet (rows 70+)
    const sheet = SpreadsheetApp.getActiveSheet();
    const outputRange = sheet.getRange(70, 1, result.rows.length, result.schema.fields.length);
    
    // Convert rows to 2D array and write
    const data = result.rows.map(row => row.f.map(cell => cell.v));
    outputRange.setValues(data);
    
    // Success
    SpreadsheetApp.getActiveSpreadsheet().toast(
      `✅ Loaded ${result.rows.length} rows`,
      'Complete',
      3
    );
    
  } catch (error) {
    SpreadsheetApp.getUi().alert('❌ Error: ' + error.message);
  }
}
```

## Support

For issues or questions:
- Check Apps Script **Execution log** (View → Logs)
- Review **Triggers** setup (Apps Script → Triggers)
- Test functions individually before integration
- Email: george@upowerenergy.uk

---

**Last Updated**: December 9, 2025  
**Compatible With**: Google Sheets, Apps Script V8 Runtime
