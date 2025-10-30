#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Function-specific dataset ID fix for BOALF load issue.
"""

import logging
import re
import sys

logging.basicConfig(level=logging.INFO)


def fix_dataset_ids_for_all_loading_functions(file_path):
    """Apply fixes to all table_id construction instances"""

    with open(file_path, "r") as f:
        content = f.read()

    # Fix pattern that creates incorrect table paths in all functions
    pattern = r'(table_id|staging_table_id|final_table_id) = f"{client\.project}\.({client\.project}\.)?{dataset_id}\.{(.*?)}"'
    replacement = r'\1 = f"{client.project}.{dataset_id}.\3"'

    # Count and log all matches
    matches = re.finditer(pattern, content)
    match_count = 0
    for match in matches:
        match_count += 1
        line_num = content[: match.start()].count("\n") + 1
        logging.info(f"Match #{match_count} at line {line_num}: {match.group(0)}")

    # Apply the fix
    new_content = re.sub(pattern, replacement, content)

    # Apply the direct table ID fix for extra safety
    hardcoded_pattern = r'(table_id|staging_table_id|final_table_id) = f"jibber-jabber-knowledge\.jibber-jabber-knowledge\.uk_energy_insights'
    hardcoded_replacement = r'\1 = f"jibber-jabber-knowledge.uk_energy_insights'
    new_content = re.sub(hardcoded_pattern, hardcoded_replacement, new_content)

    # Revert our previous fix that caused a local variable error
    direct_fix_pattern = (
        r'    table_id = f"jibber-jabber-knowledge\.uk_energy_insights\.{table_name}"'
    )
    direct_fix_replacement = (
        r'    table_id = f"{client.project}.{dataset_id}.{table_name}"'
    )
    new_content = re.sub(direct_fix_pattern, direct_fix_replacement, new_content)

    # Write the updated content back
    with open(file_path, "w") as f:
        f.write(new_content)

    logging.info(f"Fixed table_id assignments in {file_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python complete_fix_dataset_ids.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    fix_dataset_ids_for_all_loading_functions(file_path)
    print(f"Fixed dataset IDs in {file_path}")
