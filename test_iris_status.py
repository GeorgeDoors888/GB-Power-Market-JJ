#!/usr/bin/env python3
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=["https://www.googleapis.com/auth/bigquery"]
)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")

def check_data_freshness(bq_client):
    """
    Check IRIS data ingestion status across all tables
    Returns status with traffic lights and data volume metrics
    """

    iris_tables = {
        'bmrs_fuelinst_iris': 'Gen Mix',
        'bmrs_bod_iris': 'BM Bids',
        'bmrs_boalf_iris': 'Acceptances',
        'bmrs_mid_iris': 'Market',
        'bmrs_indgen_iris': 'Units',
    }

    table_stats = []
    total_rows_today = 0
    freshest_age = 999999
    freshest_table = None

    for table, short_name in iris_tables.items():
        query = f"""
        SELECT
            COUNT(*) as row_count,
            MAX(settlementDate) as latest_timestamp,
            TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), TIMESTAMP(MAX(settlementDate)), MINUTE) as age_minutes
        FROM `{PROJECT_ID}.{DATASET}.{table}`
        WHERE CAST(settlementDate AS DATE) >= CURRENT_DATE()
        """

        try:
            df = bq_client.query(query).to_dataframe()
            if not df.empty and df['row_count'].iloc[0] > 0:
                rows = int(df['row_count'].iloc[0])
                age_minutes = int(df['age_minutes'].iloc[0])
                latest_ts = df['latest_timestamp'].iloc[0]

                # Determine status: Green < 30min, Orange < 120min, Red >= 120min
                if age_minutes < 30:
                    status_icon = '🟢'
                    status_text = 'FRESH'
                elif age_minutes < 120:
                    status_icon = '🟠'
                    status_text = 'AGING'
                else:
                    status_icon = '🔴'
                    status_text = 'STALE'

                table_stats.append({
                    'table': table,
                    'name': short_name,
                    'rows': rows,
                    'age_minutes': age_minutes,
                    'status_icon': status_icon,
                    'status_text': status_text,
                    'latest_ts': latest_ts
                })

                total_rows_today += rows

                if age_minutes < freshest_age:
                    freshest_age = age_minutes
                    freshest_table = short_name
        except Exception as e:
            # Skip tables with errors
            continue

    # Determine overall status based on freshest data
    if freshest_age < 30:
        overall_status = 'OK'
        overall_icon = '🟢'
        overall_text = 'ACTIVE'
    elif freshest_age < 120:
        overall_status = 'AGING'
        overall_icon = '🟠'
        overall_text = 'AGING'
    else:
        overall_status = 'STALE'
        overall_icon = '🔴'
        overall_text = 'STALE'

    # Create compact status message for dashboard
    active_streams = sum(1 for s in table_stats if s['status_icon'] == '🟢')
    aging_streams = sum(1 for s in table_stats if s['status_icon'] == '🟠')
    stale_streams = sum(1 for s in table_stats if s['status_icon'] == '🔴')

    status_message = f"{overall_icon} IRIS Ingestion: {total_rows_today:,} rows today | {active_streams}🟢 {aging_streams}🟠 {stale_streams}🔴 streams"

    return {
        'status': overall_status,
        'icon': overall_icon,
        'text': overall_text,
        'total_rows': total_rows_today,
        'active_streams': active_streams,
        'aging_streams': aging_streams,
        'stale_streams': stale_streams,
        'freshest_age': freshest_age,
        'freshest_table': freshest_table,
        'table_stats': table_stats,
        'message': status_message
    }

# Test it
print("🕐 Testing IRIS ingestion status check...\n")
result = check_data_freshness(bq_client)

print(f"📊 Overall Status: {result['icon']} {result['text']}")
print(f"📈 Total rows ingested today: {result['total_rows']:,}")
print(f"🟢 Active streams: {result['active_streams']}")
print(f"🟠 Aging streams: {result['aging_streams']}")
print(f"🔴 Stale streams: {result['stale_streams']}")
print(f"\n💬 Dashboard message:")
print(f"   {result['message']}")

print(f"\n📋 Detailed breakdown:")
for stat in result['table_stats']:
    print(f"   {stat['status_icon']} {stat['name']:12s}: {stat['rows']:6,} rows ({stat['age_minutes']:4d} min)")
