#!/usr/bin/env python3
"""
ERA5 CDS Download Benchmark & Full Pipeline

What this script does:
1. Downloads ERA5 data from CDS API (weather + ocean/wave variables)
2. Saves NetCDF files permanently to disk (Dell storage)
3. Parses and uploads to BigQuery
4. Benchmarks 1-month download and extrapolates to full timeline
5. Provides accurate time estimates for complete dataset

Strategy:
- One farm at a time (sequential completion for early analysis)
- Icing season priority (Nov-Mar first, then Apr-Oct)
- Rate-limited by CDS free tier (400 seconds between requests)
- Files saved to ~/era5_downloads/ before BigQuery upload

Install:
  pip3 install cdsapi xarray netCDF4 pandas google-cloud-bigquery pyarrow
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

import cdsapi
import xarray as xr
import pandas as pd
from google.cloud import bigquery


# -------------------------
# CONFIG
# -------------------------

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_OCEAN = "era5_ocean_wave_data"
TABLE_WEATHER = "era5_weather_data"
LOCATION = "US"

# Storage directories
STORAGE_DIR_OCEAN = Path.home() / "era5_downloads" / "ocean_wave"
STORAGE_DIR_WEATHER = Path.home() / "era5_downloads" / "weather"
STORAGE_DIR_OCEAN.mkdir(parents=True, exist_ok=True)
STORAGE_DIR_WEATHER.mkdir(parents=True, exist_ok=True)

# Date range
START_YEAR = 2020
END_YEAR = 2025
ICING_MONTHS = [11, 12, 1, 2, 3]
NON_ICING_MONTHS = [4, 5, 6, 7, 8, 9, 10]

# CDS API rate limiting (free tier)
CDS_WAIT_SECONDS = 400  # Mandatory wait between requests


# -------------------------
# VARIABLE GROUPS
# -------------------------

OCEAN_WAVE_GROUPS = [
    {
        'name': 'air_sea_interaction',
        'vars': [
            'air_density_over_the_oceans',
            'coefficient_of_drag_with_waves',
            'ocean_surface_stress_equivalent_10m_neutral_wind_speed',
            'ocean_surface_stress_equivalent_10m_neutral_wind_direction',
            'normalized_energy_flux_into_ocean',
        ],
    },
    {
        'name': 'wave_basics',
        'vars': [
            'significant_height_of_combined_wind_waves_and_swell',
            'significant_height_of_wind_waves',
            'significant_height_of_total_swell',
            'mean_wave_period',
            'peak_wave_period',
            'mean_wave_direction',
        ],
    },
    {
        'name': 'wave_details',
        'vars': [
            'mean_direction_of_wind_waves',
            'mean_direction_of_total_swell',
            'mean_period_of_wind_waves',
            'mean_period_of_total_swell',
            'mean_zero_crossing_wave_period',
            'maximum_individual_wave_height',
        ],
    },
    {
        'name': 'spectral_properties',
        'vars': [
            'wave_spectral_peakedness',
            'wave_spectral_directional_width',
            'mean_square_slope_of_waves',
            'significant_height_of_first_swell_partition',
            'significant_height_of_second_swell_partition',
            'significant_height_of_third_swell_partition',
        ],
    },
    {
        'name': 'bathymetry',
        'vars': ['model_bathymetry'],
    },
]

WEATHER_GROUPS = [
    {
        'name': 'temperature_humidity',
        'vars': ['2m_temperature', '2m_dewpoint_temperature'],
    },
    {
        'name': 'precipitation_cloud',
        'vars': ['total_precipitation', 'total_cloud_cover'],
    },
    {
        'name': 'wind',
        'vars': ['10m_u_component_of_wind', '10m_v_component_of_wind'],
    },
]


# -------------------------
# DATA CLASSES
# -------------------------

@dataclass(frozen=True)
class WindFarm:
    name: str
    lat: float
    lon: float
    capacity_mw: int
    farm_type: str = "fixed"  # fixed or floating


@dataclass
class BenchmarkResult:
    """Results from benchmarking a single month download."""
    farm_name: str
    year: int
    month: int
    variable_groups: int
    requests_made: int
    download_time_s: float
    parse_time_s: float
    upload_time_s: float
    write_time_s: float
    total_time_s: float
    rows_uploaded: int
    files_saved: int
    total_file_size_mb: float
    errors: int = 0


@dataclass
class FullRunStats:
    """Statistics for complete download run."""
    total_farms: int
    total_months: int
    total_requests: int
    total_time_s: float
    total_rows: int
    total_files: int
    total_size_mb: float
    avg_time_per_request_s: float
    avg_time_per_farm_days: float
    errors: int = 0
    benchmark: Optional[BenchmarkResult] = None


# -------------------------
# HELPERS
# -------------------------

def format_seconds(s: float) -> str:
    """Format seconds as human-readable duration."""
    s = float(s)
    if s < 60:
        return f"{s:.1f}s"
    if s < 3600:
        return f"{s/60:.1f}m"
    if s < 86400:
        return f"{s/3600:.2f}h"
    return f"{s/86400:.2f} days"


def generate_month_list(priority_icing_season: bool = True) -> List[tuple[int, int]]:
    """Generate (year, month) list with optional icing season priority."""
    months = []
    
    if priority_icing_season:
        # Icing season first (Nov-Mar)
        for year in range(START_YEAR, END_YEAR + 1):
            for month in ICING_MONTHS:
                if year == START_YEAR and month < 11:
                    continue
                if year == END_YEAR and month > 12:
                    continue
                months.append((year, month))
        
        # Then non-icing season (Apr-Oct)
        for year in range(START_YEAR, END_YEAR + 1):
            for month in NON_ICING_MONTHS:
                if year > END_YEAR:
                    continue
                months.append((year, month))
    else:
        # Sequential by year
        for year in range(START_YEAR, END_YEAR + 1):
            for month in range(1, 13):
                months.append((year, month))
    
    return months


def get_days_in_month(year: int, month: int) -> List[str]:
    """Get list of days for given month."""
    if month == 2:
        days_in_month = 29 if year % 4 == 0 else 28
    elif month in [4, 6, 9, 11]:
        days_in_month = 30
    else:
        days_in_month = 31
    
    return [str(d).zfill(2) for d in range(1, days_in_month + 1)]


# -------------------------
# CDS DOWNLOAD
# -------------------------

def init_cds_client() -> cdsapi.Client:
    """Initialize CDS API client."""
    return cdsapi.Client()


def download_era5_month(
    client: cdsapi.Client,
    farm: WindFarm,
    year: int,
    month: int,
    var_group: Dict[str, Any],
    output_file: Path,
    dataset_type: str = "ocean",
) -> tuple[bool, float, float]:
    """
    Download one month of ERA5 data for one farm and one variable group.
    
    Returns: (success, download_time_s, file_size_mb)
    """
    # Build area box (0.5° around point)
    north = farm.lat + 0.25
    south = farm.lat - 0.25
    east = farm.lon + 0.25
    west = farm.lon - 0.25
    
    days = get_days_in_month(year, month)
    hours = [f"{h:02d}:00" for h in range(24)]
    
    # Base request parameters
    request = {
        'product_type': ['reanalysis'],
        'variable': var_group['vars'],
        'year': [str(year)],
        'month': [str(month).zfill(2)],
        'day': days,
        'time': hours,
        'area': [north, west, south, east],
        'data_format': 'netcdf',
        'download_format': 'unarchived',
    }
    
    # Choose dataset
    if dataset_type == "ocean":
        dataset = 'reanalysis-era5-single-levels'
    else:
        dataset = 'reanalysis-era5-single-levels'
    
    try:
        t0 = time.time()
        result = client.retrieve(dataset, request)
        result.download(str(output_file))
        download_time = time.time() - t0
        
        # Get file size
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        
        return True, download_time, file_size_mb
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False, 0.0, 0.0


# -------------------------
# PARSING & UPLOAD
# -------------------------

def parse_ocean_wave_netcdf(nc_file: Path, farm: WindFarm) -> Optional[pd.DataFrame]:
    """Parse ocean/wave NetCDF file to DataFrame."""
    try:
        ds = xr.open_dataset(nc_file)
        
        data_rows = []
        time_coord = 'valid_time' if 'valid_time' in ds.coords else 'time'
        
        for time_idx in range(len(ds[time_coord])):
            time_val = pd.Timestamp(ds[time_coord].values[time_idx])
            
            row = {
                'farm_name': farm.name,
                'time_utc': time_val,
                'latitude': float(farm.lat),
                'longitude': float(farm.lon),
            }
            
            # Extract available variables
            var_mapping = {
                'air_density_over_the_oceans': 'air_density_kg_m3',
                'coefficient_of_drag_with_waves': 'drag_coefficient',
                'ocean_surface_stress_equivalent_10m_neutral_wind_speed': 'stress_equiv_wind_speed_10m',
                'significant_height_of_combined_wind_waves_and_swell': 'wave_height_m',
                'peak_wave_period': 'wave_peak_period_s',
                'mean_wave_direction': 'wave_direction_deg',
            }
            
            for var_name, col_name in var_mapping.items():
                if var_name in ds:
                    row[col_name] = float(ds[var_name].values[time_idx, 0, 0])
            
            data_rows.append(row)
        
        ds.close()
        return pd.DataFrame(data_rows)
        
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        return None


def upload_to_bigquery(
    df: pd.DataFrame,
    table_name: str,
    project_id: str = PROJECT_ID,
    dataset: str = DATASET,
    location: str = LOCATION,
) -> tuple[bool, float]:
    """Upload DataFrame to BigQuery. Returns (success, upload_time_s)."""
    try:
        t0 = time.time()
        
        client = bigquery.Client(project=project_id, location=location)
        table_id = f"{project_id}.{dataset}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        upload_time = time.time() - t0
        return True, upload_time
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False, 0.0


# -------------------------
# BENCHMARK: Download 1 month
# -------------------------

def benchmark_one_month(
    farm: WindFarm,
    year: int,
    month: int,
    dataset_type: str = "ocean",
    dry_run: bool = False,
) -> BenchmarkResult:
    """
    Benchmark downloading one month of data for one farm.
    
    This gives us accurate timing for:
    - CDS API download speed
    - NetCDF parsing time
    - BigQuery upload time
    - File write time
    """
    print(f"\n{'='*80}")
    print(f"🔬 BENCHMARK: {farm.name} - {year}-{month:02d}")
    print(f"{'='*80}")
    
    client = init_cds_client()
    temp_dir = Path('/tmp/era5_benchmark')
    temp_dir.mkdir(exist_ok=True)
    
    var_groups = OCEAN_WAVE_GROUPS if dataset_type == "ocean" else WEATHER_GROUPS
    storage_dir = STORAGE_DIR_OCEAN if dataset_type == "ocean" else STORAGE_DIR_WEATHER
    table_name = TABLE_OCEAN if dataset_type == "ocean" else TABLE_WEATHER
    
    total_download_time = 0.0
    total_parse_time = 0.0
    total_upload_time = 0.0
    total_write_time = 0.0
    total_rows = 0
    files_saved = 0
    total_file_size = 0.0
    errors = 0
    
    for i, var_group in enumerate(var_groups, 1):
        print(f"\n📥 Group {i}/{len(var_groups)}: {var_group['name']}")
        
        output_file = temp_dir / f"{farm.name.replace(' ', '_')}_{year}_{month:02d}_{var_group['name']}.nc"
        
        # DOWNLOAD
        print(f"   Downloading...")
        if not dry_run:
            success, download_time, file_size = download_era5_month(
                client, farm, year, month, var_group, output_file, dataset_type
            )
            total_download_time += download_time
            total_file_size += file_size
            
            if not success:
                errors += 1
                print(f"   ❌ Download failed")
                continue
            
            print(f"   ✅ Downloaded: {file_size:.2f} MB in {format_seconds(download_time)}")
        else:
            download_time = 8.0  # Simulated
            file_size = 0.15
            total_download_time += download_time
            total_file_size += file_size
        
        # PARSE
        if not dry_run and output_file.exists():
            print(f"   Parsing...")
            t0 = time.time()
            df = parse_ocean_wave_netcdf(output_file, farm)
            parse_time = time.time() - t0
            total_parse_time += parse_time
            
            if df is None or len(df) == 0:
                errors += 1
                print(f"   ❌ Parse failed")
                continue
            
            print(f"   ✅ Parsed: {len(df):,} rows in {format_seconds(parse_time)}")
            total_rows += len(df)
            
            # UPLOAD
            print(f"   Uploading to BigQuery...")
            success, upload_time = upload_to_bigquery(df, table_name)
            total_upload_time += upload_time
            
            if not success:
                errors += 1
                print(f"   ❌ Upload failed")
                continue
            
            print(f"   ✅ Uploaded: {len(df):,} rows in {format_seconds(upload_time)}")
            
            # SAVE FILE
            print(f"   Saving file...")
            t0 = time.time()
            permanent_path = storage_dir / output_file.name
            output_file.rename(permanent_path)
            write_time = time.time() - t0
            total_write_time += write_time
            files_saved += 1
            
            print(f"   💾 Saved to: {permanent_path}")
        
        # CDS RATE LIMIT
        if i < len(var_groups):
            print(f"   ⏳ Waiting {CDS_WAIT_SECONDS}s (CDS rate limit)...")
            if not dry_run:
                time.sleep(CDS_WAIT_SECONDS)
    
    total_time = total_download_time + total_parse_time + total_upload_time + total_write_time
    
    result = BenchmarkResult(
        farm_name=farm.name,
        year=year,
        month=month,
        variable_groups=len(var_groups),
        requests_made=len(var_groups),
        download_time_s=total_download_time,
        parse_time_s=total_parse_time,
        upload_time_s=total_upload_time,
        write_time_s=total_write_time,
        total_time_s=total_time,
        rows_uploaded=total_rows,
        files_saved=files_saved,
        total_file_size_mb=total_file_size,
        errors=errors,
    )
    
    print(f"\n{'='*80}")
    print(f"📊 BENCHMARK RESULTS")
    print(f"{'='*80}")
    print(f"Requests:      {result.requests_made}")
    print(f"Download time: {format_seconds(result.download_time_s)}")
    print(f"Parse time:    {format_seconds(result.parse_time_s)}")
    print(f"Upload time:   {format_seconds(result.upload_time_s)}")
    print(f"Write time:    {format_seconds(result.write_time_s)}")
    print(f"Total time:    {format_seconds(result.total_time_s)}")
    print(f"Rows uploaded: {result.rows_uploaded:,}")
    print(f"Files saved:   {result.files_saved}")
    print(f"File size:     {result.total_file_size_mb:.2f} MB")
    print(f"Errors:        {result.errors}")
    
    return result


# -------------------------
# EXTRAPOLATE & ESTIMATE
# -------------------------

def extrapolate_timeline(
    benchmark: BenchmarkResult,
    total_farms: int,
    total_months: int,
    dataset_type: str = "ocean",
) -> Dict[str, Any]:
    """
    Extrapolate full download timeline from benchmark.
    """
    var_groups = OCEAN_WAVE_GROUPS if dataset_type == "ocean" else WEATHER_GROUPS
    
    # Time per month (including rate limiting)
    requests_per_month = len(var_groups)
    time_per_month_s = benchmark.total_time_s + (CDS_WAIT_SECONDS * (requests_per_month - 1))
    
    # Time per farm (all months)
    time_per_farm_s = time_per_month_s * total_months
    time_per_farm_days = time_per_farm_s / 86400
    
    # Total time (all farms)
    total_time_s = time_per_farm_s * total_farms
    total_time_days = total_time_s / 86400
    
    # Data estimates
    rows_per_month = benchmark.rows_uploaded
    rows_per_farm = rows_per_month * total_months
    total_rows = rows_per_farm * total_farms
    
    files_per_month = benchmark.files_saved
    files_per_farm = files_per_month * total_months
    total_files = files_per_farm * total_farms
    
    size_per_month_mb = benchmark.total_file_size_mb
    size_per_farm_mb = size_per_month_mb * total_months
    total_size_mb = size_per_farm_mb * total_farms
    
    return {
        'time_per_month_s': time_per_month_s,
        'time_per_farm_days': time_per_farm_days,
        'total_time_days': total_time_days,
        'rows_per_month': rows_per_month,
        'rows_per_farm': rows_per_farm,
        'total_rows': total_rows,
        'files_per_month': files_per_month,
        'files_per_farm': files_per_farm,
        'total_files': total_files,
        'size_per_month_mb': size_per_month_mb,
        'size_per_farm_mb': size_per_farm_mb,
        'total_size_mb': total_size_mb,
        'total_size_gb': total_size_mb / 1024,
    }


def print_timeline_estimates(
    benchmark: BenchmarkResult,
    farms: List[WindFarm],
    months: List[tuple[int, int]],
    dataset_type: str = "ocean",
):
    """Print comprehensive timeline estimates."""
    est = extrapolate_timeline(
        benchmark,
        total_farms=len(farms),
        total_months=len(months),
        dataset_type=dataset_type,
    )
    
    print(f"\n{'='*80}")
    print(f"📅 TIMELINE ESTIMATES ({dataset_type.upper()} DATA)")
    print(f"{'='*80}")
    print(f"\nBased on benchmark: {benchmark.farm_name} {benchmark.year}-{benchmark.month:02d}")
    print(f"  Requests:  {benchmark.requests_made}")
    print(f"  Time:      {format_seconds(benchmark.total_time_s)}")
    print(f"  Rows:      {benchmark.rows_uploaded:,}")
    print(f"\n--- PER MONTH ---")
    print(f"  Time:      {format_seconds(est['time_per_month_s'])}")
    print(f"  Rows:      {est['rows_per_month']:,}")
    print(f"  Files:     {est['files_per_month']}")
    print(f"  Size:      {est['size_per_month_mb']:.1f} MB")
    print(f"\n--- PER FARM ({len(months)} months) ---")
    print(f"  Time:      {format_seconds(est['time_per_farm_days'] * 86400)} ({est['time_per_farm_days']:.1f} days)")
    print(f"  Rows:      {est['rows_per_farm']:,}")
    print(f"  Files:     {est['files_per_farm']}")
    print(f"  Size:      {est['size_per_farm_mb']:.1f} MB ({est['size_per_farm_mb']/1024:.2f} GB)")
    print(f"\n--- TOTAL ({len(farms)} farms × {len(months)} months) ---")
    print(f"  Time:      {format_seconds(est['total_time_days'] * 86400)} ({est['total_time_days']:.1f} days)")
    print(f"  Rows:      {est['total_rows']:,}")
    print(f"  Files:     {est['total_files']:,}")
    print(f"  Size:      {est['total_size_mb']:.1f} MB ({est['total_size_gb']:.2f} GB)")
    print(f"\n--- MILESTONES ---")
    for i in [1, 5, 10, len(farms)]:
        if i <= len(farms):
            days = est['time_per_farm_days'] * i
            pct = (i / len(farms)) * 100
            print(f"  Farm {i:2d}: Day {days:5.1f} ({pct:5.1f}% complete)")


# -------------------------
# MAIN
# -------------------------

if __name__ == "__main__":
    # Sample farms (replace with your actual farms)
    FARMS = [
        WindFarm("Hornsea One", 53.95, 1.75, 1218, "fixed"),
        WindFarm("Hornsea Two", 53.95, 1.95, 1386, "fixed"),
        WindFarm("Dogger Bank A", 55.00, 1.50, 1200, "fixed"),
        # Add more farms...
    ]
    
    # Generate month list (icing season priority)
    MONTHS = generate_month_list(priority_icing_season=True)
    
    print(f"\n{'='*80}")
    print(f"ERA5 DOWNLOAD BENCHMARK & TIMING ANALYSIS")
    print(f"{'='*80}")
    print(f"Farms:         {len(FARMS)}")
    print(f"Months:        {len(MONTHS)} ({START_YEAR}-{END_YEAR}, icing season priority)")
    print(f"Dataset types: Ocean/Wave + Weather")
    print(f"Storage:       {STORAGE_DIR_OCEAN}")
    print(f"BigQuery:      {PROJECT_ID}.{DATASET}")
    
    # BENCHMARK: Ocean/Wave
    bench_ocean = benchmark_one_month(
        farm=FARMS[0],
        year=2020,
        month=11,  # November (icing season)
        dataset_type="ocean",
        dry_run=False,  # Set True to simulate without actual download
    )
    
    # EXTRAPOLATE
    print_timeline_estimates(
        benchmark=bench_ocean,
        farms=FARMS,
        months=MONTHS,
        dataset_type="ocean",
    )
    
    # Save benchmark results
    results_file = Path("era5_benchmark_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            'benchmark': {
                'farm': bench_ocean.farm_name,
                'year': bench_ocean.year,
                'month': bench_ocean.month,
                'total_time_s': bench_ocean.total_time_s,
                'rows': bench_ocean.rows_uploaded,
                'files': bench_ocean.files_saved,
                'size_mb': bench_ocean.total_file_size_mb,
            },
            'estimates': extrapolate_timeline(bench_ocean, len(FARMS), len(MONTHS), "ocean"),
            'config': {
                'farms': len(FARMS),
                'months': len(MONTHS),
                'start_year': START_YEAR,
                'end_year': END_YEAR,
                'cds_wait_seconds': CDS_WAIT_SECONDS,
            }
        }, f, indent=2)
    
    print(f"\n✅ Benchmark results saved to: {results_file}")
    print(f"\n💡 Next steps:")
    print(f"   1. Review timing estimates above")
    print(f"   2. Adjust farm list if needed")
    print(f"   3. Run full download: python3 download_era5_ocean_waves.py")
    print(f"   4. Monitor progress: ./monitor_era5_downloads.sh")
