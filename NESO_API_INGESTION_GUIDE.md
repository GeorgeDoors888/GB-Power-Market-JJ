# NESO API Ingestion Guide

**Created**: 28 December 2025  
**Replaces**: Manual CSV downloads (3-4 hours) → Automated API calls (15-30 minutes)

## 🚀 Quick Start

### 1. Discover Available Datasets

```bash
python3 ingest_neso_api.py --discover
```

This will:
- Search NESO API for constraint costs, MBSS, skip rates
- Save dataset IDs to `neso_discovered_datasets.json`
- Show dataset names, titles, and IDs

### 2. Explore a Specific Dataset

```bash
python3 ingest_neso_api.py --dataset-id historic-constraint-breakdown
```

This shows:
- Dataset title and description
- List of resources (CSV files) with UUIDs
- Last modified dates, formats, sizes

### 3. Download Resource to BigQuery (Test)

```bash
python3 ingest_neso_api.py \
  --resource-id <UUID_FROM_STEP_2> \
  --table-name neso_constraint_breakdown \
  --test
```

Test mode:
- Downloads first 10 rows only
- Shows data preview
- No BigQuery upload

### 4. Production Download

```bash
python3 ingest_neso_api.py \
  --resource-id <UUID> \
  --table-name neso_constraint_breakdown
```

Production mode:
- Downloads all data (paginated, respects rate limits)
- Auto-detects schema
- Uploads to BigQuery
- Replaces existing table

---

## 📚 NESO API Details

### API Base URL
```
https://api.neso.energy/api/3/action/
```

### Rate Limits (CRITICAL)
- **CKAN endpoints** (search, metadata): 1 request/second
- **Datastore queries** (data download): 2 requests/minute

**Script automatically enforces these limits.**

### Key Endpoints

#### 1. Search Datasets
```bash
curl "https://api.neso.energy/api/3/action/package_search?q=constraint"
```

#### 2. Get Dataset Metadata
```bash
curl "https://api.neso.energy/api/3/action/package_show?id=historic-constraint-breakdown"
```

#### 3. Get Resource Info (check last_modified)
```bash
curl "https://api.neso.energy/api/3/action/resource_show?id=<resource_uuid>"
```

#### 4. Query Datastore (paginated)
```bash
curl "https://api.neso.energy/api/3/action/datastore_search?resource_id=<uuid>&limit=100&offset=0"
```

#### 5. SQL Query (most powerful)
```bash
curl "https://api.neso.energy/api/3/action/datastore_search_sql?sql=SELECT * FROM \"<uuid>\" LIMIT 5"
```

---

## 🎯 Target Datasets

Based on manual download requirements, find these via API:

### 1. Historic Constraint Breakdown
**Search term**: `constraint breakdown` or `constraint cost`  
**Expected**: Monthly CSV files (2022-2025)  
**BigQuery table**: `neso_constraint_breakdown`

### 2. MBSS (Mandatory Balancing Services)
**Search term**: `MBSS` or `mandatory balancing services`  
**Expected**: Daily cost breakdown  
**BigQuery table**: `neso_mbss`

### 3. Skip Rate
**Search term**: `skip rate`  
**Expected**: Monthly skip rate metrics  
**BigQuery table**: `neso_skip_rates`

### 4. 24-Month Forecast
**Search term**: `24 month constraint forecast`  
**Expected**: Forward-looking constraint costs  
**BigQuery table**: `neso_forecast`

### 5. Modelled Constraint Costs
**Search term**: `modelled constraint costs`  
**Expected**: Historical attribution  
**BigQuery table**: `neso_modelled_costs`

---

## 🔄 Workflow Example

### Step-by-Step: Ingest Constraint Breakdown

```bash
# 1. Discover datasets
python3 ingest_neso_api.py --discover
# Output saved to: neso_discovered_datasets.json

# 2. Find "historic-constraint-breakdown" ID in JSON
cat neso_discovered_datasets.json | grep -A 3 "constraint"

# 3. Get dataset details (find resource UUIDs)
python3 ingest_neso_api.py --dataset-id historic-constraint-breakdown

# 4. Test download (first resource)
python3 ingest_neso_api.py \
  --resource-id <UUID_OF_FIRST_CSV> \
  --table-name neso_constraint_breakdown_2025_12 \
  --test

# 5. Production download (all resources)
for uuid in <UUID1> <UUID2> <UUID3>; do
  python3 ingest_neso_api.py \
    --resource-id $uuid \
    --table-name neso_constraint_breakdown
  sleep 60  # Respect rate limits
done
```

---

## 🆚 API vs Manual Comparison

### Manual Download (OLD)
- ❌ 48 CSV files × 2 min each = **2 hours** clicking
- ❌ Download folder management
- ❌ Need to re-download if data updates
- ❌ Human error (missed files, wrong folders)

### API Download (NEW)
- ✅ **15-30 minutes** automated
- ✅ Programmatic, repeatable
- ✅ Check `last_modified` → only fetch if changed
- ✅ Direct to BigQuery (no local storage)
- ✅ Rate limit enforcement built-in

---

## 🧪 Testing Strategy

### 1. Test Search
```bash
python3 ingest_neso_api.py --search "constraint"
# Verify: Returns results
```

### 2. Test Discovery
```bash
python3 ingest_neso_api.py --discover
# Verify: Creates neso_discovered_datasets.json with 10+ datasets
```

### 3. Test Metadata
```bash
python3 ingest_neso_api.py --dataset-id <DATASET_ID>
# Verify: Shows resources with UUIDs
```

### 4. Test Sample Download
```bash
python3 ingest_neso_api.py \
  --resource-id <UUID> \
  --table-name test_neso_sample \
  --test
# Verify: Shows 10 rows preview, no BigQuery upload
```

### 5. Test Production Download
```bash
python3 ingest_neso_api.py \
  --resource-id <UUID> \
  --table-name test_neso_full
# Verify: Creates BigQuery table with all rows
```

---

## ⚠️ Rate Limit Management

Script enforces:
- **CKAN calls**: 1 second delay between calls
- **Datastore queries**: 30 second delay (2/min)

**For bulk downloads**:
- Process 1 resource at a time
- Add 60-second sleep between resources
- Monitor API response times (if slow, increase delays)

**Example bulk script**:
```bash
#!/bin/bash
for uuid in uuid1 uuid2 uuid3; do
  echo "Processing $uuid..."
  python3 ingest_neso_api.py --resource-id $uuid --table-name neso_data
  echo "Waiting 60 seconds..."
  sleep 60
done
```

---

## 🔍 Troubleshooting

### Problem: "429 Too Many Requests"
**Solution**: Increase delays in script:
- Edit `CKAN_DELAY` to 2.0 seconds
- Edit `DATASTORE_DELAY` to 45.0 seconds

### Problem: "Resource not found"
**Solution**: 
- Resource UUID may be wrong
- Check dataset metadata again: `--dataset-id <id>`
- NESO may have updated dataset structure

### Problem: "Empty result set"
**Solution**:
- Resource may not support datastore API (CSV download only)
- Check `resource_show` → if format="CSV", may need manual download
- Some datasets are download-only, not queryable

### Problem: BigQuery schema errors
**Solution**:
- Script uses `autodetect=True` (usually works)
- For custom schema: Edit script, add explicit schema definition
- Check for special characters in column names

---

## 📊 Verification Queries

After ingestion, verify data in BigQuery:

```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

# Check tables created
tables = ['neso_constraint_breakdown', 'neso_mbss', 'neso_skip_rates']
for table_name in tables:
    try:
        table = client.get_table(f'inner-cinema-476211-u9.uk_energy_prod.{table_name}')
        print(f'✅ {table_name}: {table.num_rows:,} rows, {table.num_bytes:,} bytes')
        print(f'   Schema: {[f.name for f in table.schema[:5]]}...')
    except Exception as e:
        print(f'⚠️  {table_name}: Not found')
"
```

---

## 🎯 Next Steps

1. **TODAY**: Run discovery
   ```bash
   python3 ingest_neso_api.py --discover
   ```

2. **REVIEW**: Check discovered datasets in JSON file

3. **TEST**: Download 1 resource in test mode

4. **PRODUCTION**: Automate all constraint cost datasets

5. **SCHEDULE**: Add to cron for daily/weekly updates
   ```bash
   # Check last_modified, re-download if changed
   0 2 * * * cd /home/george/GB-Power-Market-JJ && python3 ingest_neso_api.py --update-all
   ```

---

## 💡 Advanced: SQL Queries

For large datasets, use SQL queries instead of pagination:

```python
from ingest_neso_api import NesoApiClient

neso = NesoApiClient()

# Filter by date range
sql = """
SELECT * FROM "<resource_uuid>"
WHERE settlement_date >= '2024-01-01'
  AND settlement_date < '2025-01-01'
"""

result = neso.query_datastore_sql(sql)
# Returns filtered data only (faster, less data transfer)
```

---

**Estimated Time Savings**: 2-3 hours (manual) → 15-30 minutes (automated)  
**Maintenance**: Can be scheduled, repeatable, auditable  
**Priority**: HIGH (replaces Todo #2 manual download task)

**Status**: ✅ Ready to use NOW
