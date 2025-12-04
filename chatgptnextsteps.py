#!/usr/bin/env python3
"""
bess_revenue_engine.py

Single-file BESS revenue engine for a 2.5 MW / 5 MWh battery in GB.

Features:
- Ingest Frequency Response auction data (DC/DM/DR) from NESO Data Portal API → BigQuery
- Ingest BMRS replacement feeds (system prices, imbalance, BOAs) → BigQuery
- Co-optimiser:
    - Frequency Response (DC / DM / DR)
    - Simple arbitrage vs SSP/SBP
    - BM (BOA) opportunity cost
    - Imbalance spread penalty
    - Wholesale volatility penalty
- Minimal SoC model (per EFA block)
- KPIs + projected annual revenue:
    - FR net margin
    - Arbitrage estimate
    - Capacity Market
    - VLP flexibility
- Google Sheets integration:
    - Update Dashboard KPI strip + block summary
    - SoC_History sheet + chart
    - FR_Mix, Arbitrage_Cycles, System_Prices, Annual_Projection sheets

This is a production-oriented template: plug in real API endpoints,
service account path, project IDs, and refine parameters for your asset.
"""

from __future__ import annotations

import os
import sys
import math
import json
import logging
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Tuple

import requests
import pandas as pd

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import gspread

# =============================================================================
# CONFIGURATION
# =============================================================================

# ---- GCP / BigQuery ----
GCP_PROJECT_ID = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"

TABLE_FR_PRICES = f"{GCP_PROJECT_ID}.{BQ_DATASET}.fr_prices"
TABLE_BM_BOAS = f"{GCP_PROJECT_ID}.{BQ_DATASET}.bm_boas"
TABLE_SYSTEM_PRICES = f"{GCP_PROJECT_ID}.{BQ_DATASET}.system_prices"

# ---- Google Sheets Dashboard ----
DASHBOARD_SHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
DASHBOARD_TAB_NAME = "Dashboard"
DASHBOARD_KPI_CELL = "A5"
DASHBOARD_SUMMARY_START = "A40"

# ---- Service Account ----
SERVICE_ACCOUNT_JSON = os.environ.get(
    "BESS_ENGINE_CREDS",
    "/path/to/inner-cinema-credentials.json"  # <- replace with your path
)

# ---- NESO / BMRS API Placeholders (replace with real endpoints) ----
NESO_FR_API = "https://data.neso.energy/api/v1/frequency-response/auction-results"  # TODO
NESO_API_KEY = os.environ.get("NESO_API_KEY", "YOUR_NESO_API_KEY")

BMRS_BASE_API = "https://api.bmreports.com/bmrs/v2"  # TODO: update to replacement API
BMRS_API_KEY = os.environ.get("BMRS_API_KEY", "YOUR_BMRS_API_KEY")

# ---- Capacity Market Assumptions (example) ----
CM_PRICE = 30.59         # £/kW/year
DERATED_FACTOR = 0.895   # derating factor for 2h battery (example)

# ---- BESS Asset Config ----
@dataclass
class BESSAsset:
    asset_id: str
    p_max_mw: float
    energy_mwh: float
    round_trip_efficiency: float = 0.9
    degradation_cost_per_mwh: float = 10.0  # £/MWh throughput


DEFAULT_ASSET = BESSAsset(
    asset_id="BESS_2P5MW_5MWH",
    p_max_mw=2.5,
    energy_mwh=5.0,
    round_trip_efficiency=0.9,
    degradation_cost_per_mwh=15.0,
)

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)

# =============================================================================
# CLIENT HELPERS
# =============================================================================

def make_bq_client() -> bigquery.Client:
    if os.path.exists(SERVICE_ACCOUNT_JSON):
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON)
        return bigquery.Client(project=GCP_PROJECT_ID, credentials=creds)
    return bigquery.Client(project=GCP_PROJECT_ID)


def make_sheets_client() -> gspread.Client:
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=scopes)
    return gspread.authorize(creds)

# =============================================================================
# STATE OF CHARGE (SoC) MODEL
# =============================================================================

@dataclass
class SoCState:
    soc_mwh: float
    max_mwh: float
    min_mwh: float = 0.0

    def can_provide_fr(self, block_hours: float) -> bool:
        """Battery must remain within SoC bounds over the FR window."""
        return self.min_mwh <= self.soc_mwh <= self.max_mwh

    def can_discharge(self, mw: float, hours: float) -> bool:
        return (self.soc_mwh - mw * hours) >= self.min_mwh

    def can_charge(self, mw: float, hours: float) -> bool:
        return (self.soc_mwh + mw * hours) <= self.max_mwh

    def discharge(self, mw: float, hours: float, efficiency: float):
        """Apply discharge — includes efficiency losses."""
        energy_out = mw * hours
        energy_reduction = energy_out / efficiency
        self.soc_mwh = max(self.min_mwh, self.soc_mwh - energy_reduction)

    def charge(self, mw: float, hours: float, efficiency: float):
        energy_in = mw * hours
        usable = energy_in * efficiency
        self.soc_mwh = min(self.max_mwh, self.soc_mwh + usable)

# =============================================================================
# INGESTION: NESO FR PRICES
# =============================================================================

def ingest_neso_fr(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Fetch DC/DM/DR auction clearing prices from NESO Data Portal and load into BigQuery.

    NOTE:
    - This is a template. Actual NESO API may require pagination, auth headers, or
      different parameter names. Adapt accordingly.
    """
    logging.info(f"Fetching NESO FR prices from {start_date} to {end_date}...")

    params = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "apiKey": NESO_API_KEY,
    }

    try:
        resp = requests.get(NESO_FR_API, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logging.warning(f"NESO FR API error: {e}")
        return pd.DataFrame()

    df = pd.DataFrame(data.get("results", []))
    if df.empty:
        logging.warning("No NESO FR results fetched.")
        return df

    # Example mapping – adjust to real NESO schema
    rename_map = {
        "delivery_date": "date",
        "efa_block": "efa_block",
        "service": "service",
        "clearing_price_gbp_per_mwh": "clearing_price",
        "volume_mw": "volume_awarded",
        "utilisation_price_gbp_per_mwh": "utilisation_price",
        "event_time": "event_time",
    }
    known_cols = [c for c in rename_map if c in df.columns]
    df = df[known_cols].rename(columns=rename_map)

    if "event_time" in df.columns:
        df["event_time"] = pd.to_datetime(df["event_time"])
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    client = make_bq_client()
    job = client.load_table_from_dataframe(df, TABLE_FR_PRICES)
    job.result()
    logging.info(f"Uploaded {len(df)} FR rows to {TABLE_FR_PRICES}")
    return df

# =============================================================================
# INGESTION: BMRS REPLACEMENT (SYSTEM PRICES + BOAs)
# =============================================================================

def ingest_bmrs_system_prices(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Template for fetching system prices (SSP/SBP) from BMRS replacement API.
    Adjust endpoint/params/schema to actual BMRS replacement feeds.
    """
    logging.info(f"Fetching BMRS system prices from {start_date} to {end_date}...")
    params = {
        "APIKey": BMRS_API_KEY,
        "FromDateTime": start_date.isoformat(),
        "ToDateTime": end_date.isoformat(),
    }

    url = f"{BMRS_BASE_API}/system-prices"  # placeholder
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logging.warning(f"BMRS system prices API error: {e}")
        return pd.DataFrame()

    df = pd.DataFrame(data.get("prices", []))
    if df.empty:
        logging.warning("No system price data fetched.")
        return df

    df = df.rename(columns={
        "time": "timestamp",
        "ssp_gbp_per_mwh": "ssp",
        "sbp_gbp_per_mwh": "sbp",
        "cashout": "cashout_price",
    })
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    client = make_bq_client()
    job = client.load_table_from_dataframe(df, TABLE_SYSTEM_PRICES)
    job.result()
    logging.info(f"Uploaded {len(df)} rows to {TABLE_SYSTEM_PRICES}")
    return df


def ingest_bmrs_boas(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Template for fetching BOA data (bid/offer acceptances) from BMRS replacement.
    Adjust fields and endpoint names to actual data.
    """
    logging.info(f"Fetching BMRS BOAs from {start_date} to {end_date}...")
    params = {
        "APIKey": BMRS_API_KEY,
        "FromDateTime": start_date.isoformat(),
        "ToDateTime": end_date.isoformat(),
    }
    url = f"{BMRS_BASE_API}/boa"  # placeholder
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logging.warning(f"BMRS BOA API error: {e}")
        return pd.DataFrame()

    df = pd.DataFrame(data.get("boas", []))
    if df.empty:
        logging.warning("No BOA data fetched.")
        return df

    df = df.rename(columns={
        "time": "timestamp",
        "unit": "unit_id",
        "bidVolumeMWh": "bid_volume",
        "offerVolumeMWh": "offer_volume",
        "acceptancePriceGBPperMWh": "acceptance_price",
        "costGBP": "cost",
        "settlementPeriod": "settlement_period",
    })
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    client = make_bq_client()
    job = client.load_table_from_dataframe(df, TABLE_BM_BOAS)
    job.result()
    logging.info(f"Uploaded {len(df)} BOA rows to {TABLE_BM_BOAS}")
    return df

# =============================================================================
# SIMPLE ARBITRAGE ENGINE
# =============================================================================

class ArbitrageEngine:
    """
    Very simple arbitrage:
    - If SBP - SSP > threshold → discharge
    - If SSP < low_threshold → charge
    """

    def __init__(self, asset: BESSAsset, threshold=20.0, low_threshold=20.0):
        self.asset = asset
        self.threshold = threshold
        self.low_threshold = low_threshold

    def compute_arbitrage_margin(
        self,
        block_system_prices: pd.DataFrame,
        soc: SoCState,
        block_hours: float
    ) -> Dict[str, Any]:
        if block_system_prices.empty:
            return {"action": "IDLE", "margin": 0.0}

        ssp = block_system_prices["ssp"].mean()
        sbp = block_system_prices["sbp"].mean()

        # Case 1: discharge when spread is high
        if (sbp - ssp) > self.threshold and soc.can_discharge(self.asset.p_max_mw, block_hours):
            revenue = sbp * self.asset.p_max_mw * block_hours
            deg_cost = self.asset.degradation_cost_per_mwh * (self.asset.p_max_mw * block_hours)
            net = revenue - deg_cost
            return {"action": "DISCHARGE", "margin": net}

        # Case 2: charge when cheap
        if ssp < self.low_threshold and soc.can_charge(self.asset.p_max_mw, block_hours):
            cost = ssp * self.asset.p_max_mw * block_hours
            return {"action": "CHARGE", "margin": -cost}

        return {"action": "IDLE", "margin": 0.0}

# =============================================================================
# CORE OPTIMISER: FR + BM AVOIDANCE + IMBALANCE + VOLATILITY + ARB + SoC
# =============================================================================

class FRBMOptimiser:
    """
    Combined FR revenue optimiser including:
    - FR prices (DC/DM/DR)
    - BM BOA opportunity cost
    - Imbalance spread penalty
    - Wholesale volatility penalty
    - Simple arbitrage (SSP/SBP)
    - Minimal SoC model
    """

    def __init__(self, asset: BESSAsset):
        self.asset = asset
        self.bq = make_bq_client()
        self.soc = SoCState(
            soc_mwh=asset.energy_mwh * 0.5,  # start at 50% SoC
            max_mwh=asset.energy_mwh,
            min_mwh=0.0,
        )
        self.arb_engine = ArbitrageEngine(asset)

    # ---- Data fetchers ----

    def _fetch_fr_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        q = f"""
        SELECT date, efa_block, service, clearing_price
        FROM `{TABLE_FR_PRICES}`
        WHERE date BETWEEN @s AND @e
        """
        job = self.bq.query(
            q,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("s", "DATE", start_date),
                    bigquery.ScalarQueryParameter("e", "DATE", end_date),
                ]
            ),
        )
        df = job.to_dataframe()
        if df.empty:
            logging.warning("No FR prices in BigQuery for given period.")
        return df

    def fetch_system_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        q = f"""
        SELECT timestamp, ssp, sbp, cashout_price
        FROM `{TABLE_SYSTEM_PRICES}`
        WHERE DATE(timestamp) BETWEEN @s AND @e
        """
        job = self.bq.query(
            q,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("s", "DATE", start_date),
                    bigquery.ScalarQueryParameter("e", "DATE", end_date),
                ]
            ),
        )
        return job.to_dataframe()

    def _fetch_boas(self, start_date: date, end_date: date) -> pd.DataFrame:
        q = f"""
        SELECT timestamp, unit_id, bid_volume, offer_volume, acceptance_price, cost
        FROM `{TABLE_BM_BOAS}`
        WHERE DATE(timestamp) BETWEEN @s AND @e
        """
        job = self.bq.query(
            q,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("s", "DATE", start_date),
                    bigquery.ScalarQueryParameter("e", "DATE", end_date),
                ]
            ),
        )
        return job.to_dataframe()

    # ---- Helper metrics ----

    @staticmethod
    def _efa_hours() -> float:
        return 4.0  # 4 hours per EFA block

    def _estimate_degradation_cost(self) -> float:
        """
        Simple assumption: 1 full cycle/day spread across 6 EFA blocks.
        """
        cycle_cost = self.asset.energy_mwh * self.asset.degradation_cost_per_mwh
        return cycle_cost / 6.0

    @staticmethod
    def _imbalance_penalty_from_df(df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        df = df.dropna(subset=["sbp", "ssp"])
        if df.empty:
            return 0.0
        spread = (df["sbp"] - df["ssp"]).abs().mean()
        return float(spread * 0.05)  # tuned factor

    @staticmethod
    def _volatility_penalty_from_df(df: pd.DataFrame) -> float:
        if df.empty or "cashout_price" not in df.columns:
            return 0.0
        df = df.dropna(subset=["cashout_price"])
        if df.empty:
            return 0.0
        vol = df["cashout_price"].std()
        return float(vol * 0.02)

    @staticmethod
    def _boa_opp_cost_from_df(df: pd.DataFrame, asset_mw: float, efa_hours: float) -> float:
        if df.empty:
            return 0.0
        df = df.dropna(subset=["acceptance_price"])
        if df.empty:
            return 0.0
        mean_price = df["acceptance_price"].mean()
        utilisation_factor = 0.25  # assume some fraction of block used
        return float(mean_price * asset_mw * efa_hours * utilisation_factor)

    # ---- Main optimisation ----

    def optimise_fr_vs_bm(
        self,
        start_date: date,
        end_date: date,
        asset: Optional[BESSAsset] = None
    ) -> Tuple[pd.DataFrame, List[Tuple[datetime, float, float]]]:
        """
        Returns:
            schedule: DataFrame with one row per EFA block
            soc_history: list of (timestamp, soc_mwh, soc_pct)
        """
        if asset is None:
            asset = self.asset

        fr = self._fetch_fr_prices(start_date, end_date)
        if fr.empty:
            logging.warning("No FR data available; nothing to optimise.")
            return pd.DataFrame(), []

        sys_prices = self.fetch_system_prices(start_date, end_date)
        boas = self._fetch_boas(start_date, end_date)

        efa_hours = self._efa_hours()
        base_deg_cost = self._estimate_degradation_cost()

        fr_pivot = fr.pivot_table(
            index=["date", "efa_block"],
            columns="service",
            values="clearing_price",
            aggfunc="mean"
        ).reset_index()
        fr_pivot.columns.name = None

        for col in ["DC", "DM", "DR"]:
            if col not in fr_pivot.columns:
                fr_pivot[col] = None

        results = []
        soc_history: List[Tuple[datetime, float, float]] = []

        for _, row in fr_pivot.iterrows():
            d = row["date"]
            efa = int(row["efa_block"])
            dc_price = row.get("DC", None)
            dm_price = row.get("DM", None)
            dr_price = row.get("DR", None)

            block_start = datetime.combine(d, datetime.min.time()) + timedelta(hours=(efa - 1) * 4)
            block_end = block_start + timedelta(hours=4)

            sp_block = sys_prices[
                (sys_prices["timestamp"] >= block_start) &
                (sys_prices["timestamp"] < block_end)
            ]
            boa_block = boas[
                (boas["timestamp"] >= block_start) &
                (boas["timestamp"] < block_end)
            ]

            imbalance_penalty = self._imbalance_penalty_from_df(sp_block)
            volatility_penalty = self._volatility_penalty_from_df(sp_block)
            boa_opp_cost = self._boa_opp_cost_from_df(boa_block, asset.p_max_mw, efa_hours)

            def fr_rev(p: Optional[float]) -> float:
                if p is None or (isinstance(p, float) and math.isnan(p)):
                    return 0.0
                return float(p * asset.p_max_mw * efa_hours)

            # Services list based on SoC
            services: List[str] = []
            if self.soc.can_provide_fr(efa_hours):
                services += ["DC", "DM", "DR"]
            else:
                logging.info(
                    f"SoC {self.soc.soc_mwh:.2f} MWh out of range; skipping FR for {d} EFA {efa}"
                )

            services += ["IDLE", "ARBITRAGE"]

            arb = self.arb_engine.compute_arbitrage_margin(sp_block, self.soc, efa_hours)
            margins: Dict[str, float] = {}

            for svc in services:
                if svc in ["DC", "DM", "DR"]:
                    price = {"DC": dc_price, "DM": dm_price, "DR": dr_price}[svc]
                    revenue = fr_rev(price)
                    deg_cost = base_deg_cost
                    net_margin = (
                        revenue
                        - deg_cost
                        - boa_opp_cost
                        - imbalance_penalty
                        - volatility_penalty
                    )
                elif svc == "ARBITRAGE":
                    net_margin = arb["margin"]
                elif svc == "IDLE":
                    net_margin = 0.0
                else:
                    net_margin = 0.0

                margins[svc] = net_margin

            chosen_service = max(margins, key=margins.get)
            chosen_net = margins[chosen_service]

            # Update SoC based on chosen action
            if chosen_service == "ARBITRAGE":
                if arb["action"] == "DISCHARGE":
                    self.soc.discharge(asset.p_max_mw, efa_hours, asset.round_trip_efficiency)
                elif arb["action"] == "CHARGE":
                    self.soc.charge(asset.p_max_mw, efa_hours, asset.round_trip_efficiency)
            # FR and IDLE assumed net-neutral SoC for this minimal model

            soc_pct = 100.0 * self.soc.soc_mwh / self.soc.max_mwh if self.soc.max_mwh > 0 else 0.0
            soc_history.append((block_start, self.soc.soc_mwh, soc_pct))

            results.append({
                "date": d,
                "efa_block": efa,
                "dc_price": dc_price,
                "dm_price": dm_price,
                "dr_price": dr_price,
                "fr_revenue_if_dc": fr_rev(dc_price),
                "fr_revenue_if_dm": fr_rev(dm_price),
                "fr_revenue_if_dr": fr_rev(dr_price),
                "deg_cost": base_deg_cost,
                "boa_opp_cost": boa_opp_cost,
                "imbalance_penalty": imbalance_penalty,
                "volatility_penalty": volatility_penalty,
                "net_margin_idle": margins.get("IDLE", 0.0),
                "net_margin_dc": margins.get("DC", 0.0),
                "net_margin_dm": margins.get("DM", 0.0),
                "net_margin_dr": margins.get("DR", 0.0),
                "net_margin_arb": margins.get("ARBITRAGE", 0.0),
                "arb_action": arb["action"],
                "chosen_service": chosen_service,
                "chosen_net_margin": chosen_net,
            })

        schedule = pd.DataFrame(results)
        logging.info(f"Optimised {len(schedule)} EFA blocks.")
        return schedule, soc_history

# =============================================================================
# KPI CALCULATION (FR + CM + VLP + Arbitrage estimate)
# =============================================================================

def compute_capacity_market_revenue(asset: BESSAsset) -> float:
    kw = asset.p_max_mw * 1000
    return kw * DERATED_FACTOR * CM_PRICE


def compute_vlp_revenue(system_prices_df: pd.DataFrame, asset: BESSAsset) -> float:
    """
    Simple VLP proxy: value from responding to imbalance spread.
    """
    if system_prices_df.empty:
        return 0.0
    df = system_prices_df.dropna(subset=["ssp", "sbp"]).copy()
    if df.empty:
        return 0.0
    df["spread"] = (df["sbp"] - df["ssp"]).abs()
    performance_factor = 0.20  # 20% of hours effectively used for VLP
    revenue = (
        df["spread"].mean()
        * asset.p_max_mw
        * performance_factor
        * 365.0
        * 24.0
    )
    return float(revenue)


def compute_kpis(
    schedule: pd.DataFrame,
    asset: BESSAsset,
    sys_prices: pd.DataFrame
) -> Dict[str, float]:
    if schedule.empty:
        return {
            "fr_net_margin_total": 0.0,
            "fr_net_margin_per_year": 0.0,
            "fr_blocks_active": 0,
            "fr_blocks_total": 0,
            "fr_idle_blocks": 0,
            "avg_boa_opp_cost": 0.0,
            "avg_imbalance_penalty": 0.0,
            "avg_volatility_penalty": 0.0,
            "cm_annual": 0.0,
            "vlp_annual": 0.0,
            "arb_annual": 0.0,
        }

    fr_blocks = schedule[schedule["chosen_service"].isin(["DC", "DM", "DR"])]
    arb_blocks = schedule[schedule["chosen_service"] == "ARBITRAGE"]
    idle_blocks = schedule[schedule["chosen_service"] == "IDLE"]

    total_fr_net = float(fr_blocks["chosen_net_margin"].sum())
    total_arb_net = float(arb_blocks["chosen_net_margin"].sum())
    blocks_count = len(schedule)

    unique_days = schedule["date"].nunique()
    annual_factor = (365.0 / unique_days) if unique_days else 0.0
    annual_fr_net = total_fr_net * annual_factor
    annual_arb_net = total_arb_net * annual_factor

    cm_annual = compute_capacity_market_revenue(asset)
    vlp_annual = compute_vlp_revenue(sys_prices, asset)

    kpis = {
        "fr_net_margin_total": total_fr_net,
        "fr_net_margin_per_year": annual_fr_net,
        "arb_net_margin_total": total_arb_net,
        "arb_annual": annual_arb_net,
        "fr_blocks_active": len(fr_blocks),
        "fr_blocks_total": blocks_count,
        "fr_idle_blocks": len(idle_blocks),
        "avg_boa_opp_cost": float(schedule["boa_opp_cost"].mean()),
        "avg_imbalance_penalty": float(schedule["imbalance_penalty"].mean()),
        "avg_volatility_penalty": float(schedule["volatility_penalty"].mean()),
        "cm_annual": cm_annual,
        "vlp_annual": vlp_annual,
    }
    return kpis

# =============================================================================
# GOOGLE SHEETS HELPERS
# =============================================================================

def ensure_sheet_exists(sh: gspread.Spreadsheet, title: str) -> None:
    try:
        sh.worksheet(title)
    except gspread.WorksheetNotFound:
        sh.add_worksheet(title, rows="2000", cols="10")

# =============================================================================
# GOOGLE SHEETS: DASHBOARD & CHARTS
# =============================================================================

def update_dashboard(schedule: pd.DataFrame, kpis: Dict[str, float]) -> None:
    client = make_sheets_client()
    sh = client.open_by_key(DASHBOARD_SHEET_ID)
    ws = sh.worksheet(DASHBOARD_TAB_NAME)

    kpi_text = (
        f"FR Net Margin (period): £{kpis['fr_net_margin_total']:,.0f} | "
        f"FR Annualised: £{kpis['fr_net_margin_per_year']:,.0f} | "
        f"Arb Annualised: £{kpis['arb_annual']:,.0f} | "
        f"CM: £{kpis['cm_annual']:,.0f} | "
        f"VLP: £{kpis['vlp_annual']:,.0f} | "
        f"FR Blocks: {kpis['fr_blocks_active']}/{kpis['fr_blocks_total']} | "
        f"Avg BOA Opp: £{kpis['avg_boa_opp_cost']:.2f}"
    )
    ws.update(DASHBOARD_KPI_CELL, kpi_text)

    start_row = int(''.join(filter(str.isdigit, DASHBOARD_SUMMARY_START)))
    start_col = ord(DASHBOARD_SUMMARY_START[0].upper()) - ord('A') + 1

    headers = [[
        "Date", "EFA Block", "Chosen Service", "Net Margin (£)",
        "FR_if_DC", "FR_if_DM", "FR_if_DR",
        "Deg Cost", "BOA Opp (£)", "Imbalance (£)", "Volatility (£)", "Arb Action"
    ]]
    ws.update((start_row, start_col), headers)

    max_rows = 200
    sub = schedule.head(max_rows)
    rows = []
    for _, r in sub.iterrows():
        rows.append([
            str(r["date"]),
            int(r["efa_block"]),
            r["chosen_service"],
            float(r["chosen_net_margin"]),
            float(r["fr_revenue_if_dc"]),
            float(r["fr_revenue_if_dm"]),
            float(r["fr_revenue_if_dr"]),
            float(r["deg_cost"]),
            float(r["boa_opp_cost"]),
            float(r["imbalance_penalty"]),
            float(r["volatility_penalty"]),
            r["arb_action"],
        ])
    ws.update((start_row + 1, start_col), rows)

    logging.info("Dashboard KPI + summary updated.")

def write_soc_history_to_sheets(soc_history: List[Tuple[datetime, float, float]]) -> None:
    client = make_sheets_client()
    sh = client.open_by_key(DASHBOARD_SHEET_ID)
    ensure_sheet_exists(sh, "SoC_History")
    ws = sh.worksheet("SoC_History")

    rows = [["Timestamp", "SoC (MWh)", "SoC (%)"]]
    for t, soc_mwh, soc_pct in soc_history:
        rows.append([t.isoformat(), soc_mwh, soc_pct])

    ws.clear()
    ws.update("A1", rows)
    logging.info("SoC history written to SoC_History sheet.")

def create_soc_chart() -> None:
    client = make_sheets_client()
    sh = client.open_by_key(DASHBOARD_SHEET_ID)
    ws = sh.worksheet("SoC_History")

    body = {
        "requests": [{
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Daily SoC Profile",
                        "basicChart": {
                            "chartType": "LINE",
                            "legendPosition": "BOTTOM_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": "Time"},
                                {"position": "LEFT_AXIS", "title": "SoC (%)"},
                            ],
                            "domains": [{
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": ws.id,
                                        "startRowIndex": 1,
                                        "startColumnIndex": 0,
                                        "endColumnIndex": 1
                                    }]
                                }
                            }],
                            "series": [{
                                "targetAxis": "LEFT_AXIS",
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": ws.id,
                                        "startRowIndex": 1,
                                        "startColumnIndex": 2,
                                        "endColumnIndex": 3
                                    }]
                                }
                            }]
                        }
                    },
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {
                                "sheetId": ws.id,
                                "rowIndex": 2,
                                "columnIndex": 4
                            }
                        }
                    }
                }
            }
        }]
    }
    sh.batch_update(body)
    logging.info("SoC chart created (SoC_History).")

def make_fr_mix_chart(schedule: pd.DataFrame) -> None:
    client = make_sheets_client()
    sh = client.open_by_key(DASHBOARD_SHEET_ID)
    ensure_sheet_exists(sh, "FR_Mix")
    ws = sh.worksheet("FR_Mix")

    mix = schedule["chosen_service"].value_counts().reset_index()
    mix.columns = ["Service", "Blocks"]
    rows = [["Service", "Blocks"]] + mix.values.tolist()

    ws.clear()
    ws.update("A1", rows)

    body = {
        "requests": [{
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "FR Service Mix",
                        "pieChart": {
                            "legendPosition": "RIGHT_LEGEND",
                            "domain": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": ws.id,
                                        "startRowIndex": 1,
                                        "startColumnIndex": 0,
                                        "endColumnIndex": 1
                                    }]
                                }
                            },
                            "series": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": ws.id,
                                        "startRowIndex": 1,
                                        "startColumnIndex": 1,
                                        "endColumnIndex": 2
                                    }]
                                }
                            }
                        }
                    },
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {
                                "sheetId": ws.id,
                                "rowIndex": 2,
                                "columnIndex": 3
                            }
                        }
                    }
                }
            }
        }]
    }
    sh.batch_update(body)
    logging.info("FR service mix chart created (FR_Mix).")

def make_arbitrage_chart(schedule: pd.DataFrame) -> None:
    client = make_sheets_client()
    sh = client.open_by_key(DASHBOARD_SHEET_ID)
    ensure_sheet_exists(sh, "Arbitrage_Cycles")
    ws = sh.worksheet("Arbitrage_Cycles")

    arb = schedule[schedule["chosen_service"] == "ARBITRAGE"].copy()
    rows = [["Date", "EFA Block", "Net Margin (£)"]]
    for _, r in arb.iterrows():
        rows.append([
            str(r["date"]),
            int(r["efa_block"]),
            float(r["chosen_net_margin"])
        ])

    ws.clear()
    ws.update("A1", rows)
    logging.info("Arbitrage cycles written (Arbitrage_Cycles).")
    # Chart can be added similarly if wanted.

def write_system_prices_chart(sys_prices: pd.DataFrame) -> None:
    client = make_sheets_client()
    sh = client.open_by_key(DASHBOARD_SHEET_ID)
    ensure_sheet_exists(sh, "System_Prices")
    ws = sh.worksheet("System_Prices")

    rows = [["Timestamp", "SSP", "SBP"]]
    for _, r in sys_prices.iterrows():
        rows.append([
            r["timestamp"].isoformat(),
            r.get("ssp", None),
            r.get("sbp", None),
        ])

    ws.clear()
    ws.update("A1", rows)
    logging.info("System prices written (System_Prices).")

def write_annual_projection(kpis: Dict[str, float]) -> None:
    client = make_sheets_client()
    sh = client.open_by_key(DASHBOARD_SHEET_ID)
    ensure_sheet_exists(sh, "Annual_Projection")
    ws = sh.worksheet("Annual_Projection")

    total = (
        kpis["fr_net_margin_per_year"]
        + kpis.get("arb_annual", 0.0)
        + kpis.get("cm_annual", 0.0)
        + kpis.get("vlp_annual", 0.0)
    )

    rows = [
        ["Revenue Stream", "Annual Revenue (£)"],
        ["Frequency Response (FR)", kpis["fr_net_margin_per_year"]],
        ["Arbitrage", kpis.get("arb_annual", 0.0)],
        ["Capacity Market", kpis.get("cm_annual", 0.0)],
        ["VLP Flexibility", kpis.get("vlp_annual", 0.0)],
        ["TOTAL", total],
    ]
    ws.clear()
    ws.update("A1", rows)
    logging.info("Annual projection written (Annual_Projection).")

# =============================================================================
# CLI & MAIN
# =============================================================================

def parse_dates_from_args() -> Tuple[date, date]:
    """
    Allow:
        python bess_revenue_engine.py
        python bess_revenue_engine.py 2025-01-01 2025-01-31
    """
    if len(sys.argv) == 3:
        s = date.fromisoformat(sys.argv[1])
        e = date.fromisoformat(sys.argv[2])
    else:
        e = datetime.utcnow().date()
        s = e - timedelta(days=30)
    return s, e

def main() -> None:
    logging.info("Starting BESS Revenue Engine (single-file).")

    start_date, end_date = parse_dates_from_args()
    logging.info(f"Using date range: {start_date} → {end_date}")

    # 1) Ingest data (you can disable in cron if you ingest separately)
    try:
        ingest_neso_fr(start_date, end_date)
    except Exception as e:
        logging.warning(f"NESO FR ingestion failed (continuing with existing data): {e}")

    try:
        ingest_bmrs_system_prices(start_date, end_date)
    except Exception as e:
        logging.warning(f"System price ingestion failed (continuing with existing data): {e}")

    try:
        ingest_bmrs_boas(start_date, end_date)
    except Exception as e:
        logging.warning(f"BOA ingestion failed (continuing with existing data): {e}")

    # 2) Optimise
    optimiser = FRBMOptimiser(DEFAULT_ASSET)
    schedule, soc_history = optimiser.optimise_fr_vs_bm(start_date, end_date, DEFAULT_ASSET)

    if schedule.empty:
        logging.error("Schedule is empty; nothing to compute or update.")
        return

    # 3) Fetch system prices again for VLP / charts
    sys_prices = optimiser.fetch_system_prices(start_date, end_date)

    # 4) Compute KPIs (FR + CM + VLP + Arb)
    kpis = compute_kpis(schedule, DEFAULT_ASSET, sys_prices)
    logging.info("KPIs computed:")
    for k, v in kpis.items():
        logging.info(f"  {k}: {v}")

    # 5) Update Sheets: dashboard, SoC history, charts, projections
    try:
        update_dashboard(schedule, kpis)
        write_soc_history_to_sheets(soc_history)
        create_soc_chart()
        make_fr_mix_chart(schedule)
        make_arbitrage_chart(schedule)
        write_system_prices_chart(sys_prices)
        write_annual_projection(kpis)
    except Exception as e:
        logging.error(f"Failed to update Google Sheets: {e}")

    logging.info("BESS Revenue Engine complete.")

if __name__ == "__main__":
    main()