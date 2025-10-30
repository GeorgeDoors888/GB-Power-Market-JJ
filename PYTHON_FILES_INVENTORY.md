# Python Files Inventory - GB Power Market Project

**Generated:** 27 October 2025, 00:45 AM  
**Total Python Files:** 424

---

## 🔥 ACTIVE FILES (Currently In Use)

### Core Ingestion
1. **`ingest_elexon_fixed.py`** ⭐ PRIMARY
   - Main data ingestion engine
   - Status: RUNNING (PID 13489)
   - Last Modified: 27 Oct 2025 (skip logic bug fix)
   - Purpose: Ingest BMRS data to BigQuery with chunking and deduplication

2. **`remove_bod_duplicates.py`** ⭐ UTILITY
   - Deduplication script for BigQuery tables
   - Created: 27 Oct 2025
   - Purpose: Remove duplicates using `_hash_key` column

3. **`monitor_progress.py`** ⭐ MONITORING
   - Log parser and progress tracker
   - Created: 27 Oct 2025
   - Purpose: Real-time ingestion monitoring and completion estimates

---

## 📦 SUPPORTING FILES (Helper Scripts)

### Analysis & Debugging
4. **`analyze_complete_datasets.py`**
   - Analyze dataset completeness
   
5. **`api_discrepancy_investigation.py`**
   - Investigate API endpoint discrepancies

6. **`inspect_table_schemas.py`**
   - Inspect BigQuery table schemas

7. **`investigate_missing_datasets.py`**
   - Find missing datasets in ingestion

8. **`bigquery_utils.py`**
   - Utility functions for BigQuery operations

### Discovery & Mapping
9. **`discover_all_datasets_dynamic.py`**
   - Dynamic dataset discovery from API

10. **`discover_all_datasets.py`**
    - Static dataset discovery

11. **`create_comprehensive_manifest.py`**
    - Create dataset manifest files

12. **`elexon_client_introspect.py`**
    - Introspect Elexon client capabilities

13. **`elexon_client_method_signatures.py`**
    - Document client method signatures

14. **`elexon_client_methods.py`**
    - List available client methods

### Download Scripts
15. **`bulk_downloader.py`**
    - Bulk data download utility

16. **`download_all_2025_data.py`**
    - Download all 2025 data

17. **`download_last_7_days.py`**
    - Download recent 7 days

18. **`download_multi_year_streaming.py`**
    - Multi-year streaming download

19. **`download_multi_year.py`**
    - Multi-year batch download

20. **`download_recovered_datasets.py`**
    - Re-download missing datasets

21. **`download_sep_oct_2025.py`**
    - Download Sep-Oct 2025 specifically

22. **`historic_downloader.py`**
    - Historical data downloader

23. **`elexon_neso_downloader.py`**
    - Combined Elexon/NESO downloader

24. **`unified_downloader.py`**
    - Unified download interface

### BigQuery Management
25. **`bq_debug_automation.py`**
    - BigQuery debugging automation

26. **`bq_fresh_start.py`**
    - Fresh BigQuery setup

27. **`fix_nested_datasets.py`**
    - Fix nested dataset structures

### Testing & Validation
28. **`neso_network_test.py`**
    - Test NESO network connectivity

29. **`rate_limit_monitor.py`**
    - Monitor API rate limits

### Sampling
30. **`sample_jan_aug_2025.py`**
    - Sample Jan-Aug 2025 data

31. **`sample_jan_aug_2025_v2.py`**
    - Version 2 of sampling script

### Authentication
32. **`fix_auth.py`**
    - Fix authentication issues

33. **`bootstrap.py`**
    - Bootstrap/setup script

### Dashboard/UI
34. **`update_dashboard.py`**
    - Update dashboard data

35. **`update_dashboard_clean.py`**
    - Clean dashboard update

---

## 🗄️ OLD PROJECT FILES (Legacy/Archived)

Located in `/old_project/` directory - **NOT IN ACTIVE USE**

### Dashboard Applications (36-50)
- `gb_energy_dashboard.py`
- `energy_dashboard_v3.py`
- `enhanced_dashboard_app.py`
- `interactive_dashboard_app.py`
- `simplified_dashboard.py`
- `bigquery_only_dashboard.py`
- `optimized_dashboard_app.py`
- `live_energy_dashboard.py`
- `gb_energy_dashboard_fixed.py`
- `gb_energy_dashboard_improved.py`
- `advanced_stats_bigquery_app.py`
- `test_dashboard_graphs.py`
- `update_dashboard_dataset.py`
- `monitor_app.py`
- `flask_wrapper.py`

### Data Collection (51-80)
- `sunday_collection.py`
- `quick_start_collection.py`
- `download_status_check.py`
- `week_bid_offer_downloader.py`
- `priority_2018_downloader.py`
- `quickstart_downloader.py`
- `download_all_bmrs_endpoints.py`
- `check_latest_bmrs_download.py`
- `complete_missing_downloader.py`
- `neso_data_loader.py`
- `elexon_data_monitor.py`
- `neso_network_info_downloader.py`
- `load_historical_data.py`
- `load_historical_data_fixed.py`
- `test_2017_historical_data.py`
- `simple_cloud_downloader.py`
- `fast_cloud_backfill.py`
- `google_drive_data_manager.py`
- Various downloaders and loaders

### BigQuery Tools (81-110)
- `check_bq_tables.py`
- `create_bq_tables.py`
- `create_bigquery_tables.py`
- `create_remaining_tables.py`
- `fix_bigquery_schemas.py`
- `fix_bigquery_summary.py`
- `comprehensive_bigquery_summary.py`
- `get_bigquery_stats.py`
- `query_bigquery_results.py`
- `scan_bigquery_neso_elexon.py`
- `advanced_stats_bigquery.py`
- `copy_bq_dataset.py`
- `bq_auth.py`
- `bq_data_validator.py`
- `bq_load_geo_data.py`
- `bigquery_auth_diagnostic.py`
- `enhanced_bigquery_loader.py`
- `gcs_to_bq_loader.py`
- Various BQ utilities

### Analysis & Reports (111-150)
- `bod_analysis.py`
- `bod_analysis_enhanced.py`
- `direct_bod_analysis.py`
- `data_analyzer.py`
- `neso_data_analyzer.py`
- `data_type_analysis.py`
- `generate_investigation_summary.py`
- `gcs_missing_datasets_report.py`
- `google_docs_comprehensive_report.py`
- `research_to_gdoc_plus.py`
- `count_bmrs_files.py`
- `find_last_dates.py`
- `find_data_horizon.py`
- `check_date_ranges_quick.py`
- `check_2016_data.py`
- `data_cheeck_summary.py`
- Various analysis scripts

### Testing & Validation (151-170)
- `sunday_validation_test.py`
- `comprehensive_balancing_test.py`
- `scripts_smoke_test_datasets.py`
- `library_core_test.py`
- `quick_check_large_datasets.py`
- Various test scripts

### Utilities (171-200)
- `extract_api_endpoints.py`
- `elexon_catalogue_plus.py`
- `neso_progress_monitor.py`
- `update_project_memory.py`
- `setup_looker_studio.py`
- `authorize_gcp_browser.py`
- `secure_env_loader_example.py`
- `simple_bod_adapter.py`
- `run_bod_with_auth.py`
- `bod_auth.py`
- Various utilities

### Data Generation (201-210)
- `generate_test_data_automated.py`
- `generate_remaining_test_data.py`
- Various test data generators

### Other (211+)
- `iris_main.py`
- `better_main.py`
- `Untitled-1.py`
- Miscellaneous scripts

---

## 🔧 SHELL SCRIPTS

### Active Scripts
1. **`run_2025_then_2024.sh`** ⭐ RUNNING
   - Auto-starts 2024 after 2025 completes
   - Status: Active in background

2. **`cleanup_and_restart_ingestion.sh`** ⭐ UTILITY
   - Full cleanup and restart workflow
   - Last used: 27 Oct 2025, 00:13

3. **`restart_ingestion.sh`** ⭐ UTILITY
   - Simple restart without cleanup

4. **`run_ingestion.sh`**
   - Basic ingestion starter

5. **`download_all_years_auto.sh`**
   - Automated multi-year download

### Legacy Scripts (in old_project/)
- `run_interactive_dashboard.sh`
- `run_gb_energy_dashboard_fixed.sh`
- `deploy_ingestion_cloud.sh`
- `monitor_live_updater.sh`
- `run_dashboard_with_statistics.sh`
- `auto_generate_data.sh`
- `run_dashboard_automated.sh`
- `run_bod_analysis_with_fallback.sh`
- `deploy_streamlit_only.sh`
- `fix_and_restart_uk_energy_system.sh`
- `run_automated_pipeline.sh`
- `run_neso_loader.sh`
- `load_elexon_data.sh`
- `run_uk_energy_system.sh`
- `load_bq_data.sh`
- Plus ~100 more legacy scripts

---

## 📋 DATA FILES

### Manifests
- `insights_manifest.json`
- `insights_manifest_complete.json`
- `insights_manifest_comprehensive.json`
- `insights_manifest_dynamic.json`
- `insights_manifest_full.json`

### Configurations
- `dataset_special_configs.json`
- `insights_endpoints.generated.yml`
- `insights_endpoints.with_units.yml`

### Results
- `discovery_results_dynamic_20251026_015758.json`
- `discovery_results_dynamic_20251026_015915.json`
- `jan_aug_sampling_results_20251026_173506.json`
- `missing_datasets_investigation.json`
- `bigquery_storage_report.json`

### Loading Plans
- `loading_plan_mapping_20250824_200345.json`
- `loading_plan_plan_20250824_200345.json`
- `loading_plan_plan_20250824_200345.md`

---

## 📖 DOCUMENTATION FILES

### Active Documentation
1. **`INGESTION_DOCUMENTATION.md`** ⭐ CREATED TODAY
   - Complete system documentation
   - 27 Oct 2025

2. **`PYTHON_FILES_INVENTORY.md`** ⭐ THIS FILE
   - Complete Python file inventory
   - 27 Oct 2025

3. **`QUICK_REFERENCE.md`**
   - Quick command reference

4. **`README.md`**
   - Project overview

### Historical Documentation
- `API_RESEARCH_FINDINGS.md`
- `ARCHITECTURE_DIAGRAM.md`
- `AUTHENTICATION_FIX.md`
- `BMRS_VS_INSIGHTS_API.md`
- `CORRECTED_ANALYSIS.md`
- `DATA_INGESTION_DOCUMENTATION.md`
- `DATASET_DISCOVERY_PROBLEM_SUMMARY.md`
- `DISCOVERY_RESULTS_20251026_015758.md`
- `DISCOVERY_RESULTS_20251026_015915.md`
- `DISCOVERY_SUCCESS_SUMMARY.md`
- `DOCUMENTATION_INDEX.md`
- `DOWNLOAD_STATUS_REPORT.md`
- `ELEXON_INGESTION_README.md`
- `ENDPOINT_DISCOVERY_ANALYSIS.md`
- `FINAL_STATUS_REPORT.md`
- `FIXED_CODE_LOCATION.md`
- `MISSING_DATASETS_REPORT.md`
- `MISSING_DATASETS_SUMMARY.md`
- `MULTI_YEAR_DOWNLOAD_PLAN.md`
- `PROOF_PN_QPN_EXIST.md`

---

## 🎯 FILE USAGE RECOMMENDATIONS

### For Daily Operations
**Use these files:**
1. `ingest_elexon_fixed.py` - Main ingestion
2. `monitor_progress.py` - Check progress
3. `remove_bod_duplicates.py` - Clean duplicates if needed
4. `restart_ingestion.sh` - Restart processes
5. `cleanup_and_restart_ingestion.sh` - Full cleanup

### For Analysis
**Use these files:**
1. `inspect_table_schemas.py` - Check schemas
2. `bigquery_utils.py` - BQ helper functions
3. `analyze_complete_datasets.py` - Dataset analysis

### For Discovery
**Use these files:**
1. `discover_all_datasets_dynamic.py` - Find new datasets
2. `create_comprehensive_manifest.py` - Update manifests

### Documentation
**Read these first:**
1. `INGESTION_DOCUMENTATION.md` - Complete system docs
2. `QUICK_REFERENCE.md` - Quick commands
3. `README.md` - Project overview

---

## ⚠️ FILES TO AVOID

**Do not use files in `/old_project/`** unless specifically needed for historical reference.

**Deprecated scripts:**
- Anything with "dashboard" in old_project/
- Cloud deployment scripts (not using cloud run currently)
- Old authentication scripts (auth is fixed in main files)

---

## 🔍 Finding Files

### By Purpose
```bash
# Ingestion-related
ls -la | grep ingest

# Analysis-related
ls -la | grep analyz

# BigQuery-related
ls -la | grep bq

# Download-related
ls -la | grep download

# Monitoring
ls -la | grep monitor
```

### By Date
```bash
# Files modified today
find . -name "*.py" -mtime 0

# Files modified in last 7 days
find . -name "*.py" -mtime -7

# Recently modified (excluding old_project)
find . -name "*.py" -mtime -30 -not -path "./old_project/*"
```

### By Size
```bash
# Large Python files (over 100KB)
find . -name "*.py" -size +100k

# Small utility scripts (under 10KB)
find . -name "*.py" -size -10k
```

---

## 📊 Statistics

**Total Python Files:** 424  
**Active Python Files:** ~35  
**Legacy Python Files:** ~389  
**Shell Scripts:** 118  
**Active Shell Scripts:** 5  
**Documentation Files:** 25+  
**Configuration Files:** 10+  

**Primary Development:**
- Main ingestion: `ingest_elexon_fixed.py` (1,800+ lines)
- Utilities: Various helper scripts (50-500 lines)
- Monitoring: `monitor_progress.py` (300+ lines)

---

**Last Updated:** 27 October 2025, 00:45 AM  
**Maintained By:** GitHub Copilot + George Major
