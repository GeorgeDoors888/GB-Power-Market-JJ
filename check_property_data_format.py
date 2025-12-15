from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser("~/.config/google-cloud/bigquery-credentials.json")

client = bigquery.Client(project="inner-cinema-476211-u9")

# Check sample property data
query = """
SELECT 
    proprietor_name_1,
    title_number,
    property_address,
    county
FROM `inner-cinema-476211-u9.companies_house.land_registry_uk_companies`
WHERE proprietor_name_1 IS NOT NULL
LIMIT 20
"""

print("📋 Sample property ownership data:\n")
results = client.query(query).result()
for i, row in enumerate(results, 1):
    print(f"{i}. {row.proprietor_name_1}")
    print(f"   Title: {row.title_number}, Address: {row.property_address[:50] if row.property_address else 'N/A'}\n")
