#!/usr/bin/env python3
"""
BOALF Spike Detector - Live Constraint Proxy
Detects constraint events by analyzing balancing acceptance patterns
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def detect_acceptance_spikes():
    """Detect constraint events from BOALF acceptance patterns"""

    print("\n🔍 Analyzing BOALF acceptance patterns...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Query last 24h of acceptances from IRIS (real-time)
    sql = f"""
    WITH recent_acceptances AS (
      SELECT
        acceptanceTime,
        bmUnit,
        levelFrom,
        levelTo,
        ABS(levelTo - levelFrom) as volume_mw,
        EXTRACT(HOUR FROM acceptanceTime) as hour,
        EXTRACT(DATE FROM acceptanceTime) as date
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE acceptanceTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
    ),

    hourly_stats AS (
      SELECT
        date,
        hour,
        COUNT(*) as acceptance_count,
        SUM(volume_mw) as total_volume_mw,
        COUNT(DISTINCT bmUnit) as unique_bmus,
        AVG(volume_mw) as avg_volume_mw
      FROM recent_acceptances
      GROUP BY date, hour
    ),

    stats_with_threshold AS (
      SELECT
        *,
        AVG(acceptance_count) OVER () as avg_count,
        STDDEV(acceptance_count) OVER () as stddev_count,
        AVG(total_volume_mw) OVER () as avg_volume,
        STDDEV(total_volume_mw) OVER () as stddev_volume
      FROM hourly_stats
    )

    SELECT
      date,
      hour,
      acceptance_count,
      total_volume_mw,
      unique_bmus,
      avg_volume_mw,
      -- Z-score for spike detection
      (acceptance_count - avg_count) / NULLIF(stddev_count, 0) as count_zscore,
      (total_volume_mw - avg_volume) / NULLIF(stddev_volume, 0) as volume_zscore,
      -- Flag as spike if >2 standard deviations
      CASE
        WHEN (acceptance_count - avg_count) / NULLIF(stddev_count, 0) > 2 THEN TRUE
        WHEN (total_volume_mw - avg_volume) / NULLIF(stddev_volume, 0) > 2 THEN TRUE
        ELSE FALSE
      END as is_spike
    FROM stats_with_threshold
    ORDER BY date DESC, hour DESC
    """

    df = client.query(sql).to_dataframe()

    print(f"✅ Analyzed {len(df)} hourly periods")

    # Detect spikes
    spikes = df[df['is_spike'] == True]

    if len(spikes) > 0:
        print(f"\n🚨 DETECTED {len(spikes)} CONSTRAINT EVENTS:")
        print("="*80)

        for _, row in spikes.iterrows():
            print(f"\n📅 Date: {row['date']} Hour: {row['hour']:02d}:00")
            print(f"   Acceptances: {row['acceptance_count']} (Z={row['count_zscore']:.1f})")
            print(f"   Volume: {row['total_volume_mw']:.0f} MW (Z={row['volume_zscore']:.1f})")
            print(f"   Unique BMUs: {row['unique_bmus']}")
            print(f"   Avg Volume: {row['avg_volume_mw']:.1f} MW")
    else:
        print("\n✅ No significant constraint spikes detected (last 24h)")

    return df, spikes

def identify_constraint_locations(spikes):
    """Identify geographic patterns in constraint events"""

    if len(spikes) == 0:
        print("\n⏭️  Skipping location analysis (no spikes detected)")
        return

    print("\n🗺️  Analyzing geographic patterns...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Get BMUs involved in spike hours
    spike_hours = spikes[['date', 'hour']].to_dict('records')

    # Query BMU locations for spike periods
    sql = f"""
    WITH spike_acceptances AS (
      SELECT
        bmUnit,
        acceptanceTime,
        ABS(levelTo - levelFrom) as volume_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE acceptanceTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
    )

    SELECT
      b.bmu_id,
      b.gsp_group,
      b.fuel_type_category,
      COUNT(*) as acceptance_count,
      SUM(s.volume_mw) as total_volume_mw
    FROM spike_acceptances s
    JOIN `{PROJECT_ID}.{DATASET}.ref_bmu_canonical` b
      ON s.bmUnit = b.bmu_id
    GROUP BY b.bmu_id, b.gsp_group, b.fuel_type_category
    HAVING acceptance_count > 5
    ORDER BY total_volume_mw DESC
    LIMIT 20
    """

    df = client.query(sql).to_dataframe()

    if len(df) > 0:
        print(f"\n📍 Top BMUs involved in constraints:")
        print("="*80)
        print(f"{'BMU ID':<15} {'GSP Group':<15} {'Fuel':<15} {'Count':>8} {'Volume MW':>12}")
        print("-"*80)

        for _, row in df.iterrows():
            print(f"{row['bmu_id']:<15} {row['gsp_group'] or 'N/A':<15} {row['fuel_type_category']:<15} {row['acceptance_count']:>8} {row['total_volume_mw']:>12,.0f}")

        # Geographic clustering
        gsp_summary = df.groupby('gsp_group').agg({
            'total_volume_mw': 'sum',
            'acceptance_count': 'sum'
        }).sort_values('total_volume_mw', ascending=False)

        print(f"\n🗺️  Geographic concentration:")
        for gsp, data in gsp_summary.head(5).iterrows():
            if gsp:
                print(f"   {gsp}: {data['total_volume_mw']:.0f} MW ({data['acceptance_count']} acceptances)")
    else:
        print("\n⚠️  No BMU location data available for spike analysis")

def create_constraint_alert_table(spikes):
    """Create BigQuery table with constraint alerts"""

    if len(spikes) == 0:
        print("\n⏭️  Skipping alert table (no spikes detected)")
        return

    print("\n💾 Creating constraint alert table...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Prepare data
    alerts = []
    for _, row in spikes.iterrows():
        alerts.append({
            'alert_date': str(row['date']),  # Convert to string
            'alert_hour': int(row['hour']),
            'acceptance_count': int(row['acceptance_count']),
            'total_volume_mw': float(row['total_volume_mw']),
            'unique_bmus': int(row['unique_bmus']),
            'count_zscore': float(row['count_zscore']),
            'volume_zscore': float(row['volume_zscore']),
            'detected_at': datetime.utcnow().isoformat()
        })

    # Define schema
    schema = [
        bigquery.SchemaField("alert_date", "DATE"),
        bigquery.SchemaField("alert_hour", "INTEGER"),
        bigquery.SchemaField("acceptance_count", "INTEGER"),
        bigquery.SchemaField("total_volume_mw", "FLOAT64"),
        bigquery.SchemaField("unique_bmus", "INTEGER"),
        bigquery.SchemaField("count_zscore", "FLOAT64"),
        bigquery.SchemaField("volume_zscore", "FLOAT64"),
        bigquery.SchemaField("detected_at", "TIMESTAMP"),
    ]

    table_id = f"{PROJECT_ID}.{DATASET}.constraint_alerts_live"

    # Append to existing table or create new
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_json(alerts, table_id, job_config=job_config)
    job.result()

    table = client.get_table(table_id)
    print(f"✅ Saved {len(alerts)} alerts to {table_id}")
    print(f"   Total rows: {table.num_rows:,}")

def main():
    print("="*80)
    print("BOALF SPIKE DETECTOR - LIVE CONSTRAINT PROXY")
    print("="*80)
    print(f"Analysis Period: Last 24 hours")
    print(f"Detection Method: Statistical spike detection (Z-score > 2)")

    # Detect spikes
    df, spikes = detect_acceptance_spikes()

    # Analyze locations
    identify_constraint_locations(spikes)

    # Save alerts
    create_constraint_alert_table(spikes)

    # Summary
    print("\n" + "="*80)
    print("✅ SPIKE DETECTION COMPLETE")
    print("="*80)
    print(f"Periods analyzed: {len(df)}")
    print(f"Constraint events detected: {len(spikes)}")

    if len(spikes) > 0:
        print(f"\n💡 Interpretation:")
        print(f"   - {len(spikes)} hours showed abnormal balancing activity")
        print(f"   - This indicates likely grid constraint events")
        print(f"   - Check geographic clustering for transmission bottlenecks")
        print(f"\n📊 Query alerts:")
        print(f"   SELECT * FROM `{PROJECT_ID}.{DATASET}.constraint_alerts_live`")
        print(f"   ORDER BY detected_at DESC LIMIT 10;")
    else:
        print("\n💡 Grid operating normally (no constraint spikes detected)")

if __name__ == "__main__":
    main()
