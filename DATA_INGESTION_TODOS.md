# Data Ingestion & NGSEA Completion - Action Items

**Created**: 28 December 2025  
**Target Completion**: 15-20 January 2026  
**Current Status**: 22/46 data sources (48%), P114 backfill in progress

---

## Overview: Why This Matters

**Goal**: Complete NGSEA detection framework + full market data coverage

**Current Blockers**:
1. P114 backfill incomplete (113M/584M records = 19%)
2. Missing NESO constraint cost data (can't validate NGSEA detections)
3. Missing FPN data (Feature C placeholder in detection algorithm)
4. Missing interconnector data (5-15% of GB market not visible)

**Impact When Complete**:
- Full historical NGSEA analysis (2022-2025, ~1,096 days)
- Cross-validation with NESO official reports
- Complete market view (generation + demand + interconnectors)
- Production-ready statistical detection algorithm

---

## Todo List (6 Items, ~12-15 days total)

### ✅ Todo 1: Monitor P114 Backfill (Autonomous)
**Status**: IN PROGRESS (autonomous)  
**Owner**: Server process (PID 2243569, 2266755, 2272015)  
**Timeline**: 3-10 days (depends on API rate limits)  
**Effort**: 0 hours (monitoring only)

**Current State**:
- Records: 113.32M / 584M (19.4%)
- Processing: 2024-03-25 to 2024-03-31 R3 runs
- Worker CPU: 79.8% (active)

**Expected Completion**: 5-10 January 2026

**Action Items**:
- [x] Backfill running (no action needed)
- [ ] Check status daily: `ps aux | grep ingest_p114`
- [ ] Monitor logs: `tail -f logs/p114_backfill.log` (if exists)
- [ ] Verify completion: Run query to check record count hits 584M

**Completion Query**:
```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
query = 'SELECT COUNT(*) as total FROM \`inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi\`'
result = client.query(query).to_dataframe()
print(f'P114 Records: {result[\"total\"][0]:,}')
print('✅ COMPLETE' if result['total'][0] >= 584000000 else '🔄 In Progress')
"
```

**Risks**:
- API rate limiting (Elexon throttles requests)
- Server downtime (AlmaLinux server)
- Network interruptions

**Mitigation**: Script has automatic retry logic, batches resume from last checkpoint

---

### 🔄 Todo 2: Download NESO Constraint Cost Publications
**Status**: NOT STARTED  
**Owner**: George (manual download)  
**Timeline**: 1-2 days  
**Effort**: 3-4 hours manual work

**Priority**: **CRITICAL** (blocks NGSEA validation)

**Datasets to Download** (6 publications):

1. **Constraint Breakdown** (Monthly CSV)
   - URL: https://data.nationalgrideso.com/constraint-management/historic-constraint-breakdown
   - Format: CSV (one file per month)
   - Coverage: Download Jan 2022 - Dec 2025 (48 files)
   - Contains: Emergency Instructions costs by category

2. **MBSS - Mandatory Balancing Services** (Daily CSV)
   - URL: https://data.nationalgrideso.com/balancing-services/mbss-mandatory-balancing-services-costs
   - Format: CSV (daily breakdown)
   - Coverage: 2022-2025
   - Contains: Day-by-day emergency service costs

3. **Annual Balancing Costs Report** (PDF + Excel)
   - URL: https://www.nationalgrideso.com/document/series/balancing-services-reports
   - Format: PDF report + Excel data tables
   - Coverage: 2022, 2023, 2024 reports
   - Contains: Official NGSEA event counts per year

4. **24-Month Constraint Cost Forecast** (CSV)
   - URL: https://data.nationalgrideso.com/constraint-management/24-month-constraint-cost-forecast
   - Format: CSV (forecast by month)
   - Contains: Expected gas supply risk periods

5. **Modelled Constraint Costs** (CSV)
   - URL: https://data.nationalgrideso.com/constraint-management/modelled-constraint-costs
   - Format: CSV (historical analysis)
   - Contains: NGSEA cost attribution

6. **Skip Rate Methodology** (CSV)
   - URL: https://data.nationalgrideso.com/balancing-services/skip-rate
   - Format: CSV (monthly metrics)
   - Contains: Non-delivery tracking (NGSEA should be 0%)

**Action Steps**:
```bash
# 1. Create download directory
mkdir -p ~/GB-Power-Market-JJ/neso_downloads/constraint_costs

# 2. Download all datasets (manual via browser or script)
cd ~/GB-Power-Market-JJ/neso_downloads/constraint_costs

# 3. Organize files
mkdir constraint_breakdown mbss annual_reports forecast modelled_costs skip_rates

# 4. Move files to subfolders (manual)

# 5. Verify downloads
ls -lh */*.csv | wc -l  # Should show ~150+ files
```

**Completion Criteria**:
- [ ] All 6 publications downloaded (2022-2025 coverage)
- [ ] Files organized in subfolder structure
- [ ] CSV files readable (spot-check with `head -5`)
- [ ] Ready for BigQuery ingestion (Todo 3)

**Time Estimate**:
- Finding correct NESO Data Portal URLs: 30 minutes
- Downloading files (manual): 2 hours
- Organizing and verifying: 30 minutes
- **Total**: 3 hours

---

### 🔄 Todo 3: Ingest NESO Constraint Costs to BigQuery
**Status**: NOT STARTED (depends on Todo 2)  
**Owner**: George (development)  
**Timeline**: 1 day  
**Effort**: 4-6 hours development

**Priority**: **CRITICAL** (enables Feature D in NGSEA detection)

**Tables to Create**:

1. `neso_constraint_breakdown` (monthly costs)
2. `neso_mbss` (daily emergency services)
3. `neso_annual_reports` (yearly event counts)
4. `neso_constraint_forecast` (24-month ahead)
5. `neso_modelled_costs` (historical attribution)
6. `neso_skip_rates` (monthly non-delivery)

**Development Plan**:

```python
# Script: ingest_neso_constraint_costs.py

#!/usr/bin/env python3
"""
Ingest NESO Constraint Cost Publications to BigQuery

Tables created:
- neso_constraint_breakdown: Monthly Emergency Instructions costs
- neso_mbss: Daily emergency service costs
- neso_annual_reports: Yearly NGSEA event counts
- neso_constraint_forecast: 24-month constraint cost forecast
- neso_modelled_costs: Historical NGSEA cost attribution
- neso_skip_rates: Monthly skip rate metrics

Usage:
    python3 ingest_neso_constraint_costs.py --data-dir neso_downloads/constraint_costs
"""

import os
import glob
import pandas as pd
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def ingest_constraint_breakdown(client, data_dir):
    """Ingest monthly constraint breakdown CSVs"""
    files = glob.glob(f"{data_dir}/constraint_breakdown/*.csv")
    
    dfs = []
    for file in files:
        df = pd.read_csv(file)
        df['file_source'] = os.path.basename(file)
        df['ingested_utc'] = datetime.utcnow()
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    
    # Upload to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET}.neso_constraint_breakdown"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(combined, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Loaded {len(combined):,} rows to neso_constraint_breakdown")

def ingest_mbss(client, data_dir):
    """Ingest MBSS daily emergency service costs"""
    files = glob.glob(f"{data_dir}/mbss/*.csv")
    
    dfs = []
    for file in files:
        df = pd.read_csv(file)
        df['ingested_utc'] = datetime.utcnow()
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    
    table_id = f"{PROJECT_ID}.{DATASET}.neso_mbss"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(combined, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Loaded {len(combined):,} rows to neso_mbss")

def ingest_annual_reports(client, data_dir):
    """Parse Excel annual reports for NGSEA event counts"""
    files = glob.glob(f"{data_dir}/annual_reports/*.xlsx")
    
    # Parse manually (structure varies by year)
    data = []
    for file in files:
        year = int(os.path.basename(file).split('_')[0])  # Extract year from filename
        
        # Read Excel, find NGSEA section (manual parsing required)
        df = pd.read_excel(file, sheet_name='NGSEA Summary')  # Adjust sheet name
        
        # Extract event count
        event_count = df.loc[df['Category'] == 'NGSEA Events', 'Count'].values[0]
        
        data.append({
            'year': year,
            'ngsea_event_count': event_count,
            'source_file': os.path.basename(file),
            'ingested_utc': datetime.utcnow()
        })
    
    df_reports = pd.DataFrame(data)
    
    table_id = f"{PROJECT_ID}.{DATASET}.neso_annual_reports"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(df_reports, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Loaded {len(df_reports):,} years to neso_annual_reports")

# Similar functions for forecast, modelled_costs, skip_rates...

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', required=True, help='Path to neso_downloads/constraint_costs')
    args = parser.parse_args()
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("Starting NESO constraint cost ingestion...")
    
    ingest_constraint_breakdown(client, args.data_dir)
    ingest_mbss(client, args.data_dir)
    ingest_annual_reports(client, args.data_dir)
    # Add other ingestions...
    
    print("\n✅ All NESO constraint cost data ingested!")

if __name__ == "__main__":
    main()
```

**Action Steps**:
1. [ ] Create `ingest_neso_constraint_costs.py` script
2. [ ] Test on sample files (1 month constraint breakdown)
3. [ ] Handle CSV format variations (years may differ)
4. [ ] Run full ingestion (all 6 datasets)
5. [ ] Verify tables created in BigQuery console
6. [ ] Update `detect_ngsea_statistical.py` Feature D to use real NESO costs

**Completion Criteria**:
- [ ] All 6 tables created in BigQuery
- [ ] Row counts match downloaded files
- [ ] Sample queries return expected data
- [ ] Feature D updated in detection algorithm

**Time Estimate**: 4-6 hours (development + testing)

---

### 🔄 Todo 4: Ingest FPN (Final Physical Notification) Data
**Status**: NOT STARTED  
**Owner**: George (development)  
**Timeline**: 1 day  
**Effort**: 6-8 hours development

**Priority**: **HIGH** (enables Feature C in NGSEA detection)

**Background**: FPN = forecast of unit output submitted by generators. Large deviations between FPN and actual metered generation indicate post-event corrections (BSCP18).

**BMRS API Endpoint**: `/datasets/PN` (Physical Notification) and `/datasets/FPN` (Final Physical Notification)

**Development Plan**:

```python
# Script: ingest_fpn_historical.py

#!/usr/bin/env python3
"""
Ingest FPN (Final Physical Notification) data from BMRS API

FPN = Generator's forecast of expected output per settlement period
Used to detect NGSEA Feature C: Large FPN vs actual mismatch

API: GET /datasets/FPN
Docs: https://developer.data.elexon.co.uk/api-details#api=prod-insig-insights-api

Usage:
    python3 ingest_fpn_historical.py --start-date 2024-01-01 --end-date 2024-12-31
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
API_KEY = os.environ.get('ELEXON_API_KEY')  # Set in environment
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FPN"

def fetch_fpn_day(date_str):
    """Fetch FPN data for one day"""
    params = {
        'settlementDate': date_str,
        'format': 'json'
    }
    headers = {'Accept': 'application/json'}
    
    response = requests.get(BASE_URL, params=params, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    return pd.DataFrame(data['data'])

def ingest_fpn_range(start_date, end_date):
    """Ingest FPN for date range"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        try:
            df = fetch_fpn_day(date_str)
            
            if df.empty:
                print(f"⚠️  No data for {date_str}")
                current += timedelta(days=1)
                continue
            
            # Add metadata
            df['ingested_utc'] = datetime.utcnow()
            
            # Upload to BigQuery (append mode)
            table_id = f"{PROJECT_ID}.{DATASET}.bmrs_fpn"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=True
            )
            
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            print(f"✅ {date_str}: {len(df):,} rows")
            
        except Exception as e:
            print(f"❌ {date_str}: {e}")
        
        current += timedelta(days=1)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start-date', required=True, help='YYYY-MM-DD')
    parser.add_argument('--end-date', required=True, help='YYYY-MM-DD')
    args = parser.parse_args()
    
    print(f"Ingesting FPN: {args.start_date} to {args.end_date}")
    ingest_fpn_range(args.start_date, args.end_date)
    print("\n✅ FPN ingestion complete!")

if __name__ == "__main__":
    main()
```

**Action Steps**:
1. [ ] Create `ingest_fpn_historical.py` script
2. [ ] Get Elexon API key: https://developer.data.elexon.co.uk/
3. [ ] Test on 1 day (2024-10-17)
4. [ ] Run backfill for 2024 (365 days)
5. [ ] Extend to 2023, 2022 if API allows
6. [ ] Create `bmrs_fpn` table in BigQuery
7. [ ] Update Feature C in `detect_ngsea_statistical.py`

**Completion Criteria**:
- [ ] `bmrs_fpn` table created with 12+ months data
- [ ] Feature C functional (FPN mismatch detection)
- [ ] Test query shows FPN vs P114 comparison works

**Time Estimate**: 6-8 hours (API integration + testing)

---

### 🔄 Todo 5: Ingest Interconnector Flows
**Status**: NOT STARTED  
**Owner**: George (development)  
**Timeline**: 2-3 days  
**Effort**: 8-12 hours development

**Priority**: **MEDIUM** (major market component, 5-15% of GB supply/demand)

**Interconnectors** (7 total):
1. IFA (UK-France, 2 GW)
2. IFA2 (UK-France, 1 GW)
3. BritNed (UK-Netherlands, 1 GW)
4. NemoLink (UK-Belgium, 1 GW)
5. NSL (North Sea Link, UK-Norway, 1.4 GW)
6. Viking (UK-Denmark, 1.4 GW)
7. ElecLink (UK-France, 1 GW)

**NESO Data Portal**: https://data.nationalgrideso.com/interconnectors/

**Development Plan**:

```python
# Script: ingest_interconnector_flows.py

#!/usr/bin/env python3
"""
Ingest interconnector flow data from NESO Data Portal

Interconnectors: IFA, IFA2, BritNed, NemoLink, NSL, Viking, ElecLink
Format: CSV per interconnector per year

Usage:
    python3 ingest_interconnector_flows.py --start-year 2022 --end-year 2025
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

INTERCONNECTORS = {
    'IFA': 'https://data.nationalgrideso.com/backend/dataset/GUID/resource/GUID',
    'IFA2': '...',
    'BritNed': '...',
    'NemoLink': '...',
    'NSL': '...',
    'Viking': '...',
    'ElecLink': '...'
}

def download_interconnector_data(name, url, year):
    """Download CSV for one interconnector-year"""
    response = requests.get(url)
    response.raise_for_status()
    
    df = pd.read_csv(io.StringIO(response.text))
    df['interconnector'] = name
    df['year'] = year
    df['ingested_utc'] = datetime.utcnow()
    
    return df

def ingest_all_interconnectors(start_year, end_year):
    """Ingest all interconnectors for year range"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    all_data = []
    
    for name, base_url in INTERCONNECTORS.items():
        for year in range(start_year, end_year + 1):
            url = base_url.replace('YEAR', str(year))  # Adjust URL template
            
            try:
                df = download_interconnector_data(name, url, year)
                all_data.append(df)
                print(f"✅ {name} {year}: {len(df):,} rows")
            except Exception as e:
                print(f"❌ {name} {year}: {e}")
    
    # Combine all
    combined = pd.concat(all_data, ignore_index=True)
    
    # Upload to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET}.neso_interconnector_flows"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(combined, table_id, job_config=job_config)
    job.result()
    
    print(f"\n✅ Total: {len(combined):,} rows to neso_interconnector_flows")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start-year', type=int, default=2022)
    parser.add_argument('--end-year', type=int, default=2025)
    args = parser.parse_args()
    
    ingest_all_interconnectors(args.start_year, args.end_year)

if __name__ == "__main__":
    main()
```

**Action Steps**:
1. [ ] Find exact NESO Data Portal URLs for each interconnector
2. [ ] Create `ingest_interconnector_flows.py` script
3. [ ] Test on 1 interconnector (IFA) for 1 year
4. [ ] Run full ingestion (7 interconnectors × 4 years)
5. [ ] Create `neso_interconnector_flows` table
6. [ ] Add interconnector flows to dashboards

**Completion Criteria**:
- [ ] All 7 interconnectors ingested (2022-2025)
- [ ] `neso_interconnector_flows` table created
- [ ] Sample query shows daily import/export totals
- [ ] Integrated into market analysis

**Time Estimate**: 8-12 hours (URL discovery + development + testing)

---

### 🔄 Todo 6: Test Full NGSEA Detection Algorithm
**Status**: NOT STARTED (depends on Todos 2, 3, 4)  
**Owner**: George (testing)  
**Timeline**: 1 day  
**Effort**: 4-6 hours testing

**Priority**: **HIGH** (validates entire NGSEA framework)

**Prerequisites**:
- ✅ P114 backfill complete (584M records)
- ✅ NESO constraint costs ingested
- ✅ FPN data ingested
- ✅ Features A, B, C, D all functional

**Test Plan**:

1. **Run Full Algorithm** (all 4 features)
```bash
cd ~/GB-Power-Market-JJ
python3 detect_ngsea_statistical.py 2024-01-01 2024-12-31 --output ngsea_detections_2024.csv
```

2. **Cross-Validate with NESO Annual Report**
```sql
-- Compare detected events vs NESO official counts
WITH detected AS (
  SELECT 
    EXTRACT(YEAR FROM settlement_date) as year,
    COUNT(DISTINCT CONCAT(settlement_date, '-', settlement_period)) as events_detected
  FROM ngsea_detections_2024
  WHERE ngsea_score >= 5  -- Threshold
  GROUP BY year
),
neso_official AS (
  SELECT 
    year,
    ngsea_event_count as events_official
  FROM neso_annual_reports
  WHERE year = 2024
)
SELECT 
  d.year,
  d.events_detected,
  n.events_official,
  d.events_detected - n.events_official as difference,
  ROUND(d.events_detected / n.events_official * 100, 1) as match_percent
FROM detected d
LEFT JOIN neso_official n USING (year)
```

**Expected Result**: 80-95% match rate

3. **Analyze False Positives/Negatives**
```sql
-- Find high-score detections not in NESO reports
SELECT * FROM ngsea_detections_2024
WHERE ngsea_score >= 5
  AND settlement_date NOT IN (
    SELECT DISTINCT event_date FROM neso_constraint_breakdown
    WHERE category = 'Emergency Instructions'
  )
ORDER BY ngsea_score DESC
LIMIT 20
```

4. **Tune Scoring Weights**
```python
# Adjust weights in detect_ngsea_statistical.py
WEIGHTS = {
    'feature_a': 2.0,  # Turn-down signature
    'feature_b': 2.0,  # No BOALF or SO-Flag
    'feature_c': 1.5,  # FPN mismatch (increase if performing well)
    'feature_d': 1.0   # NESO constraint cost spike
}

THRESHOLD = 5.5  # Adjust based on precision/recall
```

5. **Generate Validation Report**
```bash
python3 validate_ngsea_detections.py \
  --detections ngsea_detections_2024.csv \
  --neso-reports neso_annual_reports \
  --output validation_report_2024.txt
```

**Action Steps**:
1. [ ] Run algorithm on full 2024 dataset
2. [ ] Compare with NESO official event counts
3. [ ] Investigate false positives (high score but not NGSEA)
4. [ ] Investigate false negatives (missed events)
5. [ ] Tune scoring weights and threshold
6. [ ] Re-run and validate improved accuracy
7. [ ] Document final configuration

**Completion Criteria**:
- [ ] Match rate ≥80% with NESO official counts
- [ ] False positive rate <20%
- [ ] False negative rate <15%
- [ ] Documented scoring configuration
- [ ] Validation report generated

**Time Estimate**: 4-6 hours (testing + tuning)

---

## Timeline Summary

| Todo | Task | Duration | Dependencies | Start Date | End Date |
|------|------|----------|--------------|------------|----------|
| 1 | Monitor P114 Backfill | 3-10 days | None | ✅ Running | 5-10 Jan |
| 2 | Download NESO Costs | 1-2 days | None | 28 Dec | 30 Dec |
| 3 | Ingest NESO to BQ | 1 day | Todo 2 | 31 Dec | 1 Jan |
| 4 | Ingest FPN Data | 1 day | None | 2 Jan | 3 Jan |
| 5 | Ingest Interconnectors | 2-3 days | None | 4 Jan | 7 Jan |
| 6 | Test NGSEA Algorithm | 1 day | Todos 1,3,4 | 10 Jan | 11 Jan |

**Critical Path**: Todo 1 (P114 backfill) is the longest pole (3-10 days)

**Earliest Completion**: 11 January 2026 (if P114 completes by 5 Jan)  
**Realistic Completion**: **15-20 January 2026** (allowing for P114 delays + testing iterations)

---

## Success Metrics

**Data Completeness**:
- [x] 22/46 sources (48%) → Target: 28/46 (61%)
- [ ] P114: 584M records (1,096 days) ✅
- [ ] NESO: 6 publications ingested ✅
- [ ] FPN: 12+ months historical ✅
- [ ] Interconnectors: 7 units, 4 years ✅

**NGSEA Detection**:
- [ ] Features A, B, C, D all functional
- [ ] 80-95% match rate with NESO official counts
- [ ] <20% false positive rate
- [ ] Production-ready algorithm

**Analysis Capability**:
- [ ] Full historical NGSEA analysis (2022-2025)
- [ ] Total industry NGSEA costs by year
- [ ] Most frequently curtailed units identified
- [ ] Seasonal patterns documented

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| P114 backfill stalls | Medium | High | Automatic retry, manual intervention if needed |
| NESO URL changes | Low | Medium | Document correct URLs, version control |
| API rate limits | Medium | Low | Add delays between requests, batch processing |
| FPN data unavailable | Low | High | Use P114 settlement as proxy (less accurate) |
| NGSEA match rate <80% | Medium | Medium | Tune scoring weights, investigate mismatches |

---

## Next Immediate Actions (Start Now)

### Can Start Immediately (No Dependencies):
1. **Todo 2**: Download NESO Constraint Costs (3-4 hours)
   - Start URL: https://data.nationalgrideso.com/constraint-management/
   - Download all 6 publications
   - Organize in subfolders

2. **Todo 4**: Develop FPN ingestion script (6-8 hours)
   - Get Elexon API key
   - Build initial script
   - Test on 1 day

3. **Todo 5**: Start interconnector URL discovery (2 hours)
   - Find NESO Data Portal links for all 7 interconnectors
   - Document CSV format for each

### Waiting on Dependencies:
4. **Todo 1**: Continue monitoring P114 backfill (check daily)
5. **Todo 3**: Ingest NESO costs (after Todo 2 complete)
6. **Todo 6**: Test algorithm (after Todos 1, 3, 4 complete)

---

*Created: 28 December 2025*  
*Target Completion: 15-20 January 2026*  
*Critical Path: P114 backfill (3-10 days)*  
*Next Action: Download NESO Constraint Costs (start now, 3-4 hours)*
