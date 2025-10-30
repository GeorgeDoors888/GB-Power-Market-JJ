#!/usr/bin/env python3
"""
Comprehensive check of all DNO data we have, including recent additions
"""

from datetime import datetime

import pandas as pd
from google.cloud import bigquery


def main():
    # Set up BigQuery client
    client = bigquery.Client(project="jibber-jabber-knowledge")

    print("🔍 COMPREHENSIVE DNO DATA AUDIT")
    print("=" * 60)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Complete UK DNO list
    complete_dno_list = {
        12: {"key": "UKPN-LPN", "name": "UK Power Networks (London)"},
        10: {"key": "UKPN-EPN", "name": "UK Power Networks (Eastern)"},
        19: {"key": "UKPN-SPN", "name": "UK Power Networks (South Eastern)"},
        16: {"key": "ENWL", "name": "Electricity North West"},
        15: {"key": "NPg-NE", "name": "Northern Powergrid (North East)"},
        23: {"key": "NPg-Y", "name": "Northern Powergrid (Yorkshire)"},
        18: {"key": "SP-Distribution", "name": "SP Energy Networks (SPD)"},
        13: {"key": "SP-Manweb", "name": "SP Energy Networks (SPM)"},
        17: {
            "key": "SSE-SHEPD",
            "name": "Scottish Hydro Electric Power Distribution (SHEPD)",
        },
        20: {"key": "SSE-SEPD", "name": "Southern Electric Power Distribution (SEPD)"},
        14: {
            "key": "NGED-WM",
            "name": "National Grid Electricity Distribution – West Midlands (WMID)",
        },
        11: {
            "key": "NGED-EM",
            "name": "National Grid Electricity Distribution – East Midlands (EMID)",
        },
        22: {
            "key": "NGED-SW",
            "name": "National Grid Electricity Distribution – South West (SWEST)",
        },
        21: {
            "key": "NGED-SWales",
            "name": "National Grid Electricity Distribution – South Wales (SWALES)",
        },
    }

    print(f"\n📋 Complete UK DNO List ({len(complete_dno_list)} DNOs):")
    for mpan_id, info in sorted(complete_dno_list.items()):
        print(f"   {mpan_id:2d}: {info['key']} - {info['name']}")

    # Get ALL tables in the dataset with creation/modification dates
    print(f"\n🔍 Scanning ALL tables for DNO data...")

    all_tables_query = """
    SELECT
        table_name,
        table_type,
        creation_time,
        last_modified_time
    FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
    ORDER BY table_name
    """

    all_tables_df = client.query(all_tables_query).to_dataframe()

    # Search for DNO-related keywords in table names
    dno_keywords = [
        "ukpn",
        "enwl",
        "electricity_north",
        "northern",
        "powergrid",
        "npg",
        "sp_energy",
        "sp_distribution",
        "manweb",
        "sp_",
        "sse",
        "ssen",
        "sepd",
        "shepd",
        "scottish",
        "southern_electric",
        "nged",
        "national_grid",
        "wmid",
        "emid",
        "swales",
        "swest",
        "dno",
        "distribution",
        "duos",
        "charging",
    ]

    potential_dno_tables = []
    for _, row in all_tables_df.iterrows():
        table_name = row["table_name"].lower()
        for keyword in dno_keywords:
            if keyword in table_name:
                potential_dno_tables.append(
                    {
                        "table_name": row["table_name"],
                        "created": row["creation_time"],
                        "modified": row["last_modified_time"],
                        "keyword_match": keyword,
                    }
                )
                break

    print(f"\n📊 Found {len(potential_dno_tables)} potentially DNO-related tables:")
    for table_info in sorted(potential_dno_tables, key=lambda x: x["table_name"]):
        print(
            f"   • {table_info['table_name']} (keyword: {table_info['keyword_match']})"
        )
        print(
            f"     Created: {table_info['created']}, Modified: {table_info['modified']}"
        )

    # Now analyze each table to determine which DNO it represents
    print(f"\n🔍 DETAILED ANALYSIS BY TABLE:")
    print("=" * 60)

    dno_coverage = {}

    for table_info in sorted(potential_dno_tables, key=lambda x: x["table_name"]):
        table_name = table_info["table_name"]
        print(f"\n📋 Table: {table_name}")

        try:
            # Get table size and row count
            table_ref = client.dataset("uk_energy_insights").table(table_name)
            table = client.get_table(table_ref)

            row_count = table.num_rows if table.num_rows else 0
            size_mb = (table.num_bytes / (1024 * 1024)) if table.num_bytes else 0

            print(f"   Rows: {row_count:,}, Size: {size_mb:.1f} MB")

            if row_count == 0:
                print(f"   ⚠️  Empty table - skipping analysis")
                continue

            # Sample the data to understand content
            sample_query = f"""
            SELECT *
            FROM `jibber-jabber-knowledge.uk_energy_insights.{table_name}`
            LIMIT 3
            """

            sample_df = client.query(sample_query).to_dataframe()

            if not sample_df.empty:
                print(
                    f"   Columns ({len(sample_df.columns)}): {list(sample_df.columns)[:8]}"
                )

                # Look for DNO identifiers in the data
                dno_identified = False

                # Check for specific DNO patterns in column names and data
                for col in sample_df.columns:
                    col_lower = col.lower()

                    # Check column names for DNO hints
                    if any(
                        keyword in col_lower
                        for keyword in [
                            "dno",
                            "area",
                            "region",
                            "network",
                            "distribution",
                        ]
                    ):
                        try:
                            unique_vals = (
                                sample_df[col].dropna().astype(str).unique()[:5]
                            )
                            print(f"   DNO-related column '{col}': {list(unique_vals)}")

                            # Try to map values to known DNOs
                            for val in unique_vals:
                                val_str = str(val).lower()
                                if "ukpn" in val_str or "uk power" in val_str:
                                    if "london" in val_str or "lpn" in val_str:
                                        dno_coverage[12] = dno_coverage.get(12, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                    elif "eastern" in val_str or "epn" in val_str:
                                        dno_coverage[10] = dno_coverage.get(10, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                    elif "south" in val_str or "spn" in val_str:
                                        dno_coverage[19] = dno_coverage.get(19, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                elif (
                                    "enwl" in val_str
                                    or "electricity north west" in val_str
                                ):
                                    dno_coverage[16] = dno_coverage.get(16, []) + [
                                        table_name
                                    ]
                                    dno_identified = True
                                elif (
                                    "northern powergrid" in val_str or "npg" in val_str
                                ):
                                    if (
                                        "north east" in val_str
                                        or "northeast" in val_str
                                    ):
                                        dno_coverage[15] = dno_coverage.get(15, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                    elif "yorkshire" in val_str:
                                        dno_coverage[23] = dno_coverage.get(23, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                elif (
                                    "sp energy" in val_str
                                    or "sp distribution" in val_str
                                ):
                                    dno_coverage[18] = dno_coverage.get(18, []) + [
                                        table_name
                                    ]
                                    dno_identified = True
                                elif "manweb" in val_str:
                                    dno_coverage[13] = dno_coverage.get(13, []) + [
                                        table_name
                                    ]
                                    dno_identified = True
                                elif (
                                    "sse" in val_str
                                    or "scottish" in val_str
                                    or "southern electric" in val_str
                                ):
                                    if "shepd" in val_str or "hydro" in val_str:
                                        dno_coverage[17] = dno_coverage.get(17, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                    elif "sepd" in val_str:
                                        dno_coverage[20] = dno_coverage.get(20, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                elif "nged" in val_str or "national grid" in val_str:
                                    if "west midland" in val_str or "wmid" in val_str:
                                        dno_coverage[14] = dno_coverage.get(14, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                    elif "east midland" in val_str or "emid" in val_str:
                                        dno_coverage[11] = dno_coverage.get(11, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                    elif "south west" in val_str or "swest" in val_str:
                                        dno_coverage[22] = dno_coverage.get(22, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                                    elif (
                                        "south wales" in val_str or "swales" in val_str
                                    ):
                                        dno_coverage[21] = dno_coverage.get(21, []) + [
                                            table_name
                                        ]
                                        dno_identified = True
                        except Exception as e:
                            print(f"   Error analyzing column {col}: {e}")

                # If no DNO identified from content, try to infer from table name
                if not dno_identified:
                    table_lower = table_name.lower()
                    if "ukpn" in table_lower:
                        # UKPN tables generally cover all 3 areas unless specified
                        for mpan_id in [10, 12, 19]:
                            dno_coverage[mpan_id] = dno_coverage.get(mpan_id, []) + [
                                table_name
                            ]
                        print(f"   Inferred: UKPN (all areas) from table name")
                    elif any(
                        keyword in table_lower
                        for keyword in ["enwl", "electricity_north"]
                    ):
                        dno_coverage[16] = dno_coverage.get(16, []) + [table_name]
                        print(f"   Inferred: ENWL from table name")
                    # Add more inference rules as needed

                if not dno_identified:
                    print(f"   ❓ Could not identify specific DNO")

        except Exception as e:
            print(f"   ❌ Error analyzing table: {e}")

    # Summary report
    print(f"\n" + "=" * 60)
    print(f"📊 FINAL DNO COVERAGE SUMMARY")
    print(f"=" * 60)

    covered_dnos = list(dno_coverage.keys())
    missing_dnos = [
        mpan_id for mpan_id in complete_dno_list.keys() if mpan_id not in covered_dnos
    ]

    print(f"\n✅ DNOs with Data ({len(covered_dnos)}/{len(complete_dno_list)}):")
    for mpan_id in sorted(covered_dnos):
        info = complete_dno_list[mpan_id]
        tables = list(set(dno_coverage[mpan_id]))  # Remove duplicates
        print(f"   {mpan_id:2d}: {info['key']} - {info['name']}")
        print(f"       Tables ({len(tables)}): {', '.join(tables[:3])}")
        if len(tables) > 3:
            print(f"       ... and {len(tables) - 3} more tables")

    print(f"\n❌ DNOs WITHOUT Data ({len(missing_dnos)}/{len(complete_dno_list)}):")
    for mpan_id in sorted(missing_dnos):
        info = complete_dno_list[mpan_id]
        print(f"   {mpan_id:2d}: {info['key']} - {info['name']}")

    coverage_percentage = (len(covered_dnos) / len(complete_dno_list)) * 100
    print(
        f"\n📈 Overall Coverage: {len(covered_dnos)}/{len(complete_dno_list)} DNOs ({coverage_percentage:.1f}%)"
    )

    # Recent additions check
    print(f"\n📅 RECENT TABLE ADDITIONS (Last 30 days):")
    recent_threshold = pd.Timestamp.now() - pd.Timedelta(days=30)

    recent_tables = []
    for table_info in potential_dno_tables:
        if pd.Timestamp(table_info["modified"]) > recent_threshold:
            recent_tables.append(table_info)

    if recent_tables:
        print(f"   Found {len(recent_tables)} recently modified DNO tables:")
        for table_info in sorted(
            recent_tables, key=lambda x: x["modified"], reverse=True
        ):
            print(
                f"     • {table_info['table_name']} (modified: {table_info['modified']})"
            )
    else:
        print(f"   No DNO tables modified in the last 30 days")


if __name__ == "__main__":
    main()
