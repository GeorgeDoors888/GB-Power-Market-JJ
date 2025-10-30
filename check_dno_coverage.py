#!/usr/bin/env python3
"""
Check which DNO IDs we have compared to the complete UK DNO list
"""

import pandas as pd
from google.cloud import bigquery


def main():
    # Set up BigQuery client
    client = bigquery.Client(project="jibber-jabber-knowledge")

    print("🔍 DNO COVERAGE ANALYSIS")
    print("=" * 50)

    # Complete UK DNO list from user
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

    print(f"📋 Complete UK DNO List ({len(complete_dno_list)} DNOs):")
    for mpan_id, info in sorted(complete_dno_list.items()):
        print(f"   {mpan_id:2d}: {info['key']} - {info['name']}")

    # Check what DNO data we have in our dataset
    print(f"\n🔍 Checking our dataset for DNO coverage...")

    # Search for all tables that might contain DNO data
    search_query = """
    SELECT table_name, table_type,
           row_count, size_bytes,
           ddl
    FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
    WHERE table_name LIKE '%dno%'
       OR table_name LIKE '%ukpn%'
       OR table_name LIKE '%enwl%'
       OR table_name LIKE '%npg%'
       OR table_name LIKE '%northern%'
       OR table_name LIKE '%sp_%'
       OR table_name LIKE '%sse%'
       OR table_name LIKE '%nged%'
       OR table_name LIKE '%distribution%'
    ORDER BY table_name
    """

    try:
        tables_df = client.query(search_query).to_dataframe()
        print(f"   Found {len(tables_df)} potentially relevant tables:")

        for _, row in tables_df.iterrows():
            size_mb = row["size_bytes"] / (1024 * 1024) if row["size_bytes"] else 0
            print(
                f"     • {row['table_name']}: {row['row_count']:,} rows, {size_mb:.1f} MB"
            )
    except Exception as e:
        print(f"   ❌ Error searching tables: {e}")

    # Check UKPN data specifically (we know we have this)
    print(f"\n📊 UKPN Data Analysis:")

    # Check what areas we have in UKPN data
    ukpn_areas_query = """
    SELECT DISTINCT
        dno_area,
        COUNT(*) as record_count
    FROM `jibber-jabber-knowledge.uk_energy_insights.ukpn_duos_charges_annex1`
    GROUP BY dno_area
    ORDER BY dno_area
    """

    try:
        ukpn_df = client.query(ukpn_areas_query).to_dataframe()
        print(f"   UKPN Areas in our dataset:")

        # Map our UKPN areas to the standard DNO list
        area_mappings = {
            "East of England Electricity Network": {"mpan_id": 10, "key": "UKPN-EPN"},
            "London Electricity Network": {"mpan_id": 12, "key": "UKPN-LPN"},
            "South Eastern England Electricity Network": {
                "mpan_id": 19,
                "key": "UKPN-SPN",
            },
        }

        covered_mpan_ids = []
        for _, row in ukpn_df.iterrows():
            area = row["dno_area"]
            if area in area_mappings:
                mapping = area_mappings[area]
                covered_mpan_ids.append(mapping["mpan_id"])
                print(
                    f"     ✅ {area}: {row['record_count']} records (MPAN ID {mapping['mpan_id']} - {mapping['key']})"
                )
            else:
                print(
                    f"     ❓ {area}: {row['record_count']} records (mapping unknown)"
                )

    except Exception as e:
        print(f"   ❌ Error analyzing UKPN data: {e}")
        covered_mpan_ids = []

    # Check for other DNO data
    print(f"\n🔍 Checking for other DNO data...")

    # Look for DNO-related tables with actual data
    other_dno_tables = []

    # Check if we have any SSEN data
    ssen_check_queries = [
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%ssen%'",
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%shepd%'",
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%sepd%'",
    ]

    # Check if we have any Northern Powergrid data
    npg_check_queries = [
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%npg%'",
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%northern%'",
    ]

    # Check if we have any NGED data
    nged_check_queries = [
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%nged%'",
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%wmid%'",
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%emid%'",
    ]

    # Check if we have any SP Energy Networks data
    sp_check_queries = [
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%sp_%'",
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%manweb%'",
    ]

    # Check if we have any ENWL data
    enwl_check_queries = [
        "SELECT COUNT(*) as count FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` WHERE table_name LIKE '%enwl%'"
    ]

    all_checks = [
        ("SSEN (Scottish/Southern)", ssen_check_queries),
        ("Northern Powergrid", npg_check_queries),
        ("NGED (National Grid ED)", nged_check_queries),
        ("SP Energy Networks", sp_check_queries),
        ("Electricity North West", enwl_check_queries),
    ]

    for dno_name, queries in all_checks:
        print(f"\n   {dno_name}:")
        found_tables = 0
        for query in queries:
            try:
                result = client.query(query).to_dataframe()
                if result["count"].iloc[0] > 0:
                    found_tables += result["count"].iloc[0]
            except:
                pass

        if found_tables > 0:
            print(f"     ✅ Found {found_tables} related tables")
        else:
            print(f"     ❌ No tables found")

    # Summary
    print(f"\n" + "=" * 50)
    print(f"📊 DNO COVERAGE SUMMARY")
    print(f"=" * 50)

    print(f"✅ DNOs we have data for:")
    if covered_mpan_ids:
        for mpan_id in sorted(covered_mpan_ids):
            info = complete_dno_list[mpan_id]
            print(f"   {mpan_id:2d}: {info['key']} - {info['name']}")

    missing_mpan_ids = [
        mpan_id
        for mpan_id in complete_dno_list.keys()
        if mpan_id not in covered_mpan_ids
    ]

    print(f"\n❌ DNOs we DON'T have data for ({len(missing_mpan_ids)} missing):")
    for mpan_id in sorted(missing_mpan_ids):
        info = complete_dno_list[mpan_id]
        print(f"   {mpan_id:2d}: {info['key']} - {info['name']}")

    coverage_percentage = (len(covered_mpan_ids) / len(complete_dno_list)) * 100
    print(
        f"\n📈 Overall Coverage: {len(covered_mpan_ids)}/{len(complete_dno_list)} DNOs ({coverage_percentage:.1f}%)"
    )

    if coverage_percentage < 100:
        print(f"\n💡 Recommendations:")
        print(f"   • We have complete UKPN coverage (3/3 license areas)")
        print(f"   • Need to collect data from {len(missing_mpan_ids)} other DNOs")
        print(
            f"   • Priority order: SSEN, Northern Powergrid, NGED, SP Energy Networks, ENWL"
        )


if __name__ == "__main__":
    main()
