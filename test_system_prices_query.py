#!/usr/bin/env python3
import requests
import urllib.parse
from datetime import datetime

endpoint = "https://gb-power-market-jj.vercel.app/api/proxy-v2"
today = datetime.now().strftime('%Y-%m-%d')

# Test System Prices query
sql_system_prices = f"""
    WITH prices AS (
      SELECT 
        DATE(settlementDate) AS d, 
        settlementPeriod AS sp,
        dataProvider,
        AVG(price) AS price
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
      WHERE DATE(settlementDate) = DATE('{today}')
      GROUP BY d, sp, dataProvider
    )
    SELECT 
      sp,
      MAX(CASE WHEN dataProvider = 'N2EXMIDP' THEN price END) AS ssp,
      MAX(CASE WHEN dataProvider = 'APXMIDP' THEN price END) AS sbp
    FROM prices
    GROUP BY sp
    ORDER BY sp
    LIMIT 5
"""

print("=" * 70)
print("Testing System Prices Query")
print("=" * 70)
print(f"Date: {today}")
print()

url = f"{endpoint}?path=/query_bigquery_get&sql={urllib.parse.quote(sql_system_prices)}"

try:
    print("Sending request...")
    response = requests.get(url, timeout=30)
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Success: {data.get('success')}")
    print(f"Error: {data.get('error')}")
    print()
    
    if data.get('data'):
        print(f"Rows returned: {len(data['data'])}")
        print("First few rows:")
        for row in data['data'][:5]:
            print(f"  SP {row.get('sp')}: SSP={row.get('ssp')}, SBP={row.get('sbp')}")
    else:
        print("No data returned")
        
except Exception as e:
    print(f"Exception: {e}")

print()
print("=" * 70)

# Let's try a simpler query to see if bmrs_mid exists and has data
simple_sql = f"""
SELECT COUNT(*) as cnt, MAX(settlementDate) as latest_date
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
"""

print("Testing simple bmrs_mid query...")
print()

url2 = f"{endpoint}?path=/query_bigquery_get&sql={urllib.parse.quote(simple_sql)}"

try:
    response2 = requests.get(url2, timeout=30)
    data2 = response2.json()
    
    print(f"Success: {data2.get('success')}")
    print(f"Error: {data2.get('error')}")
    
    if data2.get('data'):
        row = data2['data'][0]
        print(f"Total rows in bmrs_mid: {row.get('cnt')}")
        print(f"Latest date: {row.get('latest_date')}")
        
except Exception as e:
    print(f"Exception: {e}")
