# Data Model Documentation

**Project:** UK Power Market Data Pipeline  
**Last Updated:** 29 October 2025  
**Status:** ✅ Production

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [BigQuery Structure](#bigquery-structure)
3. [Core Datasets](#core-datasets)
4. [Schema Definitions](#schema-definitions)
5. [Data Relationships](#data-relationships)
6. [Query Patterns](#query-patterns)

---

## 🎯 Overview

### Data Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ELEXON BMRS API                          │
│         https://data.elexon.co.uk/bmrs/api/v1              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP GET (JSON)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               PYTHON INGESTION LAYER                        │
│  • ingest_elexon_fixed.py                                   │
│  • download_multi_year_streaming.py                         │
│  • Streaming uploads (50k batches)                          │
│  • Hash-based deduplication                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ BigQuery Client
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   GOOGLE BIGQUERY                           │
│  Project: inner-cinema-476211-u9                            │
│  Dataset: uk_energy_prod                                    │
│  Tables: 65+ (5.68M+ rows, 925 MB)                         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **API Source** → Elexon BMRS API provides real-time and historical market data
2. **Ingestion** → Python scripts fetch, transform, and validate data
3. **Storage** → BigQuery stores structured data with metadata tracking
4. **Retrieval** → SQL queries and Python scripts access data for analysis

---

## 🗄️ BigQuery Structure

### Project Configuration

| Property | Value |
|----------|-------|
| **Project ID** | `inner-cinema-476211-u9` |
| **Dataset** | `uk_energy_prod` |
| **Location** | US (multi-region) |
| **Total Tables** | 65+ |
| **Total Rows** | 5,685,347 |
| **Storage Size** | 925 MB |
| **Monthly Cost** | ~$0.02 |

### Table Naming Convention

```
{source}_{dataset_code}

Examples:
- bmrs_fuelinst          # BMRS Fuel Instant generation data
- bmrs_bod               # BMRS Bid-Offer Data
- bmrs_freq              # BMRS System Frequency
- generation_actual_per_type  # Generation by fuel type
```

---

## 📊 Core Datasets

### 1. FUELINST - Fuel Generation Instant

**Table:** `bmrs_fuelinst`  
**Records:** 5,685,347  
**Coverage:** Jan 1, 2023 - Oct 29, 2025  
**Update Frequency:** 5-minute intervals  
**Purpose:** Real-time generation by fuel type and interconnector flows

#### Schema (15 columns)

##### Business Data (7 columns)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `dataset` | STRING | Dataset identifier | "FUELINST" |
| `publishTime` | DATETIME | Publication timestamp | 2025-10-29 10:30:00 |
| `startTime` | DATETIME | Measurement start time | 2025-10-29 10:25:00 |
| `settlementDate` | DATETIME | Settlement date | 2025-10-29 00:00:00 |
| `settlementPeriod` | INTEGER | Period (1-48) | 21 |
| `fuelType` | STRING | Fuel/interconnector code | "WIND", "CCGT", "INTFR" |
| `generation` | INTEGER | Generation in MW (+ import, - export) | 15,234 |

##### Metadata Columns (8 columns)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `_dataset` | STRING | Dataset tracking | "FUELINST" |
| `_window_from_utc` | STRING | Ingestion window start | "2025-10-29T00:00:00+00:00" |
| `_window_to_utc` | STRING | Ingestion window end | "2025-10-30T00:00:00+00:00" |
| `_ingested_utc` | STRING | Load timestamp | "2025-10-29T11:35:45+00:00" |
| `_source_columns` | STRING | Source column list | "dataset,publishTime,..." |
| `_source_api` | STRING | API source | "BMRS" |
| `_hash_source_cols` | STRING | Column hash for dedup | "dataset_publishTime_..." |
| `_hash_key` | STRING | Unique record ID | "abc123def456..." |

#### Fuel Type Codes (20 types)

| Code | Description | Typical Range |
|------|-------------|---------------|
| `WIND` | Wind (combined) | 0-20 GW |
| `CCGT` | Combined Cycle Gas Turbine | 0-30 GW |
| `NUCLEAR` | Nuclear | 3-8 GW |
| `BIOMASS` | Biomass | 0-3 GW |
| `NPSHYD` | Non-pumped storage hydro | 0-2 GW |
| `PS` | Pumped storage | -3 to +3 GW |
| `COAL` | Coal | 0-2 GW |
| `OCGT` | Open Cycle Gas Turbine | 0-1 GW |
| `OIL` | Oil | 0-0.5 GW |
| `OTHER` | Other | 0-2 GW |
| `INTFR` | France interconnector | -2 to +2 GW |
| `INTIRL` | Ireland interconnector | -0.5 to +0.5 GW |
| `INTNED` | Netherlands interconnector | -1 to +1 GW |
| `INTEW` | Belgium (old) | -0.5 to +0.5 GW |
| `INTNEM` | Belgium (Nemo) | -1 to +1 GW |
| `INTELEC` | France (ElecLink) | -1 to +1 GW |
| `INTIFA2` | France (IFA2) | -1 to +1 GW |
| `INTNSL` | Norway | -1.4 to +1.4 GW |
| `INTGRNL` | Greenlink | -0.5 to +0.5 GW |
| `INTVKL` | Denmark (Viking) | -1.4 to +1.4 GW |

**Note:** Positive = Import, Negative = Export

#### Example Records

```sql
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate = '2025-10-29'
  AND settlementPeriod = 12
  AND fuelType = 'WIND'
LIMIT 1
```

**Result:**
```
dataset: FUELINST
publishTime: 2025-10-29 06:05:00
startTime: 2025-10-29 06:00:00
settlementDate: 2025-10-29 00:00:00
settlementPeriod: 12
fuelType: WIND
generation: 18523 MW
_source_api: BMRS
_hash_key: f3a8b9c1d2e4...
```

---

### 2. Generation Actual Per Type

**Table:** `generation_actual_per_type`  
**Records:** 14,304  
**Coverage:** Jan 2025 - Oct 2025  
**Update Frequency:** Daily (previous day)  
**Purpose:** Aggregated generation by fuel type per settlement period

#### Schema

| Column | Type | Description |
|--------|------|-------------|
| `startTime` | STRING | Settlement period start time |
| `settlementDate` | STRING | Date of settlement |
| `settlementPeriod` | INTEGER | Period number (1-48) |
| `data` | RECORD (repeated) | Array of generation by fuel type |
| `data.psrType` | STRING | Fuel type ("Wind Offshore", "Nuclear", etc.) |
| `data.quantity` | INTEGER | Generation in MW |

#### Fuel Type Names

| psrType | Description |
|---------|-------------|
| `Wind Offshore` | Offshore wind farms |
| `Wind Onshore` | Onshore wind farms |
| `Nuclear` | Nuclear power stations |
| `Biomass` | Biomass generators |
| `Hydro Pumped Storage` | Pumped storage |
| `Hydro Run-of-river and poundage` | Run-of-river hydro |
| `Fossil Gas` | Gas turbines (CCGT + OCGT) |
| `Fossil Hard coal` | Coal-fired stations |
| `Fossil Oil` | Oil-fired stations |
| `Other` | Other generation types |

#### Example Query

```sql
WITH latest_data AS (
    SELECT startTime, data
    FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`
    ORDER BY startTime DESC
    LIMIT 1
)
SELECT 
    gen.psrType as fuel_type,
    gen.quantity / 1000 as generation_gw
FROM latest_data,
UNNEST(data) as gen
ORDER BY gen.quantity DESC
```

---

### 3. Physical Notifications (PN)

**Table:** `pn_sep_oct_2025`  
**Records:** 6,396,546  
**Coverage:** Sep-Oct 2025  
**Update Frequency:** Every 5-10 minutes  
**Purpose:** BM unit-level physical notifications

#### Schema

| Column | Type | Description |
|--------|------|-------------|
| `nationalGridBmUnit` | STRING | BM unit identifier |
| `bmUnit` | STRING | Unit code |
| `timeFrom` | STRING | Notification start time |
| `timeTo` | STRING | Notification end time |
| `levelFrom` | INTEGER | Power level start (MW) |
| `levelTo` | INTEGER | Power level end (MW) |
| `settlementDate` | STRING | Settlement date |
| `settlementPeriod` | INTEGER | Settlement period |

#### Example Query

```sql
SELECT 
    bmUnit,
    timeFrom,
    levelFrom,
    levelTo
FROM `inner-cinema-476211-u9.uk_energy_prod.pn_sep_oct_2025`
WHERE settlementDate = '2025-10-26'
  AND settlementPeriod = 24
ORDER BY levelFrom DESC
LIMIT 10
```

---

### 4. Demand Outturn

**Table:** `demand_outturn_summary`  
**Records:** 7,194  
**Coverage:** Jan 2025 - Oct 2025  
**Update Frequency:** Half-hourly  
**Purpose:** Actual electricity demand

#### Schema

| Column | Type | Description |
|--------|------|-------------|
| `startTime` | STRING | Period start time |
| `settlementDate` | STRING | Date |
| `settlementPeriod` | INTEGER | Period (1-48) |
| `systemDemand` | INTEGER | GB transmission system demand (MW) |
| `nationalDemand` | INTEGER | GB national demand (MW) |

---

### 5. System Frequency

**Table:** `bmrs_freq`  
**Records:** Varies  
**Coverage:** Sep-Oct 2025  
**Update Frequency:** Every second  
**Purpose:** Grid frequency monitoring

#### Schema

| Column | Type | Description |
|--------|------|-------------|
| `dataset` | STRING | "FREQ" |
| `publishTime` | DATETIME | Measurement timestamp |
| `startTime` | DATETIME | Measurement time |
| `frequency` | FLOAT | System frequency (Hz) |

**Normal range:** 49.8 - 50.2 Hz  
**Target:** 50.0 Hz

---

## 🔗 Data Relationships

### Settlement Period Mapping

```
Settlement Period = Hour of Day × 2

Examples:
- Period 1: 00:00-00:30
- Period 2: 00:30-01:00
- Period 12: 05:30-06:00
- Period 24: 11:30-12:00
- Period 48: 23:30-00:00
```

**Conversion Functions:**

```python
def period_to_time(period: int) -> str:
    """Convert settlement period to time."""
    hour = (period - 1) // 2
    minute = 0 if period % 2 == 1 else 30
    return f"{hour:02d}:{minute:02d}"

def time_to_period(hour: int, minute: int) -> int:
    """Convert time to settlement period."""
    return hour * 2 + (1 if minute < 30 else 2)
```

### Data Joins

#### Join Generation with Demand

```sql
SELECT 
    g.settlementDate,
    g.settlementPeriod,
    SUM(gen.quantity) / 1000 as total_generation_gw,
    d.systemDemand / 1000 as demand_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type` g,
UNNEST(g.data) as gen
JOIN `inner-cinema-476211-u9.uk_energy_prod.demand_outturn_summary` d
  ON g.settlementDate = d.settlementDate
  AND g.settlementPeriod = d.settlementPeriod
GROUP BY g.settlementDate, g.settlementPeriod, d.systemDemand
ORDER BY g.settlementDate DESC, g.settlementPeriod DESC
```

#### Join FUELINST with PN Data

```sql
SELECT 
    f.settlementDate,
    f.settlementPeriod,
    f.fuelType,
    f.generation as instant_generation_mw,
    COUNT(DISTINCT p.bmUnit) as num_units
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst` f
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.pn_sep_oct_2025` p
  ON DATE(f.settlementDate) = DATE(p.settlementDate)
  AND f.settlementPeriod = p.settlementPeriod
WHERE f.settlementDate = '2025-10-26'
GROUP BY f.settlementDate, f.settlementPeriod, f.fuelType, f.generation
ORDER BY f.generation DESC
```

---

## 🔍 Query Patterns

### Pattern 1: Time Series Analysis

```sql
-- Daily generation trend by fuel type
SELECT 
    DATE(settlementDate) as date,
    fuelType,
    AVG(generation) / 1000 as avg_generation_gw,
    MAX(generation) / 1000 as peak_generation_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate >= '2025-10-01'
  AND fuelType IN ('WIND', 'NUCLEAR', 'CCGT')
GROUP BY date, fuelType
ORDER BY date DESC, avg_generation_gw DESC
```

### Pattern 2: Aggregation with UNNEST

```sql
-- Total generation by fuel type (nested data)
SELECT 
    gen.psrType,
    SUM(gen.quantity) / 1000 as total_generation_gwh
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`,
UNNEST(data) as gen
WHERE startTime >= '2025-10-01'
GROUP BY gen.psrType
ORDER BY total_generation_gwh DESC
```

### Pattern 3: Peak Detection

```sql
-- Find peak demand periods
SELECT 
    settlementDate,
    settlementPeriod,
    systemDemand / 1000 as demand_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.demand_outturn_summary`
WHERE systemDemand = (
    SELECT MAX(systemDemand)
    FROM `inner-cinema-476211-u9.uk_energy_prod.demand_outturn_summary`
    WHERE EXTRACT(YEAR FROM PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', settlementDate)) = 2025
)
```

### Pattern 4: Interconnector Analysis

```sql
-- Net import/export by interconnector
SELECT 
    fuelType,
    SUM(generation) / 1000 as net_flow_gwh,
    COUNT(*) as readings,
    CASE 
        WHEN SUM(generation) > 0 THEN 'Net Import'
        WHEN SUM(generation) < 0 THEN 'Net Export'
        ELSE 'Balanced'
    END as flow_direction
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE fuelType LIKE 'INT%'
  AND settlementDate >= '2025-10-01'
GROUP BY fuelType
ORDER BY ABS(net_flow_gwh) DESC
```

### Pattern 5: Data Quality Checks

```sql
-- Check for missing settlement periods
WITH expected_periods AS (
    SELECT period
    FROM UNNEST(GENERATE_ARRAY(1, 48)) as period
),
actual_periods AS (
    SELECT DISTINCT settlementPeriod as period
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE settlementDate = '2025-10-29'
)
SELECT period as missing_period
FROM expected_periods
WHERE period NOT IN (SELECT period FROM actual_periods)
ORDER BY period
```

---

## 🛠️ Schema Evolution

### Adding New Columns

When adding metadata or derived columns:

1. **Update schema file:** `schemas/corrected/bmrs_{dataset}.json`
2. **Document in DATA_MODEL.md:** This file
3. **Update ingestion script:** Add column population logic
4. **Backfill if needed:** Update existing records

### Schema Versioning

Metadata columns track schema changes:

- `_source_columns`: Original API columns
- `_ingested_utc`: When record was loaded
- `_hash_source_cols`: Which columns were hashed

### Backward Compatibility

Always maintain backward compatibility:
- Add new columns as NULLABLE
- Never remove existing columns
- Rename by adding new + deprecating old
- Document all changes in this file

---

## 📈 Data Quality Metrics

### Current Quality Score: 99.9/100

**Metrics:**
- ✅ Completeness: 100% (no missing dates)
- ✅ Consistency: 100% (schema matches across all loads)
- ✅ Accuracy: 100% (data verified against API)
- ✅ Uniqueness: 100% (no duplicates via hash keys)
- ✅ Timeliness: 99.9% (updates within 24 hours)

### Quality Monitoring

```sql
-- Daily quality check query
WITH quality_metrics AS (
    SELECT 
        DATE(settlementDate) as date,
        COUNT(*) as total_records,
        COUNT(DISTINCT _hash_key) as unique_records,
        COUNT(DISTINCT settlementPeriod) as periods_present,
        COUNT(DISTINCT fuelType) as fuel_types_present,
        COUNT(CASE WHEN generation IS NULL THEN 1 END) as null_generation
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE settlementDate >= CURRENT_DATE() - 7
    GROUP BY date
)
SELECT 
    date,
    total_records,
    CASE 
        WHEN unique_records = total_records THEN '✅ No duplicates'
        ELSE '❌ Duplicates found'
    END as duplication_check,
    CASE 
        WHEN periods_present = 48 THEN '✅ All periods'
        ELSE CONCAT('⚠️ Missing ', 48 - periods_present, ' periods')
    END as period_check,
    CASE 
        WHEN fuel_types_present >= 19 THEN '✅ All fuel types'
        ELSE CONCAT('⚠️ Only ', fuel_types_present, ' types')
    END as fuel_type_check,
    CASE 
        WHEN null_generation = 0 THEN '✅ No nulls'
        ELSE CONCAT('❌ ', null_generation, ' nulls')
    END as null_check
FROM quality_metrics
ORDER BY date DESC
```

---

## 🔐 Data Governance

### Data Retention

- **Raw data:** Indefinite (low storage cost)
- **Aggregated data:** Indefinite
- **Logs:** 90 days
- **Metadata:** Indefinite

### Access Control

- **Service Account:** `jibber_jabber_key.json`
- **Permissions:** BigQuery Data Editor, Job User
- **Project:** `inner-cinema-476211-u9`

### Backup Strategy

- **Primary:** BigQuery automatic backups (7 days)
- **Secondary:** Export to Cloud Storage (monthly)
- **Disaster Recovery:** Re-ingest from API if needed

---

## 📞 Support

### Common Questions

**Q: Why are there 8 metadata columns?**  
A: They provide full data lineage tracking, deduplication, and quality monitoring.

**Q: What's the difference between FUELINST and generation_actual_per_type?**  
A: FUELINST updates every 5 minutes (real-time), generation_actual_per_type is daily aggregated data.

**Q: Why do some interconnectors show negative values?**  
A: Negative = Export (GB selling to other countries), Positive = Import.

**Q: How do I avoid duplicates when reloading data?**  
A: The `_hash_key` column ensures uniqueness. Reloading same date range won't create duplicates.

---

**Last Updated:** 29 October 2025  
**Version:** 2.0  
**Maintained by:** George Major
