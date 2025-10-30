#!/usr/bin/env python3
"""Update the _load_dataframe_safely calls to use the new enhanced function."""

import logging
import re
import shutil
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def update_function_calls(filepath):
    """Replace calls to _load_dataframe_safely with load_dataframe_with_schema_adaptation."""
    # Create backup
    backup_path = f"{filepath}.bak3"
    shutil.copy2(filepath, backup_path)
    logging.info(f"Created backup at {backup_path}")

    with open(filepath, "r") as f:
        content = f.read()

    # Delete any existing implementation of the load_dataframe_with_schema_adaptation function
    pattern_func_def = r'def load_dataframe_with_schema_adaptation\(.*?\n(\s+""".*?"""\n)?.*?\n\s+return True'
    content = re.sub(pattern_func_def, "", content, flags=re.DOTALL)

    # Find all instances of the original function call
    pattern = (
        r"_load_dataframe_safely\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+)([^)]*)\)"
    )

    # Replace function calls with the new one
    def replacement(match):
        client = match.group(1).strip()
        df = match.group(2).strip()
        dataset = match.group(3).strip()
        table = match.group(4).strip()
        extra_args = match.group(5).strip()

        # Format the new function call with proper indentation
        result = f"load_dataframe_with_schema_adaptation(\n"
        result += f"            {client},\n"
        result += f"            {df},\n"
        result += f"            {client}.project,\n"
        result += f"            {dataset},\n"
        result += f"            {table}"

        # Add any extra arguments
        if extra_args:
            for arg in extra_args.split(","):
                if "=" in arg:
                    result += f",\n            {arg.strip()}"

        # Add auto_add_schema_fields parameter
        result += ",\n            auto_add_schema_fields=True\n        )"

        return result

    # Replace function calls
    new_content = re.sub(pattern, replacement, content)

    # Count new occurrences for verification
    new_count = new_content.count("load_dataframe_with_schema_adaptation(")

    # Write updated content
    with open(filepath, "w") as f:
        f.write(new_content)

    logging.info(
        f"Updated {new_count} function calls to use load_dataframe_with_schema_adaptation"
    )

    return new_count


def main():
    """Main function."""
    script_path = Path(__file__).resolve().parent
    target_file = script_path / "ingest_elexon_fixed.py"

    if not target_file.exists():
        logging.error(f"Target file not found: {target_file}")
        sys.exit(1)

    try:
        replacements = update_function_calls(target_file)
        logging.info(
            f"✅ Successfully updated {replacements} function calls in {target_file.name}"
        )
    except Exception as e:
        logging.error(f"Failed to update function calls: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


def main():
    """Main function."""
    script_path = Path(__file__).resolve().parent
    target_file = script_path / "ingest_elexon_fixed.py"

    if not target_file.exists():
        logging.error(f"Target file not found: {target_file}")
        sys.exit(1)

    try:
        replacements = update_function_calls(target_file)
        logging.info(
            f"✅ Successfully updated {replacements} function calls in {target_file.name}"
        )
    except Exception as e:
        logging.error(f"Failed to update function calls: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
