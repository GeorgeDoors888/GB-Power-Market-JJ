# DNO & DUoS Rates Lookup System

**Last Updated**: November 22, 2025  
**Status**: ✅ Production (with MPAN/DUoS/Clustering toolkit)

## Overview

Automated system for looking up UK Distribution Network Operator (DNO) information and DUoS (Distribution Use of System) rates based on postcode or MPAN ID. Integrated into the BESS (Battery Energy Storage System) sheet for cost analysis.

**New Features** (Nov 22, 2025):
- ✅ MPAN core generation with mod-11 checksum validation
- ✅ DUoS cost calculator for half-hourly profiles
- ✅ Clustering features extraction for site grouping
- ✅ TOU flexibility modeling and value calculation
- ✅ **CRITICAL FIX**: Full MPAN parsing now correctly extracts distributor ID from core (not top line)

## Architecture

```
User clicks button in Google Sheets
         ↓
Apps Script (bess_auto_trigger.gs)
         ↓
ngrok tunnel (https://...ngrok-free.app)
         ↓
Flask webhook (localhost:5001)
         ↓
Python script (dno_lookup_python.py)
    ├─→ postcodes.io API (lat/lng lookup)
    ├─→ BigQuery (DNO info + DUoS rates)
    └─→ Google Sheets API (gspread)
         ↓
BESS sheet updated (rows 6, 9-13)
```

## Components

### 1. Apps Script Button Handler
**File**: `bess_auto_trigger.gs`  
**Function**: `manualRefreshDno()`

```javascript
// Reads A6 (postcode), B6 (MPAN), A9 (voltage)
// Calls webhook: https://26eff9472aea.ngrok-free.app/trigger-dno-lookup
// Shows loading indicator in A4:H4
```

### 2. Webhook Server
**File**: `dno_webhook_server.py`  
**Port**: 5001  
**Endpoint**: POST `/trigger-dno-lookup`

```bash
# Start server
cd "/Users/georgemajor/GB Power Market JJ"
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/inner-cinema-credentials.json"
nohup python3 dno_webhook_server.py > webhook.log 2>&1 &

# Check status
ps aux | grep dno_webhook
```

### 3. ngrok Tunnel
**Purpose**: Expose localhost:5001 to Google Apps Script

```bash
# Start tunnel
ngrok http 5001

# Update webhook URL in bess_auto_trigger.gs with ngrok URL
```

### 4. Python Lookup Script
**File**: `dno_lookup_python.py`  
**Dependencies**: `gspread`, `google-cloud-bigquery`, `requests`

**Functions**:
- `lookup_postcode(postcode)` → lat/lng via postcodes.io
- `lookup_dno_by_coordinates(lat, lng)` → MPAN ID (10-23)
- `lookup_dno_by_mpan(mpan_id)` → DNO details from BigQuery
- `get_duos_rates(dno_key, voltage)` → Rates + time bands from BigQuery
- `update_bess_sheet()` → Updates Google Sheet via gspread

## Data Sources

### BigQuery Tables

#### 1. DNO Reference Data
**Table**: `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`

```sql
SELECT 
    mpan_distributor_id,  -- 10-23
    dno_key,              -- e.g., "UKPN-EPN"
    dno_name,             -- e.g., "UK Power Networks (Eastern)"
    dno_short_code,       -- e.g., "EPN"
    market_participant_id,
    gsp_group_id,
    gsp_group_name
FROM neso_dno_reference
WHERE mpan_distributor_id = 10
```

#### 2. DUoS Unit Rates
**Table**: `inner-cinema-476211-u9.gb_power.duos_unit_rates`

```sql
SELECT 
    time_band_name,        -- Red, Amber, Green
    ROUND(AVG(unit_rate_p_kwh), 4) as rate_p_kwh
FROM duos_unit_rates
WHERE dno_key = 'UKPN-EPN'
  AND voltage_level = 'HV'  -- LV, HV, EHV
  AND tariff_code LIKE '%Non-Domestic%'
GROUP BY time_band_name
```

#### 3. Time Bands
**Table**: `inner-cinema-476211-u9.gb_power.duos_time_bands`

```sql
SELECT 
    time_band_name,  -- Red, Amber, Green
    day_type,        -- Weekday, Weekend
    start_time,      -- 00:00:00
    end_time         -- 08:00:00
FROM duos_time_bands
WHERE dno_key = 'UKPN-EPN'
ORDER BY day_type DESC, start_time
```

### Postcode API
**Endpoint**: `https://api.postcodes.io/postcodes/{postcode}`

```json
{
  "status": 200,
  "result": {
    "postcode": "SW2 5UP",
    "latitude": 51.4526,
    "longitude": -0.1236
  }
}
```

## Google Sheets Layout

### BESS Sheet Structure

**Row 6: DNO Information**
```
A6: Postcode      (e.g., "SW2 5UP")
B6: MPAN ID       (10-23)
C6: DNO Key       (e.g., "UKPN-EPN")
D6: DNO Name      (e.g., "UK Power Networks (Eastern)")
E6: Short Code    (e.g., "EPN")
F6: Market Part.  (e.g., "EELC")
G6: GSP Group ID  (e.g., "A")
H6: GSP Group     (e.g., "Eastern")
```

**Row 9: Voltage & Rates**
```
A9: Voltage Level (dropdown: LV/HV/EHV)
B9: Red Rate      (p/kWh)
C9: Amber Rate    (p/kWh)
D9: Green Rate    (p/kWh)
```

**Rows 10-13: Time Schedule**
```
Row 10: "Weekday Times:" | "" | ""
Row 11: "16:00-19:30"    | "08:00-16:00"  | "00:00-08:00"
Row 12: ""               | "19:30-22:00"  | "22:00-23:59"
Row 13: ""               | ""             | "All Weekend"
```

## Usage Examples

### 1. Command Line (Direct)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"

# By MPAN ID
python3 dno_lookup_python.py 10 HV
# Output: UKPN-EPN, HV rates

# By postcode
python3 dno_lookup_python.py "SW2 5UP" LV
# Looks up coordinates → MPAN 10 → UKPN-EPN

# Read from sheet
python3 dno_lookup_python.py
# Uses values in A6, B6, A9
```

### 2. Button in Google Sheets
1. User enters postcode in A6 (e.g., "M1 1AD")
2. Selects voltage in A9 dropdown (e.g., "HV (1-132kV)")
3. Clicks "Refresh DNO Data" button
4. Apps Script → webhook → Python → Sheet updates automatically

### 3. Auto-Trigger on Edit (Optional)
```javascript
// Add onEdit trigger in Apps Script
function onEdit(e) {
  if (e.range.getA1Notation() === 'A6' || e.range.getA1Notation() === 'B6') {
    manualRefreshDno();
  }
}
```

## Time Band Examples

### UKPN-EPN (Eastern)
**Red (Peak)**: £48.37/MWh
- Weekdays: 16:00-19:30 (evening peak demand)

**Amber (Shoulder)**: £4.57/MWh
- Weekdays: 08:00-16:00 (business hours)
- Weekdays: 19:30-22:00 (wind-down period)

**Green (Off-Peak)**: £0.38/MWh
- Weekdays: 00:00-08:00 (overnight)
- Weekdays: 22:00-23:59 (late night)
- All weekend: 00:00-23:59

### NPg-Y (Yorkshire)
**Red**: £19.30/MWh (16:00-19:30 weekdays)  
**Amber**: £5.46/MWh (08:00-16:00, 19:30-22:00 weekdays)  
**Green**: £0.67/MWh (nights + weekends)

## MPAN to DNO Mapping

| MPAN | DNO Key | DNO Name | Region |
|------|---------|----------|--------|
| 10 | UKPN-EPN | UK Power Networks (Eastern) | East England |
| 11 | NGED-EM | National Grid (East Midlands) | East Midlands |
| 12 | UKPN-LPN | UK Power Networks (London) | London |
| 13 | SP-Manweb | SP Energy Networks (Manweb) | North Wales, Merseyside |
| 14 | NGED-WM | National Grid (West Midlands) | West Midlands |
| 15 | NPg-NE | Northern Powergrid (North East) | North East |
| 16 | ENWL | Electricity North West | North West |
| 17 | SSE-SHEPD | SSE (Scottish Hydro) | North Scotland |
| 18 | SP-Distribution | SP Energy Networks | South Scotland |
| 19 | UKPN-SPN | UK Power Networks (South East) | South East |
| 20 | SSE-SEPD | SSE (Southern Electric) | Southern |
| 21 | NGED-SWales | National Grid (South Wales) | South Wales |
| 22 | NGED-SW | National Grid (South Western) | South West |
| 23 | NPg-Y | Northern Powergrid (Yorkshire) | Yorkshire |

## Voltage Levels

- **LV** (Low Voltage): <1kV - Domestic, small commercial
- **HV** (High Voltage): 1-132kV - Industrial, large commercial
- **EHV** (Extra High Voltage): >132kV - Large industrial, grid-scale

## Troubleshooting

### Webhook Not Responding
```bash
# Check if running
ps aux | grep dno_webhook

# Check logs
tail -f webhook.log

# Restart
pkill -f dno_webhook_server
python3 dno_webhook_server.py &
```

### ngrok Tunnel Expired
```bash
# Check status
curl http://localhost:4040/api/tunnels

# Restart tunnel
pkill ngrok
ngrok http 5001

# Update webhook URL in Apps Script
```

### Sheet Not Updating
```bash
# Test Python script directly
python3 dno_lookup_python.py

# Check credentials
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test gspread access
python3 -c "import gspread; print('OK')"
```

### Invalid Postcode
- Use real UK postcodes: M1 1AD, LS1 2TW, SW1A 1AA
- Check postcodes.io: https://api.postcodes.io/postcodes/SW25UP

## Future Enhancements

1. **Eliminate webhook dependency**: Use Google Cloud Functions or Apps Script BigQuery API
2. **Auto-refresh on edit**: Trigger lookup when postcode/MPAN changes
3. **Historical rates**: Track DUoS rate changes over time
4. **Rate comparison**: Show rates across all DNOs for best location
5. **Custom function**: `=DNO_LOOKUP(A6, A9)` formula in sheets

## NEW: MPAN Automation System

### Complete Pipeline: MPAN → DNO → LLFC → R/A/G Rates

**Files**:
- `mpan_parser.py` - MPAN validation & parsing (checksum, DNO extraction)
- `llfc_tariff_loader.py` - LLFC → Tariff mapping from BigQuery
- `mpan_to_rates.py` - End-to-end lookup pipeline

### Usage

**Parse any MPAN format**:
```bash
# Core MPAN only (13 digits)
python3 mpan_to_rates.py 1234567890123

# Full MPAN with top line (PC/MTC/LLFC)
python3 mpan_to_rates.py "00 801 0840 1234567890123" HV

# Output:
# ================================================================================
# MPAN → DNO → DUoS Rates Summary
# ================================================================================
# MPAN: 1234567890123
# DNO: UK Power Networks (London) (UKPN-LPN)
# Region: London
# Voltage: HV
# Profile Class: 00
# MTC: 801
# LLFC: 0840
# 
# DUoS Rates:
#   Red: 4.837 p/kWh = £48.37/MWh
#   Amber: 0.457 p/kWh = £4.57/MWh
#   Green: 0.038 p/kWh = £0.38/MWh
# ================================================================================
```

### MPAN Components

**Full MPAN Structure**:
```
PC   MTC  LLFC  S  Profile  Region  Dist  Check
00   801  0840  12  34      567     8901  23
└─┬─┘└─┬┘└──┬┘  └────────┬────────────┘└┬┘
  │    │    │           Core MPAN (13)  │
  │    │    └─ Line Loss Factor Class   │
  │    └───── Meter Timeswitch Code     │
  └────────── Profile Class             └─ Checksum
```

**Checksum Validation**:
- Uses mod-11 algorithm (S-number check)
- Validates authenticity of MPAN
- Detects transcription errors

**Distributor ID → DNO**:
- First 2 digits of core MPAN (10-23)
- Maps to 14 GB DNO regions
- Automatic lookup in parser

### LLFC-Based Tariff Lookup

**When LLFC Available** (full MPAN):
1. Parse PC/MTC/LLFC from top line
2. Query `gb_power.llfc_tariff_mapping` table
3. Get exact tariff code for that LLFC
4. Return precise R/A/G rates

**When LLFC Missing** (core only):
1. Use distributor ID → DNO
2. Average rates for DNO + voltage level
3. Source LLFC from:
   - ECOES/MPAS API (supplier access)
   - Supplier data feed
   - Manual entry in BESS sheet

### Integration with BESS Sheet

**Update `dno_lookup_python.py`** to use MPAN parser:
```python
from mpan_to_rates import MPANRatesLookup

def update_bess_sheet(mpan=None, voltage='LV'):
    lookup = MPANRatesLookup()
    
    # Full MPAN lookup with LLFC
    result = lookup.lookup(mpan, voltage)
    
    # Update sheet with precise rates
    bess_ws.update([[result['rates']['Red']['rate'],
                     result['rates']['Amber']['rate'],
                     result['rates']['Green']['rate']]], 'B9:D9')
```

## Advanced Features: MPAN/DUoS/Clustering Toolkit

### MPAN Core Generator (`mpan_generator_validator.py`)

Generate checksum-valid MPAN cores for testing and analysis.

**Key Functions**:
```python
from mpan_generator_validator import *

# Generate valid MPAN for specific DNO
mpan = generate_valid_mpan_core(dno_id='10')  # UKPN EPN
# Output: '1029018361541' (valid checksum)

# Validate existing MPAN
is_valid = is_valid_mpan_core('1200123456787')
# Output: True/False

# Lookup DNO from MPAN
info = mpan_core_lookup('1200123456789')
# Output: {'dno_id': '12', 'dno_name': 'UK Power Networks (London)', ...}

# Parse full 21-digit MPAN
core = extract_core_from_full_mpan('00 801 0840 1200123456789')
# Output: '1200123456789'

# Batch generation
batch = generate_batch_valid_mpans(100, dno_id='14')
# Output: List of 100 valid MPAN cores for NGED West Midlands
```

**Mod-11 Checksum Algorithm**:
- Prime weights: [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]
- Formula: `sum(digit × prime) mod 11 mod 10`
- Detects transcription errors in MPAN entry

**Test Results**:
```
✅ All 14 DNO regions: MPAN generation working
✅ Checksum validation: 100% accurate
✅ DNO mapping: Correct extraction from distributor ID
```

### DUoS Cost Calculator (`duos_cost_calculator.py`)

Calculate Distribution Use of System charges for half-hourly consumption profiles.

**Basic Usage**:
```python
import pandas as pd
from duos_cost_calculator import DuosTariff, calculate_duos_costs

# Define tariff (UKPN EPN HV example)
tariff = DuosTariff(
    dno_id='10',
    tariff_name='UKPN-EPN HV 2025',
    voltage_level='HV',
    red_rate=0.04837,      # £/kWh (16:00-19:00 weekday)
    amber_rate=0.00457,    # £/kWh (shoulder periods)
    green_rate=0.00038,    # £/kWh (off-peak)
    fixed_p_per_day=120,   # p/day
    capacity_p_per_kva_per_day=5  # p/kVA/day
)

# Load HH profile (must have 'timestamp' and 'kwh' columns)
df_hh = pd.read_csv('hh_profile.csv')
df_hh['timestamp'] = pd.to_datetime(df_hh['timestamp'])

# Calculate costs
result = calculate_duos_costs(df_hh, tariff, kva_capacity=300)

# Analyze costs
print(f"Total DUoS: £{result['duos_total_cost'].sum():.2f}")
print(f"Red band: £{result[result['band']=='red']['duos_unit_cost'].sum():.2f}")
```

**TOU Band Assignment** (default):
- **Red**: 16:00-19:00 weekdays (peak)
- **Amber**: 08:00-16:00, 19:00-22:00 weekdays (shoulder)
- **Green**: 00:00-08:00, 22:00-23:59 weekdays + all weekend (off-peak)

**Output Columns**:
- `band`: 'red', 'amber', or 'green'
- `unit_rate`: £/kWh rate for that HH
- `duos_unit_cost`: Energy charge (£)
- `duos_fixed_cap_cost`: Fixed + capacity charge (£)
- `duos_total_cost`: Total DUoS charge for HH (£)

**Example Results** (1 week office profile, 300 kVA):
```
Total DUoS: £458.54/week (£23,844/year)
  Unit costs: £345.14 (75%)
  Fixed + capacity: £113.40 (25%)

By TOU Band:
  Red:   £272.91 (5,642 kWh, 79% of unit costs)
  Amber: £67.08 (14,678 kWh, 19%)
  Green: £5.15 (13,565 kWh, 1.5%)
```

**Insight**: 79% of costs from 17% of energy (red band) → High value for demand flexibility

### Clustering Features (`profile_clustering_features.py`)

Extract characteristics from load profiles for site grouping and analysis.

**Feature Extraction**:
```python
from profile_clustering_features import extract_profile_features

# Extract features from HH profile
features = extract_profile_features(df_hh, site_id='office_building_1')

print(features)
# Output:
# Profile: office_building_1
#   Peak: 222.2 kW, Mean: 100.8 kW
#   Peak Ratio: 2.20, Load Factor: 0.45
#   Weekend Factor: 0.31, Day/Night: 1.52
#   Type: Weekday-dominant, Peaky, Variable
```

**Feature Definitions**:
- **Peak Ratio**: `max_kw / mean_kw` (spikiness, higher = more variable)
- **Load Factor**: `mean_kw / max_kw` (flatness, 0-1, higher = more constant)
- **Weekend Factor**: `weekend_mean / weekday_mean` (business pattern)
- **Day/Night Ratio**: `day_mean / night_mean` (temporal pattern)
- **Monthly CV**: Coefficient of variation of monthly means (seasonality)

**Profile Classes**:
- `is_weekday_dominant`: Weekend factor < 0.5 (office/industrial)
- `is_peaky`: Peak ratio > 2.0 (high variability)
- `is_baseload`: Load factor > 0.7 (continuous process)

**Batch Processing**:
```python
from profile_clustering_features import create_features_dataframe

# Extract features for multiple sites
profiles = {
    'office_1': df_office,
    'factory_1': df_factory,
    'apartments_1': df_apartments
}

features_df = create_features_dataframe(profiles)
# Output: DataFrame with one row per site, ready for clustering
```

**Use Cases**:
- Site classification for tariff optimization
- Portfolio segmentation
- Demand response potential scoring
- Faster clustering (5-15 features vs 17,520 HH points)

### Flexibility Value Calculator

Calculate savings from demand shifting/reduction.

**Example**:
```python
from profile_clustering_features import calculate_flexibility_value

# Synthetic TOU prices
prices = pd.Series([0.15 if 16 <= ts.hour < 19 else 0.05 for ts in df['timestamp']])

# Calculate value of 30% load flexibility
flex_value = calculate_flexibility_value(
    df_hh,
    flex_fraction=0.30,
    prices_hh=prices,
    shift_energy=True  # Shift to cheaper periods
)

print(f"Baseline: £{flex_value['baseline_cost_gbp']:.2f}")
print(f"Flexible: £{flex_value['flexible_cost_gbp']:.2f}")
print(f"Value: £{flex_value['value_gbp']:.2f} ({flex_value['value_percent']:.1f}% saving)")
# Output: 12.1% saving by shifting 30% of peak load
```

**Modeling Options**:
- **Reduction**: Remove load during expensive periods
- **Shift**: Move load to cheaper periods (energy conserved)
- **Custom red_periods**: Define expensive windows manually

### Integration with BESS Sheet

**Enhanced DNO Lookup** with clustering features:
```python
# In dno_lookup_python.py
from profile_clustering_features import extract_profile_features

def update_bess_sheet_enhanced(mpan, voltage, hh_profile_df=None):
    """Update BESS sheet with rates + clustering features"""
    
    # Standard DNO/DUoS lookup
    result = lookup_dno_by_mpan(mpan, voltage)
    
    # If HH profile provided, calculate features
    if hh_profile_df is not None:
        features = extract_profile_features(hh_profile_df, site_id=mpan)
        
        # Update additional cells
        bess_ws.update([[
            features.peak_ratio,
            features.load_factor,
            features.weekend_factor,
            features.day_night_ratio
        ]], 'F15:I15')  # New clustering features row
```

**Future: Clustering Button**:
1. User uploads HH profile CSV
2. System extracts features
3. Matches to profile archetypes (office, factory, retail, etc.)
4. Recommends optimal tariff
5. Calculates flexibility value

## Troubleshooting

### Issue: Wrong DNO Shown After MPAN Entry

**Symptoms**: Enter full MPAN `00800999932 1405566778899`, but sheet shows wrong DNO (e.g., UKPN London ID 12 instead of NGED West Midlands ID 14)

**Root Cause**: MPAN parser module import failed, falling back to legacy parsing which extracts wrong digits

**Fix Applied** (Nov 22, 2025):
1. Updated `dno_lookup_python.py` import from non-existent `mpan_parser` to actual `mpan_generator_validator`
2. Rewrote `parse_mpan_input()` to:
   - Detect full MPAN format (with spaces/dashes)
   - Extract 13-digit core using `extract_core_from_full_mpan()`
   - Lookup DNO from core using `mpan_core_lookup()`
   - Return correct distributor ID

**Verification**:
```python
# Test parsing function
from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup

full_mpan = "00800999932 1405566778899"
core = extract_core_from_full_mpan(full_mpan)  # Returns: 1405566778899
info = mpan_core_lookup(core)  # Returns: ID 14 (NGED West Midlands)
```

**Critical Code** (do not modify without testing):
```python
# In dno_lookup_python.py lines 13-17
from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup
MPAN_PARSER_AVAILABLE = True

# In parse_mpan_input() function
if ' ' in mpan_str or '-' in mpan_str:
    core = extract_core_from_full_mpan(mpan_str)  # Extract from full MPAN
else:
    core = mpan_str[:13]  # Already core MPAN
```

### MPAN Format Support

The system now correctly handles:
- ✅ Full 21-digit MPAN: `00 801 0840 1405566778899`
- ✅ Core 13-digit MPAN: `1405566778899`
- ✅ Simple 2-digit ID: `14`
- ✅ Spaces and dashes: `00800999932 1405566778899`

## Related Documentation

- `PROJECT_CONFIGURATION.md` - GCP project settings
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - BigQuery table schemas
- `.github/copilot-instructions.md` - AI coding agent guide
- `bess_auto_trigger.gs` - Apps Script source code
- `dno_lookup_python.py` - Python source code ⚠️ CRITICAL
- `mpan_generator_validator.py` - MPAN generation/validation ⚠️ CRITICAL
- `duos_cost_calculator.py` - DUoS cost calculator
- `profile_clustering_features.py` - Clustering features extraction
- `MPAN_DUOS_QUICKSTART.md` - Quick reference guide
- `mpan_parser.py` - **NEW**: MPAN validation
- `llfc_tariff_loader.py` - **NEW**: LLFC tariff mapping
- `mpan_to_rates.py` - **NEW**: Complete pipeline

---

**Maintainer**: George Major (george@upowerenergy.uk)  
**Project**: GB Power Market JJ  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
