#!/usr/bin/env python3
"""
Analyze T_HUMR-1 generation patterns and BNUoS costs
and upload results to Google Sheets and Docs
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google API setup
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]

SPREADSHEET_ID = "1f9Xe_zyzUl882F1HPtBoKJBFDWf4gizbJTSPqI_ok90"
DOCUMENT_ID = "1Ir945DrRthwAHeIZr7OekbGsqHoLcxL-e6Hyc_Qdjmc"


def get_google_service(api_name: str, api_version: str):
    """Initialize Google API service"""
    credentials = service_account.Credentials.from_service_account_file(
        "jibber_jabber_key.json", scopes=SCOPES
    )
    return build(api_name, api_version, credentials=credentials)


def fetch_generation_data() -> Optional[pd.DataFrame]:
    """Fetch T_HUMR-1 generation data from BigQuery"""
    query = """
    WITH ranked_data AS (
      SELECT
        settlementDate,
        settlementPeriod,
        bmUnit,
        activeFlag,
        notificationTime,
        notificationSequence,
        timeFrom,
        timeTo,
        levelFrom,
        levelTo,
        _ingested_utc as timestamp,
        ROW_NUMBER() OVER (
          PARTITION BY settlementDate, settlementPeriod, bmUnit
          ORDER BY _ingested_utc DESC
        ) as rn
      FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_pn`
      WHERE bmUnit = 'T_HUMR-1'
      AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
    )
    SELECT
      settlementDate,
      settlementPeriod,
      bmUnit,
      activeFlag,
      notificationTime,
      notificationSequence,
      timeFrom,
      timeTo,
      levelFrom,
      levelTo,
      timestamp
    FROM ranked_data
    WHERE rn = 1
    ORDER BY settlementDate, settlementPeriod"""

    # Create BigQuery client
    client = bigquery.Client()

    try:
        # Execute query
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def analyze_generation_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze generation patterns and calculate metrics"""
    # Convert levels to numeric type if needed
    df["levelFrom"] = pd.to_numeric(df["levelFrom"], errors="coerce")
    df["levelTo"] = pd.to_numeric(df["levelTo"], errors="coerce")

    # Calculate average level for the period
    df["avg_level"] = (df["levelFrom"] + df["levelTo"]) / 2

    # Weekly statistics
    weekly_stats = (
        df.resample("W", on="timestamp")
        .agg({"avg_level": ["min", "mean", "max", "std"]})
        .reset_index()
    )

    # Detect periods of zero generation
    zero_gen = df[df["avg_level"] == 0].copy()
    zero_periods = []

    if not zero_gen.empty:
        zero_gen["period_start"] = zero_gen["timestamp"].diff() > pd.Timedelta(hours=1)
        period_starts = zero_gen[zero_gen["period_start"]]["timestamp"]
        period_ends = zero_gen[zero_gen["timestamp"].diff(-1) < -pd.Timedelta(hours=1)][
            "timestamp"
        ]

        for start, end in zip(period_starts, period_ends):
            period = {
                "start": start,
                "end": end,
                "duration_hours": (end - start).total_seconds() / 3600,
                "period": f"{start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}",
            }
            zero_periods.append(period)

    return {"weekly_stats": weekly_stats, "zero_periods": zero_periods}


def create_visualizations(df: pd.DataFrame, analysis: Dict[str, Any]) -> List[str]:
    """Create visualizations and save them to files"""
    plt.style.use("seaborn")
    image_files = []

    # 1. Generation Level Over Time
    plt.figure(figsize=(15, 6))
    plt.plot(df["timestamp"], df["avg_level"])
    plt.title("T_HUMR-1 Generation Level Over Time")
    plt.xlabel("Date")
    plt.ylabel("Average Generation Level (MW)")
    plt.grid(True)

    # Save the plot
    generation_plot = "t_humr1_generation.png"
    plt.savefig(generation_plot)
    plt.close()
    image_files.append(generation_plot)

    # 2. Weekly Statistics
    weekly_stats = analysis["weekly_stats"]
    plt.figure(figsize=(15, 6))
    plt.plot(weekly_stats["timestamp"], weekly_stats["avg_level"]["mean"], label="Mean")
    plt.fill_between(
        weekly_stats["timestamp"],
        weekly_stats["avg_level"]["min"],
        weekly_stats["avg_level"]["max"],
        alpha=0.3,
        label="Min-Max Range",
    )
    plt.title("T_HUMR-1 Weekly Generation Statistics")
    plt.xlabel("Date")
    plt.ylabel("Generation Level (MW)")
    plt.legend()
    plt.grid(True)

    # Save the plot
    weekly_plot = "t_humr1_weekly_stats.png"
    plt.savefig(weekly_plot)
    plt.close()
    image_files.append(weekly_plot)

    return image_files


def main():
    # Fetch data
    df = fetch_generation_data()
    if df is None or df.empty:
        print("No data available for analysis")
        return

    # Analyze patterns
    analysis = analyze_generation_patterns(df)

    # Create visualizations
    image_files = create_visualizations(df, analysis)

    # Print summary
    print("\nAnalysis Summary:")
    print("================")

    # Weekly statistics
    weekly_stats = analysis["weekly_stats"]
    print("\nWeekly Statistics:")
    print(
        f"Average generation level: {weekly_stats['avg_level']['mean'].mean():.2f} MW"
    )
    print(f"Maximum generation level: {weekly_stats['avg_level']['max'].max():.2f} MW")
    print(f"Minimum generation level: {weekly_stats['avg_level']['min'].min():.2f} MW")

    # Zero generation periods
    zero_periods = analysis["zero_periods"]
    print(f"\nNumber of zero generation periods: {len(zero_periods)}")
    if zero_periods:
        print("\nSignificant zero generation periods:")
        for period in sorted(
            zero_periods, key=lambda x: x["duration_hours"], reverse=True
        )[:5]:
            print(f"- {period['period']} ({period['duration_hours']:.1f} hours)")

    print("\nVisualization files generated:")
    for file in image_files:
        print(f"- {file}")


if __name__ == "__main__":
    main()
