#!/usr/bin/env python3
"""
GB Power Market - Optimised BESS Engine

Forward-looking battery optimization with 48-period (24-hour) horizon.
Replaces myopic decision-making with true profit-maximizing dispatch.

Key Features:
- Look-ahead optimization (not just current period)
- Charge decision: η * max(future_R) > cost_now
- Discharge decision: R_now > min(future_cost)
- Respects SoC constraints
- Efficiency losses accounted for
"""

import pandas as pd
import numpy as np
from typing import Tuple

# ====================================================
# CONFIGURATION
# ====================================================

HORIZON = 48  # 48 settlement periods = 24 hours look-ahead
EFFICIENCY = 0.85  # 85% round-trip efficiency
BATTERY_POWER_MW = 2.5
BATTERY_ENERGY_MWH = 5.0
SOC_MIN = 0.05 * BATTERY_ENERGY_MWH  # 5% minimum
SOC_MAX = BATTERY_ENERGY_MWH  # 100% maximum


# ====================================================
# OPTIMIZATION CORE
# ====================================================

def optimize_bess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply forward-looking optimization to battery dispatch decisions.
    
    Args:
        df: DataFrame with columns:
            - ssp_charge: System buy price
            - duos_charge: DUoS charge
            - levies_per_mwh: Fixed levies
            - ppa_price: PPA discharge price
            - bm_revenue_per_mwh: BM/VLP revenue
            - dc_revenue_per_mwh: Dynamic Containment
            - cm_revenue_per_mwh: Capacity Market
            - other_revenue_per_mwh: Other revenues
    
    Returns:
        DataFrame with additional columns:
            - cost_now: Total cost per MWh
            - r_now: Total revenue per MWh
            - future_max_r: Max revenue in look-ahead window
            - future_min_c: Min cost in look-ahead window
            - charge_signal: Boolean - should charge?
            - discharge_signal: Boolean - should discharge?
    """
    df = df.copy()

    # ================================================
    # 1. Compute total cost and revenue per MWh
    # ================================================
    
    df["cost_now"] = (
        df["ssp_charge"] + 
        df["duos_charge"] + 
        df["levies_per_mwh"]
    )
    
    df["r_now"] = (
        df["ppa_price"] +
        df["bm_revenue_per_mwh"] +
        df["dc_revenue_per_mwh"] +
        df["cm_revenue_per_mwh"] +
        df["other_revenue_per_mwh"]
    )

    # ================================================
    # 2. Look-ahead windows (rolling max/min)
    # ================================================
    
    # Future maximum revenue in next HORIZON periods
    df["future_max_r"] = (
        df["r_now"]
        .rolling(window=HORIZON, min_periods=1)
        .max()
        .shift(-HORIZON)  # Look forward
    )

    # Future minimum cost in next HORIZON periods
    df["future_min_c"] = (
        df["cost_now"]
        .rolling(window=HORIZON, min_periods=1)
        .min()
        .shift(-HORIZON)  # Look forward
    )

    # If horizon shifts beyond data, fill with last known values
    df["future_max_r"].fillna(df["r_now"].max(), inplace=True)
    df["future_min_c"].fillna(df["cost_now"].min(), inplace=True)

    # ================================================
    # 3. Charge / discharge decision signals
    # ================================================
    
    # Charge if: η * max(future_R) > cost_now
    # (i.e., even after efficiency losses, future discharge is worth more than charging cost)
    df["charge_signal"] = (EFFICIENCY * df["future_max_r"]) > df["cost_now"]
    
    # Discharge if: R_now > min(future_cost)
    # (i.e., revenue now exceeds best future charging opportunity)
    df["discharge_signal"] = df["r_now"] > df["future_min_c"]
    
    # Additional profitability checks
    df["charge_profitable"] = df["cost_now"] < 120  # Threshold for profitable charging
    df["discharge_profitable"] = df["r_now"] > df["cost_now"]  # Immediate arbitrage opportunity
    
    # Final signals combine optimization with profitability
    df["charge_signal"] = df["charge_signal"] & df["charge_profitable"]
    df["discharge_signal"] = df["discharge_signal"] & df["discharge_profitable"]

    return df


# ====================================================
# SoC SIMULATION WITH OPTIMISED DECISIONS
# ====================================================

def simulate_soc_optimized(df: pd.DataFrame, initial_soc: float = 2.5) -> pd.DataFrame:
    """
    Run full SoC time-series simulation using optimized signals.
    
    Args:
        df: Optimized DataFrame from optimize_bess()
        initial_soc: Starting state of charge (MWh)
    
    Returns:
        DataFrame with complete time-series including:
            - soc_start, soc_end
            - charge_mwh, discharge_mwh
            - sp_cost, sp_revenue, sp_net
            - action (CHARGE/DISCHARGE/IDLE)
    """
    df = df.copy()
    soc = initial_soc
    
    results = []
    
    for idx, row in df.iterrows():
        record = row.to_dict()
        record["soc_start"] = soc
        
        # Half-hour energy capacity
        half_hr_energy = BATTERY_POWER_MW * 0.5  # MWh per 30-min period
        
        # Default: IDLE
        charge_mwh = 0.0
        discharge_mwh = 0.0
        cost = 0.0
        revenue = 0.0
        action = "IDLE"
        
        # ================================================
        # CHARGING DECISION
        # ================================================
        if row["charge_signal"] and soc < SOC_MAX:
            # Charge up to SoC max, limited by power rating
            charge_mwh = min(half_hr_energy, SOC_MAX - soc)
            soc += charge_mwh
            cost = charge_mwh * row["cost_now"]
            action = "CHARGE"
        
        # ================================================
        # DISCHARGING DECISION
        # ================================================
        elif row["discharge_signal"] and soc > SOC_MIN:
            # Discharge down to SoC min, limited by power rating and efficiency
            max_discharge = min(
                half_hr_energy * EFFICIENCY,  # Power limit after efficiency
                soc - SOC_MIN  # SoC constraint
            )
            discharge_mwh = max_discharge
            soc -= discharge_mwh
            revenue = discharge_mwh * row["r_now"]
            action = "DISCHARGE"
        
        # Store results
        record["charge_mwh"] = charge_mwh
        record["discharge_mwh"] = discharge_mwh
        record["soc_end"] = soc
        record["sp_cost"] = cost
        record["sp_revenue"] = revenue
        record["sp_net"] = revenue - cost
        record["action"] = action
        
        results.append(record)
    
    return pd.DataFrame(results)


# ====================================================
# PERFORMANCE METRICS
# ====================================================

def compute_metrics(df: pd.DataFrame) -> dict:
    """
    Compute comprehensive battery performance metrics.
    
    Returns:
        Dictionary with:
            - charged_mwh: Total energy charged
            - discharged_mwh: Total energy discharged
            - cycles: Number of full cycles
            - total_revenue: Total revenue (£)
            - total_cost: Total charging cost (£)
            - gross_profit: Revenue - cost
            - avg_efficiency: Actual round-trip efficiency
            - utilization: % of time battery active
            - charge_periods: Count of charging periods
            - discharge_periods: Count of discharge periods
    """
    charged = df["charge_mwh"].sum()
    discharged = df["discharged_mwh"].sum()
    cycles = charged / BATTERY_ENERGY_MWH
    
    total_revenue = df["sp_revenue"].sum()
    total_cost = df["sp_cost"].sum()
    gross_profit = total_revenue - total_cost
    
    # Actual efficiency (might differ from theoretical due to partial cycles)
    actual_efficiency = discharged / charged if charged > 0 else 0
    
    # Utilization
    active_periods = ((df["action"] == "CHARGE") | (df["action"] == "DISCHARGE")).sum()
    utilization = active_periods / len(df) * 100
    
    charge_periods = (df["action"] == "CHARGE").sum()
    discharge_periods = (df["action"] == "DISCHARGE").sum()
    
    return {
        "charged_mwh": charged,
        "discharged_mwh": discharged,
        "cycles": cycles,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "gross_profit": gross_profit,
        "avg_efficiency": actual_efficiency,
        "utilization_pct": utilization,
        "charge_periods": charge_periods,
        "discharge_periods": discharge_periods,
        "avg_profit_per_cycle": gross_profit / cycles if cycles > 0 else 0
    }


# ====================================================
# HELPER: COMPARE MYOPIC VS OPTIMIZED
# ====================================================

def compare_strategies(df: pd.DataFrame) -> Tuple[dict, dict]:
    """
    Compare myopic (greedy) vs optimized strategies.
    
    Returns:
        (myopic_metrics, optimized_metrics)
    """
    
    # Myopic strategy: charge when cost < 120, discharge when revenue > cost
    df_myopic = df.copy()
    df_myopic["charge_signal"] = df_myopic["cost_now"] < 120
    df_myopic["discharge_signal"] = df_myopic["r_now"] > df_myopic["cost_now"]
    
    df_myopic_sim = simulate_soc_optimized(df_myopic)
    myopic_metrics = compute_metrics(df_myopic_sim)
    
    # Optimized strategy
    df_optimized = optimize_bess(df)
    df_optimized_sim = simulate_soc_optimized(df_optimized)
    optimized_metrics = compute_metrics(df_optimized_sim)
    
    return myopic_metrics, optimized_metrics


# ====================================================
# MAIN EXECUTION
# ====================================================

if __name__ == "__main__":
    print("=" * 80)
    print("GB POWER MARKET - OPTIMISED BESS ENGINE")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Horizon: {HORIZON} periods ({HORIZON/2} hours)")
    print(f"  Efficiency: {EFFICIENCY*100}%")
    print(f"  Battery: {BATTERY_ENERGY_MWH} MWh / {BATTERY_POWER_MW} MW")
    print(f"  SoC Range: {SOC_MIN:.2f} - {SOC_MAX:.2f} MWh")
    print("\n" + "=" * 80)
    
    # Example usage would require BigQuery data
    # See full_btm_bess_simulation.py for complete integration
    
    print("\n✅ Optimisation engine ready")
    print("   Import this module to use optimize_bess() and simulate_soc_optimized()")
    print("=" * 80)
