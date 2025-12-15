from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser("~/.config/google-cloud/bigquery-credentials.json")

client = bigquery.Client(project="inner-cinema-476211-u9")

# List all tables in companies_house dataset
print("📋 Tables in companies_house dataset:")
tables = client.list_tables("inner-cinema-476211-u9.companies_house")
for table in tables:
    print(f"   - {table.table_id}")

print("\n" + "="*70 + "\n")

# Check directors table schema
try:
    table = client.get_table("inner-cinema-476211-u9.companies_house.directors")
    print("📊 Directors table schema:")
    for field in table.schema:
        print(f"   - {field.name} ({field.field_type})")
except Exception as e:
    print(f"❌ Directors table error: {e}")

print("\n" + "="*70 + "\n")

# Check land_registry tables
try:
    dataset_ref = client.dataset("companies_house")
    tables = list(client.list_tables(dataset_ref))
    land_tables = [t.table_id for t in tables if 'land' in t.table_id.lower() or 'property' in t.table_id.lower()]
    print(f"🏠 Land/Property related tables: {land_tables}")
    
    if land_tables:
        for table_id in land_tables[:3]:
            table = client.get_table(f"inner-cinema-476211-u9.companies_house.{table_id}")
            print(f"\n📊 {table_id} schema:")
            for field in table.schema[:10]:
                print(f"   - {field.name} ({field.field_type})")
except Exception as e:
    print(f"❌ Error: {e}")
