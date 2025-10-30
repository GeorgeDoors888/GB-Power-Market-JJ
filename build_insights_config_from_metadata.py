"""
Builds a YAML configuration file for the Elexon Insights API ingestion
by parsing the official OpenAPI metadata.
"""

import json
import re
from pathlib import Path

import yaml

# Constants
METADATA_FILE = Path("api_metadata.json")
OUTPUT_YAML_FILE = Path("insights_endpoints.generated.yml")
PROJECT_ROOT = Path(__file__).parent


def sanitize_key(name):
    """Converts a human-readable name into a snake_case key."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return s2.replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "")


def analyze_parameters(params):
    """Analyzes endpoint parameters to determine their type and purpose."""
    date_params = []
    param_columns = []
    static_params = {}

    # Standard date parameters used by the ingestion script
    date_param_names = {
        "from",
        "to",
        "settlementDate",
        "settlementPeriodFrom",
        "settlementPeriodTo",
    }

    for param in params:
        name = param.get("name")
        if name in date_param_names:
            date_params.append(name)
        # Parameters with 'example' are often good candidates for static default values
        elif "example" in param:
            static_params[name] = param["example"]
        # All other parameters are potential columns
        else:
            param_columns.append(name)

    return date_params, param_columns, static_params


def build_config():
    """
    Reads the API metadata and builds the YAML configuration dictionary.
    """
    print(f"Reading API metadata from {METADATA_FILE}...")
    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)

    config = {
        "defaults": {
            "project": "jibber-jabber-knowledge",
            "dataset": "uk_energy_insights",
        },
        "base_urls": {
            "insights": "https://data.elexon.co.uk/bmrs/api/v1",
            "bmrs": "https://data.elexon.co.uk/bmrs/api/v1",
        },
        "groups": {},
    }

    print("Processing API definitions...")
    for api_definition in metadata:  # Iterate through the list of API definitions
        if not api_definition:
            print("  - Skipping an empty API definition.")
            continue

        # Determine the group and base from the server URL for this definition
        server_url = api_definition.get("servers", [{}])[0].get("url", "")
        if "bmrs" in server_url:
            group_name = "bmrs_datasets"
            base = "bmrs"
            table_name_prefix = "bmrs"
        elif "insights" in server_url:
            group_name = "insights_datasets"
            base = "insights"
            table_name_prefix = "ins"
        else:
            title = api_definition.get("info", {}).get("title", "Unknown")
            print(
                f"  - Skipping API definition '{title}' with unknown server URL: {server_url}"
            )
            continue

        paths = api_definition.get("paths")
        if not paths:
            print(
                f"  - Skipping API definition with no 'paths': {api_definition.get('info', {}).get('title')}"
            )
            continue

        if group_name not in config["groups"]:
            config["groups"][group_name] = {}

        print(f"Processing paths for group '{group_name}'...")
        for path, path_item in paths.items():
            if "get" not in path_item:
                continue

            get_op = path_item["get"]
            summary = get_op.get("summary", path)  # Use path as fallback for summary
            endpoint_key = sanitize_key(summary)

            # The path from the file is relative, so we use it directly.
            api_path = path

            parameters = get_op.get("parameters", [])
            date_params, param_columns, static_params = analyze_parameters(parameters)

            # Heuristic to identify the main date parameter for partitioning
            primary_date_param = (
                "settlementDate" if "settlementDate" in date_params else "from"
            )

            endpoint_config = {
                "path": api_path,
                "base": base,
                "table_name": f"{table_name_prefix}_{endpoint_key}",
                "params": static_params,
                "date_params": date_params,
                "param_columns": param_columns,
                "primary_date_param": primary_date_param,
                "response_format": "json",  # Default for Insights
            }

            # BMRS datasets are typically CSV
            if base == "bmrs":
                endpoint_config["response_format"] = "csv"

            config["groups"][group_name][endpoint_key] = endpoint_config
            print(f"  + Added endpoint '{endpoint_key}' to group '{group_name}'")

    return config


def main():
    """Main function to generate and write the config file."""
    config_data = build_config()

    print(f"\nWriting generated configuration to {OUTPUT_YAML_FILE}...")
    with open(OUTPUT_YAML_FILE, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, indent=2)

    print("\nConfiguration generation complete.")
    print(f"Next steps:")
    print(f"1. Review the generated file: {OUTPUT_YAML_FILE}")
    print(f"2. Update the ingestion script to use this new configuration file.")
    print(
        f"   e.g., python ingest_insights_endpoints.py --config {OUTPUT_YAML_FILE} ..."
    )


if __name__ == "__main__":
    main()
