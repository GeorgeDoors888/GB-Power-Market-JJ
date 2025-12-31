#!/usr/bin/env python3
"""
Quick verification script for automated downloads
Shows current data status and next scheduled run times
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import subprocess

PROJECT_ID = "inner-cinema-476211-u9"
client = bigquery.Client(project=PROJECT_ID, location="US")

print("=" * 80)
print("📊 AUTOMATED DOWNLOADS - STATUS CHECK")
print("=" * 80)
print(f"Checked: {datetime.now():%Y-%m-%d %H:%M:%S}\n")

# Check P114 data freshness
print("1️⃣ P114 SETTLEMENT DATA")
print("-" * 80)
try:
    query = """
    SELECT
        MAX(settlement_date) as latest_date,
        COUNT(*) as total_records,
        COUNT(DISTINCT settlement_run) as run_types
    FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
    """
    result = client.query(query).to_dataframe()

    latest = result['latest_date'][0]
    total = result['total_records'][0]
    runs = result['run_types'][0]

    days_old = (datetime.now().date() - latest).days if latest else None

    print(f"Latest Date:      {latest}")
    print(f"Total Records:    {total:,}")
    print(f"Settlement Runs:  {runs}")
    print(f"Freshness:        {days_old} days old {'✅' if days_old <= 2 else '⚠️'}")

except Exception as e:
    print(f"❌ Error: {e}")

print()

# Check NESO data
print("2️⃣ NESO CONSTRAINT COSTS")
print("-" * 80)

neso_tables = [
    'neso_constraint_breakdown',
    'neso_mbss',
    'neso_constraint_forecast',
    'neso_modelled_costs',
    'neso_skip_rates'
]

for table in neso_tables:
    try:
        query = f"SELECT COUNT(*) as cnt FROM `inner-cinema-476211-u9.uk_energy_prod.{table}`"
        result = client.query(query).to_dataframe()
        count = result['cnt'][0]

        status = "✅" if count > 0 else "⚠️ Empty"
        print(f"{table:35} {count:>10,} rows {status}")

    except Exception as e:
        print(f"{table:35} ❌ Not found or error")

print()

# Check cron schedule
print("3️⃣ CRON SCHEDULE")
print("-" * 80)

try:
    cron_output = subprocess.check_output(['crontab', '-l'], text=True)

    if 'auto_download_p114_daily' in cron_output:
        print("✅ P114 cron job installed (2am daily)")
    else:
        print("❌ P114 cron job NOT found")

    if 'auto_download_neso_daily' in cron_output:
        print("✅ NESO cron job installed (3am daily)")
    else:
        print("❌ NESO cron job NOT found")

except Exception as e:
    print(f"⚠️  Could not check cron: {e}")

print()

# Next run times
print("4️⃣ NEXT SCHEDULED RUNS")
print("-" * 80)

now = datetime.now()
today_2am = now.replace(hour=2, minute=0, second=0, microsecond=0)
today_3am = now.replace(hour=3, minute=0, second=0, microsecond=0)

if now < today_2am:
    next_p114 = today_2am
else:
    next_p114 = today_2am + timedelta(days=1)

if now < today_3am:
    next_neso = today_3am
else:
    next_neso = today_3am + timedelta(days=1)

print(f"P114 Download:    {next_p114:%Y-%m-%d %H:%M} ({(next_p114 - now).total_seconds() / 3600:.1f}h from now)")
print(f"NESO Download:    {next_neso:%Y-%m-%d %H:%M} ({(next_neso - now).total_seconds() / 3600:.1f}h from now)")

print()

# Log file check
print("5️⃣ LOG FILES")
print("-" * 80)

import os
log_dir = "/home/george/GB-Power-Market-JJ/logs"

for log_file in ['p114_daily.log', 'neso_daily.log']:
    log_path = os.path.join(log_dir, log_file)

    if os.path.exists(log_path):
        size = os.path.getsize(log_path) / 1024  # KB
        mtime = datetime.fromtimestamp(os.path.getmtime(log_path))
        print(f"{log_file:20} {size:>8.1f} KB (modified {mtime:%Y-%m-%d %H:%M})")
    else:
        print(f"{log_file:20} Not created yet (will be created after first run)")

print()
print("=" * 80)
print("✅ STATUS CHECK COMPLETE")
print("=" * 80)
print()
print("📝 Manual test commands:")
print("  python3 /home/george/GB-Power-Market-JJ/auto_download_p114_daily.py")
print("  python3 /home/george/GB-Power-Market-JJ/auto_download_neso_daily.py")
print()
