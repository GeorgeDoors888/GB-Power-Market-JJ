from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

# Check BOALF for last 3 days
query = f"""
SELECT
  CAST(settlementDate AS DATE) as date,
  MIN(settlementPeriod) as min_period,
  MAX(settlementPeriod) as max_period,
  COUNT(DISTINCT settlementPeriod) as num_periods,
  COUNT(*) as total_records
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
WHERE CAST(settlementDate AS DATE) >= '2025-12-10'
AND validation_flag = 'Valid'
GROUP BY date
ORDER BY date DESC
"""

df = client.query(query).to_dataframe()
print("BOALF Data Availability (last 3 days):")
print(df.to_string())
print("\n✅ Use date with 48 periods (or close to it)")
