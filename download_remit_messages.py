#!/usr/bin/env python3
"""
Download REMIT unavailability messages for wind farms to distinguish icing from maintenance/curtailment.
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import re
from typing import List, Dict

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "remit_unavailability_messages"

# Wind farm BMU IDs (subset - expand based on needs)
WIND_BMUS = [
    "T_ABRBO-1", "T_ABRBO-2", "T_ABRBO-3", "T_ABRBO-4",  # Aberdeen Bay
    "T_HYWIN-1", "T_HYWIN-2",  # Hywind Scotland
    "T_KINCA-1", "T_KINCA-2",  # Kincardine
    "T_GRIFW-1",  # Griffin
    "T_WHILW-1", "T_WHILW-2",  # Whitelee
    "T_CLDRW-1",  # Clyde
    "T_GORDO-1", "T_GORDO-2",  # Gordon
    "T_DORENW-1",  # Dorenell
    "T_BEATW-1", "T_BEATW-2", "T_BEATW-3",  # Beatrice
    "T_MORYW-1", "T_MORYW-2", "T_MORYW-3",  # Moray East
    "T_DUDGW-1", "T_DUDGW-2",  # Dudgeon
    "T_RACEW-1", "T_RACEW-2", "T_RACEW-3",  # Race Bank
    "T_TRITN-1", "T_TRITN-2",  # Triton Knoll
    "T_WLNYO-1", "T_WLNYO-2", "T_WLNYO-3",  # Walney Extension
    "T_HORNO-1", "T_HORNO-2", "T_HORNO-3",  # Hornsea One
    "T_HRNSO-1", "T_HRNSO-2",  # Hornsea Two
    "T_EOWDO-1",  # EOWDC
    "T_GRGBW-1", "T_GRGBW-2",  # Greater Gabbard
    "T_LNCSW-1", "T_LNCSW-2",  # London Array
    "T_LBAPO-1", "T_LBAPO-2",  # Lincs + Lynn and Inner Dowsing
    "T_SHRSW-1", "T_SHRSW-2",  # Sheringham Shoal
    "T_GALW-1",  # Galloper
    "T_RMPNW-1", "T_RMPNW-2",  # Rampion
    "T_WALYO-1", "T_WALYO-2",  # Walney 1 & 2
]

# Weather-related keywords for categorization
ICING_KEYWORDS = ["ice", "icing", "frost", "freeze", "frozen"]
EXTREME_WEATHER_KEYWORDS = ["storm", "wind speed", "lightning", "thunder", "weather", "gust", "cyclone"]
MAINTENANCE_KEYWORDS = ["maintenance", "planned", "repair", "service", "inspection", "upgrade", "commissioning"]


def fetch_remit_messages(bmu_id: str, start_date: str, end_date: str) -> List[Dict]:
    """
    Fetch REMIT messages for a BMU from Elexon API.
    
    Args:
        bmu_id: BMU identifier (e.g., T_ABRBO-1)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        List of message dictionaries
    """
    base_url = "https://api.bmreports.com/BMRS/REMIT/v1"
    
    # Elexon API format: REMIT/v1?ServiceType=CSV&BMUnitId=T_ABRBO-1&FromDate=2021-01-01&ToDate=2021-12-31
    params = {
        "ServiceType": "XML",  # XML easier to parse than CSV
        "BMUnitId": bmu_id,
        "FromDate": start_date,
        "ToDate": end_date,
        "APIKey": "OPEN"  # Elexon API is open (no key needed)
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse XML response (simplified - may need xml.etree.ElementTree for production)
        # For now, use CSV mode which is simpler
        params["ServiceType"] = "CSV"
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 204:  # No content
            return []
        
        # Parse CSV lines
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            return []
        
        # CSV format: HDR, data rows, footer
        # Skip header and footer, parse data rows
        messages = []
        for line in lines[1:]:
            if line.startswith("FTR"):
                break
            
            parts = line.split(',')
            if len(parts) < 10:
                continue
            
            messages.append({
                "bmu_id": bmu_id,
                "message_id": parts[0],
                "message_type": parts[1],
                "event_start": parts[2],
                "event_end": parts[3],
                "fuel_type": parts[4],
                "message_text": parts[5],
                "available_capacity": float(parts[6]) if parts[6] else None,
                "unavailable_capacity": float(parts[7]) if parts[7] else None,
                "published_time": parts[8],
            })
        
        return messages
    
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Error fetching {bmu_id}: {e}")
        return []


def categorize_message(message_text: str) -> str:
    """
    Categorize REMIT message based on free-text content.
    
    Categories:
        WEATHER_ICING: Ice/frost/freeze mentions
        WEATHER_EXTREME: Storm/high winds/lightning
        WEATHER_OTHER: Other weather-related
        MAINTENANCE: Planned maintenance/repairs
        NON_WEATHER: Non-weather related unavailability
    """
    text_lower = message_text.lower()
    
    # Check icing keywords (highest priority - most specific)
    if any(keyword in text_lower for keyword in ICING_KEYWORDS):
        return "WEATHER_ICING"
    
    # Check extreme weather
    if any(keyword in text_lower for keyword in EXTREME_WEATHER_KEYWORDS):
        return "WEATHER_EXTREME"
    
    # Check maintenance
    if any(keyword in text_lower for keyword in MAINTENANCE_KEYWORDS):
        return "MAINTENANCE"
    
    # Generic weather mention
    if "weather" in text_lower:
        return "WEATHER_OTHER"
    
    return "NON_WEATHER"


def upload_to_bigquery(df: pd.DataFrame):
    """Upload REMIT messages to BigQuery."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    # Define schema
    schema = [
        bigquery.SchemaField("bmu_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("message_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("message_type", "STRING"),
        bigquery.SchemaField("event_start", "TIMESTAMP"),
        bigquery.SchemaField("event_end", "TIMESTAMP"),
        bigquery.SchemaField("fuel_type", "STRING"),
        bigquery.SchemaField("message_text", "STRING"),
        bigquery.SchemaField("available_capacity", "FLOAT64"),
        bigquery.SchemaField("unavailable_capacity", "FLOAT64"),
        bigquery.SchemaField("published_time", "TIMESTAMP"),
        bigquery.SchemaField("category", "STRING"),
        bigquery.SchemaField("download_time", "TIMESTAMP"),
    ]
    
    # Create or replace table
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=True)
    
    print(f"\n📤 Uploading {len(df)} REMIT messages to BigQuery...")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=schema,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    print(f"✅ Uploaded to {table_id}")
    
    # Summary statistics
    summary = df.groupby("category").size().to_dict()
    print(f"\n📊 Category Summary:")
    for category, count in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}")


def main():
    """Download all REMIT messages for wind farms (2021-2025)."""
    print("=" * 80)
    print("REMIT Unavailability Messages Downloader")
    print("=" * 80)
    print(f"BMUs: {len(WIND_BMUS)}")
    print(f"Date range: 2021-01-01 to 2025-12-31")
    print(f"Target: {PROJECT_ID}.{DATASET}.{TABLE_NAME}")
    print("=" * 80)
    
    all_messages = []
    
    # Download in yearly chunks to avoid API timeouts
    years = [2021, 2022, 2023, 2024, 2025]
    
    total_bmus = len(WIND_BMUS)
    for i, bmu_id in enumerate(WIND_BMUS, 1):
        print(f"\n[{i}/{total_bmus}] Fetching {bmu_id}...")
        
        for year in years:
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            messages = fetch_remit_messages(bmu_id, start_date, end_date)
            
            if messages:
                print(f"  ✅ {year}: {len(messages)} messages")
                all_messages.extend(messages)
            else:
                print(f"  ⚪ {year}: No messages")
            
            # Rate limiting (be gentle with Elexon API)
            time.sleep(2)
    
    if not all_messages:
        print("\n⚠️  No REMIT messages found for any BMU")
        return
    
    print(f"\n✅ Total messages collected: {len(all_messages)}")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_messages)
    
    # Categorize messages
    print("\n🏷️  Categorizing messages...")
    df["category"] = df["message_text"].apply(categorize_message)
    df["download_time"] = datetime.utcnow()
    
    # Convert date strings to datetime
    for col in ["event_start", "event_end", "published_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    # Upload to BigQuery
    upload_to_bigquery(df)
    
    print("\n" + "=" * 80)
    print("✅ REMIT message download complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
