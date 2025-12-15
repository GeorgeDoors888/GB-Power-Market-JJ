#!/usr/bin/env python3
"""
BTM BESS – Greedy vs Optimised Dispatch + Dashboard Writer

MODIFIED: Writes to BESS sheet rows 400+ (doesn't clear existing data)
Preserves rows 1-399 (DNO, HH, BtM PPA, Enhanced Revenue Analysis)

- Fetches v_btm_bess_inputs from BigQuery
- Runs two modes:
    * greedy: local decision rule (charge/discharge based on NOW)
    * optimised: look-ahead rule (48 SP lookahead)
- Writes outputs to Google Sheets:
    * BESS rows 400+ (full time series for both modes)
    * Dashboard (KPIs for each mode)
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import gspread
import os

# ---------------- CONFIG ----------------

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
VIEW = "v_btm_bess_inputs"
SERVICE_ACCOUNT_FILE = os.environ.get(
    'GOOGLE_APPLICATION_CREDENTIALS',
    '/home/george/.config/google-cloud/bigquery-credentials.json'
)
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"  # CORRECT sheet

BATTERY_POWER_MW = 2.5
BATTERY_ENERGY_MWH = 5.0
EFFICIENCY = 0.85
SOC_MIN = 0.05 * BATTERY_ENERGY_MWH
SOC_MAX = BATTERY_ENERGY_MWH
INITIAL_SOC = 2.5  # MWh

FIXED_OPEX = 100_000.0
VARIABLE_OPEX_PER_MWH = 3.0

LOOKAHEAD_SP = 48  # 1 day = 48 settlement periods

BTM_START_ROW = 400  # Start writing BTM comparison here (below enhanced model)

# ---------------- HELPERS ----------------

def make_bq_client() -> bigquery.Client:
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"],
    )
    return bigquery.Client(project=PROJECT_ID, credentials=creds, location='US')


def make_gs_client():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(creds)


def fetch_inputs() -> pd.DataFrame:
    """Fetch data from v_btm_bess_inputs view"""
    client = make_bq_client()
    sql = f"""
    SELECT *
    FROM `{PROJECT_ID}.{DATASET}.{VIEW}`
    WHERE ts_halfhour >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY)
    ORDER BY ts_halfhour
    LIMIT 336  -- 7 days = 336 settlement periods
    """
    
    try:
        df = client.query(sql).to_dataframe()
        print(f"✅ Fetched {len(df)} rows from {VIEW}")
        return df
    except Exception as e:
        print(f"❌ Error fetching {VIEW}: {e}")
        print("⚠️  View may not exist - create it first with the SQL provided")
        return pd.DataFrame()


def add_cost_revenue_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate total cost and revenue per settlement period"""
    df = df.copy()
    df["cost_now"] = df["ssp_charge"] + df["duos_charge"] + df["levies_per_mwh"]
    df["r_now"] = (
        df["ppa_price"] +
        df["bm_revenue_per_mwh"] +
        df["dc_revenue_per_mwh"] +
        df["cm_revenue_per_mwh"] +
        df["other_revenue_per_mwh"]
    )
    return df


# ---------------- RESULT DATACLASS ----------------

@dataclass
class SimResult:
    df: pd.DataFrame
    total_revenue: float
    total_cost: float
    charged_mwh: float
    discharged_mwh: float
    ebitda: float


# ---------------- GREEDY SIMULATION ----------------

def simulate_greedy(df_in: pd.DataFrame) -> SimResult:
    """
    Greedy dispatch: charge/discharge based ONLY on current SP
    - Charge if η * R_now > C_now
    - Discharge if R_now > C_now
    """
    df = df_in.copy()
    soc = INITIAL_SOC

    records = []
    total_revenue = 0.0
    total_cost = 0.0
    charged_mwh = 0.0
    discharged_mwh = 0.0

    for _, row in df.iterrows():
        record = row.to_dict()
        record["soc_start"] = soc

        half_hour_energy = BATTERY_POWER_MW * 0.5
        cost_now = row["cost_now"]
        r_now = row["r_now"]

        charge_mwh = 0.0
        discharge_mwh = 0.0
        action = "IDLE"
        sp_cost = 0.0
        sp_rev = 0.0

        # Greedy rule
        if soc < SOC_MAX and (EFFICIENCY * r_now > cost_now):
            charge_mwh = min(half_hour_energy, SOC_MAX - soc)
            soc += charge_mwh
            sp_cost = charge_mwh * cost_now
            total_cost += sp_cost
            charged_mwh += charge_mwh
            action = "CHARGE"

        elif soc > SOC_MIN and (r_now > cost_now):
            discharge_mwh = min(half_hour_energy * EFFICIENCY, soc - SOC_MIN)
            soc -= discharge_mwh
            sp_rev = discharge_mwh * r_now
            total_revenue += sp_rev
            discharged_mwh += discharge_mwh
            action = "DISCHARGE"

        record["charge_mwh"] = charge_mwh
        record["discharge_mwh"] = discharge_mwh
        record["soc_end"] = soc
        record["sp_cost"] = sp_cost
        record["sp_revenue"] = sp_rev
        record["sp_net"] = sp_rev - sp_cost
        record["mode"] = "GREEDY"
        record["action"] = action

        records.append(record)

    var_opex = VARIABLE_OPEX_PER_MWH * discharged_mwh
    ebitda = total_revenue - total_cost - var_opex - FIXED_OPEX

    df_out = pd.DataFrame.from_records(records)
    return SimResult(
        df=df_out,
        total_revenue=total_revenue,
        total_cost=total_cost,
        charged_mwh=charged_mwh,
        discharged_mwh=discharged_mwh,
        ebitda=ebitda,
    )


# ---------------- OPTIMISED SIMULATION ----------------

def add_lookahead_signals(df_in: pd.DataFrame) -> pd.DataFrame:
    """Add 48 SP lookahead signals for optimized dispatch"""
    df = df_in.copy()

    # Future max revenue over next LOOKAHEAD_SP periods
    df["future_max_r"] = (
        df["r_now"]
        .rolling(window=LOOKAHEAD_SP, min_periods=1)
        .max()
        .shift(-LOOKAHEAD_SP)
    )
    df["future_min_c"] = (
        df["cost_now"]
        .rolling(window=LOOKAHEAD_SP, min_periods=1)
        .min()
        .shift(-LOOKAHEAD_SP)
    )

    # Fill tails
    df["future_max_r"].fillna(df["r_now"].max(), inplace=True)
    df["future_min_c"].fillna(df["cost_now"].min(), inplace=True)

    # Decision logic
    df["charge_signal"] = (EFFICIENCY * df["future_max_r"] > df["cost_now"])
    df["discharge_signal"] = (df["r_now"] > df["future_min_c"])

    return df


def simulate_optimised(df_in: pd.DataFrame) -> SimResult:
    """
    Optimized dispatch: look ahead 48 SP (1 day)
    - Charge if η * max(R_future) > C_now
    - Discharge if R_now > min(C_future)
    """
    df = add_lookahead_signals(df_in)
    soc = INITIAL_SOC

    records = []
    total_revenue = 0.0
    total_cost = 0.0
    charged_mwh = 0.0
    discharged_mwh = 0.0

    for _, row in df.iterrows():
        record = row.to_dict()
        record["soc_start"] = soc

        half_hour_energy = BATTERY_POWER_MW * 0.5
        cost_now = row["cost_now"]
        r_now = row["r_now"]

        charge_mwh = 0.0
        discharge_mwh = 0.0
        action = "IDLE"
        sp_cost = 0.0
        sp_rev = 0.0

        charge_sig = bool(row["charge_signal"])
        discharge_sig = bool(row["discharge_signal"])

        if soc < SOC_MAX and charge_sig:
            charge_mwh = min(half_hour_energy, SOC_MAX - soc)
            soc += charge_mwh
            sp_cost = charge_mwh * cost_now
            total_cost += sp_cost
            charged_mwh += charge_mwh
            action = "CHARGE"
        elif soc > SOC_MIN and discharge_sig:
            discharge_mwh = min(half_hour_energy * EFFICIENCY, soc - SOC_MIN)
            soc -= discharge_mwh
            sp_rev = discharge_mwh * r_now
            total_revenue += sp_rev
            discharged_mwh += discharge_mwh
            action = "DISCHARGE"

        record["charge_mwh"] = charge_mwh
        record["discharge_mwh"] = discharge_mwh
        record["soc_end"] = soc
        record["sp_cost"] = sp_cost
        record["sp_revenue"] = sp_rev
        record["sp_net"] = sp_rev - sp_cost
        record["mode"] = "OPTIMISED"
        record["action"] = action

        records.append(record)

    var_opex = VARIABLE_OPEX_PER_MWH * discharged_mwh
    ebitda = total_revenue - total_cost - var_opex - FIXED_OPEX

    df_out = pd.DataFrame.from_records(records)
    return SimResult(
        df=df_out,
        total_revenue=total_revenue,
        total_cost=total_cost,
        charged_mwh=charged_mwh,
        discharged_mwh=discharged_mwh,
        ebitda=ebitda,
    )


# ---------------- SHEET WRITER (MODIFIED) ----------------

def write_to_sheets(greedy: SimResult, opti: SimResult):
    """
    Write BTM comparison to BESS sheet starting at row 400
    DOES NOT clear existing data (rows 1-399)
    """
    gc = make_gs_client()
    ss = gc.open_by_key(SPREADSHEET_ID)
    bess = ss.worksheet("BESS")

    # Clear only BTM section (rows 400+)
    print(f"📝 Writing BTM comparison to BESS sheet row {BTM_START_ROW}+...")
    
    # Section divider
    bess.update(range_name=f'A{BTM_START_ROW-2}', values=[['─' * 100]])
    bess.update(range_name=f'A{BTM_START_ROW-1}', values=[['─── BTM BESS: Greedy vs Optimized Dispatch Comparison ───']])

    # Combine both modes
    df_bess = pd.concat([greedy.df, opti.df], ignore_index=True)
    df_bess.sort_values(["ts_halfhour", "mode"], inplace=True)

    # Write headers and data
    headers = list(df_bess.columns)
    bess.update(range_name=f'A{BTM_START_ROW}', values=[headers])
    
    if not df_bess.empty:
        data = df_bess.astype(str).values.tolist()
        bess.update(range_name=f'A{BTM_START_ROW+1}', values=data)
        print(f"✅ Wrote {len(data)} rows to BESS!A{BTM_START_ROW+1}")

    # Write summary KPIs to Dashboard
    try:
        dash = ss.worksheet("Dashboard")
        
        # Write KPI comparison
        dash.update(range_name="A50", values=[["─── BTM BESS Comparison ───"]])
        dash.update(range_name="A51", values=[["Mode", "Charged MWh", "Discharged MWh", "Revenue £", "Cost £", "EBITDA £"]])
        dash.update(range_name="A52", values=[[
            "GREEDY",
            f"{greedy.charged_mwh:.2f}",
            f"{greedy.discharged_mwh:.2f}",
            f"£{greedy.total_revenue:,.0f}",
            f"£{greedy.total_cost:,.0f}",
            f"£{greedy.ebitda:,.0f}"
        ]])
        dash.update(range_name="A53", values=[[
            "OPTIMISED",
            f"{opti.charged_mwh:.2f}",
            f"{opti.discharged_mwh:.2f}",
            f"£{opti.total_revenue:,.0f}",
            f"£{opti.total_cost:,.0f}",
            f"£{opti.ebitda:,.0f}"
        ]])
        
        # Comparison metrics
        improvement = opti.ebitda - greedy.ebitda
        improvement_pct = (improvement / abs(greedy.ebitda) * 100) if greedy.ebitda != 0 else 0
        dash.update(range_name="A54", values=[[f"Improvement: £{improvement:,.0f} ({improvement_pct:+.1f}%)"]])
        
        print("✅ Updated Dashboard with BTM KPIs")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not update Dashboard: {e}")


# ---------------- MAIN ----------------

def main():
    print("="*70)
    print("BTM BESS - GREEDY VS OPTIMIZED DISPATCH COMPARISON")
    print("="*70)
    
    df_raw = fetch_inputs()
    if df_raw.empty:
        print("❌ No data in v_btm_bess_inputs view")
        print("\n⚠️  Create the view first using the SQL:")
        print("   CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs` AS ...")
        return

    df = add_cost_revenue_columns(df_raw)

    print("\n🔄 Running simulations...")
    greedy = simulate_greedy(df)
    opti = simulate_optimised(df)

    print(f"\n{'='*70}")
    print(f"📊 RESULTS")
    print(f"{'='*70}")
    print(f"GREEDY EBITDA:    £{greedy.ebitda:>12,.0f}")
    print(f"OPTIMISED EBITDA: £{opti.ebitda:>12,.0f}")
    print(f"IMPROVEMENT:      £{(opti.ebitda - greedy.ebitda):>12,.0f} ({((opti.ebitda - greedy.ebitda)/abs(greedy.ebitda)*100):+.1f}%)")
    print(f"{'='*70}")

    write_to_sheets(greedy, opti)
    
    print("\n✅ BTM comparison complete")
    print(f"🌐 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")


if __name__ == "__main__":
    main()
