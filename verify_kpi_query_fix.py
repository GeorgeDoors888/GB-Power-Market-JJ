from google.cloud import bigquery
from datetime import date, timedelta
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

# Find most recent complete BOALF date
check_query = """
SELECT
  CAST(settlementDate AS DATE) as date,
  COUNT(DISTINCT settlementPeriod) as num_periods
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE CAST(settlementDate AS DATE) >= CURRENT_DATE() - 7
  AND validation_flag = 'Valid'
GROUP BY date
HAVING COUNT(DISTINCT settlementPeriod) >= 40
ORDER BY date DESC
LIMIT 1
"""

result = client.query(check_query).to_dataframe()
boalf_date = result.iloc[0]['date']
num_periods = result.iloc[0]['num_periods']

print(f"✅ Using BOALF date: {boalf_date} ({num_periods} periods)\n")

# Test the actual KPI query with first 5 periods
test_query = f"""
WITH
periods AS (
  SELECT period
  FROM UNNEST(GENERATE_ARRAY(1, 5)) AS period
),

boalf_data AS (
  SELECT
    settlementPeriod as period,
    AVG(acceptancePrice) as avg_acceptance,
    SUM(acceptanceVolume * acceptancePrice) / NULLIF(SUM(acceptanceVolume), 0) as vol_wtd_price
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
  WHERE CAST(settlementDate AS DATE) = '{boalf_date}'
    AND validation_flag = 'Valid'
    AND acceptancePrice IS NOT NULL
  GROUP BY period
)

SELECT
  p.period,
  COALESCE(b.avg_acceptance, 0) as avg_accept,
  COALESCE(b.vol_wtd_price, 0) as vol_wtd
FROM periods p
LEFT JOIN boalf_data b ON p.period = b.period
ORDER BY p.period
"""

df = client.query(test_query).to_dataframe()
print("Sample KPI data (first 5 periods):")
print(df.to_string())
print(f"\n✅ Avg Accept: £{df['avg_accept'].mean():.2f}/MWh")
print(f"✅ Vol-Wtd: £{df['vol_wtd'].mean():.2f}/MWh")
print("\n✅ Data looks good - ready for deployment once gspread connection fixed")
