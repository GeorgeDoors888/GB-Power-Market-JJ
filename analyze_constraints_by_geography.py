#!/usr/bin/env python3
"""
analyze_constraints_by_geography.py

Analyzes SO-flagged (constraint-related) BOALF actions by:
  - Region (North Scotland, South Scotland, England & Wales, Interconnector)
  - DNO area
  - GSP group
  - Fuel type (Wind, Solar, CCGT, Hydro, Interconnector, etc.)

Combines bmrs_boalf + bmrs_boalf_iris and joins to bmu_registration_data
to tag each BMU with geographic and fuel metadata.

Usage:
  python3 analyze_constraints_by_geography.py [--days N] [--export-csv]
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

import pandas as pd
from google.cloud import bigquery


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze constraint actions by geography and fuel type"
    )
    parser.add_argument(
        "--project",
        default="inner-cinema-476211-u9",
        help="GCP project ID (default: inner-cinema-476211-u9)",
    )
    parser.add_argument(
        "--dataset",
        default="uk_energy_prod",
        help="BigQuery dataset (default: uk_energy_prod)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Lookback window in days (default: 30)",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export results to CSV file",
    )
    parser.add_argument(
        "--csv-file",
        default="constraint_geography_analysis.csv",
        help="CSV filename (default: constraint_geography_analysis.csv)",
    )
    return parser.parse_args()


def build_query(project: str, dataset: str) -> str:
    """
    Returns the constraint geography analysis query with parameterized dates.
    
    Combines:
      - bmrs_boalf + bmrs_boalf_iris (SO-flagged actions)
      - bmu_registration_data (geography + fuel metadata)
    
    Outputs:
      - region (North Scotland / South Scotland / England & Wales)
      - dno_area (DNO company)
      - gsp_group (GSP group name)
      - fuel_group (Wind, Solar, CCGT, Hydro, etc.)
      - n_actions (count)
      - total_mw_adjusted (sum of absolute MW changes)
      - share_of_total_pct (percentage of total MW-adjusted)
    """
    return f"""
-- Constraint actions by geography and fuel type
-- ============================================
-- Combines bmrs_boalf + bmrs_boalf_iris with bmu_registration_data

WITH
-- 1) All SO-flagged (constraint-related) BOALF actions
combined_boalf AS (
  SELECT
    bmUnit,
    CAST(settlementDate AS DATE) AS settlement_date,
    settlementPeriodFrom AS sp_from,
    settlementPeriodTo   AS sp_to,
    soFlag,
    levelFrom,
    levelTo
  FROM `{project}.{dataset}.bmrs_boalf`
  WHERE CAST(settlementDate AS DATE) BETWEEN @start_date AND @end_date
    AND soFlag = TRUE

  UNION ALL

  SELECT
    bmUnit,
    CAST(settlementDate AS DATE) AS settlement_date,
    settlementPeriodFrom AS sp_from,
    settlementPeriodTo   AS sp_to,
    soFlag,
    levelFrom,
    levelTo
  FROM `{project}.{dataset}.bmrs_boalf_iris`
  WHERE CAST(settlementDate AS DATE) BETWEEN @start_date AND @end_date
    AND soFlag = TRUE
),

-- 2) Join to BMU registration to pull geography + fuel
boalf_with_meta AS (
  SELECT
    bo.bmUnit,

    -- MW change per action (absolute)
    SAFE_CAST(ABS(bo.levelTo - bo.levelFrom) AS FLOAT64) AS mw_adjusted,

    -- Pull metadata from registration table
    br.fueltype                          AS raw_fueltype,
    br.gspgroupname                      AS raw_gsp_group
  FROM combined_boalf bo
  LEFT JOIN `{project}.{dataset}.bmu_registration_data` br
    ON bo.bmUnit = br.nationalgridbmunit
       OR bo.bmUnit = br.elexonbmunit
),

-- 3) Classify region and fuel (simplified - GSP-based geography)
classified AS (
  SELECT
    bmUnit,
    mw_adjusted,

    -- Region classification (using GSP group patterns + interconnector/transmission prefix)
    CASE
      WHEN bmUnit LIKE 'I_%' THEN 'Interconnector'
      WHEN bmUnit LIKE 'T_%' THEN 'Transmission (National Grid)'
      WHEN raw_gsp_group LIKE '%SCOTLAND%' 
           OR raw_gsp_group IN ('_A', '_B', '_C', '_D', '_E', '_F', '_G') 
           THEN 'Scotland'
      WHEN raw_gsp_group IS NOT NULL AND raw_gsp_group != '' THEN 'England & Wales'
      ELSE 'Other / Unknown'
    END AS region,

    -- GSP group
    COALESCE(raw_gsp_group, 'Unknown') AS gsp_group,

    -- Fuel grouping
    CASE
      WHEN UPPER(raw_fueltype) = 'WIND'           THEN 'Wind'
      WHEN UPPER(raw_fueltype) = 'SOLAR'          THEN 'Solar'
      WHEN UPPER(raw_fueltype) IN ('CCGT','GAS')  THEN 'CCGT / Gas'
      WHEN UPPER(raw_fueltype) LIKE 'HYDRO%'      THEN 'Hydro'
      WHEN UPPER(raw_fueltype) LIKE 'NUCLEAR%'    THEN 'Nuclear'
      WHEN UPPER(raw_fueltype) LIKE 'INTERCONNECTOR%' 
           OR bmUnit LIKE 'I_%'                   THEN 'Interconnector'
      WHEN raw_fueltype IS NULL                   THEN 'Unknown'
      ELSE raw_fueltype
    END AS fuel_group
  FROM boalf_with_meta
),

-- 4) Aggregate by region / GSP / fuel
agg AS (
  SELECT
    region,
    gsp_group,
    fuel_group,
    COUNT(*) AS n_actions,
    ROUND(SUM(mw_adjusted), 1) AS total_mw_adjusted
  FROM classified
  GROUP BY region, gsp_group, fuel_group
)

-- 5) Add share of total MW-adjusted for charting
SELECT
  region,
  gsp_group,
  fuel_group,
  n_actions,
  total_mw_adjusted,
  ROUND(
    100.0 * total_mw_adjusted
    / NULLIF(SUM(total_mw_adjusted) OVER (), 0),
    2
  ) AS share_of_total_pct
FROM agg
ORDER BY
  total_mw_adjusted DESC,
  region,
  gsp_group,
  fuel_group
"""


def print_summary(df: pd.DataFrame, start_date: date, end_date: date) -> None:
    """Print formatted summary of constraint analysis results."""
    if df.empty:
        print("❌ No constraint actions found in the selected window.")
        return

    total_actions = df["n_actions"].sum()
    total_mw = df["total_mw_adjusted"].sum()

    print("=" * 80)
    print("CONSTRAINT ACTIONS BY GEOGRAPHY & FUEL TYPE")
    print("=" * 80)
    print(f"Analysis Period: {start_date} → {end_date}")
    print()
    print(f"Total Constraint Actions: {total_actions:,}")
    print(f"Total MW Adjusted:        {total_mw:,.1f} MW")
    print()

    # Regional summary
    print("=" * 80)
    print("BY REGION")
    print("=" * 80)
    region_summary = (
        df.groupby("region")
        .agg(
            {
                "n_actions": "sum",
                "total_mw_adjusted": "sum",
                "share_of_total_pct": "sum",
            }
        )
        .sort_values("total_mw_adjusted", ascending=False)
    )
    
    for region, row in region_summary.iterrows():
        print(
            f"{region:20} {int(row['n_actions']):>6,} actions  "
            f"{row['total_mw_adjusted']:>10,.1f} MW  "
            f"({row['share_of_total_pct']:>5.1f}%)"
        )
    print()

    # Fuel type summary
    print("=" * 80)
    print("BY FUEL TYPE")
    print("=" * 80)
    fuel_summary = (
        df.groupby("fuel_group")
        .agg(
            {
                "n_actions": "sum",
                "total_mw_adjusted": "sum",
                "share_of_total_pct": "sum",
            }
        )
        .sort_values("total_mw_adjusted", ascending=False)
    )
    
    for fuel, row in fuel_summary.iterrows():
        print(
            f"{fuel:20} {int(row['n_actions']):>6,} actions  "
            f"{row['total_mw_adjusted']:>10,.1f} MW  "
            f"({row['share_of_total_pct']:>5.1f}%)"
        )
    print()

    # Top 10 by MW adjusted
    print("=" * 80)
    print("TOP 10 COMBINATIONS (by MW Adjusted)")
    print("=" * 80)
    print(
        f"{'Region':<30} {'GSP Group':<25} "
        f"{'Fuel':<15} {'Actions':>7} {'MW':>12} {'Share':>7}"
    )
    print("-" * 80)
    
    top_10 = df.nlargest(10, "total_mw_adjusted")
    for _, row in top_10.iterrows():
        print(
            f"{row['region']:<30} "
            f"{row['gsp_group']:<25} {row['fuel_group']:<15} "
            f"{int(row['n_actions']):>7,} {row['total_mw_adjusted']:>12,.1f} "
            f"{row['share_of_total_pct']:>6.1f}%"
        )
    print()
    print("=" * 80)


def main() -> None:
    args = parse_args()

    # Initialize BigQuery client
    client = bigquery.Client(project=args.project)

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)

    # Build and run query
    query = build_query(args.project, args.dataset)
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )

    print(f"Running constraint geography analysis...")
    print(f"Date range: {start_date} to {end_date}")
    print()

    try:
        df = client.query(query, job_config=job_config).to_dataframe()
    except Exception as e:
        print(f"❌ Query failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Print summary
    print_summary(df, start_date, end_date)

    # Export to CSV if requested
    if args.export_csv:
        df.to_csv(args.csv_file, index=False)
        print(f"✓ Results exported to: {args.csv_file}")
        print()


if __name__ == "__main__":
    main()
