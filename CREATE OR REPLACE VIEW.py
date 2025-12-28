CREATE OR REPLACE VIEW
  `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs` AS

-- 1) Base: system prices + DUoS band
WITH base_prices AS (
  SELECT
    settlementDate,
    settlementPeriod,
    -- Build half-hourly timestamp (UTC – adjust if needed)
    TIMESTAMP(
      CONCAT(
        CAST(settlementDate AS STRING),
        " ",
        LPAD(CAST((settlementPeriod - 1) / 2 AS STRING), 2, "0"), ":",
        LPAD(CAST((settlementPeriod - 1) % 2 * 30 AS STRING), 2, "0")
      )
    ) AS ts_halfhour,

    systemBuyPrice AS ssp_charge,
    systemSellPrice AS ssp_sell,

    CASE
      WHEN EXTRACT(DAYOFWEEK FROM settlementDate) IN (1,7)
        THEN 'GREEN'
      WHEN settlementPeriod BETWEEN 33 AND 39
        THEN 'RED'
      WHEN settlementPeriod BETWEEN 17 AND 32
        OR settlementPeriod BETWEEN 40 AND 44
        THEN 'AMBER'
      ELSE 'GREEN'
    END AS duos_band
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
),

-- 2) DUoS rates (hard-coded for NGED West Midlands as per your example)
duos_rates AS (
  SELECT 'RED' AS duos_band,   17.64 AS duos_rate UNION ALL
  SELECT 'AMBER',              2.05  UNION ALL
  SELECT 'GREEN',              0.11
),

-- 3) Fixed levies (RO, FiT, CfD, CCL, BSUoS, TNUoS, etc) per MWh
levies AS (
  SELECT
    98.15 AS levies_per_mwh  -- £/MWh, adjust if you refine
),

-- 4) BMRS BOALF – average £/MWh BM/VLP revenue per SP
bm_vlp_revenue AS (
  SELECT
    settlementDate,
    settlementPeriod,
    -- average revenue per MWh accepted (simple approximation)
    AVG(acceptancePrice) AS bm_revenue_per_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE levelTo IS NOT NULL
  GROUP BY settlementDate, settlementPeriod
),

-- 5) Optional: Dynamic Containment (or ESO service) £/MWh per SP
-- Adjust table/field names to match your DC dataset
dc_revenue AS (
  SELECT
    TIMESTAMP_TRUNC(event_time, MINUTE) AS ts_halfhour,
    AVG(dc_price_mwh) AS dc_revenue_per_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.esoservices_dynamic_containment`
  GROUP BY ts_halfhour
),

-- 6) Capacity Market revenue per MWh (amortised from £/kW/yr)
capacity_market AS (
  SELECT
    5.0 AS cm_revenue_per_mwh  -- example value; update from your CM data
),

-- 7) PPA price (can later be made time-varying if needed)
ppa_price AS (
  SELECT
    150.0 AS ppa_price
),

-- 8) Optional: other revenues (DSO flex, constraint mgmt)
other_revenue AS (
  SELECT
    0.0 AS other_revenue_per_mwh  -- placeholder for now
),

joined AS (
  SELECT
    bp.ts_halfhour,
    bp.settlementDate,
    bp.settlementPeriod,
    bp.ssp_charge,
    dr.duos_rate AS duos_charge,
    lev.levies_per_mwh,
    ppa.ppa_price,

    COALESCE(bm.bm_revenue_per_mwh, 0.0) AS bm_revenue_per_mwh,
    COALESCE(dc.dc_revenue_per_mwh, 0.0) AS dc_revenue_per_mwh,
    cm.cm_revenue_per_mwh,
    other.other_revenue_per_mwh,
    bp.duos_band

  FROM base_prices bp
  LEFT JOIN duos_rates dr
    ON bp.duos_band = dr.duos_band
  CROSS JOIN levies lev
  CROSS JOIN ppa_price ppa
  CROSS JOIN capacity_market cm
  CROSS JOIN other_revenue other
  LEFT JOIN bm_vlp_revenue bm
    ON bp.settlementDate = bm.settlementDate
   AND bp.settlementPeriod = bm.settlementPeriod
  LEFT JOIN dc_revenue dc
    ON TIMESTAMP_TRUNC(bp.ts_halfhour, MINUTE) = dc.ts_halfhour
)

SELECT *
FROM joined
ORDER BY ts_halfhour; 

#!/usr/bin/env python3
"""
BTM BESS – Greedy vs Optimised Dispatch + Dashboard Writer

- Fetches v_btm_bess_inputs from BigQuery
- Runs two modes:
    * greedy: local decision rule
    * optimised: look-ahead rule
- Writes outputs to Google Sheets:
    * BESS (full time series)
    * Dashboard (KPIs for each mode)

Requires:
    pip install google-cloud-bigquery gspread oauth2client pandas
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from typing import Tuple

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import gspread


# ---------------- CONFIG ----------------

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
VIEW = "v_btm_bess_inputs"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"  # GB Live 2 - CORRECT!

BATTERY_POWER_MW = 2.5
BATTERY_ENERGY_MWH = 5.0
EFFICIENCY = 0.85
SOC_MIN = 0.05 * BATTERY_ENERGY_MWH
SOC_MAX = BATTERY_ENERGY_MWH
INITIAL_SOC = 2.5  # MWh

FIXED_OPEX = 100_000.0
VARIABLE_OPEX_PER_MWH = 3.0

LOOKAHEAD_SP = 48  # 1 day = 48 settlement periods


# ---------------- HELPERS ----------------

def make_bq_client() -> bigquery.Client:
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"],
    )
    return bigquery.Client(project=PROJECT_ID, credentials=creds)


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
    client = make_bq_client()
    sql = f"""
    SELECT *
    FROM `{PROJECT_ID}.{DATASET}.{VIEW}`
    ORDER BY ts_halfhour
    """
    df = client.query(sql).to_dataframe()
    return df


def add_cost_revenue_columns(df: pd.DataFrame) -> pd.DataFrame:
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


# ---------------- GREEDY SIM ----------------

@dataclass
class SimResult:
    df: pd.DataFrame
    total_revenue: float
    total_cost: float
    charged_mwh: float
    discharged_mwh: float
    ebitda: float


def simulate_greedy(df_in: pd.DataFrame) -> SimResult:
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

        # Greedy rule: look only at "now"
        # Charge if η * r_now > cost_now
        if soc < SOC_MAX and (EFFICIENCY * r_now > cost_now):
            charge_mwh = min(half_hour_energy, SOC_MAX - soc)
            soc += charge_mwh
            sp_cost = charge_mwh * cost_now
            total_cost += sp_cost
            charged_mwh += charge_mwh
            action = "CHARGE"

        # Else discharge if r_now > cost_now
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


# ---------------- OPTIMISED SIM ----------------

def add_lookahead_signals(df_in: pd.DataFrame) -> pd.DataFrame:
    df = df_in.copy()

    # future max revenue over next LOOKAHEAD_SP
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

    # Decision logic:
    df["charge_signal"] = (EFFICIENCY * df["future_max_r"] > df["cost_now"])
    df["discharge_signal"] = (df["r_now"] > df["future_min_c"])

    return df


def simulate_optimised(df_in: pd.DataFrame) -> SimResult:
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


# ---------------- DASHBOARD WRITER ----------------

def write_to_sheets(greedy: SimResult, opti: SimResult):
    gc = make_gs_client()
    ss = gc.open_by_key(SPREADSHEET_ID)

    # BESS sheet: full time-series, both modes stacked
    try:
        bess = ss.worksheet("BESS")
    except gspread.WorksheetNotFound:
        bess = ss.add_worksheet("BESS", rows="50000", cols="30")

    bess.clear()

    df_bess = pd.concat([greedy.df, opti.df], ignore_index=True)
    df_bess.sort_values(["ts_halfhour", "mode"], inplace=True)

    headers = list(df_bess.columns)
    bess.append_row(headers)
    if not df_bess.empty:
        bess.update("A2", df_bess.values.tolist())

    # Dashboard KPIs
    dash = ss.worksheet("Dashboard")

    # Example: two rows of KPIs, one per mode
    # Greedy in row 10, Optimised in row 11
    dash.update("A10", [["Mode", "Charged MWh", "Discharged MWh", "Revenue", "Cost", "EBITDA"]])
    dash.update("A11", [[
        "GREEDY",
        greedy.charged_mwh,
        greedy.discharged_mwh,
        greedy.total_revenue,
        greedy.total_cost,
        greedy.ebitda
    ]])
    dash.update("A12", [[
        "OPTIMISED",
        opti.charged_mwh,
        opti.discharged_mwh,
        opti.total_revenue,
        opti.total_cost,
        opti.ebitda
    ]])

    # Last updated timestamp
    import datetime as dt
    dash.update("A99", [[f"Last Updated: {dt.datetime.now().isoformat(sep=' ', timespec='seconds')}"]])


# ---------------- MAIN ----------------

def main():
    df_raw = fetch_inputs()
    if df_raw.empty:
        print("No data in v_btm_bess_inputs.")
        return

    df = add_cost_revenue_columns(df_raw)

    greedy = simulate_greedy(df)
    opti = simulate_optimised(df)

    print("GREEDY EBITDA:   £{:,.0f}".format(greedy.ebitda))
    print("OPTIMISED EBITDA £{:,.0f}".format(opti.ebitda))

    write_to_sheets(greedy, opti)


if __name__ == "__main__":
    main() D) What optimisation mode actually does vs greedy

To make it crystal clear:

1. Greedy mode

Uses only current SP values:
	•	Charges if
\eta \cdot R_\text{now} > C_\text{now}
	•	Discharges if
R_\text{now} > C_\text{now}

No awareness of tomorrow’s peak, no “saving” energy for later.

⸻

2. Optimised mode

Adds look-ahead across LOOKAHEAD_SP periods (e.g. 48 SP = 1 day):
	•	Compute future max revenue \max R_{t..t+H}
	•	Compute future min cost \min C_{t..t+H}

Then:
	•	Charge if
\eta \cdot \max_{t..t+H}(R) > C_t
→ only fill the battery when you know there’s a better revenue period coming.
	•	Discharge if
R_t > \min_{t..t+H}(C)
→ only empty the battery when today’s revenue is better than any cheap buying period ahead.

So the battery behaves more like a trader with a view rather than a dumb arbitrage robot.

⸻

If you’d like, I can next:
	•	Add a side-by-side chart in the Dashboard (Greedy vs Optimised SoC and EBITDA),
	•	Or extend the view to split BM revenue into:
	•	curtailment (take generation off),
	•	turn-up (add generation / demand),
and feed them as separate revenue lines.