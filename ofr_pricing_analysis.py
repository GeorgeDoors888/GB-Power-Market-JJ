#!/usr/bin/env python3
"""
ofr_pricing_analysis.py

Compute realised £/MWh utilisation prices for OFR-linked actions
in bmrs_disbsad, and (optionally) compare to non-OFR actions.

Intended usage:
  python3 ofr_pricing_analysis.py \
      --project inner-cinema-476211-u9 \
      --dataset uk_energy_prod \
      --table bmrs_disbsad \
      --days 30
"""

from __future__ import annotations

import argparse
import datetime as dt

import pandas as pd
from google.cloud import bigquery


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OFR pricing analysis from DISBSAD.")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--dataset", required=True, help="BigQuery dataset name")
    parser.add_argument(
        "--table",
        default="bmrs_disbsad",
        help="BigQuery table name (default: bmrs_disbsad)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Lookback window in days (default: 30)",
    )
    parser.add_argument(
        "--compare-non-ofr",
        action="store_true",
        help="Also compute simple comparison to non-OFR actions.",
    )
    return parser.parse_args()


def build_ofr_query(project: str, dataset: str, table: str) -> str:
    """
    Returns a parameterised query that:
      - Filters to assetId LIKE 'OFR-%'
      - Filters by settlementDate BETWEEN @start_date AND @end_date
      - Requires cost IS NOT NULL AND volume > 0
      - Computes per-action price, and aggregated stats
    """
    fqtn = f"`{project}.{dataset}.{table}`"

    return f"""
    WITH base AS (
      SELECT
        assetId,
        CAST(settlementDate AS DATE) AS settlement_date,
        cost,
        volume,
        SAFE_DIVIDE(cost, NULLIF(volume, 0)) AS price_per_mwh
      FROM {fqtn}
      WHERE assetId LIKE 'OFR-%'
        AND CAST(settlementDate AS DATE) BETWEEN @start_date AND @end_date
        AND cost IS NOT NULL
        AND volume > 0
    ),
    per_action AS (
      SELECT
        assetId,
        settlement_date,
        cost,
        volume,
        price_per_mwh
      FROM base
      WHERE price_per_mwh IS NOT NULL
    )
    SELECT
      COUNT(*) AS n_actions,
      ROUND(SUM(cost), 2) AS total_cost_gbp,
      ROUND(SUM(volume), 2) AS total_volume_mwh,
      ROUND(SUM(cost) / NULLIF(SUM(volume), 0), 2) AS volume_weighted_avg_price_per_mwh,
      ROUND(MIN(price_per_mwh), 2) AS min_price_per_mwh,
      ROUND(MAX(price_per_mwh), 2) AS max_price_per_mwh,
      ROUND(APPROX_QUANTILES(price_per_mwh, 4)[OFFSET(1)], 2) AS q1_price_per_mwh,
      ROUND(APPROX_QUANTILES(price_per_mwh, 4)[OFFSET(2)], 2) AS median_price_per_mwh,
      ROUND(APPROX_QUANTILES(price_per_mwh, 4)[OFFSET(3)], 2) AS q3_price_per_mwh
    FROM per_action
    """


def build_comparison_query(project: str, dataset: str, table: str) -> str:
    """
    Simple comparison: OFR vs "other" actions that look like generator balancing.

    NOTE:
      - This is deliberately broad and *illustrative*.
      - For anything in docs, always label clearly that it's based on this
        classification logic and the chosen date window.
    """
    fqtn = f"`{project}.{dataset}.{table}`"

    return f"""
    WITH base AS (
      SELECT
        CASE
          WHEN assetId LIKE 'OFR-%' THEN 'OFR'
          ELSE 'Non-OFR'
        END AS bucket,
        CAST(settlementDate AS DATE) AS settlement_date,
        cost,
        volume,
        SAFE_DIVIDE(cost, NULLIF(volume, 0)) AS price_per_mwh
      FROM {fqtn}
      WHERE CAST(settlementDate AS DATE) BETWEEN @start_date AND @end_date
        AND cost IS NOT NULL
        AND volume > 0
    )
    SELECT
      bucket,
      COUNT(*) AS n_actions,
      ROUND(SUM(cost), 2) AS total_cost_gbp,
      ROUND(SUM(volume), 2) AS total_volume_mwh,
      ROUND(SUM(cost) / NULLIF(SUM(volume), 0), 2) AS volume_weighted_avg_price_per_mwh
    FROM base
    GROUP BY bucket
    ORDER BY bucket
    """


def print_ofr_summary(df: pd.DataFrame, start_date: dt.date, end_date: dt.date) -> None:
    if df.empty:
        print("❌ No OFR DISBSAD actions found in the selected window.")
        return

    row = df.iloc[0]

    print("=" * 80)
    print("OFR UTILISATION PRICE ANALYSIS (DISBSAD)")
    print("=" * 80)
    print(f"Window: {start_date} → {end_date}")
    print()
    print(f"Actions:       {int(row['n_actions']):,}")
    print(f"Total cost:    £{row['total_cost_gbp']:,}")
    print(f"Total volume:  {row['total_volume_mwh']:,} MWh")
    print()
    print("Realised utilisation price (£/MWh, from cost / volume):")
    print(f"  Volume-weighted avg: {row['volume_weighted_avg_price_per_mwh']:.2f}")
    print(f"  Min:                  {row['min_price_per_mwh']:.2f}")
    print(f"  Q1:                   {row['q1_price_per_mwh']:.2f}")
    print(f"  Median:               {row['median_price_per_mwh']:.2f}")
    print(f"  Q3:                   {row['q3_price_per_mwh']:.2f}")
    print(f"  Max:                  {row['max_price_per_mwh']:.2f}")
    print()
    print("NOTE: These figures use only actions where cost and volume are both present")
    print("      and volume > 0. Availability fees or other revenue streams are NOT")
    print("      included, so this is strictly a utilisation price from DISBSAD.")
    print("=" * 80)


def print_comparison(df: pd.DataFrame) -> None:
    if df.empty or df["bucket"].nunique() < 2:
        print("⚠️ Not enough data for OFR vs Non-OFR comparison.")
        return

    print()
    print("=" * 80)
    print("OFR vs NON-OFR: SIMPLE UTILISATION PRICE COMPARISON")
    print("=" * 80)
    print(df.to_string(index=False))
    print()
    # Optional relative comparison:
    ofr = df[df["bucket"] == "OFR"]["volume_weighted_avg_price_per_mwh"].iloc[0]
    non = df[df["bucket"] == "Non-OFR"]["volume_weighted_avg_price_per_mwh"].iloc[0]
    if non != 0:
        diff_pct = 100.0 * (non - ofr) / non
        print(f"OFR vs Non-OFR (volume-weighted avg £/MWh):")
        print(f"  OFR:      {ofr:.2f}")
        print(f"  Non-OFR:  {non:.2f}")
        print(f"  Difference: {diff_pct:+.1f}% (negative = OFR cheaper)")
    print("=" * 80)


def main() -> None:
    args = parse_args()

    client = bigquery.Client(project=args.project)

    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=args.days)

    ofr_query = build_ofr_query(args.project, args.dataset, args.table)
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )

    df_ofr = client.query(ofr_query, job_config=job_config).to_dataframe()
    print_ofr_summary(df_ofr, start_date, end_date)

    if args.compare_non_ofr:
        cmp_query = build_comparison_query(args.project, args.dataset, args.table)
        df_cmp = client.query(cmp_query, job_config=job_config).to_dataframe()
        print_comparison(df_cmp)


if __name__ == "__main__":
    main()
