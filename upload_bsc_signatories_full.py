from google.cloud import bigquery
import pandas as pd
import os
from datetime import datetime

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "bsc_signatories_full"

client = bigquery.Client(project=PROJECT_ID, location="US")

# Read the CSV (you uploaded it)
csv_path = "/Users/georgemajor/Downloads/ELEXON-BSC-Signatories_20251220162340.csv"

print(f"�� Reading CSV file...")
df = pd.read_csv(csv_path)

print(f"✅ Loaded {len(df)} parties")
print(f"📋 Columns: {list(df.columns)}")
print(f"\n🔍 Sample data:")
print(df.head(3))

# Add scraped timestamp
df['scraped_date'] = datetime.now()

# Upload to BigQuery
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

print(f"\n⬆️  Uploading to BigQuery: {table_id}")

job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE",  # Replace existing data
    schema=[
        bigquery.SchemaField("Party Name", "STRING"),
        bigquery.SchemaField("Party ID", "STRING"),
        bigquery.SchemaField("Party Address", "STRING"),
        bigquery.SchemaField("Party Roles", "STRING"),
        bigquery.SchemaField("Allocated OSM", "STRING"),
        bigquery.SchemaField("Telephone", "STRING"),
        bigquery.SchemaField("Email", "STRING"),
        bigquery.SchemaField("scraped_date", "TIMESTAMP"),
    ]
)

job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()

print(f"✅ Upload complete!")
print(f"📊 Rows uploaded: {len(df)}")
print(f"💾 Table: {table_id}")
