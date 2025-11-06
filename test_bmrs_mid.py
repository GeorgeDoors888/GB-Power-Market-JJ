#!/usr/bin/env python3
"""Simple test script to check bmrs_mid data"""
import os
from google.cloud import bigquery

PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/opt/arbitrage/service-account.json'
client = bigquery.Client(project=PROJECT)

# Simple query to see what's in bmrs_mid
query = f"""
SELECT 
    dataset,
    settlementDate,
    settlementPeriod,
    price,
    volume
FROM `{PROJECT}.{DATASET}.bmrs_mid`
WHERE DATE(settlementDate) = '2025-11-05'
LIMIT 10
"""

print("🔍 Checking bmrs_mid structure...")
df = client.query(query).to_dataframe()
print(df.to_string())
print(f"\n✅ Rows: {len(df)}")
print(f"📊 Columns: {list(df.columns)}")
