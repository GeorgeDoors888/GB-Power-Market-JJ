#!/bin/bash
# NESO Data Loader Runner
# This script runs both the main data loader and the fix script

set -e

echo "Starting NESO data loading process..."
echo "======================================"

# Activate virtual environment
source venv/bin/activate

# Set variables
PROJECT_ID="jibber-jabber-knowledge"
DATASET_ID="uk_energy_prod"
BASE_DIR="neso_network_information"

echo "Step 1: Running main data loader..."
python neso_data_loader.py --project $PROJECT_ID --dataset $DATASET_ID --base-dir $BASE_DIR

echo "Step 2: Running fix script for special cases..."
python neso_data_loader_fix.py

echo "Step 3: Validating data load..."
python -c "
from google.cloud import bigquery
import pandas as pd

# Connect to BigQuery
client = bigquery.Client(project='$PROJECT_ID')

# Get all tables in the dataset
tables = list(client.list_tables('$DATASET_ID'))
neso_tables = [table.table_id for table in tables if table.table_id.startswith('neso_')]

print(f'Total tables in dataset: {len(tables)}')
print(f'Total NESO tables: {len(neso_tables)}')

# Sample rows from key tables
key_tables = [
    'neso_capacity_market_component',
    'neso_constraint_cost_24m',
    'neso_dno_license_areas',
    'neso_grid_supply_points'
]

for table in key_tables:
    try:
        query = f'SELECT COUNT(*) as row_count FROM `{PROJECT_ID}.{DATASET_ID}.{table}`'
        df = client.query(query).to_dataframe()
        print(f'{table}: {df.row_count.values[0]} rows')
    except Exception as e:
        print(f'Error querying {table}: {str(e)}')
"

echo "======================================"
echo "NESO data loading complete!"
