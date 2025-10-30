import pickle

import pandas as pd


def analyze_dataframe(file_path, column_name):
    """
    Loads a pickled DataFrame and performs an in-depth analysis on a specific column
    to find rows with non-scalar or problematic data types.
    """
    print(f"--- Analyzing {file_path} for column '{column_name}' ---")

    try:
        with open(file_path, "rb") as f:
            df = pickle.load(f)
    except Exception as e:
        print(f"❌ Failed to load pickle file: {e}")
        return

    print(f"✅ Loaded DataFrame with {len(df)} rows.")

    problematic_rows = []

    # Find rows where the column contains lists, dicts, or other non-standard types
    for index, value in df[column_name].items():
        # Check for list or dict types specifically
        if isinstance(value, (list, dict)):
            problematic_rows.append((index, value, type(value)))
        # Also check for pandas NA, which can cause issues
        elif pd.isna(value) and not isinstance(value, (str, float, int)):
            problematic_rows.append((index, value, type(value)))

    if not problematic_rows:
        print(
            f"✅ No rows with list, dict, or complex NA types found in '{column_name}'."
        )

        # If no complex types, let's check for simple type mixing (e.g. str and float)
        unique_types = df[column_name].apply(type).unique()
        if len(unique_types) > 1:
            print(f"⚠️ Found multiple simple data types: {unique_types}")
            print(df[column_name].apply(type).value_counts())
        else:
            print("✅ Column contains a single, simple data type.")

    else:
        print(f"🚨 Found {len(problematic_rows)} problematic rows in '{column_name}':")
        for index, value, v_type in problematic_rows:
            print(f"  - Row index {index}: Value='{value}' (Type: {v_type})")

    print("-" * 50 + "\n")


if __name__ == "__main__":
    # Analyze the BOD dataset
    analyze_dataframe(
        "debug_frames/BOD__window_from_utc_20250829_134351.pkl", "_window_from_utc"
    )

    # Analyze the RDRI dataset
    analyze_dataframe("debug_frames/RDRI_elbow2_20250829_134422.pkl", "elbow2")
