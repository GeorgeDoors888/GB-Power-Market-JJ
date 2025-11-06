#!/usr/bin/env python3
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/opt/arbitrage/service-account.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

query = """
SELECT 
    MIN(DATE(settlementDate)) as min_date, 
    MAX(DATE(settlementDate)) as max_date, 
    COUNT(*) as total_rows,
    COUNT(DISTINCT dataset) as datasets
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
"""

print("🔍 Checking bmrs_mid date range...")
df = client.query(query).to_dataframe()
print(df.to_string())
