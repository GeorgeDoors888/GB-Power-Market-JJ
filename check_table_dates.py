#!/usr/bin/env python3
import requests
import urllib.parse

endpoint = "https://gb-power-market-jj.vercel.app/api/proxy-v2"

tables = ['bmrs_mid', 'bmrs_bod', 'bmrs_boalf', 'bmrs_indgen_iris', 'bmrs_inddem_iris']

for table in tables:
    sql = f"SELECT MAX(DATE(settlementDate)) as latest FROM `inner-cinema-476211-u9.uk_energy_prod.{table}`"
    url = f"{endpoint}?path=/query_bigquery_get&sql={urllib.parse.quote(sql)}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('success'):
            latest = data['data'][0]['latest'] if data['data'] else None
            print(f"✅ {table:25} Latest date: {latest}")
        else:
            print(f"❌ {table:25} Error: {data.get('error', 'Unknown')}")
    except Exception as e:
        print(f"❌ {table:25} Exception: {e}")
