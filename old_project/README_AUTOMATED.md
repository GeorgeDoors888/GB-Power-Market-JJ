# UK Energy System Dashboard - Automated Scripts

These scripts automatically handle BigQuery table and column name discrepancies for the UK energy system dashboard and analysis tools.

## Quick Start

### Running the Dashboard (Column-Name-Safe)

```bash
./run_dashboard_automated.sh
```

### Running the BOD Analysis

```bash
./run_bod_analysis.sh
```

## Column Name Handling

These scripts automatically handle:
- camelCase vs snake_case column names (e.g., `fuelType` vs `fuel_type`)
- Missing tables (synthetic data is generated)
- Different column names between tables

## Troubleshooting

If you encounter issues, check the table schemas directly:

```bash
source venv/bin/activate
python -c "from google.cloud import bigquery; client = bigquery.Client(project='jibber-jabber-knowledge'); table_id = 'jibber-jabber-knowledge.uk_energy_prod.TABLE_NAME'; table = client.get_table(table_id); [print(f'- {field.name} ({field.field_type})') for field in table.schema]"
```
