import logging

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

YEARS = [2022, 2023, 2024, 2025]
OUTPUT_COMPARISON_FILE = "schema_comparison_report.csv"
OUTPUT_CHANGES_ONLY_FILE = "schema_changes_only_report.csv"


def compare_schema_reports():
    """
    Loads schema reports from multiple years, compares them, and generates
    a full comparison report and a report highlighting only the changes.
    """
    all_schemas = []
    logging.info(f"Loading schema reports for years: {YEARS}")

    for year in YEARS:
        try:
            filename = f"api_schema_report_{year}.csv"
            df = pd.read_csv(filename)
            df["year"] = year
            all_schemas.append(df)
            logging.info(f"Successfully loaded {filename}")
        except FileNotFoundError:
            logging.error(f"File not found: {filename}. Skipping this year.")
            continue

    if not all_schemas:
        logging.error("No schema reports were loaded. Aborting comparison.")
        return

    # Combine all data into a single DataFrame
    combined_df = pd.concat(all_schemas, ignore_index=True)

    # Create a unique identifier for each schema entry (dataset + column)
    # We need to handle the 'N/A' columns for empty datasets
    combined_df["schema_key"] = (
        combined_df["dataset"] + "->" + combined_df["column_name"]
    )

    # Pivot the table to have years as columns and schema as rows
    pivot_df = combined_df.pivot_table(
        index=["dataset", "column_name"],
        columns="year",
        values="api_dtype",
        aggfunc="first",
    ).fillna("NOT_PRESENT")

    # Save the full comparison report
    pivot_df.to_csv(OUTPUT_COMPARISON_FILE)
    logging.info(f"Full schema comparison report saved to '{OUTPUT_COMPARISON_FILE}'")

    # Identify rows with changes
    # A change occurs if the number of unique values in a row is greater than 1
    # (ignoring "NOT_PRESENT" which just means the dataset/column wasn't there)
    def has_changed(row):
        # Count unique values, excluding 'NOT_PRESENT'
        unique_values = row[row != "NOT_PRESENT"].nunique()
        return unique_values > 1

    changes = pivot_df.apply(has_changed, axis=1)
    changes_df = pivot_df[changes]

    if changes_df.empty:
        logging.info("No schema changes detected across the years.")
    else:
        changes_df.to_csv(OUTPUT_CHANGES_ONLY_FILE)
        logging.info(f"Schema changes report saved to '{OUTPUT_CHANGES_ONLY_FILE}'")


if __name__ == "__main__":
    compare_schema_reports()
