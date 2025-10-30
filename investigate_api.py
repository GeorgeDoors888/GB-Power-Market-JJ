import argparse

import pandas as pd

from ingest_elexon_fixed import _fetch_bmrs, _parse_iso_date


def investigate_dataset(
    dataset: str, start_date: str, end_date: str, bm_units: str = None
):
    """
    Fetches a sample of data for a given dataset and prints its structure.
    """
    print(f"--- Investigating dataset: {dataset} ---")

    start_dt = _parse_iso_date(start_date)
    end_dt = _parse_iso_date(end_date)

    bm_units_list = bm_units.split(",") if bm_units else None

    try:
        df = _fetch_bmrs(dataset, start_dt, end_dt, bm_units=bm_units_list)

        if df is None or df.empty:
            print("No data returned from the API for this dataset and time range.")
            return

        print("\n[+] DataFrame Info:")
        df.info()

        print("\n[+] DataFrame Columns:")
        print(df.columns.tolist())

        print(f"\n[+] First 5 rows of data for {dataset}:")
        print(df.head())

    except Exception as e:
        print(f"\n[!] An error occurred while fetching data for {dataset}: {e}")

    print("-" * (len(dataset) + 28))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Investigate Elexon BMRS API responses."
    )
    parser.add_argument(
        "--datasets",
        type=str,
        default="PN,MELS,MILS",
        help="Comma-separated list of datasets to investigate.",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2025-08-28",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2025-08-29",
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--bm-units",
        type=str,
        help="Comma-separated list of BM units to filter by.",
        default="2__AANGE001,2__ALOND000",
    )

    args = parser.parse_args()

    datasets_to_check = [ds.strip().upper() for ds in args.datasets.split(",")]

    for ds in datasets_to_check:
        investigate_dataset(ds, args.start, args.end, args.bm_units)
