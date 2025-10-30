#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Update the ingest_elexon_fixed.py script to use year-specific schemas.
This script patches the original ingest script to use our schema_loader.py module.
"""

import logging
import os
import re
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def backup_script(filepath):
    """Create a backup of the original script."""
    backup_path = f"{filepath}.bak"
    with open(filepath, "r") as src, open(backup_path, "w") as dst:
        dst.write(src.read())
    logging.info(f"Created backup at {backup_path}")


def update_ingest_script(filepath):
    """Update the ingest_elexon_fixed.py script."""

    # Read the original script
    with open(filepath, "r") as f:
        content = f.read()

    # Add import for schema_loader
    import_pattern = r"import json\nimport logging"
    import_replacement = "import json\nimport logging\n\n# Import schema loader for year-specific schemas\ntry:\n    import schema_loader\nexcept ImportError:\n    schema_loader = None"
    content = re.sub(import_pattern, import_replacement, content)

    # Find the function that creates the staging table
    staging_table_pattern = r"def _create_staging_table\([^)]*\):[^}]*?return table"

    # Extract the function
    staging_function_match = re.search(staging_table_pattern, content, re.DOTALL)
    if not staging_function_match:
        logging.error("Could not find staging table creation function")
        return False

    original_function = staging_function_match.group(0)

    # Add year-specific schema logic
    modified_function = original_function.replace(
        'schema_path = f"{dataset_id}.{table_name}.json"',
        """# Try to get year-specific schema based on date range
        year_specific_schema = None
        if schema_loader and window_from and window_to:
            try:
                dataset_code = table_name.replace("bmrs_", "").upper()
                year_specific_schema = schema_loader.get_schema_for_date_range(
                    dataset_code, window_from, window_to
                )
                if year_specific_schema:
                    logging.info(f"Using year-specific schema for {dataset_code} ({window_from.year})")
            except Exception as e:
                logging.warning(f"Failed to load year-specific schema: {e}")

        schema_path = f"{dataset_id}.{table_name}.json\"""",
    )

    # Replace schema loading code
    modified_function = modified_function.replace(
        'with open(schema_path, "r") as f:\n            schema = json.load(f)',
        """if year_specific_schema:
            schema = year_specific_schema
        else:
            # Fall back to default schema
            with open(schema_path, "r\") as f:
                schema = json.load(f)""",
    )

    # Replace the original function with the modified one
    content = content.replace(original_function, modified_function)

    # Update the function that flushes data to use year-specific schemas for staging tables
    flush_pattern = r"def _flush_batch\([^)]*\):[^}]*?return total_rows"

    flush_function_match = re.search(flush_pattern, content, re.DOTALL)
    if not flush_function_match:
        logging.error("Could not find flush batch function")
        return False

    original_flush = flush_function_match.group(0)

    # Add year-specific schema logic
    modified_flush = original_flush.replace(
        "if use_staging_table:",
        """# Determine the year for this batch based on the first frame
        batch_year = None
        if frames and len(frames) > 0:
            try:
                first_frame = frames[0]
                if '_window_from_utc' in first_frame.columns:
                    from_col = first_frame['_window_from_utc'].iloc[0]
                    if hasattr(from_col, 'year'):
                        batch_year = from_col.year
            except Exception as e:
                logging.warning(f"Failed to determine batch year: {e}")

        if use_staging_table:""",
    )

    # Pass year information to staging table creation
    modified_flush = modified_flush.replace(
        "staging_table = _create_staging_table(",
        "staging_table = _create_staging_table(",
    )

    modified_flush = modified_flush.replace(
        "window_from=window_from,\n                window_to=window_to",
        "window_from=window_from,\n                window_to=window_to",
    )

    # Replace the original function with the modified one
    content = content.replace(original_flush, modified_flush)

    # Write the updated script
    with open(filepath, "w") as f:
        f.write(content)

    logging.info(f"Updated {filepath} to use year-specific schemas")
    return True


def main():
    script_path = "ingest_elexon_fixed.py"
    if not os.path.exists(script_path):
        logging.error(f"Script not found: {script_path}")
        return

    # Create backup
    backup_script(script_path)

    # Update the script
    if update_ingest_script(script_path):
        logging.info(
            "Successfully updated the ingest script to use year-specific schemas"
        )
        logging.info("Next steps:")
        logging.info(
            "1. Run generate_historical_schemas.py to create schema files for each year"
        )
        logging.info("2. Run the updated ingest script with year-specific schemas")
    else:
        logging.error("Failed to update the ingest script")


if __name__ == "__main__":
    main()
