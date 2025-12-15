# BtM BESS + CHP Revenue Model as a Virtual Lead / Trading Party

**Scope**

This document explains:

- How the GB electricity market works **from the perspective of a Virtual Lead Party (VLP) / Virtual Trading Party (VTP)**.
- How **baselining and deviation volumes** work under the BSC (P376 + P415).
- How to wire this into your **BigQuery** dataset and **Railway-hosted** Python stack.
- The recommended **Google Sheets layout** for single–settlement-period revenue + SoC modelling (for BESS and CHP).
- How **BESS and CHP interact and are optimised** behind the meter.

It is designed specifically for your stack:

- BigQuery project: `inner-cinema-476211-u9`
- Dataset: `uk_energy_prod`
- Google Sheets dashboards: `GB Live`, `BESS`, `BtM Revenue`, etc.
- Python services running on Railway / Cloud Run.

---

## 1. Market Structure – How a VLP / VTP Actually Interacts With the System

### 1.1 Roles: VLP and VTP

Under the BSC:

- A **Virtual Lead Party (VLP)** is an independent aggregator that operates **Secondary BM Units** and can provide balancing services in the **Balancing Mechanism (BM)** for aggregated MSIDs / AMSIDs.
- A **Virtual Trading Party (VTP)** (introduced with P415) can trade **Deviation Volumes in the wholesale market** (day-ahead / intraday) based on flexible demand/generation behind MSIDs/AMSIDs.

Both use **Baselined BM Units** and **Baselining Methodology BL01** to determine the “what would have happened” case versus actual metered behaviour.

---

### 1.2 Baselining – How Delivered Volume is Determined

The Baselining Methodology Document (version 3.0) defines:

- **Baselined Entities**: MSID Pairs, AMSID Pairs, or asset-differencing schemes that need a **Baseline Value** in MWh per Settlement Period.
- **BL01** (current default method) that:
  1. Uses up to the last **60 days of historical metered data** of the same day type (working / non-working).
  2. Excludes **Event Days** (days with BM dispatch, virtual trading, outages, etc.).
  3. Computes an **Unadjusted Baseline** = straight average over the selected historical days.
  4. Adds an **In-Day Adjustment** using the last 3 hours of metered data before Gate Closure to correct for weather/conditions on the day.
  5. Produces a per–Settlement Period **Baseline Value** in MWh for each Baselined Entity.

**Delivered Volume** for flexibility (BM or wholesale) is then:

```text
Delivered Volume (MWh) = Actual Metered Volume – Baseline Value
```

This is what drives:
- BM revenues (Bids/Offers) for a VLP; and
- Wholesale deviation volumes for a VTP (P415).

---

### 1.3 Where BESS / CHP Fit in

- Your battery is an AMSID/MSID behind a Secondary BM Unit and possibly a Trading Secondary BM Unit.
- Your CHP is another MSID (or set) with:
  - Fuel costs (gas/biomass),
  - Electricity export/import position,
  - Heat loads (which indirectly constrain operation).

For a VLP/VTP, BESS + CHP are just flexible metered points whose baseline is calculated centrally by SVAA, and whose deviation from baseline is tradable:
- Into BM (Bids/Offers),
- Into wholesale (DA/ID),
- Into ESO services (DC/FR/Reserve),
- While also delivering behind-the-meter value (avoided import, PPA).

---

## 2. BigQuery Architecture – Views and Tables

### 2.1 Source Tables (example mapping)

Your dataset `uk_energy_prod` already includes tables such as:
- `bmrs_boalf` – Bid/Offer Acceptance data (Balancing Mechanism).
- `bmrs_costs` – system prices, SSP/SBP, BSUoS proxies.
- `vlp_trades_summary` / `vlp_trades_detail` – your own summaries of VLP trades.
- Additional tables for:
  - DUoS/TNUoS/BSUoS rates,
  - Capacity Market auction results,
  - ESO service prices (DC, FR, STOR),
  - PPA price history.

### 2.2 Core View: `v_btm_bess_inputs`

You’ll define a BigQuery view that pulls together all inputs per Settlement Period for the battery + CHP site.

**Suggested schema (key headers):**

```sql
settlement_date           DATE
settlement_period         INT64              -- 1..48
sp_start_utc              TIMESTAMP
sp_duration_hours         FLOAT64           -- 0.5 for GB
gsp_id                    STRING
dno_region                STRING

bm_unit_id_bess           STRING
bm_unit_id_chp            STRING
is_bess_baselined         BOOL
is_chp_baselined          BOOL

baseline_bess_mwh         FLOAT64           -- BL01 baseline
baseline_chp_mwh          FLOAT64
actual_bess_mwh           FLOAT64           -- metered
actual_chp_mwh            FLOAT64
deviation_bess_mwh        FLOAT64           -- actual - baseline
deviation_chp_mwh         FLOAT64

ssp_price_gbp_mwh         FLOAT64           -- system sell price
sbp_price_gbp_mwh         FLOAT64           -- system buy price
wholesale_price_da        FLOAT64
wholesale_price_id        FLOAT64
ppa_price_gbp_mwh         FLOAT64

bm_offer_price_bess       FLOAT64
bm_bid_price_bess         FLOAT64
eso_util_price_bess       FLOAT64          -- DC/FR utilisation
eso_avail_price_bess      FLOAT64          -- £/MW/h
dso_avail_price_bess      FLOAT64
cm_price_gbp_kw_yr        FLOAT64

duos_band                 STRING           -- Red/Amber/Green
duos_import_gbp_mwh       FLOAT64
tnuos_import_gbp_mwh      FLOAT64
bsuos_import_gbp_mwh      FLOAT64
levies_import_gbp_mwh     FLOAT64          -- RO+FiT+CfD+CCL+ECO+WHD+AAHEDC
full_import_cost_gbp_mwh  FLOAT64          -- energy + DUoS + levies

bess_charge_cost_gbp_mwh  FLOAT64          -- all-in per charged MWh
bess_discharge_cost_gbp_mwh FLOAT64        -- all-in per discharged MWh (includes η)

soc_start_mwh             FLOAT64          -- SoC at start of SP
soc_end_mwh               FLOAT64
soc_min_mwh               FLOAT64
soc_max_mwh               FLOAT64

chp_fuel_cost_gbp_mwh_el  FLOAT64          -- fuel cost per MWh electric
chp_heat_value_gbp_mwh_th FLOAT64          -- credit for delivered heat
chp_marginal_cost_gbp_mwh FLOAT64          -- net electric marginal cost

energy_route_bess         STRING           -- {BM, PPA, Wholesale, ESO Util, BtM Avoided}
energy_route_chp          STRING
cm_equiv_gbp_mwh          FLOAT64          -- CM £/kW/yr → £/MWh
availability_gbp_mwh      FLOAT64          -- ESO/DNO availability → £/MWh eq

event_day_flag            BOOL             -- BSC Event Day
bm_acceptance_flag        BOOL
wholesale_activity_flag   BOOL
```

This view is the single source of truth that Railway/Cloud Run Python will query for each Settlement Period.

---

## 3. Google Sheet Layout – Single-Event Revenue & SoC Block

This corresponds to what you asked for, extended with SoC. Put it on a sheet like `BESS_Event`.

### 3.1 Input/parameter block

| Cell | Input / Parameter | Value | Note |
| :--- | :--- | :--- | :--- |
| A2 | **Input / Parameter** | | |
| A3 | Discharged MWh | 1 | (MWh this SP, e.g. 1.0) |
| A4 | Settlement Period hours | 0.5 | (0.5 for GB SP) |
| | | | |
| A6 | Energy Route (dropdown) | BM | (BM, PPA, Wholesale, ESO Util, BtM Avoided) |
| | | | |
| A8 | BM price (£/MWh) | 220 | |
| A9 | PPA price (£/MWh) | 150 | |
| A10 | Wholesale price (£/MWh) | 130 | |
| A11 | ESO utilisation price (£/MWh) | 180 | |
| A12 | Full import cost (£/MWh) | 140 | (energy + DUoS + levies) |
| | | | |
| A14 | CM revenue (equiv £/MWh) | 5 | (CM £/kW/year converted to £/MWh) |
| A15 | Availability £/MW/h | 10 | (ESO/DSO availability rate) |
| | | | |
| A17 | Charging cost £/MWh (net) | 120 | (all-in cost per discharged MWh incl. efficiency) |
| | | | |
| A19 | **---- SoC parameters ----** | | |
| A20 | SoC at start (MWh) | 3.0 | (state of charge at SP start) |
| A21 | SoC minimum (MWh) | 1.0 | |
| A22 | SoC maximum (MWh) | 5.0 | |
| A23 | Max charge power (MW) | 2.5 | |
| A24 | Max discharge power (MW) | 2.5 | |
| A25 | Round-trip efficiency (%) | 85% | |
| | | | |
| A27 | **---- Derived values ----** | | |
| A28 | Discharge power (MW) | | |
| A29 | SoC at end (MWh) | | |
| A30 | Energy revenue (£) | | |
| A31 | CM revenue (£) | | |
| A32 | Availability revenue (£) | | |
| A33 | Total stacked revenue (£) | | |
| A34 | Charging cost (£) | | |
| A35 | Margin on this 1 MWh (£) | | |

---

## 4. Python Logic (Optimisation)

For each SP:

```python
# 1. Pull inputs from v_btm_bess_inputs
price_route = choose_best_energy_route(...)  # BM vs PPA vs Wholesale vs BtM
bess_value_per_mwh = energy_price - bess_discharge_cost_gbp_mwh \
                     + cm_equiv_gbp_mwh + availability_equiv_gbp_mwh

chp_value_per_mwh = ppa_price_gbp_mwh - chp_marginal_cost_gbp_mwh

# 2. Apply SoC constraints
max_bess_discharge_mwh = min(
    (soc_start_mwh - soc_min_mwh),
    max_discharge_power_mw * sp_duration_hours
)

# 3. Merit order
if bess_value_per_mwh > chp_value_per_mwh and max_bess_discharge_mwh > 0:
    bess_dispatch_mwh = max_bess_discharge_mwh
    chp_dispatch_mwh  = min(site_net_load_mwh - bess_dispatch_mwh, chp_max_mwh)
else:
    chp_dispatch_mwh  = min(site_net_load_mwh, chp_max_mwh)
    bess_dispatch_mwh = max(0, site_net_load_mwh - chp_dispatch_mwh)

# 4. Update SoC
soc_end_mwh = soc_start_mwh - bess_dispatch_mwh + bess_charge_mwh
```

---

## 5. Implementation in Practice

- You’d run this across 48 SPs per day with SoC carried forward.
- The BESS/CHP optimiser runs in Python (Railway) using BigQuery inputs.
- The resulting dispatch, margins and SoC profiles are written back to your Google Sheets (GB Live, BESS, BtM Revenue) via your `/sheets_read` / `/sheets_write` endpoints.

---

## 6. How Calculations Align With BSC & Baselining

This design aligns with the Baselining Methodology and P415 as follows:

- **Delivered MWh per SP is always:**
  ```text
  Actual Metered – Baseline (BL01, with in-day adjustment)
  ```
  calculated centrally by SVAA using BL01, which averages up to the last 60 like-for-like days and adjusts using a 3-hour pre-gate window.

- **Your BigQuery view `v_btm_bess_inputs` must respect:**
  - Baselined vs non-baselined MSIDs/AMSIDs.
  - **Event Days** (exclude from baseline selection).
  - Distinction between BM Acceptances and Wholesale Market Activity Notifications for VTP trades.

- **The Google Sheet block sits on top as a transparent calculator showing:**
  - What you earned for a specific SP.
  - How SoC moved.
  - How CM + availability overlay on the core energy route.

---

## 7. Summary

- The market logic (BM + wholesale + ESO + CM + DUoS/levies) is implemented once in `v_btm_bess_inputs` in BigQuery.
- The BESS/CHP optimiser in Python uses this view and enforces SoC + technical limits.
- The Google Sheets block you requested gives a clear, auditable per-SP breakdown:
  - Inputs (prices, costs, SoC).
  - Stacked revenues (energy + CM + availability).
  - Charging cost.
  - Margin.
  - SoC trajectory.

**Next Steps:**
1.  Save this file as `BTM_BESS_CHP_VLP_Revenue_Model.md` in your repo.
2.  Implement `v_btm_bess_inputs` in BigQuery with the suggested headers.
3.  Build the `BESS_Event` sheet block exactly as outlined and wire it to BigQuery outputs.
