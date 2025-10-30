#!/usr/bin/env python3
"""
Real-time Energy Data Dashboard
Provides live monitoring of the automation system with refreshing status
"""

import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone

from automated_data_tracker import DataTracker


def clear_screen():
    """Clear the terminal screen"""
    os.system("clear" if os.name == "posix" else "cls")


def get_system_status():
    """Get comprehensive system status"""
    status = {
        "timestamp": datetime.now(timezone.utc),
        "google_sheets": "❌ Error",
        "cron_job": "❌ Error",
        "last_updates": {},
        "recent_activity": [],
        "disk_space_gb": 0,
        "bigquery_tables": 0,
        "automation_running": False,
    }

    try:
        # Google Sheets status
        tracker = DataTracker()
        last_times = tracker.get_last_ingestion_times()
        status["google_sheets"] = "✅ Connected"
        status["last_updates"] = last_times

        # Check if automation should run
        current_time = datetime.now(timezone.utc)
        elexon_last = last_times.get("ELEXON_ALL", current_time - timedelta(hours=4))
        time_since_elexon = current_time - elexon_last

        if time_since_elexon.total_seconds() > 600:  # 10 minutes
            status["automation_running"] = True

    except Exception as e:
        status["google_sheets"] = f"❌ Error: {str(e)[:50]}"

    try:
        # Cron status
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode == 0 and "energy_15min_updater.sh" in result.stdout:
            status["cron_job"] = "✅ Active"
        else:
            status["cron_job"] = "❌ Not found"
    except:
        status["cron_job"] = "❌ Error"

    try:
        # Disk space
        script_dir = "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"
        stat = os.statvfs(script_dir)
        status["disk_space_gb"] = (stat.f_bavail * stat.f_frsize) / (1024**3)
    except:
        pass

    try:
        # BigQuery tables
        from google.cloud import bigquery

        client = bigquery.Client(project="jibber-jabber-knowledge")
        query = "SELECT COUNT(*) as table_count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`"
        result = client.query(query).to_dataframe()
        status["bigquery_tables"] = result["table_count"].iloc[0]
    except:
        pass

    try:
        # Recent activity
        log_dir = (
            "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/logs/automation"
        )
        if os.path.exists(log_dir):
            log_files = []
            for filename in os.listdir(log_dir):
                if filename.endswith(".log"):
                    filepath = os.path.join(log_dir, filename)
                    stat = os.stat(filepath)
                    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                    log_files.append((filename, mtime))

            log_files.sort(key=lambda x: x[1], reverse=True)
            status["recent_activity"] = log_files[:3]
    except:
        pass

    return status


def display_dashboard(status):
    """Display the monitoring dashboard"""
    clear_screen()

    timestamp = status["timestamp"]
    print("🚀 ENERGY DATA AUTOMATION DASHBOARD")
    print("=" * 60)
    print(f"⏰ Last updated: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    # System Status
    print("🔧 SYSTEM STATUS")
    print("-" * 30)
    print(f"📊 Google Sheets: {status['google_sheets']}")
    print(f"⏰ Cron Job: {status['cron_job']}")
    print(f"💾 Disk Space: {status['disk_space_gb']:.1f} GB free")
    print(f"🗃️  BigQuery Tables: {status['bigquery_tables']}")
    print()

    # Data Update Status
    print("📈 LAST UPDATE TIMES")
    print("-" * 30)
    current_time = timestamp

    for source, last_update in status["last_updates"].items():
        age = current_time - last_update
        age_minutes = age.total_seconds() / 60

        if age_minutes < 15:
            status_icon = "🟢"
        elif age_minutes < 60:
            status_icon = "🟡"
        else:
            status_icon = "🔴"

        print(
            f"{status_icon} {source}: {last_update.strftime('%H:%M:%S')} ({age_minutes:.0f}m ago)"
        )

    print()

    # Activity Status
    print("⚡ AUTOMATION STATUS")
    print("-" * 30)

    if status["automation_running"]:
        print("🔄 Next update: Ready to run")
    else:
        print("⏸️  Next update: Waiting (data is recent)")

    print()

    # Recent Activity
    print("📝 RECENT ACTIVITY")
    print("-" * 30)

    if status["recent_activity"]:
        for filename, mtime in status["recent_activity"]:
            age = current_time - mtime
            age_str = f"{age.total_seconds()/60:.0f}m ago"
            print(f"📄 {filename}: {age_str}")
    else:
        print("📄 No recent log files")

    print()
    print("🔧 MANAGEMENT")
    print("-" * 30)
    print("• Press Ctrl+C to exit")
    print("• Manual update: ./energy_15min_updater.sh")
    print("• View logs: tail -f logs/automation/15min_updates_*.log")
    print("• Edit schedule: crontab -e")
    print()
    print(
        "🌐 Track data: https://docs.google.com/spreadsheets/d/1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw/edit"
    )


def main():
    """Main dashboard loop"""
    print("🚀 Starting Energy Data Automation Dashboard...")
    print("Press Ctrl+C to exit")
    time.sleep(2)

    try:
        while True:
            status = get_system_status()
            display_dashboard(status)

            # Update every 30 seconds
            time.sleep(30)

    except KeyboardInterrupt:
        clear_screen()
        print("👋 Dashboard stopped. Automation continues running in background.")
        print()
        print("The 15-minute automation system is still active via cron.")
        print("Monitor status anytime with: python monitor_automation_status.py")


if __name__ == "__main__":
    main()
