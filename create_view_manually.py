#!/usr/bin/env python3
"""
Create v_bm_curtailment_classified view in BigQuery
"""
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

CREDENTIALS_FILE = '/home/george/inner-cinema-credentials.json'
BQ_PROJECT = 'inner-cinema-476211-u9'

creds = Credentials.from_service_account_file(
    CREDENTIALS_FILE,
    scopes=['https://www.googleapis.com/auth/bigquery']
)
client = bigquery.Client(project=BQ_PROJECT, credentials=creds, location='US')

# Read SQL and extract just the CREATE VIEW statement
with open('/home/george/GB-Power-Market-JJ/create_bm_curtailment_view.sql', 'r') as f:
    lines = f.readlines()

# Find CREATE VIEW and ending semicolon
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'CREATE OR REPLACE VIEW' in line:
        start_idx = i
    if start_idx is not None and ';' in line and 'ORDER BY' in lines[i-2:i+1].__str__():
        end_idx = i + 1
        break

if start_idx is None:
    print('❌ Could not find CREATE OR REPLACE VIEW statement')
    exit(1)

view_sql = ''.join(lines[start_idx:end_idx])

print('Creating v_bm_curtailment_classified view...')
print(f'SQL length: {len(view_sql)} characters')
print()

try:
    query_job = client.query(view_sql)
    query_job.result()
    print('✅ View created successfully!')
    print()
    print('View: inner-cinema-476211-u9.uk_energy_prod.v_bm_curtailment_classified')
    print()
except Exception as e:
    print(f'❌ Error: {e}')
    print()
    # Show first 50 lines of SQL for debugging
    print('First 50 lines of SQL:')
    for i, line in enumerate(view_sql.split('\n')[:50]):
        print(f'{i+1:3d}: {line}')
