#!/usr/bin/env python3
"""
Quick test of HUMR-1 report for a single day where we have cost data
"""

import datetime
import os
import sys

import pandas as pd
from google.cloud import bigquery
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Constants
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_insights"


def authenticate_google_apis():
    """Authenticate with Google APIs using OAuth2."""
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/bigquery",
    ]

    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


def test_single_day_data():
    """Test data integration for a single day where we have both generation and cost data."""
    print("🔍 Testing HUMR-1 data integration for 2025-09-18...")

    creds = authenticate_google_apis()
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds)

    test_date = "2025-09-18"

    # Get HUMR-1 generation data for the test date
    gen_query = f"""
    SELECT
        DATETIME_TRUNC(timeTo, MINUTE) as datetime_utc,
        levelTo as humr1_generation_mw
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_pn`
    WHERE bmUnit = 'T_HUMR-1' AND DATE(timeTo) = '{test_date}'
    ORDER BY datetime_utc
    """

    print("📊 Fetching HUMR-1 generation data...")
    gen_df = bq_client.query(gen_query).to_dataframe()
    print(f"   -> Found {len(gen_df)} generation records")

    # Get costs data for the test date
    cost_query = f"""
    SELECT
        settlementDate,
        settlementPeriod,
        systemSellPrice,
        systemBuyPrice,
        priceDerivationCode
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_costs`
    WHERE settlementDate = '{test_date}'
    ORDER BY settlementPeriod
    """

    print("💰 Fetching costs data...")
    cost_df = bq_client.query(cost_query).to_dataframe()
    print(f"   -> Found {len(cost_df)} cost records")

    if not cost_df.empty:
        # Create datetime for costs
        cost_df["datetime_utc"] = pd.to_datetime(
            cost_df["settlementDate"]
        ) + pd.to_timedelta((cost_df["settlementPeriod"] - 1) * 30, unit="minutes")

        # Show sample of costs data
        print("\n💰 Sample costs data:")
        print(
            cost_df[
                [
                    "datetime_utc",
                    "systemSellPrice",
                    "systemBuyPrice",
                    "priceDerivationCode",
                ]
            ].head()
        )

        # Check price ranges
        print(f"\n📈 Price ranges:")
        print(
            f"   System Sell Price: £{cost_df['systemSellPrice'].min():.2f} - £{cost_df['systemSellPrice'].max():.2f}"
        )
        print(
            f"   System Buy Price:  £{cost_df['systemBuyPrice'].min():.2f} - £{cost_df['systemBuyPrice'].max():.2f}"
        )

    if not gen_df.empty:
        print("\n⚡ Sample generation data:")
        print(gen_df.head())

        # Check if we have overlapping time periods
        if not cost_df.empty:
            gen_times = set(gen_df["datetime_utc"].dt.floor("30T"))
            cost_times = set(cost_df["datetime_utc"].dt.floor("30T"))
            overlap = gen_times.intersection(cost_times)
            print(
                f"\n🔗 Time overlap: {len(overlap)} 30-minute periods have both generation and cost data"
            )

            if overlap:
                print("✅ Data integration should work for this date!")
            else:
                print("⚠️ No time overlap between generation and cost data")


if __name__ == "__main__":
    test_single_day_data()
