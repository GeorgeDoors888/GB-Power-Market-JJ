#!/usr/bin/env python3
"""
Create VLP Dual KPI System: BOALF Accepted Prices + System Imbalance Prices

**CORRECTED VERSION** - BOALF table has NO price column, must join with BOD!

This script generates TWO separate KPIs for Dashboard V3:
1. BOALF Accepted Price - What VLP earns (requires BOD join for prices)
2. System Imbalance Price - Market baseline reference
3. VLP Premium - Difference between the two

NO volume calculations - unit prices (£/MWh) only!

Author: GB Power Market JJ
Date: 2025-12-04
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"

# VLP BMUs (update as needed)
VLP_UNITS = ['FBPGM002', 'FFSEN005']
DAYS_BACK = 7  # Last 7 days
HISTORICAL_CUTOFF = '2025-10-28'  # Last date in historical bmrs_boalf table

# Initialize BigQuery client
try:
    credentials = service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/bigquery']
    )
    client = bigquery.Client(
        credentials=credentials,
        project=PROJECT_ID,
        location=LOCATION
    )
    print(f"✅ Connected to BigQuery project: {PROJECT_ID}")
except Exception as e:
    print(f"❌ Failed to connect to BigQuery: {e}")
    sys.exit(1)

# ============================================================================
# QUERY 1: BOALF Accepted Prices (Primary VLP Revenue KPI)
# CRITICAL: BOALF has NO price column - must join with BOD to get prices!
# Uses UNION of historical + IRIS tables for complete coverage
# ============================================================================

boalf_query = f"""
WITH boalf_unified AS (
  -- Historical data (up to {HISTORICAL_CUTOFF})
  SELECT
    bmUnit,
    settlementDate,
    settlementPeriodFrom,
    settlementPeriodTo,
    acceptanceNumber,
    acceptanceTime,
    levelFrom,
    levelTo,
    soFlag,
    storFlag
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
    AND settlementDate <= DATE('{HISTORICAL_CUTOFF}')
  
  UNION ALL
  
  -- IRIS realtime data (after {HISTORICAL_CUTOFF})
  SELECT
    bmUnit,
    settlementDate,
    settlementPeriodFrom,
    settlementPeriodTo,
    acceptanceNumber,
    acceptanceTime,
    levelFrom,
    levelTo,
    soFlag,
    storFlag
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
    AND settlementDate > DATE('{HISTORICAL_CUTOFF}')
),
bod_unified AS (
  -- Historical BOD data
  SELECT
    bmUnit,
    settlementDate,
    settlementPeriod,
    offer,
    bid
  FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
    AND settlementDate <= DATE('{HISTORICAL_CUTOFF}')
  
  UNION ALL
  
  -- IRIS BOD data
  SELECT
    bmUnit,
    settlementDate,
    settlementPeriod,
    offer,
    bid
  FROM `{PROJECT_ID}.{DATASET}.bmrs_bod_iris`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
    AND settlementDate > DATE('{HISTORICAL_CUTOFF}')
),
boalf_acceptances AS (
  SELECT
    boalf.bmUnit,
    boalf.settlementDate,
    boalf.settlementPeriodFrom,
    boalf.settlementPeriodTo,
    boalf.acceptanceNumber,
    boalf.acceptanceTime,
    boalf.levelFrom,
    boalf.levelTo,
    boalf.soFlag,
    boalf.storFlag,
    CASE 
      WHEN boalf.levelTo > boalf.levelFrom THEN 'INCREASE'
      WHEN boalf.levelTo < boalf.levelFrom THEN 'DECREASE'
      ELSE 'NEUTRAL'
    END AS instruction_type,
    -- Join with BOD to get the accepted price
    CASE 
      WHEN boalf.levelTo > boalf.levelFrom THEN bod.offer  -- Generation increase = offer price
      WHEN boalf.levelTo < boalf.levelFrom THEN bod.bid    -- Generation decrease = bid price
      ELSE (bod.offer + bod.bid) / 2  -- Neutral = average
    END AS accepted_price_gbp_per_mwh,
    bod.offer AS submitted_offer_price,
    bod.bid AS submitted_bid_price,
    ABS(boalf.levelTo - boalf.levelFrom) AS volume_change_mw
  FROM boalf_unified boalf
  LEFT JOIN bod_unified bod
    ON boalf.bmUnit = bod.bmUnit
    AND boalf.settlementDate = bod.settlementDate
    -- Match BOD settlement period with BOALF period range
    AND bod.settlementPeriod >= boalf.settlementPeriodFrom
    AND bod.settlementPeriod <= boalf.settlementPeriodTo
  WHERE boalf.bmUnit IN UNNEST(@vlp_units)
)
SELECT *
FROM boalf_acceptances
WHERE accepted_price_gbp_per_mwh IS NOT NULL  -- Filter out acceptances with no matching BOD price
ORDER BY settlementDate DESC, settlementPeriodFrom DESC
"""

# ============================================================================
# QUERY 2: System Imbalance Prices (Market Reference KPI)
# ============================================================================

imbalance_query = f"""
SELECT
  settlementDate,
  settlementPeriod,
  price AS imbalance_price_gbp_per_mwh,  -- Single price column in bmrs_mid
  volume AS imbalance_volume_mwh
FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
ORDER BY settlementDate DESC, settlementPeriod DESC
"""

# ============================================================================
# Execute Queries
# ============================================================================

print("\n" + "=" * 80)
print("FETCHING VLP DUAL KPI DATA")
print("=" * 80)
print(f"VLP BMUs: {', '.join(VLP_UNITS)}")
print(f"Time Range: Last {DAYS_BACK} days")
print()

job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ArrayQueryParameter("vlp_units", "STRING", VLP_UNITS),
        bigquery.ScalarQueryParameter("days_back", "INT64", DAYS_BACK)
    ]
)

try:
    print("📊 Fetching BOALF accepted prices...")
    boalf_df = client.query(boalf_query, job_config=job_config).to_dataframe()
    print(f"   ✅ Retrieved {len(boalf_df)} BOALF acceptances")
    
    print("📊 Fetching system imbalance prices...")
    imbalance_df = client.query(imbalance_query, job_config=job_config).to_dataframe()
    print(f"   ✅ Retrieved {len(imbalance_df)} settlement periods")
except Exception as e:
    print(f"❌ Query failed: {e}")
    sys.exit(1)

# ============================================================================
# Validate Data
# ============================================================================

print("\n" + "=" * 80)
print("DATA VALIDATION")
print("=" * 80)

if len(boalf_df) == 0:
    print("⚠️ WARNING: No BOALF data found for VLP BMUs")
    print(f"   BMUs: {VLP_UNITS}")
    print(f"   Date range: Last {DAYS_BACK} days")
    print("   Possible reasons:")
    print("   1. VLP BMUs not active in this period")
    print("   2. No accepted balancing instructions")
    print("   3. BMU names incorrect")
    sys.exit(1)

if len(imbalance_df) == 0:
    print("⚠️ WARNING: No imbalance data found")
    sys.exit(1)

# Check for null prices
boalf_nulls = boalf_df['accepted_price_gbp_per_mwh'].isna().sum()
if boalf_nulls > 0:
    print(f"⚠️ WARNING: {boalf_nulls} BOALF acceptances have null prices")
    boalf_df = boalf_df.dropna(subset=['accepted_price_gbp_per_mwh'])
    print(f"   Dropped nulls, {len(boalf_df)} rows remain")

imbalance_nulls = imbalance_df['imbalance_avg_price_gbp_per_mwh'].isna().sum()
if imbalance_nulls > 0:
    print(f"⚠️ WARNING: {imbalance_nulls} settlement periods have null imbalance prices")
    imbalance_df = imbalance_df.dropna(subset=['imbalance_avg_price_gbp_per_mwh'])
    print(f"   Dropped nulls, {len(imbalance_df)} rows remain")

print("✅ Data validation passed")

# ============================================================================
# Calculate KPIs
# ============================================================================

print("\n" + "=" * 80)
print("📊 KPI 1: BOALF ACCEPTED PRICE (VLP Revenue Signal)")
print("=" * 80)

vlp_avg = boalf_df['accepted_price_gbp_per_mwh'].mean()
vlp_min = boalf_df['accepted_price_gbp_per_mwh'].min()
vlp_max = boalf_df['accepted_price_gbp_per_mwh'].max()
vlp_std = boalf_df['accepted_price_gbp_per_mwh'].std()
vlp_med = boalf_df['accepted_price_gbp_per_mwh'].median()

print(f"Average VLP Price:     £{vlp_avg:.2f}/MWh")
print(f"Median VLP Price:      £{vlp_med:.2f}/MWh")
print(f"Min VLP Price:         £{vlp_min:.2f}/MWh")
print(f"Max VLP Price:         £{vlp_max:.2f}/MWh")
print(f"Std Dev:               £{vlp_std:.2f}/MWh")
print(f"Volatility (CV):       {(vlp_std / vlp_avg * 100):.1f}%")
print(f"Total Acceptances:     {len(boalf_df)}")

# Breakdown by instruction type
increases = len(boalf_df[boalf_df['instruction_type'] == 'INCREASE'])
decreases = len(boalf_df[boalf_df['instruction_type'] == 'DECREASE'])
print(f"  - Increase Instructions: {increases}")
print(f"  - Decrease Instructions: {decreases}")

# Breakdown by BMU
print("\nBy BMU:")
for bmu in VLP_UNITS:
    bmu_df = boalf_df[boalf_df['bmUnit'] == bmu]
    if len(bmu_df) > 0:
        print(f"  {bmu}: {len(bmu_df)} acceptances, avg £{bmu_df['accepted_price_gbp_per_mwh'].mean():.2f}/MWh")
    else:
        print(f"  {bmu}: No acceptances")

# ============================================================================

print("\n" + "=" * 80)
print("📊 KPI 2: SYSTEM IMBALANCE PRICE (Market Baseline)")
print("=" * 80)

system_avg = imbalance_df['imbalance_price_gbp_per_mwh'].mean()
system_min = imbalance_df['imbalance_price_gbp_per_mwh'].min()
system_max = imbalance_df['imbalance_price_gbp_per_mwh'].max()
system_std = imbalance_df['imbalance_price_gbp_per_mwh'].std()
system_med = imbalance_df['imbalance_price_gbp_per_mwh'].median()

print(f"Average Imbalance Price:  £{system_avg:.2f}/MWh")
print(f"Median Imbalance Price:   £{system_med:.2f}/MWh")
print(f"Min Imbalance Price:      £{system_min:.2f}/MWh")
print(f"Max Imbalance Price:      £{system_max:.2f}/MWh")
print(f"Std Dev:                  £{system_std:.2f}/MWh")
print(f"Volatility (CV):          {(system_std / system_avg * 100):.1f}%")
print(f"Settlement Periods:       {len(imbalance_df)}")

# ============================================================================

print("\n" + "=" * 80)
print("📊 KPI 3: VLP PREMIUM (Value-Add Over Market)")
print("=" * 80)

premium = vlp_avg - system_avg
premium_pct = (premium / system_avg) * 100

print(f"VLP Premium:           £{premium:.2f}/MWh")
print(f"VLP Premium %:         {premium_pct:.1f}%")
print()

if premium > 0:
    print(f"✅ VLP earning £{premium:.2f}/MWh ABOVE market baseline ({premium_pct:.1f}% premium)")
elif premium < 0:
    print(f"⚠️ VLP earning £{abs(premium):.2f}/MWh BELOW market baseline ({abs(premium_pct):.1f}% discount)")
else:
    print("ℹ️ VLP earning exactly market baseline")

# ============================================================================
# Sanity Checks
# ============================================================================

print("\n" + "=" * 80)
print("SANITY CHECKS")
print("=" * 80)

warnings = []

# VLP price range check
if vlp_avg < 10 or vlp_avg > 200:
    warnings.append(f"Unusual VLP avg price: £{vlp_avg:.2f}/MWh (expected £10-200/MWh)")

# System price range check
if system_avg < 5 or system_avg > 300:
    warnings.append(f"Unusual system avg price: £{system_avg:.2f}/MWh (expected £5-300/MWh)")

# Premium range check
if abs(premium) > 100:
    warnings.append(f"Unusual VLP premium: £{premium:.2f}/MWh (expected £-50 to £50/MWh)")

# Volatility check
vlp_cv = vlp_std / vlp_avg * 100
if vlp_cv > 100:
    warnings.append(f"Very high VLP volatility: {vlp_cv:.1f}% (CV > 100%)")

if warnings:
    for warning in warnings:
        print(f"⚠️ {warning}")
else:
    print("✅ All values within expected ranges")

# ============================================================================
# Export Data
# ============================================================================

print("\n" + "=" * 80)
print("EXPORTING DATA")
print("=" * 80)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Export detailed BOALF data
boalf_file = f'vlp_boalf_prices_{DAYS_BACK}d_{timestamp}.csv'
boalf_df.to_csv(boalf_file, index=False)
print(f"✅ Exported BOALF data: {boalf_file} ({len(boalf_df)} rows)")

# Export detailed imbalance data
imbalance_file = f'system_imbalance_prices_{DAYS_BACK}d_{timestamp}.csv'
imbalance_df.to_csv(imbalance_file, index=False)
print(f"✅ Exported imbalance data: {imbalance_file} ({len(imbalance_df)} rows)")

# Export KPI summary (single row for Dashboard V3 import)
summary = {
    'timestamp': datetime.now().isoformat(),
    'days_analyzed': DAYS_BACK,
    'vlp_bmunits': ','.join(VLP_UNITS),
    'vlp_avg_price_gbp_per_mwh': vlp_avg,
    'vlp_median_price_gbp_per_mwh': vlp_med,
    'vlp_min_price_gbp_per_mwh': vlp_min,
    'vlp_max_price_gbp_per_mwh': vlp_max,
    'vlp_price_stddev': vlp_std,
    'vlp_price_volatility_pct': vlp_std / vlp_avg * 100,
    'vlp_total_acceptances': len(boalf_df),
    'system_avg_price_gbp_per_mwh': system_avg,
    'system_median_price_gbp_per_mwh': system_med,
    'system_min_price_gbp_per_mwh': system_min,
    'system_max_price_gbp_per_mwh': system_max,
    'system_price_stddev': system_std,
    'system_price_volatility_pct': system_std / system_avg * 100,
    'system_settlement_periods': len(imbalance_df),
    'vlp_premium_gbp_per_mwh': premium,
    'vlp_premium_percent': premium_pct
}

summary_df = pd.DataFrame([summary])
summary_file = f'vlp_kpi_summary_{DAYS_BACK}d_{timestamp}.csv'
summary_df.to_csv(summary_file, index=False)
print(f"✅ Exported KPI summary: {summary_file} (1 row for Dashboard V3)")

# ============================================================================
# Dashboard V3 Import Instructions
# ============================================================================

print("\n" + "=" * 80)
print("📋 DASHBOARD V3 IMPORT INSTRUCTIONS")
print("=" * 80)
print()
print("Option 1: Import detailed data (for sparklines)")
print(f"  1. Import {boalf_file} → Sheet name: VLPPRICE")
print(f"  2. Import {imbalance_file} → Sheet name: SYSPRICE")
print("  3. Update formulas:")
print("     F10 (VLP Avg):     =AVERAGE(VLPPRICE!G:G)")
print("     I10 (System Avg):  =AVERAGE(SYSPRICE!D:D)")
print("     J10 (Premium):     =F10-I10")
print()
print("Option 2: Import KPI summary (single-row import)")
print(f"  1. Import {summary_file} → Sheet name: VLP_KPI")
print("  2. Reference cells directly:")
print("     F10: =VLP_KPI!D2  (vlp_avg_price_gbp_per_mwh)")
print("     I10: =VLP_KPI!K2  (system_avg_price_gbp_per_mwh)")
print("     J10: =VLP_KPI!S2  (vlp_premium_gbp_per_mwh)")
print()
print("Option 3: Add sparklines (7-day trends)")
print("  Row 16: =SPARKLINE(VLPPRICE!G:G)")
print("  Row 17: =SPARKLINE(SYSPRICE!D:D)")
print("  Row 18: =SPARKLINE(VLPPRICE!G:G-SYSPRICE!D:D)  (premium trend)")

print("\n" + "=" * 80)
print("✅ VLP DUAL KPI GENERATION COMPLETE")
print("=" * 80)
