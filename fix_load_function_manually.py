#!/usr/bin/env python3
"""Manual fix for load function in ingest_elexon_fixed.py"""

import logging
import re
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main():
    """Fix the ingest_elexon_fixed.py file directly."""
    filepath = Path(__file__).resolve().parent / "ingest_elexon_fixed.py"

    # Read the file
    with open(filepath, "r") as f:
        lines = f.readlines()

    # Find the _load_dataframe_safely function definition
    start_line = None
    end_line = None
    for i, line in enumerate(lines):
        if line.strip() == "def _load_dataframe_safely(":
            start_line = i
            break

    if start_line is None:
        logging.error("Could not find _load_dataframe_safely function definition")
        return

    # Find the end of the function
    # This is a bit hacky, but we'll look for a line with just a def or a blank line after the start
    line_level = len(lines[start_line]) - len(lines[start_line].lstrip())
    for i in range(start_line + 1, len(lines)):
        stripped = lines[i].lstrip()
        if not stripped:  # Empty line
            continue
        current_level = len(lines[i]) - len(stripped)
        if current_level <= line_level and (
            stripped.startswith("def ") or stripped.startswith("class ")
        ):
            end_line = i - 1
            break

    if end_line is None:
        end_line = len(lines) - 1

    # Keep a copy of the function
    old_function = "".join(lines[start_line : end_line + 1])
    logging.info(
        f"Found _load_dataframe_safely function at lines {start_line}-{end_line}"
    )

    # Replace function calls
    new_lines = []
    i = 0
    call_count = 0
    while i < len(lines):
        line = lines[i]
        if "_load_dataframe_safely(" in line:
            # Extract the parameters
            call_lines = [line]
            paren_count = line.count("(") - line.count(")")
            j = i + 1
            while paren_count > 0 and j < len(lines):
                call_lines.append(lines[j])
                paren_count += lines[j].count("(") - lines[j].count(")")
                j += 1

            call_text = "".join(call_lines)

            # Use regex to extract parameters
            match = re.search(
                r"_load_dataframe_safely\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+)(.*?)\)",
                call_text,
                re.DOTALL,
            )
            if match:
                client = match.group(1).strip()
                df = match.group(2).strip()
                dataset = match.group(3).strip()
                table = match.group(4).strip()
                extras = match.group(5).strip()

                # Build the replacement call
                indent = " " * (len(line) - len(line.lstrip()))
                replacement = f"{indent}load_dataframe_with_schema_adaptation(\n"
                replacement += f"{indent}    {client},\n"
                replacement += f"{indent}    {df},\n"
                replacement += f"{indent}    {client}.project,\n"
                replacement += f"{indent}    {dataset},\n"
                replacement += f"{indent}    {table}"

                if extras:
                    replacement += f",{extras}"

                replacement += f",\n{indent}    auto_add_schema_fields=True\n{indent})"

                new_lines.append(replacement)
                i = j
                call_count += 1
                continue

        # Skip the function definition itself
        if i >= start_line and i <= end_line:
            i += 1
            continue

        new_lines.append(line)
        i += 1

    # Write the updated file
    with open(filepath, "w") as f:
        f.writelines(new_lines)

    logging.info(
        f"Updated {call_count} function calls to use load_dataframe_with_schema_adaptation"
    )


if __name__ == "__main__":
    main()
