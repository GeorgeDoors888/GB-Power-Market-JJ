# DNO/MPAN/DUoS Lookup System - Complete Code Reference

**Last Updated**: December 22, 2025
**Purpose**: Document all code related to UK electricity distribution network operator (DNO) lookups, MPAN parsing, and DUoS rate retrieval for battery energy storage systems (BESS)

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [MPAN Parsing System](#mpan-parsing-system)
4. [DNO Lookup Methods](#dno-lookup-methods)
5. [DUoS Rate Lookup](#duos-rate-lookup)
6. [Google Sheets Integration](#google-sheets-integration)
7. [BigQuery Tables](#bigquery-tables)
8. [Webhook & Automation](#webhook--automation)
9. [Data Ingestion Scripts](#data-ingestion-scripts)
10. [File Index](#file-index)

---

## 🎯 System Overview

### Purpose
Battery energy storage systems (BESS) need to know their DNO area and DUoS (Distribution Use of System) charges to calculate:
- **Red Band** charges (peak periods 16:00-19:30 weekdays) - Highest cost
- **Amber Band** charges (shoulder periods 08:00-16:00, 19:30-22:00) - Medium cost
- **Green Band** charges (off-peak overnight & weekends) - Lowest cost

### Business Value
- **Arbitrage Optimization**: Charge during Green periods, discharge during Red
- **Cost Avoidance**: Minimize expensive Red period consumption
- **Revenue Maximization**: Target high-price balancing opportunities minus DUoS costs

### Data Flow
```
Postcode/MPAN Input
    ↓
[Postcode → Coordinates] (postcodes.io API)
    ↓
[Coordinates → DNO ID] (Regional mapping or BigQuery boundaries)
    ↓
[MPAN Parsing] (Distributor ID extraction from 13-digit core)
    ↓
[DNO Lookup] (BigQuery neso_dno_reference table)
    ↓
[DUoS Rate Lookup] (BigQuery gb_power.duos_unit_rates + duos_time_bands)
    ↓
Google Sheets Update (BESS sheet A4:H13)
```

---

## 🔧 Core Components

### 1. Main Python Script: `dno_lookup_python.py`

**Location**: `/home/george/GB-Power-Market-JJ/dno_lookup_python.py`
**Lines**: 618 total
**Purpose**: Complete DNO lookup pipeline from postcode/MPAN to rates display

**Key Functions**:

```python
lookup_postcode(postcode: str) → (lat, lng)
# Calls postcodes.io API to get coordinates
# Returns: (latitude, longitude) tuple

lookup_dno_by_coordinates(lat: float, lng: float) → mpan_id
# Maps UK coordinates to DNO MPAN ID (10-23)
# Uses regional boundary approximations
# Returns: MPAN distributor ID (10-23)

parse_mpan_input(input_str: str) → (mpan_id, mpan_data, use_advanced)
# ⚠️ CRITICAL: Must use extract_core_from_full_mpan() for full MPAN
# Supports:
#   - Full 21-digit: "00 801 0840 1405566778899" → ID 14
#   - Core 13-digit: "1405566778899" → ID 14
#   - Simple 2-digit: "14" → ID 14
# Common trap: Extracting from TOP LINE (08) instead of CORE (14)

lookup_dno_by_mpan(mpan_id: int) → dict
# Queries BigQuery neso_dno_reference table
# Returns: {dno_key, dno_name, market_participant_id, gsp_group_id, ...}

get_duos_rates(dno_key: str, voltage_level: str, llfc: str = None) → dict
# Queries gb_power.duos_unit_rates + duos_time_bands
# Returns: {
#   'Red': {'rate': 4.837, 'schedule': ['16:00-19:30']},
#   'Amber': {'rate': 0.457, 'schedule': ['08:00-16:00', '19:30-22:00']},
#   'Green': {'rate': 0.038, 'schedule': ['00:00-08:00', 'All Weekend']}
# }
```

**Configuration**:
```python
SHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'  # BESS sheet
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_UK = "uk_energy_prod"  # DNO reference data (US region)
DATASET_GB = "gb_power"        # DUoS rates (EU region)
POSTCODE_API = "https://api.postcodes.io/postcodes/"
```

**Critical Import** (Lines 16-22):
```python
# ⚠️ DO NOT CHANGE: Must import from mpan_generator_validator
# Context: Full MPAN has distributor ID in CORE (14) not top line (08)
# Fixed: 2025-11-22 - Was pointing to non-existent mpan_parser module
from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup
MPAN_PARSER_AVAILABLE = True
```

**Usage**:
```bash
# Read from BESS sheet (A6 postcode, B6 MPAN, A9 voltage)
python3 dno_lookup_python.py

# Direct MPAN lookup
python3 dno_lookup_python.py 14 HV

# Full MPAN parsing
python3 dno_lookup_python.py "1405566778899" LV
```

**Output Location**: BESS sheet cells C6:H13

---

### 2. MPAN Parser: `mpan_generator_validator.py`

**Location**: `/home/george/GB-Power-Market-JJ/mpan_generator_validator.py`
**Lines**: 230 total
**Purpose**: Generate and validate MPAN core numbers with mod-11 checksum

**Key Functions**:

```python
mpan_check_digit(first_12_digits: str) → int
# Calculates check digit using prime weights: [3,5,7,13,17,19,23,29,31,37,41,43]
# Algorithm: (sum of digit×prime) mod 11 mod 10
# Example: "140556677889" → check digit 9 → full core "1405566778899"

is_valid_mpan_core(mpan_core_13: str) → bool
# Validates 13-digit MPAN core checksum
# Returns: True if last digit matches calculated check digit

generate_valid_mpan_core(dno_id: str = None) → str
# Generates random valid 13-digit MPAN core
# Args: dno_id (10-23) or None for random DNO
# Returns: Valid core with correct checksum

extract_core_from_full_mpan(full_mpan: str) → str
# Extracts 13-digit core from 21-digit full MPAN
# Example: "00 801 0840 1405566778899" → "1405566778899"

mpan_core_lookup(core: str) → dict
# Returns: {
#   'distributor_id': '14',
#   'dno_key': 'NGED-WM',
#   'dno_name': 'National Grid (West Midlands)',
#   'valid_checksum': True
# }
```

**DNO Mapping** (Lines 13-25):
```python
DNO_MAP = {
    "10": "UK Power Networks (Eastern)",
    "11": "National Grid (East Midlands)",
    "12": "UK Power Networks (London)",
    "13": "SP Energy Networks (Manweb)",
    "14": "National Grid (West Midlands)",
    "15": "Northern Powergrid (North East)",
    "16": "Electricity North West",
    "17": "SSE (Scottish Hydro)",
    "18": "SP Energy Networks (Southern Scotland)",
    "19": "UK Power Networks (South East)",
    "20": "SSE (Southern Electric)",
    "21": "National Grid (South Wales)",
    "22": "National Grid (South Western)",
    "23": "Northern Powergrid (Yorkshire)",
}
```

**MPAN Structure**:
```
Full MPAN (21 digits): SS CCC MTLLLL CCCCCCCCCCCCD
                       ↓  ↓   ↓  ↓    ↓
                       PC MTC LF LLFC Core (13 digits)

Core MPAN (13 digits): DD MMMMMMMMMM D
                       ↓  ↓          ↓
                       DNO Meter ID  Check digit

Where:
- PC (2 digits): Profile Class (00-08)
- MTC (3 digits): Meter Timeswitch Code
- LLFC (4 digits): Line Loss Factor Class (voltage/tariff indicator)
- DNO (2 digits): Distributor ID (10-23) ⚠️ THIS IS THE KEY VALUE
- Meter ID (10 digits): Unique meter identifier
- Check digit (1 digit): Mod-11 checksum
```

**Common Error**:
```python
# ❌ WRONG - Extracts from top line (Profile Class)
mpan_id = int(full_mpan[:2])  # Gets "00" not "14"

# ✅ CORRECT - Extracts from core
core = extract_core_from_full_mpan(full_mpan)  # Gets "1405566778899"
mpan_id = int(core[:2])  # Gets "14" ✅
```

---

### 3. Apps Script: `bess_dno_lookup.gs`

**Location**: `/home/george/GB-Power-Market-JJ/bess_dno_lookup.gs`
**Lines**: 312 total
**Purpose**: Google Sheets menu integration for DNO lookup

**Menu Items**:
```javascript
🔌 DNO Lookup
├── 🔄 Refresh DNO Data      → refreshDNOData()
├── 📍 Lookup by Postcode    → lookupByPostcode()
├── 🆔 Lookup by MPAN ID     → lookupByMPAN()
└── ℹ️ Instructions         → showInstructions()
```

**Key Functions**:

```javascript
onOpen()
// Adds DNO Lookup menu when spreadsheet opens

refreshDNOData()
// Main function - reads A6 (postcode) or B6 (MPAN), triggers lookup
// Priority: Postcode first, then MPAN

lookupByPostcode()
// Calls postcodes.io API for coordinates
// Shows alert: "Postcode lookup requires additional data, use MPAN instead"
// Note: Full postcode → GSP mapping not yet implemented

lookupByMPAN()
// Queries BigQuery via Vercel proxy
// SQL: SELECT * FROM neso_dno_reference WHERE mpan_distributor_id = ?
// Populates: C6:H6 with DNO details
```

**Configuration** (Lines 12-14):
```javascript
const BIGQUERY_PROJECT = "inner-cinema-476211-u9";
const BIGQUERY_DATASET = "uk_energy_prod";
const PROXY_URL = "https://gb-power-market-jj.vercel.app/api/proxy-v2";
```

**Note**: Direct BigQuery queries from Apps Script have authentication issues. System now uses Python script via webhook or manual execution.

---

### 4. Auto-Trigger: `bess_auto_trigger.gs`

**Location**: `/home/george/GB-Power-Market-JJ/bess_auto_trigger.gs`
**Lines**: 252 total
**Purpose**: Automatic DNO lookup on cell edit

**Installation**:
1. Copy to Apps Script editor
2. Click clock icon (Triggers)
3. Add trigger: `onEdit` → From spreadsheet → On edit
4. Save

**How It Works**:
```javascript
function onEdit(e) {
  // Runs automatically when any cell edited
  // Check if edit was in A6 (postcode) or B6 (MPAN)
  if (row === 6 && (col === 1 || col === 2)) {
    // Show loading indicator
    sheet.getRange('A4:H4').setValue('🔄 Looking up DNO...');

    // Trigger lookup via webhook or direct API
    triggerDnoLookup(postcode, mpanId, voltage);
  }
}

function triggerDnoLookup(postcode, mpanId, voltage) {
  // Option 1: Call postcodes.io API directly
  const postcodeResponse = UrlFetchApp.fetch(
    `https://api.postcodes.io/postcodes/${postcodeClean}`
  );

  // Option 2: Call Python webhook server
  UrlFetchApp.fetch('http://localhost:5001/trigger-dno-lookup', {
    method: 'post',
    payload: JSON.stringify({postcode, mpanId, voltage})
  });
}
```

**Current Status**: Auto-trigger created but webhook server needs to be running for full automation. Manual button preferred for reliability.

---

## 🔍 MPAN Parsing System

### Files
1. `mpan_generator_validator.py` - Core parser (✅ Working)
2. `mpan_parser.py` - Legacy parser (deprecated)
3. `mpan_to_rates.py` - Complete pipeline
4. `mpan_voltage_detector.py` - Voltage level detection
5. `test_mpan_parsing.py` - Unit tests

### Complete Pipeline: `mpan_to_rates.py`

**Location**: `/home/george/GB-Power-Market-JJ/mpan_to_rates.py`
**Lines**: 176 total

**Class**: `MPANRatesLookup`

**Usage**:
```python
from mpan_to_rates import MPANRatesLookup

lookup = MPANRatesLookup()

# Full MPAN with LLFC (line loss factor class)
result = lookup.lookup("00 801 0840 1405566778899", voltage="HV")

# Prints:
# ✅ Valid MPAN
#    DNO: National Grid (West Midlands) (NGED-WM)
#    Distributor ID: 14
#    Voltage: HV
#    LLFC: 0840
# 💰 DUoS Rates (via LLFC):
#    Red: 1.764 p/kWh
#    Amber: 0.457 p/kWh
#    Green: 0.038 p/kWh
```

**Methods**:
```python
lookup(mpan_string: str, voltage: str = None) → dict
# Complete MPAN → rates lookup
# Returns: {
#   'mpan': {...},        # Parsed MPAN data
#   'rates': {...},       # R/A/G rates with time bands
#   'summary': "..."      # Formatted text summary
# }

_fallback_rates(dno_key: str, voltage: str) → dict
# When LLFC not available, use average rates for DNO/voltage

_format_summary(mpan_data: dict, rates_data: dict) → str
# Human-readable summary text
```

---

## 🗺️ DNO Lookup Methods

### Method 1: Postcode → Coordinates → DNO

**Function**: `lookup_postcode()` in `dno_lookup_python.py`

**Steps**:
1. Call postcodes.io API: `https://api.postcodes.io/postcodes/{postcode}`
2. Extract latitude/longitude from response
3. Map coordinates to DNO using regional boundaries
4. Query BigQuery for DNO details

**Regional Mapping** (Lines 73-102 in `dno_lookup_python.py`):
```python
regional_guess = {
    # Scotland
    (56.0, 60.0, -7.0, -1.0): 17,  # SSE-SHEPD (North Scotland)
    (55.0, 56.0, -5.0, -2.0): 18,  # SP-Distribution (South Scotland)

    # North England
    (54.0, 55.5, -3.5, -1.0): 15,  # NPg-NE (North East)
    (53.0, 54.5, -2.5, -0.5): 23,  # NPg-Y (Yorkshire)
    (53.0, 54.0, -3.5, -2.0): 16,  # ENWL (North West)

    # Midlands
    (52.0, 53.5, -3.0, -0.5): 11,  # NGED-EM (East Midlands)
    (52.0, 53.0, -3.0, -1.5): 14,  # NGED-WM (West Midlands)

    # London & South East
    (51.3, 51.7, -0.5, 0.3): 12,   # UKPN-LPN (London)
    (50.8, 51.8, -0.5, 1.5): 19,   # UKPN-SPN (South Eastern)

    # South West & Wales
    (51.0, 52.5, -5.5, -2.5): 21,  # NGED-SWales (South Wales)
    (50.0, 51.5, -6.0, -2.0): 22,  # NGED-SW (South Western)
}
```

**Limitations**:
- Regional boundaries are approximations (rectangular lat/lng boxes)
- For precise lookup, would need actual DNO boundary polygons
- Some border areas may map to wrong DNO

**Alternative**: Use BigQuery `neso_dno_boundaries` table (not yet implemented)

---

### Method 2: MPAN → DNO (Direct)

**Function**: `lookup_dno_by_mpan()` in `dno_lookup_python.py`

**Steps**:
1. Parse MPAN to extract distributor ID (first 2 digits of 13-digit core)
2. Query BigQuery: `SELECT * FROM neso_dno_reference WHERE mpan_distributor_id = ?`
3. Return DNO details

**Example**:
```python
mpan_id = 14
dno = lookup_dno_by_mpan(mpan_id)
# Returns:
# {
#   'mpan_distributor_id': 14,
#   'dno_key': 'NGED-WM',
#   'dno_name': 'National Grid Electricity Distribution – West Midlands',
#   'dno_short_code': 'WMID',
#   'market_participant_id': 'MIDE',
#   'gsp_group_id': 'E',
#   'gsp_group_name': 'West Midlands'
# }
```

**Advantages**:
- ✅ 100% accurate (MPAN definitively identifies DNO)
- ✅ No API calls needed (just BigQuery)
- ✅ Works for any valid MPAN

**Disadvantages**:
- ⚠️ Requires knowing MPAN (not always available for new sites)
- ⚠️ Must parse correctly (use `mpan_generator_validator.py`)

---

### Method 3: Postcode Exact Lookup (Future)

**Not Yet Implemented** - Would require:
1. Ofgem postcode → MPAN mapping database
2. Or NESO GSP Group → Postcode mapping
3. Or DNO boundary polygons in BigQuery

**Potential Sources**:
- Ofgem Address Database
- National Grid ESO Postcode Lookup
- OpenStreetMap with DNO boundary overlay

---

## 💰 DUoS Rate Lookup

### Function: `get_duos_rates()` in `dno_lookup_python.py`

**Purpose**: Retrieve Red/Amber/Green rates for a specific DNO and voltage level

**Signature**:
```python
get_duos_rates(
    dno_key: str,      # e.g., "NGED-WM"
    voltage_level: str, # "LV", "HV", or "EHV"
    llfc: str = None   # Optional LLFC code for tariff-specific rates
) → dict
```

**Returns**:
```python
{
    'Red': {
        'rate': 4.837,  # p/kWh
        'schedule': ['16:00-19:30 weekdays']
    },
    'Amber': {
        'rate': 0.457,
        'schedule': ['08:00-16:00 weekdays', '19:30-22:00 weekdays']
    },
    'Green': {
        'rate': 0.038,
        'schedule': ['00:00-08:00 weekdays', 'All Weekend']
    }
}
```

**BigQuery Queries**:

1. **Get Rates**:
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
ORDER BY time_band_name
```

2. **Get Time Bands**:
```sql
SELECT
    time_band_name,
    day_type,
    start_time,
    end_time
FROM `inner-cinema-476211-u9.gb_power.duos_time_bands`
WHERE dno_key = 'NGED-WM'
ORDER BY day_type DESC, start_time
```

**LLFC Enhancement**:
If LLFC code provided (e.g., "0840"), adds filter:
```sql
AND tariff_code LIKE '%0840%'
```

This retrieves tariff-specific rates instead of generic DNO-wide averages.

---

### DUoS Cost Calculator: `duos_cost_calculator.py`

**Location**: `/home/george/GB-Power-Market-JJ/duos_cost_calculator.py`
**Lines**: 286 total
**Purpose**: Calculate DUoS costs for half-hourly consumption profiles

**Key Functions**:

```python
duos_band_for_hh(ts: pd.Timestamp) → str
# Assigns 'red', 'amber', or 'green' band to timestamp
# Uses configurable time windows:
#   red_windows = ((16, 19.5),)          # 16:00-19:30
#   amber_windows = ((8, 16), (19.5, 22)) # 08:00-16:00, 19:30-22:00
#   weekend_is_green = True

calculate_duos_costs(df_hh: pd.DataFrame, tariff: DuosTariff) → pd.DataFrame
# Processes HH profile (timestamp, kwh) and applies DUoS rates
# Returns df with columns:
#   - band: 'red'/'amber'/'green'
#   - unit_rate: £/kWh
#   - duos_unit_cost: £
#   - duos_fixed_cap_cost: £ (daily charges / 48)
#   - duos_total_cost: £
```

**Data Structure**:
```python
@dataclass
class DuosTariff:
    dno_id: str
    tariff_name: str
    voltage_level: str
    red_rate: float      # £/kWh
    amber_rate: float
    green_rate: float
    fixed_p_per_day: float         # pence/day
    capacity_p_per_kva_per_day: float  # pence/kVA/day
    reactive_rate: float = 0.0     # £/kVArh (optional)
```

**Usage Example**:
```python
import pandas as pd
from duos_cost_calculator import calculate_duos_costs, DuosTariff

# Define tariff (e.g., UKPN London HV)
tariff = DuosTariff(
    dno_id="UKPN-LPN",
    tariff_name="HV Import",
    voltage_level="HV",
    red_rate=0.04837,    # £/kWh = 4.837 p/kWh
    amber_rate=0.00457,
    green_rate=0.00038,
    fixed_p_per_day=150.0,  # £1.50/day in pence
    capacity_p_per_kva_per_day=2.5
)

# Load HH profile
df = pd.DataFrame({
    'timestamp': pd.date_range('2025-01-01', periods=48, freq='30min'),
    'kwh': [100, 150, 200, ...]  # 48 HH periods
})

# Calculate costs
df_with_costs = calculate_duos_costs(
    df_hh=df,
    tariff=tariff,
    kva_capacity=500.0  # 500 kVA agreed capacity
)

# Analyze
total_cost = df_with_costs['duos_total_cost'].sum()
red_cost = df_with_costs[df_with_costs['band']=='red']['duos_total_cost'].sum()
```

---

## 📊 Google Sheets Integration

### BESS Sheet Layout

**Sheet ID**: `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`
**Sheet Name**: `BESS`

**Input Cells**:
- **A6**: Postcode (e.g., "LS1 2TW")
- **B6**: MPAN ID (10-23) or full MPAN core (13 digits)
- **A9**: Voltage level dropdown ("LV (<1kV)", "HV (1-20kV)", "EHV (>20kV)")

**Output Cells (DNO Details)**:
- **C6**: DNO Key (e.g., "NGED-WM")
- **D6**: DNO Name
- **E6**: DNO Short Code
- **F6**: Market Participant ID
- **G6**: GSP Group ID
- **H6**: GSP Group Name

**Output Cells (DUoS Rates)**:
- **A9**: Voltage level
- **B9**: Red rate (p/kWh)
- **C9**: Amber rate
- **D9**: Green rate

**Output Cells (Time Schedules)**:
- **A10-D12**: Weekday time bands for Red/Amber/Green
- **A13**: Weekend note ("All Weekend = Green")

### Trigger Button

**Location**: BESS sheet cell (TBD - add drawing with assigned script)
**Function**: `manualRefreshDno()` in `bess_auto_trigger.gs`
**Action**: Calls webhook server or shows manual command dialog

**Button Code**:
```javascript
function manualRefreshDno() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const postcode = sheet.getRange('A6').getValue();
  const mpanId = sheet.getRange('B6').getValue();
  const voltage = sheet.getRange('A9').getValue();

  // Option 1: Show command to run
  const message = `Run this command:\n\npython3 dno_lookup_python.py`;
  SpreadsheetApp.getUi().alert('DNO Lookup', message, SpreadsheetApp.getUi().ButtonSet.OK);

  // Option 2: Call webhook (requires server running)
  // UrlFetchApp.fetch('http://localhost:5001/trigger-dno-lookup', {...});
}
```

---

## 🗄️ BigQuery Tables

### Table 1: `neso_dno_reference`

**Project**: `inner-cinema-476211-u9`
**Dataset**: `uk_energy_prod`
**Location**: US
**Rows**: 14 (one per DNO)

**Schema**:
```sql
CREATE TABLE uk_energy_prod.neso_dno_reference (
    mpan_distributor_id INT64,      -- 10-23
    dno_key STRING,                  -- e.g., "NGED-WM"
    dno_name STRING,                 -- Full name
    dno_short_code STRING,           -- e.g., "WMID"
    market_participant_id STRING,    -- e.g., "MIDE"
    gsp_group_id STRING,             -- e.g., "E"
    gsp_group_name STRING,           -- e.g., "West Midlands"
    license_area STRING,
    company_name STRING,
    contact_email STRING,
    website_url STRING
);
```

**Example Row**:
```sql
SELECT * FROM uk_energy_prod.neso_dno_reference WHERE mpan_distributor_id = 14;

-- Returns:
-- mpan_distributor_id: 14
-- dno_key: NGED-WM
-- dno_name: National Grid Electricity Distribution – West Midlands (WMID)
-- dno_short_code: WMID
-- market_participant_id: MIDE
-- gsp_group_id: E
-- gsp_group_name: West Midlands
```

**Source**: `ingest_all_dno_duos_tariffs.py` (DNO_LICENSE_AREAS constant)

---

### Table 2: `gb_power.duos_unit_rates`

**Project**: `inner-cinema-476211-u9`
**Dataset**: `gb_power`
**Location**: EU
**Rows**: ~500 (14 DNOs × 3 voltages × ~12 tariff variations)

**Schema**:
```sql
CREATE TABLE gb_power.duos_unit_rates (
    dno_key STRING,                  -- e.g., "NGED-WM"
    voltage_level STRING,            -- "LV", "HV", "EHV"
    tariff_code STRING,              -- Optional LLFC code
    time_band_name STRING,           -- "Red", "Amber", "Green"
    unit_rate_p_kwh FLOAT64,         -- Rate in pence/kWh
    fixed_charge_p_mpan_day FLOAT64, -- Fixed charge pence/MPAN/day
    capacity_charge_p_kva_day FLOAT64, -- Capacity pence/kVA/day
    reactive_charge_p_kvarh FLOAT64, -- Reactive power charge
    effective_from DATE,             -- Tariff start date
    effective_to DATE,               -- Tariff end date (null if current)
    tariff_year STRING               -- e.g., "2025-26"
);
```

**Example Query**:
```sql
SELECT
    time_band_name,
    unit_rate_p_kwh,
    effective_from
FROM `inner-cinema-476211-u9.gb_power.duos_unit_rates`
WHERE dno_key = 'UKPN-EPN'
  AND voltage_level = 'HV'
  AND effective_from <= CURRENT_DATE()
  AND (effective_to IS NULL OR effective_to >= CURRENT_DATE())
ORDER BY time_band_name;

-- Returns:
-- Amber | 0.457 | 2025-04-01
-- Green | 0.038 | 2025-04-01
-- Red   | 4.837 | 2025-04-01
```

**Source**: `ingest_all_dno_duos_tariffs.py` (PLACEHOLDER_RATES - needs updating with real DNO tariff documents)

---

### Table 3: `gb_power.duos_time_bands`

**Project**: `inner-cinema-476211-u9`
**Dataset**: `gb_power`
**Location**: EU
**Rows**: ~200 (14 DNOs × ~14 time periods)

**Schema**:
```sql
CREATE TABLE gb_power.duos_time_bands (
    dno_key STRING,           -- e.g., "NGED-WM"
    time_band_name STRING,    -- "Red", "Amber", "Green"
    day_type STRING,          -- "Weekday", "Weekend"
    start_time TIME,          -- HH:MM:SS
    end_time TIME,
    season STRING,            -- "Winter", "Summer", "All-year"
    start_month INT64,        -- 1-12
    end_month INT64,
    description STRING
);
```

**Example Query**:
```sql
SELECT
    time_band_name,
    day_type,
    start_time,
    end_time
FROM `inner-cinema-476211-u9.gb_power.duos_time_bands`
WHERE dno_key = 'UKPN-SPN'
  AND day_type = 'Weekday'
ORDER BY start_time;

-- Returns:
-- Green | Weekday | 00:00:00 | 07:00:00
-- Amber | Weekday | 07:00:00 | 16:00:00
-- Red   | Weekday | 16:00:00 | 19:30:00
-- Amber | Weekday | 19:30:00 | 22:00:00
-- Green | Weekday | 22:00:00 | 23:59:59
```

**Source**: `ingest_all_dno_duos_tariffs.py` (TIME_BAND_DEFINITIONS)

---

### Table 4: `neso_dno_boundaries` (Optional)

**Status**: ⚠️ Not yet created
**Purpose**: Polygon boundaries for precise postcode → DNO mapping

**Proposed Schema**:
```sql
CREATE TABLE uk_energy_prod.neso_dno_boundaries (
    dno_key STRING,
    mpan_distributor_id INT64,
    boundary_geom GEOGRAPHY,  -- Polygon
    min_lat FLOAT64,
    max_lat FLOAT64,
    min_lng FLOAT64,
    max_lng FLOAT64
);
```

**Usage**:
```sql
-- Find DNO by point
SELECT dno_key, mpan_distributor_id
FROM uk_energy_prod.neso_dno_boundaries
WHERE ST_CONTAINS(boundary_geom, ST_GEOGPOINT(-1.5437, 53.8008))
LIMIT 1;
```

**Data Source Options**:
- Ofgem License Area boundaries (GeoJSON)
- National Grid ESO DNO boundaries
- OpenStreetMap DNO region polygons

---

## 🔗 Webhook & Automation

### Webhook Server: `dno_webhook_server.py`

**Location**: `/home/george/GB-Power-Market-JJ/dno_webhook_server.py`
**Lines**: 195 total
**Purpose**: Flask server that Apps Script can call to trigger Python DNO lookup

**Endpoints**:

#### 1. `/trigger-dno-lookup` (POST)

**Payload**:
```json
{
  "postcode": "LS1 2TW",  // Optional
  "mpan_id": 23,          // Optional
  "voltage": "HV"         // Optional
}
```

**Response**:
```json
{
  "status": "success",
  "stdout": "✅ DNO lookup complete...",
  "stderr": "",
  "returncode": 0
}
```

**Action**: Executes `python3 dno_lookup_python.py [mpan_id] [voltage]`

#### 2. `/generate-hh-profile` (POST)

**Payload**:
```json
{
  "min_kw": 500,
  "avg_kw": 1500,
  "max_kw": 2500,
  "days": 365
}
```

**Purpose**: Generate synthetic half-hourly consumption profiles for testing

---

### Running the Webhook Server

**Start server**:
```bash
cd /home/george/GB-Power-Market-JJ
python3 dno_webhook_server.py

# Output:
# * Running on http://127.0.0.1:5001
```

**Expose via ngrok** (for remote Apps Script access):
```bash
ngrok http 5001

# Get public URL: https://abc123.ngrok.io
# Update Apps Script webhook URL to: https://abc123.ngrok.io/trigger-dno-lookup
```

**Systemd service** (production deployment):
```bash
sudo nano /etc/systemd/system/dno-webhook.service
```

```ini
[Unit]
Description=DNO Lookup Webhook Server
After=network.target

[Service]
Type=simple
User=george
WorkingDirectory=/home/george/GB-Power-Market-JJ
Environment="GOOGLE_APPLICATION_CREDENTIALS=/home/george/.config/google-cloud/bigquery-credentials.json"
ExecStart=/usr/bin/python3 /home/george/GB-Power-Market-JJ/dno_webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable dno-webhook
sudo systemctl start dno-webhook
sudo systemctl status dno-webhook
```

---

## 📥 Data Ingestion Scripts

### 1. `ingest_all_dno_duos_tariffs.py`

**Location**: `/home/george/GB-Power-Market-JJ/ingest_all_dno_duos_tariffs.py`
**Lines**: 296 total
**Purpose**: Populate BigQuery with DUoS rates for all 14 DNOs

**What It Does**:
1. Defines 14 DNO license areas (lines 16-30)
2. Creates time band definitions (Red/Amber/Green schedules)
3. Populates `gb_power.duos_unit_rates` table
4. Populates `gb_power.duos_time_bands` table

**Usage**:
```bash
python3 ingest_all_dno_duos_tariffs.py

# Output:
# ✅ Created table: gb_power.duos_unit_rates
# ✅ Created table: gb_power.duos_time_bands
# 📊 Inserted 420 unit rate rows
# 📊 Inserted 196 time band rows
```

**⚠️ Important Note**: Currently uses PLACEHOLDER_RATES (lines 78-95). Should be updated with official DNO tariff documents from:
- UK Power Networks: [Charges Page](https://www.ukpowernetworks.co.uk/connections/charging-and-payment/use-of-system-charges)
- National Grid: [DUoS Statements](https://www.nationalgrid.co.uk/distribution-charges)
- SSE: [Network Charges](https://www.ssen.co.uk/connections/charges/)
- SP Energy Networks: [Tariffs](https://www.spenergynetworks.co.uk/pages/charges.aspx)
- Northern Powergrid: [Charges](https://www.northernpowergrid.com/charges-and-payments)
- Electricity North West: [DUoS Tariffs](https://www.enwl.co.uk/charges/)

---

### 2. `check_dno_coverage.py`

**Location**: `/home/george/GB-Power-Market-JJ/check_dno_coverage.py`
**Purpose**: Verify all 14 DNOs have complete data in BigQuery

**Usage**:
```bash
python3 check_dno_coverage.py

# Output:
# ✅ UKPN-EPN: 3 rates, 14 time bands
# ✅ NGED-EM: 3 rates, 14 time bands
# ✅ UKPN-LPN: 3 rates, 14 time bands
# ...
# 🎯 Coverage: 14/14 DNOs complete
```

---

### 3. `create_duos_sp_mapping_view.sql`

**Location**: `/home/george/GB-Power-Market-JJ/create_duos_sp_mapping_view.sql`
**Purpose**: Create BigQuery view linking DUoS rates to settlement periods

**View**: `gb_power.duos_sp_rates_view`

**Example Query**:
```sql
SELECT * FROM `inner-cinema-476211-u9.gb_power.duos_sp_rates_view`
WHERE dno_key = 'UKPN-LPN'
  AND voltage_level = 'HV'
  AND settlement_period = 36  -- 17:30-18:00 (Red period)
LIMIT 1;

-- Returns:
-- dno_key: UKPN-LPN
-- voltage_level: HV
-- settlement_period: 36
-- time_band: Red
-- rate_p_kwh: 4.837
-- start_time: 17:30
-- end_time: 18:00
```

---

## 📁 File Index

### Python Scripts (Core Functionality)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `dno_lookup_python.py` | 618 | Main DNO lookup pipeline | ✅ Working |
| `mpan_generator_validator.py` | 230 | MPAN parsing & validation | ✅ Working |
| `mpan_to_rates.py` | 176 | Complete MPAN → rates pipeline | ✅ Working |
| `duos_cost_calculator.py` | 286 | HH profile DUoS cost calculation | ✅ Working |
| `ingest_all_dno_duos_tariffs.py` | 296 | Populate BigQuery tables | ✅ Working |
| `dno_webhook_server.py` | 195 | Flask webhook for Apps Script | ✅ Created, needs deployment |
| `mpan_voltage_detector.py` | ~150 | Detect voltage from LLFC | 🔧 Development |
| `mpan_detail_extractor.py` | ~100 | Extract all MPAN components | 🔧 Development |

### Google Apps Script Files

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `bess_dno_lookup.gs` | 312 | DNO lookup menu integration | ✅ Working |
| `bess_auto_trigger.gs` | 252 | Auto-trigger on cell edit | ✅ Created, needs trigger setup |
| `bess_webapp_api.gs` | ~200 | Web app API endpoints | 🔧 Development |

### Test & Utility Scripts

| File | Purpose | Status |
|------|---------|--------|
| `test_mpan_parsing.py` | MPAN parser unit tests | ✅ Working |
| `test_mpan_details.py` | MPAN detail extraction tests | ✅ Working |
| `check_dno_coverage.py` | Verify DNO data completeness | ✅ Working |
| `read_actual_mpan.py` | Read MPAN from BESS sheet | ✅ Working |
| `parse_actual_mpan.py` | Parse sheet MPAN and display | ✅ Working |
| `verify_mpan_display.py` | Verify MPAN parsing display | ✅ Working |

### Data & Configuration Files

| File | Purpose | Status |
|------|---------|--------|
| `create_duos_sp_mapping_view.sql` | BigQuery view creation | ✅ Working |
| `GB_Energy_Dashboard_FullPack/schemas/btm_mpan_schema.json` | MPAN data schema | 📄 Reference |

### Documentation

| File | Purpose | Status |
|------|---------|--------|
| `DNO_MPAN_DUOS_LOOKUP_SYSTEM.md` (this file) | Complete system documentation | ✅ Complete |
| `.github/copilot-instructions.md` | AI agent instructions (includes DNO section) | ✅ Updated |

### Legacy/Deprecated Files

| File | Status | Notes |
|------|--------|-------|
| `mpan_parser.py` | ⚠️ Deprecated | Use `mpan_generator_validator.py` instead |
| `chatgpt_files/dno_lookup_python.py` | 📄 Archive | Old version |
| `chatgpt_files/bess_dno_lookup.gs` | 📄 Archive | Old version |
| `bess-apps-script/bess_dno_lookup.gs` | 📄 Archive | Old version |

---

## 🔍 Common Issues & Solutions

### Issue 1: Wrong Distributor ID Extracted

**Symptom**: MPAN "00 801 0840 1405566778899" returns DNO ID 00 or 08 instead of 14

**Root Cause**: Parsing top line instead of core MPAN

**Solution**:
```python
# ❌ WRONG
mpan_id = int(full_mpan[:2])  # Gets "00" from Profile Class

# ✅ CORRECT
from mpan_generator_validator import extract_core_from_full_mpan
core = extract_core_from_full_mpan(full_mpan)  # Gets "1405566778899"
mpan_id = int(core[:2])  # Gets "14" ✅
```

**Fixed in**: `dno_lookup_python.py` lines 16-22 (import from correct module)

---

### Issue 2: No Rates Found for DNO/Voltage

**Symptom**: Query returns 0 rows from `duos_unit_rates`

**Possible Causes**:
1. DNO key mismatch (e.g., "UKPN-Eastern" vs "UKPN-EPN")
2. Voltage level mismatch (e.g., "High Voltage" vs "HV")
3. No data ingested for this DNO/voltage combination
4. LLFC filter too specific

**Solution**:
```bash
# Check what DNO keys exist
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
df = client.query('SELECT DISTINCT dno_key FROM gb_power.duos_unit_rates').to_dataframe()
print(df)
"

# Re-ingest data if missing
python3 ingest_all_dno_duos_tariffs.py
```

---

### Issue 3: Apps Script Authorization Error

**Symptom**: "Exception: Authorization is required to perform that action"

**Solution**:
1. Go to Apps Script editor
2. Click Run (play button)
3. Review permissions dialog
4. Click "Advanced" → "Go to [project]" → "Allow"
5. Test menu item again

---

### Issue 4: Postcode Lookup Returns Wrong DNO

**Symptom**: Postcode near DNO boundary maps to wrong area

**Root Cause**: Regional approximations use rectangular lat/lng boxes, not actual boundary polygons

**Solution**:
- Use MPAN lookup instead (100% accurate)
- Or implement proper boundary polygons in BigQuery (future enhancement)

---

### Issue 5: Webhook Server Not Responding

**Symptom**: Apps Script call times out or returns 500 error

**Checks**:
```bash
# Is server running?
ps aux | grep dno_webhook_server

# Check logs
tail -f /var/log/dno-webhook.log  # If using systemd

# Test endpoint directly
curl -X POST http://localhost:5001/trigger-dno-lookup \
  -H "Content-Type: application/json" \
  -d '{"mpan_id": 14, "voltage": "HV"}'
```

**Solutions**:
- Start server: `python3 dno_webhook_server.py &`
- Check firewall: `sudo ufw allow 5001`
- Use ngrok for external access: `ngrok http 5001`

---

## 🚀 Quick Start Guide

### For New Users

1. **Get MPAN or Postcode**:
   - Open BESS sheet
   - Enter postcode in A6 OR MPAN in B6
   - Select voltage in A9

2. **Run Lookup**:
   ```bash
   cd /home/george/GB-Power-Market-JJ
   python3 dno_lookup_python.py
   ```

3. **View Results**:
   - DNO details appear in C6:H6
   - DUoS rates appear in B9:D9
   - Time schedules appear in A10:D13

### For Developers

1. **Test MPAN Parsing**:
   ```bash
   python3 test_mpan_parsing.py
   ```

2. **Test DNO Lookup**:
   ```bash
   python3 dno_lookup_python.py 14 HV
   # Should return NGED West Midlands, Red: 1.764 p/kWh
   ```

3. **Test Complete Pipeline**:
   ```python
   from mpan_to_rates import MPANRatesLookup
   lookup = MPANRatesLookup()
   result = lookup.lookup("1405566778899", "HV")
   print(result['summary'])
   ```

4. **Deploy Webhook**:
   ```bash
   # Option 1: Manual
   python3 dno_webhook_server.py &

   # Option 2: Systemd service
   sudo systemctl start dno-webhook
   ```

---

## 📚 Additional Resources

### Official DNO Documentation

- **Ofgem**: [Distribution Network Operators](https://www.ofgem.gov.uk/energy-policy-and-regulation/industry-licensing/licences-and-licence-conditions/electricity-supply-licence-conditions)
- **NESO (formerly National Grid ESO)**: [DNO Contact List](https://www.nationalgrideso.com/industry-information/codes/distribution-code-and-grid-code/dno-contact-list)
- **Elexon**: [MPAN Guidance](https://www.elexon.co.uk/documents/training-guidance/bsc-guidance-notes/meter-administration-guidance/)

### DUoS Tariff Documents (2025-26)

| DNO | Tariff Document |
|-----|----------------|
| UK Power Networks | [Statement of Use of System Charges](https://www.ukpowernetworks.co.uk/connections/charging-and-payment/use-of-system-charges) |
| National Grid (West Midlands) | [DUoS Charging Statement](https://www.nationalgrid.co.uk/distribution-charges) |
| SSE | [Network Charges](https://www.ssen.co.uk/connections/charges/) |
| SP Energy Networks | [Charging Statements](https://www.spenergynetworks.co.uk/pages/charges.aspx) |
| Northern Powergrid | [Use of System Charges](https://www.northernpowergrid.com/charges-and-payments) |
| Electricity North West | [DUoS Tariff Schedule](https://www.enwl.co.uk/charges/) |

### API Documentation

- **postcodes.io**: [API Docs](https://postcodes.io/docs)
- **BigQuery API**: [Python Client Docs](https://cloud.google.com/python/docs/reference/bigquery/latest)
- **Google Sheets API**: [Apps Script Reference](https://developers.google.com/apps-script/reference/spreadsheet)

---

## ✅ Testing Checklist

- [ ] MPAN parsing (13-digit core → distributor ID)
- [ ] MPAN validation (checksum verification)
- [ ] Full MPAN parsing (21-digit with LLFC extraction)
- [ ] Postcode → coordinates (postcodes.io API)
- [ ] Coordinates → DNO (regional mapping)
- [ ] MPAN → DNO (BigQuery lookup)
- [ ] DNO → DUoS rates (Red/Amber/Green)
- [ ] DUoS rates → time schedules (weekday/weekend)
- [ ] LLFC → specific tariff rates
- [ ] HH profile → DUoS cost calculation
- [ ] Google Sheets read (A6, B6, A9)
- [ ] Google Sheets write (C6:H13)
- [ ] Apps Script menu integration
- [ ] Apps Script button trigger
- [ ] Webhook endpoint (POST request)
- [ ] Webhook → Python script execution
- [ ] BigQuery table completeness (14 DNOs, 3 voltages)

---

## 📞 Support

**Issues**: Check `.github/copilot-instructions.md` for troubleshooting
**Updates**: See `CHANGELOG.md` for version history
**Questions**: george@upowerenergy.uk

---

*Documentation Version: 1.0*
*Created: December 22, 2025*
*Maintainer: George Major*
