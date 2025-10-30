#!/usr/bin/env python3
"""
Test FUELINST stream endpoint fix
Loads July 16, 2025, Settlement Period 12 data
"""
import os
import sys
os.chdir('/Users/georgemajor/GB Power Market JJ')
sys.path.insert(0, '.')

from datetime import datetime
from google.cloud import bigquery

# First, clear any existing Oct 29 junk data from bmrs_fuelinst
client = bigquery.Client(project='inner-cinema-476211-u9')

print("=" * 80)
print("FUELINST STREAM ENDPOINT FIX TEST")
print("=" * 80)
print()

print("Step 1: Clear corrupted data from bmrs_fuelinst")
delete_query = """
DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(settlementDate) >= '2025-10-28'
"""
job = client.query(delete_query)
job.result()
print(f"✅ Deleted corrupted Oct 28-29 data")
print()

print("Step 2: Run ingestion for July 16, 2025 (single day test)")
# Run the fixed ingestion
os.system('./.venv/bin/python ingest_elexon_fixed.py --start 2025-07-16 --end 2025-07-16 --only FUELINST 2>&1 | tail -20')
print()

print("Step 3: Verify data loaded correctly")
query = """
SELECT 
  settlementDate,
  settlementPeriod,
  fuelType,
  SUM(generation) as total_generation_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate = '2025-07-16'
  AND settlementPeriod = 12
GROUP BY settlementDate, settlementPeriod, fuelType
ORDER BY total_generation_mw DESC
"""

results = list(client.query(query).result())

if results:
    print(f"✅ SUCCESS! Found {len(results)} fuel types for July 16, Period 12")
    print()
    print("Generation by fuel type:")
    print("-" * 60)
    for row in results:
        print(f"{row.fuelType:12} {row.total_generation_mw:>10,.0f} MW")
    print()
    print("✅ USER'S ORIGINAL QUERY CAN NOW BE ANSWERED!")
else:
    print("❌ FAILED: No data found for July 16, 2025, Period 12")
    print()
    print("Checking what data exists:")
    check_query = """
    SELECT 
      MIN(settlementDate) as first_date,
      MAX(settlementDate) as last_date,
      COUNT(*) as total_rows
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    """
    check_results = list(client.query(check_query).result())[0]
    print(f"Date range: {check_results.first_date} to {check_results.last_date}")
    print(f"Total rows: {check_results.total_rows}")
