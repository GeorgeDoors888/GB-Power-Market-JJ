from google.cloud import bigquery

client = bigquery.Client(project="jibber-jabber-knowledge")
table_list = [
    'elexon_demand_outturn',
    'generation_outturn',
    'bid_offer_acceptances',
    'system_warnings',
    'frequency'
]

print('Last processed date per table:')
for table in table_list:
    try:
        df = client.query(f'SELECT MAX(settlement_date) as last_date FROM `jibber-jabber-knowledge.uk_energy_prod.{table}`').result().to_dataframe()
        print(f'{table}:', df["last_date"].values[0])
    except Exception as e:
        print(f'{table}: ERROR -', e)
