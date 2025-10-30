#!/usr/bin/env python3
"""
BMRS Notifications Monitor
-------------------------
Monitors various BMRS notifications including REMIT messages, system warnings,
and operational updates. Uses the BMRS API to fetch real-time notifications.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BMRSNotificationMonitor:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the BMRS notification monitor."""
        self.api_key = api_key or os.getenv("BMRS_API_KEY")
        if not self.api_key:
            print("⚠️  Warning: No BMRS API key found!")
            print("Please set your BMRS API key using one of these methods:")
            print("1. Set BMRS_API_KEY environment variable:")
            print("   export BMRS_API_KEY='your-api-key-here'")
            print("2. Pass the API key directly:")
            print("   ./monitor_bmrs_notifications.py --api-key your-api-key-here")
            print(
                "\nYou can get an API key from the BMRS portal: https://www.bmreports.com/bmrs"
            )
            raise ValueError("BMRS API key is required")

        self.base_url = "https://api.bmreports.com/BMRS"

    def fetch_historical_notifications(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        notification_types: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical notifications for a specific date range.

        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format (defaults to today)
            notification_types: List of notification types to fetch
                             ['REMIT', 'SYSTEM_WARN', 'MARGIN'] (defaults to all)

        Returns:
            Dictionary of DataFrames containing historical notifications by type
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        if notification_types is None:
            notification_types = ["REMIT", "SYSTEM_WARN", "MARGIN"]

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        results = {}

        logger.info(f"Fetching historical data from {start_date} to {end_date}")

        if "REMIT" in notification_types:
            params = {
                "APIKey": self.api_key,
                "ServiceType": "xml",
                "EventStart": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "EventEnd": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "EventType": "REMIT",
            }

            try:
                response = self._make_request("REMIT", params)
                messages = self._parse_remit_response(response)
                results["REMIT"] = pd.DataFrame(messages)
                logger.info(
                    f"Fetched {len(results['REMIT'])} historical REMIT messages"
                )
            except Exception as e:
                logger.error(f"Error fetching historical REMIT data: {str(e)}")
                results["REMIT"] = pd.DataFrame()

        if "SYSTEM_WARN" in notification_types:
            params = {
                "APIKey": self.api_key,
                "ServiceType": "xml",
                "FromDateTime": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "ToDateTime": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "MessageType": "SYSTEM_WARN",
            }

            try:
                response = self._make_request("MESSAGELISTINGS", params)
                warnings = self._parse_system_warnings(response)
                results["SYSTEM_WARN"] = pd.DataFrame(warnings)
                logger.info(
                    f"Fetched {len(results['SYSTEM_WARN'])} historical system warnings"
                )
            except Exception as e:
                logger.error(f"Error fetching historical system warnings: {str(e)}")
                results["SYSTEM_WARN"] = pd.DataFrame()

        if "MARGIN" in notification_types:
            params = {
                "APIKey": self.api_key,
                "ServiceType": "xml",
                "FromDateTime": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "ToDateTime": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "MessageType": "MARGIN",
            }

            try:
                response = self._make_request("SYSDEM", params)
                margins = self._parse_capacity_margins(response)
                results["MARGIN"] = pd.DataFrame(margins)
                logger.info(
                    f"Fetched {len(results['MARGIN'])} historical capacity margins"
                )
            except Exception as e:
                logger.error(f"Error fetching historical capacity margins: {str(e)}")
                results["MARGIN"] = pd.DataFrame()

        # Add timestamps and sort
        for key in results:
            if not results[key].empty:
                results[key]["timestamp"] = pd.to_datetime(results[key]["publishTime"])
                results[key] = results[key].sort_values("timestamp", ascending=False)

        return results

    def fetch_remit_messages(self, hours_back: int = 24) -> pd.DataFrame:
        """
        Fetch REMIT messages for power station outages and updates.

        Args:
            hours_back: How many hours of history to fetch

        Returns:
            DataFrame containing REMIT messages
        """
        from_time = datetime.now() - timedelta(hours=hours_back)

        params = {
            "APIKey": self.api_key,
            "ServiceType": "xml",
            "EventStart": from_time.strftime("%Y-%m-%d %H:%M:%S"),
            "EventType": "REMIT",
        }

        try:
            response = self._make_request("REMIT", params)
            messages = self._parse_remit_response(response)

            df = pd.DataFrame(messages)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["publishTime"])
                df = df.sort_values("timestamp", ascending=False)

            logger.info(f"Fetched {len(df)} REMIT messages")
            return df

        except Exception as e:
            logger.error(f"Error fetching REMIT messages: {str(e)}")
            return pd.DataFrame()

    def fetch_system_warnings(self, hours_back: int = 24) -> pd.DataFrame:
        """
        Fetch system warnings (SYSWARN, NISM, HIST, etc.).

        Args:
            hours_back: How many hours of history to fetch

        Returns:
            DataFrame containing system warnings
        """
        from_time = datetime.now() - timedelta(hours=hours_back)

        params = {
            "APIKey": self.api_key,
            "ServiceType": "xml",
            "FromDateTime": from_time.strftime("%Y-%m-%d %H:%M:%S"),
            "MessageType": "SYSTEM_WARN",
        }

        try:
            response = self._make_request("MESSAGELISTINGS", params)
            warnings = self._parse_system_warnings(response)

            df = pd.DataFrame(warnings)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["publishTime"])
                df = df.sort_values("timestamp", ascending=False)

            logger.info(f"Fetched {len(df)} system warnings")
            return df

        except Exception as e:
            logger.error(f"Error fetching system warnings: {str(e)}")
            return pd.DataFrame()

    def fetch_capacity_margins(self, hours_back: int = 24) -> pd.DataFrame:
        """
        Fetch capacity margin notices and warnings.

        Args:
            hours_back: How many hours of history to fetch

        Returns:
            DataFrame containing capacity margins
        """
        from_time = datetime.now() - timedelta(hours=hours_back)

        params = {
            "APIKey": self.api_key,
            "ServiceType": "xml",
            "FromDateTime": from_time.strftime("%Y-%m-%d %H:%M:%S"),
            "MessageType": "MARGIN",
        }

        try:
            response = self._make_request("SYSDEM", params)
            margins = self._parse_capacity_margins(response)

            df = pd.DataFrame(margins)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["publishTime"])
                df = df.sort_values("timestamp", ascending=False)

            logger.info(f"Fetched {len(df)} capacity margin notices")
            return df

        except Exception as e:
            logger.error(f"Error fetching capacity margins: {str(e)}")
            return pd.DataFrame()

    def monitor_live_notifications(self, update_interval: int = 300):
        """
        Continuously monitor for new notifications.

        Args:
            update_interval: Seconds between updates
        """
        while True:
            try:
                # Fetch recent notifications
                remit_df = self.fetch_remit_messages(hours_back=1)
                warnings_df = self.fetch_system_warnings(hours_back=1)
                margins_df = self.fetch_capacity_margins(hours_back=1)

                # Print any new notifications
                self._print_new_notifications(remit_df, "REMIT Messages")
                self._print_new_notifications(warnings_df, "System Warnings")
                self._print_new_notifications(margins_df, "Capacity Margins")

                # Wait for next update
                logger.info(f"Waiting {update_interval} seconds for next update...")
                time.sleep(update_interval)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying

    def _make_request(self, endpoint: str, params: Dict) -> requests.Response:
        """Make a request to the BMRS API."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response

    def _parse_remit_response(self, response: requests.Response) -> List[Dict]:
        """Parse REMIT message response."""
        # Implementation depends on actual response format
        # This is a placeholder for the parsing logic
        return []

    def _parse_system_warnings(self, response: requests.Response) -> List[Dict]:
        """Parse system warnings response."""
        # Implementation depends on actual response format
        # This is a placeholder for the parsing logic
        return []

    def _parse_capacity_margins(self, response: requests.Response) -> List[Dict]:
        """Parse capacity margins response."""
        # Implementation depends on actual response format
        # This is a placeholder for the parsing logic
        return []

    def _print_new_notifications(self, df: pd.DataFrame, notification_type: str):
        """Print new notifications in a formatted way."""
        if df.empty:
            return

        print(f"\n=== New {notification_type} ===")
        for _, row in df.iterrows():
            print(f"Time: {row['timestamp']}")
            print(f"Type: {row.get('messageType', 'N/A')}")
            print(f"Status: {row.get('status', 'N/A')}")
            print(f"Message: {row.get('message', 'N/A')}")
            print("-" * 50)


def main():
    """Main execution."""
    try:
        # Parse command line arguments
        import argparse

        parser = argparse.ArgumentParser(description="BMRS Notification Monitor")

        # Add API key argument
        parser.add_argument(
            "--api-key",
            type=str,
            help="Your BMRS API key (alternatively, set BMRS_API_KEY environment variable)",
        )
        parser.add_argument(
            "--historical",
            action="store_true",
            help="Fetch historical data instead of live monitoring",
        )
        parser.add_argument(
            "--start-date", type=str, help="Start date for historical data (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--end-date", type=str, help="End date for historical data (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--notification-types",
            type=str,
            nargs="+",
            choices=["REMIT", "SYSTEM_WARN", "MARGIN"],
            help="Types of notifications to fetch",
        )
        args = parser.parse_args()

        # Initialize the monitor with API key
        monitor = BMRSNotificationMonitor(api_key=args.api_key)

        if args.historical:
            if not args.start_date:
                print("Error: --start-date is required for historical data")
                return 1

            # Fetch historical notifications
            historical_data = monitor.fetch_historical_notifications(
                start_date=args.start_date,
                end_date=args.end_date,
                notification_types=args.notification_types,
            )

            # Print historical data
            for notification_type, df in historical_data.items():
                print(f"\n=== Historical {notification_type} Notifications ===")
                if not df.empty:
                    print(
                        df[
                            ["timestamp", "messageType", "status", "message"]
                        ].to_string()
                    )
                else:
                    print(f"No {notification_type} notifications found for this period")

        else:
            # Fetch recent notifications
            print("\n=== Recent REMIT Messages ===")
            remit_df = monitor.fetch_remit_messages(hours_back=24)
            if not remit_df.empty:
                print(
                    remit_df[
                        ["timestamp", "messageType", "status", "message"]
                    ].to_string()
                )

            print("\n=== Recent System Warnings ===")
            warnings_df = monitor.fetch_system_warnings(hours_back=24)
            if not warnings_df.empty:
                print(
                    warnings_df[
                        ["timestamp", "messageType", "status", "message"]
                    ].to_string()
                )

            print("\n=== Recent Capacity Margins ===")
            margins_df = monitor.fetch_capacity_margins(hours_back=24)
            if not margins_df.empty:
                print(
                    margins_df[
                        ["timestamp", "messageType", "status", "message"]
                    ].to_string()
                )

            # Start live monitoring
            print("\nStarting live monitoring (Press Ctrl+C to stop)...")
            monitor.monitor_live_notifications()

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
