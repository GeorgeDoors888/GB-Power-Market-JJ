import logging

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

YEARS = [2022, 2023, 2024, 2025]
OUTPUT_FILE = "dataset_availability_summary.txt"


def summarize_availability():
    """
    Reads the yearly schema reports and identifies which datasets were unavailable
    (i.e., returned no data) for the sample period in each year.
    The summary is printed to the console and saved to a text file.
    """
    availability_summary = {year: [] for year in YEARS}

    logging.info("Starting dataset availability summary...")

    for year in YEARS:
        try:
            filename = f"api_schema_report_{year}.csv"
            df = pd.read_csv(filename)

            # Find datasets that are marked as having no data
            unavailable_datasets = (
                df[
                    df["sample_value"] == "No data returned from API for sample period."
                ]["dataset"]
                .unique()
                .tolist()
            )

            availability_summary[year] = sorted(unavailable_datasets)
            logging.info(
                f"Found {len(unavailable_datasets)} unavailable datasets for {year}."
            )

        except FileNotFoundError:
            logging.error(f"File not found: {filename}. Skipping this year.")
            continue

    # Generate the report string
    report_lines = [
        "Dataset Availability Summary (Based on a 1-hour sample from June 1st each year)\n",
        "=" * 80,
        "\n",
    ]

    for year, datasets in availability_summary.items():
        report_lines.append(f"\nUnavailable Datasets for {year}:\n")
        report_lines.append("-" * (len(str(year)) + 25) + "\n")
        if datasets:
            for dataset in datasets:
                report_lines.append(f"- {dataset}\n")
        else:
            report_lines.append("All datasets were available.\n")

    report_content = "".join(report_lines)

    # Print to console
    print(report_content)

    # Save to file
    try:
        with open(OUTPUT_FILE, "w") as f:
            f.write(report_content)
        logging.info(f"Availability summary saved to '{OUTPUT_FILE}'")
    except Exception as e:
        logging.error(f"Failed to save summary file: {e}")


if __name__ == "__main__":
    summarize_availability()
