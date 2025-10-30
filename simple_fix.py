#!/usr/bin/env python3
"""Simple script to fix the ingest_elexon_fixed.py file."""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main():
    """Fix ingest_elexon_fixed.py"""
    # Paths
    script_dir = Path(__file__).resolve().parent
    ingest_file = script_dir / "ingest_elexon_fixed.py"
    backup_file = script_dir / "ingest_elexon_fixed.py.bak"

    # Ensure files exist
    if not ingest_file.exists():
        logging.error(f"File not found: {ingest_file}")
        sys.exit(1)

    if not backup_file.exists():
        logging.error(f"Backup file not found: {backup_file}")
        sys.exit(1)

    # Read the backup file to get original content
    with open(backup_file, "r") as f:
        content = f.read()

    # Add import for the enhanced function
    if (
        "from bigquery_utils import load_dataframe_with_schema_adaptation"
        not in content
    ):
        if "from bigquery_utils import" in content:
            content = content.replace(
                "from bigquery_utils import",
                "from bigquery_utils import load_dataframe_with_schema_adaptation,",
            )
        else:
            # Add after other imports
            content = content.replace(
                "from schema_validator import get_schema_for_year, validate_schema_compatibility",
                "from schema_validator import get_schema_for_year, validate_schema_compatibility\nfrom bigquery_utils import load_dataframe_with_schema_adaptation",
            )

    # Comment out the _load_dataframe_safely function
    start_marker = "def _load_dataframe_safely("
    end_marker = "def _update_dataset_metadata("

    if start_marker in content and end_marker in content:
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx != -1 and end_idx != -1:
            # Extract the part to comment out
            function_part = content[start_idx:end_idx]

            # Comment each line
            commented_part = "\n".join(
                [f"# {line}" for line in function_part.split("\n")]
            )

            # Replace in content
            content = content[:start_idx] + commented_part + content[end_idx:]

    # Replace function calls
    call_count = content.count("_load_dataframe_safely(")
    content = content.replace(
        "_load_dataframe_safely(", "load_dataframe_with_schema_adaptation("
    )

    # Add the client.project parameter to each call
    # This is more complex and would require more sophisticated regex
    # For simplicity, we'll handle this manually if needed

    # Write updated content
    with open(ingest_file, "w") as f:
        f.write(content)

    logging.info(
        f"Updated {call_count} function calls to use load_dataframe_with_schema_adaptation"
    )
    logging.info(
        "Manual step: You will need to add client.project as the third parameter in each function call"
    )


if __name__ == "__main__":
    main()
