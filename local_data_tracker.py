#!/usr/bin/env python3
"""
Local File-Based Data Tracker

This is a drop-in replacement for the Google Sheets-based DataTracker,
allowing the system to work without requiring Google Sheets credentials.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("local_tracker.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Path to the local tracking file
TRACKER_FILE = "data_tracker.json"


class LocalDataTracker:
    """Local file-based implementation of the DataTracker interface"""

    def __init__(self):
        """Initialize the tracker"""
        self.tracker_data = self._load_tracker_data()

    def _load_tracker_data(self) -> Dict[str, Any]:
        """Load tracker data from file"""
        try:
            if os.path.exists(TRACKER_FILE):
                with open(TRACKER_FILE, "r") as f:
                    return json.load(f)
            else:
                # Create default structure
                default_data = {
                    "last_ingestion_times": {},
                    "ingestion_history": [],
                    "metadata": {
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                }
                with open(TRACKER_FILE, "w") as f:
                    json.dump(default_data, f, indent=2)
                return default_data
        except Exception as e:
            logger.error(f"Error loading tracker data: {e}")
            # Return empty structure on error
            return {
                "last_ingestion_times": {},
                "ingestion_history": [],
                "metadata": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(e),
                },
            }

    def _save_tracker_data(self):
        """Save tracker data to file"""
        try:
            # Update metadata
            self.tracker_data["metadata"]["updated_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            # Write to file
            with open(TRACKER_FILE, "w") as f:
                json.dump(self.tracker_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tracker data: {e}")

    def get_last_ingestion_times(self) -> Dict[str, datetime]:
        """Get dictionary of last ingestion times for all data sources"""
        result = {}

        try:
            for key, timestamp_str in self.tracker_data["last_ingestion_times"].items():
                try:
                    # Convert ISO string to datetime
                    result[key] = datetime.fromisoformat(timestamp_str)
                except:
                    # Skip entries with invalid timestamps
                    continue

            return result
        except Exception as e:
            logger.error(f"Error getting last ingestion times: {e}")
            return {}

    def update_ingestion_time(
        self,
        data_source: str,
        category: str,
        timestamp: datetime,
        status: str,
        details: Optional[Dict] = None,
    ):
        """Update the ingestion time for a data source"""
        try:
            # Create the key (e.g., "ELEXON_HIGH")
            key = f"{data_source}_{category}"

            # Update last ingestion time
            self.tracker_data["last_ingestion_times"][key] = timestamp.isoformat()

            # Add to history
            history_entry = {
                "data_source": data_source,
                "category": category,
                "timestamp": timestamp.isoformat(),
                "status": status,
            }

            if details:
                history_entry["details"] = details

            self.tracker_data["ingestion_history"].append(history_entry)

            # Limit history to 1000 entries
            if len(self.tracker_data["ingestion_history"]) > 1000:
                self.tracker_data["ingestion_history"] = self.tracker_data[
                    "ingestion_history"
                ][-1000:]

            # Save changes
            self._save_tracker_data()

            logger.info(
                f"Updated ingestion time for {key}: {timestamp.isoformat()} ({status})"
            )

        except Exception as e:
            logger.error(f"Error updating ingestion time: {e}")

    # Additional methods to match the DataTracker interface
    def get_ingestion_history(self, limit: int = 100) -> list:
        """Get ingestion history"""
        try:
            return self.tracker_data["ingestion_history"][-limit:]
        except Exception as e:
            logger.error(f"Error getting ingestion history: {e}")
            return []
