#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced data freshness monitoring script for Elexon BMRS data in BigQuery
Shows the most recent data, last modification times, and data freshness metrics
"""

import sys
from datetime import datetime, timedelta

from google.cloud import bigquery

# Try to import optional packages
try:
    import pytz
    import tabulate

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

# Color codes for terminal output
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
BOLD = "\033[1m"


def get_table_metadata(client, table_id):
    """Get table metadata including last modification time"""
    try:
        table_ref = bigquery.TableReference.from_string(table_id)
        table = client.get_table(table_ref)
        return {
            "modified": table.modified,
            "created": table.created,
            "num_rows": table.num_rows,
            "size_bytes": table.num_bytes,
        }
    except Exception as e:
        print(f"Error getting metadata for {table_id}: {e}")
        return None


def main():
    if not HAS_DEPS:
        print("For enhanced output, please install optional dependencies:")
        print("pip install tabulate pytz")
        print("\nRunning with basic output...\n")

    client = bigquery.Client(project="jibber-jabber-knowledge")
    project = "jibber-jabber-knowledge"
    dataset = "uk_energy_insights"

    # Current time in UTC for comparison
    utc_now = datetime.utcnow().replace(microsecond=0)
    if "pytz" in sys.modules:
        utc_now = datetime.now(pytz.UTC)

    print(f"\n{BOLD}{BLUE}ELEXON BMRS DATA FRESHNESS REPORT{RESET}")
    print(f"Generated at: {utc_now}")
    print("-" * 80)

    # HIGH FREQUENCY DATASETS (15-minute update cycle)
    high_freq_tables = ["freq", "fuelinst", "bod", "boalf", "disbsad", "imbalngc"]

    # MEDIUM FREQUENCY DATASETS (30-minute update cycle)
    medium_freq_tables = ["mels", "mils", "pn", "qpn", "netbsad"]

    # First check the most recent settlement date and period for each table
    latest_data_rows = []
    for table_name in high_freq_tables + medium_freq_tables:
        full_table_id = f"{project}.{dataset}.bmrs_{table_name}"

        # Get table metadata
        metadata = get_table_metadata(client, full_table_id)

        if not metadata:
            latest_data_rows.append(
                [table_name.upper(), "ERROR", "N/A", "N/A", "N/A", "N/A"]
            )
            continue

        # Query to get the most recent data
        query = f"""
        SELECT
          settlementDate,
          MAX(settlementPeriod) as latest_period,
          COUNT(*) as record_count,
          MAX(CAST(publishTime AS DATETIME)) as latest_publish
        FROM `{full_table_id}`
        WHERE settlementDate = (
          SELECT MAX(settlementDate)
          FROM `{full_table_id}`
        )
        GROUP BY settlementDate
        """

        try:
            result = list(client.query(query).result())

            if result:
                row = result[0]
                latest_date = row.settlementDate
                latest_period = row.latest_period
                record_count = row.record_count
                publish_time = row.latest_publish

                # Calculate freshness (difference between now and publish time)
                if publish_time:
                    # Convert to UTC if using pytz
                    if "pytz" in sys.modules and not publish_time.tzinfo:
                        publish_time = pytz.UTC.localize(publish_time)

                    freshness_hours = (utc_now - publish_time).total_seconds() / 3600
                    if freshness_hours < 1:
                        freshness_str = f"{GREEN}{freshness_hours:.2f} hours{RESET}"
                    elif freshness_hours < 24:
                        freshness_str = f"{YELLOW}{freshness_hours:.2f} hours{RESET}"
                    else:
                        freshness_str = f"{RED}{freshness_hours:.2f} hours{RESET}"
                else:
                    freshness_str = "N/A"

                # Metadata last modified time
                mod_time = metadata["modified"]
                # Convert to UTC if using pytz
                if "pytz" in sys.modules and not mod_time.tzinfo:
                    mod_time = pytz.UTC.localize(mod_time)

                mod_hours_ago = (utc_now - mod_time).total_seconds() / 3600

                if mod_hours_ago < 1:
                    mod_time_str = f"{GREEN}{mod_hours_ago:.2f} hours ago{RESET}"
                elif mod_hours_ago < 24:
                    mod_time_str = f"{YELLOW}{mod_hours_ago:.2f} hours ago{RESET}"
                else:
                    mod_time_str = f"{RED}{mod_hours_ago:.2f} hours ago{RESET}"

                latest_data_rows.append(
                    [
                        f"{BOLD}{table_name.upper()}{RESET}",
                        latest_date.strftime("%Y-%m-%d"),
                        latest_period,
                        record_count,
                        (
                            publish_time.strftime("%Y-%m-%d %H:%M")
                            if publish_time
                            else "N/A"
                        ),
                        freshness_str,
                        mod_time_str,
                    ]
                )
            else:
                latest_data_rows.append(
                    [table_name.upper(), "No data", "N/A", 0, "N/A", "N/A", "N/A"]
                )
        except Exception as e:
            latest_data_rows.append(
                [
                    table_name.upper(),
                    f"ERROR: {str(e)[:30]}...",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                ]
            )

    # Print table of results
    headers = [
        "Dataset",
        "Latest Date",
        "Latest Period",
        "Records",
        "Publish Time",
        "Data Age",
        "Last Modified",
    ]

    if "tabulate" in sys.modules:
        print(tabulate.tabulate(latest_data_rows, headers=headers, tablefmt="grid"))
    else:
        # Basic table format if tabulate not available
        print("\n{:<10} {:<12} {:<14} {:<10} {:<20} {:<15} {:<15}".format(*headers))
        print("-" * 100)
        for row in latest_data_rows:
            # Strip ANSI color codes for basic output
            clean_row = [
                str(col)
                .replace(RED, "")
                .replace(GREEN, "")
                .replace(YELLOW, "")
                .replace(BLUE, "")
                .replace(MAGENTA, "")
                .replace(CYAN, "")
                .replace(BOLD, "")
                .replace(RESET, "")
                for col in row
            ]
            print("{:<10} {:<12} {:<14} {:<10} {:<20} {:<15} {:<15}".format(*clean_row))

    # Quick summary and recommendations
    print("\n" + "=" * 80)
    print(f"{BOLD}DATA FRESHNESS SUMMARY{RESET}")
    print("-" * 80)

    # Check for stale data (older than 24 hours)
    stale_tables = []
    for row in latest_data_rows:
        age_col = row[5]  # Data Age column
        if "hours" in str(age_col):
            try:
                hours = float(
                    "".join(c for c in str(age_col) if c.isdigit() or c == ".")
                )
                if hours > 24:
                    stale_tables.append(row[0].replace(BOLD, "").replace(RESET, ""))
            except:
                pass

    if stale_tables:
        print(f"{YELLOW}⚠️ Stale datasets (>24 hours old):{RESET}")
        for table in stale_tables:
            print(f"  - {table}")
        print()

        print(f"{BOLD}RECOMMENDED ACTIONS:{RESET}")
        print("1. Run the new fetch_recent_elexon.py script to get the latest data:")
        print("   python fetch_recent_elexon.py")
        print()
        print("2. Check Elexon BMRS API status at:")
        print("   https://developer.data.elexon.co.uk/api-status")
        print()
        print("3. If problems persist, check system logs for API errors")
    else:
        print(
            f"{GREEN}✅ All datasets appear to be up-to-date (within last 24 hours){RESET}"
        )
        print("Continue monitoring with scheduled fetch_recent_elexon.py runs")

    print("=" * 80)


if __name__ == "__main__":
    main()
