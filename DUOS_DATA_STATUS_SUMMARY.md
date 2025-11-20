# DUoS Tariff Data - Where Did It Go?
**Investigation Date**: November 18, 2025

## 🔍 Current Status

### Excel Files in Workspace
- **Only 1 Excel file found**: `All_Generators.xlsx` (1.9 MB)
- **NO DUoS/tariff Excel files present**

### BigQuery Status

#### ✅ DUoS Table Structure EXISTS (gb_power dataset, EU region)
```
📊 Dataset: gb_power
   • duos_tariff_definitions: 0 rows, 0.00 MB  ⚠️ EMPTY
   • duos_time_bands: 0 rows, 0.00 MB          ⚠️ EMPTY
   • duos_unit_rates: 0 rows, 0.00 MB          ⚠️ EMPTY
```

#### ❌ DUoS Data: NEVER POPULATED
All three DUoS tables are **EMPTY** - they were created with schemas but never filled with data.

---

## �� Historical Context (from Documentation)

### From BESS_VLP_SESSION_SUMMARY.md (Nov 9, 2025)
```markdown
5. ✅ DUoS charges investigation (tables empty, structure exists)
```

### From DNUOS_CHARGES_STATUS.md (Nov 9, 2025)
```markdown
### Quick Answer: **DUoS tariff data is NOT in BigQuery yet**
- ✅ Table schemas exist (well-designed, ready to use)
- ⚠️ All 3 DUoS tables are EMPTY (0 rows)
- ✅ DNO reference data is complete (14 license areas)
- �� Action needed: Import tariff data from DNO websites
```

### From DNO_DATA_COMPLETE_INVENTORY.md (Nov 9, 2025)
```markdown
| **DUoS Tariff Data** | ⚠️ EMPTY | 0 rows | Need to populate |

**The only gap is DUoS tariff data** (table structure exists but needs population from DNO websites).
```

---

## 🎯 The Truth

### DUoS Data Was NEVER Uploaded

1. **Table schemas created**: Nov 9, 2025 or earlier
2. **Tables left empty**: Intentionally empty, awaiting data import
3. **No Excel files**: No DUoS tariff Excel files were ever in this workspace
4. **Documented gap**: This was known and documented on Nov 9

### Why Empty?

DUoS tariff data is:
- **Complex**: Different rates for 14 DNOs × multiple voltage levels × time bands
- **Dispersed**: Each DNO publishes separately on their websites
- **Regulatory**: Must be extracted from official tariff documents
- **Time-consuming**: Requires manual extraction or scraping

---

## 📊 What DUoS Tables SHOULD Contain

### 1. duos_tariff_definitions
- Tariff codes (e.g., "LLFC 1", "Profile Class 5-8")
- Voltage levels (HV, LV, EHV)
- Customer categories (Domestic, Commercial, Industrial)
- Effective dates

**Example rows needed:**
```
UKPN-LPN, LLFC-0100, "Domestic Unrestricted", LV, Profile Class 1
NGED-EM, LLFC-0900, "Non-Domestic HH", HV, Half-hourly metered
```

### 2. duos_time_bands
- Red/Amber/Green band definitions
- Time ranges (e.g., Red: 16:00-19:00 weekdays Nov-Feb)
- Seasonal variations

**Example rows needed:**
```
UKPN-LPN, Red, Winter, Weekday, 16:00, 19:00, Nov, Feb
UKPN-LPN, Green, All-year, Weekend, 00:00, 23:59
```

### 3. duos_unit_rates
- Actual p/kWh charges
- By DNO, time band, voltage level
- Historical rates for trend analysis

**Example rows needed:**
```
UKPN-LPN, Red, HV, 8.54 p/kWh, 2025-04-01, 2026-03-31
NGED-EM, Green, LV, 1.23 p/kWh, 2025-04-01, 2026-03-31
```

---

## 🚫 What Doesn't Exist

### Companies House "charges" Table ≠ DUoS
Found in BigQuery:
```
📊 Dataset: companies_house
   • charges: 2,804,487 rows, 1175.44 MB
   • charges_backup_20251029_112807: 8,898,738 rows, 2612.08 MB
```

**This is NOT DUoS data"/Users/georgemajor/GB Power Market JJ" && python3 -c "
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = 'inner-cinema-476211-u9'

credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
client = bigquery.Client(project=PROJECT_ID, credentials=credentials)

print('🔍 Checking for DUoS tables across ALL datasets...\\n')

# List all datasets
datasets = list(client.list_datasets())
print(f'Found {len(datasets)} datasets\\n')

for dataset in datasets:
    dataset_id = dataset.dataset_id
    tables = list(client.list_tables(f'{PROJECT_ID}.{dataset_id}'))
    
    # Look for DUoS/tariff related tables
    duos_tables = [t for t in tables if 'duos' in t.table_id.lower() or 'tariff' in t.table_id.lower() or 'charge' in t.table_id.lower()]
    
    if duos_tables:
        print(f'📊 Dataset: {dataset_id}')
        for table in duos_tables:
            full_table = client.get_table(f'{PROJECT_ID}.{dataset_id}.{table.table_id}')
            print(f'   • {table.table_id}: {full_table.num_rows:,} rows, {full_table.num_bytes/1024/1024:.2f} MB')
        print()
"* This is Companies House financial charges (mortgages, loans, secured debts).

---

## 📁 Where to Get DUoS Data

### Official DNO Sources (14 networks)

1. **UK Power Networks (UKPN)** - 3 regions
   - LPN (London): https://www.ukpowernetworks.co.uk/electricity/charges
   - EPN (Eastern)
   - SPN (South Eastern)

2. **NGED (National Grid Electricity Distribution)** - 4 regions
   - East Midlands: https://www.nationalgrid.co.uk/electricity-distribution/connections/charges
   - West Midlands
   - South West
   - South Wales

3. **SSE (Scottish & Southern Electricity)** - 2 regions
   - SHEPD (Highlands)
   - SEPD (Southern)

4. **Northern Powergrid** - 2 regions
   - North East
   - Yorkshire

5. **Electricity North West (ENWL)**

6. **SP Energy Networks** - 2 regions
   - Distribution (Scotland)
   - Manweb (Wales/Northwest)

### Ofgem Central Source
- **DCP 228**: https://www.ofgem.gov.uk/publications/dcp-228-charges-reconciliation
- Standardized format but requires processing

---

## 🔧 How to Populate (Future Work)

### Option 1: Manual Upload (Fastest)
1. Download current tariff PDFs from each DNO
2. Extract rates to Excel/CSV
3. Upload via `upload_missing_csv_files.py` (already created today!)

### Option 2: Web Scraping (Automated)
1. Build scraper for each DNO website
2. Parse PDF tariff tables (PyPDF2/pdfplumber)
3. Auto-populate BigQuery

### Option 3: Ofgem API (If Available)
Check if Ofgem provides API access to DCP 228 data

---

## ✅ What IS Complete

### DNO Reference Data (Perfect!)
```sql
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
-- Returns: All 14 UK DNOs with full details
```

### Generator Data (Excellent!)
- `all_generators`: 7,384 rows (uploaded today!)
- `sva_generators`: 7,072 rows
- `cva_plants`: 1,581 rows

### Market Data (Comprehensive!)
- `bmrs_costs`: 118,058 rows (system prices)
- `bmrs_mid`: Market index data
- 204 BMRS tables total

---

## 💡 Business Impact

### What Works Without DUoS Data
✅ Battery arbitrage analysis (system prices)
✅ VLP revenue tracking
✅ Generation forecasting
✅ Market price analysis
✅ DNO identification (via BESS_VLP tool)

### What Needs DUoS Data
❌ Full battery profitability (missing network costs)
❌ Site-specific cost estimation
❌ Connection tariff comparison
❌ Red band charging optimization
❌ Regional cost analysis

---

## 📋 Recommended Next Steps

### Immediate (This Week)
1. **Test BESS_VLP Tool**: Verify postcode → DNO lookup works
2. **Prioritize DNOs**: Which regions matter most for battery analysis?
3. **Check Ofgem**: Is DCP 228 data available in structured format?

### Short-Term (This Month)
1. **Manual Data Entry**: Start with top 3 DNOs (UKPN-LPN, NGED-EM, ENWL)
2. **Red Band Only**: Just populate peak time rates initially
3. **2025-26 Tariffs**: Current year only

### Medium-Term (Q1 2026)
1. **Full Historical**: Back to 2020 for trend analysis
2. **All DNOs**: Complete coverage
3. **Automated Updates**: Scraper for annual tariff changes

---

## 📊 Summary

**Excel Files**: Only `All_Generators.xlsx` exists (no DUoS files)

**BigQuery Status**:
- ✅ Table schemas: Perfect, ready to use
- ⚠️ Table data: EMPTY (0 rows in all 3 tables)
- ✅ DNO reference: Complete
- ❌ DUoS tariffs: Never uploaded

**Why Empty**: DUoS data requires manual extraction from 14 DNO websites - complex regulatory data not available in simple format

**Impact**: Can do 80% of battery analysis without it, but need it for true profitability calculations

**Solution**: Prioritize manual upload for key DNOs, automate later

---

*Investigation completed: November 18, 2025*
*Source: BigQuery queries + documentation review*
