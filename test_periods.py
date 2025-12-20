from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

# Check COSTS periods for Dec 17
query = f"""
SELECT
  MIN(settlementPeriod) as min_period,
  MAX(settlementPeriod) as max_period,
  COUNT(DISTINCT settlementPeriod) as num_periods
FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
WHERE CAST(settlementDate AS DATE) = '2025-12-17'
"""

df = client.query(query).to_dataframe()
print("COSTS Dec 17:")
print(df.to_string())

# Check BOALF periods for Dec 17
query2 = f"""
SELECT
  MIN(settlementPeriod) as min_period,
  MAX(settlementPeriod) as max_period,
  COUNT(DISTINCT settlementPeriod) as num_periods
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
WHERE CAST(settlementDate AS DATE) = '2025-12-17'
AND validation_flag = 'Valid'
"""

df2 = client.query(query2).to_dataframe()
print("\nBOALF Dec 17:")
print(df2.to_string())
