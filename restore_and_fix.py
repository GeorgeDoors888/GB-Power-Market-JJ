#!/usr/bin/env python3
"""
Completely restore ingest_elexon_fixed.py and enhance it with the new function.
"""

import logging
import re
import shutil
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main():
    """Main function to fix the ingest_elexon_fixed.py file."""
    # Get the original backup
    script_dir = Path(__file__).resolve().parent

    # Original backup file and output file
    backup_file = script_dir / "ingest_elexon_fixed.py.bak"
    output_file = script_dir / "ingest_elexon_fixed.py"

    # New backup with timestamp
    new_backup = script_dir / f"ingest_elexon_fixed.py.bak.final"

    # Check if original backup exists
    if not backup_file.exists():
        logging.error(f"Backup file not found: {backup_file}")
        sys.exit(1)

    # Create a new backup
    shutil.copy2(backup_file, new_backup)
    logging.info(f"Created new backup: {new_backup}")

    # Read the original backup
    with open(backup_file, "r") as f:
        content = f.read()

    # First, add the import
    if (
        "from bigquery_utils import load_dataframe_with_schema_adaptation"
        not in content
    ):
        content = content.replace(
            "from schema_validator import get_schema_for_year, validate_schema_compatibility",
            "from schema_validator import get_schema_for_year, validate_schema_compatibility\nfrom bigquery_utils import load_dataframe_with_schema_adaptation",
        )
        logging.info("Added import for load_dataframe_with_schema_adaptation")

    # Find all function calls using regex pattern
    pattern = r"_load_dataframe_safely\(\s*([^,\n]+),\s*([^,\n]+),\s*([^,\n]+),\s*([^,\n]+)((?:,[\s\n]*(?:[^,=\n]+=[^,\n]+))*)\s*\)"

    matches = list(re.finditer(pattern, content))
    if not matches:
        logging.warning("No function calls found to replace")
        return

    # Process each match from end to start to avoid offset issues
    for match in reversed(matches):
        client = match.group(1).strip()
        df = match.group(2).strip()
        dataset = match.group(3).strip()
        table = match.group(4).strip()
        extras = match.group(5).strip()

        # Build replacement
        replacement = f"load_dataframe_with_schema_adaptation(\n            {client},\n            {df},\n            {client}.project,\n            {dataset},\n            {table}{extras},\n            auto_add_schema_fields=True\n        )"

        # Replace in content
        content = content[: match.start()] + replacement + content[match.end() :]

    # Write the fixed file
    with open(output_file, "w") as f:
        f.write(content)

    logging.info(f"Updated {len(matches)} function calls")


if __name__ == "__main__":
    main()
