#!/usr/bin/env python3
"""
ERA5 Hourly Point Time-Series Downloader
Downloads wind (u100, v100), temperature, and dewpoint at UK turbine locations
2020-2025 (6 years × 41 locations = 246 year-location requests)

Requires:
  pip install cdsapi pandas numpy xarray netcdf4
  
Setup:
  1. Register at cds.climate.copernicus.eu
  2. Create ~/.cdsapirc:
     url: https://cds.climate.copernicus.eu/api/v2
     key: {UID}:{API_KEY}
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import numpy as np
import xarray as xr
import cdsapi

# ---- USER SETTINGS ----
LOCATIONS_CSV = "turbines.csv"   # Must have: id, latitude, longitude
OUT_DIR = "era5_points"
MAX_WORKERS = 3                  # 2-4 recommended (don't hammer CDS queue)
YEARS = list(range(2020, 2026))  # 2020..2025 inclusive
# -----------------------

os.makedirs(OUT_DIR, exist_ok=True)

print("="*80)
print("ERA5 HOURLY POINT TIME-SERIES DOWNLOADER")
print("="*80)
print(f"Output directory: {OUT_DIR}")
print(f"Years: {YEARS[0]}-{YEARS[-1]} ({len(YEARS)} years)")
print(f"Concurrent workers: {MAX_WORKERS}")
print("")

# Initialize CDS API client (reads ~/.cdsapirc)
try:
    c = cdsapi.Client()
    print("✅ CDS API credentials loaded from ~/.cdsapirc")
except Exception as e:
    print(f"❌ Failed to initialize CDS API client: {e}")
    print("\nSetup required:")
    print("  1. Register at https://cds.climate.copernicus.eu")
    print("  2. Create ~/.cdsapirc with your UID:API_KEY")
    exit(1)


def dewpoint_to_rh(t_k, td_k):
    """
    Compute relative humidity (%) from temperature and dewpoint (Kelvin).
    Uses Magnus formula (over water); accurate for typical meteorological ranges.
    """
    t_c = t_k - 273.15
    td_c = td_k - 273.15
    a, b = 17.625, 243.04
    es = np.exp((a * t_c) / (b + t_c))
    e  = np.exp((a * td_c) / (b + td_c))
    rh = 100.0 * (e / es)
    return np.clip(rh, 0, 100)


def uv_to_speed_dir(u, v):
    """
    Convert U/V wind components to speed (m/s) and direction (degrees).
    Direction convention: meteorological "from" direction (0° = North)
    """
    speed = np.sqrt(u**2 + v**2)
    # arctan2(-u, -v) gives meteorological "from" direction
    direction = (np.degrees(np.arctan2(-u, -v)) + 360) % 360
    return speed, direction


def build_year_request(lat, lon, year):
    """
    Build CDS API request for full year at single point.
    Uses ERA5 hourly time-series dataset (optimized for point queries).
    """
    return {
        "variable": [
            "u_component_of_wind_100m",
            "v_component_of_wind_100m",
            "2m_temperature",
            "2m_dewpoint_temperature",
        ],
        "year": str(year),
        "month": [f"{m:02d}" for m in range(1, 13)],
        "day": [f"{d:02d}" for d in range(1, 32)],
        "time": [f"{h:02d}:00" for h in range(0, 24)],
        # "area" expects [N, W, S, E]; use point as degenerate bbox
        "area": [lat, lon, lat, lon],
        "format": "netcdf",
    }


def build_month_request(lat, lon, year, month):
    """
    Build CDS API request for single month (fallback if year request fails).
    """
    import calendar
    days = [f"{d:02d}" for d in range(1, calendar.monthrange(year, month)[1] + 1)]
    return {
        "variable": [
            "u_component_of_wind_100m",
            "v_component_of_wind_100m",
            "2m_temperature",
            "2m_dewpoint_temperature",
        ],
        "year": str(year),
        "month": [f"{month:02d}"],
        "day": days,
        "time": [f"{h:02d}:00" for h in range(0, 24)],
        "area": [lat, lon, lat, lon],
        "format": "netcdf",
    }


def retrieve_with_fallback(station_id, lat, lon, year):
    """
    Download ERA5 data for one year at one location.
    Tries full year first; falls back to 12 monthly requests if year fails.
    Returns path to NetCDF file.
    """
    year_nc = os.path.join(OUT_DIR, f"era5_{station_id}_{year}.nc")
    
    if os.path.exists(year_nc):
        print(f"  [SKIP] {station_id} {year} (already downloaded)")
        return year_nc

    try:
        print(f"  [DOWNLOAD] {station_id} {year} (year request)...")
        c.retrieve(
            "reanalysis-era5-single-levels-timeseries",
            build_year_request(lat, lon, year),
            year_nc
        )
        print(f"  [✅] {station_id} {year}")
        return year_nc
        
    except Exception as e:
        print(f"  [FALLBACK] {station_id} {year} → monthly requests (error: {str(e)[:100]})")
        month_files = []
        
        for m in range(1, 13):
            m_nc = os.path.join(OUT_DIR, f"era5_{station_id}_{year}_{m:02d}.nc")
            if not os.path.exists(m_nc):
                print(f"    Downloading month {m}/12...")
                c.retrieve(
                    "reanalysis-era5-single-levels-timeseries",
                    build_month_request(lat, lon, year, m),
                    m_nc
                )
            month_files.append(m_nc)

        # Merge monthly files into single year file
        print(f"    Merging 12 months into {year_nc}...")
        ds = xr.open_mfdataset(month_files, combine="by_coords")
        ds.to_netcdf(year_nc)
        ds.close()
        
        # Clean up monthly files
        for m_nc in month_files:
            os.remove(m_nc)
            
        print(f"  [✅] {station_id} {year} (monthly fallback)")
        return year_nc


def process_to_parquet(nc_path, parquet_path, station_id, year):
    """
    Convert NetCDF to Parquet with derived variables (wind speed/dir, RH).
    """
    if os.path.exists(parquet_path):
        return
        
    ds = xr.open_dataset(nc_path)
    
    # Extract variables
    u = ds["u_component_of_wind_100m"].values
    v = ds["v_component_of_wind_100m"].values
    t = ds["2m_temperature"].values
    td = ds["2m_dewpoint_temperature"].values
    time_vals = pd.to_datetime(ds["time"].values)

    # Compute derived variables
    speed, direction = uv_to_speed_dir(u, v)
    rh = dewpoint_to_rh(t, td)

    # Build DataFrame
    df = pd.DataFrame({
        "turbine_id": station_id,
        "time": time_vals,
        "u100": u,
        "v100": v,
        "t2m_k": t,
        "d2m_k": td,
        "wind_speed_100m": speed,
        "wind_dir_from_deg": direction,
        "rh_2m_pct": rh,
    })
    
    df.to_parquet(parquet_path, index=False)
    ds.close()
    print(f"  [PARQUET] {station_id} {year}: {len(df)} rows")


def job(row):
    """
    Process one turbine location across all years.
    """
    sid = str(row["id"])
    lat = float(row["latitude"])
    lon = float(row["longitude"])

    print(f"\n{'='*60}")
    print(f"Processing: {sid}")
    print(f"Location: {lat:.2f}°N, {lon:.2f}°E")
    print(f"{'='*60}")

    for y in YEARS:
        # Download NetCDF
        nc = retrieve_with_fallback(sid, lat, lon, y)
        
        # Convert to Parquet
        pq = os.path.join(OUT_DIR, f"era5_{sid}_{y}.parquet")
        process_to_parquet(nc, pq, sid, y)
    
    return sid


def main():
    # Load turbine locations
    try:
        locs = pd.read_csv(LOCATIONS_CSV)
        required_cols = {'id', 'latitude', 'longitude'}
        if not required_cols.issubset(locs.columns):
            raise ValueError(f"CSV must have columns: {required_cols}")
        print(f"✅ Loaded {len(locs)} turbine locations from {LOCATIONS_CSV}")
    except Exception as e:
        print(f"❌ Failed to load {LOCATIONS_CSV}: {e}")
        exit(1)

    print(f"\nTotal requests: {len(locs)} locations × {len(YEARS)} years = {len(locs) * len(YEARS)}")
    print(f"Estimated time: 1-12 hours (depends on CDS queue)")
    print(f"\nStarting downloads with {MAX_WORKERS} concurrent workers...\n")

    t0 = time.time()
    completed = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(job, row) for _, row in locs.iterrows()]
        
        for f in as_completed(futures):
            try:
                sid = f.result()
                completed += 1
                print(f"\n[{completed}/{len(locs)}] Completed: {sid}")
            except Exception as e:
                print(f"\n❌ Job failed: {e}")

    elapsed = time.time() - t0
    print("\n" + "="*80)
    print("✅ ALL ERA5 DOWNLOADS COMPLETE")
    print("="*80)
    print(f"Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
    print(f"Locations processed: {completed}/{len(locs)}")
    print(f"Output directory: {OUT_DIR}")
    print(f"Files created: {len(locs) * len(YEARS)} NetCDF + {len(locs) * len(YEARS)} Parquet")
    print("\nNext steps:")
    print("  1. Run: python3 ingest_era5_to_bigquery.py")
    print("  2. Query: SELECT * FROM uk_energy_prod.era5_turbine_hourly LIMIT 100")


if __name__ == "__main__":
    main()
