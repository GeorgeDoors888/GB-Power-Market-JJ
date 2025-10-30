import pandas as pd
import os

# === Load the DUoS master file ===
duos_file = "duos_outputs2/DNO_DUoS_All_Data.csv"   # path to your file
print(f"Looking for file at: {os.path.abspath(duos_file)}")
df = pd.read_csv(duos_file)

# Check data loaded correctly
print(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
print("Columns:", df.columns.tolist())
print("\nSample data:")
print(df.head(3))

# === Standardise date/year ===
# The file has a "Year" column, but you might also want a date index.
if 'Year' in df.columns:
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    print(f"\nYear column values: {df['Year'].unique()}")
else:
    print("\nWARNING: No 'Year' column found!")

# If there's a more granular time field (e.g. Time_Period, Band), you can build a datetime
if 'Time_Period' in df.columns:
    print(f"\nTime_Period sample values: {df['Time_Period'].head(3).tolist()}")
    # Example: assume Time_Period encodes month/day, combine with Year
    # (Adjust depending on your format)
    df['Date'] = pd.to_datetime(df['Year'].astype(str), format='%Y', errors='coerce')
    print(f"Created Date column using Year only: {df['Date'].head(3)}")
else:
    # Fallback: use just the year (as a datetime for consistency)
    print("\nWARNING: No 'Time_Period' column found!")
    df['Date'] = pd.to_datetime(df['Year'], format='%Y', errors='coerce')

# === Organise data by DNO ID and Date ===
if 'DNO_Key' in df.columns:
    print(f"\nDNO_Key sample values: {df['DNO_Key'].head(3).tolist()}")
else:
    print("\nWARNING: No 'DNO_Key' column found!")
# Check if required numeric columns exist
required_columns = ['Min_Rate_p_kWh', 'Max_Rate_p_kWh', 'Mean_Rate_p_kWh', 'Median_Rate_p_kWh', 'Count']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    print(f"\nWARNING: Missing required columns: {missing_columns}")
    # Try to find similar columns
    for missing in missing_columns:
        similar = [col for col in df.columns if missing.lower().replace('_', '') in col.lower().replace('_', '')]
        if similar:
            print(f"  - Instead of {missing}, found: {similar}")

# Proceed with aggregation using available columns
agg_columns = {col: 'mean' for col in required_columns if col in df.columns}
if not agg_columns:
    print("\nERROR: No columns to aggregate!")
else:
    grouped = df.groupby(['DNO_Key', 'Date']).agg(agg_columns).reset_index()
    print(f"\nAfter grouping: {grouped.shape[0]} rows")
    
    # === Optional: merge in reference file for names ===
    dno_ref_file = "duos_outputs2/DNO_Reference.csv"
    print(f"Looking for DNO reference file at: {os.path.abspath(dno_ref_file)}")
    dno_ref = pd.read_csv(dno_ref_file)
    print(f"DNO reference loaded: {dno_ref.shape[0]} rows")
    print(f"DNO_Key values in reference: {dno_ref['DNO_Key'].unique().tolist()[:5]}...")
    
    merged = grouped.merge(dno_ref[['DNO_Key', 'DNO_Name']], on='DNO_Key', how='left')
    print(f"After merging: {merged.shape[0]} rows")
    
    # === Save organised data ===
    merged = merged.sort_values(['DNO_Key', 'Date'])
    merged.to_csv("Organised_DNO_By_Date.csv", index=False)
    
    print("\n✅ Organised data saved to Organised_DNO_By_Date.csv")
    print(merged.head(20))
