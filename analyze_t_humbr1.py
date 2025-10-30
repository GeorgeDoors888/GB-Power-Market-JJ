#!/usr/bin/env python3
"""
Analyze T_HUMBR-1 generation patterns and BNUoS costs
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
    """Fetch T_HUMBR-1 generation data from BigQuery"""
    query = """
    WITH ranked_data AS (
      SELECT
        settlementDate,
        settlementPeriod,
        bmUnit,
        levelFrom as generation_mw,
        _ingested_utc as timestamp,
        ROW_NUMBER() OVER (
          PARTITION BY settlementDate, settlementPeriod, bmUnit
          ORDER BY _ingested_utc DESC
        ) as rn
      FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_pn`
      WHERE bmUnit = 'T_HUMBR-1'
      AND DATE(_ingested_utc) >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
    )
    SELECT
      settlementDate,
      settlementPeriod,
      bmUnit,
      generation_mw,
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
    """Analyze generation patterns and calculate metrics including GW/GWh patterns"""
    # Convert MW to GW for clarity
    df["generation_gw"] = df["generation_mw"] / 1000

    # Calculate hourly energy in GWh
    df["energy_gwh"] = df["generation_gw"] * 1  # Since data is hourly

    # Weekly statistics
    weekly_stats = (
        df.resample("W", on="timestamp")
        .agg(
            {
                "generation_gw": ["min", "mean", "max", "std"],
                "energy_gwh": "sum",  # Total weekly energy
            }
        )
        .reset_index()
    )

    # Detect periods of zero generation
    zero_gen = df[df["generation_gw"] == 0].copy()
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
    """Create and save visualization plots"""
    plot_files = []

    # Set style
    sns.set_style("whitegrid")  # Use seaborn's whitegrid style

    # 1. Generation Pattern Over Time
    plt.figure(figsize=(15, 6))
    plt.plot(
        df["timestamp"], df["generation_gw"], label="Generation (GW)", color="blue"
    )
    plt.title("T_HUMBR-1 Generation Pattern (Last 24 Months)")
    plt.xlabel("Date")
    plt.ylabel("Generation (GW)")
    plt.grid(True)
    plt.legend()
    generation_plot = "t_humbr1_generation.png"
    plt.savefig(generation_plot, dpi=300, bbox_inches="tight")
    plt.close()
    plot_files.append(generation_plot)

    # 2. Weekly Statistics
    plt.figure(figsize=(15, 6))
    weekly_stats = analysis["weekly_stats"]
    plt.plot(
        weekly_stats["timestamp"], weekly_stats["generation_gw"]["mean"], label="Mean"
    )
    plt.fill_between(
        weekly_stats["timestamp"],
        weekly_stats["generation_gw"]["min"],
        weekly_stats["generation_gw"]["max"],
        alpha=0.3,
    )
    plt.title("Weekly Generation Statistics")
    plt.xlabel("Date")
    plt.ylabel("Generation (MW)")
    plt.legend()
    weekly_plot = "weekly_stats.png"
    plt.savefig(weekly_plot)
    plt.close()
    plot_files.append(weekly_plot)

    # 3. Zero Generation Periods
    if analysis["zero_periods"]:
        zero_periods_df = pd.DataFrame(analysis["zero_periods"])
        plt.figure(figsize=(15, 6))
        plt.scatter(
            zero_periods_df["start"], zero_periods_df["bnuos_savings"], alpha=0.6
        )
        plt.title("BNUoS Savings During Zero Generation Periods")
        plt.xlabel("Period Start")
        plt.ylabel("BNUoS Savings (GBP)")
        savings_plot = "bnuos_savings.png"
        plt.savefig(savings_plot)
        plt.close()
        plot_files.append(savings_plot)

    return plot_files


def update_google_sheet(service, analysis: Dict[str, Any]):
    """Update the Google Sheet with analysis results"""
    try:
        # Sheet 1: Weekly Statistics
        headers = [
            "Week",
            "Min Generation (GW)",
            "Mean Generation (GW)",
            "Max Generation (GW)",
            "Std Dev",
            "Total Energy (GWh)",
        ]

        weekly_values = [headers]
        for idx, row in analysis["weekly_stats"].iterrows():
            weekly_values.append(
                [
                    row["timestamp"].strftime("%Y-%m-%d"),
                    str(row["generation_gw"]["min"]),
                    str(row["generation_gw"]["mean"]),
                    str(row["generation_gw"]["max"]),
                    str(row["generation_gw"]["std"]),
                    str(row["energy_gwh"]),
                ]
            )

        # Update Weekly Stats sheet
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID, range="Weekly Stats!A1:F"
        ).execute()

        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="Weekly Stats!A1",
            valueInputOption="RAW",
            body={"values": weekly_values},
        ).execute()

        # Sheet 2: Zero Generation Periods
        if analysis["zero_periods"]:
            zero_headers = ["Start Time", "End Time", "Duration (hours)", "Period"]
            zero_values = [zero_headers]

            # Sort by duration
            sorted_periods = sorted(
                analysis["zero_periods"],
                key=lambda x: x["duration_hours"],
                reverse=True,
            )

            for period in sorted_periods:
                zero_values.append(
                    [
                        period["start"].strftime("%Y-%m-%d %H:%M"),
                        period["end"].strftime("%Y-%m-%d %H:%M"),
                        str(period["duration_hours"]),
                        period["period"],
                    ]
                )

            # Update Zero Periods sheet
            service.spreadsheets().values().clear(
                spreadsheetId=SPREADSHEET_ID, range="Zero Periods!A1:D"
            ).execute()

            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range="Zero Periods!A1",
                valueInputOption="RAW",
                body={"values": zero_values},
            ).execute()

        body = {"values": weekly_values}

        # Update the sheet
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="Weekly Stats!A1",
            valueInputOption="RAW",
            body=body,
        ).execute()

    except HttpError as error:
        print(f"An error occurred: {error}")


def update_google_doc(service, analysis: Dict[str, Any], plot_files: List[str]):
    """Update the Google Doc with analysis summary and plots"""
    try:
        # Calculate statistics
        avg_generation = analysis["weekly_stats"]["energy_gwh"].mean()
        max_generation = analysis["weekly_stats"]["generation_gw"]["max"].max()
        min_generation = analysis["weekly_stats"]["generation_gw"]["min"].min()
        std_dev = analysis["weekly_stats"]["generation_gw"]["std"].mean()
        zero_periods = analysis.get("zero_periods", [])

        # Create summary text
        summary = {
            "title": "T_HUMBR-1 Generation Analysis Report",
            "summary": f"Analysis Period: Last 24 Months\n\n"
            f"Generation Statistics:\n"
            f"- Weekly Average Generation: {avg_generation:.2f} GWh\n"
            f"- Maximum Generation: {max_generation:.2f} GW\n"
            f"- Minimum Generation: {min_generation:.2f} GW\n"
            f"- Standard Deviation: {std_dev:.2f} GW\n\n"
            f"Zero Generation Periods: {len(zero_periods)}\n\n",
        }

        # Add significant zero generation periods
        if zero_periods:
            summary["summary"] += "Significant Zero Generation Periods:\n"
            # Sort by duration
            sorted_periods = sorted(
                zero_periods, key=lambda x: x["duration_hours"], reverse=True
            )
            for period in sorted_periods[:5]:  # Top 5 longest periods
                summary[
                    "summary"
                ] += f"- {period['period']} ({period['duration_hours']:.1f} hours)\n"

        # Update document
        requests = [
            {
                "insertText": {
                    "text": summary["title"] + "\n\n" + summary["summary"],
                    "location": {"index": 1},
                }
            }
        ]

        service.documents().batchUpdate(
            documentId=DOCUMENT_ID, body={"requests": requests}
        ).execute()

        # Upload and insert images
        # Note: This would require additional implementation to handle image uploads

    except HttpError as error:
        print(f"An error occurred: {error}")


def main():
    """Main execution function"""
    print("Starting analysis...")

    # Initialize services
    print("Initializing Google services...")
    try:
        sheets_service = get_google_service("sheets", "v4")
        docs_service = get_google_service("docs", "v1")
        print("✓ Google services initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Google services: {str(e)}")
        return

    print("Fetching generation data...")
    df = fetch_generation_data()
    if df is None:
        print("❌ Failed to fetch generation data")
        return
    print(f"✓ Retrieved {len(df)} rows of data")

    print("Analyzing generation patterns...")
    analysis = analyze_generation_patterns(df)
    print("✓ Analysis complete")

    print("Creating visualizations...")
    plot_files = create_visualizations(df, analysis)
    print(f"✓ Created {len(plot_files)} visualization files")

    print("Updating Google Sheet...")
    update_google_sheet(sheets_service, analysis)
    print("✓ Google Sheet updated")

    print("Updating Google Doc...")
    update_google_doc(docs_service, analysis, plot_files)
    print("✓ Google Doc updated")

    print("\nReport generation complete!")

    # Fetch and analyze data
    print("Fetching generation data...")
    df = fetch_generation_data()
    if df is None:
        print("❌ Failed to fetch generation data")
        return
    print(f"✓ Retrieved {len(df) if df is not None else 0} rows of data")

    # Analyze data
    analysis = analyze_generation_patterns(df)

    # Create visualizations
    plot_files = create_visualizations(df, analysis)

    # Update Google Sheet and Doc
    update_google_sheet(sheets_service, analysis)
    update_google_doc(docs_service, analysis, plot_files)


if __name__ == "__main__":
    main()
