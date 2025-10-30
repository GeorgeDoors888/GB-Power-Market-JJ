# Project Documentation: UK Energy Insights Data Pipeline

## Overview
This document outlines the project structure, the code used to populate the BigQuery tables, and the processes involved in managing and analyzing the UK Energy Insights dataset. The project leverages Python scripts, Google Cloud BigQuery, and Elexon APIs to fetch, process, and store energy data.

---

## Project Structure

### Key Components
- **BigQuery Dataset**: `uk_energy_insights`
  - **Location**: US
  - **Tables**: Contains multiple tables such as `bmrs_boalf`, `bmrs_bod`, `bmrs_disbsad`, etc., each representing different energy metrics.
- **Python Scripts**:
  - `live_data_updater.py`: Fetches live data from Elexon and NESO APIs.
  - `bq_write_inventory.py`: Generates a detailed inventory of the BigQuery dataset.
  - `elexon_neso_downloader.py`: Downloads historical data from Elexon and NESO APIs.

---

## Code Used to Populate Tables

### Live Data Updater
The `live_data_updater.py` script is the core component for fetching and updating live data. It includes the following key methods:

- **`update_elexon_dataset(dataset_name)`**:
  - Fetches recent data for a specific Elexon dataset.
  - Deduplicates data using composite keys.
  - Uploads data to Google Cloud Storage and BigQuery.

- **`update_all_elexon_datasets()`**:
  - Iterates through all Elexon datasets and updates them.

- **Rate Limiting**:
  - Ensures compliance with Elexon API rate limits using `_respect_elexon_rate_limit()`.

### Inventory Script
The `bq_write_inventory.py` script generates a detailed inventory of the BigQuery dataset, including metadata such as table size, row count, and last modified timestamp.

---

## BigQuery Dataset Inventory

### Dataset Details
- **Project**: `jibber-jabber-knowledge`
- **Dataset**: `uk_energy_insights`
- **Location**: US

### Example Tables
- **`bmrs_boalf`**:
  - Rows: 3,702,236
  - Size: 882.1 MB
  - Last Modified: 2025-08-29
- **`bmrs_bod`**:
  - Rows: 572,659,776
  - Size: 119.6 GB
  - Last Modified: 2025-08-30
- **`bmrs_disbsad`**:
  - Rows: 1,457,416
  - Size: 144.7 MB
  - Last Modified: 2025-08-30

---

## How to Access the Data

### Web Console
Access the dataset via the Google Cloud Console:
[BigQuery Console](https://console.cloud.google.com/bigquery?project=jibber-jabber-knowledge)

### Python (google-cloud-bigquery)
```python
from google.cloud import bigquery
client = bigquery.Client(project="jibber-jabber-knowledge")
table = client.get_table("jibber-jabber-knowledge.uk_energy_insights.<table_name>")
rows = client.list_rows(table, max_results=10)
for r in rows: print(dict(r))
```

### bq CLI
```bash
bq show --schema --format=prettyjson jibber-jabber-knowledge:uk_energy_insights.<table_name>
bq head --max_rows 10 jibber-jabber-knowledge:uk_energy_insights.<table_name>
```

---

## Example Query
```sql
SELECT *
FROM `jibber-jabber-knowledge.uk_energy_insights.<table_name>`
ORDER BY _ingested_utc DESC
LIMIT 100;
```

---

## Code for Data Ingestion to BigQuery

### Script: `live_data_updater.py`

The `live_data_updater.py` script is responsible for ingesting data into BigQuery. It interacts with the Elexon API to fetch live energy data and processes it before uploading it to BigQuery.

### Methodology

1. **API Integration**:
   - The script uses the Elexon API to fetch datasets such as `demand_outturn`, `generation_outturn`, and `system_warnings`.
   - API rate limits are respected using the `_respect_elexon_rate_limit` method.

2. **Data Processing**:
   - Data is fetched in JSON format and converted into a Pandas DataFrame.
   - Deduplication is performed using composite keys based on `settlement_date` and `settlement_period`.
   - Data is standardized by renaming columns and converting date fields to the appropriate format.

3. **Cloud Storage**:
   - Processed data is temporarily saved as JSON files and uploaded to Google Cloud Storage.
   - The `update_elexon_dataset` method handles this process, ensuring data integrity.

4. **BigQuery Upload**:
   - Data is uploaded to BigQuery using the `google-cloud-bigquery` library.
   - The schema is validated before uploading to ensure compatibility.

### Key Methods

- **`update_elexon_dataset(dataset_name)`**:
  - Fetches and processes data for a specific dataset.
  - Handles deduplication, schema validation, and uploads to BigQuery.

- **`update_all_elexon_datasets()`**:
  - Iterates through all Elexon datasets and updates them in BigQuery.

- **`_respect_elexon_rate_limit()`**:
  - Ensures compliance with Elexon API rate limits by introducing delays between requests.

### Example Workflow

1. **Fetch Data**:
   - The script constructs API requests using the dataset name and date range.
   - Example:
     ```python
     url = f"{self.elexon_base_url}/{endpoint}"
     params = {
         'from': from_date,
         'to': to_date,
         'format': 'json'
     }
     response = self.session.get(url, params=params)
     ```

2. **Process Data**:
   - Deduplication and column standardization are performed.
   - Example:
     ```python
     df = df.rename(columns={
         'settlementDate': 'settlement_date',
         'settlementPeriod': 'settlement_period'
     })
     ```

3. **Upload to BigQuery**:
   - Data is uploaded using the BigQuery client.
   - Example:
     ```python
     load_job = self.bigquery_client.load_table_from_dataframe(
         df, table_ref, job_config=job_config
     )
     load_job.result()
     ```

This script is a robust and efficient solution for ingesting live energy data into BigQuery, ensuring data accuracy and compliance with API constraints.

---

## Final Notes
This project represents a robust and scalable solution for managing UK energy data. The codebase is well-documented and adheres to best practices, ensuring maintainability and extensibility. The `live_data_updater.py` script, in particular, is a standout component, showcasing advanced data handling and API integration techniques.
