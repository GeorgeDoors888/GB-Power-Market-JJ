#!/usr/bin/env python3
"""
interactive_analysis_dashboard.py

Interactive dashboard for OFR pricing and constraint geography analysis
with date range filtering controls.

Features:
  - Date range selection (from/to dates)
  - Real-time filtering of analysis results
  - Interactive prompts for analysis type
  - Export filtered results to CSV

Usage:
  python3 interactive_analysis_dashboard.py
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta

import pandas as pd
from google.cloud import bigquery


def get_date_input(prompt: str, default_date: date) -> date:
    """Get date input from user with validation."""
    while True:
        date_str = input(f"{prompt} (YYYY-MM-DD) [default: {default_date}]: ").strip()
        
        if not date_str:
            return default_date
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD")


def get_analysis_choice() -> str:
    """Get user's analysis choice."""
    print("\n" + "=" * 60)
    print("ANALYSIS OPTIONS")
    print("=" * 60)
    print("1. OFR Pricing Analysis (DISBSAD)")
    print("2. Constraint Geography Analysis (BOALF)")
    print("3. Both Analyses")
    print("=" * 60)
    
    while True:
        choice = input("Select analysis (1/2/3): ").strip()
        if choice in ["1", "2", "3"]:
            return choice
        print("❌ Invalid choice. Please select 1, 2, or 3")


def run_ofr_analysis(
    client: bigquery.Client,
    start_date: date,
    end_date: date,
    export_csv: bool = False
) -> pd.DataFrame:
    """Run OFR pricing analysis for date range."""
    print(f"\n🔄 Running OFR pricing analysis ({start_date} to {end_date})...")
    
    query = f"""
    WITH base AS (
      SELECT
        assetId,
        CAST(settlementDate AS DATE) AS settlement_date,
        cost,
        volume,
        SAFE_DIVIDE(cost, NULLIF(volume, 0)) AS price_per_mwh
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad`
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
      ROUND(SUM(cost) / NULLIF(SUM(volume), 0), 2) AS avg_price_per_mwh,
      ROUND(MIN(price_per_mwh), 2) AS min_price,
      ROUND(MAX(price_per_mwh), 2) AS max_price,
      ROUND(APPROX_QUANTILES(price_per_mwh, 4)[OFFSET(2)], 2) AS median_price
    FROM per_action
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )
    
    df = client.query(query, job_config=job_config).to_dataframe()
    
    if not df.empty:
        row = df.iloc[0]
        print("\n" + "=" * 60)
        print("OFR PRICING RESULTS")
        print("=" * 60)
        print(f"Actions:       {int(row['n_actions']):,}")
        print(f"Total cost:    £{row['total_cost_gbp']:,.2f}")
        print(f"Total volume:  {row['total_volume_mwh']:,.2f} MWh")
        print(f"Avg price:     £{row['avg_price_per_mwh']:.2f}/MWh")
        print(f"Price range:   £{row['min_price']:.2f} - £{row['max_price']:.2f}/MWh")
        print(f"Median:        £{row['median_price']:.2f}/MWh")
        print("=" * 60)
        
        if export_csv:
            filename = f"ofr_pricing_{start_date}_{end_date}.csv"
            df.to_csv(filename, index=False)
            print(f"✓ Exported to: {filename}")
    else:
        print("❌ No OFR actions found in date range")
    
    return df


def run_constraint_analysis(
    client: bigquery.Client,
    start_date: date,
    end_date: date,
    export_csv: bool = False
) -> pd.DataFrame:
    """Run constraint geography analysis for date range."""
    print(f"\n🔄 Running constraint analysis ({start_date} to {end_date})...")
    
    query = f"""
    WITH combined_boalf AS (
      SELECT
        bmUnit,
        CAST(settlementDate AS DATE) AS settlement_date,
        levelFrom,
        levelTo
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) BETWEEN @start_date AND @end_date
        AND soFlag = TRUE

      UNION ALL

      SELECT
        bmUnit,
        CAST(settlementDate AS DATE) AS settlement_date,
        levelFrom,
        levelTo
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) BETWEEN @start_date AND @end_date
        AND soFlag = TRUE
    ),
    
    boalf_with_meta AS (
      SELECT
        bo.bmUnit,
        SAFE_CAST(ABS(bo.levelTo - bo.levelFrom) AS FLOAT64) AS mw_adjusted,
        br.fueltype AS raw_fueltype,
        br.gspgroupname AS raw_gsp_group
      FROM combined_boalf bo
      LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data` br
        ON bo.bmUnit = br.nationalgridbmunit
           OR bo.bmUnit = br.elexonbmunit
    ),
    
    classified AS (
      SELECT
        bmUnit,
        mw_adjusted,
        CASE
          WHEN bmUnit LIKE 'I_%' THEN 'Interconnector'
          WHEN bmUnit LIKE 'T_%' THEN 'Transmission (National Grid)'
          WHEN raw_gsp_group LIKE '%SCOTLAND%' THEN 'Scotland'
          WHEN raw_gsp_group IS NOT NULL AND raw_gsp_group != '' THEN 'England & Wales'
          ELSE 'Other / Unknown'
        END AS region,
        COALESCE(raw_gsp_group, 'Unknown') AS gsp_group,
        CASE
          WHEN UPPER(raw_fueltype) = 'WIND' THEN 'Wind'
          WHEN UPPER(raw_fueltype) = 'SOLAR' THEN 'Solar'
          WHEN UPPER(raw_fueltype) IN ('CCGT','GAS') THEN 'CCGT / Gas'
          WHEN UPPER(raw_fueltype) LIKE 'HYDRO%' THEN 'Hydro'
          WHEN UPPER(raw_fueltype) LIKE 'NUCLEAR%' THEN 'Nuclear'
          WHEN UPPER(raw_fueltype) LIKE 'INTERCONNECTOR%' OR bmUnit LIKE 'I_%' THEN 'Interconnector'
          WHEN raw_fueltype IS NULL THEN 'Unknown'
          ELSE raw_fueltype
        END AS fuel_group
      FROM boalf_with_meta
    )
    
    SELECT
      region,
      fuel_group,
      COUNT(*) AS n_actions,
      ROUND(SUM(mw_adjusted), 1) AS total_mw_adjusted,
      ROUND(100.0 * SUM(mw_adjusted) / NULLIF(SUM(SUM(mw_adjusted)) OVER (), 0), 2) AS share_pct
    FROM classified
    GROUP BY region, fuel_group
    ORDER BY total_mw_adjusted DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )
    
    df = client.query(query, job_config=job_config).to_dataframe()
    
    if not df.empty:
        total_actions = df["n_actions"].sum()
        total_mw = df["total_mw_adjusted"].sum()
        
        print("\n" + "=" * 60)
        print("CONSTRAINT GEOGRAPHY RESULTS")
        print("=" * 60)
        print(f"Total actions:  {total_actions:,}")
        print(f"Total MW adj:   {total_mw:,.1f} MW")
        print()
        print("Top 5 Categories:")
        print("-" * 60)
        
        for idx, row in df.head(5).iterrows():
            print(
                f"{row['region']:<25} {row['fuel_group']:<15} "
                f"{int(row['n_actions']):>6,} actions  {row['total_mw_adjusted']:>10,.1f} MW "
                f"({row['share_pct']:>5.1f}%)"
            )
        print("=" * 60)
        
        if export_csv:
            filename = f"constraints_{start_date}_{end_date}.csv"
            df.to_csv(filename, index=False)
            print(f"✓ Exported to: {filename}")
    else:
        print("❌ No constraint actions found in date range")
    
    return df


def main():
    """Main interactive dashboard loop."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     INTERACTIVE ANALYSIS DASHBOARD                          ║")
    print("║     OFR Pricing & Constraint Geography                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project="inner-cinema-476211-u9")
    except Exception as e:
        print(f"❌ Failed to connect to BigQuery: {e}")
        sys.exit(1)
    
    # Get date range
    print("\n" + "=" * 60)
    print("DATE RANGE SELECTION")
    print("=" * 60)
    
    default_end = date.today()
    default_start = default_end - timedelta(days=30)
    
    start_date = get_date_input("From date", default_start)
    end_date = get_date_input("To date", default_end)
    
    # Validate date range
    if start_date > end_date:
        print("❌ Start date must be before end date")
        sys.exit(1)
    
    days = (end_date - start_date).days
    print(f"\n✓ Date range: {start_date} to {end_date} ({days} days)")
    
    # Get analysis choice
    choice = get_analysis_choice()
    
    # Ask about CSV export
    export = input("\nExport results to CSV? (y/n) [y]: ").strip().lower()
    export_csv = export != "n"
    
    # Run selected analysis
    try:
        if choice in ["1", "3"]:
            run_ofr_analysis(client, start_date, end_date, export_csv)
        
        if choice in ["2", "3"]:
            run_constraint_analysis(client, start_date, end_date, export_csv)
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
