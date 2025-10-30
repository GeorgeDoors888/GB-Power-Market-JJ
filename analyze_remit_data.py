#!/usr/bin/env python
"""
REMIT data analyzer - Extract and analyze current REMIT events.

This script queries the REMIT data in BigQuery and provides analysis
of current unavailability events including affected units, impact on
capacity, and duration of outages.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from google.cloud import bigquery

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_insights"
REMIT_TABLE = "bmrs_remit"


def get_current_remit_events(
    client: bigquery.Client,
    include_recent_ended: bool = False,
    fuel_types: Optional[List[str]] = None,
    limit: int = 1000,
) -> pd.DataFrame:
    """
    Retrieve current REMIT unavailability events

    Args:
        client: BigQuery client
        include_recent_ended: Include events that ended in the past 7 days
        fuel_types: Optional list of fuel types to filter by
        limit: Maximum number of events to return

    Returns:
        DataFrame of REMIT events
    """
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{REMIT_TABLE}"

    # Build time filter
    time_filter = "eventEndTime > CURRENT_TIMESTAMP()"
    if include_recent_ended:
        time_filter = f"(eventEndTime > CURRENT_TIMESTAMP() OR eventEndTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY))"

    # Build fuel type filter
    fuel_filter = ""
    if fuel_types:
        fuel_list = ", ".join([f"'{fuel}'" for fuel in fuel_types])
        fuel_filter = f"AND fuelType IN ({fuel_list})"

    query = f"""
    SELECT
        mrid as messageID,
        messageType,
        eventType,
        unavailabilityType,
        participantId,
        assetId,
        assetType,
        affectedUnit,
        affectedUnitEIC,
        fuelType,
        normalCapacity,
        availableCapacity,
        unavailableCapacity,
        eventStatus,
        eventStartTime,
        eventEndTime,
        cause as reason,
        relatedInformation,
        revisionNumber,
        publishTime,
        outageProfile
    FROM `{table_id}`
    WHERE
        {time_filter}
        {fuel_filter}
    ORDER BY eventEndTime DESC
    LIMIT {limit}
    """

    df = client.query(query).to_dataframe()

    # Calculate duration in days
    if not df.empty:
        df["durationHours"] = (
            df["eventEndTime"] - df["eventStartTime"]
        ).dt.total_seconds() / 3600
        df["startedAgo"] = (
            datetime.now() - df["eventStartTime"].dt.to_pydatetime()
        ).dt.total_seconds() / 3600
        df["endsIn"] = (
            df["eventEndTime"].dt.to_pydatetime() - datetime.now()
        ).dt.total_seconds() / 3600

        # Format timestamps for display
        df["eventStartTime"] = df["eventStartTime"].dt.strftime("%Y-%m-%d %H:%M")
        df["eventEndTime"] = df["eventEndTime"].dt.strftime("%Y-%m-%d %H:%M")
        df["publishTime"] = df["publishTime"].dt.strftime("%Y-%m-%d %H:%M")

    return df


def analyze_remit_events(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze REMIT events and produce summary statistics

    Args:
        df: DataFrame of REMIT events

    Returns:
        Dictionary of analysis results
    """
    if df.empty:
        return {"status": "No events found"}

    results = {
        "total_events": len(df),
        "total_unavailable_capacity": df["unavailableCapacity"].sum(),
        "avg_event_duration_hours": df["durationHours"].mean(),
        "max_event_duration_hours": df["durationHours"].max(),
        "ongoing_events": len(df[df["endsIn"] > 0]),
        "future_events": len(df[df["startedAgo"] < 0]),
        "by_fuel_type": {},
        "by_unavailability_type": {},
        "longest_events": [],
        "largest_capacity_impact": [],
    }

    # Analyze by fuel type
    fuel_counts = df["fuelType"].value_counts()
    for fuel, count in fuel_counts.items():
        fuel_df = df[df["fuelType"] == fuel]
        results["by_fuel_type"][fuel] = {
            "count": int(count),
            "total_unavailable_capacity": float(fuel_df["unavailableCapacity"].sum()),
            "avg_duration_hours": float(fuel_df["durationHours"].mean()),
        }

    # Analyze by unavailability type
    type_counts = df["unavailabilityType"].value_counts()
    for type_name, count in type_counts.items():
        type_df = df[df["unavailabilityType"] == type_name]
        results["by_unavailability_type"][type_name] = {
            "count": int(count),
            "total_unavailable_capacity": float(type_df["unavailableCapacity"].sum()),
            "avg_duration_hours": float(type_df["durationHours"].mean()),
        }

    # Get longest events
    longest = df.nlargest(5, "durationHours")
    for _, row in longest.iterrows():
        results["longest_events"].append(
            {
                "unit": row["affectedUnit"],
                "fuel_type": row["fuelType"],
                "duration_hours": float(row["durationHours"]),
                "start": row["eventStartTime"],
                "end": row["eventEndTime"],
                "capacity_impact": float(row["unavailableCapacity"]),
            }
        )

    # Get largest capacity impact
    largest_impact = df.nlargest(5, "unavailableCapacity")
    for _, row in largest_impact.iterrows():
        results["largest_capacity_impact"].append(
            {
                "unit": row["affectedUnit"],
                "fuel_type": row["fuelType"],
                "capacity_impact": float(row["unavailableCapacity"]),
                "duration_hours": float(row["durationHours"]),
                "start": row["eventStartTime"],
                "end": row["eventEndTime"],
            }
        )

    return results


def generate_report(analysis: Dict[str, Any], detailed: bool = False) -> str:
    """
    Generate a human-readable report from the analysis

    Args:
        analysis: Analysis results dictionary
        detailed: Whether to include detailed event information

    Returns:
        Formatted report text
    """
    if "status" in analysis:
        return f"REMIT Analysis Report: {analysis['status']}"

    report = "REMIT Analysis Report\n"
    report += "====================\n\n"

    report += f"Total Events: {analysis['total_events']}\n"
    report += (
        f"Total Unavailable Capacity: {analysis['total_unavailable_capacity']:.2f} MW\n"
    )
    report += (
        f"Average Event Duration: {analysis['avg_event_duration_hours']:.2f} hours\n"
    )
    report += f"Ongoing Events: {analysis['ongoing_events']}\n"
    report += f"Future Events: {analysis['future_events']}\n\n"

    report += "Analysis by Fuel Type\n"
    report += "---------------------\n"
    for fuel, data in analysis["by_fuel_type"].items():
        report += f"{fuel}: {data['count']} events, {data['total_unavailable_capacity']:.2f} MW unavailable, "
        report += f"avg duration {data['avg_duration_hours']:.2f} hours\n"

    report += "\nAnalysis by Unavailability Type\n"
    report += "------------------------------\n"
    for type_name, data in analysis["by_unavailability_type"].items():
        report += f"{type_name}: {data['count']} events, {data['total_unavailable_capacity']:.2f} MW unavailable, "
        report += f"avg duration {data['avg_duration_hours']:.2f} hours\n"

    report += "\nLongest Events\n"
    report += "-------------\n"
    for event in analysis["longest_events"]:
        report += f"{event['unit']} ({event['fuel_type']}): {event['duration_hours']:.2f} hours, "
        report += f"{event['capacity_impact']:.2f} MW unavailable\n"
        report += f"  Period: {event['start']} to {event['end']}\n"

    report += "\nLargest Capacity Impact\n"
    report += "----------------------\n"
    for event in analysis["largest_capacity_impact"]:
        report += f"{event['unit']} ({event['fuel_type']}): {event['capacity_impact']:.2f} MW unavailable, "
        report += f"{event['duration_hours']:.2f} hours\n"
        report += f"  Period: {event['start']} to {event['end']}\n"

    return report


def main():
    parser = argparse.ArgumentParser(description="Analyze REMIT data from BigQuery")
    parser.add_argument(
        "--include-recent-ended",
        action="store_true",
        help="Include events that ended in the past 7 days",
    )
    parser.add_argument(
        "--fuel-types",
        default="",
        help="Comma-separated list of fuel types to filter by (e.g., NUCLEAR,CCGT)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output file to write results (JSON format)",
    )
    parser.add_argument(
        "--report",
        default="",
        help="Output file to write report (text format)",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include detailed event information in the report",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of events to retrieve",
    )

    args = parser.parse_args()

    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)

    # Parse fuel types if provided
    fuel_types = None
    if args.fuel_types:
        fuel_types = [f.strip() for f in args.fuel_types.split(",") if f.strip()]

    # Get REMIT events
    df = get_current_remit_events(
        client,
        include_recent_ended=args.include_recent_ended,
        fuel_types=fuel_types,
        limit=args.limit,
    )

    if df.empty:
        logger.info("No REMIT events found matching the criteria")
        return

    logger.info(f"Retrieved {len(df)} REMIT events")

    # Analyze events
    analysis = analyze_remit_events(df)

    # Generate report
    report = generate_report(analysis, detailed=args.detailed)
    print(report)

    # Save output if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"Analysis saved to {args.output}")

    if args.report:
        with open(args.report, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {args.report}")


if __name__ == "__main__":
    main()
