#!/usr/bin/env python3
"""
ELEXON Insights IRIS Monitor
---------------------------
Monitors real-time notifications from ELEXON's IRIS service using Azure Service Bus.
Provides real-time and historical access to system warnings, outages, and notifications.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from azure.identity import ClientSecretCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from google.api_core import retry
from google.cloud import bigquery

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class IRISMonitor:
    def __init__(
        self, project_id: Optional[str] = None, dataset_id: Optional[str] = None
    ):
        """Initialize the IRIS monitor with Azure and BigQuery credentials."""
        # IRIS Service Bus connection details
        self.namespace = "elexon-insights-iris"
        self.queue_name = "iris.047b7f5d-7cc1-4f3d-a454-fe188a9f42f3"
        self.tenant_id = "4203b7a0-7773-4de5-b830-8b263a20426e"
        self.client_id = "5ac22e4f-fcfa-4be8-b513-a6dc767d6312"

        # BigQuery settings
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.dataset_id = dataset_id or "uk_energy_insights"
        self.table_id = "bmrs_notifications"

        # Initialize BigQuery
        self.bq_client = bigquery.Client(project=self.project_id)
        self._ensure_bigquery_table()

        # Full connection string
        self.servicebus_url = "https://elexon-insights-iris.servicebus.windows.net/iris.047b7f5d-7cc1-4f3d-a454-fe188a9f42f3"

        # Initialize credentials and infrastructure
        self._initialize_credentials()
        self._ensure_bigquery_table()

    def _ensure_bigquery_table(self):
        """Create BigQuery table if it doesn't exist."""
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("notification_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("message", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("affected_units", "STRING", mode="REPEATED"),
            bigquery.SchemaField("start_time", "TIMESTAMP"),
            bigquery.SchemaField("end_time", "TIMESTAMP"),
            bigquery.SchemaField("capacity_affected_mw", "FLOAT64"),
            bigquery.SchemaField("raw_payload", "STRING", mode="REQUIRED"),
        ]

        table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"

        try:
            # Check if table exists
            self.bq_client.get_table(table_id)
            logger.info(f"✅ BigQuery table exists: {table_id}")
        except Exception:
            # Create table
            table = bigquery.Table(table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY, field="timestamp"
            )
            self.bq_client.create_table(table)
            logger.info(f"✅ Created BigQuery table: {table_id}")

    def _initialize_credentials(self):
        """Initialize Azure credentials."""
        try:
            self.credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=os.getenv(
                    "IRIS_CLIENT_SECRET"
                ),  # Get from environment variable
            )
            logger.info("✅ Successfully initialized Azure credentials")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure credentials: {str(e)}")
            raise

    def download_historical_alerts(self, year: int = 2025, batch_size: int = 1000):
        """
        Download all historical alerts for a given year.

        Args:
            year: The year to download alerts for
            batch_size: How many alerts to process in each batch
        """
        try:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)

            logger.info(f"📥 Downloading alerts for {year}")
            logger.info(f"   From: {start_date}")
            logger.info(f"   To:   {end_date}")

            # Create Azure Service Bus client
            servicebus_client = ServiceBusClient(
                fully_qualified_namespace=self.namespace,
                credential=self.credential,
            )

            downloaded = 0
            with servicebus_client.get_queue_receiver(
                queue_name=self.queue_name,
                sub_queue=None,  # Main queue
                max_wait_time=30,  # 30 second timeout
                receive_mode="peekLock",  # Don't remove messages
            ) as receiver:
                while True:
                    # Get a batch of messages
                    messages = receiver.peek_messages(
                        max_message_count=batch_size,
                        sequence_number=None,  # Start from beginning
                    )

                    if not messages:
                        break

                    # Process messages
                    for msg in messages:
                        try:
                            # Parse message
                            body = json.loads(str(msg))

                            # Check if message is within our date range
                            msg_time = datetime.fromisoformat(
                                body.get("timestamp", "").replace("Z", "+00:00")
                            )
                            if start_date <= msg_time <= end_date:
                                # Store in BigQuery
                                self._store_notification(body)
                                downloaded += 1

                                if downloaded % 100 == 0:
                                    logger.info(f"✓ Downloaded {downloaded} alerts...")

                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Skipping invalid JSON message")
                            continue
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {str(e)}")
                            continue

                    # Add a small delay to avoid hitting rate limits
                    time.sleep(1)

            logger.info(f"✅ Downloaded {downloaded} alerts for {year}")

        except Exception as e:
            logger.error(f"❌ Error downloading historical alerts: {str(e)}")
            raise

    def monitor_live_notifications(
        self, notification_types: Optional[List[str]] = None
    ):
        """
        Monitor live notifications from IRIS service.

        Args:
            notification_types: Optional list of notification types to filter
                              ['REMIT', 'SYSTEM_WARN', 'MARGIN', etc.]
        """
        try:
            # Create a Service Bus client
            servicebus_client = ServiceBusClient(
                fully_qualified_namespace=self.namespace,
                credential=self.credential,
            )

            logger.info("✅ Connected to IRIS Service Bus")
            logger.info(f"📡 Monitoring queue: {self.queue_name}")

            # Create a receiver for the queue
            with servicebus_client.get_queue_receiver(
                queue_name=self.queue_name
            ) as receiver:
                logger.info("🎯 Waiting for notifications... (Press Ctrl+C to stop)")

                while True:
                    try:
                        # Receive messages in batches
                        messages = receiver.receive_messages(
                            max_message_count=10, max_wait_time=5
                        )

                        for msg in messages:
                            try:
                                # Parse message body
                                body = json.loads(str(msg))

                                # Filter by notification type if specified
                                if (
                                    notification_types
                                    and body.get("type") not in notification_types
                                ):
                                    continue

                                # Store notification in BigQuery
                                self._store_notification(body)

                                # Print notification details
                                self._print_notification(body)

                                # Complete the message (remove from queue)
                                receiver.complete_message(msg)

                            except json.JSONDecodeError:
                                logger.warning("⚠️ Received invalid JSON message")
                                receiver.dead_letter_message(msg)

                    except Exception as e:
                        logger.error(f"❌ Error processing messages: {str(e)}")
                        break

        except KeyboardInterrupt:
            logger.info("\n⏹️ Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in live monitoring: {str(e)}")
            raise

    def _store_notification(self, notification: Dict):
        """Store notification in BigQuery."""
        try:
            # Prepare the row data
            row = {
                "timestamp": datetime.now().isoformat(),
                "notification_id": notification.get(
                    "id", str(datetime.now().timestamp())
                ),
                "type": notification.get("type", "Unknown"),
                "status": notification.get("status", "Unknown"),
                "message": notification.get("message", ""),
                "affected_units": notification.get("affected_units", []),
                "start_time": notification.get("start_time"),
                "end_time": notification.get("end_time"),
                "capacity_affected_mw": notification.get("capacity_affected_mw"),
                "raw_payload": json.dumps(notification),
            }

            # Insert into BigQuery with retry
            table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            errors = self.bq_client.insert_rows_json(
                table_id, [row], retry=retry.Retry(deadline=30)
            )

            if not errors:
                logger.info("✅ Notification stored in BigQuery")
            else:
                logger.error(f"❌ Errors inserting into BigQuery: {errors}")

        except Exception as e:
            logger.error(f"❌ Error storing notification: {str(e)}")

    def _print_notification(self, notification: Dict):
        """Print a formatted notification."""
        print("\n" + "=" * 50)
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📝 Type: {notification.get('type', 'Unknown')}")
        print(f"📊 Status: {notification.get('status', 'Unknown')}")

        # Print affected units if present
        if units := notification.get("affected_units"):
            print("\n🏭 Affected Units:")
            for unit in units:
                print(f"  - {unit}")

        # Print detailed message
        if msg := notification.get("message"):
            print("\n📄 Message:")
            print(msg)

        print("=" * 50 + "\n")


def main():
    """Main execution."""
    try:
        # Check for required environment variable
        if not os.getenv("IRIS_CLIENT_SECRET"):
            print("⚠️ Error: IRIS_CLIENT_SECRET environment variable not set")
            print("Please set your IRIS client secret:")
            print("export IRIS_CLIENT_SECRET='your-client-secret-here'")
            return 1

        # Initialize monitor
        monitor = IRISMonitor()

        # Parse command line arguments
        import argparse

        parser = argparse.ArgumentParser(description="ELEXON IRIS Monitor")

        # Add download option
        parser.add_argument(
            "--download-year",
            type=int,
            help="Download historical alerts for a specific year",
        )
        parser.add_argument(
            "--notification-types",
            type=str,
            nargs="+",
            choices=["REMIT", "SYSTEM_WARN", "MARGIN"],
            help="Types of notifications to monitor",
        )
        parser.add_argument(
            "--download-year",
            type=int,
            help="Download historical alerts for a specific year",
        )
        args = parser.parse_args()

        if args.download_year:
            # Download historical alerts for specified year
            monitor.download_historical_alerts(year=args.download_year)
            return 0

        # Start monitoring
        monitor.monitor_live_notifications(notification_types=args.notification_types)

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
