# BESS HH Profile Generator - USER GUIDE

## ⚠️ IMPORTANT: THIS IS A DEMAND PROFILE TOOL, NOT A REVENUE CALCULATOR

## Overview
**Script**: `bess_hh_profile_generator.py`  
**Purpose**: Generate half-hourly charge/discharge demand profiles for network analysis  
**Status**: ⚠️ Educational/Network Analysis Tool (28 Dec 2025)

**NOT SUITABLE FOR**: Revenue forecasting, trading decisions, financial analysis

## What This Tool Does
- ✅ Creates charge/discharge patterns based on price signals
- ✅ Tracks battery State of Charge (SOC) over time
- ✅ Shows DUoS cost impact on consumption (charging only)
- ✅ Useful for network impact analysis and grid connection studies
- ✅ Educational tool for understanding battery behavior

## What This Tool DOES NOT Do
- ❌ **Calculate real battery revenue** (uses wrong model - see below)
- ❌ Account for Balancing Mechanism bids/offers (actual revenue source)
- ❌ Include frequency response contracts (FFR, DCH, DM, DR)
- ❌ Model wholesale trading strategies
- ❌ Apply to generation/export (DUoS rates are consumption-only!)

## ⚠️ Critical Limitation: Revenue Model is Wrong

**The Problem**: This tool applies DUoS rates to battery discharge (generation), which is incorrect:
- **DUoS rates apply to CONSUMPTION (import) only**, not generation/export
- Real battery revenue comes from **Balancing Mechanism acceptances** (£/MWh × MWh from BOALF data)
- The "£295.13 revenue" example is **misleading** - it assumes you pay DUoS when selling to grid (you don't)

**For Real Battery Revenue Analysis**: Use `boalf_with_prices` table (BM acceptances with actual £ paid by National Grid)

## Quick Start

### Basic Usage
```bash
python3 bess_hh_profile_generator.py \
  --start-date 2024-10-17 \
  --end-date 2024-10-18 \
  --dno NGED-WM \
  --voltage HV \
  --output both
```

### With Custom Battery Parameters
```bash
python3 bess_hh_profile_generator.py \
  --start-date 2024-10-17 \
  --end-date 2024-10-18 \
  --dno UKPN-EPN \
  --voltage LV \
  --capacity 5.0 \
  --power 2.5 \
  --efficiency 0.88 \
  --output sheets
```

## Command Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--start-date` | ✅ Yes | - | Start date (YYYY-MM-DD) |
| `--end-date` | ✅ Yes | - | End date (YYYY-MM-DD) |
| `--dno` | No | NGED-WM | DNO key (see DNO list below) |
| `--voltage` | No | HV | Voltage level (LV or HV) |
| `--capacity` | No | 2.0 | Battery capacity (MWh) |
| `--power` | No | 1.0 | Max charge/discharge power (MW) |
| `--efficiency` | No | 0.90 | Round-trip efficiency (0-1) |
| `--output` | No | both | Output format: csv, sheets, or both |
| `--csv-file` | No | bess_hh_profile.csv | CSV filename |

## DNO Keys (for --dno argument)

| DNO Key | DNO Name | Region |
|---------|----------|--------|
| NGED-WM | NGED West Midlands | Birmingham, Coventry |
| NGED-EM | NGED East Midlands | Leicester, Nottingham |
| NGED-SW | NGED South West | Bristol, Plymouth |
| NGED-S | NGED South Wales | Cardiff, Swansea |
| UKPN-EPN | UKPN Eastern | East Anglia |
| UKPN-LPN | UKPN London | Greater London |
| UKPN-SPN | UKPN South East | Kent, Sussex |
| NPG | Northern Powergrid | North East England |
| SSE-SEPD | SSE Southern | Oxford, Portsmouth |
| SSE-SHEPD | SSE Scottish Hydro | Highlands, Islands |
| ENWL | Electricity North West | Manchester, Liverpool |
| SPEN-SPD | SP Energy Networks South | Central Scotland |
| SPEN-SPMW | SP Energy Networks Manweb | North Wales, Cheshire |
| SSEN-SEPD | SSEN South | South England |

## Output Format

### CSV Columns
| Column | Description | Example |
|--------|-------------|---------|
| `datetime` | UK timestamp | 2024-10-17 16:00:00+01:00 |
| `date` | Date | 2024-10-17 |
| `period` | Settlement period (1-48) | 33 |
| `band` | DUoS time band | RED |
| `is_weekend` | Weekend flag | False |
| `price_gbp_mwh` | Imbalance price (£/MWh) | 126.69 |
| `duos_p_kwh` | DUoS rate (p/kWh) | 1.764 |
| `duos_gbp_mwh` | DUoS rate (£/MWh) | 17.64 |
| `action` | CHARGE/DISCHARGE/HOLD | DISCHARGE |
| `power_mw` | Power (MW) | 1.0 |
| `energy_mwh` | Energy (MWh) | 0.5 |
| `soc` | State of Charge (0-1) | 0.525 |
| `revenue_gbp` | Revenue (£) | 54.52 |

### Google Sheets Output
- Exports to spreadsheet: `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`
- Creates/overwrites sheet: "HH Profile"
- Same columns as CSV format

## Example Results

### Test Run: Oct 17-18, 2024 (High Price Period)
**Configuration**:
- Battery: 2.0 MWh, 1.0 MW
- DNO: NGED West Midlands (HV)
- DUoS Rates: Red 1.764, Amber 0.205, Green 0.011 p/kWh

**⚠️ IMPORTANT: These "revenue" figures are NOT realistic - they assume DUoS applies to generation (it doesn't)**

**Results (Demand Profile)**:
```
Total Periods:        96 (2 days × 48 periods)
Charge Periods:       23 (consumption: 6.11 MWh)
Discharge Periods:    14 (generation: 6.30 MWh)
Hold Periods:         59 (no action)
Average SOC:          50.1%
```

**What This Shows**:
- Battery would charge 23 times during low prices (£70.50/MWh avg)
- Battery would discharge 14 times during high prices (£127/MWh avg)
- Price differential: £56.50/MWh average spread
- **Network impact**: Shows when battery stresses grid (charging = import, discharging = export)

**For Real Revenue**: Query `boalf_with_prices` table for actual BM acceptances:
```sql
SELECT SUM(revenue_estimate_gbp) 
FROM boalf_with_prices 
WHERE bm_unit_id IN ('FBPGM002', 'FFSEN005')  -- VLP battery units
  AND acceptance_date BETWEEN '2024-10-17' AND '2024-10-18'
  AND validation_flag = 'Valid'
```
**Actual Oct 17-18 VLP Revenue**: Query this for real numbers!

## Strategy Logic

### Decision Algorithm
The generator uses a simple **price-based arbitrage** strategy:

1. **DISCHARGE** when:
   - Price > daily average × 1.2
   - SOC > minimum (10%)
   - Revenue = Energy × (Price - DUoS)

2. **CHARGE** when:
   - Price < daily average × 0.8
   - SOC < maximum (95%)
   - Cost = Energy × (Price + DUoS)

3. **HOLD** otherwise (preserve battery cycles)

### DUoS Time Bands (UK Standard)
- **RED** (highest cost): 16:00-19:30 weekdays
- **AMBER**: 08:00-16:00 + 19:30-22:00 weekdays
- **GREEN** (lowest cost): 00:00-08:00 + 22:00-23:59 weekdays + all weekend

## Integration with BESS Calculator

### Menu Item (Apps Script)
The BESS sheet menu has "Generate HH Profile" option which:
1. Reads date range from sheet cells
2. Calls this Python script via webhook
3. Imports results back to sheet

### Manual Integration
```python
from bess_hh_profile_generator import generate_hh_profile, export_to_sheets

# Generate profile
profile_df = generate_hh_profile(
    start_date='2024-10-17',
    end_date='2024-10-18',
    dno_key='NGED-WM',
    voltage='HV'
)

# Export to sheets
export_to_sheets(profile_df, sheet_name='HH Profile')
```

## Troubleshooting

### "No price data found"
- Check date range is within bmrs_costs table coverage (2016-present)
- Verify dates are in YYYY-MM-DD format
- Historical data may have gaps before 2020

### "No DUoS rates found"
- Verify DNO key matches table (use `--dno` list above)
- Check voltage level is LV or HV (case sensitive)
- Falls back to NGED-WM defaults if lookup fails

### "404 Not found: Table bmrs_costs"
- Ensure `inner-cinema-credentials.json` is in current directory
- Check BigQuery access with smart.grd@gmail.com account

### Large date ranges
- Recommend <= 7 days per run (336 periods)
- Longer ranges increase memory usage
- Consider splitting into weekly batches

## Advanced Usage

### Custom Optimization
Modify strategy logic in `generate_hh_profile()` function:
- Line 270: Discharge threshold (currently 1.2× daily avg)
- Line 282: Charge threshold (currently 0.8× daily avg)
- Line 285-290: Battery constraints (power, SOC limits)

### Batch Processing
```bash
# Generate profiles for entire month
for day in {01..31}; do
  python3 bess_hh_profile_generator.py \
    --start-date 2024-10-$day \
    --end-date 2024-10-$day \
    --output csv \
    --csv-file profiles/oct_$day.csv
done
```

### Revenue Analysis
```python
import pandas as pd
df = pd.read_csv('bess_hh_profile.csv')

# Revenue by hour of day
hourly = df.groupby(df['datetime'].str[11:13])['revenue_gbp'].sum()
print(hourly.sort_values(ascending=False).head(10))

# Best days
daily = df.groupby('date')['revenue_gbp'].sum()
print(daily.sort_values(ascending=False))
```

## Files

| File | Purpose |
|------|---------|
| `bess_hh_profile_generator.py` | Main script (389 lines) |
| `bess_hh_profile.csv` | Default CSV output |
| `test_profile.csv` | Test output (Oct 17-18) |

## Related Scripts

- `bess_live_duos_tracker.py` - Real-time DUoS band display
- `dno_webapp_client.py` - DNO lookup via postcode/MPAN
- `btm_dno_lookup.py` - BtM sheet DNO automation

## Next Steps

1. **Optimize Strategy**: Add machine learning for price prediction
2. **Frequency Response**: Include FFR/DCH revenue streams
3. **Multi-Day Optimization**: Optimize across rolling 7-day windows
4. **Degradation Model**: Account for cycle life costs
5. **Real-Time Mode**: Generate live schedules with forecasted prices

---

**Status**: ✅ Production Ready  
**Last Updated**: 28 December 2025  
**Maintainer**: george@upowerenergy.uk  
**Test Results**: £295.13 revenue (Oct 17-18, 2MWh battery, NGED-WM HV)
