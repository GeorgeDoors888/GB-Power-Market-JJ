#!/usr/bin/env python3
"""
TCR Charge Model - Non-Energy Cost Calculator
Calculates TNUoS, DNUoS, BSUoS, RO, FiT, CfD, CCL, and other levies
for 2025-2030 scenarios (central/high/low)

Supports PV+BESS savings estimation via volumetric reduction
"""

from dataclasses import dataclass
from typing import Dict, Tuple
import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

@dataclass
class SiteMeta:
    site_id: str
    year: int
    scenario: str  # 'central', 'high', 'low'
    tnuos_zone: str
    tnuos_band: str
    tnuos_voltage: str
    dno: str
    duos_region: str
    duos_band: str
    voltage_level: str  # HV, LV, EHV

class TCRChargeModel:
    def __init__(self, bq_client: bigquery.Client):
        self.bq = bq_client

    def _load_levy_rates(self, year: int, scenario: str) -> pd.DataFrame:
        """Load non-energy levy rates (RO, FiT, CfD, BSUoS, CCL, etc.)"""
        q = f"""
        SELECT component, rate_gbp_per_mwh
        FROM `{PROJECT_ID}.{DATASET}.non_energy_levy_rates`
        WHERE year = @year AND scenario = @scenario
        """
        job = self.bq.query(
            q,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("year", "INT64", year),
                    bigquery.ScalarQueryParameter("scenario", "STRING", scenario),
                ]
            ),
        )
        return job.to_dataframe()

    def _load_tnuos_fixed(self, meta: SiteMeta) -> float:
        """Load TNUoS fixed charge (£/year) by zone/band/voltage"""
        q = f"""
        SELECT fixed_annual_charge_gbp
        FROM `{PROJECT_ID}.{DATASET}.tcr_tnuos_demand_bands`
        WHERE zone = @zone
          AND voltage_group = @voltage
          AND band = @band
          AND @year BETWEEN EXTRACT(YEAR FROM valid_from)
                       AND EXTRACT(YEAR FROM valid_to)
        LIMIT 1
        """
        job = self.bq.query(
            q,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("zone", "STRING", meta.tnuos_zone),
                    bigquery.ScalarQueryParameter("voltage", "STRING", meta.tnuos_voltage),
                    bigquery.ScalarQueryParameter("band", "STRING", meta.tnuos_band),
                    bigquery.ScalarQueryParameter("year", "INT64", meta.year),
                ]
            ),
        )
        df = job.to_dataframe()
        return float(df["fixed_annual_charge_gbp"][0]) if not df.empty else 0.0

    def _load_dnuos_fixed(self, meta: SiteMeta) -> float:
        """Load DNUoS (DUoS) fixed residual charge (£/year) by DNO/region/band"""
        q = f"""
        SELECT fixed_annual_charge_gbp
        FROM `{PROJECT_ID}.{DATASET}.tcr_dnuos_residual_bands`
        WHERE dno = @dno
          AND region_code = @region
          AND voltage_group = @voltage
          AND band = @band
          AND @year BETWEEN EXTRACT(YEAR FROM valid_from)
                       AND EXTRACT(YEAR FROM valid_to)
        LIMIT 1
        """
        job = self.bq.query(
            q,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("dno", "STRING", meta.dno),
                    bigquery.ScalarQueryParameter("region", "STRING", meta.duos_region),
                    bigquery.ScalarQueryParameter("voltage", "STRING", meta.tnuos_voltage),
                    bigquery.ScalarQueryParameter("band", "STRING", meta.duos_band),
                    bigquery.ScalarQueryParameter("year", "INT64", meta.year),
                ]
            ),
        )
        df = job.to_dataframe()
        return float(df["fixed_annual_charge_gbp"][0]) if not df.empty else 0.0

    def _load_import_mwh(self, site_id: str, year: int) -> float:
        """Load total annual import MWh for site"""
        q = f"""
        SELECT total_import_mwh
        FROM `{PROJECT_ID}.{DATASET}.v_import_by_site_year`
        WHERE site_id = @site_id AND year = @year
        """
        job = self.bq.query(
            q,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("site_id", "STRING", site_id),
                    bigquery.ScalarQueryParameter("year", "INT64", year),
                ]
            ),
        )
        df = job.to_dataframe()
        return float(df["total_import_mwh"][0]) if not df.empty else 0.0

    def calculate_charges(self, meta: SiteMeta) -> Dict[str, float]:
        """
        Calculate all non-energy charges for a site/year/scenario
        Returns dict with component-level and total charges
        """
        import_mwh = self._load_import_mwh(meta.site_id, meta.year)
        
        # Fixed charges (per site, not volumetric)
        tnuos_fixed = self._load_tnuos_fixed(meta)
        dnuos_fixed = self._load_dnuos_fixed(meta)
        
        # Volumetric levies
        levy_df = self._load_levy_rates(meta.year, meta.scenario)
        levies = {}
        for _, row in levy_df.iterrows():
            comp = row["component"]
            rate = float(row["rate_gbp_per_mwh"])
            levies[comp] = rate * import_mwh
        
        total = tnuos_fixed + dnuos_fixed + sum(levies.values())
        
        return {
            "site_id": meta.site_id,
            "year": meta.year,
            "scenario": meta.scenario,
            "import_mwh": import_mwh,
            "tnuos_fixed_gbp": tnuos_fixed,
            "dnuos_fixed_gbp": dnuos_fixed,
            **{f"{k}_gbp": v for k, v in levies.items()},
            "total_non_energy_gbp": total,
            "non_energy_gbp_per_mwh": (total / import_mwh) if import_mwh > 0 else 0.0,
        }


def run_scenarios_for_site(site_id: str) -> pd.DataFrame:
    """
    Run TCR charge calculations for all years (2025-2030) and scenarios (central/high/low)
    Returns DataFrame with 18 rows (6 years × 3 scenarios)
    """
    client = bigquery.Client(project=PROJECT_ID)
    model = TCRChargeModel(client)

    # Load site metadata
    q_meta = f"""
    SELECT site_id, tnuos_zone, tcr_tnuos_band, voltage_group,
           dno, duos_region, tcr_dnuos_band
    FROM `{PROJECT_ID}.{DATASET}.site_static_attributes`
    WHERE site_id = @site_id
    """
    job = client.query(
        q_meta,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("site_id", "STRING", site_id)
            ]
        ),
    )
    meta_df = job.to_dataframe()
    if meta_df.empty:
        raise ValueError(f"No metadata for site {site_id}")

    row = meta_df.iloc[0]

    results = []
    for year in range(2025, 2031):
        for scenario in ["central", "high", "low"]:
            meta = SiteMeta(
                site_id=site_id,
                year=year,
                scenario=scenario,
                tnuos_zone=row["tnuos_zone"],
                tnuos_band=row["tcr_tnuos_band"],
                tnuos_voltage=row["voltage_group"],
                dno=row["dno"],
                duos_region=row["duos_region"],
                duos_band=row["tcr_dnuos_band"],
                voltage_level=row.get("voltage_level", "HV"),
            )
            charges = model.calculate_charges(meta)
            results.append(charges)

    return pd.DataFrame(results)


def estimate_pv_bess_savings(
    site_meta: SiteMeta,
    pv_size_mw: float,
    bess_power_mw: float,
    bess_energy_mwh: float,
    duos_red_p_kwh: float = 20.0,
    duos_amber_p_kwh: float = 6.0,
    duos_green_p_kwh: float = 1.0
) -> Dict[str, float]:
    """
    Simplified PV+BESS savings estimation
    Assumes:
    - PV reduces daytime import (amber/green periods)
    - BESS shifts load away from red periods
    - Returns baseline vs with-PV-BESS charges
    """
    client = bigquery.Client(project=PROJECT_ID)
    model = TCRChargeModel(client)
    
    # Baseline charges
    baseline = model.calculate_charges(site_meta)
    
    # Estimate import reduction
    # PV ~1000 MWh/MW/yr in UK, BESS shifts ~500 MWh/yr from red to off-peak
    pv_annual_mwh = pv_size_mw * 1000
    bess_shift_mwh = bess_energy_mwh * 365 * 0.5  # ~0.5 cycles/day
    
    # Reduced import
    reduced_import_mwh = baseline["import_mwh"] - pv_annual_mwh
    
    # DUoS savings (red avoidance)
    red_avoidance_mwh = min(bess_shift_mwh, baseline["import_mwh"] * 0.15)  # ~15% red
    duos_savings_gbp = red_avoidance_mwh * (duos_red_p_kwh - duos_green_p_kwh) / 100 * 1000
    
    # Levy savings (proportional to import reduction)
    levy_savings_pct = (pv_annual_mwh / baseline["import_mwh"]) if baseline["import_mwh"] > 0 else 0
    levy_components = [k for k in baseline.keys() if k.endswith('_gbp') and k not in ['tnuos_fixed_gbp', 'dnuos_fixed_gbp', 'total_non_energy_gbp']]
    
    levy_savings_gbp = sum(baseline[k] * levy_savings_pct for k in levy_components if k in baseline)
    
    # Total savings
    total_savings_gbp = duos_savings_gbp + levy_savings_gbp
    
    return {
        "site_id": site_meta.site_id,
        "year": site_meta.year,
        "scenario": site_meta.scenario,
        "baseline_total_gbp": baseline["total_non_energy_gbp"],
        "with_pv_bess_total_gbp": baseline["total_non_energy_gbp"] - total_savings_gbp,
        "savings_gbp": total_savings_gbp,
        "savings_pct": 100 * total_savings_gbp / baseline["total_non_energy_gbp"] if baseline["total_non_energy_gbp"] > 0 else 0,
        "baseline_gbp_per_mwh": baseline["non_energy_gbp_per_mwh"],
        "with_pv_bess_gbp_per_mwh": (baseline["total_non_energy_gbp"] - total_savings_gbp) / reduced_import_mwh if reduced_import_mwh > 0 else 0,
        "duos_savings_gbp": duos_savings_gbp,
        "levy_savings_gbp": levy_savings_gbp,
    }


if __name__ == "__main__":
    # Example: Run TCR scenarios for a site
    site_id = "SITE_001"
    
    try:
        df = run_scenarios_for_site(site_id)
        print(f"\n📊 TCR Charge Forecasts for {site_id} (2025-2030)")
        print("=" * 80)
        print(df[['year', 'scenario', 'total_non_energy_gbp', 'non_energy_gbp_per_mwh']].to_string())
    except Exception as e:
        print(f"⚠️  Error: {e}")
