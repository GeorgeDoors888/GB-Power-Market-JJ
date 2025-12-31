#!/usr/bin/env python3
"""
Curtailment Impact Analysis - Identify and filter curtailment events
Purpose: Clean training datasets by removing curtailed periods
Methods: BOALF parsing, residual-based detection, time series analysis
Expected: 10-20% accuracy improvement on unconstrained forecasts
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Curtailment detection thresholds
RESIDUAL_THRESHOLD = -0.4  # Actual is 40% below expected = curtailment
MIN_DURATION_HOURS = 1  # Minimum curtailment duration
WIND_THRESHOLD_LOW = 5.0  # Only check curtailment when wind > 5 m/s
WIND_THRESHOLD_HIGH = 25.0  # Exclude extreme wind (potential turbine cutoff)


def get_wind_farms_with_bmus():
    """Get list of wind farms with their BM unit mappings."""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT
        farm_name,
        bm_unit_id,
        capacity_mw
    FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu`
    WHERE bm_unit_id IS NOT NULL
    ORDER BY farm_name, bm_unit_id
    """
    
    df = client.query(query).to_dataframe()
    
    # Group by farm
    farms = {}
    for _, row in df.iterrows():
        farm = row['farm_name']
        if farm not in farms:
            farms[farm] = {
                'bm_units': [],
                'total_capacity': 0
            }
        farms[farm]['bm_units'].append(row['bm_unit_id'])
        farms[farm]['total_capacity'] += row['capacity_mw']
    
    return farms


def get_boalf_curtailment(farm_name, bm_units, start_date, end_date):
    """
    Parse BOALF acceptances for curtailment events.
    Negative acceptance volumes indicate curtailment (reduce generation).
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    bm_units_str = "', '".join(bm_units)
    
    query = f"""
    WITH curtailment_acceptances AS (
        SELECT
            bmUnit,
            TIMESTAMP(acceptanceTime) as acceptance_time,
            acceptanceVolume,
            acceptancePrice,
            soFlag
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
        WHERE bmUnit IN ('{bm_units_str}')
          AND DATE(acceptanceTime) BETWEEN '{start_date}' AND '{end_date}'
          AND acceptanceVolume < 0  -- Negative = curtailment
          AND validation_flag = 'Valid'
    )
    SELECT
        DATE(acceptance_time) as curtailment_date,
        EXTRACT(HOUR FROM acceptance_time) as hour,
        COUNT(*) as num_acceptances,
        SUM(ABS(acceptanceVolume)) as total_mw_curtailed,
        AVG(acceptancePrice) as avg_price,
        STRING_AGG(DISTINCT soFlag, ', ') as so_flags
    FROM curtailment_acceptances
    GROUP BY curtailment_date, hour
    ORDER BY curtailment_date, hour
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f"  ⚠️  Error querying BOALF: {e}")
        return pd.DataFrame()


def get_generation_and_wind(farm_name, bm_units, start_date, end_date):
    """
    Get actual generation and wind conditions for residual-based detection.
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    bm_units_str = "', '".join(bm_units)
    
    query = f"""
    WITH generation AS (
        SELECT
            TIMESTAMP_TRUNC(TIMESTAMP(settlementDate), HOUR) as hour_utc,
            bmUnit,
            AVG(levelTo) as avg_generation_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_pn`
        WHERE bmUnit IN ('{bm_units_str}')
          AND CAST(settlementDate AS DATE) BETWEEN '{start_date}' AND '{end_date}'
          AND levelTo > 0
        GROUP BY hour_utc, bmUnit
    ),
    
    wind AS (
        SELECT
            TIMESTAMP_TRUNC(time_utc, HOUR) as hour_utc,
            AVG(wind_speed_100m) as avg_wind_speed,
            AVG(wind_gusts_10m) as avg_wind_gusts
        FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
        WHERE farm_name = '{farm_name}'
          AND DATE(time_utc) BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY hour_utc
    )
    
    SELECT
        g.hour_utc,
        g.bmUnit,
        g.avg_generation_mw,
        w.avg_wind_speed,
        w.avg_wind_gusts
    FROM generation g
    LEFT JOIN wind w ON g.hour_utc = w.hour_utc
    WHERE w.avg_wind_speed IS NOT NULL
    ORDER BY g.hour_utc, g.bmUnit
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f"  ⚠️  Error querying generation/wind: {e}")
        return pd.DataFrame()


def calculate_power_curve_expected(wind_speed, rated_capacity_mw):
    """
    Simple power curve model for expected generation.
    Cut-in: 4 m/s, Rated: 12 m/s, Cut-out: 25 m/s
    """
    if wind_speed < 4.0:
        return 0.0
    elif wind_speed > 25.0:
        return 0.0
    elif wind_speed >= 12.0:
        return rated_capacity_mw
    else:
        # Cubic relationship between cut-in and rated
        normalized = (wind_speed - 4.0) / (12.0 - 4.0)
        return rated_capacity_mw * (normalized ** 3)


def detect_residual_curtailment(df, capacity_mw):
    """
    Residual-based curtailment detection.
    If actual << expected (based on wind), likely curtailment.
    """
    # Calculate expected generation from power curve
    df['expected_mw'] = df['avg_wind_speed'].apply(
        lambda ws: calculate_power_curve_expected(ws, capacity_mw)
    )
    
    # Calculate residual
    df['residual'] = (df['avg_generation_mw'] - df['expected_mw']) / (df['expected_mw'] + 1e-6)
    
    # Flag curtailment
    curtailment_mask = (
        (df['residual'] < RESIDUAL_THRESHOLD) &  # Actual much lower than expected
        (df['avg_wind_speed'] > WIND_THRESHOLD_LOW) &  # Good wind conditions
        (df['avg_wind_speed'] < WIND_THRESHOLD_HIGH)  # Not extreme wind
    )
    
    df['is_curtailed'] = curtailment_mask.astype(int)
    
    return df


def identify_curtailment_events(df):
    """
    Group consecutive curtailed hours into events.
    """
    if df.empty or 'is_curtailed' not in df:
        return []
    
    df = df.sort_values('hour_utc')
    
    events = []
    current_event = None
    
    for _, row in df.iterrows():
        if row['is_curtailed'] == 1:
            if current_event is None:
                # Start new event
                current_event = {
                    'start_time': row['hour_utc'],
                    'end_time': row['hour_utc'],
                    'hours': 1,
                    'avg_wind': row['avg_wind_speed'],
                    'avg_generation': row['avg_generation_mw'],
                    'avg_expected': row['expected_mw'],
                    'total_mw_lost': row['expected_mw'] - row['avg_generation_mw']
                }
            else:
                # Continue event
                current_event['end_time'] = row['hour_utc']
                current_event['hours'] += 1
                current_event['total_mw_lost'] += (row['expected_mw'] - row['avg_generation_mw'])
        else:
            if current_event is not None:
                # Event ended
                if current_event['hours'] >= MIN_DURATION_HOURS:
                    events.append(current_event)
                current_event = None
    
    # Add final event if still active
    if current_event is not None and current_event['hours'] >= MIN_DURATION_HOURS:
        events.append(current_event)
    
    return events


def analyze_farm(farm_name, farm_info, start_date, end_date):
    """
    Complete curtailment analysis for one farm.
    """
    print(f"\n{'='*80}")
    print(f"Farm: {farm_name}")
    print(f"{'='*80}")
    print(f"BM Units: {', '.join(farm_info['bm_units'])}")
    print(f"Capacity: {farm_info['total_capacity']:.0f} MW")
    print()
    
    # Method 1: BOALF curtailment acceptances
    print("Method 1: BOALF Acceptances (negative volumes)")
    boalf_df = get_boalf_curtailment(farm_name, farm_info['bm_units'], start_date, end_date)
    
    if not boalf_df.empty:
        total_hours = len(boalf_df)
        total_mw = boalf_df['total_mw_curtailed'].sum()
        print(f"  ✅ Found {total_hours} curtailed hours")
        print(f"  📉 Total curtailed: {total_mw:.0f} MW·h")
        print(f"  💰 Avg price: £{boalf_df['avg_price'].mean():.2f}/MWh")
    else:
        print(f"  ⚪ No BOALF curtailment found")
    
    # Method 2: Residual-based detection
    print("\nMethod 2: Residual-Based Detection")
    gen_wind_df = get_generation_and_wind(farm_name, farm_info['bm_units'], start_date, end_date)
    
    if gen_wind_df.empty:
        print(f"  ⚠️  No generation/wind data available")
        return None
    
    # Aggregate by hour (multiple BM units per farm)
    hourly_df = gen_wind_df.groupby('hour_utc').agg({
        'avg_generation_mw': 'sum',
        'avg_wind_speed': 'mean',
        'avg_wind_gusts': 'mean'
    }).reset_index()
    
    # Detect curtailment
    hourly_df = detect_residual_curtailment(hourly_df, farm_info['total_capacity'])
    
    curtailed_hours = hourly_df['is_curtailed'].sum()
    total_hours = len(hourly_df)
    curtailment_pct = (curtailed_hours / total_hours) * 100 if total_hours > 0 else 0
    
    print(f"  ✅ Analyzed {total_hours:,} hours")
    print(f"  📉 Curtailed: {curtailed_hours:,} hours ({curtailment_pct:.1f}%)")
    
    # Identify events
    events = identify_curtailment_events(hourly_df)
    
    print(f"\nCurtailment Events: {len(events)}")
    if events:
        total_mw_lost = sum(e['total_mw_lost'] for e in events)
        avg_duration = np.mean([e['hours'] for e in events])
        
        print(f"  Duration: {avg_duration:.1f} hours avg")
        print(f"  Energy lost: {total_mw_lost:.0f} MW·h")
        print(f"  Revenue loss (£50/MWh): £{total_mw_lost * 50:,.0f}")
        
        # Print top 5 events
        events_sorted = sorted(events, key=lambda e: e['total_mw_lost'], reverse=True)
        print(f"\n  Top 5 Events:")
        for i, event in enumerate(events_sorted[:5], 1):
            print(f"    {i}. {event['start_time']:%Y-%m-%d %H:%M} ({event['hours']}h)")
            print(f"       Wind: {event['avg_wind']:.1f} m/s")
            print(f"       Lost: {event['total_mw_lost']:.0f} MW·h")
    
    return {
        'farm_name': farm_name,
        'capacity_mw': farm_info['total_capacity'],
        'total_hours': total_hours,
        'curtailed_hours': curtailed_hours,
        'curtailment_pct': curtailment_pct,
        'num_events': len(events),
        'total_mw_lost': sum(e['total_mw_lost'] for e in events) if events else 0,
        'boalf_hours': len(boalf_df) if not boalf_df.empty else 0,
    }


def save_results(results):
    """Save curtailment analysis results to CSV."""
    if not results:
        print("\n⚠️  No results to save")
        return
    
    df = pd.DataFrame(results)
    output_file = 'curtailment_analysis_results.csv'
    df.to_csv(output_file, index=False)
    
    print(f"\n{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}")
    
    # Summary statistics
    print("\nSummary Statistics:")
    print(f"  Farms analyzed: {len(df)}")
    print(f"  Avg curtailment: {df['curtailment_pct'].mean():.1f}%")
    print(f"  Total MW·h lost: {df['total_mw_lost'].sum():,.0f}")
    print(f"  Total events: {df['num_events'].sum():,}")


def main():
    """Main curtailment analysis pipeline."""
    print("="*80)
    print("Curtailment Impact Analysis")
    print("="*80)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Analysis period (last 6 months for testing)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)
    
    print(f"Analysis period: {start_date} to {end_date}")
    print()
    
    # Get wind farms
    farms = get_wind_farms_with_bmus()
    print(f"Wind farms with BM units: {len(farms)}")
    print()
    
    # Analyze first 5 farms (testing)
    results = []
    
    for i, (farm_name, farm_info) in enumerate(list(farms.items())[:5], 1):
        print(f"\n[{i}/{min(5, len(farms))}]")
        result = analyze_farm(farm_name, farm_info, start_date, end_date)
        if result:
            results.append(result)
    
    # Save results
    save_results(results)
    
    print("\n" + "="*80)
    print("✅ Curtailment Analysis Complete")
    print("="*80)
    print("\nNext Steps:")
    print("1. Review curtailment_analysis_results.csv")
    print("2. Upload curtailment events to BigQuery table")
    print("3. Filter training data: Exclude curtailed hours")
    print("4. Retrain models with clean dataset")
    print("5. Expected: 10-20% accuracy improvement")
    print("="*80)


if __name__ == "__main__":
    main()
