#!/usr/bin/env python3
"""
Non-invasive Data Tracker
Works with existing Google Sheets structure without clearing data
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import google.auth
import gspread
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

# Load environment variables
load_dotenv()

# Configuration
SPREADSHEET_ID = "1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw"
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "uk_energy_insights"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("non_invasive_tracker.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class NonInvasiveTracker:
    def __init__(self):
        self.setup_google_sheets()
        self.bq_client = bigquery.Client(project=BQ_PROJECT)

    def setup_google_sheets(self):
        """Initialize Google Sheets connection without modifying existing data"""
        try:
            credentials, _ = google.auth.default(
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
            )

            self.gc = gspread.authorize(credentials)

            # Try to find a suitable worksheet for tracking
            spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)

            # Look for existing tracking sheet or use a new one
            try:
                self.sheet = spreadsheet.worksheet("DataTracking")
                logger.info("Using existing DataTracking worksheet")
            except:
                try:
                    # Create a new worksheet for tracking without touching Sheet1
                    self.sheet = spreadsheet.add_worksheet(
                        "DataTracking", rows=100, cols=6
                    )
                    # Set headers
                    self.sheet.update(
                        "A1:F1",
                        [
                            [
                                "Source",
                                "Dataset",
                                "Last_Update",
                                "Status",
                                "Tracked_At",
                                "Notes",
                            ]
                        ],
                    )
                    logger.info("Created new DataTracking worksheet")
                except:
                    # Fall back to finding any available sheet that's not the main one
                    all_sheets = spreadsheet.worksheets()
                    for ws in all_sheets:
                        if ws.title.lower() not in ["sheet1", "main", "dashboard"]:
                            self.sheet = ws
                            logger.info(f"Using worksheet: {ws.title}")
                            break
                    else:
                        # Last resort - use Sheet1 but be very careful
                        self.sheet = spreadsheet.sheet1
                        logger.warning("Using Sheet1 - will append data carefully")

            logger.info("Google Sheets connection established")

        except Exception as e:
            logger.error(f"Failed to setup Google Sheets: {e}")
            raise

    def get_last_ingestion_from_bigquery(self) -> Dict[str, datetime]:
        """Get last ingestion times directly from BigQuery data"""
        last_times = {}
        current_time = datetime.now(timezone.utc)

        # Check key BMRS tables for their latest data
        key_tables = ["bmrs_bod", "bmrs_freq", "bmrs_fuelinst"]

        for table in key_tables:
            try:
                query = f"""
                SELECT MAX(_window_from_utc) as latest_data
                FROM `{BQ_PROJECT}.{BQ_DATASET}.{table}`
                WHERE _window_from_utc IS NOT NULL
                """

                result = self.bq_client.query(query).to_dataframe()
                if not result.empty and result["latest_data"].iloc[0] is not None:
                    latest_data = pd.to_datetime(result["latest_data"].iloc[0])
                    if latest_data.tz is None:
                        latest_data = latest_data.tz_localize("UTC")
                    else:
                        latest_data = latest_data.tz_convert("UTC")

                    last_times[f"ELEXON_{table.upper()}"] = latest_data.to_pydatetime()
                    logger.info(f"Latest data in {table}: {latest_data}")

            except Exception as e:
                logger.warning(f"Could not check {table}: {e}")

        # If we found any data, use the earliest as the overall last time
        if last_times:
            # Use the minimum time to be conservative
            overall_last = min(last_times.values())
            last_times["ELEXON_ALL"] = overall_last
        else:
            # Default to 4 hours ago
            last_times["ELEXON_ALL"] = current_time - timedelta(hours=4)

        last_times["NESO_ALL"] = current_time - timedelta(hours=24)  # Default for NESO

        return last_times

    def update_tracking_safely(
        self, source: str, dataset: str, timestamp: datetime, status: str = "SUCCESS"
    ):
        """Update tracking without disturbing existing sheet structure"""
        try:
            current_time = datetime.now(timezone.utc)

            # Find a safe place to add tracking data
            # Look for empty rows or append at the end
            all_values = self.sheet.get_all_values()

            # Find the first completely empty row
            empty_row = None
            for i, row in enumerate(all_values):
                if all(cell.strip() == "" for cell in row):
                    empty_row = i + 1  # 1-indexed
                    break

            if empty_row is None:
                # Append at the end
                empty_row = len(all_values) + 1

            # Prepare tracking data
            tracking_data = [
                source,
                dataset,
                timestamp.isoformat(),
                status,
                current_time.isoformat(),
                f"Auto-tracked at {current_time.strftime('%H:%M')}",
            ]

            # Update the row
            range_name = f"A{empty_row}:F{empty_row}"
            self.sheet.update(range_name, [tracking_data])

            logger.info(f"Added tracking data at row {empty_row}")

        except Exception as e:
            logger.error(f"Failed to update tracking: {e}")
            # Don't fail the whole process if tracking fails

    def check_if_update_needed(self) -> Dict:
        """Check if an update is needed based on BigQuery data freshness"""
        try:
            last_times = self.get_last_ingestion_from_bigquery()
            current_time = datetime.now(timezone.utc)

            elexon_last = last_times.get(
                "ELEXON_ALL", current_time - timedelta(hours=4)
            )
            time_since_elexon = current_time - elexon_last

            logger.info(
                f"Last Elexon data: {elexon_last} ({time_since_elexon.total_seconds()/60:.1f} minutes ago)"
            )

            # Check if we need to update (if data is older than 2 hours)
            if time_since_elexon.total_seconds() > 7200:  # 2 hours
                logger.info("📊 Data is getting stale, update recommended")

                # Calculate incremental date range
                start_date = (elexon_last - timedelta(hours=1)).strftime(
                    "%Y-%m-%d"
                )  # 1 hour buffer
                end_date = current_time.strftime("%Y-%m-%d")

                return {
                    "action": "elexon_update",
                    "start_date": start_date,
                    "end_date": end_date,
                    "last_update": elexon_last.isoformat(),
                    "staleness_hours": time_since_elexon.total_seconds() / 3600,
                }
            else:
                logger.info("⏭️  Data is recent enough, skipping update")
                return {
                    "action": "skip",
                    "reason": "data_recent",
                    "time_since_last": time_since_elexon.total_seconds() / 60,
                    "last_data": elexon_last.isoformat(),
                }

        except Exception as e:
            logger.error(f"Error checking update status: {e}")
            return {"action": "error", "error": str(e)}


def main():
    """Main function that checks BigQuery directly"""
    logger.info("🔍 Checking data freshness without modifying your sheets...")

    tracker = NonInvasiveTracker()
    result = tracker.check_if_update_needed()

    # Only update tracking if we're actually doing something
    if result.get("action") == "elexon_update":
        tracker.update_tracking_safely(
            "ELEXON", "ALL", datetime.now(timezone.utc), "CHECK_REQUESTED"
        )

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
