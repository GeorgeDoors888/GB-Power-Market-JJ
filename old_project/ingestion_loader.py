# ingestion_loader.py (routing section)
import re
from dataclasses import dataclass
from typing import Optional, Iterable, List, Tuple

PROJECT = "jibber-jabber-knowledge"
DATASET = "uk_energy_prod"  # Production dataset in europe-west2 region

def t(table_name: str) -> str:
    return f"{PROJECT}.{DATASET}.{table_name}"

@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern
    table: str

# Helper: build a regex anchored to bucket-root or after gs://bucket/
def rx(prefix: str, ext: str = r"(csv|json)"):
    # Matches:
    #  - exact prefix (with any subfolders/files under it)
    #  - handles gs://bucket/… or relative paths
    #  - insists on a file extension at the end
    #
    # Example: prefix="bmrs_data/fuelinst/" ->
    #   r"(^|/)bmrs_data/fuelinst/.+\.((csv|json))$"
    return re.compile(rf"(^|/){re.escape(prefix)}.+\.{ext}$", re.IGNORECASE)

# ---------------------------
# Concrete routing rules
# ---------------------------
RULES: List[Rule] = [
    # ---------- Core BMRS (legacy & extended) ----------
    Rule("bmrs_bod",              rx("bmrs_data/bid_offer_acceptances/", "json"),           t("elexon_bid_offer_acceptances")),
    Rule("bmrs_demand_outturn",   rx("bmrs_data/demand_outturn/", "json"),                  t("elexon_demand_outturn")),
    Rule("bmrs_generation_out",   rx("bmrs_data/generation_outturn/", "json"),              t("elexon_generation_outturn")),
    Rule("bmrs_system_warnings",  rx("bmrs_data/system_warnings/", "json"),                 t("elexon_system_warnings")),

    Rule("bmrs_fuelinst",         rx("bmrs_data/fuelinst/"),                                t("bmrs_fuelinst")),
    Rule("bmrs_frequency",        rx("bmrs_data/frequency/"),                               t("elexon_frequency")),
    Rule("bmrs_market_index",     rx("bmrs_data/market_index/"),                            t("elexon_market_index")),      # MELNGC family
    Rule("bmrs_netbsad",          rx("bmrs_data/netbsad/"),                                 t("elexon_netbsad")),
    Rule("bmrs_disbsad",          rx("bmrs_data/disbsad/"),                                 t("elexon_disbsad")),
    Rule("bmrs_nonbm",            rx("bmrs_data/nonbm/"),                                   t("elexon_nonbm")),
    Rule("bmrs_qas",              rx("bmrs_data/qas/"),                                     t("elexon_qas")),
    Rule("bmrs_temp_fc",          rx("bmrs_data/temp_forecasts/"),                          t("elexon_temp_forecasts")),
    Rule("bmrs_wind_fc_legacy",   rx("bmrs_data/wind_forecasts_legacy/"),                   t("elexon_wind_forecasts_legacy")),
    Rule("bmrs_individual_gen",   rx("bmrs_data/individual_generation/"),                   t("elexon_individual_generation")),

    # ---------- NESO core & extended ----------
    Rule("neso_demand",           rx("neso_data/demand/"),                                  t("neso_demand_forecasts")),
    Rule("neso_wind",             rx("neso_data/wind/"),                                    t("neso_wind_forecasts")),
    Rule("neso_carbon_nat",       rx("neso_data/carbon/"),                                  t("neso_carbon_intensity")),
    Rule("neso_carbon_reg",       rx("neso_data/carbon_regional/"),                         t("neso_carbon_intensity_regional")),
    Rule("neso_balancing",        rx("neso_data/balancing_services/"),                      t("neso_balancing_services")),
    Rule("neso_ic_flows",         rx("neso_data/interconnector_flows/"),                    t("neso_interconnector_flows")),
    Rule("neso_inertia",          rx("neso_data/inertia/"),                                 t("neso_inertia")),
    Rule("neso_constraint_det",   rx("neso_data/constraint_detail/"),                       t("neso_constraint_detail")),
    Rule("neso_dynamic_srv",      rx("neso_data/dynamic_services/"),                        t("neso_dynamic_services")),
    Rule("neso_opmr",             rx("neso_data/opmr/"),                                    t("neso_opmr")),
    Rule("neso_nrapm",            rx("neso_data/nrapm/"),                                   t("neso_nrapm")),
    Rule("neso_voltage_reqs",     rx("neso_data/voltage_requirements/"),                    t("neso_voltage_requirements")),
    Rule("neso_demand_perf",      rx("neso_data/demand_forecast/performance/"),             t("neso_demand_forecast_performance")),
    Rule("neso_outages",          rx("neso_data/outages/"),                                 t("neso_outages")),
    Rule("neso_geo_gsp",          rx("neso_data/geography/gsp/"),                           t("neso_geography_gsp")),
    Rule("neso_geo_dno",          rx("neso_data/geography/dno_zones/"),                     t("neso_geography_dno_zones")),

    # FES families (split into explicit tables for clarity/partitioning)
    Rule("neso_fes_es1",          rx("neso_data/fes/es1/"),                                 t("neso_future_scenarios_es1")),
    Rule("neso_fes_flx1",         rx("neso_data/fes/flx1/"),                                t("neso_future_scenarios_flx1")),
    Rule("neso_fes_ws1",          rx("neso_data/fes/ws1/"),                                 t("neso_future_scenarios_ws1")),
    Rule("neso_fes_blocks",       rx("neso_data/fes/building_blocks/"),                     t("neso_future_scenarios_building_blocks")),

    Rule("neso_capacity_margin",  rx("neso_data/capacity_margin/"),                         t("neso_capacity_margin")),
    Rule("neso_gas_day_ahead",    rx("neso_data/gas_day_ahead/"),                           t("neso_gas_day_ahead")),

    # ---------- Market prices ----------
    Rule("market_wholesale",      rx("market_prices/wholesale/"),                           t("market_prices_wholesale")),

    # ---------- Optional future enrichment ----------
    # Rule("enrich_gas_da",      rx("enrichment/gas_day_ahead_prices/"),                    t("enrichment_gas_day_ahead_prices")),
    # Rule("enrich_capacity",    rx("enrichment/capacity_margin/"),                         t("enrichment_capacity_margin")),
]

def map_object_to_table(obj_name: str) -> Optional[str]:
    """
    Return fully-qualified table for a GCS object path based on regex rules,
    or None if no rule matches.
    """
    obj = obj_name
    if obj.startswith("gs://"):
        parts = obj.split("/", 3)
        obj = parts[3] if len(parts) >= 4 else ""
    for rule in RULES:
        if rule.pattern.search(obj):
            return rule.table
    return None

# ---------------------------
# Minimal required-field guards (tweak incrementally)
# ---------------------------
REQUIRED_FIELDS = {
    t("elexon_bid_offer_acceptances"): {"timestamp", "settlement_date", "settlement_period", "bmu_id"},
    t("elexon_demand_outturn"):        {"settlement_date", "settlement_period", "national_demand"},
    t("elexon_generation_outturn"):    {"settlement_date", "settlement_period", "fuel_type", "generation_mw"},
    t("elexon_system_warnings"):       {"timestamp", "warning_type"},

    t("bmrs_fuelinst"):                {"timestamp", "fuel_type", "generation_mw"},
    t("elexon_frequency"):             {"timestamp", "frequency_hz"},
    t("elexon_market_index"):          {"timestamp"},  # MELNGC varies; tighten when you finalize schema
    t("elexon_netbsad"):               {"timestamp"},
    t("elexon_disbsad"):               {"timestamp"},
    t("elexon_nonbm"):                 {"timestamp"},
    t("elexon_qas"):                   {"timestamp"},
    t("elexon_temp_forecasts"):        {"settlement_date", "settlement_period", "temperature_forecast"},
    t("elexon_wind_forecasts_legacy"): {"settlement_date", "settlement_period"},
    t("elexon_individual_generation"): {"settlement_date", "settlement_period", "bmu_id"},

    t("neso_demand_forecasts"):              {"settlement_date", "settlement_period", "national_demand_forecast"},
    t("neso_wind_forecasts"):                {"settlement_date", "settlement_period"},
    t("neso_carbon_intensity"):              {"timestamp", "carbon_intensity_gco2_kwh"},
    t("neso_carbon_intensity_regional"):     {"timestamp", "region_code", "carbon_intensity_gco2_kwh"},
    t("neso_balancing_services"):            {"charge_date", "settlement_period"},
    t("neso_interconnector_flows"):          {"trading_date", "settlement_period", "interconnector_name"},
    t("neso_inertia"):                       {"timestamp", "inertia_gva_s"},
    t("neso_constraint_detail"):             {"constraint_date"},   # refine as schema stabilizes
    t("neso_dynamic_services"):              {"timestamp"},
    t("neso_opmr"):                          {"requirement_date"},
    t("neso_nrapm"):                         {"timestamp"},
    t("neso_voltage_requirements"):          {"requirement_date", "region_code"},
    t("neso_demand_forecast_performance"):   {"settlement_date", "settlement_period"},
    t("neso_outages"):                       {"timestamp"},
    t("neso_geography_gsp"):                 {"gsp_id", "longitude", "latitude"},
    t("neso_geography_dno_zones"):           {"dno_area"},
    t("neso_future_scenarios_es1"):          {"scenario_year", "scenario_name", "technology_type"},
    t("neso_future_scenarios_flx1"):         {"scenario_year", "scenario_name", "technology_type"},
    t("neso_future_scenarios_ws1"):          {"scenario_year", "scenario_name", "technology_type"},
    t("neso_future_scenarios_building_blocks"): {"scenario_year", "building_block_id"},
    t("neso_capacity_margin"):               {"date"},
    t("neso_gas_day_ahead"):                 {"gas_date"},

    t("market_prices_wholesale"):            {"trade_date"},  # adapt if your schema differs
}

def list_mappings() -> List[Tuple[str, str]]:
    return [(r.name, r.table) for r in RULES]

def classify_many(objs: Iterable[str]) -> List[Tuple[str, Optional[str]]]:
    return [(o, map_object_to_table(o)) for o in objs]

# ---- Optional CLI for quick checks ----
if __name__ == "__main__":
    import argparse, sys
    parser = argparse.ArgumentParser(description="Ingestion routing debugger")
    parser.add_argument("--list-mappings", action="store_true", help="Print pattern→table rules")
    parser.add_argument("--classify", nargs="*", help="Object paths to classify")
    args = parser.parse_args()

    if args.list_mappings:
        for name, table in list_mappings():
            print(f"{name:28s} -> {table}")
    if args.classify:
        for obj, table in classify_many(args.classify):
            print(f"{obj} -> {table}")
    if not (args.list_mappings or args.classify):
        parser.print_help(sys.stderr)
