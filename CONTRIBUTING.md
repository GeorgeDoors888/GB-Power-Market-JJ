# Contributing to UK Power Market Data Pipeline

Thank you for your interest in contributing to this project! This document provides guidelines and best practices for contributing to the codebase.

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Standards](#code-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Submitting Changes](#submitting-changes)
6. [Documentation](#documentation)
7. [Data Quality](#data-quality)

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** (tested on 3.11.6)
- **Google Cloud Account** with BigQuery access
- **Service Account Key** with BigQuery permissions
- **Git** for version control

### Project Structure

```
GB Power Market JJ/
├── ingest_elexon_fixed.py       # Main ingestion script
├── download_multi_year_streaming.py  # Historical data downloader
├── bulk_downloader.py            # Bulk dataset downloader
├── update_dashboard_clean.py     # Dashboard update script
├── discover_all_datasets.py      # API dataset discovery
│
├── docs/
│   ├── README.md                 # Project overview
│   ├── DATA_MODEL.md             # Data model documentation
│   ├── AUTOMATION.md             # Automation guide
│   └── CONTRIBUTING.md           # This file
│
├── schemas/
│   └── corrected/                # Table schema definitions
│
├── insights_manifest_*.json      # Dataset manifests
├── jibber_jabber_key.json       # Service account key (DO NOT COMMIT)
└── requirements.txt              # Python dependencies
```

---

## 💻 Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/GeorgeDoors888/jibber-jabber-24-august-2025-big-bop.git
cd "GB Power Market JJ"
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Core Dependencies:**
- `google-cloud-bigquery` - BigQuery client
- `pandas` - Data manipulation
- `requests` - API calls
- `tqdm` - Progress bars
- `pyyaml` - Configuration files

### 4. Configure Authentication

```bash
# Set up service account key
export GOOGLE_APPLICATION_CREDENTIALS="jibber_jabber_key.json"

# Verify access
python -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected')"
```

### 5. Test the Setup

```bash
# Run a simple query
python update_dashboard_clean.py

# Or test ingestion with a small date range
python ingest_elexon_fixed.py --start 2025-10-01 --end 2025-10-02 --only FUELINST
```

---

## 📝 Code Standards

### Python Style Guide

We follow **PEP 8** with these specific guidelines:

#### Naming Conventions

```python
# Functions: snake_case
def fetch_data_from_api():
    pass

# Classes: PascalCase
class DataIngestionPipeline:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

# Variables: snake_case
dataset_name = "FUELINST"
records_count = 5000
```

#### Import Organization

```python
# Standard library imports first
import os
import sys
from datetime import datetime, timedelta

# Third-party imports second
import pandas as pd
import requests
from google.cloud import bigquery
from tqdm import tqdm

# Local imports last
from utils import sanitize_dataframe
```

#### Function Documentation

```python
def fetch_dataset(dataset_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch dataset from Elexon BMRS API for specified date range.
    
    Args:
        dataset_code: Dataset identifier (e.g., 'FUELINST', 'BOD')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        DataFrame containing fetched records
    
    Raises:
        requests.HTTPError: If API request fails
        ValueError: If date format is invalid
    
    Example:
        >>> df = fetch_dataset('FUELINST', '2025-01-01', '2025-01-02')
        >>> print(len(df))
        5780
    """
    # Implementation here
    pass
```

### Error Handling

Always use proper error handling with informative messages:

```python
try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
except requests.HTTPError as e:
    logging.error(f"❌ API request failed: {e}")
    raise
except requests.Timeout:
    logging.warning("⚠️ Request timed out, retrying...")
    # Retry logic here
```

### Logging

Use structured logging with appropriate levels:

```python
import logging

# Setup at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Usage
logging.info("✅ Successfully loaded 5780 rows")
logging.warning("⚠️ Rate limit approaching")
logging.error("❌ Failed to connect to API")
logging.debug("🔍 Request parameters: {params}")
```

---

## 🧪 Testing Guidelines

### Manual Testing

Before submitting changes, test with:

```bash
# Test with a single day
python ingest_elexon_fixed.py --start 2025-10-01 --end 2025-10-02 --only FUELINST

# Verify data loaded correctly
python -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
query = '''
SELECT COUNT(*) as count 
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\`
WHERE DATE(settlementDate) = '2025-10-01'
'''
result = list(client.query(query).result())[0]
print(f'Records: {result.count}')
"
```

### Data Quality Checks

Always verify:

1. **Row counts** - Expected vs actual
2. **Date ranges** - Correct data for requested dates
3. **Null values** - No unexpected nulls in critical columns
4. **Duplicates** - Hash keys prevent duplicates

```python
# Example quality check
def verify_data_quality(table_name: str, expected_date: str):
    """Verify data quality after ingestion."""
    query = f"""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT _hash_key) as unique_rows,
        COUNT(CASE WHEN generation IS NULL THEN 1 END) as null_generation,
        MIN(DATE(settlementDate)) as min_date,
        MAX(DATE(settlementDate)) as max_date
    FROM `{table_name}`
    WHERE DATE(settlementDate) = '{expected_date}'
    """
    # Run query and verify results
```

### Regression Testing

Before making changes to core ingestion logic:

1. Record current data state
2. Make your changes
3. Re-ingest same date range
4. Compare results (should be identical)

---

## 📤 Submitting Changes

### Git Workflow

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** with clear, atomic commits:
   ```bash
   git add ingest_elexon_fixed.py
   git commit -m "Fix: Use stream endpoint for FUELINST historical data"
   ```

3. **Write good commit messages:**
   ```
   Fix: Use stream endpoint for FUELINST historical data
   
   - Changed from /generation/actual/per-type to /datasets/FUELINST/stream
   - Added publishDateTimeFrom/To parameter handling
   - Resolves issue where only current data was returned
   
   Tested: 2023-2025 data loads correctly (5.68M rows)
   ```

4. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** with:
   - Clear title describing the change
   - Description of what changed and why
   - Testing performed
   - Any breaking changes

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `Fix:` - Bug fix
- `Feature:` - New feature
- `Docs:` - Documentation changes
- `Refactor:` - Code refactoring
- `Test:` - Adding tests
- `Perf:` - Performance improvement

**Example:**
```
Fix: Stream endpoint for historical FUELINST data

Standard Insights API endpoints only return current data regardless
of date parameters. Switched to /datasets/FUELINST/stream endpoint
which respects historical date ranges.

Changes:
- Updated endpoint URL (line 670)
- Added publishDateTime parameter handling (lines 676-686)
- Tested with 2023-2025 date ranges

Resolves: #42
```

---

## 📚 Documentation

### When to Update Documentation

Update documentation when you:
- Add new datasets
- Change API endpoints
- Modify data schemas
- Add new features
- Fix significant bugs
- Change configuration

### Documentation Files to Update

| Change Type | Files to Update |
|-------------|-----------------|
| New dataset | `DATA_MODEL.md`, `QUICK_REFERENCE.md` |
| API changes | `DATA_INGESTION_DOCUMENTATION.md` |
| New script | `README.md`, `DOCUMENTATION_INDEX.md` |
| Bug fix | Create `*_FIX_DOCUMENTATION.md` |
| Automation | `AUTOMATION.md` |

### Documentation Style

- Use **clear headings** with emoji for visual navigation
- Include **code examples** that are copy-pasteable
- Add **actual results** from queries when possible
- Use **tables** for comparisons and mappings
- Include **timestamps** on status documents

**Example:**
```markdown
### ✅ Working Solution

**Endpoint:** `/datasets/FUELINST/stream`

**Parameters:**
- `publishDateTimeFrom`: `2025-01-01T00:00:00Z`
- `publishDateTimeTo`: `2025-01-02T00:00:00Z`

**Result:** Returns actual historical data (5,780 records)
```

---

## 🎯 Data Quality

### Data Quality Principles

1. **Completeness** - No missing dates or periods
2. **Consistency** - Same schema across all loads
3. **Accuracy** - Data matches source API
4. **Uniqueness** - No duplicates (enforced by hash keys)
5. **Timeliness** - Daily updates within 24 hours

### Quality Checks

Run these checks after any ingestion:

```sql
-- Check for missing dates
WITH expected_dates AS (
  SELECT date
  FROM UNNEST(GENERATE_DATE_ARRAY('2025-01-01', '2025-10-29')) as date
),
actual_dates AS (
  SELECT DISTINCT DATE(settlementDate) as date
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
)
SELECT date as missing_date
FROM expected_dates
WHERE date NOT IN (SELECT date FROM actual_dates)
ORDER BY date;

-- Check for duplicates
SELECT 
  _hash_key,
  COUNT(*) as count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
GROUP BY _hash_key
HAVING count > 1;

-- Check for null values in critical columns
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN generation IS NULL THEN 1 END) as null_generation,
  COUNT(CASE WHEN fuelType IS NULL THEN 1 END) as null_fuel_type
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`;
```

### Schema Management

When adding new columns:

1. **Add to schema definition** in `schemas/corrected/`
2. **Update documentation** in `DATA_MODEL.md`
3. **Test with existing data** - ensure backward compatibility
4. **Add to metadata columns** if it's tracking metadata

---

## 🔧 Common Tasks

### Adding a New Dataset

1. **Discover the dataset:**
   ```python
   python discover_all_datasets.py
   ```

2. **Test the endpoint:**
   ```bash
   curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/NEWDATASET/stream?publishDateTimeFrom=2025-10-01T00:00:00Z&publishDateTimeTo=2025-10-02T00:00:00Z"
   ```

3. **Add to manifest:**
   Edit `insights_manifest_dynamic.json`

4. **Update ingestion script:**
   Add endpoint mapping in `ingest_elexon_fixed.py`

5. **Test ingestion:**
   ```bash
   python ingest_elexon_fixed.py --start 2025-10-01 --end 2025-10-02 --only NEWDATASET
   ```

6. **Document:**
   Update `DATA_MODEL.md` with schema and usage

### Handling API Changes

1. **Test new endpoint** with curl first
2. **Document behavior** in a markdown file
3. **Update code** with proper error handling
4. **Test with historical dates** to verify
5. **Update documentation** with findings

### Performance Optimization

When optimizing:

1. **Profile first** - Identify actual bottleneck
2. **Test with real data** - Use production-size datasets
3. **Measure improvement** - Before/after metrics
4. **Document changes** - Why and what improved

---

## 🚨 Common Issues

### Issue: Rate Limiting

**Solution:** Use 7-day windows and batch requests

```python
# Good: 7-day windows
for start, end in generate_7day_windows(start_date, end_date):
    fetch_data(start, end)

# Bad: Full year at once
fetch_data('2025-01-01', '2025-12-31')
```

### Issue: Memory Exhaustion

**Solution:** Use streaming uploads (50k batches)

```python
# Good: Stream in batches
def stream_to_bigquery(records_generator):
    batch = []
    for record in records_generator:
        batch.append(record)
        if len(batch) >= 50000:
            upload_batch(batch)
            batch = []

# Bad: Load all to memory
all_records = fetch_all_records()  # Could be 16M+ records
upload_all(all_records)  # Crashes with 40GB+ memory usage
```

### Issue: Wrong Data Dates

**Solution:** Always verify actual dates in response

```python
# After fetching, verify dates match request
if not df.empty:
    actual_dates = df['settlementDate'].min(), df['settlementDate'].max()
    logging.info(f"Requested: {start_date} to {end_date}")
    logging.info(f"Received: {actual_dates[0]} to {actual_dates[1]}")
```

---

## 📞 Getting Help

### Resources

- **Documentation:** Start with [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
- **Quick Reference:** Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **API Docs:** https://www.elexon.co.uk/guidance-note/bmrs-api-data-push-user-guide/

### Contact

- **Repository:** https://github.com/GeorgeDoors888/jibber-jabber-24-august-2025-big-bop
- **Issues:** Create an issue on GitHub
- **Maintainer:** George Major (Upowerenergy)

---

## ✅ Checklist Before Submitting

- [ ] Code follows PEP 8 style guide
- [ ] All functions have docstrings
- [ ] Changes tested with real data
- [ ] Data quality verified (no nulls, no duplicates)
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No sensitive data in commits (keys, credentials)
- [ ] `.gitignore` updated if needed

---

**Last Updated:** 29 October 2025  
**Version:** 1.0
