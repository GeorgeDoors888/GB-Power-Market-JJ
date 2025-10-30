# Project Plan: Historical Elexon Data Ingestion (2022-2025)

## 1. Objective

The goal of this project is to perform a large-scale historical data ingestion from the Elexon APIs into the Google BigQuery project `jibber-jabber-knowledge`, dataset `elexon_data_landing_zone`. This plan outlines the sequential process for ingesting data for the years 2025, 2024, 2023, and 2022, and includes reporting steps to validate the process.

---

## 2. Execution Phases

The project is divided into the following phases, which will be executed sequentially.

### Phase 1: Ingest 2025 Data

The first step is to backfill all available data for the year 2025.

-   **Action:** Execute the `ingest_elexon_fixed.py` script.
-   **Date Range:** From `2025-01-01` to `2026-01-01`.
-   **Command:**
    ```bash
    nohup python ingest_elexon_fixed.py --start 2025-01-01 --end 2026-01-01 > ingest_2025.log 2>&1 &
    ```
-   **Note:** This is a long-running background process. Progress will be monitored via the `ingest_2025.log` file.

### Phase 2: Generate Mid-Project Report

After the 2025 data has been ingested, a report will be generated to document the size and scope of the tables in BigQuery.

-   **Action:** Create and execute a new reporting script, `generate_bq_report.py`.
-   **Functionality:** This script will:
    1.  Connect to the `jibber-jabber-knowledge.elexon_data_landing_zone` dataset.
    2.  Query the `INFORMATION_SCHEMA` to get metadata for each table (table name, total rows, size in MB).
    3.  Output the results into two files: `BQ_TABLE_REPORT.txt` and `BQ_TABLE_REPORT.json`.
-   **Data Access Definition:** The report will serve as a manifest of the available data. Access is granted via standard Google Cloud IAM roles for BigQuery. Users can query data using:
    -   The Google Cloud Console UI.
    -   BigQuery client libraries in Python, Java, Go, etc.
    -   Connected tools like Looker Studio or other BI platforms.

### Phase 3: Ingest Historical Data (2022-2024)

With the 2025 data in place, the process will be repeated for the previous three years, one year at a time.

-   **Action:** Execute the `ingest_elexon_fixed.py` script for each year.

-   **2024 Ingestion:**
    ```bash
    nohup python ingest_elexon_fixed.py --start 2024-01-01 --end 2025-01-01 > ingest_2024.log 2>&1 &
    ```

-   **2023 Ingestion:**
    ```bash
    nohup python ingest_elexon_fixed.py --start 2023-01-01 --end 2024-01-01 > ingest_2023.log 2>&1 &
    ```

-   **2022 Ingestion:**
    ```bash
    nohup python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 > ingest_2022.log 2>&1 &
    ```

### Phase 4: Final Report

Once all historical data has been successfully ingested, the reporting script will be run again to generate a final, comprehensive manifest of the entire dataset.

-   **Action:** Re-run `generate_bq_report.py`.
-   **Output:** Updated `BQ_TABLE_REPORT.txt` and `BQ_TABLE_REPORT.json` files reflecting the complete 2022-2025 dataset.

---

## 3. Approval

Execution of this plan will commence upon user approval.
