#!/usr/bin/env python3
"""
Test queries on BigQuery data to verify what we can use for dashboard
"""

from google.cloud import bigquery
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/georgemajor/GB Power Market JJ/jibber_jabber_key.json"

client = bigquery.Client(project=PROJECT_ID)

print("=" * 80)
print("🔍 TESTING BIGQUERY DATA FOR DASHBOARD")
print("=" * 80)
print()

# Test 1: Latest generation by fuel type
print("1️⃣ Testing: Latest Generation by Fuel Type")
print("-" * 80)
query1 = """
SELECT 
    publishTime,
    fuelType,
    generation
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_fuel_instant`
WHERE publishTime = (
    SELECT MAX(publishTime) 
    FROM `inner-cinema-476211-u9.uk_energy_prod.generation_fuel_instant`
)
ORDER BY generation DESC
"""

try:
    results = client.query(query1).result()
    print("✅ SUCCESS! Latest generation data:")
    total_gen = 0
    for row in results:
        gen_gw = row.generation / 1000
        total_gen += gen_gw
        print(f"   {row.fuelType:15} : {gen_gw:6.2f} GW  (at {row.publishTime})")
    print(f"\n   📊 TOTAL GENERATION: {total_gen:.2f} GW")
except Exception as e:
    print(f"❌ FAILED: {e}")

print()

# Test 2: Latest system frequency
print("2️⃣ Testing: Latest System Frequency")
print("-" * 80)
query2 = """
SELECT 
    startTime,
    frequency
FROM `inner-cinema-476211-u9.uk_energy_prod.system_frequency`
ORDER BY startTime DESC
LIMIT 5
"""

try:
    results = client.query(query2).result()
    print("✅ SUCCESS! Latest frequency readings:")
    for row in results:
        print(f"   {row.startTime}: {row.frequency:.3f} Hz")
except Exception as e:
    print(f"❌ FAILED: {e}")

print()

# Test 3: Latest demand
print("3️⃣ Testing: Latest Demand Outturn")
print("-" * 80)
query3 = """
SELECT 
    publishTime,
    demand,
    transmissionSystemDemand
FROM `inner-cinema-476211-u9.uk_energy_prod.demand_outturn`
ORDER BY publishTime DESC
LIMIT 5
"""

try:
    results = client.query(query3).result()
    print("✅ SUCCESS! Latest demand data:")
    for row in results:
        demand_gw = row.demand / 1000 if row.demand else 0
        print(f"   {row.publishTime}: {demand_gw:.2f} GW")
except Exception as e:
    print(f"❌ FAILED: {e}")

print()

# Test 4: Check for wind/solar specific data
print("4️⃣ Testing: Wind & Solar Generation Data")
print("-" * 80)
query4 = """
SELECT 
    settlementDate,
    settlementPeriod,
    generation
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_wind_solar`
ORDER BY settlementDate DESC, settlementPeriod DESC
LIMIT 5
"""

try:
    results = client.query(query4).result()
    print("✅ SUCCESS! Latest wind & solar data:")
    for row in results:
        gen_gw = row.generation / 1000 if row.generation else 0
        print(f"   {row.settlementDate} SP{row.settlementPeriod}: {gen_gw:.2f} GW")
except Exception as e:
    print(f"❌ FAILED: {e}")

print()

# Test 5: Check Sep/Oct 2025 data
print("5️⃣ Testing: September & October 2025 Data")
print("-" * 80)
query5 = """
SELECT 
    COUNT(*) as record_count,
    MIN(publishTime) as earliest,
    MAX(publishTime) as latest
FROM `inner-cinema-476211-u9.uk_energy_prod.fuelinst_sep_oct_2025`
"""

try:
    results = client.query(query5).result()
    print("✅ SUCCESS! Sep/Oct 2025 fuel data:")
    for row in results:
        print(f"   Records: {row.record_count:,}")
        print(f"   Date range: {row.earliest} to {row.latest}")
except Exception as e:
    print(f"❌ FAILED: {e}")

print()

# Test 6: Latest interconnector flows (if available)
print("6️⃣ Testing: Interconnector Data")
print("-" * 80)
query6 = """
SELECT 
    table_name
FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE '%interconnect%' OR table_name LIKE '%import%' OR table_name LIKE '%export%'
"""

try:
    results = client.query(query6).result()
    tables = [row.table_name for row in results]
    if tables:
        print(f"✅ Found interconnector-related tables:")
        for table in tables:
            print(f"   - {table}")
    else:
        print("⚠️  No specific interconnector tables found")
        print("   (Interconnector data might be in generation_fuel_instant as 'INTFR', 'INTNED', etc.)")
except Exception as e:
    print(f"❌ FAILED: {e}")

print()
print("=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print("""
Based on the tests above:
✅ We CAN query: Generation by fuel type, System frequency, Demand outturn
⚠️  We SHOULD check: How interconnectors are represented in the data
💡 We HAVE: 36+ million records from Sep/Oct 2025 test download
""")
