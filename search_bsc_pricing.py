#!/usr/bin/env python3
"""
Search BigQuery for BSC/Elexon documentation about Final Demand Customer pricing
"""
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

creds = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/bigquery']
)
client = bigquery.Client(project=PROJECT_ID, credentials=creds, location='US')

print('='*100)
print('SEARCHING BIGQUERY FOR BSC/ELEXON TABLES')
print('='*100)
print()

# List all tables in dataset
tables = list(client.list_tables(DATASET))
print(f'Total tables in {DATASET}: {len(tables)}')
print()

# Look for BSC/settlement/demand related tables
bsc_tables = []
demand_tables = []
cost_tables = []

for table in tables:
    table_name = table.table_id.lower()
    if 'bsc' in table_name or 'settlement' in table_name or 'balance' in table_name:
        bsc_tables.append(table.table_id)
    if 'demand' in table_name or 'consumption' in table_name:
        demand_tables.append(table.table_id)
    if 'cost' in table_name or 'price' in table_name or 'charge' in table_name:
        cost_tables.append(table.table_id)

print('BSC/SETTLEMENT TABLES:')
for t in sorted(bsc_tables)[:20]:
    print(f'  • {t}')
print()

print('DEMAND/CONSUMPTION TABLES:')
for t in sorted(demand_tables)[:20]:
    print(f'  • {t}')
print()

print('COST/PRICE TABLES:')
for t in sorted(cost_tables)[:20]:
    print(f'  • {t}')
print()

# Query bmrs_costs for system prices structure
print('='*100)
print('SYSTEM PRICING STRUCTURE (bmrs_costs sample)')
print('='*100)
print()

query = f"""
SELECT 
    settlementDate,
    settlementPeriod,
    systemBuyPrice,
    systemSellPrice,
    (systemSellPrice - systemBuyPrice) as system_spread
FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
WHERE settlementDate >= '2025-11-01'
    AND settlementDate <= '2025-11-30'
    AND systemBuyPrice IS NOT NULL
    AND systemSellPrice IS NOT NULL
ORDER BY (systemSellPrice - systemBuyPrice) DESC
LIMIT 10
"""

df = client.query(query).to_dataframe()
print(df.to_string())
print()

# Check if there's a table with BSC charges/levies
print('='*100)
print('SEARCHING FOR BSC CHARGE TABLES')
print('='*100)
print()

charge_keywords = ['tnuos', 'duos', 'bsuos', 'triad', 'levy', 'charge', 'tariff']
charge_tables = []

for table in tables:
    table_name = table.table_id.lower()
    if any(keyword in table_name for keyword in charge_keywords):
        charge_tables.append(table.table_id)

if charge_tables:
    print('CHARGE/TARIFF TABLES FOUND:')
    for t in sorted(charge_tables):
        print(f'  • {t}')
        # Get sample of first table
        if t == charge_tables[0]:
            sample_query = f"""
            SELECT * 
            FROM `{PROJECT_ID}.{DATASET}.{t}`
            LIMIT 5
            """
            try:
                df_sample = client.query(sample_query).to_dataframe()
                print(f'\n  Sample from {t}:')
                print(df_sample.to_string())
                print()
            except Exception as e:
                print(f'  (Could not sample: {str(e)[:100]})')
else:
    print('No specific charge tables found')

print()
print('='*100)
print('FINAL DEMAND CUSTOMER PRICING NOTES')
print('='*100)
print("""
Final Demand Customers in UK electricity market:
  • Supply electricity directly to end consumers
  • Must pay BSUoS (Balancing Services Use of System)
  • Subject to TNUoS (Transmission Network Use of System)  
  • Must pay DUoS (Distribution Use of System)
  • Environmental levies: CCL, RO, FiT
  • System buy/sell prices from bmrs_costs

PPA (Power Purchase Agreement) for BESS:
  • Typically includes 'pass-through' costs
  • PPA price = Energy price + Network costs + Levies
  • For BtM (Behind-the-Meter): BESS displaces these costs
  • Revenue = (PPA price - import costs) × MWh supplied

Need to check BESS sheet for how PPA price is structured!
""")
