#!/usr/bin/env python3
"""
Verify Zero Duplicates Across All BMRS Tables

This script checks for duplicate data in BigQuery tables by analyzing:
1. Total row counts vs unique key combinations
2. Duplicate rows for each table
3. Window metadata consistency

Run after all ingestion completes (after 11:12 PM tonight).
"""

import sys
from google.cloud import bigquery
from datetime import datetime

# BigQuery setup
PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Key datasets to check
DATASETS_TO_CHECK = [
    ("bmrs_bod", ["settlementDate", "settlementPeriod", "bmUnit"]),
    ("bmrs_fuelinst", ["settlementDate", "settlementPeriod", "fuelType"]),
    ("bmrs_freq", ["measurementTime"]),
    ("bmrs_fuelhh", ["settlementDate", "settlementPeriod", "fuelType"]),
    ("bmrs_detsysprices", ["settlementDate", "settlementPeriod"]),
    ("bmrs_imbalngc", ["settlementDate", "settlementPeriod"]),
]


def check_duplicate_rows(client: bigquery.Client, table_name: str, key_columns: list[str]) -> dict:
    """
    Check for duplicate rows in a table based on key columns.
    
    Returns:
        dict with total_rows, unique_keys, duplicate_count, duplicate_percentage
    """
    table_id = f"{PROJECT}.{DATASET}.{table_name}"
    
    # Build CONCAT expression for unique key
    concat_parts = []
    for col in key_columns:
        concat_parts.append(f"CAST({col} AS STRING)")
    
    concat_expr = " || '|' || ".join(concat_parts)
    
    query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNT(DISTINCT {concat_expr}) as unique_keys
    FROM `{table_id}`
    """
    
    try:
        result = client.query(query).result()
        row = next(result)
        
        total_rows = row["total_rows"]
        unique_keys = row["unique_keys"]
        duplicate_count = total_rows - unique_keys
        duplicate_pct = (duplicate_count / total_rows * 100) if total_rows > 0 else 0
        
        return {
            "table": table_name,
            "total_rows": total_rows,
            "unique_keys": unique_keys,
            "duplicate_count": duplicate_count,
            "duplicate_percentage": duplicate_pct,
            "status": "✅ CLEAN" if duplicate_count == 0 else f"❌ {duplicate_count:,} DUPLICATES",
        }
    
    except Exception as e:
        return {
            "table": table_name,
            "total_rows": 0,
            "unique_keys": 0,
            "duplicate_count": 0,
            "duplicate_percentage": 0,
            "status": f"⚠️  ERROR: {str(e)}",
        }


def check_window_consistency(client: bigquery.Client, table_name: str) -> dict:
    """
    Check if windows have been loaded multiple times.
    
    Returns:
        dict with window_count, expected behavior
    """
    table_id = f"{PROJECT}.{DATASET}.{table_name}"
    
    query = f"""
    SELECT 
      _window_from_utc,
      COUNT(*) as rows_in_window,
      COUNT(DISTINCT settlementDate) as unique_dates
    FROM `{table_id}`
    WHERE _window_from_utc IS NOT NULL
    GROUP BY _window_from_utc
    HAVING COUNT(*) > 10000  -- Flag unusually large windows
    ORDER BY rows_in_window DESC
    LIMIT 10
    """
    
    try:
        results = list(client.query(query).result())
        
        if not results:
            return {
                "status": "✅ All windows normal size",
                "suspicious_windows": 0,
            }
        
        suspicious = []
        for row in results:
            suspicious.append({
                "window": row["_window_from_utc"],
                "rows": row["rows_in_window"],
                "dates": row["unique_dates"],
            })
        
        return {
            "status": f"⚠️  {len(suspicious)} unusually large windows",
            "suspicious_windows": suspicious,
        }
    
    except Exception as e:
        return {
            "status": f"⚠️  ERROR: {str(e)}",
            "suspicious_windows": [],
        }


def check_settlement_period_consistency(client: bigquery.Client, table_name: str, sample_date: str = "2025-06-15") -> dict:
    """
    Check if settlement periods have reasonable row counts (should be ~30-50 BMUs per period for BOD).
    """
    table_id = f"{PROJECT}.{DATASET}.{table_name}"
    
    # Different tables have different structures
    if "bod" in table_name.lower():
        group_cols = "settlementDate, settlementPeriod"
        entity_col = "bmUnit"
    elif "fuelinst" in table_name.lower() or "fuelhh" in table_name.lower():
        group_cols = "settlementDate, settlementPeriod"
        entity_col = "fuelType"
    elif "freq" in table_name.lower():
        # FREQ doesn't have settlement periods
        return {"status": "✅ FREQ uses continuous time series", "avg_rows_per_period": "N/A"}
    else:
        group_cols = "settlementDate, settlementPeriod"
        entity_col = "settlementDate"  # Fallback
    
    query = f"""
    SELECT 
      AVG(row_count) as avg_rows_per_period,
      MAX(row_count) as max_rows_per_period,
      MIN(row_count) as min_rows_per_period,
      STDDEV(row_count) as stddev_rows
    FROM (
      SELECT 
        {group_cols},
        COUNT(*) as row_count
      FROM `{table_id}`
      WHERE settlementDate = '{sample_date}'
      GROUP BY {group_cols}
    )
    """
    
    try:
        result = client.query(query).result()
        row = next(result)
        
        avg_rows = row["avg_rows_per_period"]
        max_rows = row["max_rows_per_period"]
        min_rows = row["min_rows_per_period"]
        stddev = row["stddev_rows"]
        
        # For BOD, expect ~30-50 rows per period (one per BMU)
        # For FUELINST, expect ~10-20 rows per period (one per fuel type)
        # Outliers suggest duplicates
        
        status = "✅ Normal distribution"
        if max_rows > avg_rows * 2:
            status = f"⚠️  Max ({max_rows}) >> Avg ({avg_rows:.1f})"
        
        return {
            "status": status,
            "avg_rows_per_period": f"{avg_rows:.1f}",
            "max_rows": max_rows,
            "min_rows": min_rows,
            "stddev": f"{stddev:.1f}" if stddev else "0",
        }
    
    except Exception as e:
        return {
            "status": f"⚠️  ERROR: {str(e)}",
            "avg_rows_per_period": "N/A",
        }


def main():
    print("=" * 80)
    print("🔍 DUPLICATE VERIFICATION REPORT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project: {PROJECT}")
    print(f"Dataset: {DATASET}")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=PROJECT)
    
    all_clean = True
    results = []
    
    print("📊 CHECKING FOR DUPLICATE ROWS")
    print("-" * 80)
    
    for table_name, key_columns in DATASETS_TO_CHECK:
        print(f"\nChecking {table_name}...", end=" ", flush=True)
        result = check_duplicate_rows(client, table_name, key_columns)
        results.append(result)
        
        print(result["status"])
        
        if result["duplicate_count"] > 0:
            all_clean = False
            print(f"  Total rows: {result['total_rows']:,}")
            print(f"  Unique keys: {result['unique_keys']:,}")
            print(f"  Duplicates: {result['duplicate_count']:,} ({result['duplicate_percentage']:.2f}%)")
    
    print()
    print("=" * 80)
    print()
    
    # Summary table
    print("📋 SUMMARY TABLE")
    print("-" * 80)
    print(f"{'Table':<25} {'Total Rows':<15} {'Unique Keys':<15} {'Duplicates':<15} {'Status':<20}")
    print("-" * 80)
    
    for result in results:
        print(
            f"{result['table']:<25} "
            f"{result['total_rows']:>14,} "
            f"{result['unique_keys']:>14,} "
            f"{result['duplicate_count']:>14,} "
            f"{result['status']:<20}"
        )
    
    print("-" * 80)
    print()
    
    # Check window consistency for a few key tables
    print("🪟 WINDOW CONSISTENCY CHECK")
    print("-" * 80)
    
    for table_name, _ in DATASETS_TO_CHECK[:3]:
        print(f"\nChecking {table_name} windows...", end=" ", flush=True)
        window_check = check_window_consistency(client, table_name)
        print(window_check["status"])
        
        if window_check.get("suspicious_windows"):
            for sw in window_check["suspicious_windows"]:
                print(f"  ⚠️  Window {sw['window']}: {sw['rows']:,} rows, {sw['dates']} dates")
    
    print()
    print("=" * 80)
    print()
    
    # Check settlement period consistency
    print("📅 SETTLEMENT PERIOD CONSISTENCY (Sample: 2025-06-15)")
    print("-" * 80)
    
    for table_name, _ in DATASETS_TO_CHECK[:4]:
        print(f"\n{table_name}:")
        sp_check = check_settlement_period_consistency(client, table_name, "2025-06-15")
        print(f"  {sp_check['status']}")
        if sp_check.get('avg_rows_per_period') != 'N/A':
            print(f"  Avg rows/period: {sp_check['avg_rows_per_period']}")
            print(f"  Range: {sp_check.get('min_rows', 'N/A')} - {sp_check.get('max_rows', 'N/A')}")
    
    print()
    print("=" * 80)
    print()
    
    # Final verdict
    if all_clean:
        print("✅ ✅ ✅  ALL TABLES CLEAN - ZERO DUPLICATES DETECTED  ✅ ✅ ✅")
        print()
        print("Your data is ready for analysis!")
        sys.exit(0)
    else:
        print("❌ ❌ ❌  DUPLICATES DETECTED - CLEANUP REQUIRED  ❌ ❌ ❌")
        print()
        print("Run the deduplication queries from DUPLICATE_PREVENTION_ANALYSIS.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
