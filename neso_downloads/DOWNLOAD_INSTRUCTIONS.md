# NESO Data Download Instructions

Created: 28 December 2025

## Directory Structure

```
~/GB-Power-Market-JJ/neso_downloads/constraint_costs/
├── constraint_breakdown/    # Monthly Emergency Instructions costs
├── mbss/                    # Daily emergency service costs
├── annual_reports/          # Yearly NGSEA event counts
├── forecast/                # 24-month constraint cost forecast
├── modelled_costs/          # Historical NGSEA cost attribution
└── skip_rates/              # Monthly skip rate metrics
```

## ⚠️ NESO REBRAND UPDATE (December 2025)

**National Grid ESO → NESO (National Energy System Operator)**

Old domain `data.nationalgrideso.com` no longer works.  
New data portal: **https://www.neso.energy/data-portal**

## Download URLs (UPDATED)

### 1. Constraint Breakdown (Monthly CSV)
**URL**: https://www.neso.energy/data-portal/constraint-management/historic-constraint-breakdown  
**Fallback**: Search "historic constraint breakdown" on https://www.neso.energy/search-data  
**Files to download**:
- Download all monthly CSV files from Jan 2022 to Dec 2025
- Save to: `constraint_breakdown/`
- Expected: ~48 files

**How to download**:
1. Visit URL above
2. Scroll to "Data Resources" section
3. Click "Download" for each monthly file
4. Save all to `constraint_breakdown/` folder

### 2. MBSS - Mandatory Balancing Services (Daily CSV)
**URL**: https://www.neso.energy/data-portal/balancing-services/mbss  
**Fallback**: Search "MBSS" or "mandatory balancing services" on data portal  
**Files to download**:
- Daily breakdown CSV files for 2022-2025
- Save to: `mbss/`

**How to download**:
1. Visit URL above
2. Download CSV for each year or combined file
3. Save to `mbss/` folder

### 3. Annual Balancing Costs Report (PDF + Excel)
**URL**: https://www.neso.energy/document/series/balancing-services-reports  
**Fallback**: Search "balancing services annual report" on main site  
**Files to download**:
- 2022, 2023, 2024 annual reports (PDF + Excel data tables)
- Save to: `annual_reports/`

**How to download**:
1. Visit URL above
2. Find "Balancing Services Reports" for each year
3. Download Excel data tables (contains NGSEA event counts)
4. Save to `annual_reports/` folder

### 4. 24-Month Constraint Cost Forecast (CSV)
**URL**: https://www.neso.energy/data-portal/constraint-management/24-month-forecast  
**Fallback**: Search "24 month constraint cost forecast" on data portal  
**Files to download**:
- Latest forecast CSV
- Save to: `forecast/`

### 5. Modelled Constraint Costs (CSV)
**URL**: https://www.neso.energy/data-portal/constraint-management/modelled-constraint-costs  
**Fallback**: Search "modelled constraint costs" on data portal  
**Files to download**:
- Historical modelled costs CSV
- Save to: `modelled_costs/`

### 6. Skip Rate Methodology (CSV)
**URL**: https://www.neso.energy/data-portal/balancing-services/skip-rate  
**Fallback**: Search "skip rate" on data portal  
**Files to download**:
- Monthly skip rate CSV files for 2022-2025
- Save to: `skip_rates/`

## Ingestion Command

After downloading all files:

```bash
# Check directory structure
ls -R ~/GB-Power-Market-JJ/neso_downloads/constraint_costs/

# Test ingestion (no upload)
python3 ingest_neso_constraint_costs.py \
  --data-dir ~/GB-Power-Market-JJ/neso_downloads/constraint_costs \
  --test

# Production ingestion (upload to BigQuery)
python3 ingest_neso_constraint_costs.py \
  --data-dir ~/GB-Power-Market-JJ/neso_downloads/constraint_costs
```

## Verification

After ingestion, verify tables created:

```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

tables = ['neso_constraint_breakdown', 'neso_mbss', 'neso_skip_rates']
for table_name in tables:
    try:
        table = client.get_table(f'inner-cinema-476211-u9.uk_energy_prod.{table_name}')
        print(f'✅ {table_name}: {table.num_rows:,} rows')
    except:
        print(f'⚠️  {table_name}: Not found')
"
```

## Status

- [ ] Download constraint_breakdown CSVs (48 files, ~2 hours)
- [ ] Download MBSS CSVs (~30 min)
- [ ] Download annual reports Excel (~15 min)
- [ ] Download forecast CSV (~5 min)
- [ ] Download modelled costs CSV (~5 min)
- [ ] Download skip_rates CSVs (~30 min)
- [ ] Run ingestion script
- [ ] Verify tables created

**Estimated Time**: 3-4 hours manual downloading
