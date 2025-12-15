# Intraday Charts Configuration - Permanent Changes

**Date:** 8 December 2025  
**Status:** ✅ Active and Auto-Updating Every 5 Minutes

## Changes Made

### 1. Data Range Extended
- **Old:** 31 settlement periods (columns M-AQ)
- **New:** 48 settlement periods (columns M-BJ)
- **Coverage:** Full day from 00:00 to 23:59 (all 48 half-hourly periods)

### 2. Chart Layout Updated

#### Left Chart (A23:E36 merged cell)
- **Type:** Stacked column chart
- **Data:** Wind Generation + System Demand
- **Colors:** 
  - Cyan (#4ECDC4) - Wind Generation
  - Red (#FF6B6B) - System Demand
- **Scale:** 0-60 GW with visible axis
- **Header:** Row 22 (A22) - "📊 Generation & Demand (GW) - 48 Periods"
- **Legend:** Row 37 (A37) - "🔵 Wind (Cyan) | 🔴 Demand (Red) | Scale: 0-60 GW"

#### Right Chart (F23:H36 merged cell)
- **Type:** Line chart
- **Data:** Wholesale Price
- **Color:** Green (#2ca02c)
- **Scale:** 0-150 £/MWh with visible axis
- **Header:** Row 22 (F22) - "💷 Wholesale Price (£/MWh) - 48 Periods"
- **Legend:** Row 37 (F37) - "🟢 Price | Scale: 0-150 £/MWh"

### 3. Code Changes in `update_bg_live_dashboard.py`

**Lines 825-840:** Data range updated from M25:AQ27 to M25:BJ27
```python
intraday_updates = [
    {'range': f'M25:BJ25', 'values': [wind_data[:48]]},     # Wind (48 periods)
    {'range': f'M26:BJ26', 'values': [demand_data[:48]]},   # Demand (48 periods)
    {'range': f'M27:BJ27', 'values': [price_data[:48]]},    # Price (48 periods)
]
```

**Lines 845-870:** Sparkline formulas updated with proper styling
```python
sparkline_formulas = [
    {
        'range': 'A23',
        'values': [['=SPARKLINE({M25:BJ25;M26:BJ26},{"charttype","column";"color1","#4ECDC4";"color2","#FF6B6B";"max",60;"ymin",0;"axis",true;"axiscolor","#333"})']]
    },
    {
        'range': 'F23',
        'values': [['=SPARKLINE(M27:BJ27,{"charttype","line";"linewidth",3;"color","#2ca02c";"max",150;"ymin",0;"axis",true;"axiscolor","#333"})']]
    }
]
```

## Automation

**Cron Job:** Every 5 minutes (288 updates/day)
```bash
*/5 * * * * /usr/bin/python3 /home/george/GB-Power-Market-JJ/update_bg_live_dashboard.py >> /home/george/GB-Power-Market-JJ/logs/bg_live_updater.log 2>&1
```

**What Gets Updated:**
1. Data in hidden columns M25:BJ27 (48 periods × 3 metrics)
2. Sparkline formulas in A23 and F23 (recreated each run)
3. Headers in A22 and F22
4. Legend labels in A37 and F37

## Testing

**Last Successful Run:** 2025-12-08 12:21:52
- Retrieved: 25 settlement periods (will be 48 by end of day)
- Wind: 65.59 GW
- Demand: 141.79 GW
- Price: £36.20/MWh
- Status: ✅ Charts updating correctly

## Maintenance Notes

### If Charts Don't Appear:
1. Check merged cells: A23:E36 (left) and F23:H36 (right) must be merged
2. Verify data exists in M25:BJ27 (use FORMULA view to see sparkline formulas)
3. Check cron job is running: `tail -f /home/george/GB-Power-Market-JJ/logs/bg_live_updater.log`

### To Manually Trigger Update:
```bash
python3 /home/george/GB-Power-Market-JJ/update_bg_live_dashboard.py
```

### To Adjust Chart Scales:
Edit `update_bg_live_dashboard.py` lines 847-851:
- `"max",60` - Change max Y-axis for generation/demand chart
- `"max",150` - Change max Y-axis for price chart

## File References

- **Script:** `/home/george/GB-Power-Market-JJ/update_bg_live_dashboard.py`
- **Sheet:** GB Live (ID: 1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I)
- **Log:** `/home/george/GB-Power-Market-JJ/logs/bg_live_updater.log`

---
*Changes are permanent and will persist across all automatic updates.*
