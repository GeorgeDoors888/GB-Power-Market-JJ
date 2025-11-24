# BESS DUoS Rate Fix Summary

## Issue
DUoS rates were showing **0.0000 p/kWh** for all time bands (Red, Amber, Green) in the BESS sheet after UpCloud deployment.

## Root Cause
The BigQuery query in `dno_lookup_python.py` was using date filtering logic that excluded future-effective rates:

```sql
WHERE effective_from <= CURRENT_DATE()
  AND (effective_to IS NULL OR effective_to >= CURRENT_DATE())
```

The NGED-WM HV rates in the `duos_unit_rates` table have:
- **effective_from**: 2026-04-01 (future date)
- **effective_to**: 2027-03-31

Since today is 2025-11-24, the query excluded all rates because they haven't taken effect yet.

## Solution
Changed the query to find the **closest rates by date** (either current or nearest future):

```sql
WITH ranked_rates AS (
    SELECT 
        time_band_name,
        ROUND(AVG(unit_rate_p_kwh), 4) as rate_p_kwh,
        effective_from,
        ROW_NUMBER() OVER (
            PARTITION BY time_band_name 
            ORDER BY ABS(DATE_DIFF(effective_from, CURRENT_DATE(), DAY))
        ) as rank
    FROM `inner-cinema-476211-u9.gb_power.duos_unit_rates`
    WHERE dno_key = 'NGED-WM'
      AND voltage_level = 'HV'
    GROUP BY time_band_name, effective_from
)
SELECT time_band_name, rate_p_kwh
FROM ranked_rates
WHERE rank = 1
```

This uses `ABS(DATE_DIFF(...))` to find rates with the smallest date distance from today, whether past or future.

## Additional Fixes

### LLFC Validation
Added validation to prevent using invalid LLFC codes:

```python
if llfc and len(str(llfc)) <= 4 and str(llfc).isdigit():
    llfc_filter = f" AND tariff_code LIKE '%{llfc}%'"
elif llfc:
    print(f"⚠️  LLFC {llfc} looks invalid (too long or not numeric), ignoring")
```

This prevents MPAN values (13 digits like "2412345678904") from being incorrectly used as LLFC codes.

### Debug Output
Added diagnostic output to help troubleshoot query issues:

```python
if len(rates_df) == 0:
    print(f"⚠️  WARNING: No rates found for {dno_key} {voltage_level}")
    print(f"Query: {rates_query}")
else:
    print(f"✅ Found {len(rates_df)} rate bands")
```

## Verified Results
After the fix, rates now display correctly for NGED-WM HV:

| Time Band | Rate (p/kWh) | Rate (£/MWh) | Schedule |
|-----------|--------------|--------------|----------|
| **Red** | 1.7640 | £17.64 | 16:00-19:30 weekdays |
| **Amber** | 0.2050 | £2.05 | 08:00-16:00, 19:30-22:00 weekdays |
| **Green** | 0.0110 | £0.11 | 00:00-08:00, 22:00-23:59, all weekend |

## Deployment Status
✅ Fixed script deployed to UpCloud server (94.237.55.234)  
✅ Monitor service restarted (PID 349308)  
✅ Webhook service running (PID 348344)  
✅ Manual test confirmed: `python3 dno_lookup_python.py 14 HV`  

## Files Modified
- `dno_lookup_python.py` (lines 199-217) - Query logic updated
- Services automatically pick up changes after restart

## Testing
```bash
# Manual test
ssh root@94.237.55.234 'cd /opt/bess && python3 dno_lookup_python.py 14 HV'

# Check monitor logs
ssh root@94.237.55.234 'tail -f /var/log/bess/monitor.log'

# Test webhook
curl -X POST http://94.237.55.234:5001/trigger-dno-lookup
```

---
**Fixed**: 2025-11-24 18:07 UTC  
**Issue**: Future-dated rates excluded by date filter  
**Solution**: Closest-date query using ABS(DATE_DIFF)
