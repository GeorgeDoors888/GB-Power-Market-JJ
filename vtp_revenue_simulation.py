# ================================================================
# VTP Revenue Simulation - Settlement Period Level
# ================================================================
# Requirements: google-cloud-bigquery, pandas
# Auth: service account with access to inner-cinema-476211-u9
# ================================================================

from google.cloud import bigquery
import pandas as pd

# --- CONFIGURATION ---
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SCRP = 98.0        # Supplier Compensation Reference Price (Elexon v2.0)
BASELINE_PRICE = 90.0  # Supplier wholesale hedge assumption
DELTA_Q = 5.0          # Deviation in MWh per SP
EFFICIENCY = 0.9

# --- INITIALISE CLIENT ---
client = bigquery.Client(project=PROJECT_ID)

# --- QUERY (joins MID and BOD on date & settlement period) ---
query = f"""
WITH joined AS (
  SELECT
    mid.settlementDate,
    mid.settlementPeriod,
    AVG(mid.price) AS market_price,
    AVG(bod.offer) AS offer_price,
    AVG(bod.bid)   AS bid_price
  FROM `{PROJECT_ID}.{DATASET}.bmrs_mid` AS mid
  JOIN `{PROJECT_ID}.{DATASET}.bmrs_bod` AS bod
  USING(settlementDate, settlementPeriod)
  WHERE settlementDate BETWEEN '2025-11-01' AND '2025-11-30'
  GROUP BY settlementDate, settlementPeriod
),
calc AS (
  SELECT *,
    CASE
      WHEN offer_price > bid_price THEN 'short'
      ELSE 'long'
    END AS system_state,
    CASE
      WHEN offer_price > bid_price THEN
        {DELTA_Q} * ((offer_price - market_price) - {SCRP})
      ELSE
        {DELTA_Q} * ((market_price - bid_price) + {SCRP})
    END AS vtp_revenue
  FROM joined
)
SELECT * FROM calc
ORDER BY settlementDate, settlementPeriod
"""

# --- RUN QUERY ---
print("⏳ Running BigQuery join between bmrs_mid and bmrs_bod...")
df = client.query(query).to_dataframe()
print(f"✅ Retrieved {len(df)} settlement periods")

# --- DAILY & WEEKLY AGGREGATION ---
df['settlementDate'] = pd.to_datetime(df['settlementDate'])
daily = (
    df.groupby(['settlementDate', 'system_state'])
      .agg(avg_SBP=('offer_price','mean'),
           avg_SSP=('bid_price','mean'),
           avg_MID=('market_price','mean'),
           total_vtp_revenue=('vtp_revenue','sum'))
      .reset_index()
)

weekly = (
    daily.groupby(pd.Grouper(key='settlementDate', freq='W-MON'))
    ['total_vtp_revenue'].sum().reset_index()
)

# --- APPLY EFFICIENCY & OUTPUT ---
daily['net_revenue'] = daily['total_vtp_revenue'] * EFFICIENCY
weekly['net_revenue'] = weekly['total_vtp_revenue'] * EFFICIENCY

print("\n--- Daily summary ---")
print(daily.round(2))

print("\n--- Weekly totals ---")
print(weekly.round(2))

# --- SAVE RESULTS ---
daily.to_csv("vtp_revenue_daily.csv", index=False)
weekly.to_csv("vtp_revenue_weekly.csv", index=False)

print("\n✅ CSV files saved:")
print("  - vtp_revenue_daily.csv")
print("  - vtp_revenue_weekly.csv")
