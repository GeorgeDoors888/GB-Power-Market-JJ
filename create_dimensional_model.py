#!/usr/bin/env python3
"""
Create Dimensional Model for VLP/VTP Analysis
Creates: dim_party, dim_bmu, fact_ops tables
Enables VP/VT role identification queries
"""

from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT_ID, location="US")

print("🏗️  BUILDING DIMENSIONAL MODEL FOR VLP/VTP ANALYSIS\n")
print("=" * 80)

# 1. CREATE dim_party (Party Dimension)
print("\n1️⃣ Creating dim_party from bsc_signatories_full...")
query_dim_party = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.dim_party` AS
SELECT
    -- Primary Key
    ROW_NUMBER() OVER (ORDER BY Party_Name) AS party_key,

    -- Natural Key
    Party_ID AS party_id,
    Party_Name AS party_name,

    -- Party Details
    Party_Address AS party_address,
    Party_Roles AS party_roles,
    Allocated_OSM AS allocated_osm,
    Telephone AS telephone,
    Email AS email,

    -- Role Flags (for easy filtering)
    REGEXP_CONTAINS(Party_Roles, r'(^|, )BP(,|$)') AS is_bsc_party,
    REGEXP_CONTAINS(Party_Roles, r'(^|, )TG(,|$)') AS is_generator,
    REGEXP_CONTAINS(Party_Roles, r'(^|, )TS(,|$)') AS is_trader_supplier,
    REGEXP_CONTAINS(Party_Roles, r'(^|, )VP(,|$)') AS is_vlp,
    REGEXP_CONTAINS(Party_Roles, r'(^|, )VT(,|$)') AS is_vtp,
    REGEXP_CONTAINS(Party_Roles, r'(^|, )TI(,|$)') AS is_interconnector,
    REGEXP_CONTAINS(Party_Roles, r'(^|, )EN(,|$)') AS is_ecvna,
    REGEXP_CONTAINS(Party_Roles, r'(^|, )DSO(,|$)') AS is_dso,
    REGEXP_CONTAINS(Party_Roles, r'(^|, )MV(,|$)') AS is_meter_operator,

    -- Multi-role classification
    ARRAY_LENGTH(SPLIT(Party_Roles, ', ')) AS role_count,
    CASE
        WHEN REGEXP_CONTAINS(Party_Roles, r'(^|, )(VP|VT)(,|$)') THEN 'Virtual Party'
        WHEN REGEXP_CONTAINS(Party_Roles, r'(^|, )TG(,|$)') THEN 'Generator'
        WHEN REGEXP_CONTAINS(Party_Roles, r'(^|, )TS(,|$)') THEN 'Supplier'
        WHEN REGEXP_CONTAINS(Party_Roles, r'(^|, )BP(,|$)') THEN 'BSC Party'
        ELSE 'Other'
    END AS primary_role_category,

    -- Metadata
    scraped_date AS source_date,
    CURRENT_TIMESTAMP() AS dim_created_at
FROM `{PROJECT_ID}.{DATASET}.bsc_signatories_full`
WHERE Party_Name IS NOT NULL
"""

try:
    client.query(query_dim_party).result()

    # Verify
    count = client.query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.dim_party`").to_dataframe()
    print(f"   ✅ Created dim_party: {count['cnt'].values[0]} parties")

    # Show VP/VT counts
    stats = client.query(f"""
        SELECT
            SUM(CAST(is_vlp AS INT64)) as vlp_count,
            SUM(CAST(is_vtp AS INT64)) as vtp_count,
            SUM(CAST(is_generator AS INT64)) as generator_count,
            SUM(CAST(is_trader_supplier AS INT64)) as supplier_count
        FROM `{PROJECT_ID}.{DATASET}.dim_party`
    """).to_dataframe()
    print(f"      • VLP (VP): {stats['vlp_count'].values[0]} parties")
    print(f"      • VTP (VT): {stats['vtp_count'].values[0]} parties")
    print(f"      • Generators (TG): {stats['generator_count'].values[0]} parties")
    print(f"      • Suppliers (TS): {stats['supplier_count'].values[0]} parties")

except Exception as e:
    print(f"   ❌ Error: {str(e)[:200]}")

# 2. CREATE dim_bmu (BM Unit Dimension)
print("\n2️⃣ Creating dim_bmu from bmu_metadata + registration...")
query_dim_bmu = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.dim_bmu` AS
SELECT
    -- Primary Key
    ROW_NUMBER() OVER (ORDER BY bm_unit_id) AS bmu_key,

    -- Natural Key
    bm_unit_id,

    -- BMU Details
    bm_unit_type,
    lead_party_name,
    national_grid_bmu_id,
    ngc_bmu_name,
    fpn_flag,
    effective_from,
    effective_to,

    -- Unit Classification
    CASE
        WHEN LOWER(bm_unit_type) LIKE '%stor%' OR LOWER(ngc_bmu_name) LIKE '%bess%' THEN 'Battery Storage'
        WHEN LOWER(bm_unit_type) LIKE '%wind%' THEN 'Wind'
        WHEN LOWER(bm_unit_type) LIKE '%solar%' OR LOWER(bm_unit_type) LIKE '%pv%' THEN 'Solar'
        WHEN LOWER(bm_unit_type) LIKE '%ccgt%' OR LOWER(bm_unit_type) LIKE '%gas%' THEN 'Gas'
        WHEN LOWER(bm_unit_type) LIKE '%coal%' THEN 'Coal'
        WHEN LOWER(bm_unit_type) LIKE '%nuclear%' THEN 'Nuclear'
        WHEN LOWER(bm_unit_type) LIKE '%hydro%' THEN 'Hydro'
        WHEN LOWER(bm_unit_type) LIKE '%interconnector%' THEN 'Interconnector'
        ELSE 'Other'
    END AS generation_type,

    -- Naming pattern flags
    bm_unit_id LIKE 'T_%' AS is_traditional_generator,
    bm_unit_id LIKE 'E_%' AS is_embedded_generator,
    bm_unit_id LIKE 'V_%' AS is_virtual_unit,
    bm_unit_id LIKE 'I_%' AS is_interconnector_unit,
    bm_unit_id LIKE '2_%' AS is_new_generation,

    -- Battery/Flex patterns
    bm_unit_id LIKE '%FLEX%' OR bm_unit_id LIKE '%BESS%' OR
    bm_unit_id LIKE '%FBPGM%' OR bm_unit_id LIKE '%FFSEN%' OR
    bm_unit_id LIKE '%STOR%' AS is_battery_storage,

    -- Metadata
    CURRENT_TIMESTAMP() AS dim_created_at
FROM `{PROJECT_ID}.{DATASET}.bmu_metadata`
WHERE bm_unit_id IS NOT NULL
"""

try:
    client.query(query_dim_bmu).result()

    # Verify
    count = client.query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.dim_bmu`").to_dataframe()
    print(f"   ✅ Created dim_bmu: {count['cnt'].values[0]} BM units")

    # Show battery/storage counts
    stats = client.query(f"""
        SELECT
            SUM(CAST(is_battery_storage AS INT64)) as battery_count,
            SUM(CAST(is_traditional_generator AS INT64)) as trad_gen_count,
            SUM(CAST(is_embedded_generator AS INT64)) as embedded_count,
            SUM(CAST(is_virtual_unit AS INT64)) as virtual_count
        FROM `{PROJECT_ID}.{DATASET}.dim_bmu`
    """).to_dataframe()
    print(f"      • Battery/Storage: {stats['battery_count'].values[0]} units")
    print(f"      • Traditional Generators: {stats['trad_gen_count'].values[0]} units")
    print(f"      • Embedded Generation: {stats['embedded_count'].values[0]} units")
    print(f"      • Virtual Units: {stats['virtual_count'].values[0]} units")

except Exception as e:
    print(f"   ❌ Error: {str(e)[:200]}")

# 3. CREATE fact_ops (Operational Facts from BOALF)
print("\n3️⃣ Creating fact_ops from bmrs_boalf_complete...")
query_fact_ops = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.fact_ops` AS
SELECT
    -- Fact Key
    CONCAT(
        CAST(DATE(acceptanceTime) AS STRING), '_',
        bmUnit, '_',
        CAST(acceptanceNumber AS STRING)
    ) AS fact_key,

    -- Foreign Keys (to be joined)
    bmUnit AS bmu_id,

    -- Time Dimensions
    DATE(acceptanceTime) AS acceptance_date,
    EXTRACT(YEAR FROM acceptanceTime) AS acceptance_year,
    EXTRACT(MONTH FROM acceptanceTime) AS acceptance_month,
    EXTRACT(DAY FROM acceptanceTime) AS acceptance_day,
    EXTRACT(HOUR FROM acceptanceTime) AS acceptance_hour,
    CAST(settlementDate AS DATE) AS settlement_date,
    settlementPeriod AS settlement_period,

    -- Acceptance Details
    acceptanceNumber,
    acceptanceTime,
    deemedBoFlag,
    soFlag,
    storFlag,
    rrFlag,
    acceptanceType,

    -- Measures (additive facts)
    acceptanceVolume AS volume_mwh,
    acceptancePrice AS price_gbp_mwh,
    acceptanceVolume * acceptancePrice AS revenue_gbp,

    -- Flags
    validation_flag,
    acceptanceType = 'OFFER' AS is_offer,
    acceptanceType = 'BID' AS is_bid,

    -- Data Quality
    CASE
        WHEN validation_flag = 'Valid' AND acceptancePrice > 0 AND acceptanceVolume > 0 THEN 'High'
        WHEN validation_flag = 'Valid' THEN 'Medium'
        ELSE 'Low'
    END AS data_quality,

    -- Metadata
    CURRENT_TIMESTAMP() AS fact_created_at

FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
WHERE validation_flag = 'Valid'
  AND acceptanceTime >= '2022-01-01'  -- Start of reliable data
"""

try:
    print("   ⏳ Processing 3.1M+ records (this may take 30-60 seconds)...")
    client.query(query_fact_ops).result()

    # Verify
    count = client.query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.fact_ops`").to_dataframe()
    print(f"   ✅ Created fact_ops: {count['cnt'].values[0]:,} acceptances")

    # Show summary stats
    stats = client.query(f"""
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT bmu_id) as unique_units,
            SUM(volume_mwh) as total_volume_mwh,
            SUM(revenue_gbp) as total_revenue_gbp,
            AVG(price_gbp_mwh) as avg_price,
            MIN(acceptance_date) as first_date,
            MAX(acceptance_date) as last_date
        FROM `{PROJECT_ID}.{DATASET}.fact_ops`
    """).to_dataframe()
    print(f"      • Unique BM Units: {stats['unique_units'].values[0]:,}")
    print(f"      • Total Volume: {stats['total_volume_mwh'].values[0]:,.0f} MWh")
    print(f"      • Total Revenue: £{stats['total_revenue_gbp'].values[0]:,.0f}")
    print(f"      • Average Price: £{stats['avg_price'].values[0]:.2f}/MWh")
    print(f"      • Date Range: {stats['first_date'].values[0]} to {stats['last_date'].values[0]}")

except Exception as e:
    print(f"   ❌ Error: {str(e)[:400]}")

print("\n" + "=" * 80)
print("\n✅ DIMENSIONAL MODEL COMPLETE!\n")
print("You can now run your original query:")
print("""
SELECT
  f.*,
  b.lead_party_name,
  p.party_id,
  p.party_roles,
  p.is_vlp,
  p.is_vtp
FROM fact_ops f
LEFT JOIN dim_bmu b
  ON f.bmu_id = b.bm_unit_id
LEFT JOIN dim_party p
  ON LOWER(TRIM(b.lead_party_name)) = LOWER(TRIM(p.party_name))
WHERE p.is_vlp = TRUE OR p.is_vtp = TRUE
LIMIT 100;
""")

print("\n💡 Quick Analysis Queries:")
print("  • VLP Revenue: SELECT party_name, SUM(revenue_gbp) FROM fact_ops f JOIN dim_bmu b JOIN dim_party p WHERE is_vlp=TRUE")
print("  • Battery Units: SELECT * FROM dim_bmu WHERE is_battery_storage=TRUE")
print("  • Multi-role Parties: SELECT * FROM dim_party WHERE role_count > 3")
