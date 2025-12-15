# GB Live Dashboard - Sparkline Implementation

**Last Updated:** December 8, 2025  
**Status:** ✅ Production

## Overview

The GB Live Dashboard displays real-time UK power generation data with inline metrics, trend sparklines, and interconnector flows in a compact 5-column layout.

## Dashboard Layout (Rows 10-19)

```
┌─────────┬──────────────────────────────────┬─────────────┬───────────────┬──────────────┐
│ Column A│ Column B                         │ Column C    │ Column D      │ Column E     │
├─────────┼──────────────────────────────────┼─────────────┼───────────────┼──────────────┤
│ Fuel    │ Inline Metrics                   │ Sparkline   │ Interconnector│ Flow (MW)    │
│ Emoji   │ GW | % | Trend | Status          │ Line Chart  │ Name + Flag   │ Import/Export│
└─────────┴──────────────────────────────────┴─────────────┴───────────────┴──────────────┘

Row 10: 💨 Wind      | 15.03 GW | 49.0% ↓ | 🟢 Active | [Teal Line]   | 🇫🇷 INTFR   | 1507 MW
Row 11: 🔥 CCGT      | 7.94 GW  | 25.9% ↓ | 🟢 Active | [Red Line]    | 🇩🇰 INTVKL  | 1426 MW
Row 12: ⚛️ Nuclear   | 3.57 GW  | 11.6% ↓ | 🟡 Active | [Orange Line] | 🇳🇴 INTNSL  | 1397 MW
Row 13: 🌱 Biomass   | 2.85 GW  | 9.3% ↓  | 🟡 Active | [Green Line]  | ⚡ INTELEC  | 997 MW
Row 14: 💧 Hydro     | 0.69 GW  | 2.3% ↓  | 🔴 Active | [Yellow Line] | 🇫🇷 INTIFA2 | 992 MW
Row 15: ❓ Other     | 0.41 GW  | 1.3% ↓  | 🔴 Active | [Blue Line]   | 🇧🇪 INTNEM  | 411 MW
Row 16: ⚡ Pumped    | 0.17 GW  | 0.6% ↓  | 🔴 Active | [Purple Line] | 🇮🇪 INTIRL  | -60 MW
Row 17: 🔥 OCGT      | 0.00 GW  | 0.0% ↓  | 🔴 Offline| [Coral Line]  | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 INTEW   | -76 MW
Row 18: ⚫ Coal      | 0.00 GW  | 0.0% →  | 🔴 Offline| [Dark Line]   | 🇬🇱 INTGRNL | -199 MW
Row 19: 🛢️ Oil       | 0.00 GW  | 0.0% →  | 🔴 Offline| [Sky Line]    | 🇳🇱 INTNED  | -559 MW
```

## Data Architecture

### Data Sources

**BigQuery Table:** `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
- Real-time IRIS data feed
- Current day only (last 24-48 hours)
- Updates every 30 minutes (settlement periods)

**Data_Hidden Sheet:** Stores 48-period timeseries data
- Rows 10-19: One row per fuel type
- Columns A-AV: 48 settlement periods (00:00-23:30)
- Only first 29-30 periods have data (current time ~14:30)
- Future periods = 0 (not yet occurred)

### Example Data Pattern

```
Data_Hidden Row 10 (Wind):
Period 1-6   (00:00-03:00): 13.52, 13.98, 14.42, 14.89, 15.21, 15.67 GW
Period 7-12  (03:30-06:00): 15.89, 16.12, 16.43, 16.21, 15.98, 15.54 GW
Period 13-18 (06:30-09:00): 15.12, 14.67, 14.23, 13.78, 13.45, 13.21 GW
Period 19-24 (09:30-12:00): 13.56, 13.89, 14.12, 14.45, 14.78, 15.03 GW
Period 25-29 (12:30-14:30): 15.23, 15.45, 15.67, 15.43, 15.03 GW (current)
Period 30-48 (15:00-23:30): 0, 0, 0, 0... (future periods)
```

## Sparkline Configuration

### Technical Specification

```javascript
=SPARKLINE(Data_Hidden!A{row}:AC{row}, {
    "charttype", "line";
    "linewidth", 2;
    "color", "{fuel_color}";
    "max", {fuel_max};
    "ymin", 0
})
```

### Color Coding & Scaling

| Fuel Type | Color Code | Hex      | Y-Max | Typical Range |
|-----------|------------|----------|-------|---------------|
| Wind      | Teal       | #4ECDC4  | 20 GW | 0-16 GW       |
| CCGT      | Red        | #FF6B6B  | 10 GW | 2-8 GW        |
| Nuclear   | Orange     | #FFA07A  | 5 GW  | 3.5-4 GW      |
| Biomass   | Green      | #52B788  | 5 GW  | 2-3 GW        |
| Hydro     | Yellow     | #F7DC6F  | 2 GW  | 0.5-1 GW      |
| Other     | Blue       | #45B7D1  | 2 GW  | 0.3-0.5 GW    |
| Pumped    | Purple     | #BB8FCE  | 1 GW  | 0-0.2 GW      |
| OCGT      | Coral      | #E76F51  | 1 GW  | 0 GW          |
| Coal      | Dark Blue  | #264653  | 1 GW  | 0 GW          |
| Oil       | Sky Blue   | #85C1E9  | 1 GW  | 0 GW          |

### Design Rationale

**Why LINE charts instead of BAR:**
- Clearer trend visualization over 29 periods
- Better visibility at small column widths
- Smooth curves show generation patterns
- Bar charts were too compressed (29 bars in small space)

**Why limit to AC column (29 periods) instead of AV (48):**
- Only first 29-30 periods have actual data
- Remaining 18-19 periods are zeros (future)
- Including zeros created flat line at end, distorting visualization
- Range A:AC captures all meaningful data

**Why custom Y-axis scaling:**
- Wind varies 0-16 GW (needs 0-20 scale)
- Nuclear steady at 3.57 GW (needs 0-5 scale)
- OCGT/Coal/Oil at 0 GW (needs 0-1 scale)
- Uniform scaling would compress small values into noise

## Interconnector Integration

### Interconnector List

| Code     | Country      | Flag | Typical Flow | Direction |
|----------|--------------|------|--------------|-----------|
| INTFR    | France       | 🇫🇷   | +1500 MW     | Import    |
| INTVKL   | Denmark      | 🇩🇰   | +1400 MW     | Import    |
| INTNSL   | Norway       | 🇳🇴   | +1400 MW     | Import    |
| INTELEC  | ElecLink     | ⚡   | +1000 MW     | Import    |
| INTIFA2  | France IFA2  | 🇫🇷   | +1000 MW     | Import    |
| INTNEM   | Belgium      | 🇧🇪   | +400 MW      | Import    |
| INTIRL   | Ireland      | 🇮🇪   | -60 MW       | Export    |
| INTEW    | Wales        | 🏴󠁧󠁢󠁥󠁮󠁧󠁿   | -76 MW       | Export    |
| INTGRNL  | Greenland    | 🇬🇱   | -199 MW      | Export    |
| INTNED   | Netherlands  | 🇳🇱   | -559 MW      | Export    |

**Flow Convention:**
- Positive values = Importing electricity into GB
- Negative values = Exporting electricity from GB
- Typically GB is net importer (~5-6 GW total)

### Layout Decision

**Original Design:** Interconnectors in rows 51-60, columns A-B (separate section)
**New Design:** Interconnectors in rows 10-19, columns D-E (alongside fuel data)

**Rationale:**
- Compact layout reduces scrolling
- Related data (generation + imports) visible together
- User requested: "can you please include interconnectors from d:10"
- Maintains visual hierarchy: fuels (A-C) → interconnectors (D-E)

## Implementation Code

### Main Script: `update_bg_live_dashboard.py`

**Lines 608-656: Fuel Type Updates with Sparklines**

```python
# Define colors and scales for sparklines
sparkline_colors = ['#4ECDC4', '#FF6B6B', '#FFA07A', '#52B788', '#F7DC6F', 
                    '#45B7D1', '#BB8FCE', '#E76F51', '#264653', '#85C1E9']
sparkline_max_vals = [20, 10, 5, 5, 2, 2, 1, 1, 1, 1]

for idx, (_, row) in enumerate(gen_mix.iterrows()):  # CRITICAL: enumerate for correct indexing
    if row_num > 21:
        break
    
    fuel = row['fuelType']
    fuel_display = fuel_emojis.get(fuel, fuel)
    gen_gw = row['generation_gw']
    percentage = row['percentage']
    percentage_display = percentage * 100
    
    # Calculate trend indicator and traffic light
    trend_indicator = '↑' if gen_gw > (total_gen * percentage * 1.05) else '↓' if gen_gw < (total_gen * percentage * 0.95) else '→'
    traffic_light = '🟢' if percentage > 0.15 else '🟡' if percentage > 0.05 else '🔴'
    status = 'Active' if gen_gw > 0.01 else 'Offline'
    
    # Column B: Inline format
    inline_text = f'{gen_gw:.2f} GW | {percentage_display:.1f}% {trend_indicator} | {traffic_light} {status}'
    
    # Column C: LINE sparkline with color and scaling
    color = sparkline_colors[idx % len(sparkline_colors)]
    max_val = sparkline_max_vals[idx % len(sparkline_max_vals)]
    sparkline_formula = f'=SPARKLINE(Data_Hidden!A{row_num}:AC{row_num},{{"charttype","line";"linewidth",2;"color","{color}";"max",{max_val};"ymin",0}})'
    
    fuel_updates.append({
        'range': f'A{row_num}:C{row_num}',
        'values': [[fuel_display, inline_text, sparkline_formula]]
    })
    row_num += 1

if fuel_updates:
    sheet.batch_update(fuel_updates, value_input_option='USER_ENTERED')
```

**Lines 660-682: Interconnector Updates**

```python
# Update interconnectors starting at row 10 in columns D-E (alongside fuel types)
if interconnectors is not None and not interconnectors.empty:
    ic_updates = []
    ic_row = 10  # Start at row 10, columns D-E
    for idx, row in interconnectors.iterrows():
        if ic_row > 21:  # Stay within fuel type rows
            break
            
        ic_name = row['fuelType']
        ic_display = interconnector_emojis.get(ic_name, ic_name)
        flow_mw = int(row['avg_flow_mw'])
        
        ic_updates.append({
            'range': f'D{ic_row}:E{ic_row}',
            'values': [[ic_display, f'{flow_mw} MW']]
        })
        
        logging.info(f"  ✅ Interconnector row {ic_row}: {ic_display} - {flow_mw} MW")
        ic_row += 1
    
    if ic_updates:
        sheet.batch_update(ic_updates)
```

### Key Code Elements

**Enumerate Pattern (CRITICAL):**
```python
# ❌ WRONG: Uses DataFrame index (unpredictable)
for idx, row in gen_mix.iterrows():
    sparkline_formula = f'=SPARKLINE(Data_Hidden!A{row_num}:AC{row_num},...)'

# ✅ CORRECT: Uses sequential counter
for idx, (_, row) in enumerate(gen_mix.iterrows()):
    sparkline_formula = f'=SPARKLINE(Data_Hidden!A{row_num}:AC{row_num},...)'
```

**Why This Matters:**
- DataFrame index from iterrows() could be 0, 1, 2, or any number
- Using df index directly caused sparklines to reference wrong rows in Data_Hidden
- Only row 10 worked (idx=0 happened to align with row_num=10)
- Rows 11-19 failed because idx didn't increment sequentially
- `enumerate()` guarantees idx starts at 0 and increments: 0, 1, 2, 3...

## Troubleshooting Guide

### Issue: Sparklines Not Displaying

**Symptoms:**
- Column C shows formula text instead of chart
- Or shows error: `#REF!` or `#VALUE!`

**Solutions:**
1. Check Data_Hidden sheet exists with data in rows 10-19
2. Verify formula uses correct sheet name: `Data_Hidden!A10:AC10`
3. Ensure column range is A:AC (29 periods), not A:AV (48 periods)
4. Confirm value_input_option='USER_ENTERED' in batch_update call

### Issue: Wrong Data in Sparklines

**Symptoms:**
- Row 10 works but rows 11-19 show wrong data
- Sparkline shows different fuel type's data

**Solutions:**
1. Check for enumerate pattern: `for idx, (_, row) in enumerate(gen_mix.iterrows())`
2. Verify row_num increments correctly after each iteration
3. Confirm Data_Hidden row numbers align with GB Live row numbers

### Issue: Interconnectors Overwriting Fuel Data

**Symptoms:**
- Columns A-C get replaced with interconnector data
- Sparklines disappear after interconnector update

**Solutions:**
1. Check interconnector range is `D{ic_row}:E{ic_row}` not `A{ic_row}:B{ic_row}`
2. Ensure ic_row starts at 10 and limits to 21
3. Verify fuel updates complete before interconnector updates run

### Issue: "Code Conflict" - Data Reverting

**Symptoms:**
- Script writes sparklines successfully
- Shortly after, data reverts to old format (e.g., "53.1%")
- Only affects some rows, not all

**Root Causes & Solutions:**
1. **Wrong enumerate usage** → Use `enumerate(gen_mix.iterrows())`
2. **Multiple scripts running** → Check `ps aux | grep update_bg_live`
3. **Apps Script trigger** → Check spreadsheet Extensions → Apps Script
4. **Manual user edits** → Coordinate timing with user

## Performance Considerations

### Query Efficiency

```python
# Fuel type query (fast - aggregates 30 periods × 40 fuel types)
SELECT fuelType, AVG(generation) as avg_gen
FROM bmrs_fuelinst_iris
WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
GROUP BY fuelType

# Interconnector query (fast - filters 10 specific codes)
SELECT fuelType, AVG(generation) as avg_flow
FROM bmrs_fuelinst_iris  
WHERE fuelType IN ('INTFR', 'INTVKL', 'INTNSL', ...)
GROUP BY fuelType
```

**Typical Execution:**
- BigQuery query: ~2 seconds
- Google Sheets API calls: ~3 seconds
- Total runtime: ~5 seconds
- Cost: Free tier (<<1GB scanned)

### Update Frequency

**Current:** Manual execution
```bash
python3 /home/george/GB-Power-Market-JJ/update_bg_live_dashboard.py
```

**Recommended:** Cron every 5 minutes
```bash
*/5 * * * * python3 /home/george/GB-Power-Market-JJ/update_bg_live_dashboard.py >> /home/george/logs/gb_live_dashboard.log 2>&1
```

**Rate Limits:**
- Google Sheets API: 300 requests/min per project
- BigQuery: 100 concurrent queries per project
- Current usage: ~6 API calls/run = 1.2 calls/min @ 5-min interval (well within limits)

## Testing & Validation

### Manual Verification

```bash
# Quick visual check
python3 << 'EOF'
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/home/george/inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
gb_live = gc.open_by_key('1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I').worksheet('GB Live')

for row in range(10, 20):
    a = gb_live.acell(f'A{row}').value
    c = gb_live.acell(f'C{row}', value_render_option='FORMULA').value
    d = gb_live.acell(f'D{row}').value
    
    has_sparkline = 'SPARKLINE' in str(c) if c else False
    print(f"Row {row}: {a} | Sparkline: {'✅' if has_sparkline else '❌'} | IC: {d}")
EOF
```

**Expected Output:**
```
Row 10: 💨 Wind | Sparkline: ✅ | IC: 🇫🇷 INTFR
Row 11: 🔥 CCGT | Sparkline: ✅ | IC: 🇩🇰 INTVKL
Row 12: ⚛️ Nuclear | Sparkline: ✅ | IC: 🇳🇴 INTNSL
...
```

### Data Freshness Check

```bash
# Verify IRIS data is recent
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
query = '''
SELECT MAX(settlementDate) as latest
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris\`
'''
print(client.query(query).to_dataframe())
"
```

**Expected:** Latest settlementDate should be within last 30 minutes

## Future Enhancements

### Potential Additions

1. **Interconnector Sparklines** (Column F)
   - Show flow trends over 48 periods
   - Color code: green for import, red for export
   - Implementation: Store IC timeseries in Data_Hidden rows 50-59

2. **Historical Comparison** (Column G)
   - Yesterday's value at same time
   - 7-day average
   - Show delta: "+2.3 GW vs yesterday"

3. **Conditional Formatting**
   - Red highlight if generation drops >20% in 30 minutes
   - Green highlight if renewables >60% of total
   - Orange alert if frequency deviation >0.2 Hz

4. **Interactive Filtering**
   - Dropdown to select fuel type
   - Expanded sparkline view (separate sheet)
   - Click fuel → jump to detailed analysis sheet

5. **Mobile Optimization**
   - Responsive layout for mobile viewing
   - Simplified view with fewer columns
   - Touch-friendly controls

## Related Documentation

- `PROJECT_CONFIGURATION.md` - BigQuery setup and credentials
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - IRIS data architecture
- `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` - Pipeline design
- `ENHANCED_BI_ANALYSIS_README.md` - Dashboard analytics

## Change Log

**December 8, 2025:**
- ✅ Changed sparklines from BAR to LINE charts
- ✅ Added color coding for each fuel type
- ✅ Added proper Y-axis scaling per fuel type
- ✅ Limited data range to 29 periods (removed trailing zeros)
- ✅ Fixed enumerate issue causing rows 11-19 to fail
- ✅ Moved interconnectors from rows 51-60 to rows 10-19, columns D-E
- ✅ Verified complete 5-column layout working

**Previous Versions:**
- November 2025: Initial implementation with percentage format only
- October 2025: Basic fuel type listing without sparklines

---

**Contact:** george@upowerenergy.uk  
**Repository:** https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Status:** ✅ Production (December 8, 2025)
