#!/usr/bin/env python3
"""
BigQuery Data Readiness Validator for NESO/Elexon
- Verifies tables exist & have rows
- Confirms date windows (min/max)
- Checks required columns & NULL rates
- Validates numeric types & detects string-as-number issues
- Validates settlement_period (1..50) & 30-min continuity samples
- Produces a concise readiness report for dashboarding

Usage:
  python bq_data_validator.py --project jibber-jabber-knowledge --dataset uk_energy
"""

import argparse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
from google.cloud import bigquery

# -----------------------------
# CONFIG: tweak for your setup
# -----------------------------
DEFAULT_PROJECT = "jibber-jabber-knowledge"
DEFAULT_DATASET = "uk_energy"

# Map each table/view to:
# - date_col (DATE or castable to DATE); None = no date filter / not time-based
# - required_cols (must exist)
# - numeric_expect (should be numeric; warn if STRING or CAST fails)
# - extra_checks: names of built-in checks to run
TABLES: Dict[str, dict] = {
    # NESO (production)
    "neso_demand_forecasts": {
        "date_col": "settlement_date",
        "required_cols": ["settlement_date", "settlement_period", "national_demand_forecast"],
        "numeric_expect": ["national_demand_forecast", "temperature_forecast", "wind_forecast", "solar_forecast"],
        "extra_checks": ["settlement_period_range", "sp_continuity_sample"],
    },
    "neso_wind_forecasts": {
        "date_col": "settlement_date",
        "required_cols": ["settlement_date", "settlement_period", "forecast_output_mw"],
        "numeric_expect": ["forecast_output_mw", "actual_output_mw", "capacity_mw", "wind_speed_ms"],
        "extra_checks": ["settlement_period_range"],
    },
    "neso_balancing_services": {
        "date_col": "charge_date",
        "required_cols": ["charge_date", "settlement_period", "cost_pounds", "volume_mwh", "bsuos_rate_pounds_mwh"],
        "numeric_expect": ["cost_pounds", "volume_mwh", "bsuos_rate_pounds_mwh", "constraint_costs"],
        "extra_checks": [],
    },
    "neso_interconnector_flows": {
        "date_col": "trading_date",
        "required_cols": ["trading_date", "settlement_period", "interconnector_name", "actual_flow_mw"],
        "numeric_expect": ["actual_flow_mw", "max_import_capacity_mw", "max_export_capacity_mw",
                           "day_ahead_price_uk", "day_ahead_price_foreign"],
        "extra_checks": ["settlement_period_range"],
    },
    "neso_carbon_intensity": {
        "date_col": "timestamp",
        "required_cols": ["timestamp", "carbon_intensity_gco2_kwh"],
        "numeric_expect": ["carbon_intensity_gco2_kwh", "renewable_percentage", "fossil_percentage",
                           "nuclear_percentage", "imports_percentage"],
        "extra_checks": [],
    },
    # Elexon (development — may be empty; we still check)
    "elexon_demand_outturn": {
        "date_col": "settlement_date",
        "required_cols": ["settlement_date", "settlement_period", "national_demand"],
        "numeric_expect": ["national_demand", "england_wales_demand", "embedded_wind_generation", "embedded_solar_generation"],
        "extra_checks": ["settlement_period_range", "sp_continuity_sample"],
    },
    "elexon_generation_outturn": {
        "date_col": "settlement_date",
        "required_cols": ["settlement_date", "settlement_period", "fuel_type", "generation_mw"],
        "numeric_expect": ["generation_mw", "generation_percentage", "capacity_factor"],
        "extra_checks": ["settlement_period_range"],
    },
    "elexon_bid_offer_acceptances": {
        "date_col": "settlement_date",
        "required_cols": ["settlement_date", "settlement_period", "bmu_id", "bid_price", "offer_price"],
        "numeric_expect": ["bid_price", "offer_price", "bid_volume", "offer_volume",
                           "accepted_bid_volume", "accepted_offer_volume"],
        "extra_checks": ["settlement_period_range"],
    },
    "elexon_system_warnings": {
        "date_col": "timestamp",
        "required_cols": ["timestamp", "warning_type", "severity"],
        "numeric_expect": [],
        "extra_checks": [],
    },
}

# NULL thresholds that trigger warnings/errors
WARN_NULL_PCT = 10.0     # warn if >10% NULLs in a required column
ERROR_NULL_PCT = 30.0    # error if >30% NULLs in a required column

# Min rows considered “usable” for a date window
MIN_ROWS_WARN = 100
MIN_ROWS_ERROR = 0

# -----------------------------
# Helper dataclasses
# -----------------------------
@dataclass
class CheckFinding:
    severity: str  # "OK" | "WARN" | "ERROR"
    table: str
    check: str
    detail: str

@dataclass
class TableReport:
    table: str
    exists: bool = False
    row_count: int = 0
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    findings: List[CheckFinding] = field(default_factory=list)

# -----------------------------
# BigQuery helpers
# -----------------------------
def table_ref(project: str, dataset: str, table: str) -> str:
    return f"`{project}.{dataset}.{table}`"

def table_exists(client: bigquery.Client, project: str, dataset: str, table: str) -> bool:
    try:
        client.get_table(f"{project}.{dataset}.{table}")
        return True
    except Exception:
        return False

def get_row_count(client: bigquery.Client, project: str, dataset: str, table: str) -> int:
    q = f"SELECT COUNT(1) c FROM {table_ref(project, dataset, table)}"
    return list(client.query(q).result())[0].c

def get_date_range(client: bigquery.Client, project: str, dataset: str, table: str, date_col: str) -> Tuple[Optional[str], Optional[str]]:
    # Cast to DATE for safety; works for DATE, DATETIME, TIMESTAMP
    q = f"""
    SELECT
      CAST(MIN(CAST({date_col} AS DATE)) AS STRING) AS min_d,
      CAST(MAX(CAST({date_col} AS DATE)) AS STRING) AS max_d
    FROM {table_ref(project, dataset, table)}
    """
    row = list(client.query(q).result())[0]
    return row.min_d, row.max_d

def null_profile(client: bigquery.Client, project: str, dataset: str, table: str, columns: List[str]) -> pd.DataFrame:
    # Compute NULL % per column
    selects = [f"SAFE_DIVIDE(SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END), COUNT(1))*100 AS null_pct_{c}" for c in columns]
    q = f"SELECT {', '.join(selects)} FROM {table_ref(project, dataset, table)}"
    df = client.query(q).to_dataframe()
    # reshape to tidy
    tidy = []
    for c in columns:
        pct = float(df.iloc[0][f"null_pct_{c}"]) if not df.empty else None
        tidy.append({"column": c, "null_pct": pct})
    return pd.DataFrame(tidy)

def check_numeric_types(client: bigquery.Client, project: str, dataset: str, table: str, cols: List[str]) -> List[CheckFinding]:
    findings = []
    try:
        schema = client.get_table(f"{project}.{dataset}.{table}").schema
        types = {f.name: f.field_type for f in schema}
    except Exception as e:
        return [CheckFinding("WARN", table, "schema", f"Failed to fetch schema: {e}")]

    for c in cols:
        if c not in types:
            findings.append(CheckFinding("ERROR", table, "schema", f"Missing expected numeric column '{c}'"))
            continue
        if types[c] not in ("INT64", "FLOAT64", "NUMERIC", "BIGNUMERIC"):
            # Count rows that cannot be cast to FLOAT64
            q = f"""
            SELECT COUNTIF(SAFE_CAST({c} AS FLOAT64) IS NULL AND {c} IS NOT NULL) AS bad
            FROM {table_ref(project, dataset, table)}
            """
            bad = list(client.query(q).result())[0].bad
            if bad > 0:
                findings.append(CheckFinding("ERROR", table, "type",
                                             f"Column '{c}' is {types[c]} and {bad} rows fail numeric cast"))
            else:
                findings.append(CheckFinding("WARN", table, "type",
                                             f"Column '{c}' is {types[c]} but all values appear castable"))
        else:
            findings.append(CheckFinding("OK", table, "type", f"Column '{c}' is numeric ({types[c]})"))
    return findings

def check_settlement_period_range(client: bigquery.Client, project: str, dataset: str, table: str) -> Optional[CheckFinding]:
    # Only run if column exists
    try:
        schema = client.get_table(f"{project}.{dataset}.{table}").schema
        if "settlement_period" not in [f.name for f in schema]:
            return None
        q = f"""
        SELECT
          COUNTIF(settlement_period < 1 OR settlement_period > 50) AS invalid,
          COUNT(*) AS total
        FROM {table_ref(project, dataset, table)}
        """
        row = list(client.query(q).result())[0]
        if row.invalid > 0:
            return CheckFinding("ERROR", table, "settlement_period_range",
                                f"{row.invalid}/{row.total} rows have settlement_period outside 1..50")
        return CheckFinding("OK", table, "settlement_period_range", "All settlement_period values in 1..50")
    except Exception as e:
        return CheckFinding("WARN", table, "settlement_period_range", f"Check failed: {e}")

def check_sp_continuity_sample(client: bigquery.Client, project: str, dataset: str, table: str, date_col: str) -> Optional[CheckFinding]:
    """
    Pick latest available date and verify we have SP 1..50 with no gaps.
    """
    try:
        # find latest date with data
        qmax = f"SELECT MAX(CAST({date_col} AS DATE)) AS d FROM {table_ref(project, dataset, table)}"
        latest = list(client.query(qmax).result())[0].d
        if latest is None:
            return CheckFinding("WARN", table, "sp_continuity", "No dates found")
        q = f"""
        WITH sp AS (
          SELECT settlement_period FROM {table_ref(project, dataset, table)}
          WHERE CAST({date_col} AS DATE) = @d
        )
        SELECT
          ARRAY_TO_STRING(
            (SELECT ARRAY(
               SELECT sp FROM UNNEST(GENERATE_ARRAY(1,50)) sp
               EXCEPT DISTINCT SELECT settlement_period FROM sp
            )), ',') AS missing
        """
        job = client.query(
            q,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("d", "DATE", latest)]
            ),
        )
        missing = list(job.result())[0].missing
        if missing:
            return CheckFinding("WARN", table, "sp_continuity", f"Latest {latest}: missing SPs [{missing}]")
        return CheckFinding("OK", table, "sp_continuity", f"Latest {latest}: complete SP 1..50")
    except Exception as e:
        return CheckFinding("WARN", table, "sp_continuity", f"Check failed: {e}")

# -----------------------------
# Orchestrator
# -----------------------------
def validate_table(client: bigquery.Client, project: str, dataset: str, name: str, spec: dict) -> TableReport:
    rep = TableReport(table=name)

    # Exists?
    rep.exists = table_exists(client, project, dataset, name)
    if not rep.exists:
        rep.findings.append(CheckFinding("ERROR", name, "existence", "Table/view not found"))
        return rep

    # Row count
    try:
        rep.row_count = get_row_count(client, project, dataset, name)
        if rep.row_count <= MIN_ROWS_ERROR:
            rep.findings.append(CheckFinding("ERROR", name, "row_count", "No rows"))
        elif rep.row_count <= MIN_ROWS_WARN:
            rep.findings.append(CheckFinding("WARN", name, "row_count", f"Low row count: {rep.row_count}"))
        else:
            rep.findings.append(CheckFinding("OK", name, "row_count", f"{rep.row_count:,} rows"))
    except Exception as e:
        rep.findings.append(CheckFinding("WARN", name, "row_count", f"Failed to count rows: {e}"))

    # Date range
    date_col = spec.get("date_col")
    if date_col:
        try:
            rep.min_date, rep.max_date = get_date_range(client, project, dataset, name, date_col)
            if rep.min_date and rep.max_date:
                rep.findings.append(CheckFinding("OK", name, "date_range", f"{rep.min_date} → {rep.max_date} (via {date_col})"))
            else:
                rep.findings.append(CheckFinding("WARN", name, "date_range", "Could not determine date range"))
        except Exception as e:
            rep.findings.append(CheckFinding("WARN", name, "date_range", f"Failed to compute date range: {e}"))

    # Required columns + NULLs
    required = spec.get("required_cols", [])
    # Missing columns?
    try:
        schema = client.get_table(f"{project}.{dataset}.{name}").schema
        have_cols = {f.name for f in schema}
        missing = [c for c in required if c not in have_cols]
        if missing:
            rep.findings.append(CheckFinding("ERROR", name, "schema", f"Missing required columns: {missing}"))
        else:
            rep.findings.append(CheckFinding("OK", name, "schema", "All required columns present"))
    except Exception as e:
        rep.findings.append(CheckFinding("WARN", name, "schema", f"Failed to fetch schema: {e}"))
        have_cols = set()

    check_nulls_cols = [c for c in required if c in have_cols]
    if check_nulls_cols:
        try:
            nulls = null_profile(client, project, dataset, name, check_nulls_cols)
            for _, r in nulls.iterrows():
                col, pct = r["column"], (r["null_pct"] or 0.0)
                if pct >= ERROR_NULL_PCT:
                    sev = "ERROR"
                elif pct >= WARN_NULL_PCT:
                    sev = "WARN"
                else:
                    sev = "OK"
                rep.findings.append(CheckFinding(sev, name, "nulls", f"{col}: {pct:.1f}% NULL"))
        except Exception as e:
            rep.findings.append(CheckFinding("WARN", name, "nulls", f"NULL profiling failed: {e}"))

    # Numeric expectations (type + castability)
    numexp = spec.get("numeric_expect", [])
    if numexp:
        rep.findings.extend(check_numeric_types(client, project, dataset, name, numexp))

    # Extra checks
    for ek in spec.get("extra_checks", []):
        if ek == "settlement_period_range":
            f = check_settlement_period_range(client, project, dataset, name)
            if f: rep.findings.append(f)
        elif ek == "sp_continuity_sample" and date_col:
            f = check_sp_continuity_sample(client, project, dataset, name, date_col)
            if f: rep.findings.append(f)

    return rep

def summarize(reports: List[TableReport]) -> pd.DataFrame:
    rows = []
    for rep in reports:
        worst = "OK"
        for f in rep.findings:
            level = {"OK":0,"WARN":1,"ERROR":2}[f.severity]
            if level > {"OK":0,"WARN":1,"ERROR":2}[worst]:
                worst = f.severity
        rows.append({
            "table": rep.table,
            "exists": rep.exists,
            "row_count": rep.row_count,
            "min_date": rep.min_date,
            "max_date": rep.max_date,
            "status": worst,
            "errors": sum(1 for f in rep.findings if f.severity=="ERROR"),
            "warnings": sum(1 for f in rep.findings if f.severity=="WARN"),
            "oks": sum(1 for f in rep.findings if f.severity=="OK"),
        })
    return pd.DataFrame(rows).sort_values(["status","table"], ascending=[False,True])

def print_report(reports: List[TableReport]) -> None:
    print("\n=== BigQuery Data Readiness Report ===\n")
    for rep in reports:
        print(f"[{rep.table}]")
        if rep.min_date or rep.max_date:
            print(f"  rows={rep.row_count:,}  range={rep.min_date} → {rep.max_date}")
        else:
            print(f"  rows={rep.row_count:,}")
        for f in rep.findings:
            tag = {"OK":"✅","WARN":"⚠️","ERROR":"❌"}[f.severity]
            print(f"  {tag} {f.check}: {f.detail}")
        print("")
    summary = summarize(reports)
    print("=== Summary ===")
    print(summary.to_string(index=False))
    print("")

# -----------------------------
# Main
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=DEFAULT_PROJECT)
    ap.add_argument("--dataset", default=DEFAULT_DATASET)
    ap.add_argument("--only", nargs="*", help="Limit to specific tables (space-separated)")
    args = ap.parse_args()

    client = bigquery.Client(project=args.project)

    targets = TABLES if not args.only else {t: TABLES[t] for t in args.only if t in TABLES}
    reports = []
    for t, spec in targets.items():
        reports.append(validate_table(client, args.project, args.dataset, t, spec))

    print_report(reports)

    # Optional: write summary to a table
    # summary_df = summarize(reports)
    # summary_df.to_gbq(f"{args.dataset}.validation_runs", project_id=args.project, if_exists="append")

if __name__ == "__main__":
    main()