from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project="inner-cinema-476211-u9")
query = "SELECT column_name FROM inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'bmrs_fuelinst_iris' ORDER BY ordinal_position"
for row in client.query(query).result():
    print(row.column_name)
