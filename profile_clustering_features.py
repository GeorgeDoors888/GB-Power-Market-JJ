#!/usr/bin/env python3
"""
HH Profile Clustering Features & TOU Flexibility Modeling
Extract features from half-hourly load profiles for clustering and flexibility analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ProfileFeatures:
    """Feature vector extracted from HH load profile for clustering"""
    site_id: str
    
    # Load shape features
    peak_ratio: float          # max/mean (spikiness)
    load_factor: float         # mean/max (flatness, 0-1)
    peak_kw: float            # Maximum demand
    mean_kw: float            # Average demand
    
    # Temporal patterns
    weekend_factor: float      # weekend_mean / weekday_mean
    day_night_ratio: float     # day_mean / night_mean
    evening_peak_factor: float # 16-19 mean / daily mean
    
    # Seasonality (if multi-month data)
    monthly_cv: float          # Coefficient of variation of monthly means
    
    # Profile class indicators
    is_weekday_dominant: bool  # weekend_factor < 0.5
    is_peaky: bool            # peak_ratio > 2.0
    is_baseload: bool         # load_factor > 0.7
    
    def to_dict(self) -> Dict:
        """Convert to dict for clustering"""
        return {
            "site_id": self.site_id,
            "peak_ratio": self.peak_ratio,
            "load_factor": self.load_factor,
            "peak_kw": self.peak_kw,
            "mean_kw": self.mean_kw,
            "weekend_factor": self.weekend_factor,
            "day_night_ratio": self.day_night_ratio,
            "evening_peak_factor": self.evening_peak_factor,
            "monthly_cv": self.monthly_cv,
            "is_weekday_dominant": int(self.is_weekday_dominant),
            "is_peaky": int(self.is_peaky),
            "is_baseload": int(self.is_baseload)
        }
    
    def __str__(self) -> str:
        return (
            f"Profile: {self.site_id}\n"
            f"  Peak: {self.peak_kw:.1f} kW, Mean: {self.mean_kw:.1f} kW\n"
            f"  Peak Ratio: {self.peak_ratio:.2f}, Load Factor: {self.load_factor:.2f}\n"
            f"  Weekend Factor: {self.weekend_factor:.2f}, Day/Night: {self.day_night_ratio:.2f}\n"
            f"  Type: {'Weekday' if self.is_weekday_dominant else 'Continuous'}, "
            f"{'Peaky' if self.is_peaky else 'Flat'}, "
            f"{'Baseload' if self.is_baseload else 'Variable'}"
        )


def extract_profile_features(df_hh: pd.DataFrame, site_id: str = "site") -> ProfileFeatures:
    """
    Extract clustering features from half-hourly load profile
    
    Args:
        df_hh: DataFrame with timestamp and kw columns
        site_id: Identifier for this site
    
    Returns:
        ProfileFeatures object
    """
    df = df_hh.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Basic stats
    peak_kw = df["kw"].max()
    mean_kw = df["kw"].mean()
    
    # Peak ratio and load factor
    peak_ratio = peak_kw / mean_kw if mean_kw > 0 else 0
    load_factor = mean_kw / peak_kw if peak_kw > 0 else 0
    
    # Add temporal features
    df["hour"] = df["timestamp"].dt.hour
    df["is_weekend"] = df["timestamp"].dt.weekday >= 5
    df["month"] = df["timestamp"].dt.month
    
    # Weekend factor
    weekday_mean = df[~df["is_weekend"]]["kw"].mean()
    weekend_mean = df[df["is_weekend"]]["kw"].mean()
    weekend_factor = weekend_mean / weekday_mean if weekday_mean > 0 else 1.0
    
    # Day/night ratio (day = 07:00-19:00)
    day_mask = (df["hour"] >= 7) & (df["hour"] < 19)
    night_mask = ~day_mask
    day_mean = df[day_mask]["kw"].mean()
    night_mean = df[night_mask]["kw"].mean()
    day_night_ratio = day_mean / night_mean if night_mean > 0 else 1.0
    
    # Evening peak factor (16:00-19:00)
    evening_mask = (df["hour"] >= 16) & (df["hour"] < 19)
    evening_mean = df[evening_mask]["kw"].mean()
    evening_peak_factor = evening_mean / mean_kw if mean_kw > 0 else 1.0
    
    # Monthly coefficient of variation (if enough data)
    if "month" in df.columns and df["month"].nunique() > 1:
        monthly_means = df.groupby("month")["kw"].mean()
        monthly_cv = monthly_means.std() / monthly_means.mean() if monthly_means.mean() > 0 else 0
    else:
        monthly_cv = 0.0
    
    # Profile class indicators
    is_weekday_dominant = weekend_factor < 0.5
    is_peaky = peak_ratio > 2.0
    is_baseload = load_factor > 0.7
    
    return ProfileFeatures(
        site_id=site_id,
        peak_ratio=peak_ratio,
        load_factor=load_factor,
        peak_kw=peak_kw,
        mean_kw=mean_kw,
        weekend_factor=weekend_factor,
        day_night_ratio=day_night_ratio,
        evening_peak_factor=evening_peak_factor,
        monthly_cv=monthly_cv,
        is_weekday_dominant=is_weekday_dominant,
        is_peaky=is_peaky,
        is_baseload=is_baseload
    )


def calculate_flexibility_value(
    df_hh: pd.DataFrame,
    flex_fraction: float,
    prices_hh: pd.Series,
    red_periods: Optional[pd.Series] = None,
    shift_energy: bool = True
) -> Dict:
    """
    Calculate value of demand flexibility (reduction or shifting)
    
    Args:
        df_hh: DataFrame with timestamp, kw columns
        flex_fraction: Fraction of load that can be shifted/reduced (0-1)
        prices_hh: Series of prices per HH (£/kWh) aligned with df_hh
        red_periods: Optional boolean series indicating expensive periods
        shift_energy: If True, shift energy to cheaper periods; if False, just reduce
    
    Returns:
        Dict with flexibility value metrics
    """
    df = df_hh.copy()
    df["price"] = prices_hh.values
    
    # If red_periods not provided, use top 10% price periods
    if red_periods is None:
        price_threshold = df["price"].quantile(0.9)
        red_periods = df["price"] >= price_threshold
    
    df["is_red"] = red_periods.values
    df["is_green"] = ~df["is_red"]
    
    # Baseline cost
    df["baseline_cost"] = df["kw"] * df["price"] * 0.5  # 0.5h = HH
    baseline_cost_total = df["baseline_cost"].sum()
    
    # Calculate flexibility
    df["flex_kw"] = 0.0
    
    # Reduce/remove load during expensive periods
    red_mask = df["is_red"]
    df.loc[red_mask, "flex_kw"] = -df.loc[red_mask, "kw"] * flex_fraction
    
    if shift_energy:
        # Shift energy to cheaper periods
        total_shifted_kwh = (-df.loc[red_mask, "flex_kw"] * 0.5).sum()  # Total energy to shift
        
        # Allocate to green periods in proportion to "headroom" (space below peak)
        green_mask = df["is_green"]
        green_headroom = (df["kw"].max() - df.loc[green_mask, "kw"]).clip(lower=0)
        total_headroom_kw = green_headroom.sum()
        
        if total_headroom_kw > 0:
            # Distribute shifted energy proportionally to headroom
            allocation_fraction = green_headroom / total_headroom_kw
            allocated_kwh = total_shifted_kwh * allocation_fraction
            df.loc[green_mask, "flex_kw"] = allocated_kwh / 0.5  # Convert kWh to kW
    
    # New load profile
    df["new_kw"] = (df["kw"] + df["flex_kw"]).clip(lower=0)
    df["new_cost"] = df["new_kw"] * df["price"] * 0.5
    
    new_cost_total = df["new_cost"].sum()
    value_gbp = baseline_cost_total - new_cost_total
    
    # Energy shifted/reduced
    energy_reduced_red = (-df.loc[red_mask, "flex_kw"] * 0.5).sum()
    energy_added_green = (df.loc[green_mask, "flex_kw"] * 0.5).sum() if shift_energy else 0
    
    return {
        "baseline_cost_gbp": baseline_cost_total,
        "flexible_cost_gbp": new_cost_total,
        "value_gbp": value_gbp,
        "value_percent": (value_gbp / baseline_cost_total * 100) if baseline_cost_total > 0 else 0,
        
        "energy_reduced_red_kwh": energy_reduced_red,
        "energy_added_green_kwh": energy_added_green,
        "energy_conserved": shift_energy,
        
        "red_periods_count": red_mask.sum(),
        "green_periods_count": green_mask.sum(),
        
        "avg_red_price": df.loc[red_mask, "price"].mean(),
        "avg_green_price": df.loc[green_mask, "price"].mean(),
    }


def create_features_dataframe(profiles_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Extract features from multiple sites for clustering
    
    Args:
        profiles_dict: Dict of {site_id: df_hh}
    
    Returns:
        DataFrame with features for all sites (one row per site)
    """
    features_list = []
    
    for site_id, df_hh in profiles_dict.items():
        features = extract_profile_features(df_hh, site_id=site_id)
        features_list.append(features.to_dict())
    
    return pd.DataFrame(features_list)


# ==================== DEMO ====================

def demo_clustering_features():
    """Demo feature extraction and flexibility calculation"""
    print("=" * 80)
    print("HH Profile Features & Flexibility Demo")
    print("=" * 80)
    
    # Create 3 synthetic profiles with different characteristics
    dates = pd.date_range("2025-01-01", periods=7*48, freq="30min")
    
    # Profile 1: Weekday business (peaky, weekday-dominant)
    np.random.seed(42)
    df1 = pd.DataFrame({
        "timestamp": dates,
        "kw": [
            (100 + 80 * np.sin((ts.hour - 12) * np.pi / 12) * (0.3 if ts.weekday() >= 5 else 1.0) +
             np.random.normal(0, 10))
            for ts in dates
        ]
    })
    df1["kw"] = df1["kw"].clip(lower=20)
    
    # Profile 2: Baseload industrial (flat, continuous)
    df2 = pd.DataFrame({
        "timestamp": dates,
        "kw": [200 + np.random.normal(0, 15) for _ in dates]
    })
    df2["kw"] = df2["kw"].clip(lower=150)
    
    # Profile 3: Residential block (evening peak, lower weekend)
    df3 = pd.DataFrame({
        "timestamp": dates,
        "kw": [
            (50 + 40 * (1 if 7 <= ts.hour < 9 or 17 <= ts.hour < 22 else 0.3) *
             (0.7 if ts.weekday() >= 5 else 1.0) + np.random.normal(0, 5))
            for ts in dates
        ]
    })
    df3["kw"] = df3["kw"].clip(lower=15)
    
    # Extract features
    print("\n📊 Profile Features:")
    for name, df in [("Office Building", df1), ("Factory", df2), ("Apartments", df3)]:
        features = extract_profile_features(df, site_id=name)
        print(f"\n{features}")
    
    # Create features dataframe
    profiles = {"Office": df1, "Factory": df2, "Apartments": df3}
    features_df = create_features_dataframe(profiles)
    print(f"\n📋 Features DataFrame for Clustering:")
    print(features_df[["site_id", "peak_ratio", "load_factor", "weekend_factor", "day_night_ratio"]].to_string(index=False))
    
    # Flexibility calculation
    print(f"\n💡 Flexibility Value Analysis (Office Building):")
    
    # Synthetic TOU prices (higher 16-19, lower nights/weekends)
    prices = pd.Series([
        (0.15 if 16 <= ts.hour < 19 and ts.weekday() < 5 else
         0.08 if 7 <= ts.hour < 23 else
         0.05)
        for ts in df1["timestamp"]
    ])
    
    # Calculate value of 30% flexibility
    flex_value = calculate_flexibility_value(
        df1,
        flex_fraction=0.30,
        prices_hh=prices,
        shift_energy=True
    )
    
    print(f"   Flexibility: 30% of load can be shifted")
    print(f"   Baseline Cost: £{flex_value['baseline_cost_gbp']:.2f}")
    print(f"   Flexible Cost: £{flex_value['flexible_cost_gbp']:.2f}")
    print(f"   Value: £{flex_value['value_gbp']:.2f} ({flex_value['value_percent']:.1f}% saving)")
    print(f"   Energy shifted: {flex_value['energy_reduced_red_kwh']:.1f} kWh from red to green")
    print(f"   Avg red price: £{flex_value['avg_red_price']:.3f}/kWh")
    print(f"   Avg green price: £{flex_value['avg_green_price']:.3f}/kWh")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_clustering_features()
