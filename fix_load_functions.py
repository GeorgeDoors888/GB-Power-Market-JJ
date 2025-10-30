#!/usr/bin/env python3
"""Direct script to update _load_dataframe_safely calls in ingest_elexon_fixed.py"""

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
    """Main function to update the file."""
    filepath = Path(__file__).resolve().parent / "ingest_elexon_fixed.py"
    if not filepath.exists():
        logging.error(f"File not found: {filepath}")
        sys.exit(1)

    # Create a backup
    backup_path = f"{filepath}.bak4"
    shutil.copy2(filepath, backup_path)
    logging.info(f"Created backup at {backup_path}")

    # Read the original file
    with open(filepath, "r") as f:
        content = f.read()

    # Add import if not present
    if (
        "from bigquery_utils import load_dataframe_with_schema_adaptation"
        not in content
    ):
        import_pattern = r"from bigquery_utils import (\w+)"
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                r"from bigquery_utils import \1, load_dataframe_with_schema_adaptation",
                content,
            )
        else:
            # Add after other imports
            import_section = "from schema_validator import get_schema_for_year, validate_schema_compatibility\n"
            new_import = (
                import_section
                + "\nfrom bigquery_utils import load_dataframe_with_schema_adaptation\n"
            )
            content = content.replace(import_section, new_import)

    # Update function calls
    original = "_load_dataframe_safely("
    replacement = "load_dataframe_with_schema_adaptation(\n            "
    count = content.count(original)
    content = content.replace(original, replacement)

    # Change the parameter names
    content = re.sub(
        r"load_dataframe_with_schema_adaptation\(\n\s+([^,\n]+),\s*\n\s+([^,\n]+),\s*\n\s+([^,\n]+),\s*\n\s+([^,\n]+)",
        r"load_dataframe_with_schema_adaptation(\n            \1,\n            \2,\n            \1.project,\n            \3,\n            \4",
        content,
    )

    # Add auto_add_schema_fields=True parameter
    content = re.sub(
        r"load_dataframe_with_schema_adaptation\(.*?\)",
        lambda m: m.group(0)[:-1] + ",\n            auto_add_schema_fields=True)",
        content,
        flags=re.DOTALL,
    )

    # Write the updated content
    with open(filepath, "w") as f:
        f.write(content)

    logging.info(
        f"Updated {count} function calls to use load_dataframe_with_schema_adaptation"
    )


if __name__ == "__main__":
    main()
