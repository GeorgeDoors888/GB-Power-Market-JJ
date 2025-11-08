#!/usr/bin/env python3
import requests
import urllib.parse

RAILWAY_URL = "https://jibber-jabber-production.up.railway.app"
TOKEN = "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"

# Simple test to see if bmrs_mid exists
sql = "SELECT COUNT(*) as cnt FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` LIMIT 1"

url = f"{RAILWAY_URL}/query_bigquery_get?sql={urllib.parse.quote(sql)}"

response = requests.get(url, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30)

print("Status:", response.status_code)
print()
print(response.text[:1000])
