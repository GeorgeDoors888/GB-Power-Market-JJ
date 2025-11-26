#!/usr/bin/env python3
"""
Show all available IRIS data from last 30 minutes
Evaluate data freshness and identify gaps
"""
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timedelta
import pytz

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Use service account credentials
credentials = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
client = bigquery.Client(project=PROJECT_ID, location="US", credentials=credentials)

print("=" * 100)
print("📊 IRIS DATA AVAILABILITY - LAST 30 MINUTES")
print("=" * 100)

# Get current time in UTC
now_utc = datetime.now(pytz.UTC)
thirty_min_ago = now_utc - timedelta(minutes=30)

print(f"\n🕒 Current Time: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"🕒 Checking from: {thirty_min_ago.strftime('%Y-%m-%d %H:%M:%S UTC')}")

# Define all IRIS tables and their key columns
iris_tables = {
    'bmrs_freq_iris': {
        'category': 'System Balancing',
        'time_col': 'measurementTime',
        'key_cols': ['measurementTime', 'frequency'],
        'purpose': 'System frequency (Hz) - 2-minute updates'
    },
    'bmrs_fuelinst_iris': {
        'category': 'System Balancing',
        'time_col': 'publishTime',
        'key_cols': ['settlementDate', 'settlementPeriod', 'fuelType', 'generation'],
        'purpose': 'Real-time fuel generation mix - 5-minute updates'
    },
    'bmrs_mid_iris': {
        'category': 'Market Pricing',
        'time_col': 'sourceFileDateTime',
        'key_cols': ['settlementDate', 'settlementPeriod', 'dataProvider', 'price', 'volume'],
        'purpose': 'Market index prices - 30-minute updates'
    },
    'bmrs_boalf_iris': {
        'category': 'Dispatch & Control',
        'time_col': 'timeFrom',
        'key_cols': ['settlementDate', 'bmUnit', 'acceptanceNumber', 'levelFrom', 'levelTo'],
        'purpose': 'Bid/Offer acceptances - event-driven'
    },
    'bmrs_mels_iris': {
        'category': 'Network Constraints',
        'time_col': 'notificationTime',
        'key_cols': ['settlementDate', 'settlementPeriod', 'bmUnit', 'levelFrom', 'levelTo'],
        'purpose': 'Maximum Export Limits - event-driven'
    },
    'bmrs_mils_iris': {
        'category': 'Network Constraints',
        'time_col': 'notificationTime',
        'key_cols': ['settlementDate', 'settlementPeriod', 'bmUnit', 'levelFrom', 'levelTo'],
        'purpose': 'Maximum Import Limits - event-driven'
    },
    'bmrs_windfor_iris': {
        'category': 'Forecasting',
        'time_col': 'publishTime',
        'key_cols': ['publishTime', 'startTime', 'generation'],
        'purpose': 'Wind generation forecast - 1-3h ahead'
    },
    'bmrs_indgen_iris': {
        'category': 'Forecasting',
        'time_col': 'publishTime',
        'key_cols': ['settlementDate', 'settlementPeriod', 'boundary', 'generation'],
        'purpose': 'Indicative generation by region'
    },
    'bmrs_inddem_iris': {
        'category': 'Forecasting',
        'time_col': 'publishTime',
        'key_cols': ['settlementDate', 'settlementPeriod', 'boundary', 'demand'],
        'purpose': 'Indicative demand by region'
    },
    'bmrs_indo_iris': {
        'category': 'System Balancing',
        'time_col': 'publishTime',
        'key_cols': ['settlementDate', 'settlementPeriod', 'demand'],
        'purpose': 'National demand outturn - actual demand'
    },
    'bmrs_remit_iris': {
        'category': 'Outage Monitoring',
        'time_col': 'publishTime',
        'key_cols': ['assetId', 'eventType', 'normalCapacity', 'unavailableCapacity', 'cause'],
        'purpose': 'Generation outage notifications (REMIT)'
    }
}

results = {}

for table_name, info in iris_tables.items():
    print(f"\n{'=' * 100}")
    print(f"📋 {table_name.upper()}")
    print(f"   Category: {info['category']}")
    print(f"   Purpose: {info['purpose']}")
    print(f"{'=' * 100}")
    
    try:
        # Check latest ingestion
        latest_query = f"""
        SELECT MAX(ingested_utc) as latest_ingest, COUNT(*) as total_rows
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
        WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
        """
        
        latest_df = client.query(latest_query).to_dataframe()
        
        if latest_df.empty or latest_df['latest_ingest'].iloc[0] is None:
            print(f"   ❌ NO DATA in last 30 minutes")
            results[table_name] = {'status': 'NO DATA', 'rows': 0}
            continue
        
        latest_ingest = latest_df['latest_ingest'].iloc[0]
        total_rows = latest_df['total_rows'].iloc[0]
        age_minutes = (now_utc - latest_ingest.replace(tzinfo=pytz.UTC)).total_seconds() / 60
        
        # Get sample data
        sample_query = f"""
        SELECT {', '.join(info['key_cols'])}
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
        WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
        ORDER BY ingested_utc DESC
        LIMIT 5
        """
        
        sample_df = client.query(sample_query).to_dataframe()
        
        # Status indicator
        if age_minutes < 5:
            status = "✅ FRESH"
        elif age_minutes < 15:
            status = "⚠️ RECENT"
        else:
            status = "🔴 STALE"
        
        print(f"   {status} | Latest: {latest_ingest.strftime('%H:%M:%S UTC')} ({age_minutes:.1f} min ago)")
        print(f"   📊 {total_rows:,} rows ingested in last 30 minutes")
        
        if not sample_df.empty:
            print(f"\n   📝 Sample data (latest 5 rows):")
            for idx, row in sample_df.head(5).iterrows():
                row_str = " | ".join([f"{col}: {row[col]}" for col in info['key_cols'] if col in row])
                print(f"      {idx+1}. {row_str}")
        
        results[table_name] = {
            'status': status,
            'rows': total_rows,
            'age_minutes': age_minutes,
            'latest_ingest': latest_ingest
        }
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results[table_name] = {'status': 'ERROR', 'rows': 0, 'error': str(e)}

# Summary
print(f"\n\n{'=' * 100}")
print("📊 SUMMARY - DATA AVAILABILITY")
print(f"{'=' * 100}\n")

categories = {}
for table_name, info in iris_tables.items():
    cat = info['category']
    if cat not in categories:
        categories[cat] = []
    
    result = results.get(table_name, {})
    categories[cat].append({
        'table': table_name,
        'status': result.get('status', 'UNKNOWN'),
        'rows': result.get('rows', 0),
        'purpose': info['purpose']
    })

for category, tables in sorted(categories.items()):
    print(f"\n🔹 {category}")
    for item in tables:
        print(f"   {item['status']} {item['table']}: {item['rows']:,} rows - {item['purpose']}")

# Identify gaps
print(f"\n\n{'=' * 100}")
print("⚠️ DATA GAPS & MISSING CATEGORIES")
print(f"{'=' * 100}\n")

gaps = []
for table_name, result in results.items():
    if result['status'] in ['NO DATA', 'ERROR']:
        gaps.append(f"❌ {table_name}: {result.get('error', 'No data in last 30 minutes')}")
    elif result.get('age_minutes', 999) > 15:
        gaps.append(f"🔴 {table_name}: Data is {result['age_minutes']:.1f} minutes old (stale)")

if gaps:
    for gap in gaps:
        print(f"   {gap}")
else:
    print("   ✅ All tables have fresh data!")

print(f"\n{'=' * 100}")
print("✅ EVALUATION COMPLETE")
print(f"{'=' * 100}")
