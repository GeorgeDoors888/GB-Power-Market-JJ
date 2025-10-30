#!/usr/bin/env python3
"""
Status Reporting Script
Sends status reports for the energy data update system
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Optional

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class StatusReporter:
    def __init__(self, log_file: Optional[str] = None):
        self.setup_logging(log_file)

    def setup_logging(self, log_file: Optional[str] = None):
        """Setup logging configuration"""
        log_format = "%(asctime)s - STATUS_REPORTER - %(levelname)s - %(message)s"

        handlers = [logging.StreamHandler(sys.stdout)]
        if log_file:
            handlers.append(logging.FileHandler(log_file, mode="a"))

        logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)

        self.logger = logging.getLogger(__name__)

    def generate_status_report(
        self, status: str, duration: float, failed_jobs: int
    ) -> Dict:
        """Generate a status report"""
        timestamp = datetime.now(timezone.utc)

        report = {
            "timestamp": timestamp.isoformat(),
            "status": status,
            "duration_seconds": duration,
            "failed_jobs": failed_jobs,
            "success": status == "success",
            "summary": self._generate_summary(status, duration, failed_jobs),
        }

        return report

    def _generate_summary(self, status: str, duration: float, failed_jobs: int) -> str:
        """Generate a human-readable summary"""
        if status == "success":
            return f"✅ All updates completed successfully in {duration:.1f}s"
        elif status == "partial":
            return f"⚠️ Updates completed with {failed_jobs} failures in {duration:.1f}s"
        else:
            return f"❌ Updates failed with {failed_jobs} errors in {duration:.1f}s"

    def save_status_report(self, report: Dict, output_file: str):
        """Save status report to file"""
        try:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Status report saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save status report: {e}")

    def send_email_alert(self, report: Dict, recipients: list):
        """Send email alert (placeholder for future implementation)"""
        # TODO: Implement email sending
        self.logger.info(f"Email alert would be sent to: {', '.join(recipients)}")
        self.logger.info(f"Subject: Energy Data Update - {report['status'].title()}")
        self.logger.info(f"Message: {report['summary']}")

    def send_slack_alert(self, report: Dict, webhook_url: str):
        """Send Slack alert (placeholder for future implementation)"""
        # TODO: Implement Slack webhook
        self.logger.info(f"Slack alert would be sent to: {webhook_url}")
        self.logger.info(f"Message: {report['summary']}")

    def log_status_report(self, report: Dict):
        """Log the status report"""
        self.logger.info("=" * 50)
        self.logger.info("ENERGY DATA UPDATE STATUS REPORT")
        self.logger.info("=" * 50)
        self.logger.info(f"Timestamp: {report['timestamp']}")
        self.logger.info(f"Status: {report['status']}")
        self.logger.info(f"Duration: {report['duration_seconds']:.1f}s")
        self.logger.info(f"Failed Jobs: {report['failed_jobs']}")
        self.logger.info(f"Summary: {report['summary']}")
        self.logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Energy Data Update Status Reporter")
    parser.add_argument(
        "--status",
        required=True,
        choices=["success", "partial", "error"],
        help="Status of the update process",
    )
    parser.add_argument(
        "--duration",
        type=float,
        required=True,
        help="Duration of the update process in seconds",
    )
    parser.add_argument(
        "--failed-jobs", type=int, default=0, help="Number of failed jobs"
    )
    parser.add_argument("--log-file", help="Path to log file for output")
    parser.add_argument("--output-file", help="Path to save status report JSON")
    parser.add_argument(
        "--email-recipients", nargs="+", help="Email addresses to send alerts to"
    )
    parser.add_argument("--slack-webhook", help="Slack webhook URL for alerts")

    args = parser.parse_args()

    reporter = StatusReporter(args.log_file)

    try:
        # Generate status report
        report = reporter.generate_status_report(
            args.status, args.duration, args.failed_jobs
        )

        # Log the report
        reporter.log_status_report(report)

        # Save to file if requested
        if args.output_file:
            reporter.save_status_report(report, args.output_file)

        # Send email alerts if configured
        if args.email_recipients:
            reporter.send_email_alert(report, args.email_recipients)

        # Send Slack alerts if configured
        if args.slack_webhook:
            reporter.send_slack_alert(report, args.slack_webhook)

    except Exception as e:
        reporter.logger.error(f"Failed to generate status report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
