#!/usr/bin/env python3
"""Test the outages query to see what it returns"""

from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/bigquery']
)
client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")

query = f"""
WITH uk_capacity AS (
    SELECT SUM(generationcapacity) as total_uk_mw
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE generationcapacity > 0
),
latest_revisions AS (
    SELECT
        affectedUnit,
        MAX(revisionNumber) as max_revision,
        MAX(eventStartTime) as latest_event_start
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
    WHERE eventStatus = 'Active'
      AND (normalCapacity - availableCapacity) >= 50
      AND eventEndTime > CURRENT_TIMESTAMP()
    GROUP BY affectedUnit
),
current_outages AS (
    SELECT
        u.affectedUnit,
        u.eventStartTime,
        u.assetName,
        u.fuelType,
        u.normalCapacity,
        u.availableCapacity,
        (u.normalCapacity - u.availableCapacity) as unavailable_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
    INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_revision
    WHERE u.eventStatus = 'Active'
      AND u.eventEndTime > CURRENT_TIMESTAMP()
)
SELECT
    c.affectedUnit as bm_unit,
    COALESCE(bmu.bmunitname, c.assetName, c.affectedUnit) as plant_name,
    c.fuelType as fuel_type,
    CAST(c.unavailable_mw AS INT64) as mw_lost,
    ROUND((c.unavailable_mw / uk.total_uk_mw) * 100, 2) as pct_lost,
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', c.eventStartTime) as start_time
FROM current_outages c
CROSS JOIN uk_capacity uk
LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
    ON c.affectedUnit = bmu.elexonbmunit OR c.affectedUnit = bmu.nationalgridbmunit
ORDER BY c.unavailable_mw DESC
LIMIT 15
"""

print("Executing query...")
df = client.query(query).to_dataframe()

print(f"\nReturned {len(df)} rows")
print("\nChecking for duplicates:")
duplicates = df[df.duplicated(['bm_unit'], keep=False)]
if len(duplicates) > 0:
    print(f"❌ FOUND {len(duplicates)} DUPLICATE ROWS:")
    print(duplicates[['bm_unit', 'plant_name', 'mw_lost']].to_string())
else:
    print("✅ NO DUPLICATES")

print("\nFull results:")
print(df[['bm_unit', 'plant_name', 'mw_lost', 'pct_lost']].to_string())
