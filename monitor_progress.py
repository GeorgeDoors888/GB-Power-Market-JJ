#!/usr/bin/env python3
import time
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

bq = bq_client()

print("📊 Monitoring indexing progress...\n")

last_count = 0
for i in range(10):  # Check 10 times
    try:
        result = bq.query("SELECT COUNT(*) as total FROM `inner-cinema-476211-u9.uk_energy_insights.documents`").result()
        for row in result:
            current_count = row.total
            diff = current_count - last_count
            print(f"[{i+1}/10] Documents indexed: {current_count:,} (+{diff:,} since last check)")
            last_count = current_count
    except Exception as e:
        print(f"Error: {e}")
    
    if i < 9:  # Don't sleep on last iteration
        time.sleep(10)  # Check every 10 seconds

print(f"\n✅ Final count: {last_count:,} documents")
