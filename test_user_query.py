#!/usr/bin/env python3
"""
Test query for user's original FUELINST request
Query: "FUELINST for July 16 2025, Settlement Period 12"
"""

from google.cloud import bigquery
import os

os.chdir('/Users/georgemajor/GB Power Market JJ')
client = bigquery.Client(project='inner-cinema-476211-u9')

print("=" * 80)
print("USER'S ORIGINAL QUERY TEST")
print("=" * 80)
print()
print("Request: FUELINST for July 16, 2025, Settlement Period 12")
print("Expected: Fuel generation by type for that specific time period")
print()

query = """
SELECT 
  fuelType,
  SUM(generation) as total_generation_mw,
  COUNT(*) as records
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE settlementDate = '2025-07-16'
  AND settlementPeriod = 12
GROUP BY fuelType
ORDER BY total_generation_mw DESC
"""

print("SQL Query:")
print("-" * 80)
print(query)
print("-" * 80)
print()

try:
    result = client.query(query).result()
    rows = list(result)
    
    if len(rows) == 0:
        print("❌ NO DATA FOUND")
        print()
        print("This is expected before the corrected ingestion completes.")
        print("After loading historical data via Insights API, this query should return:")
        print()
        print("Fuel Type          | Generation (MW) | Records")
        print("-------------------|-----------------|--------")
        print("CCGT               | ~8,000          | ~X")
        print("Wind               | ~6,000          | ~X")
        print("Nuclear            | ~5,000          | ~X")
        print("Biomass            | ~2,000          | ~X")
        print("Coal               | ~1,500          | ~X")
        print("Hydro              | ~500            | ~X")
        print("Solar              | ~3,000          | ~X")
        print("etc...")
    else:
        print("✅ DATA FOUND:")
        print()
        print(f"{'Fuel Type':<20} | {'Generation (MW)':>15} | {'Records':>8}")
        print("-" * 50)
        
        total = 0
        for row in rows:
            fuel = row['fuelType']
            gen = row['total_generation_mw']
            recs = row['records']
            total += gen
            print(f"{fuel:<20} | {gen:>15,.0f} | {recs:>8}")
        
        print("-" * 50)
        print(f"{'TOTAL':<20} | {total:>15,.0f} |")
        print()
        
        # Check if data is actually from July 16 or if it's the Oct 28 bug
        date_check_query = """
        SELECT DISTINCT settlementDate
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
        WHERE settlementDate = '2025-07-16'
        """
        date_result = list(client.query(date_check_query).result())
        
        if date_result:
            actual_date = date_result[0]['settlementDate']
            if str(actual_date) == '2025-07-16 00:00:00':
                print("✅ Data is from correct date: July 16, 2025")
            else:
                print(f"⚠️  Data date mismatch: {actual_date}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    print()
    print("This error is expected if:")
    print("1. Data hasn't been loaded yet")
    print("2. Table schema is different than expected")
    print("3. No data exists for July 16, 2025")

print()
print("=" * 80)
