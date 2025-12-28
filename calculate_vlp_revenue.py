#!/usr/bin/env python3
"""
Calculate VLP (Virtual Lead Party) Revenue from BM Acceptances
Joins bmrs_boalf_complete with vlp_unit_ownership to aggregate revenue by VLP

Output: Creates mart.bm_value_by_vlp_sp table with VLP revenue by settlement period
"""

import os
from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
OUTPUT_TABLE = f"{PROJECT_ID}.{DATASET}.mart_bm_value_by_vlp_sp"

# Initialize BigQuery client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project=PROJECT_ID, location="US")

def calculate_vlp_revenue(start_date='2025-01-01', end_date=None):
    """
    Calculate VLP revenue from BM acceptances

    Args:
        start_date: Start date for revenue calculation (YYYY-MM-DD)
        end_date: End date (defaults to today)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"🔍 Calculating VLP Revenue from {start_date} to {end_date}")
    print("=" * 90)

    query = f"""
    CREATE OR REPLACE TABLE `{OUTPUT_TABLE}` AS

    WITH boalf_cleaned AS (
      SELECT
        -- Strip BM Unit prefix (2__FBPGM002 → FBPGM002)
        bmUnit as raw_bm_unit,
        REGEXP_EXTRACT(bmUnit, r'__(.+)$') as clean_bm_unit,
        acceptanceNumber,
        acceptanceTime,
        CAST(settlementDate AS DATE) as settlement_date,
        settlementPeriod,
        acceptanceType,
        -- Convert MW to MWh (MW × 0.5 for 30-min settlement period)
        acceptanceVolume * 0.5 AS accepted_mwh,
        acceptancePrice as price_gbp_per_mwh,
        -- Calculate gross revenue
        acceptanceVolume * 0.5 * acceptancePrice AS gross_value_gbp,
        -- Flags
        soFlag as is_so_acceptance,
        storFlag as is_stor_acceptance,
        rrFlag as is_replacement_reserve,
        deemedBoFlag as is_deemed_bo,
        -- Metadata
        _price_source,
        _matched_pairId,
        validation_flag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE validation_flag = 'Valid'
        AND CAST(settlementDate AS DATE) >= '{start_date}'
        AND CAST(settlementDate AS DATE) <= '{end_date}'
    ),

    boalf_with_vlp AS (
      SELECT
        b.*,
        v.vlp_name,
        -- Add party info
        p.party_id,
        p.party_name,
        p.bmu_count as vlp_total_units
      FROM boalf_cleaned b
      LEFT JOIN `{PROJECT_ID}.{DATASET}.vlp_unit_ownership` v
        ON b.clean_bm_unit = v.bm_unit
      LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_party` p
        ON v.vlp_name = p.party_name
      WHERE v.vlp_name IS NOT NULL  -- Only VLP units
    ),

    revenue_by_sp AS (
      SELECT
        settlement_date,
        settlementPeriod,
        vlp_name,
        party_id,
        party_name,
        -- Aggregate metrics
        COUNT(DISTINCT acceptanceNumber) as acceptance_count,
        SUM(accepted_mwh) as total_accepted_mwh,
        SUM(gross_value_gbp) as total_gross_value_gbp,
        AVG(price_gbp_per_mwh) as avg_price_gbp_per_mwh,
        MIN(price_gbp_per_mwh) as min_price_gbp_per_mwh,
        MAX(price_gbp_per_mwh) as max_price_gbp_per_mwh,
        -- Acceptance types
        SUM(CASE WHEN acceptanceType = 'OFFER' THEN accepted_mwh ELSE 0 END) as offer_mwh,
        SUM(CASE WHEN acceptanceType = 'BID' THEN accepted_mwh ELSE 0 END) as bid_mwh,
        -- SO/STOR flags
        SUM(CASE WHEN is_so_acceptance THEN 1 ELSE 0 END) as so_acceptance_count,
        SUM(CASE WHEN is_stor_acceptance THEN 1 ELSE 0 END) as stor_acceptance_count,
        -- Metadata
        MAX(vlp_total_units) as vlp_total_units,
        CURRENT_TIMESTAMP() as calculated_at
      FROM boalf_with_vlp
      GROUP BY settlement_date, settlementPeriod, vlp_name, party_id, party_name
    )

    SELECT * FROM revenue_by_sp
    ORDER BY settlement_date DESC, settlementPeriod, total_gross_value_gbp DESC
    """

    print(f"📊 Running query...")
    job = client.query(query)
    job.result()  # Wait for completion

    print(f"✅ Created table: {OUTPUT_TABLE}")

    # Get summary stats
    summary_query = f"""
    SELECT
      COUNT(DISTINCT vlp_name) as vlp_count,
      COUNT(DISTINCT settlement_date) as date_count,
      SUM(acceptance_count) as total_acceptances,
      ROUND(SUM(total_accepted_mwh), 2) as total_mwh,
      ROUND(SUM(total_gross_value_gbp), 2) as total_value_gbp,
      ROUND(AVG(avg_price_gbp_per_mwh), 2) as avg_price
    FROM `{OUTPUT_TABLE}`
    """
    summary = client.query(summary_query).to_dataframe()

    print("\n📈 Summary Statistics:")
    print("=" * 90)
    print(summary.to_string(index=False))

    # Top VLPs by revenue
    top_vlps_query = f"""
    SELECT
      vlp_name,
      COUNT(DISTINCT settlement_date) as days_active,
      SUM(acceptance_count) as acceptances,
      ROUND(SUM(total_accepted_mwh), 2) as total_mwh,
      ROUND(SUM(total_gross_value_gbp), 2) as total_value_gbp,
      ROUND(AVG(avg_price_gbp_per_mwh), 2) as avg_price
    FROM `{OUTPUT_TABLE}`
    GROUP BY vlp_name
    ORDER BY total_value_gbp DESC
    """
    top_vlps = client.query(top_vlps_query).to_dataframe()

    print("\n🏆 Top VLPs by Revenue:")
    print("=" * 90)
    print(top_vlps.to_string(index=False))

    return summary, top_vlps

if __name__ == "__main__":
    import sys

    # Parse command line args
    start_date = sys.argv[1] if len(sys.argv) > 1 else '2025-01-01'
    end_date = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        summary, top_vlps = calculate_vlp_revenue(start_date, end_date)
        print("\n✅ VLP revenue calculation complete!")
        print(f"💾 Output table: {OUTPUT_TABLE}")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
