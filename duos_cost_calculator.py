#!/usr/bin/env python3
"""
DUoS Cost Calculator for Half-Hourly (HH) Profiles
Calculates Distribution Use of System charges based on time-of-use tariffs
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional


@dataclass
class DuosTariff:
    """
    DUoS tariff structure for a specific DNO, voltage level, and year
    
    All unit rates in £/kWh
    fixed_p_per_day in pence/day
    capacity_p_per_kva_per_day in pence/kVA/day
    """
    dno_id: str
    tariff_name: str
    voltage_level: str  # LV, HV, EHV
    
    # Time-of-use unit rates (£/kWh)
    red_rate: float
    amber_rate: float
    green_rate: float
    
    # Fixed charges
    fixed_p_per_day: float = 0.0
    capacity_p_per_kva_per_day: float = 0.0
    
    # Reactive power charge (£/kVArh) - optional
    reactive_rate: float = 0.0
    
    def __str__(self):
        return (f"{self.dno_id} {self.tariff_name} ({self.voltage_level})\n"
                f"  Red: £{self.red_rate:.4f}/kWh, Amber: £{self.amber_rate:.4f}/kWh, "
                f"Green: £{self.green_rate:.4f}/kWh")


def duos_band_for_hh(
    ts: pd.Timestamp,
    red_windows: Tuple[Tuple[float, float], ...] = ((16, 19.5),),
    amber_windows: Tuple[Tuple[float, float], ...] = ((8, 16), (19.5, 22)),
    weekend_is_green: bool = True
) -> str:
    """
    Assign DUoS time-of-use band to a half-hourly timestamp
    
    Args:
        ts: Timestamp for the half-hour period
        red_windows: Tuple of (start_hour, end_hour) for red periods
        amber_windows: Tuple of (start_hour, end_hour) for amber periods
        weekend_is_green: If True, all weekend periods are green
    
    Returns:
        Band name: 'red', 'amber', or 'green'
    
    Example red_windows for typical DNO:
        ((16, 19.5),)  # 16:00-19:30 weekdays (peak evening demand)
    """
    # Convert to decimal hour (16:30 = 16.5)
    hour = ts.hour + ts.minute / 60.0
    is_weekend = ts.weekday() >= 5  # Saturday=5, Sunday=6
    
    # Weekend check
    if weekend_is_green and is_weekend:
        return "green"
    
    # Check red periods first (highest priority)
    for h0, h1 in red_windows:
        if h0 <= hour < h1:
            return "red"
    
    # Check amber periods
    for h0, h1 in amber_windows:
        if h0 <= hour < h1:
            return "amber"
    
    # Default to green
    return "green"


def calculate_duos_costs(
    df_hh: pd.DataFrame,
    tariff: DuosTariff,
    kva_capacity: float = 0.0,
    red_windows: Tuple[Tuple[float, float], ...] = ((16, 19.5),),
    amber_windows: Tuple[Tuple[float, float], ...] = ((8, 16), (19.5, 22)),
    kvarh_column: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate DUoS costs for half-hourly consumption data
    
    Args:
        df_hh: DataFrame with columns: timestamp, kwh (and optionally site_id)
        tariff: DuosTariff object with rates and charges
        kva_capacity: Agreed supply capacity in kVA (for capacity charges)
        red_windows: Red band time windows
        amber_windows: Amber band time windows
        kvarh_column: Optional column name for reactive power (kVArh)
    
    Returns:
        DataFrame with additional columns:
            - band: TOU band (red/amber/green)
            - unit_rate: £/kWh rate for this period
            - duos_unit_cost: Energy charge (£)
            - duos_fixed_cap_cost: Daily fixed + capacity charge (£/HH)
            - duos_reactive_cost: Reactive power charge (£) if applicable
            - duos_total_cost: Total DUoS cost (£)
    """
    df = df_hh.copy()
    
    # Validate required columns
    if "timestamp" not in df.columns or "kwh" not in df.columns:
        raise ValueError("df_hh must contain 'timestamp' and 'kwh' columns")
    
    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    
    # Assign TOU bands to each half-hour
    df["band"] = df["timestamp"].apply(
        lambda t: duos_band_for_hh(t, red_windows, amber_windows)
    )
    
    # Map band to unit rate
    rate_map = {
        "red": tariff.red_rate,
        "amber": tariff.amber_rate,
        "green": tariff.green_rate
    }
    df["unit_rate"] = df["band"].map(rate_map)
    
    # Calculate unit cost (energy charge)
    df["duos_unit_cost"] = df["kwh"] * df["unit_rate"]
    
    # Daily fixed + capacity charges (allocated evenly across 48 HH periods)
    daily_fixed_gbp = tariff.fixed_p_per_day / 100.0
    daily_capacity_gbp = (tariff.capacity_p_per_kva_per_day * kva_capacity) / 100.0
    daily_total_gbp = daily_fixed_gbp + daily_capacity_gbp
    
    # Allocate daily charges: each HH gets 1/48th of daily charge
    df["duos_fixed_cap_cost"] = daily_total_gbp / 48.0
    
    # Reactive power charges (if applicable)
    if kvarh_column and kvarh_column in df.columns and tariff.reactive_rate > 0:
        df["duos_reactive_cost"] = df[kvarh_column] * tariff.reactive_rate
    else:
        df["duos_reactive_cost"] = 0.0
    
    # Total DUoS cost per HH period
    df["duos_total_cost"] = (
        df["duos_unit_cost"] +
        df["duos_fixed_cap_cost"] +
        df["duos_reactive_cost"]
    )
    
    return df


def summarize_duos_costs(df_with_costs: pd.DataFrame) -> Dict:
    """
    Summarize DUoS costs by band and component
    
    Args:
        df_with_costs: DataFrame output from calculate_duos_costs()
    
    Returns:
        Dict with summary statistics
    """
    summary = {
        "total_cost_gbp": df_with_costs["duos_total_cost"].sum(),
        "unit_cost_gbp": df_with_costs["duos_unit_cost"].sum(),
        "fixed_cap_cost_gbp": df_with_costs["duos_fixed_cap_cost"].sum(),
        "reactive_cost_gbp": df_with_costs["duos_reactive_cost"].sum(),
        
        "total_kwh": df_with_costs["kwh"].sum(),
        "avg_rate_p_per_kwh": (df_with_costs["duos_unit_cost"].sum() / df_with_costs["kwh"].sum()) * 100 if df_with_costs["kwh"].sum() > 0 else 0,
        
        "by_band": {}
    }
    
    # Breakdown by TOU band
    for band in ["red", "amber", "green"]:
        band_df = df_with_costs[df_with_costs["band"] == band]
        if not band_df.empty:
            summary["by_band"][band] = {
                "kwh": band_df["kwh"].sum(),
                "cost_gbp": band_df["duos_unit_cost"].sum(),
                "periods": len(band_df)
            }
    
    return summary


# ==================== EXAMPLE TARIFFS ====================

# Example: UKPN Eastern (EPN) HV tariff 2025/26
UKPN_EPN_HV_2025 = DuosTariff(
    dno_id="10",
    tariff_name="HV Non-Domestic Banded",
    voltage_level="HV",
    red_rate=0.04837,      # £/kWh (48.37p/kWh)
    amber_rate=0.00457,    # £/kWh (4.57p/kWh)
    green_rate=0.00038,    # £/kWh (0.38p/kWh)
    fixed_p_per_day=120.0, # 120p/day
    capacity_p_per_kva_per_day=5.0  # 5p/kVA/day
)

# Example: ENWL LV tariff 2025/26
ENWL_LV_2025 = DuosTariff(
    dno_id="16",
    tariff_name="LV Non-Domestic Banded",
    voltage_level="LV",
    red_rate=0.0180,
    amber_rate=0.0095,
    green_rate=0.0042,
    fixed_p_per_day=45.0,
    capacity_p_per_kva_per_day=0.0  # No capacity charge for LV
)


# ==================== DEMO ====================

def demo_duos_calculation():
    """Demo DUoS cost calculation with synthetic profile"""
    print("=" * 80)
    print("DUoS Cost Calculator Demo")
    print("=" * 80)
    
    # Create synthetic HH profile for 1 week
    dates = pd.date_range("2025-01-01", periods=7*48, freq="30min")
    
    # Synthetic load pattern: weekday peak, weekend lower
    np.random.seed(42)
    base_load = 100  # kW
    df = pd.DataFrame({
        "timestamp": dates,
        "kwh": [
            (base_load + 50 * np.sin((ts.hour - 12) * np.pi / 12) +
             np.random.normal(0, 10) -
             (30 if ts.weekday() >= 5 else 0)) * 0.5  # HH energy in kWh
            for ts in dates
        ]
    })
    df["kwh"] = df["kwh"].clip(lower=10)  # Minimum 10 kWh
    
    # Apply DUoS tariff
    print(f"\n📋 Tariff: {UKPN_EPN_HV_2025}")
    print(f"   Capacity: 500 kVA")
    
    df_costs = calculate_duos_costs(
        df,
        tariff=UKPN_EPN_HV_2025,
        kva_capacity=500.0
    )
    
    # Summarize
    summary = summarize_duos_costs(df_costs)
    
    print(f"\n💰 DUoS Cost Summary (1 week):")
    print(f"   Total Cost: £{summary['total_cost_gbp']:.2f}")
    print(f"   Unit Cost: £{summary['unit_cost_gbp']:.2f}")
    print(f"   Fixed/Capacity: £{summary['fixed_cap_cost_gbp']:.2f}")
    print(f"   Total Energy: {summary['total_kwh']:.0f} kWh")
    print(f"   Average Rate: {summary['avg_rate_p_per_kwh']:.2f} p/kWh")
    
    print(f"\n📊 Breakdown by TOU Band:")
    for band, data in summary["by_band"].items():
        print(f"   {band.capitalize():6s}: {data['kwh']:8.0f} kWh "
              f"({data['periods']:3d} HH) = £{data['cost_gbp']:7.2f}")
    
    # Show sample periods
    print(f"\n📅 Sample Half-Hour Periods:")
    print(df_costs[["timestamp", "band", "kwh", "unit_rate", "duos_total_cost"]].head(10).to_string(index=False))
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_duos_calculation()
