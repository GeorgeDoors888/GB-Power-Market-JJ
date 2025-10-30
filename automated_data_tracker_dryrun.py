#!/usr/bin/env python3
"""
Automated Data Tracker with Google Sheets Integration
Tracks last ingestion times and manages incremental updates for Elexon and NESO data.
Modified version to support dry-run mode without Google Sheets authentication
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

# Only import gspread if not in dry run mode
try:
    import gspread
    from google.oauth2 import service_account

    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configuration
SPREADSHEET_ID = "1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw"
WORKSHEET_NAME = "Sheet1"  # Adjust if needed
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "uk_energy_insights"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("automated_tracker.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DataTracker:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.setup_google_sheets()
        try:
            self.bq_client = bigquery.Client(project=BQ_PROJECT)
        except Exception as e:
            logger.warning(f"Could not connect to BigQuery: {e}")
            self.bq_client = None

    def setup_google_sheets(self):
        """Initialize Google Sheets connection"""
        if self.dry_run:
            logger.info("Dry run mode: Google Sheets integration disabled")
            self.gc = None
            self.sheet = None
            return

        # Skip Google Sheets setup if gspread is not available
        if not GSPREAD_AVAILABLE:
            logger.warning(
                "gspread module not available. Google Sheets integration disabled."
            )
            self.gc = None
            self.sheet = None
            return

        try:
            # Use the jibber-jabber-knowledge service account
            # This account has access to the spreadsheet: jibber-jabber-knowledge@appspot.gserviceaccount.com
            service_account_info = {
                "type": "service_account",
                "project_id": "jibber-jabber-knowledge",
                "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID", ""),
                "private_key": os.environ.get("GOOGLE_PRIVATE_KEY", "").replace(
                    "\\n", "\n"
                ),
                "client_email": "jibber-jabber-knowledge@appspot.gserviceaccount.com",
                "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/jibber-jabber-knowledge%40appspot.gserviceaccount.com",
                "universe_domain": "googleapis.com",
            }

            # Check for service account credentials file first
            cred_files = [
                "client_secrets.json",
                "service_account.json",
                "google_credentials.json",
                f'{os.path.expanduser("~")}/.config/gcloud/application_default_credentials.json',
            ]

            credentials = None

            # First try to use the environment variables
            if (
                service_account_info["private_key"]
                and service_account_info["private_key_id"]
            ):
                try:
                    credentials = service_account.Credentials.from_service_account_info(
                        service_account_info,
                        scopes=[
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive",
                        ],
                    )
                    logger.info("Using credentials from environment variables")
                except Exception as e:
                    logger.warning(
                        f"Could not use service account info from environment: {e}"
                    )

            # If that didn't work, try files
            if not credentials:
                for cred_file in cred_files:
                    if os.path.exists(cred_file):
                        try:
                            credentials = (
                                service_account.Credentials.from_service_account_file(
                                    cred_file,
                                    scopes=[
                                        "https://www.googleapis.com/auth/spreadsheets",
                                        "https://www.googleapis.com/auth/drive",
                                    ],
                                )
                            )
                            logger.info(f"Using credentials from {cred_file}")
                            break
                        except Exception as e:
                            logger.debug(f"Could not load {cred_file}: {e}")
                            continue

            if not credentials:
                logger.warning(
                    "No service account credentials found. Using default ADC."
                )
                # Fall back to default credentials
                import google.auth

                credentials, _ = google.auth.default(
                    scopes=[
                        "https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive",
                    ]
                )

            self.gc = gspread.authorize(credentials)
            self.sheet = self.gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
            logger.info("Google Sheets connection established")

        except Exception as e:
            logger.error(f"Failed to setup Google Sheets: {e}")
            self.gc = None
            self.sheet = None
            logger.warning("Continuing without Google Sheets integration")

    def get_last_ingestion_times(self) -> Dict[str, datetime]:
        """Get the last ingestion times from Google Sheets"""
        if self.dry_run or not self.sheet:
            # In dry-run mode, return default values
            logger.info(
                "Dry run mode or no Google Sheets: returning default ingestion times"
            )
            current_time = datetime.now(timezone.utc)
            return {
                "ELEXON_HIGH": current_time - timedelta(minutes=30),
                "ELEXON_STANDARD": current_time - timedelta(minutes=45),
                "REMIT_ALL": current_time - timedelta(minutes=45),
                "NESO_ALL": current_time - timedelta(hours=3),
            }

        try:
            # Define expected headers to handle duplicates issue
            expected_headers = [
                "Source",
                "Dataset",
                "Last_Update",
                "Status",
                "Tracked_At",
                "Notes",
            ]

            # Get all data from the sheet with expected headers
            data = self.sheet.get_all_records(expected_headers=expected_headers)
            last_times = {}

            current_time = datetime.now(timezone.utc)

            for row in data:
                source = row.get("Source", "").strip()
                dataset = row.get("Dataset", "").strip()
                last_update_str = row.get("Last_Update", "").strip()

                if source and dataset and last_update_str:
                    try:
                        # Parse the timestamp
                        last_update = datetime.fromisoformat(
                            last_update_str.replace("Z", "+00:00")
                        )
                        key = f"{source}_{dataset}"
                        last_times[key] = last_update
                        logger.debug(f"Loaded last time for {key}: {last_update}")
                    except ValueError as e:
                        logger.warning(
                            f"Could not parse timestamp '{last_update_str}' for {source}_{dataset}: {e}"
                        )
                        # Default to 4 hours ago if can't parse
                        last_times[f"{source}_{dataset}"] = current_time - timedelta(
                            hours=4
                        )

            # If no data found, set defaults
            if not last_times:
                logger.info("No existing tracking data found. Setting defaults.")
                default_time = current_time - timedelta(hours=4)
                last_times = {"ELEXON_ALL": default_time, "NESO_ALL": default_time}

            return last_times

        except Exception as e:
            logger.error(f"Error reading from Google Sheets: {e}")
            # Return safe defaults
            current_time = datetime.now(timezone.utc)
            return {
                "ELEXON_HIGH": current_time - timedelta(minutes=30),
                "ELEXON_STANDARD": current_time - timedelta(minutes=45),
                "REMIT_ALL": current_time - timedelta(minutes=45),
                "NESO_ALL": current_time - timedelta(hours=3),
            }

    def update_ingestion_time(
        self, source: str, dataset: str, timestamp: datetime, status: str = "SUCCESS"
    ):
        """Update the last ingestion time in Google Sheets"""
        if self.dry_run:
            logger.info(f"Dry run mode: would update {source}_{dataset} to {timestamp}")
            return

        if not self.sheet:
            logger.warning(
                f"Google Sheets not available, skipping update for {source}_{dataset}"
            )
            return

        try:
            current_time = datetime.now(timezone.utc)

            # Prepare the new row data
            new_row = [
                source,
                dataset,
                timestamp.isoformat(),
                status,
                current_time.isoformat(),
                f"Automated update at {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            ]

            # Try to find existing row first
            try:
                data = self.sheet.get_all_records()
                row_index = None

                for i, row in enumerate(data):
                    if (
                        row.get("Source", "").strip() == source
                        and row.get("Dataset", "").strip() == dataset
                    ):
                        row_index = (
                            i + 2
                        )  # +2 because sheets are 1-indexed and we skip header
                        break

                if row_index:
                    # Update existing row
                    self.sheet.update(f"A{row_index}:F{row_index}", [new_row])
                    logger.info(
                        f"Updated existing row {row_index} for {source}_{dataset}"
                    )
                else:
                    # Append new row
                    self.sheet.append_row(new_row)
                    logger.info(f"Added new row for {source}_{dataset}")

            except Exception as e:
                logger.warning(f"Could not update existing row, appending new: {e}")
                # Just append if we can't find/update existing
                self.sheet.append_row(new_row)

        except Exception as e:
            logger.error(f"Failed to update Google Sheets: {e}")
            # Don't fail the whole process if sheets update fails

    def ensure_sheet_headers(self):
        """Ensure the Google Sheet has proper headers"""
        if self.dry_run or not self.sheet:
            logger.info("Dry run mode or no Google Sheets: skipping header check")
            return

        try:
            headers = [
                "Source",
                "Dataset",
                "Last_Update",
                "Status",
                "Tracked_At",
                "Notes",
            ]

            # Check if headers exist
            first_row = self.sheet.row_values(1)
            if not first_row or first_row != headers:
                # Set headers
                self.sheet.update("A1:F1", [headers])
                logger.info("Sheet headers initialized")

        except Exception as e:
            logger.error(f"Failed to set sheet headers: {e}")

    def get_incremental_date_range(
        self, last_time: datetime, buffer_minutes: int = 30
    ) -> Tuple[str, str]:
        """Calculate the date range for incremental ingestion"""
        current_time = datetime.now(timezone.utc)

        # Add buffer to ensure we don't miss data
        start_time = last_time - timedelta(minutes=buffer_minutes)
        end_time = current_time

        # Format for the ingestion script
        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")

        logger.info(f"Incremental range: {start_str} to {end_str}")
        return start_str, end_str

    def check_bigquery_data_freshness(
        self, dataset_name: str, hours_threshold: int = 2
    ) -> bool:
        """Check if BigQuery data is fresh enough"""
        if self.dry_run or not self.bq_client:
            logger.info(
                f"Dry run mode or no BigQuery client: assuming {dataset_name} is stale"
            )
            return False

        try:
            table_id = f"{BQ_PROJECT}.{BQ_DATASET}.bmrs_{dataset_name.lower()}"

            query = f"""
            SELECT MAX(_window_from_utc) as latest_data
            FROM `{table_id}`
            WHERE _window_from_utc IS NOT NULL
            """

            result = self.bq_client.query(query).to_dataframe()
            if result.empty or result["latest_data"].iloc[0] is None:
                return False

            latest_data = pd.to_datetime(result["latest_data"].iloc[0])
            current_time = datetime.now(timezone.utc)

            age_hours = (
                current_time - latest_data.tz_localize("UTC")
            ).total_seconds() / 3600

            logger.info(
                f"Dataset {dataset_name}: latest data is {age_hours:.1f} hours old"
            )
            return age_hours <= hours_threshold

        except Exception as e:
            logger.warning(f"Could not check freshness for {dataset_name}: {e}")
            return False


def main():
    """Main automation function"""
    logger.info("🚀 Starting automated data tracking update...")

    tracker = DataTracker()

    try:
        # Ensure sheet headers are set
        tracker.ensure_sheet_headers()

        # Get last ingestion times
        last_times = tracker.get_last_ingestion_times()

        current_time = datetime.now(timezone.utc)

        # Process Elexon data
        elexon_last = last_times.get("ELEXON_ALL", current_time - timedelta(hours=4))
        time_since_elexon = current_time - elexon_last

        logger.info(
            f"Last Elexon update: {elexon_last} ({time_since_elexon.total_seconds()/60:.1f} minutes ago)"
        )

        # Process NESO data
        neso_last = last_times.get("NESO_ALL", current_time - timedelta(hours=4))
        time_since_neso = current_time - neso_last

        logger.info(
            f"Last NESO update: {neso_last} ({time_since_neso.total_seconds()/60:.1f} minutes ago)"
        )

        logger.info("✅ Automated tracker run complete")

    except Exception as e:
        logger.error(f"Error in automated data tracker: {e}")


if __name__ == "__main__":
    main()
