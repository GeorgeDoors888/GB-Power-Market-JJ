from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser("~/.config/google-cloud/bigquery-credentials.json")
client = bigquery.Client(project="inner-cinema-476211-u9")

print("📊 Checking data availability:\n")

# Check directors table
query1 = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.companies_house.directors` WHERE is_active = TRUE"
result1 = list(client.query(query1).result())[0]
print(f"✅ Active directors: {result1.count:,}")

# Check companies table  
query2 = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.companies_house.companies`"
result2 = list(client.query(query2).result())[0]
print(f"✅ Companies: {result2.count:,}")

# Check land registry
query3 = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.companies_house.land_registry_uk_companies`"
result3 = list(client.query(query3).result())[0]
print(f"✅ UK property records: {result3.count:,}")

# Sample companies
print("\n📋 Sample companies:\n")
query4 = "SELECT company_number, company_name FROM `inner-cinema-476211-u9.companies_house.companies` LIMIT 5"
for row in client.query(query4).result():
    print(f"   {row.company_number}: {row.company_name}")

# Sample directors
print("\n👔 Sample active directors:\n")
query5 = "SELECT company_number, name, role FROM `inner-cinema-476211-u9.companies_house.directors` WHERE is_active = TRUE LIMIT 5"
for row in client.query(query5).result():
    print(f"   {row.company_number}: {row.name} ({row.role})")

# Sample property owners
print("\n🏠 Sample property owners:\n")
query6 = "SELECT proprietor_name_1, COUNT(*) as prop_count FROM `inner-cinema-476211-u9.companies_house.land_registry_uk_companies` GROUP BY proprietor_name_1 ORDER BY prop_count DESC LIMIT 10"
for row in client.query(query6).result():
    print(f"   {row.proprietor_name_1}: {row.prop_count} properties")
