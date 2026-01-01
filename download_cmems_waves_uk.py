#!/usr/bin/env python3
"""
Copernicus Marine (CMEMS) UK Wave Data Downloader
Downloads ALL wave variables over UK bounding box (gridded data)

Coverage:
  - Reanalysis: 2020-2025-10-31 (GLOBAL_MULTIYEAR_WAV_001_032)
  - Forecast tail: 2025-11-01 to today (GLOBAL_ANALYSISFORECAST_WAV_001_027)

Requires:
  pip install copernicusmarine xarray netcdf4 pandas

Setup:
  export CMEMS_USERNAME="your_username"
  export CMEMS_PASSWORD="your_password"
  (or configure via: copernicusmarine login)
"""

from __future__ import annotations
import os
from datetime import date
import pandas as pd
import copernicusmarine as cm

# -----------------------------
# UK BOUNDING BOX (optimized for offshore wind region + Atlantic approaches)
# Covers all UK offshore wind farms plus upstream weather systems
# -----------------------------
UK_BOX = dict(
    minimum_longitude=-12.0,  # West: Atlantic approaches (upstream systems)
    maximum_longitude=  4.5,  # East: North Sea (all UK farms)
    minimum_latitude= 49.5,   # South: English Channel
    maximum_latitude= 61.5,   # North: Scotland offshore
)

# UK offshore wind farms are concentrated in:
#   - North Sea: 51-58°N, 0-4°E (Hornsea, Dogger Bank, Beatrice)
#   - Irish Sea: 53-55°N, -5 to -3°E (Walney, Gwynt y Môr)
#   - Atlantic approaches: Provide 12-48hr upstream wave warning
# This bbox captures all farms + ~500km Atlantic buffer for weather systems

OUTDIR = "cmems_waves_uk"
os.makedirs(OUTDIR, exist_ok=True)

# Set credentials from environment (export before running)
os.environ.setdefault('COPERNICUSMARINE_SERVICE_USERNAME', 'majorgeorge273@gmail.com')
os.environ.setdefault('COPERNICUSMARINE_SERVICE_PASSWORD', 'Ferit01342@2')

# Copernicus Marine product IDs (BLUE OCEAN = physical ocean/waves)
REANALYSIS_PRODUCT = "GLOBAL_MULTIYEAR_WAV_001_032"
FORECAST_PRODUCT   = "GLOBAL_ANALYSISFORECAST_WAV_001_027"

# Date range
START = "2020-01-01"
REANALYSIS_END = "2025-10-31"  # Per product documentation
END_TODAY = date.today().isoformat()

print("="*80)
print("CMEMS UK WAVE DATA DOWNLOADER")
print("="*80)
print(f"Bounding box: {UK_BOX['minimum_latitude']:.1f}-{UK_BOX['maximum_latitude']:.1f}°N, "
      f"{UK_BOX['minimum_longitude']:.1f}-{UK_BOX['maximum_longitude']:.1f}°E")
print(f"Period: {START} → {END_TODAY}")
print(f"Output: {OUTDIR}")
print("")


def list_product_datasets_and_vars(product_id: str):
    """
    Auto-discover all datasets and variables from product metadata.
    Returns list of (dataset_id, [variable_ids...])
    """
    print(f"Discovering datasets/variables for {product_id}...")
    
    try:
        cat = cm.describe(product_id=product_id)
        cat_dict = cat.model_dump()
        datasets = cat_dict["products"][0]["datasets"]
    except Exception as e:
        raise RuntimeError(
            f"Failed to parse catalogue for {product_id}. "
            f"Error: {e}. Try: pip install -U copernicusmarine"
        )

    out = []
    for ds in datasets:
        dataset_id = ds["dataset_id"]
        variables = []
        
        # Try common metadata locations
        if "variables" in ds:
            variables = [v["variable_id"] for v in ds["variables"]]
        else:
            # Search nested structure
            for ver in ds.get("versions", []):
                for part in ver.get("parts", []):
                    for v in part.get("variables", []):
                        vid = v.get("variable_id")
                        if vid:
                            variables.append(vid)
            variables = sorted(set(variables))

        if variables:
            out.append((dataset_id, variables))
            print(f"  ✅ {dataset_id}: {len(variables)} variables")
    
    if not out:
        raise RuntimeError(f"No datasets/variables found for {product_id}")
    
    return out


def subset_year(dataset_id: str, variables: list[str], year: int, out_path: str):
    """
    Download one year of gridded wave data for UK box.
    """
    start = f"{year}-01-01"
    end   = f"{year}-12-31"

    print(f"\n[DOWNLOAD] {dataset_id} year {year} ({len(variables)} vars)...")
    
    cm.subset(
        dataset_id=dataset_id,
        variables=variables,
        start_datetime=start,
        end_datetime=end,
        output_filename=os.path.basename(out_path),  # Just filename, not full path
        output_directory=os.path.dirname(out_path),  # Directory only
        file_format="netcdf",
        **UK_BOX
    )
    
    print(f"  ✅ Saved: {out_path}")


def subset_timerange(dataset_id: str, variables: list[str], start: str, end: str, out_path: str):
    """
    Download arbitrary time range (for partial years or forecast tail).
    """
    print(f"\n[DOWNLOAD] {dataset_id} {start} → {end} ({len(variables)} vars)...")
    
    cm.subset(
        dataset_id=dataset_id,
        variables=variables,
        start_datetime=start,
        end_datetime=end,
        output_filename=os.path.basename(out_path),  # Just filename
        output_directory=os.path.dirname(out_path),  # Directory only
        file_format="netcdf",
        **UK_BOX
    )
    
    print(f"  ✅ Saved: {out_path}")


def main():
    print("Step 1: Reanalysis (2020 → 2025-10-31)")
    print("-" * 60)
    
    # GLOBAL_MULTIYEAR_WAV_001_032 - Wave reanalysis
    # Use explicit dataset_id and variables (auto-discovery failing)
    REANALYSIS_DATASET = "cmems_mod_glo_wav_my_0.2deg_PT3H-i"
    
    # Core wave variables from product documentation
    WAVE_VARS = [
        "VHM0",       # Significant wave height (m)
        "VMDR",       # Mean wave direction (degrees)
        "VTPK",       # Wave period at spectral peak (s)
        "VTM01_SW1",  # Mean period of primary swell (s)
        "VTM01_SW2",  # Mean period of secondary swell (s)
        "VTM01_WW",   # Mean period of wind waves (s)
        "VHM0_SW1",   # Significant height of primary swell (m)
        "VHM0_SW2",   # Significant height of secondary swell (m)
        "VHM0_WW",    # Significant height of wind waves (m)
        "VMDR_SW1",   # Direction of primary swell (degrees)
        "VMDR_SW2",   # Direction of secondary swell (degrees)
        "VMDR_WW",    # Direction of wind waves (degrees)
    ]
    
    print(f"Dataset: {REANALYSIS_DATASET}")
    print(f"Variables: {len(WAVE_VARS)} wave parameters")
    print(f"Dataset: {REANALYSIS_DATASET}")
    print(f"Variables: {len(WAVE_VARS)} wave parameters")
    
    # Download year-by-year (safer, resumable)
    years = range(2020, 2026)  # 2020..2025
    
    for y in years:
        if y < 2025:
            # Full year
            out_file = os.path.join(OUTDIR, f"{REANALYSIS_DATASET}_UK_{y}.nc")
            if os.path.exists(out_file):
                print(f"  [SKIP] {out_file} (already exists)")
                continue
            subset_year(REANALYSIS_DATASET, WAVE_VARS, y, out_file)
        else:
            # 2025 partial (Jan 1 → Oct 31)
            out_file = os.path.join(OUTDIR, f"{REANALYSIS_DATASET}_UK_2025_to_1031.nc")
            if os.path.exists(out_file):
                print(f"  [SKIP] {out_file} (already exists)")
                continue
            subset_timerange(REANALYSIS_DATASET, WAVE_VARS, "2025-01-01", REANALYSIS_END, out_file)

    # Optional: Forecast tail (Nov-Dec 2025 if today > Oct 31)
    if pd.to_datetime(END_TODAY) > pd.to_datetime(REANALYSIS_END):
        print("\n" + "="*80)
        print("Step 2: Forecast Tail (2025-11-01 → today)")
        print("-" * 60)
        
        # GLOBAL_ANALYSISFORECAST_WAV_001_027 - Analysis/Forecast
        FORECAST_DATASET = "cmems_mod_glo_wav_anfc_0.083deg_PT3H-i"
        
        out_file = os.path.join(OUTDIR, f"{FORECAST_DATASET}_UK_2025-11-01_to_{END_TODAY}.nc")
        if os.path.exists(out_file):
            print(f"  [SKIP] {out_file} (already exists)")
        else:
            subset_timerange(FORECAST_DATASET, WAVE_VARS, "2025-11-01", END_TODAY, out_file)

    print("\n" + "="*80)
    print("✅ ALL CMEMS WAVE DOWNLOADS COMPLETE")
    print("="*80)
    
    # List downloaded files
    files = sorted([f for f in os.listdir(OUTDIR) if f.endswith('.nc')])
    print(f"\nDownloaded files ({len(files)}):")
    total_size = 0
    for f in files:
        path = os.path.join(OUTDIR, f)
        size_mb = os.path.getsize(path) / (1024**2)
        total_size += size_mb
        print(f"  {f}: {size_mb:.1f} MB")
    
    print(f"\nTotal size: {total_size:.1f} MB ({total_size/1024:.2f} GB)")
    print(f"Output directory: {OUTDIR}")
    print("\nNext steps:")
    print("  1. Run: python3 ingest_cmems_waves_to_bigquery.py")
    print("  2. Query: SELECT * FROM uk_energy_prod.cmems_waves_uk_grid LIMIT 100")


if __name__ == "__main__":
    main()
