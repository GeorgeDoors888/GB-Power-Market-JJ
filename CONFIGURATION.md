# ⚙️ Configuration Guide

Complete configuration reference for the BESS Dashboard system.

---

## 📋 Table of Contents

- [Environment Setup](#environment-setup)
- [Google Cloud Configuration](#google-cloud-configuration)
- [Dashboard Settings](#dashboard-settings)
- [Rate Configuration](#rate-configuration)
- [Battery Parameters](#battery-parameters)
- [Time Band Definitions](#time-band-definitions)
- [Logging Configuration](#logging-configuration)
- [Performance Tuning](#performance-tuning)

---

## 🌍 Environment Setup

### credentials.json

**Location:** Project root (`/Users/georgemajor/GB-Power-Market-JJ/credentials.json`)

**Purpose:** Service account authentication for Google Cloud APIs

**Structure:**
```json
{
  "type": "service_account",
  "project_id": "inner-cinema-476211-u9",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQ...==\n-----END PRIVATE KEY-----\n",
  "client_email": "bess-dashboard@inner-cinema-476211-u9.iam.gserviceaccount.com",
  "client_id": "1234567890",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/bess-dashboard%40inner-cinema-476211-u9.iam.gserviceaccount.com"
}
```

**Obtaining Credentials:**
1. Open GCP Console: https://console.cloud.google.com/
2. Navigate to: IAM & Admin → Service Accounts
3. Click: Create Service Account
   - Name: `bess-dashboard`
   - Description: `BESS Dashboard service account`
4. Grant Roles:
   - `BigQuery Data Viewer`
   - `BigQuery Job User`
5. Click: Keys → Add Key → Create New Key → JSON
6. Download file, rename to `credentials.json`
7. Move to project root

**Security:**
```bash
# Set restrictive permissions
chmod 600 credentials.json

# Verify not in git
git check-ignore credentials.json
# Output: credentials.json

# If not ignored, add to .gitignore
echo "credentials.json" >> .gitignore
```

**Environment Variable (Optional):**
```bash
# Add to ~/.zshrc
export GOOGLE_APPLICATION_CREDENTIALS="/Users/georgemajor/GB-Power-Market-JJ/credentials.json"

# Reload
source ~/.zshrc

# Verify
echo $GOOGLE_APPLICATION_CREDENTIALS
```

---

## ☁️ Google Cloud Configuration

### BigQuery Project

**Project ID:** `inner-cinema-476211-u9`

**Dataset:** `uk_energy_prod`

**Tables:**

#### balancing_prices
```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.balancing_prices` (
  settlement_date DATE,
  settlement_period INT64,
  system_sell_price FLOAT64,
  system_buy_price FLOAT64,
  net_imbalance_volume FLOAT64,
  created_at TIMESTAMP
)
PARTITION BY settlement_date
CLUSTER BY settlement_period
OPTIONS(
  description="Elexon BMRS balancing prices",
  partition_expiration_days=NULL
);
```

**Row Count:** ~35,000+ (growing daily)

**Partition:** By `settlement_date` (efficient date range queries)

**Cluster:** By `settlement_period` (efficient period filtering)

---

#### duos_tariff_rates
```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.duos_tariff_rates` (
  dno_code STRING,
  dno_name STRING,
  voltage_level STRING,
  time_band STRING,
  rate_p_per_kwh FLOAT64,
  effective_from DATE,
  effective_to DATE,
  source STRING,
  created_at TIMESTAMP
)
OPTIONS(
  description="DUoS tariff rates by DNO, voltage, and time band"
);
```

**Row Count:** 207 (14 DNOs × 3 voltages × 3 bands + extras)

**Update Frequency:** Annual (April)

**Voltage Levels:** LV, HV, EHV

**Time Bands:** RED, AMBER, GREEN

---

#### dno_duos_rates
```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.dno_duos_rates` (
  dno_code STRING,
  time_band STRING,
  start_hour INT64,
  end_hour INT64,
  weekday_only BOOL,
  rate_description STRING
)
OPTIONS(
  description="Time band hour ranges by DNO"
);
```

**Purpose:** Define when each time band applies (hour ranges)

---

#### neso_dno_reference
```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` (
  mpan_id STRING,
  dno_key STRING,
  dno_name STRING,
  dno_short_code STRING,
  market_participant_id STRING,
  gsp_group_id STRING,
  gsp_group_name STRING,
  region STRING,
  created_at TIMESTAMP
)
OPTIONS(
  description="NESO DNO reference data (14 distribution areas)"
);
```

**Row Count:** 14 (one per DNO)

**MPAN Range:** 10-23

---

### Google Sheets Access

**Dashboard ID:** `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`

**Worksheet:** `BESS`

**Sharing:**
1. Open Dashboard: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit
2. Click "Share" button
3. Add service account email:
   ```
   bess-dashboard@inner-cinema-476211-u9.iam.gserviceaccount.com
   ```
4. Set permission: Editor
5. Uncheck "Notify people"
6. Click "Share"

**Verification:**
```python
import gspread

gc = gspread.service_account(filename='credentials.json')
sheet = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
print(f"✅ Access granted: {sheet.title}")
```

---

## 📊 Dashboard Settings

### Cell References

#### Configuration Inputs

| Cell | Description | Type | Example | Validation |
|------|-------------|------|---------|------------|
| A6 | Postcode | String | `SW2 5UP` | UK format |
| B6 | MPAN ID | Integer | `14` | 10-23 range |
| A10 | Voltage Level | Dropdown | `LV` | LV/HV/EHV |
| B10 | DUoS RED Rate | Float | `8.50` | p/kWh |
| C10 | DUoS AMBER Rate | Float | `2.10` | p/kWh |
| D10 | DUoS GREEN Rate | Float | `0.45` | p/kWh |
| B13 | RED Time Band | String | `16:00-19:00` | HH:MM-HH:MM |
| B14 | AMBER Time Band | String | `06:00-08:00,14:00-16:00` | Comma-separated |
| B17 | Battery Min kW | Float | `500` | > 0 |
| B18 | Battery Avg kW | Float | `1500` | > Min |
| B19 | Battery Max kW | Float | `2500` | > Avg |
| B21 | PPA Price | Float | `150.00` | £/MWh |
| L6 | Analysis Period | Dropdown | `90 Days` | Predefined list |

#### Output Ranges

| Range | Description | Source | Format |
|-------|-------------|--------|--------|
| B6:H6 | DNO Details | Apps Script | Text |
| A22:C69 | HH Profile | Apps Script | Time, Band, kW |
| A90:G162 | PPA Arbitrage | Python | Month, Band, £/MWh |
| A170:F205 | Revenue Breakdown | Python | Category, Amount, % |
| A210:D245 | Visualization Stats | Python | Metric, Value |
| A250:F285 | Cost Breakdown | Python | Component, £/MWh, % |

### Data Validation Rules

#### A10: Voltage Level
```javascript
{
  "condition": {
    "type": "ONE_OF_LIST",
    "values": ["LV", "HV", "EHV"]
  },
  "strict": true,
  "showCustomUi": true
}
```

#### L6: Analysis Period
```javascript
{
  "condition": {
    "type": "ONE_OF_LIST",
    "values": [
      "30 Days",
      "90 Days",
      "6 Months",
      "1 Year",
      "2 Years (Full Analysis)"
    ]
  },
  "strict": true,
  "showCustomUi": true
}
```

#### B6: MPAN ID
```javascript
{
  "condition": {
    "type": "NUMBER_BETWEEN",
    "values": [10, 23]
  },
  "strict": true,
  "showCustomUi": true,
  "inputMessage": "Enter MPAN ID (10-23)"
}
```

---

## 💰 Rate Configuration

### Fixed Levies (2024/25)

**Update Frequency:** Annual (April)

**Source:** Ofgem, National Grid ESO

```python
# £/MWh
BSUOS_RATE = 3.40          # Balancing Services Use of System
TNUOS_RATE = 15.50         # Transmission Network Use of System
RO_LEVY = 5.20             # Renewables Obligation
FIT_LEVY = 2.85            # Feed-in Tariff
CFD_LEVY = 2.20            # Contracts for Difference
FCP_RATE = 9.00            # Feed-in Premium

# Total Fixed Levies
FIXED_LEVIES = BSUOS_RATE + TNUOS_RATE + RO_LEVY + FIT_LEVY + CFD_LEVY + FCP_RATE
# = 38.15 £/MWh
```

**Historical Rates:**
| Year | BSUoS | TNUoS | Levies | Total |
|------|-------|-------|--------|-------|
| 2022/23 | 4.10 | 12.30 | 18.50 | 34.90 |
| 2023/24 | 3.75 | 14.20 | 19.20 | 37.15 |
| 2024/25 | 3.40 | 15.50 | 19.25 | 38.15 |
| 2025/26 | 3.20* | 16.80* | 20.10* | 40.10* |

*Projected

**Configuration File:** `config/fixed_levies.json`
```json
{
  "effective_from": "2024-04-01",
  "effective_to": "2025-03-31",
  "rates_gbp_per_mwh": {
    "bsuos": 3.40,
    "tnuos": 15.50,
    "ro_levy": 5.20,
    "fit_levy": 2.85,
    "cfd_levy": 2.20,
    "fcp": 9.00
  },
  "total": 38.15,
  "source": "Ofgem Targeted Charging Review 2024/25"
}
```

---

### DUoS Rates

**Update Frequency:** Annual (April)

**Source:** DNO tariff schedules

**Configuration:** BigQuery table `duos_tariff_rates`

**Example Rates (NGED-WM LV 2024/25):**
```json
{
  "dno_code": "NGED",
  "dno_name": "National Grid Electricity Distribution - West Midlands",
  "voltage_level": "LV",
  "rates_p_per_kwh": {
    "RED": 8.50,
    "AMBER": 2.10,
    "GREEN": 0.45
  },
  "time_bands": {
    "RED": {
      "description": "Super Peak",
      "periods": [33, 34, 35, 36, 37, 38],
      "hours": "16:00-19:00",
      "weekdays_only": true
    },
    "AMBER": {
      "description": "Peak",
      "periods": [13, 14, 15, 16, 29, 30, 31, 32],
      "hours": "06:00-08:00, 14:00-16:00",
      "weekdays_only": true
    },
    "GREEN": {
      "description": "Off-Peak",
      "periods": "All other",
      "hours": "Other times + weekends",
      "weekdays_only": false
    }
  }
}
```

**Rate Ranges by Voltage:**

| Voltage | RED (p/kWh) | AMBER (p/kWh) | GREEN (p/kWh) |
|---------|-------------|---------------|---------------|
| LV | 7.50 - 9.50 | 1.80 - 2.40 | 0.35 - 0.55 |
| HV | 5.20 - 6.80 | 1.20 - 1.80 | 0.25 - 0.40 |
| EHV | 3.50 - 4.50 | 0.80 - 1.20 | 0.15 - 0.25 |

**Update Process:**
1. DNOs publish tariffs (February)
2. Effective date: April 1st
3. Update BigQuery table:
   ```sql
   UPDATE `inner-cinema-476211-u9.uk_energy_prod.duos_tariff_rates`
   SET 
     rate_p_per_kwh = NEW_RATE,
     effective_from = '2025-04-01',
     effective_to = '2026-03-31'
   WHERE dno_code = 'NGED'
     AND voltage_level = 'LV'
     AND time_band = 'RED';
   ```
4. Verify in dashboard (B10:D10)

---

### SO Payment Rates

**Update Frequency:** Quarterly

**Source:** National Grid ESO Frequency Response Market

```python
# £/MW/day (2024 Q4 average)
FFR_RATE = 50.00           # Firm Frequency Response (Primary)
DCR_RATE = 13.33           # Demand Control Response (Secondary)
DM_RATE = 9.44             # Dynamic Moderation
DR_RATE = 5.00             # Dynamic Regulation
BID_RATE = 1.67            # Balancing Mechanism bids
BOD_RATE = 1.11            # Balancing Mechanism offers
```

**Historical Rates (FFR):**
| Quarter | FFR (£/MW/day) | Change |
|---------|----------------|--------|
| 2023 Q4 | 42.50 | - |
| 2024 Q1 | 45.80 | +7.8% |
| 2024 Q2 | 48.20 | +5.2% |
| 2024 Q3 | 51.30 | +6.4% |
| 2024 Q4 | 50.00 | -2.5% |

**Configuration File:** `config/so_payments.json`
```json
{
  "effective_from": "2024-10-01",
  "effective_to": "2024-12-31",
  "rates_gbp_per_mw_per_day": {
    "ffr_primary": 50.00,
    "dcr_secondary": 13.33,
    "dm": 9.44,
    "dr": 5.00,
    "bm_bid": 1.67,
    "bm_bod": 1.11
  },
  "source": "National Grid ESO Frequency Response Market Data",
  "notes": "Rates vary by market conditions"
}
```

---

### Capacity Market

**Update Frequency:** Annual (auction results)

**Auction:** T-4 (4 years ahead)

```python
# £/kW/year
CM_RATE_2024 = 28.00       # 2024/25 delivery year
CM_RATE_2025 = 32.50       # 2025/26 (T-4 2021 auction)
CM_RATE_2026 = 41.00       # 2026/27 (T-4 2022 auction)
CM_RATE_2027 = 45.00       # 2027/28 (T-4 2023 auction)
```

**Auction Results:**
| Auction | Delivery Year | Clearing Price (£/kW) | Capacity Secured |
|---------|---------------|-----------------------|------------------|
| T-4 2020 | 2024/25 | 28.00 | 49.3 GW |
| T-4 2021 | 2025/26 | 32.50 | 50.1 GW |
| T-4 2022 | 2026/27 | 41.00 | 51.8 GW |
| T-4 2023 | 2027/28 | 45.00 | 53.2 GW |

**Configuration:**
```json
{
  "delivery_year": "2024/25",
  "clearing_price_gbp_per_kw": 28.00,
  "contract_start": "2024-10-01",
  "contract_end": "2025-09-30",
  "de_rating_factor": 0.95,
  "availability_threshold": 0.85,
  "penalty_rate_gbp_per_kw_per_hour": 0.10,
  "stress_events_per_year": 12,
  "notice_period_hours": 4
}
```

---

## 🔋 Battery Parameters

### Default Configuration

```python
BATTERY_CONFIG = {
    # Capacity
    'capacity_mwh': 2.5,              # Storage capacity (MWh)
    'usable_capacity_mwh': 2.375,     # 95% usable (5% reserve)
    
    # Power
    'power_mw': 1.0,                  # Max charge/discharge rate (MW)
    'power_factor': 1.0,              # Unity power factor
    
    # Efficiency
    'round_trip_efficiency': 0.85,    # 85% RT efficiency
    'charge_efficiency': 0.92,        # 92% charge
    'discharge_efficiency': 0.92,     # 92% discharge (0.92 × 0.92 ≈ 0.85)
    'inverter_efficiency': 0.98,      # 98% inverter
    
    # Cycling
    'cycles_per_day': 2,              # Daily cycles
    'max_cycles_lifetime': 7300,      # Warranty cycles (10 years)
    'current_cycles': 0,              # Cycle counter
    
    # Degradation
    'degradation_rate_per_year': 0.02,  # 2% capacity loss/year
    'warranty_years': 10,
    'warranty_threshold': 0.80,       # 80% capacity retained
    
    # Operating Constraints
    'min_soc': 0.05,                  # 5% min state of charge
    'max_soc': 0.95,                  # 95% max state of charge
    'max_charge_rate_mw': 1.0,
    'max_discharge_rate_mw': 1.0,
    
    # Temperature
    'operating_temp_min_c': 0,
    'operating_temp_max_c': 40,
    'optimal_temp_c': 25,
    
    # Response Times
    'response_time_ffr_ms': 500,      # 500ms for FFR
    'response_time_dcr_s': 10,        # 10s for DCR
    'ramp_rate_mw_per_s': 1.0,        # Full power in 1 second
    
    # Voltage
    'voltage_level': 'LV',            # LV/HV/EHV
    'nominal_voltage_kv': 0.4,        # 400V for LV
    
    # Location
    'postcode': 'B33 8TH',
    'mpan_id': 14,                    # NGED-WM
    'gsp_group': 14,
    
    # Cost
    'capex_gbp_per_kwh': 400,         # £400/kWh (£1M for 2.5 MWh)
    'opex_gbp_per_year': 25000,       # £25k/year O&M
    'insurance_gbp_per_year': 15000,  # £15k/year
    'land_lease_gbp_per_year': 10000, # £10k/year
}
```

### Configuration File

**Location:** `config/battery_params.json`

```json
{
  "battery_id": "BESS-001",
  "site_name": "West Midlands Battery Storage",
  "capacity": {
    "total_mwh": 2.5,
    "usable_mwh": 2.375,
    "reserve_percent": 5
  },
  "power": {
    "max_mw": 1.0,
    "power_factor": 1.0,
    "inverter_efficiency": 0.98
  },
  "efficiency": {
    "round_trip": 0.85,
    "charge": 0.92,
    "discharge": 0.92
  },
  "cycling": {
    "daily_cycles": 2,
    "warranty_cycles": 7300,
    "degradation_per_year": 0.02
  },
  "operating_constraints": {
    "min_soc": 0.05,
    "max_soc": 0.95,
    "temp_range_c": [0, 40]
  },
  "location": {
    "postcode": "B33 8TH",
    "mpan_id": 14,
    "dno": "NGED-WM",
    "voltage_level": "LV"
  },
  "financial": {
    "capex_gbp": 1000000,
    "opex_annual_gbp": 25000,
    "insurance_annual_gbp": 15000,
    "land_lease_annual_gbp": 10000
  }
}
```

### Loading Configuration

```python
import json

def load_battery_config(config_file='config/battery_params.json'):
    """Load battery configuration from JSON file."""
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config

# Usage
battery = load_battery_config()
print(f"Capacity: {battery['capacity']['total_mwh']} MWh")
print(f"Power: {battery['power']['max_mw']} MW")
print(f"Efficiency: {battery['efficiency']['round_trip'] * 100}%")
```

---

## ⏰ Time Band Definitions

### Standard Time Bands

```python
TIME_BANDS = {
    'RED': {
        'name': 'Super Peak',
        'description': 'Highest demand periods',
        'periods': [33, 34, 35, 36, 37, 38],
        'hours': '16:00-19:00',
        'duration_hours': 3,
        'weekdays_only': True,
        'typical_ssp_range': [100, 150],  # £/MWh
        'strategy': 'Discharge (Sell)',
        'color': '#d62728'  # Red
    },
    'AMBER': {
        'name': 'Peak',
        'description': 'Morning & afternoon peaks',
        'periods': [13, 14, 15, 16, 29, 30, 31, 32],
        'hours': '06:00-08:00, 14:00-16:00',
        'duration_hours': 4,
        'weekdays_only': True,
        'typical_ssp_range': [70, 100],  # £/MWh
        'strategy': 'Variable (price dependent)',
        'color': '#ff7f0e'  # Orange
    },
    'GREEN': {
        'name': 'Off-Peak',
        'description': 'Low demand periods',
        'periods': list(range(1, 13)) + list(range(17, 29)) + list(range(39, 49)),
        'hours': 'All other times',
        'duration_hours': 17,
        'weekdays_only': False,
        'typical_ssp_range': [40, 70],  # £/MWh
        'strategy': 'Charge (Buy)',
        'color': '#2ca02c'  # Green
    }
}
```

### Period to Time Mapping

```python
def period_to_time(settlement_period):
    """Convert settlement period (1-48) to time string."""
    hour = (settlement_period - 1) // 2
    minute = 30 if settlement_period % 2 == 0 else 0
    return f"{hour:02d}:{minute:02d}"

# Examples
period_to_time(1)   # '00:00'
period_to_time(2)   # '00:30'
period_to_time(35)  # '17:00'
period_to_time(48)  # '23:30'
```

### Time to Period Mapping

```python
def time_to_period(hour, minute):
    """Convert time to settlement period (1-48)."""
    if minute < 30:
        return hour * 2 + 1
    else:
        return hour * 2 + 2

# Examples
time_to_period(0, 0)    # 1
time_to_period(0, 30)   # 2
time_to_period(17, 0)   # 35
time_to_period(23, 30)  # 48
```

### Custom Time Bands

**Dashboard Cells:** B13 (RED), B14 (AMBER)

**Format:** `HH:MM-HH:MM[,HH:MM-HH:MM]`

**Examples:**
```python
# RED: Single range
"16:00-19:00"  # Periods 33-38

# AMBER: Multiple ranges
"06:00-08:00,14:00-16:00"  # Periods 13-16, 29-32

# GREEN: Implicit (everything else)
```

**Parsing Function:**
```python
def parse_time_band(band_string):
    """Parse time band string to period list."""
    periods = []
    ranges = band_string.split(',')
    
    for range_str in ranges:
        start_str, end_str = range_str.split('-')
        start_hour = int(start_str.split(':')[0])
        start_min = int(start_str.split(':')[1])
        end_hour = int(end_str.split(':')[0])
        end_min = int(end_str.split(':')[1])
        
        start_period = time_to_period(start_hour, start_min)
        end_period = time_to_period(end_hour, end_min)
        
        periods.extend(range(start_period, end_period + 1))
    
    return periods

# Usage
red_periods = parse_time_band("16:00-19:00")
print(red_periods)
# Output: [33, 34, 35, 36, 37, 38]
```

---

## 📝 Logging Configuration

### Log Directory Structure

```
logs/
├── ppa_arbitrage_20241130.log
├── bess_revenue_20241130.log
├── visualization_20241130.log
├── dashboard_update_20241130.log
└── system_20241130.log
```

### Python Logging Setup

```python
import logging
import os
from datetime import datetime

LOG_DIR = 'logs'
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logging(script_name):
    """Configure logging for a script."""
    # Create logs directory
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Log filename with date
    log_file = os.path.join(
        LOG_DIR,
        f"{script_name}_{datetime.now().strftime('%Y%m%d')}.log"
    )
    
    # Configure logging
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ]
    )
    
    logger = logging.getLogger(script_name)
    logger.info(f"{'=' * 60}")
    logger.info(f"{script_name} started")
    logger.info(f"{'=' * 60}")
    
    return logger

# Usage in script
logger = setup_logging('ppa_arbitrage')
logger.info("Connecting to BigQuery...")
logger.info(f"Retrieved {len(df):,} rows")
logger.error(f"Failed to connect: {error}")
```

### Log Rotation

```bash
#!/bin/bash
# cleanup_logs.sh

LOG_DIR="logs"
RETENTION_DAYS=7

echo "🧹 Cleaning up logs older than ${RETENTION_DAYS} days..."

find "$LOG_DIR" -name "*.log" -type f -mtime +${RETENTION_DAYS} -delete

echo "✅ Log cleanup complete"
```

**Add to cron (daily at 2 AM):**
```bash
crontab -e

# Add line:
0 2 * * * /Users/georgemajor/GB-Power-Market-JJ/cleanup_logs.sh
```

---

## ⚡ Performance Tuning

### BigQuery Optimization

```python
# Query configuration
from google.cloud import bigquery

job_config = bigquery.QueryJobConfig()

# Enable caching (reuse results within 24 hours)
job_config.use_query_cache = True

# Use legacy SQL or standard SQL
job_config.use_legacy_sql = False

# Set maximum bytes billed (safety limit)
job_config.maximum_bytes_billed = 1073741824  # 1 GB

# Set query priority
job_config.priority = bigquery.QueryPriority.INTERACTIVE  # or BATCH

# Query with config
query_job = client.query(sql, job_config=job_config)
results = query_job.result()
```

### Pandas Optimization

```python
# Read BigQuery with specific dtypes
df = pd.read_gbq(
    query,
    project_id='inner-cinema-476211-u9',
    dtype={
        'settlement_period': 'int8',  # 1-48 fits in int8
        'ssp': 'float32',  # Don't need float64 precision
    }
)

# Use categorical for repeated values
df['time_band'] = df['time_band'].astype('category')

# Memory usage
print(f"Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
```

### Sheets API Optimization

```python
# Batch updates instead of individual cells
import gspread

# ❌ BAD: 100 API calls
for i, value in enumerate(values):
    worksheet.update_cell(i+1, 1, value)

# ✅ GOOD: 1 API call
worksheet.update('A1:A100', [[v] for v in values])

# Add retry logic with exponential backoff
from gspread.exceptions import APIError
import time

def update_with_retry(worksheet, range, values, max_retries=5):
    for attempt in range(max_retries):
        try:
            worksheet.update(range, values)
            return
        except APIError as e:
            if '429' in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

---

**Next Steps:**
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [API Reference](API_REFERENCE.md) - Function documentation
- [Troubleshooting](TROUBLESHOOTING.md) - Issue resolution
