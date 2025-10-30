#!/usr/bin/env python3
"""
Quick fix script for name conflict in ingest_elexon_fixed.py
This script renames all references to load_dataframe_with_schema_adaptation
to local_load_dataframe_with_schema_adaptation
"""

import re

FILE_PATH = (
    "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/ingest_elexon_fixed.py"
)


def fix_function_references():
    """
    Read the file content, fix all function name references,
    and write it back.
    """
    with open(FILE_PATH, "r") as f:
        content = f.read()

    # Step 1: Rename the import with alias
    import_pattern = r"from bigquery_utils import \(\s+BigQueryQuotaManager,\s+load_dataframe_with_retry,\s+load_dataframe_with_schema_adaptation,?\s+\)"
    import_replacement = "from bigquery_utils import (\n    BigQueryQuotaManager,\n    load_dataframe_with_retry,\n    load_dataframe_with_schema_adaptation as bq_load_dataframe_with_schema_adaptation,\n)"
    content = re.sub(import_pattern, import_replacement, content)

    # Step 2: Rename the function definition
    def_pattern = r"def load_dataframe_with_schema_adaptation\("
    def_replacement = "def local_load_dataframe_with_schema_adaptation("
    content = re.sub(def_pattern, def_replacement, content)

    # Step 3: Rename all function calls
    # Make sure we don't replace inside comments or strings
    # This is a simplistic approach - a proper parser would be better
    call_pattern = r"(?<![\"'])load_dataframe_with_schema_adaptation\("
    call_replacement = "local_load_dataframe_with_schema_adaptation("
    content = re.sub(call_pattern, call_replacement, content)

    # Write back the modified content
    with open(FILE_PATH, "w") as f:
        f.write(content)

    print(f"Fixed function name references in {FILE_PATH}")


if __name__ == "__main__":
    fix_function_references()
