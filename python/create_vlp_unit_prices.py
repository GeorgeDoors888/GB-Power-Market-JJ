#!/usr/bin/env python3
"""
Calculate VLP unit prices (£/MWh) from BOD+BOALF joined data.

This script:
1. Joins BOALF (acceptances) with BOD (submitted prices)
2. Determines actual accepted price based on instruction direction
3. Calculates average VLP unit prices (NO volume multiplication)
4. Exports to CSV for dashboard import

NO TOTAL REVENUE CALCULATION - Just unit prices (£/MWh)
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
VLP_UNITS = ['FBPGM002', 'FFSEN005']  # Update with your VLP BMUs
DAYS_LOOKBACK = 30

# Use service account credentials
credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/bigquery']
)
client = bigquery.Client(credentials=credentials, project=PROJECT_ID, location="US")

print("=" * 70)
print("VLP UNIT PRICE CALCULATOR")
print("=" * 70)
print(f"Project: {PROJECT_ID}")
print(f"VLP BMUs: {', '.join(VLP_UNITS)}")
print(f"Lookback Period: {DAYS_LOOKBACK} days")
print("=" * 70)

# Main query - Join BOALF acceptances with BOD prices
# CRITICAL: BOALF uses settlementPeriodFrom/To (range), BOD uses settlementPeriod (single)
query = f"""
WITH accepted_prices AS (
  SELECT
    boalf.bmUnit,
    boalf.settlementDate,
    boalf.settlementPeriodFrom,
    boalf.settlementPeriodTo,
    boalf.acceptanceNumber,
    boalf.acceptanceTime,
    boalf.timeFrom,
    boalf.timeTo,
    boalf.levelFrom,
    boalf.levelTo,
    boalf.soFlag,
    boalf.storFlag,
    bod.offer AS offer_price,
    bod.bid AS bid_price,
    -- Determine which price was actually accepted based on instruction direction
    CASE 
      WHEN boalf.levelFrom < boalf.levelTo THEN bod.offer  -- Increase generation (use offer)
      WHEN boalf.levelFrom > boalf.levelTo THEN bod.bid    -- Decrease generation (use bid)
      ELSE (bod.offer + bod.bid) / 2  -- No net change (use average)
    END AS accepted_price_gbp_per_mwh,
    CASE 
      WHEN boalf.levelFrom < boalf.levelTo THEN 'OFFER_ACCEPTED'
      WHEN boalf.levelFrom > boalf.levelTo THEN 'BID_ACCEPTED'
      ELSE 'NEUTRAL'
    END AS instruction_type
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf` boalf
  LEFT JOIN `{PROJECT_ID}.{DATASET}.bmrs_bod` bod
    ON boalf.bmUnit = bod.bmUnit
    AND boalf.settlementDate = bod.settlementDate
    -- Join on period range: BOD's single period must be within BOALF's period range
    AND bod.settlementPeriod >= boalf.settlementPeriodFrom
    AND bod.settlementPeriod <= boalf.settlementPeriodTo
  WHERE boalf.bmUnit IN UNNEST(@vlp_units)
    AND boalf.settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_lookback DAY)
),
imbalance_prices AS (
  SELECT
    settlementDate,
    settlementPeriod,
    price AS imbalance_price_gbp_per_mwh
  FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_lookback DAY)
)
SELECT
  ap.bmUnit,
  ap.settlementDate,
  ap.settlementPeriodFrom,
  ap.settlementPeriodTo,
  ap.acceptanceTime,
  ap.timeFrom,
  ap.timeTo,
  ap.accepted_price_gbp_per_mwh AS vlp_unit_price,
  ap.instruction_type,
  ap.offer_price AS submitted_offer,
  ap.bid_price AS submitted_bid,
  ap.soFlag,
  ap.storFlag,
  ip.imbalance_price_gbp_per_mwh AS system_imbalance_price,
  ap.accepted_price_gbp_per_mwh - ip.imbalance_price_gbp_per_mwh AS vlp_premium_over_imbalance
FROM accepted_prices ap
LEFT JOIN imbalance_prices ip
  ON ap.settlementDate = ip.settlementDate
  AND ip.settlementPeriod >= ap.settlementPeriodFrom
  AND ip.settlementPeriod <= ap.settlementPeriodTo
WHERE ap.accepted_price_gbp_per_mwh IS NOT NULL
ORDER BY ap.settlementDate DESC, ap.settlementPeriodFrom DESC, ap.acceptanceTime DESC
"""

print("\n⏳ Querying BigQuery (BOD + BOALF join)...")

try:
    df = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("vlp_units", "STRING", VLP_UNITS),
                bigquery.ScalarQueryParameter("days_lookback", "INT64", DAYS_LOOKBACK)
            ]
        )
    ).to_dataframe()
    
    print(f"✅ Retrieved {len(df)} accepted instructions with prices\n")
    
    if len(df) == 0:
        print("❌ NO DATA FOUND")
        print("\nPossible reasons:")
        print("  1. VLP BMUs not active in selected period")
        print("  2. No accepted instructions (no balancing activity)")
        print("  3. BOD/BOALF join failed (check BMU names match)")
        exit(1)
    
    # Calculate KPIs
    print("=" * 70)
    print("VLP UNIT PRICE KPIs")
    print("=" * 70)
    
    # Overall statistics
    print(f"\n📊 Accepted Price Statistics:")
    print(f"   Average:  £{df['vlp_unit_price'].mean():.2f}/MWh")
    print(f"   Median:   £{df['vlp_unit_price'].median():.2f}/MWh")
    print(f"   Min:      £{df['vlp_unit_price'].min():.2f}/MWh")
    print(f"   Max:      £{df['vlp_unit_price'].max():.2f}/MWh")
    print(f"   Std Dev:  £{df['vlp_unit_price'].std():.2f}/MWh")
    
    # Breakdown by instruction type
    print(f"\n📈 Instruction Type Breakdown:")
    for instr_type in df['instruction_type'].unique():
        subset = df[df['instruction_type'] == instr_type]
        print(f"   {instr_type}: {len(subset)} acceptances, Avg £{subset['vlp_unit_price'].mean():.2f}/MWh")
    
    # Imbalance comparison
    if df['system_imbalance_price'].notna().any():
        print(f"\n💰 VLP Premium Analysis:")
        print(f"   Avg System Imbalance Price: £{df['system_imbalance_price'].mean():.2f}/MWh")
        print(f"   Avg VLP Premium:           £{df['vlp_premium_over_imbalance'].mean():.2f}/MWh")
        print(f"   Premium %:                  {(df['vlp_premium_over_imbalance'].mean() / df['system_imbalance_price'].mean() * 100):.1f}%")
    
    # Validation checks
    print(f"\n✅ Data Quality Checks:")
    avg_price = df['vlp_unit_price'].mean()
    if 10 <= avg_price <= 200:
        print(f"   Price range: REALISTIC (£{avg_price:.2f}/MWh within £10-200)")
    else:
        print(f"   ⚠️ Price range: UNUSUAL (£{avg_price:.2f}/MWh outside £10-200)")
    
    join_rate = len(df[df['vlp_unit_price'].notna()]) / len(df) * 100
    if join_rate >= 95:
        print(f"   BOD/BOALF join: EXCELLENT ({join_rate:.1f}% success)")
    elif join_rate >= 80:
        print(f"   BOD/BOALF join: GOOD ({join_rate:.1f}% success)")
    else:
        print(f"   ⚠️ BOD/BOALF join: POOR ({join_rate:.1f}% success - check data)")
    
    # Export to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'vlp_unit_prices_{DAYS_LOOKBACK}d_{timestamp}.csv'
    df.to_csv(filename, index=False)
    
    print(f"\n📁 Export:")
    print(f"   File: {filename}")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    
    # Sample output
    print(f"\n📋 Sample Data (first 5 rows):")
    print(df[['bmUnit', 'settlementDate', 'settlementPeriodFrom', 'settlementPeriodTo', 
              'vlp_unit_price', 'instruction_type', 'vlp_premium_over_imbalance']].head().to_string(index=False))
    
    print("\n" + "=" * 70)
    print("✅ VLP UNIT PRICE CALCULATION COMPLETE")
    print("=" * 70)
    print(f"\n🎯 KEY VALUE: Average VLP Price = £{df['vlp_unit_price'].mean():.2f}/MWh")
    print("   (This is the value to display on Dashboard V3)")
    print("\n❌ DO NOT multiply by volume to get total revenue!")
    print("   Volume is project-specific - dashboard shows unit prices only")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("  1. Check credentials: inner-cinema-credentials.json exists")
    print("  2. Check VLP BMU names match BigQuery data")
    print("  3. Check date range has data (try increasing DAYS_LOOKBACK)")
    print("  4. Verify BOD and BOALF tables exist in dataset")
    exit(1)
