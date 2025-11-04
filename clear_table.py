#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

bq = bq_client()

print("🗑️  Clearing existing documents table...")

# Delete all existing records
query = "DELETE FROM `inner-cinema-476211-u9.uk_energy_insights.documents` WHERE TRUE"
job = bq.query(query)
job.result()

print("✅ Table cleared successfully")

# Verify it's empty
result = bq.query("SELECT COUNT(*) as total FROM `inner-cinema-476211-u9.uk_energy_insights.documents`").result()
for row in result:
    print(f"📊 Current document count: {row.total}")
