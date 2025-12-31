#!/usr/bin/env python3
"""
Incremental REMIT messages download (yesterday only).
Downloads previous day's operational notifications.
Run daily at 02:00 UTC via cron.
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "remit_unavailability_messages"
ELEXON_API_URL = "https://data.elexon.co.uk/bmrs/api/v1/remit/message/list"


def check_existing_dates():
    """Get existing dates in BigQuery to avoid duplicates."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT DATE(publishTime) as msg_date
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    WHERE DATE(publishTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    """
    
    try:
        df = client.query(query).to_dataframe()
        return set(df['msg_date'].dt.date)
    except Exception as e:
        print(f"⚠️  Error checking existing dates: {e}")
        return set()


def download_remit_messages(target_date):
    """Download REMIT messages for a specific date."""
    params = {
        "publishDateTimeFrom": target_date.strftime("%Y-%m-%d 00:00:00"),
        "publishDateTimeTo": (target_date + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00"),
    }
    
    all_messages = []
    
    try:
        print(f"  Fetching messages from Elexon API...")
        response = requests.get(ELEXON_API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if "data" not in data:
            print(f"  ⚠️  No data field in response")
            return pd.DataFrame()
        
        messages = data["data"]
        print(f"  ✅ Received {len(messages)} messages")
        
        if not messages:
            return pd.DataFrame()
        
        # Parse messages
        for msg in messages:
            parsed = {
                "messageId": msg.get("messageId"),
                "messageType": msg.get("messageType"),
                "eventType": msg.get("eventType"),
                "eventStart": msg.get("eventStart"),
                "eventEnd": msg.get("eventEnd"),
                "fuelType": msg.get("fuelType"),
                "assetId": msg.get("assetId"),
                "assetName": msg.get("assetName"),
                "unavailableCapacity": msg.get("unavailableCapacity"),
                "availableCapacity": msg.get("availableCapacity"),
                "normalCapacity": msg.get("normalCapacity"),
                "reason": msg.get("reason"),
                "message": msg.get("message"),
                "publishTime": msg.get("publishTime"),
                "participantId": msg.get("participantId"),
            }
            all_messages.append(parsed)
        
        df = pd.DataFrame(all_messages)
        
        # Convert timestamps
        df["eventStart"] = pd.to_datetime(df["eventStart"])
        df["eventEnd"] = pd.to_datetime(df["eventEnd"])
        df["publishTime"] = pd.to_datetime(df["publishTime"])
        
        return df
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return pd.DataFrame()


def upload_to_bigquery(df, target_date):
    """Upload REMIT messages to BigQuery (append mode with duplicate check)."""
    if df.empty:
        print("⚪ No data to upload")
        return
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    # Check if table exists
    try:
        client.get_table(table_id)
        table_exists = True
    except Exception:
        table_exists = False
    
    if table_exists:
        # Remove any existing data for this date
        print(f"  🗑️  Removing existing data for {target_date}...")
        delete_query = f"""
        DELETE FROM `{table_id}`
        WHERE DATE(publishTime) = '{target_date}'
        """
        client.query(delete_query).result()
    
    print(f"📤 Uploading {len(df):,} messages to BigQuery...")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded to {table_id}")


def main():
    """Download yesterday's REMIT messages."""
    print("="*80)
    print("REMIT Unavailability Messages - Incremental Update")
    print("="*80)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Download yesterday's data (T-1)
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    print(f"Target date: {yesterday}")
    print()
    
    # Check if already have this date
    existing_dates = check_existing_dates()
    
    if yesterday in existing_dates:
        print(f"⚠️  Already have data for {yesterday}")
        print("   (Will re-download to ensure completeness)")
        print()
    
    # Download messages
    print(f"Downloading REMIT messages for {yesterday}...")
    df = download_remit_messages(yesterday)
    
    if df.empty:
        print(f"\n⚠️  No messages for {yesterday}")
        print("="*80)
        sys.exit(0)
    
    # Summary by fuel type
    print("\nMessages by fuel type:")
    fuel_counts = df["fuelType"].value_counts()
    for fuel, count in fuel_counts.items():
        print(f"  {fuel}: {count}")
    
    # Summary by event type
    print("\nMessages by event type:")
    event_counts = df["eventType"].value_counts()
    for event, count in event_counts.items():
        print(f"  {event}: {count}")
    
    # Upload to BigQuery
    print()
    upload_to_bigquery(df, yesterday)
    
    print("\n" + "="*80)
    print(f"✅ Downloaded {len(df):,} messages for {yesterday}")
    print("="*80)


if __name__ == "__main__":
    main()
