#!/usr/bin/env python3
"""
Cross-Correlation Analysis: Upstream Weather Signal Lead Times
================================================================

Validates documented lead times for offshore wind farm event prediction:
- Surface pressure: 6-12 hour lead time (rapid drop → storm, rise → calm)
- Temperature: 3-6 hour lead time (frontal passage detection)
- Wind direction: 1-3 hour lead time (direction shift → turbulence/calm)
- Humidity: 2-4 hour lead time (high humidity → calm periods)

Uses scipy.signal.correlate for time-lagged correlation analysis with
bootstrap confidence intervals for statistical significance.

Methodology:
-----------
1. Extract coastal station data (upstream, 50-150km west of farms)
2. Extract offshore farm event data (CALM, STORM, TURBULENCE events)
3. Calculate cross-correlation at various time lags (-24h to +24h)
4. Identify peak correlation lag (= lead time)
5. Bootstrap 1000 iterations for 95% confidence intervals
6. Statistical significance testing (p-value < 0.05)

Output:
-------
- Correlation heatmaps (farm × station × variable)
- Lead time distribution plots
- Statistical summary tables
- Updated methodology documentation

Author: George Major
Date: January 2026
Task: 11 of 16 (Wind Analysis Pipeline)
"""

import logging
import numpy as np
import pandas as pd
from scipy import signal, stats
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Tuple, Dict, List
import json

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
OUTPUT_DIR = "correlation_analysis_results"

# Analysis parameters
MAX_LAG_HOURS = 24  # Check lags from -24h to +24h
MIN_CORRELATION = 0.3  # Minimum correlation coefficient to report
BOOTSTRAP_ITERATIONS = 1000
CONFIDENCE_LEVEL = 0.95

# Coastal stations (upstream, west of offshore farms)
COASTAL_STATIONS = {
    "Blackpool": {"lat": 53.817, "lon": -3.050, "description": "Irish Sea coast"},
    "Liverpool": {"lat": 53.425, "lon": -3.000, "description": "Mersey estuary"},
    "Aberystwyth": {"lat": 52.415, "lon": -4.082, "description": "West Wales coast"},
    "Tiree": {"lat": 56.499, "lon": -6.879, "description": "Inner Hebrides"},
    "Stornoway": {"lat": 58.210, "lon": -6.391, "description": "Outer Hebrides"},
    "Malin_Head": {"lat": 55.367, "lon": -7.344, "description": "Northern Ireland"}
}

# Offshore wind farms to analyze
TARGET_FARMS = [
    "Barrow",
    "Burbo Bank Extension", 
    "Walney Extension",
    "Ormonde"
]

# Signal types to analyze
SIGNAL_TYPES = {
    "pressure": {
        "column": "surface_pressure_hpa",
        "description": "Surface pressure (hPa)",
        "expected_lead_h": (6, 12),
        "event_relation": "Rapid drop → storm, rise → calm"
    },
    "temperature": {
        "column": "temperature_2m_c",
        "description": "Temperature 2m (°C)",
        "expected_lead_h": (3, 6),
        "event_relation": "Frontal passage → temp change → events"
    },
    "wind_direction": {
        "column": "wind_direction_deg",
        "description": "Wind direction (°)",
        "expected_lead_h": (1, 3),
        "event_relation": "Direction shift → turbulence/calm"
    },
    "humidity": {
        "column": "relative_humidity_2m_pct",
        "description": "Relative humidity 2m (%)",
        "expected_lead_h": (2, 4),
        "event_relation": "High humidity → calm periods"
    }
}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('correlation_analysis.log'),
        logging.StreamHandler()
    ]
)

def get_bigquery_client():
    """Initialize BigQuery client."""
    return bigquery.Client(project=PROJECT_ID, location="US")

def get_coastal_weather_data(station_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Retrieve weather data from coastal station.
    
    Args:
        station_name: Name of coastal station
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with hourly weather data
    """
    client = get_bigquery_client()
    station = COASTAL_STATIONS[station_name]
    
    # Query coastal weather data
    # Note: Using wind_speed_10m and wind_direction_10m (not 100m for coastal stations)
    
    query = f"""
    SELECT 
        timestamp as hour,
        wind_speed_10m_ms as wind_speed_ms,
        wind_direction_10m_deg as wind_direction_deg,
        temperature_2m_c,
        relative_humidity_2m_pct,
        surface_pressure_hpa,
        wind_gusts_10m_ms
    FROM `{PROJECT_ID}.{DATASET}.coastal_weather_data`
    WHERE station_name = '{station_name}'
    AND DATE(timestamp) >= '{start_date}'
    AND DATE(timestamp) <= '{end_date}'
    ORDER BY timestamp
    """
    
    try:
        df = client.query(query).to_dataframe()
        logging.info(f"✅ Retrieved {len(df)} hours of data for {station_name}")
        return df
    except Exception as e:
        logging.warning(f"⚠️ Coastal station data not available for {station_name}: {e}")
        logging.info(f"💡 Need to download coastal station data first")
        return pd.DataFrame()

def get_offshore_farm_events(farm_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Retrieve offshore wind farm event data.
    
    Args:
        farm_name: Name of offshore wind farm
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        DataFrame with hourly event flags
    """
    client = get_bigquery_client()
    
    query = f"""
    SELECT 
        hour,
        is_calm_event,
        is_storm_event,
        is_turbulence_event,
        is_icing_event,
        has_any_event,
        actual_mw
    FROM `{PROJECT_ID}.{DATASET}.wind_unified_features`
    WHERE farm_name = '{farm_name}'
    AND DATE(hour) >= '{start_date}'
    AND DATE(hour) <= '{end_date}'
    ORDER BY hour
    """
    
    try:
        df = client.query(query).to_dataframe()
        logging.info(f"✅ Retrieved {len(df)} hours of event data for {farm_name}")
        return df
    except Exception as e:
        logging.error(f"❌ Failed to retrieve farm data for {farm_name}: {e}")
        return pd.DataFrame()

def calculate_pressure_gradient(pressure_series: pd.Series, hours: int = 3) -> pd.Series:
    """
    Calculate pressure gradient (change over N hours).
    
    Args:
        pressure_series: Pressure time series (hPa)
        hours: Time window for gradient calculation
        
    Returns:
        Pressure gradient series (hPa/h)
    """
    return pressure_series.diff(hours) / hours

def cross_correlate_signals(
    signal1: np.ndarray,
    signal2: np.ndarray,
    max_lag: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate cross-correlation between two signals at various lags.
    
    Args:
        signal1: Upstream signal (coastal station)
        signal2: Downstream signal (farm event indicator)
        max_lag: Maximum lag to test (hours)
        
    Returns:
        Tuple of (lags, correlation_coefficients)
    """
    # Normalize signals
    signal1_norm = (signal1 - np.mean(signal1)) / (np.std(signal1) + 1e-10)
    signal2_norm = (signal2 - np.mean(signal2)) / (np.std(signal2) + 1e-10)
    
    # Calculate cross-correlation
    correlation = signal.correlate(signal2_norm, signal1_norm, mode='same')
    correlation = correlation / len(signal1)
    
    # Extract relevant lags
    center = len(correlation) // 2
    lag_range = slice(center - max_lag, center + max_lag + 1)
    lags = np.arange(-max_lag, max_lag + 1)
    
    return lags, correlation[lag_range]

def bootstrap_confidence_interval(
    signal1: np.ndarray,
    signal2: np.ndarray,
    max_lag: int,
    n_iterations: int = 1000,
    confidence: float = 0.95
) -> Dict[str, np.ndarray]:
    """
    Calculate bootstrap confidence intervals for cross-correlation.
    
    Args:
        signal1: Upstream signal
        signal2: Downstream signal
        max_lag: Maximum lag to test
        n_iterations: Number of bootstrap iterations
        confidence: Confidence level (default 0.95)
        
    Returns:
        Dict with 'lags', 'mean', 'lower', 'upper' arrays
    """
    n = len(signal1)
    correlations = []
    
    for _ in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        sig1_boot = signal1[indices]
        sig2_boot = signal2[indices]
        
        # Calculate correlation
        lags, corr = cross_correlate_signals(sig1_boot, sig2_boot, max_lag)
        correlations.append(corr)
    
    correlations = np.array(correlations)
    
    # Calculate percentiles
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    return {
        'lags': lags,
        'mean': np.mean(correlations, axis=0),
        'lower': np.percentile(correlations, lower_percentile, axis=0),
        'upper': np.percentile(correlations, upper_percentile, axis=0)
    }

def find_peak_correlation_lag(lags: np.ndarray, correlations: np.ndarray) -> Tuple[int, float]:
    """
    Find lag with maximum correlation (lead time).
    
    Args:
        lags: Array of lag values (hours)
        correlations: Array of correlation coefficients
        
    Returns:
        Tuple of (peak_lag_hours, peak_correlation)
    """
    # Only consider positive lags (upstream signal leads farm event)
    positive_mask = lags > 0
    if not np.any(positive_mask):
        return 0, 0.0
    
    positive_lags = lags[positive_mask]
    positive_corrs = correlations[positive_mask]
    
    peak_idx = np.argmax(np.abs(positive_corrs))
    peak_lag = positive_lags[peak_idx]
    peak_corr = positive_corrs[peak_idx]
    
    return int(peak_lag), float(peak_corr)

def analyze_farm_station_pair(
    farm_name: str,
    station_name: str,
    signal_type: str,
    start_date: str,
    end_date: str
) -> Dict:
    """
    Analyze correlation between coastal station and offshore farm.
    
    Args:
        farm_name: Offshore wind farm name
        station_name: Coastal station name
        signal_type: 'pressure', 'temperature', 'wind_direction', or 'humidity'
        start_date: Analysis start date
        end_date: Analysis end date
        
    Returns:
        Dict with analysis results
    """
    logging.info(f"\n{'='*70}")
    logging.info(f"Analyzing: {farm_name} ← {station_name} ({signal_type})")
    logging.info(f"{'='*70}")
    
    # Get data
    coastal_data = get_coastal_weather_data(station_name, start_date, end_date)
    farm_data = get_offshore_farm_events(farm_name, start_date, end_date)
    
    if coastal_data.empty or farm_data.empty:
        logging.warning("⚠️ Insufficient data - skipping this pair")
        return None
    
    # Merge on timestamp
    merged = pd.merge(
        coastal_data,
        farm_data,
        left_on='hour',
        right_on='hour',
        how='inner'
    )
    
    if len(merged) < 100:
        logging.warning(f"⚠️ Only {len(merged)} matching hours - need more data")
        return None
    
    # Extract signals
    signal_config = SIGNAL_TYPES[signal_type]
    upstream_signal = merged[signal_config['column']].values
    
    # For pressure, use gradient (rate of change matters)
    if signal_type == 'pressure':
        upstream_signal = calculate_pressure_gradient(pd.Series(upstream_signal), hours=3).values
    
    # Downstream signal: event occurrence (binary)
    # Focus on CALM and STORM events (most predictable)
    downstream_signal = (merged['is_calm_event'] > 0) | (merged['is_storm_event'] > 0)
    downstream_signal = downstream_signal.astype(float).values
    
    # Remove NaN values
    valid_mask = ~(np.isnan(upstream_signal) | np.isnan(downstream_signal))
    upstream_signal = upstream_signal[valid_mask]
    downstream_signal = downstream_signal[valid_mask]
    
    if len(upstream_signal) < 100:
        logging.warning("⚠️ Too many NaN values after filtering")
        return None
    
    # Calculate cross-correlation
    lags, correlations = cross_correlate_signals(
        upstream_signal,
        downstream_signal,
        MAX_LAG_HOURS
    )
    
    # Find peak
    peak_lag, peak_corr = find_peak_correlation_lag(lags, correlations)
    
    # Bootstrap confidence interval
    logging.info(f"🔄 Calculating bootstrap confidence intervals ({BOOTSTRAP_ITERATIONS} iterations)...")
    ci = bootstrap_confidence_interval(
        upstream_signal,
        downstream_signal,
        MAX_LAG_HOURS,
        n_iterations=BOOTSTRAP_ITERATIONS,
        confidence=CONFIDENCE_LEVEL
    )
    
    # Statistical significance (p-value)
    # Use permutation test: shuffle downstream signal, recalculate correlation
    null_distribution = []
    for _ in range(1000):
        shuffled = np.random.permutation(downstream_signal)
        _, null_corr = cross_correlate_signals(upstream_signal, shuffled, MAX_LAG_HOURS)
        null_peak_lag, null_peak_corr = find_peak_correlation_lag(lags, null_corr)
        null_distribution.append(null_peak_corr)
    
    null_distribution = np.array(null_distribution)
    p_value = np.mean(np.abs(null_distribution) >= np.abs(peak_corr))
    
    # Expected lead time range
    expected_min, expected_max = signal_config['expected_lead_h']
    
    # Validation result
    is_validated = (
        peak_lag >= expected_min and
        peak_lag <= expected_max and
        np.abs(peak_corr) >= MIN_CORRELATION and
        p_value < 0.05
    )
    
    result = {
        'farm_name': farm_name,
        'station_name': station_name,
        'signal_type': signal_type,
        'signal_description': signal_config['description'],
        'n_observations': len(upstream_signal),
        'date_range': f"{start_date} to {end_date}",
        'peak_lag_hours': peak_lag,
        'peak_correlation': peak_corr,
        'expected_lag_min': expected_min,
        'expected_lag_max': expected_max,
        'is_validated': is_validated,
        'p_value': p_value,
        'confidence_interval_lower': float(ci['lower'][np.argmax(np.abs(correlations))]),
        'confidence_interval_upper': float(ci['upper'][np.argmax(np.abs(correlations))]),
        'lags': lags.tolist(),
        'correlations': correlations.tolist(),
        'ci_mean': ci['mean'].tolist(),
        'ci_lower': ci['lower'].tolist(),
        'ci_upper': ci['upper'].tolist()
    }
    
    # Log summary
    logging.info(f"\n📊 RESULTS:")
    logging.info(f"  Peak lag: {peak_lag} hours (expected: {expected_min}-{expected_max}h)")
    logging.info(f"  Peak correlation: {peak_corr:.3f}")
    logging.info(f"  P-value: {p_value:.4f} {'✅ Significant' if p_value < 0.05 else '❌ Not significant'}")
    logging.info(f"  95% CI: [{ci['lower'][np.argmax(np.abs(correlations))]:.3f}, {ci['upper'][np.argmax(np.abs(correlations))]:.3f}]")
    logging.info(f"  Validation: {'✅ VALIDATED' if is_validated else '❌ NOT VALIDATED'}")
    
    return result

def create_correlation_plot(result: Dict, output_path: str):
    """
    Create correlation vs lag plot with confidence intervals.
    
    Args:
        result: Analysis result dictionary
        output_path: Path to save plot
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    lags = np.array(result['lags'])
    correlations = np.array(result['correlations'])
    ci_mean = np.array(result['ci_mean'])
    ci_lower = np.array(result['ci_lower'])
    ci_upper = np.array(result['ci_upper'])
    
    # Plot correlation
    ax.plot(lags, correlations, 'b-', linewidth=2, label='Cross-correlation')
    
    # Plot confidence interval
    ax.fill_between(lags, ci_lower, ci_upper, alpha=0.3, color='blue', label='95% CI')
    
    # Mark peak
    peak_lag = result['peak_lag_hours']
    peak_corr = result['peak_correlation']
    ax.plot(peak_lag, peak_corr, 'ro', markersize=10, label=f'Peak: {peak_lag}h lag, r={peak_corr:.3f}')
    
    # Expected range
    ax.axvspan(
        result['expected_lag_min'],
        result['expected_lag_max'],
        alpha=0.2,
        color='green',
        label=f'Expected range: {result["expected_lag_min"]}-{result["expected_lag_max"]}h'
    )
    
    # Formatting
    ax.axhline(0, color='k', linestyle='--', linewidth=0.5)
    ax.axvline(0, color='k', linestyle='--', linewidth=0.5)
    ax.set_xlabel('Lag (hours, negative = coastal lags farm)', fontsize=12)
    ax.set_ylabel('Cross-correlation coefficient', fontsize=12)
    ax.set_title(
        f"{result['farm_name']} ← {result['station_name']}\n"
        f"{result['signal_description']} | n={result['n_observations']:,} hours | p={result['p_value']:.4f}",
        fontsize=14,
        fontweight='bold'
    )
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logging.info(f"📈 Saved plot: {output_path}")

def create_summary_table(results: List[Dict]) -> pd.DataFrame:
    """
    Create summary table of all analysis results.
    
    Args:
        results: List of analysis result dictionaries
        
    Returns:
        Summary DataFrame
    """
    summary_data = []
    
    for r in results:
        if r is None:
            continue
        
        summary_data.append({
            'Farm': r['farm_name'],
            'Station': r['station_name'],
            'Signal': r['signal_type'],
            'N': r['n_observations'],
            'Peak Lag (h)': r['peak_lag_hours'],
            'Expected (h)': f"{r['expected_lag_min']}-{r['expected_lag_max']}",
            'Correlation': f"{r['peak_correlation']:.3f}",
            'P-value': f"{r['p_value']:.4f}",
            'Validated': '✅' if r['is_validated'] else '❌'
        })
    
    return pd.DataFrame(summary_data)

def main():
    """Main analysis workflow."""
    import os
    
    logging.info("="*70)
    logging.info("CROSS-CORRELATION ANALYSIS: UPSTREAM WEATHER LEAD TIMES")
    logging.info("="*70)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Analysis period (use recent data for faster testing)
    start_date = "2024-01-01"
    end_date = "2024-12-31"
    
    logging.info(f"\n📅 Analysis period: {start_date} to {end_date}")
    logging.info(f"🎯 Target farms: {', '.join(TARGET_FARMS)}")
    logging.info(f"📍 Coastal stations: {', '.join(COASTAL_STATIONS.keys())}")
    logging.info(f"📊 Signal types: {', '.join(SIGNAL_TYPES.keys())}")
    
    # Check data availability
    logging.info(f"\n🔍 Checking data availability...")
    client = get_bigquery_client()
    
    # Check if coastal station data exists
    try:
        query = """
        SELECT COUNT(*) as count
        FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = 'coastal_weather_data'
        """
        result = client.query(query).to_dataframe()
        if result['count'][0] == 0:
            logging.error("❌ coastal_weather_data table does not exist")
            logging.info("\n💡 NEXT STEP: Download coastal station data first")
            return
        else:
            logging.info(f"✅ coastal_weather_data table exists")
    except Exception as e:
        logging.error(f"❌ Error checking data: {e}")
        return
    
    # Run analysis for all farm-station-signal combinations
    results = []
    
    for farm in TARGET_FARMS:
        for station in COASTAL_STATIONS.keys():
            for signal_type in SIGNAL_TYPES.keys():
                result = analyze_farm_station_pair(
                    farm,
                    station,
                    signal_type,
                    start_date,
                    end_date
                )
                
                if result:
                    results.append(result)
                    
                    # Create plot
                    plot_path = os.path.join(
                        OUTPUT_DIR,
                        f"correlation_{farm}_{station}_{signal_type}.png"
                    )
                    create_correlation_plot(result, plot_path)
    
    # Create summary table
    if results:
        summary_df = create_summary_table(results)
        summary_path = os.path.join(OUTPUT_DIR, "correlation_summary.csv")
        summary_df.to_csv(summary_path, index=False)
        
        logging.info("\n" + "="*70)
        logging.info("📊 SUMMARY TABLE")
        logging.info("="*70)
        print(summary_df.to_string(index=False))
        
        logging.info(f"\n✅ Saved summary: {summary_path}")
        
        # Save full results as JSON
        json_path = os.path.join(OUTPUT_DIR, "correlation_results_full.json")
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f"✅ Saved full results: {json_path}")
        
        # Validation statistics
        validated_count = sum(1 for r in results if r['is_validated'])
        total_count = len(results)
        validation_rate = 100 * validated_count / total_count if total_count > 0 else 0
        
        logging.info(f"\n🎯 VALIDATION SUMMARY:")
        logging.info(f"  Total analyses: {total_count}")
        logging.info(f"  Validated: {validated_count} ({validation_rate:.1f}%)")
        logging.info(f"  Not validated: {total_count - validated_count}")
        
    else:
        logging.warning("\n⚠️ No results - check data availability")
    
    logging.info("\n" + "="*70)
    logging.info("✅ ANALYSIS COMPLETE")
    logging.info("="*70)

if __name__ == "__main__":
    main()
