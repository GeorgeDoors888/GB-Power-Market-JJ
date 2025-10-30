import argparse  # Import argparse
import logging
from datetime import datetime

import pandas as pd

from ingest_elexon_fixed import CHUNK_RULES, _fetch_bmrs

# Configure logging to show progress
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def generate_api_schema_report(year: int):
    """
    Fetches a sample from each dataset for a specific year from the Elexon API,
    inspects its schema, and writes the findings to a year-specific CSV file.
    """
    output_csv_file = f"api_schema_report_{year}.csv"
    sample_date = datetime(year, 6, 1)  # Use June 1st of the given year for sampling

    schema_report_data = []
    datasets_to_check = sorted(list(CHUNK_RULES.keys()))

    total_datasets = len(datasets_to_check)
    logging.info(
        f"Starting schema investigation for {total_datasets} datasets for the year {year}..."
    )

    for i, dataset in enumerate(datasets_to_check):
        logging.info(
            f"[{i+1}/{total_datasets}] --- Checking dataset: {dataset} for year {year} ---"
        )
        try:
            start_dt = sample_date
            # Fetch a small 1-hour window
            end_dt = start_dt.replace(hour=1)

            # Use the existing fetch function from the ingestion script
            df = _fetch_bmrs(dataset, start_dt, end_dt)

            if df is None or df.empty:
                logging.warning(
                    f"No data returned from API for {dataset} in {year}. Marking as empty."
                )
                schema_report_data.append(
                    {
                        "dataset": dataset,
                        "column_name": "N/A",
                        "api_dtype": "N/A",
                        "sample_value": "No data returned from API for sample period.",
                    }
                )
                continue

            logging.info(
                f"Successfully fetched {len(df)} rows for {dataset}. Analyzing schema..."
            )

            # Get the first row to use for sample values
            sample_row = df.head(1)

            for col in df.columns:
                dtype = str(df[col].dtype)
                sample_value = (
                    sample_row[col].iloc[0] if not sample_row.empty else "N/A"
                )

                schema_report_data.append(
                    {
                        "dataset": dataset,
                        "column_name": col,
                        "api_dtype": dtype,
                        "sample_value": sample_value,
                    }
                )

        except Exception as e:
            logging.error(
                f"An error occurred while fetching or processing {dataset} for year {year}: {e}",
                exc_info=True,
            )
            schema_report_data.append(
                {
                    "dataset": dataset,
                    "column_name": "N/A",
                    "api_dtype": "ERROR",
                    "sample_value": str(e),
                }
            )

    # Convert the collected data into a pandas DataFrame
    report_df = pd.DataFrame(schema_report_data)

    # Save the final report to a CSV file
    try:
        report_df.to_csv(output_csv_file, index=False)
        logging.info(
            f"✅ Schema report for {year} successfully generated and saved to '{output_csv_file}'"
        )
    except Exception as e:
        logging.error(f"Failed to save the report for {year} to CSV: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Elexon API schema report for a specific year."
    )
    parser.add_argument(
        "year", type=int, help="The year to generate the schema report for."
    )
    args = parser.parse_args()

    generate_api_schema_report(args.year)
