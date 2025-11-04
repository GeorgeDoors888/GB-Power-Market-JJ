#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")

print("=== Configuration Check ===")
print(f"GCP Project: {os.environ.get('GCP_PROJECT', 'NOT SET')}")
print(f"BigQuery Dataset: {os.environ.get('BQ_DATASET', 'NOT SET')}")
print(f"Vertex Location: {os.environ.get('VERTEX_LOCATION', 'NOT SET')}")
print(f"Embed Provider: {os.environ.get('EMBED_PROVIDER', 'NOT SET')}")
print(f"API Host: {os.environ.get('API_HOST', 'NOT SET')}")
print(f"API Port: {os.environ.get('API_PORT', 'NOT SET')}")

print("\n=== BigQuery Connection ===")
try:
    from src.auth.google_auth import bq_client
    bq = bq_client()
    result = bq.query("SELECT COUNT(*) as total FROM `inner-cinema-476211-u9.uk_energy_insights.documents`").result()
    for row in result:
        print(f"✅ BigQuery connected: {row.total:,} documents indexed")
except Exception as e:
    print(f"❌ BigQuery error: {e}")

print("\n=== Vertex AI Configuration ===")
print(f"Model: {os.environ.get('VERTEX_EMBED_MODEL', 'NOT SET')}")
print(f"Location: {os.environ.get('VERTEX_LOCATION', 'NOT SET')}")
