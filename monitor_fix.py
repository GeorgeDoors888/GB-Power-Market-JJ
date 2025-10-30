#!/usr/bin/env python3
"""
Monitor the failed datasets fix progress
"""

import os
import subprocess
import time
from datetime import datetime


def check_progress():
    """Check the current state of the fix."""

    # Check if process is running
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

        ingest_running = "ingest_elexon_fixed.py" in result.stdout
        fix_running = "fix_failed_datasets.py" in result.stdout

    except:
        ingest_running = False
        fix_running = False

    # Find latest log file
    log_files = [
        f
        for f in os.listdir(".")
        if f.startswith("fix_failed_datasets_") and f.endswith(".log")
    ]
    if log_files:
        latest_log = max(log_files, key=lambda x: os.path.getmtime(x))

        try:
            with open(latest_log, "r") as f:
                content = f.read()

            # Count successes and current progress
            success_lines = [
                line
                for line in content.split("\n")
                if "✅" in line and "SUCCESS" in line
            ]
            progress_lines = [
                line for line in content.split("\n") if "📊 Progress:" in line
            ]

            current_dataset = None
            if progress_lines:
                last_progress = progress_lines[-1]
                if " - " in last_progress:
                    current_dataset = last_progress.split(" - ")[-1]

            return {
                "ingest_running": ingest_running,
                "fix_running": fix_running,
                "successes": len(success_lines),
                "current_dataset": current_dataset,
                "log_file": latest_log,
            }
        except:
            return None

    return None


def main():
    """Monitor progress."""

    print("🔍 BMRS Failed Datasets Fix Monitor")
    print("=" * 40)

    start_time = datetime.now()

    while True:
        status = check_progress()

        current_time = datetime.now()
        elapsed = current_time - start_time

        print(
            f"\n⏰ {current_time.strftime('%H:%M:%S')} (Elapsed: {str(elapsed).split('.')[0]})"
        )

        if status:
            print(f"🏃 Fix script running: {'✅' if status['fix_running'] else '❌'}")
            print(f"🔄 Ingest running: {'✅' if status['ingest_running'] else '❌'}")
            print(f"✅ Completed: {status['successes']}/30")
            if status["current_dataset"]:
                print(f"📊 Current dataset: {status['current_dataset']}")
            print(f"📝 Log file: {status['log_file']}")

            # If both processes stopped, we're done
            if not status["fix_running"] and not status["ingest_running"]:
                print("\n🎉 All processes completed!")

                # Show final results
                try:
                    with open(status["log_file"], "r") as f:
                        content = f.read()

                    if "FINAL RESULTS" in content:
                        final_section = content.split("FINAL RESULTS")[-1]
                        print("\n📊 FINAL RESULTS:")
                        for line in final_section.split("\n")[:10]:
                            if line.strip():
                                print(line)
                except:
                    pass

                break
        else:
            print("❌ No progress information available")

        time.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    main()
