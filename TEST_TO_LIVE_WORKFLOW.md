# Test → Live Dashboard Workflow

## Overview
This workflow allows safe, iterative improvements to the Live Dashboard v2 by using a Test sheet as a sandbox environment. You make layout changes in Test, then the agent replicates those changes to Live Dashboard v2 automatically.

## Why This Workflow?

**Problem**: Editing Live Dashboard v2 directly is risky:
- Auto-refresh scripts run every 5-10 minutes
- Accidental changes affect production immediately
- No way to preview layout before applying
- Hard to track what changed

**Solution**: Test → Live replication workflow:
- ✅ Safe experimentation in Test sheet
- ✅ Review changes before applying to Live
- ✅ Automated replication (no manual copying)
- ✅ Layout changes only (data stays fresh)
- ✅ Clear audit trail of what changed

## The Process

### Step 1: Make Changes in Test Sheet
**Location**: [GB Live 2 > Test](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid=1837760869)

**You can modify**:
- Column widths (resize columns)
- Row heights (resize rows)
- Cell merges (merge/unmerge cells)
- Cell positions (move content around)
- Hide/unhide columns or rows
- Conditional formatting
- Data validation rules
- Protected ranges

**Do NOT modify** (won't replicate correctly):
- Cell formulas (sparklines, calculations)
- Cell values (data content)
- Charts/images (requires separate handling)
- Apps Script triggers

**Example Changes**:
```
Before (messy):
| A | B | C | D | E | F | G | H | I | J | K | L | M | ...
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [cramped data everywhere]

After (organized):
| A (wide) | B | C (hidden) | D | E (merged) ->  | F | ...
|----------|---|-------------|---|---------------|---|
| [clean layout with breathing room]
```

### Step 2: Agent Reviews Changes
**Command**:
```bash
python3 replicate_test_to_live.py --analyze
```

**What happens**:
1. Script fetches both Test and Live Dashboard v2 layouts
2. Compares:
   - Column widths (all 26 columns A-Z)
   - Row heights (all 1009 rows)
   - Cell merges (merged ranges)
3. Displays differences:
   ```
   📊 Layout Changes Detected:

   Column Width Changes (5):
   - Column D: 100px → 150px (wider)
   - Column F: 80px → 0px (hidden)
   - Column M: 120px → 180px (wider)

   Row Height Changes (3):
   - Row 5: 21px → 40px (taller header)
   - Row 12: 21px → 0px (hidden)

   Cell Merge Changes (2):
   - Added merge: E5:F5 (header spanning 2 columns)
   - Removed merge: M19:S19 (split cells)

   Total: 10 changes detected
   ```

**Review Process**:
- Agent shows you what will change
- You verify changes are correct
- You approve or request modifications

### Step 3: Agent Applies Changes to Live
**Command**:
```bash
python3 replicate_test_to_live.py --apply
```

**What happens**:
1. Script builds batchUpdate request with all layout changes
2. Applies to Live Dashboard v2 via Google Sheets API
3. Verifies changes applied successfully
4. Reports completion:
   ```
   ✅ Layout Changes Applied to Live Dashboard v2

   - 5 column widths updated
   - 3 row heights updated
   - 2 cell merges updated

   Live Dashboard maintains data updates (auto-refresh still running)
   Layout now matches Test sheet

   🔗 https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid=687718775
   ```

**Important**:
- Data formulas/sparklines NOT touched (remain functional)
- Auto-refresh scripts continue running (5-10 min intervals)
- Only layout properties are copied

## Architecture

### Test Sheet
- **Purpose**: Sandbox for layout experiments
- **Created**: Fresh copy of Live Dashboard v2
- **Updated**: On-demand (when you request refresh)
- **Contains**: Static snapshot of data + formulas
- **Sheet ID**: 1837760869 (current)

### Live Dashboard v2
- **Purpose**: Production dashboard
- **Auto-Refresh**: Every 5-10 minutes via cron
- **Contains**: Live data + sparklines + formulas
- **Sheet ID**: 687718775
- **Users**: You + ChatGPT queries + stakeholders

### Replication Tool
**File**: `replicate_test_to_live.py`

**Features**:
- Compare layouts between Test and Live
- Detect column/row/merge differences
- Generate batchUpdate API calls
- Apply changes safely

**Modes**:
- `--analyze`: Preview changes (read-only)
- `--apply`: Execute changes (write to Live)

**Technical Details**:
```python
# Tracks 3 layout properties:
1. Column widths (pixelSize for columns 0-25)
2. Row heights (pixelSize for rows 0-1008)
3. Cell merges (startRow, endRow, startColumn, endColumn)

# API calls used:
- spreadsheets.get() - Fetch layouts
- spreadsheets.batchUpdate() - Apply changes
  - updateDimensionProperties (resize)
  - mergeCells / unmergeCells (merge changes)
```

## Common Workflows

### Scenario 1: Reorganize Dashboard Sections
**Goal**: Move KPIs section from columns M-S to columns E-K

**Steps**:
1. Open Test sheet
2. Select columns M-S, cut
3. Select column E, insert cut cells
4. Adjust column widths for better spacing
5. Request agent review: `--analyze`
6. Approve and apply: `--apply`
7. ✅ Live Dashboard reorganized

### Scenario 2: Hide Unnecessary Columns
**Goal**: Hide columns with intermediate calculations

**Steps**:
1. Open Test sheet
2. Right-click columns C, F, H → Hide columns
3. Verify dashboard still readable
4. Request agent review: `--analyze`
5. Check hidden columns list (width = 0px)
6. Approve and apply: `--apply`
7. ✅ Live Dashboard cleaner

### Scenario 3: Improve Header Layout
**Goal**: Merge header cells and increase height

**Steps**:
1. Open Test sheet
2. Select A5:D5, right-click → Merge cells
3. Increase row 5 height to 40px
4. Center-align merged header
5. Request agent review: `--analyze`
6. See merge and height changes
7. Approve and apply: `--apply`
8. ✅ Live Dashboard headers improved

### Scenario 4: Undo Changes
**Goal**: Revert Test back to current Live state

**Steps**:
1. Request agent refresh Test sheet
2. Agent deletes current Test
3. Agent duplicates Live Dashboard v2 as new Test
4. ✅ Test matches Live again (clean slate)

## Safety Features

### What CAN'T Go Wrong
- ❌ Can't break formulas (not replicated)
- ❌ Can't lose data (data not touched)
- ❌ Can't stop auto-refresh (scripts separate)
- ❌ Can't affect other sheets (only Test/Live targeted)

### What's Protected
- ✅ Sparklines remain functional
- ✅ Auto-refresh cron continues
- ✅ Data formulas stay intact
- ✅ Apps Script triggers unaffected
- ✅ Other worksheets untouched

### Rollback Process
If changes look wrong in Live:
1. Don't panic (data still updating)
2. Request agent refresh Test from Live (captures current state)
3. Manually fix layout in Test
4. Re-run `--analyze` and `--apply`
5. ✅ Layout corrected

## Technical Limitations

### Not Replicated (Current Version)
- ❌ Cell formulas (sparklines, calculations)
- ❌ Cell values (data content)
- ❌ Charts/graphs
- ❌ Images
- ❌ Conditional formatting (future enhancement)
- ❌ Data validation (future enhancement)
- ❌ Protected ranges (future enhancement)

### Why These Limitations?
**Formulas**: Auto-refresh scripts update data; replicating formulas would overwrite with static Test data

**Charts**: Require separate API endpoints (sheets.spreadsheets.batchUpdate doesn't handle embedded objects)

**Conditional Formatting**: Requires additional analysis of format rules (future enhancement planned)

### Future Enhancements
Planned additions to `replicate_test_to_live.py`:
1. Conditional formatting replication
2. Data validation rules
3. Protected range settings
4. Named ranges
5. Chart positions (if not data-dependent)

## Workflow Best Practices

### Before Starting
- ✅ Verify Test sheet is up-to-date (request refresh if needed)
- ✅ Review current Live layout (know what you're changing)
- ✅ Plan changes (sketch desired layout)

### During Editing
- ✅ Make related changes together (all column widths in one session)
- ✅ Test readability (zoom out, check mobile view)
- ✅ Don't touch formulas/data (layout only)

### After Editing
- ✅ Always run `--analyze` first (preview changes)
- ✅ Review change list carefully
- ✅ Verify row/column numbers correct
- ✅ Approve with `--apply` when satisfied

### Iteration
- ✅ Make changes in small batches (5-10 changes per cycle)
- ✅ Test each batch before next (verify in Live)
- ✅ Keep Test fresh (refresh weekly if heavily editing)

## Example Session

```
You: "The dashboard is a mess, moving items around looks like jibberish"

Agent: "Let me refresh the Test sheet with current Live data"
[Creates fresh Test copy]

You: [Opens Test sheet, makes layout changes:
     - Hides columns C, F, H (intermediate calculations)
     - Widens columns D, M, P (cramped data)
     - Merges header cells in row 5
     - Increases header row height to 40px]

You: "Test looks better now, can you apply these changes to Live?"

Agent: "Analyzing changes..."
[Runs replicate_test_to_live.py --analyze]

Agent: "Found 8 changes:
       - 3 columns hidden
       - 3 columns widened
       - 1 row height increased
       - 1 cell merge added

       Shall I apply these to Live Dashboard v2?"

You: "Yes, apply them"

Agent: [Runs replicate_test_to_live.py --apply]

Agent: "✅ Changes applied. Live Dashboard now matches Test layout.
       Auto-refresh still running, data stays fresh."

You: [Checks Live Dashboard]

You: "Perfect! Much cleaner now."
```

## Troubleshooting

### "Test sheet outdated"
**Symptom**: Test missing recent sparklines/formulas
**Fix**: Request agent refresh Test from Live

### "Changes not showing in Live"
**Symptom**: Applied changes but Live looks same
**Fix**: Hard refresh browser (Ctrl+Shift+R), check correct sheet tab

### "Too many changes detected"
**Symptom**: `--analyze` shows 100+ changes
**Fix**: Test sheet very outdated, request fresh copy from Live

### "Error: Invalid sheet ID"
**Symptom**: Script fails with "No sheet with id: XXXXX"
**Fix**: Agent queries current sheet IDs and updates cache

### "Formulas broken after apply"
**Symptom**: Sparklines stopped working
**Fix**: This shouldn't happen (formulas not touched), but request Test refresh to restore

## File Locations

**Replication Tool**:
```
/home/george/GB-Power-Market-JJ/replicate_test_to_live.py
```

**Sheet IDs Cache**:
```
/home/george/GB-Power-Market-JJ/SHEET_IDS_CACHE.py
```

**Google Sheets**:
```
Spreadsheet: GB Live 2
URL: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

Sheets:
- Live Dashboard v2 (ID: 687718775) - Production
- Test (ID: 1837760869) - Sandbox
```

**Auto-Refresh Scripts**:
```
/home/george/GB-Power-Market-JJ/update_all_dashboard_sections_fast.py (5 min cron)
/home/george/GB-Power-Market-JJ/update_live_metrics.py (10 min cron)
```

## Summary

**You**: Edit layout in Test sheet (safe sandbox)
**Agent**: Reviews changes (`--analyze`)
**You**: Approve changes
**Agent**: Applies to Live (`--apply`)
**Result**: Clean, organized Live Dashboard with fresh data

**Key Benefits**:
- 🎨 Safe layout experimentation
- 🔍 Preview before applying
- 🤖 Automated replication
- 📊 Data stays live and fresh
- ✅ Clear change tracking

---

*Last Updated: December 29, 2025*
*Part of GB Power Market JJ project*
