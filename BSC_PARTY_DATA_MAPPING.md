# BSC Party Data Mapping - BigQuery Data Availability

**Generated**: December 20, 2025
**Purpose**: Maps BSC party roles to available BigQuery operational data

---

## 📊 Data Availability Summary

| Party Role | Role Description | BigQuery Data Sources | Data Quality |
|-----------|------------------|----------------------|--------------|
| **BP** | BSC Party (Trading) | ✅ BOALF, BOD, DISBSAD | Excellent (700 parties) |
| **TG** | Generator | ✅ BOALF, BOD, INDGEN | Excellent (physical units) |
| **TS** | Trader (Supplier) | ✅ DISBSAD, BOALF | Good (settlement data) |
| **VP** | Virtual Lead Party | ✅ BOALF (33 battery units) | Excellent (revenue data) |
| **EN** | ECVNA | ✅ DISBSAD | Limited (3 parties) |
| **TI** | Interconnector | ⚠️ BOD only | Moderate |
| **TN** | Transmission | ⚠️ BOD only | Moderate |
| **MV** | Meter Operator | ❌ No BMRS data | N/A |
| **DSO** | Distribution Operator | ❌ No BMRS data | N/A |
| **AV/VT** | Aggregator/Trader | ⚠️ BOALF (limited) | Moderate |

---

## 🗂️ BigQuery Table Schemas & Usage

### 1. bmrs_boalf_complete (Balancing Acceptances WITH PRICES)
**Best for**: Revenue analysis, VLP tracking, battery arbitrage
**Columns**: `bmUnit`, `acceptancePrice`, `acceptanceVolume`, `acceptanceType`, `validation_flag`
**Coverage**: 2022-2025, ~3.1M valid acceptances
**Sample Query**:
```sql
SELECT bmUnit, COUNT(*) as acceptances,
       AVG(acceptancePrice) as avg_price,
       SUM(acceptanceVolume) as total_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE validation_flag = 'Valid'
  AND acceptanceTime >= '2025-01-01'
GROUP BY bmUnit
```

**Key Findings (2025 Battery Units)**:
- **2__FBPGM001**: 5,538 acceptances, 25,747 MWh offers, £71.36/MWh avg
- **2__FBPGM002**: 4,503 acceptances, 31,517 MWh offers, £71.60/MWh avg
- **2__FFSEN007**: 1,589 acceptances, £73.07/MWh avg (Gresham House?)
- **33 total battery units** tracked via FLEX/BESS naming patterns

---

### 2. bmrs_bod (Bid-Offer Data Submissions)
**Best for**: Market participation analysis, unit activity levels
**Columns**: `bmUnit`, `offer`, `bid`, `pairId`, `settlementDate`
**Coverage**: 2022-2025, 404M+ rows
**Critical**: Column is `bmUnit` NOT `bmUnitId`!

**Sample Query**:
```sql
SELECT bmUnit, COUNT(*) as submission_count,
       AVG(offer) as avg_offer,
       AVG(bid) as avg_bid
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND (offer > 0 OR bid > 0)
GROUP BY bmUnit
```

**Top 30-Day Active Units**:
- **T_HUMR-1**: 17,296 submissions (highest activity)
- **E_RHEI-1**: 12,812 submissions
- **V__JZENO001**: 10,438 submissions (VLP unit)

---

### 3. bmrs_disbsad (System Imbalance Settlement)
**Best for**: Financial settlement analysis, party-level costs/revenue
**Columns**: `partyId`, `volume`, `cost`, `soFlag`, `storFlag`
**Coverage**: 2022-2025, 511k records
**Note**: Uses **partyId** (not bmUnit) - matches BSC signatory Party_ID field

**Sample Query**:
```sql
SELECT partyId, COUNT(*) as settlement_records,
       SUM(volume) as total_volume_mwh,
       SUM(cost) as total_cost_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
WHERE settlementDate >= '2025-01-01'
GROUP BY partyId
```

**Top Settlement Parties (All-Time)**:
- **Danske Commodities A/S**: 46,065 records
- **UKPR**: 43,007 records (750,489 MWh)
- **Habitat Energy**: 33,262 records (415,012 MWh)
- **Octopus Energy**: 22,393 records

---

### 4. bmrs_indgen_iris (Real-Time Generation)
**Best for**: System-level generation monitoring
**Columns**: `generation`, `settlementDate`, `settlementPeriod` (NO bmUnit!)
**Coverage**: Last 51 days, 2M+ records
**Limitation**: Aggregate only - no unit-level breakdown

**Aggregate Stats**:
- Average generation: 8,295 MW
- Maximum generation: 51,311 MW
- Data freshness: Oct 30 - Dec 22, 2025

---

## 🔋 Virtual Lead Party (VP) Analysis

### Battery Storage Units - 2025 Activity

| BM Unit | Acceptances | Offer MWh | Bid MWh | Avg Price | Last Active |
|---------|------------|-----------|---------|-----------|-------------|
| 2__FBPGM001 | 5,538 | 25,747 | 25,428 | £71.36 | Dec 20 |
| 2__FBPGM002 | 4,503 | 31,517 | 25,826 | £71.60 | Dec 18 |
| 2__FFSEN007 | 1,589 | 4,179 | 5,318 | £73.07 | Dec 18 |
| 2__BFLEX004 | 1,326 | 4,919 | 7,129 | £34.78 | Dec 18 |
| 2__GFLEX008 | 537 | 2,324 | 2,563 | £38.11 | Dec 18 |

**Revenue Model**: Buy cheap (bid) → sell expensive (offer)
**Data Source**: `bmrs_boalf_complete` table with validation_flag='Valid'

---

## 🎯 Analysis Sheet Dropdown Integration

### ANALYSIS_DROPDOWNS.gs Implementation

**Location**: Google Sheets Apps Script
**Status**: ✅ Ready for deployment (120 lines)

**4 Dropdowns Created**:
1. **Time Period (B4)**: LIVE DATA, TODAY, WEEK, MONTH, YEAR, ALL
2. **From Date (D4)**: Last 90 days + next 7 days (98 options)
3. **To Date (F4)**: Same date range as From Date
4. **Party Role (H4)**: 14 BSC roles (BP, TG, TS, VP, DSO, etc.)

**Deployment Steps**:
```
1. Open Google Sheets → Extensions → Apps Script
2. Copy ANALYSIS_DROPDOWNS.gs content
3. Save and Run → addAnalysisDropdowns()
4. Refresh sheet to see dropdowns in row 4
```

---

## 📋 BSC Signatories Upload Summary

### bsc_signatories_full Table

**Rows**: 700 parties (362 skipped due to CSV formatting)
**Columns**: Party_Name, Party_ID, Party_Address, Party_Roles, Allocated_OSM, Telephone, Email
**Source**: `/home/george/imac-sync/ELEXON-BSC-Signatories_20251220162340.csv`

**Party Role Distribution**:
- **694 BP** (BSC Party - trading license)
- **3 EN** (ECVNA - energy imbalance)
- **2 Other** (Elexon system roles)
- **1 TG** (Generator - explicit role)

**Multi-Role Examples**:
- **BPGAS**: BP,TI,TN,TG,EN,MV,TS,VP (8 roles)
- **DANSKE**: BP,TI,TN,EN,MV,VP (6 roles)
- **DRAX**: BP,TG,EN (3 roles)
- **COPPER** (Octopus): BP,TS,VP,VT,EN,MV (6 roles)

---

## 🚀 Query Patterns for Party Analysis

### 1. Find All Data for Specific Party
```sql
-- Step 1: Get party details
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bsc_signatories_full`
WHERE Party_Name = 'Octopus Energy';

-- Step 2: Find settlement data (uses Party_Name directly)
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
WHERE partyId = 'Octopus Energy'
  AND settlementDate >= '2025-01-01';

-- Step 3: Find BM unit activity (requires BM unit name)
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE bmUnit LIKE '%COPPER%'  -- Match party naming pattern
  AND validation_flag = 'Valid';
```

### 2. Battery Revenue Analysis (VP Role)
```sql
SELECT
    bmUnit,
    SUM(CASE WHEN acceptanceType = 'OFFER' THEN acceptanceVolume * acceptancePrice ELSE 0 END) as offer_revenue_gbp,
    SUM(CASE WHEN acceptanceType = 'BID' THEN acceptanceVolume * acceptancePrice ELSE 0 END) as bid_cost_gbp,
    SUM(CASE WHEN acceptanceType = 'OFFER' THEN acceptanceVolume * acceptancePrice ELSE 0 END) -
    SUM(CASE WHEN acceptanceType = 'BID' THEN acceptanceVolume * acceptancePrice ELSE 0 END) as net_revenue_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE bmUnit LIKE '%FLEX%' OR bmUnit LIKE '%BESS%' OR bmUnit LIKE '%FBPGM%'
  AND validation_flag = 'Valid'
  AND acceptanceTime >= '2025-01-01'
GROUP BY bmUnit
ORDER BY net_revenue_gbp DESC;
```

### 3. Generator Activity by Party Role (TG)
```sql
-- Find generators in BOD
SELECT bmUnit, COUNT(*) as submission_count,
       AVG(offer) as avg_offer_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE bmUnit LIKE 'T_%'  -- Traditional generators (T_ prefix)
  AND settlementDate >= '2025-01-01'
GROUP BY bmUnit
ORDER BY submission_count DESC;
```

---

## 🛠️ Data Gaps & Limitations

### Missing Data Sources
- **DSO/DNO Data**: No BMRS integration (separate DUoS system)
- **Meter Operator (MV)**: No direct BMRS data
- **INDGEN Unit-Level**: Only aggregate generation available
- **IRIS COSTS**: Not currently configured (no real-time imbalance prices)

### Schema Inconsistencies
- BOD uses `bmUnit` column
- INDGEN has NO unit identifier
- DISBSAD uses `partyId` (matches Party_Name not Party_ID)
- BOALF uses `bmUnit` (most consistent)

### Naming Conventions
- Traditional generators: `T_XXXX-1` (e.g., T_HUMR-1)
- Embedded generation: `E_XXXX-1` (e.g., E_RHEI-1)
- Virtual units: `V__XXXXX` (e.g., V__JZENO001)
- Battery/Flex: `2__XFLEX00X`, `2__FBPGM00X`, `2__FFSEN00X`

---

## 📌 Next Steps

1. **Deploy ANALYSIS_DROPDOWNS.gs** to Google Sheets
2. **Create party-BM unit mapping table** (automate name matching)
3. **Add IRIS real-time cost data** (currently missing from pipeline)
4. **Build dashboard queries** using party role filters
5. **Document DSO/DNO data sources** (separate from BMRS)

---

## 📚 Related Documentation

- `PROJECT_CONFIGURATION.md` - BigQuery setup and credentials
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Table schemas and gotchas
- `APPS_SCRIPT_GUIDE.md` - Google Sheets Apps Script deployment
- `ANALYSIS_DROPDOWNS.gs` - Party role dropdown implementation

---

**Last Updated**: December 20, 2025
**Maintainer**: George Major (george@upowerenergy.uk)
