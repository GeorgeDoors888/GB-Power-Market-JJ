#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json
import os
import sys

from google.cloud import bigquery
from google.oauth2 import service_account

# Path to service account key file
KEY_PATH = "jibber_jaber_key.json"


def get_bigquery_client():
    """Create an authenticated BigQuery client using service account credentials"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            KEY_PATH, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return bigquery.Client(credentials=credentials, project=credentials.project_id)
    except Exception as e:
        print(f"Error authenticating with BigQuery: {e}")
        return None


def query_bigquery(client, query):
    """Run a query against BigQuery and return the results"""
    try:
        query_job = client.query(query)
        return list(query_job.result())
    except Exception as e:
        print(f"Error executing query: {e}")
        return None


def get_latest_generation_data(client):
    """Get the latest generation data for all fuel types"""
    query = """
    WITH latest_time AS (
        SELECT MAX(startTime) as max_time
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    )

    SELECT
        fuelType,
        generation,
        startTime,
        publishTime
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    JOIN latest_time ON startTime = max_time
    ORDER BY fuelType
    """
    return query_bigquery(client, query)


def get_latest_interconnector_data(client):
    """Get the latest interconnector flow data"""
    query = """
    WITH latest_time AS (
        SELECT MAX(startTime) as max_time
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
        WHERE fuelType LIKE 'INT%'
    )

    SELECT
        fuelType as interconnectorId,
        generation as flow,
        startTime
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    JOIN latest_time ON startTime = max_time
    WHERE fuelType LIKE 'INT%'
    ORDER BY fuelType
    """
    return query_bigquery(client, query)


# Query to get interconnector data
interconnector_query = """
WITH latest_time AS (
    SELECT MAX(startTime) as max_time
    FROM `jibber-jabber-knowledge.uk_energy_insights.interconnector_flows`
)

SELECT
    interconnectorId,
    flow,
    startTime
FROM `jibber-jabber-knowledge.uk_energy_insights.interconnector_flows`
JOIN latest_time ON startTime = max_time
ORDER BY interconnectorId
"""

# Query to get total system demand
demand_query = """
WITH latest_time AS (
    SELECT MAX(startTime) as max_time
    FROM `jibber-jabber-knowledge.uk_energy_insights.system_demand`
)

SELECT
    demandValue,
    startTime
FROM `jibber-jabber-knowledge.uk_energy_insights.system_demand`
JOIN latest_time ON startTime = max_time
LIMIT 1
"""


def get_system_demand(client):
    """Calculate the total system demand based on generation data"""
    query = """
    WITH latest_time AS (
        SELECT MAX(startTime) as max_time
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    )

    SELECT
        SUM(generation) as total_generation,
        MAX(startTime) as startTime
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    JOIN latest_time ON startTime = max_time
    """
    return query_bigquery(client, query)


def get_remit_events(client, limit=30, include_future=True):
    """Get the latest REMIT events for all types of unavailability

    Args:
        client: BigQuery client
        limit: Maximum number of events to return
        include_future: Whether to include events that start in the future

    Returns:
        List of REMIT events
    """
    # Build the time filter based on parameters
    time_filter = "eventEndTime > CURRENT_TIMESTAMP()"
    if not include_future:
        time_filter += " AND eventStartTime <= CURRENT_TIMESTAMP()"

    query = f"""
    SELECT
        mrid as messageID,
        messageType,
        unavailabilityType,
        assetId as assetID,
        affectedUnit,
        fuelType,
        eventStartTime as eventStart,
        eventEndTime as eventEnd,
        normalCapacity,
        availableCapacity,
        unavailableCapacity,
        eventStatus,
        revisionNumber,
        publishTime as publicationTimestamp,
        cause as reason
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_remit`
    WHERE
        messageType = 'ELECTRICITY_UNAVAILABILITY'
        AND {time_filter}
    ORDER BY
        -- Show currently active events first, then future events
        CASE WHEN eventStartTime <= CURRENT_TIMESTAMP() THEN 1 ELSE 2 END,
        -- For active events, show those ending soonest first
        CASE WHEN eventStartTime <= CURRENT_TIMESTAMP() THEN eventEndTime END ASC,
        -- For future events, show those starting soonest first
        CASE WHEN eventStartTime > CURRENT_TIMESTAMP() THEN eventStartTime END ASC
    LIMIT {limit}
    """
    return query_bigquery(client, query)


def get_system_messages(client):
    """Get the latest system warning messages from REMIT data"""
    query = """
    SELECT
        messageType as warningType,
        messageHeading as headline,
        relatedInformation as details,
        publishTime as issueTime,
        mrid as messageID
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_remit`
    WHERE
        messageType IN ('SYSTEM_WARNING', 'SYSTEM_ALERT', 'HIGH_RISK_OF_DEMAND_CONTROL', 'ELECTRICITY_SYSTEM_WARNING')
        AND publishTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    ORDER BY publishTime DESC
    LIMIT 5
    """
    return query_bigquery(client, query)


def get_remit_summary(client):
    """Get a summary of current REMIT events grouped by fuel type"""
    query = """
    SELECT
        fuelType,
        COUNT(*) as eventCount,
        SUM(unavailableCapacity) as totalUnavailableCapacity,
        MIN(eventEndTime) as earliestEnd,
        MAX(eventEndTime) as latestEnd
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_remit`
    WHERE
        messageType = 'ELECTRICITY_UNAVAILABILITY'
        AND eventEndTime > CURRENT_TIMESTAMP()
        AND eventStartTime <= CURRENT_TIMESTAMP()
    GROUP BY fuelType
    ORDER BY totalUnavailableCapacity DESC
    """
    return query_bigquery(client, query)


def get_neso_data_status(client):
    """Check the status of NESO data tables"""
    query = """
    SELECT
        table_id,
        creation_time,
        last_modified_time,
        row_count,
        size_bytes
    FROM
        `jibber-jabber-knowledge.uk_energy_insights.__TABLES__`
    WHERE
        table_id LIKE 'neso%'
    ORDER BY
        last_modified_time DESC
    LIMIT 10
    """
    return query_bigquery(client, query)


def format_timestamp(timestamp):
    """Format a timestamp for JSON output"""
    if hasattr(timestamp, "isoformat"):
        return timestamp.isoformat()
    return str(timestamp)


def process_query_results(results):
    """Convert BigQuery result rows to a list of dictionaries"""
    if not results:
        return []

    processed = []
    for row in results:
        # Convert to dictionary
        row_dict = dict(row.items())

        # Format any timestamp objects
        for key, value in row_dict.items():
            if isinstance(value, (datetime.datetime, datetime.date)):
                row_dict[key] = format_timestamp(value)

        processed.append(row_dict)

    return processed


def main():
    # Get BigQuery client
    client = get_bigquery_client()
    if not client:
        print("Failed to authenticate with BigQuery. Exiting.")
        sys.exit(1)

    # Get latest data
    generation_data = get_latest_generation_data(client)
    interconnector_data = get_latest_interconnector_data(client)
    demand_data = get_system_demand(client)

    # Get REMIT data
    remit_events = get_remit_events(client, limit=50)
    remit_summary = get_remit_summary(client)
    system_messages = get_system_messages(client)

    # Get NESO data status for monitoring
    neso_data = get_neso_data_status(client)

    # Process the results
    output = {
        "timestamp": datetime.datetime.now().isoformat(),
        "generation": process_query_results(generation_data),
        "interconnectors": process_query_results(interconnector_data),
        "demand": process_query_results(demand_data),
        "remit": {
            "events": process_query_results(remit_events),
            "summary": process_query_results(remit_summary),
        },
        "systemMessages": process_query_results(system_messages),
        "nesoStatus": process_query_results(neso_data),
    }

    # Calculate total generation
    total_generation = 0
    for item in output["generation"]:
        if item["fuelType"] not in [
            "INTFR",
            "INTIRL",
            "INTNED",
            "INTEW",
            "INTNEM",
            "INTELEC",
            "INTNSL",
        ]:
            total_generation += float(item["generation"])

    output["totalGeneration"] = total_generation

    # Add metadata
    output["metadata"] = {
        "generationCount": len(output["generation"]),
        "interconnectorCount": len(output["interconnectors"]),
        "remitEventCount": len(output["remit"]["events"]),
        "systemMessageCount": len(output["systemMessages"]),
        "dataTimestamp": datetime.datetime.now().isoformat(),
    }

    # Output as JSON
    print(json.dumps(output, indent=2))

    # Save to file
    with open("latest_energy_data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Data successfully saved to latest_energy_data.json")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
