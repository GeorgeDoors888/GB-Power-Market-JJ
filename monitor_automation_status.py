#!/usr/bin/env python3
"""
Energy Data Automation Status Monitor
Shows the current status of the 15-minute automation system
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone

from automated_data_tracker import DataTracker


def get_cron_status():
    """Check if the cron job is active"""
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode == 0:
            cron_content = result.stdout
            if "energy_15min_updater.sh" in cron_content:
                return "✅ Active"
            else:
                return "❌ Not found"
        else:
            return "❌ No crontab"
    except Exception as e:
        return f"❌ Error: {e}"


def get_recent_logs(log_dir, hours=2):
    """Get recent log entries"""
    try:
        log_files = []
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.endswith(".log"):
                    filepath = os.path.join(log_dir, filename)
                    stat = os.stat(filepath)
                    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

                    if (
                        datetime.now(timezone.utc) - mtime
                    ).total_seconds() < hours * 3600:
                        log_files.append((filepath, mtime))

        log_files.sort(key=lambda x: x[1], reverse=True)
        return log_files[:5]  # Return 5 most recent

    except Exception as e:
        return []


def main():
    """Main status monitoring function"""
    print("🔍 Energy Data Automation Status Monitor")
    print("=" * 50)

    # Check Google Sheets connectivity
    print("\n📊 Google Sheets Integration:")
    try:
        tracker = DataTracker()
        last_times = tracker.get_last_ingestion_times()
        print("   ✅ Connected and accessible")

        print("\n📈 Last Update Times:")
        for key, timestamp in last_times.items():
            age = datetime.now(timezone.utc) - timestamp
            age_str = f"{age.total_seconds()/60:.1f} minutes ago"
            print(
                f"   • {key}: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')} ({age_str})"
            )

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Check cron job status
    print("\n⏰ Cron Job Status:")
    cron_status = get_cron_status()
    print(f"   {cron_status}")

    # Check virtual environment
    print("\n🐍 Virtual Environment:")
    venv_path = (
        "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/.venv_ingestion"
    )
    if os.path.exists(venv_path):
        print("   ✅ Virtual environment exists")

        # Check key packages
        try:
            import subprocess

            result = subprocess.run(
                [
                    f"{venv_path}/bin/python",
                    "-c",
                    "import pandas, google.cloud.bigquery, gspread; print('All packages OK')",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("   ✅ All required packages installed")
            else:
                print(f"   ❌ Package issues: {result.stderr}")
        except Exception as e:
            print(f"   ⚠️  Could not verify packages: {e}")
    else:
        print("   ❌ Virtual environment not found")

    # Check recent logs
    print("\n📝 Recent Activity:")
    script_dir = "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"
    log_dir = os.path.join(script_dir, "logs", "automation")

    recent_logs = get_recent_logs(log_dir)
    if recent_logs:
        for log_path, mtime in recent_logs:
            filename = os.path.basename(log_path)
            age = datetime.now(timezone.utc) - mtime
            print(f"   • {filename}: {age.total_seconds()/60:.0f} min ago")
    else:
        print("   ⚠️  No recent log files found")

    # Check disk space
    print("\n💾 System Resources:")
    try:
        stat = os.statvfs(script_dir)
        free_space_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        print(f"   • Free disk space: {free_space_gb:.1f} GB")

        if free_space_gb < 1:
            print("   ⚠️  Low disk space warning!")

    except Exception as e:
        print(f"   ⚠️  Could not check disk space: {e}")

    # Check BigQuery connectivity
    print("\n🗃️  BigQuery Connectivity:")
    try:
        from google.cloud import bigquery

        client = bigquery.Client(project="jibber-jabber-knowledge")

        # Test query
        query = "SELECT COUNT(*) as table_count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`"
        result = client.query(query).to_dataframe()
        table_count = result["table_count"].iloc[0]

        print(f"   ✅ Connected - {table_count} tables available")

    except Exception as e:
        print(f"   ❌ Connection error: {e}")

    # Summary and recommendations
    print("\n📋 Summary & Recommendations:")
    print("   • System is configured for 15-minute automated updates")
    print("   • Tracks last update times in Google Sheets")
    print("   • Only ingests missing data since last successful run")
    print("   • Logs all activities for monitoring")
    print("")
    print("🔧 Management Commands:")
    print(f"   • Manual update: {script_dir}/energy_15min_updater.sh")
    print(f"   • View logs: tail -f {log_dir}/15min_updates_$(date +%Y%m%d).log")
    print("   • Edit cron: crontab -e")
    print("")
    print("🌐 Monitor your data at:")
    print(
        "   https://docs.google.com/spreadsheets/d/1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw/edit"
    )


if __name__ == "__main__":
    main()
