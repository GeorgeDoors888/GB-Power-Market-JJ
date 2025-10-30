#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fix dataset and table IDs in ingest_elexon_fixed.py.
"""

import logging
import re
import sys

logging.basicConfig(level=logging.INFO)


def fix_dataset_ids(file_path):
    """Fix incorrect dataset and table IDs."""

    with open(file_path, "r") as f:
        content = f.read()

    # Replace occurrences of double project reference
    pattern = r"jibber-jabber-knowledge\.jibber-jabber-knowledge\.uk_energy_insights"
    replacement = "jibber-jabber-knowledge.uk_energy_insights"

    new_content = content.replace(pattern, replacement)

    # Fix table_id construction in the function that loads dataframes
    table_id_pattern = r'table_id = f"{client\.project}\.{client\.project}\.{dataset_id}\.{table_name}"'
    table_id_replacement = r'table_id = f"{client.project}.{dataset_id}.{table_name}"'

    new_content = re.sub(table_id_pattern, table_id_replacement, new_content)

    # Fix another possible location - loading with project name construction
    pattern2 = r'table_id = f"{client\.project}\.{client\.project}\.{dataset_id}"'
    replacement2 = r'table_id = f"{client.project}.{dataset_id}"'

    new_content = re.sub(pattern2, replacement2, new_content)

    # Write the updated content back
    with open(file_path, "w") as f:
        f.write(new_content)

    logging.info(f"Fixed dataset IDs in {file_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_dataset_ids.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    fix_dataset_ids(file_path)
    print(f"Fixed dataset IDs in {file_path}")
