#!/usr/bin/env python3
"""Comprehensive data verification for all years"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='inner-cinema-476211-u9')

print('🔍 COMPREHENSIVE DATA VERIFICATION')
print('=' * 80)
print()

# Check FUELINST (uses settlementDate)
print('📊 BMRS_FUELINST (Fuel Generation):')
for year in [2022, 2023, 2024, 2025]:
    query = f"""
    SELECT 
      COUNT(*) as row_count,
      MIN(settlementDate) as first_date,
      MAX(settlementDate) as last_date,
      COUNT(DISTINCT settlementDate) as distinct_days
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE EXTRACT(YEAR FROM settlementDate) = {year}
    """
    result = list(client.query(query).result())[0]
    if result['row_count'] > 0:
        print(f'  {year}: ✅ {result["row_count"]:>10,} rows | {result["distinct_days"]:>3} days | {result["first_date"]} to {result["last_date"]}')
    else:
        print(f'  {year}: ❌ No data')

print()

# Check FREQ (uses measurementTime)
print('📊 BMRS_FREQ (System Frequency):')
for year in [2022, 2023, 2024, 2025]:
    query = f"""
    SELECT 
      COUNT(*) as row_count,
      MIN(measurementTime) as first_time,
      MAX(measurementTime) as last_time
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
    WHERE EXTRACT(YEAR FROM measurementTime) = {year}
    """
    result = list(client.query(query).result())[0]
    if result['row_count'] > 0:
        print(f'  {year}: ✅ {result["row_count"]:>10,} rows | {result["first_time"]} to {result["last_time"]}')
    else:
        print(f'  {year}: ❌ No data')

print()

# Check BOD (uses settlementDate)
print('📊 BMRS_BOD (Bid-Offer Data):')
for year in [2022, 2023, 2024, 2025]:
    query = f"""
    SELECT 
      COUNT(*) as row_count,
      MIN(settlementDate) as first_date,
      MAX(settlementDate) as last_date
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
    WHERE EXTRACT(YEAR FROM settlementDate) = {year}
    """
    result = list(client.query(query).result())[0]
    if result['row_count'] > 0:
        print(f'  {year}: ✅ {result["row_count"]:>10,} rows | {result["first_date"]} to {result["last_date"]}')
    else:
        print(f'  {year}: ❌ No data')

print()
print('=' * 80)
print('✅ VERIFICATION COMPLETE')
print('=' * 80)
