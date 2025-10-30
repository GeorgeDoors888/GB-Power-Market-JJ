#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fix dataset and table IDs in ingest_elexon_fixed.py with debugging.
"""

import logging
import re
import sys

logging.basicConfig(level=logging.INFO)


def fix_dataset_ids(file_path):
    """Fix incorrect dataset and table IDs with detailed debugging."""

    with open(file_path, "r") as f:
        content = f.read()

    # Search for specific string patterns that might indicate the issue
    table_pattern = (
        r"jibber-jabber-knowledge\.jibber-jabber-knowledge\.uk_energy_insights"
    )

    # Count occurrences and log positions
    matches = re.finditer(table_pattern, content)
    match_count = 0
    for match in matches:
        match_count += 1
        start, end = match.span()
        line_start = content.rfind("\n", 0, start) + 1
        line_end = content.find("\n", end)
        if line_end == -1:
            line_end = len(content)
        line = content[line_start:line_end]
        line_num = content[:start].count("\n") + 1
        logging.info(f"Match #{match_count} at line {line_num}: {line}")

    # If explicit pattern not found, try more general patterns
    if match_count == 0:
        logging.info("Searching for more general patterns...")

        # Look for any instance of project name being duplicated in a string
        gen_pattern = r"(jibber-jabber-knowledge)\.\1"
        gen_matches = re.finditer(gen_pattern, content)
        gen_count = 0
        for match in gen_matches:
            gen_count += 1
            start, end = match.span()
            line_start = content.rfind("\n", 0, start) + 1
            line_end = content.find("\n", end)
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end]
            line_num = content[:start].count("\n") + 1
            logging.info(f"General match #{gen_count} at line {line_num}: {line}")

    # Look for table construction patterns
    load_pattern = r"⬆️ Loading \{len\(df\)\} rows to \{(.*?)\}"
    load_matches = re.finditer(load_pattern, content)
    for match in load_matches:
        table_var = match.group(1)
        logging.info(f"Found table ID construction: {table_var}")

    # Attempt all possible fixes
    replacements = [
        # Fix direct string literals
        (
            r"jibber-jabber-knowledge\.jibber-jabber-knowledge\.uk_energy_insights",
            r"jibber-jabber-knowledge.uk_energy_insights",
        ),
        # Fix table_id construction in format strings
        (
            r'table_id = f"{client\.project}\.{client\.project}\.{dataset_id}',
            r'table_id = f"{client.project}.{dataset_id}',
        ),
        # Fix other potential issues
        (
            r'f"{args\.project}\.{args\.project}\.{args\.dataset}',
            r'f"{args.project}.{args.dataset}',
        ),
        # Fix string literals in logging statements
        (
            r"Loading .* rows to jibber-jabber-knowledge\.jibber-jabber-knowledge",
            r"Loading .* rows to jibber-jabber-knowledge",
        ),
    ]

    new_content = content
    for pattern, replacement in replacements:
        before_count = len(new_content)
        new_content = re.sub(pattern, replacement, new_content)
        after_count = len(new_content)
        if before_count != after_count:
            logging.info(f"Applied fix: {pattern} -> {replacement}")

    # Finally do a direct string replacement to catch any remaining issues
    direct_pattern = "jibber-jabber-knowledge.jibber-jabber-knowledge"
    direct_replacement = "jibber-jabber-knowledge"
    if direct_pattern in new_content:
        new_content = new_content.replace(direct_pattern, direct_replacement)
        logging.info(
            f"Applied direct string replacement: {direct_pattern} -> {direct_replacement}"
        )

    # Write the updated content back
    with open(file_path, "w") as f:
        f.write(new_content)

    logging.info(f"Fixed dataset IDs in {file_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_dataset_ids_with_debug.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    fix_dataset_ids(file_path)
    print(f"Fixed dataset IDs in {file_path}")
