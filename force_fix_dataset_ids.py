#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced debugging for dataset IDs with forced direct table path fix.
"""

import logging
import sys

logging.basicConfig(level=logging.INFO)


def fix_dataset_ids_for_loading(file_path):
    """Force dataset ID fixes in the load dataframe function"""

    with open(file_path, "r") as f:
        content = f.read()

    # Locate the function where the issue occurs
    func_start = content.find("def local_load_dataframe_with_schema_adaptation(")
    if func_start == -1:
        func_start = content.find("def load_dataframe_with_schema_adaptation(")

    if func_start == -1:
        logging.error("Could not find load_dataframe function")
        return

    # Find the table_id assignment within the function
    table_id_line_start = content.find("table_id =", func_start)
    if table_id_line_start == -1:
        logging.error("Could not find table_id assignment")
        return

    line_end = content.find("\n", table_id_line_start)
    original_line = content[table_id_line_start:line_end]

    logging.info(f"Found original table_id assignment: {original_line}")

    # Replace with hardcoded path
    new_line = (
        '    table_id = f"jibber-jabber-knowledge.uk_energy_insights.{table_name}"'
    )

    # Apply the replacement
    new_content = content[:table_id_line_start] + new_line + content[line_end:]

    # Write the updated content back
    with open(file_path, "w") as f:
        f.write(new_content)

    logging.info(f"Fixed table_id assignment in {file_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python force_fix_dataset_ids.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    fix_dataset_ids_for_loading(file_path)
    print(f"Fixed dataset IDs in {file_path}")
