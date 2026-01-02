#!/usr/bin/env python3
"""
UK Offshore Wind Turbine Specs (Operational + Pipeline)
- Source A: DESNZ REPD quarterly extract (CSV, GOV.UK)
- Source B: The Crown Estate ArcGIS layer (England/Wales/NI wind site agreements)
- Source C: Crown Estate Scotland ArcGIS layer (Scottish offshore wind)

Outputs a BigQuery table with:
- turbine specs from REPD (MW, count, height)
- clear operating flag
- agreement/lease phase from Crown Estate datasets
- robust name-join logic (phase/extension/OWF/Ltd handling + fuzzy fallback)
"""

from __future__ import annotations

import os
import re
import json
import math
import datetime as dt
from typing import Dict, Any, List, Optional, Tuple

import requests
import pandas as pd
from rapidfuzz import process, fuzz

from google.cloud import bigquery


# -----------------------------
# CONFIG
# -----------------------------

# REPD quarterly CSV (example: Oct 2025 Q3). You can swap this to the newest quarterly file.
# GOV.UK page lists the asset links; this is the direct CSV asset URL.
REPD_CSV_URL = (
    "https://assets.publishing.service.gov.uk/media/691d9a4e2c6b98ecdbc50038/REPD_Publication_Q3_2025.csv"
)

# The Crown Estate (England/Wales/NI) ArcGIS layer query endpoint (Layer ID 0)
TCE_QUERY_URL = (
    "https://services2.arcgis.com/PZklK9Q45mfMFuZs/ArcGIS/rest/services/"
    "WindSite_EngWalNI_TheCrownEstate/FeatureServer/0/query"
)

# Crown Estate Scotland ArcGIS layer query endpoint (Layer ID 0)
CES_QUERY_URL = (
    "https://services3.arcgis.com/nGV4jiurzcahJ9LV/ArcGIS/rest/services/"
    "Offshore_Wind_Crown_Estate_Scotland/FeatureServer/0/query"
)

# BigQuery destination
GCP_PROJECT = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"
BQ_TABLE = "offshore_wind_turbine_specs_repd_crown"

# When True, we exclude obviously dead projects (abandoned/withdrawn/refused/decommissioned).
# If you want "literally all historical offshore entries", set False.
ACTIVE_PIPELINE_ONLY = True

# Fuzzy matching threshold (0-100)
FUZZY_THRESHOLD = 90


# -----------------------------
# HELPERS: ArcGIS REST paging
# -----------------------------

def fetch_arcgis_all_features(
    query_url: str,
    out_fields: str,
    where: str = "1=1",
    page_size: int = 1000,
    return_geometry: bool = False,
) -> List[Dict[str, Any]]:
    """Fetch all features from an ArcGIS FeatureServer layer using resultOffset paging."""
    features: List[Dict[str, Any]] = []
    offset = 0

    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "f": "json",
            "returnGeometry": "true" if return_geometry else "false",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }
        r = requests.get(query_url, params=params, timeout=60)
        r.raise_for_status()
        payload = r.json()

        page = payload.get("features", [])
        features.extend(page)

        # ArcGIS signals more rows via exceededTransferLimit
        exceeded = payload.get("exceededTransferLimit", False)
        if not exceeded and len(page) < page_size:
            break

        offset += page_size

        # Safety stop to avoid infinite loops if server behaves oddly
        if offset > 200000:
            raise RuntimeError("ArcGIS paging exceeded safety limit.")

    return features


# -----------------------------
# HELPERS: cleaning + coercion
# -----------------------------

NOT_SET = {"Not set", "NOT SET", "", None}

def to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if s in NOT_SET:
        return None
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None

def to_int(x: Any) -> Optional[int]:
    f = to_float(x)
    if f is None or math.isnan(f):
        return None
    return int(round(f))

def parse_ddmmyyyy(s: Any) -> Optional[dt.date]:
    if s is None:
        return None
    st = str(s).strip()
    if st in NOT_SET:
        return None
    # REPD uses dd/mm/yyyy
    try:
        d = dt.datetime.strptime(st, "%d/%m/%Y").date()
        return d
    except ValueError:
        return None


# -----------------------------
# STATUS MAPPING
# -----------------------------

def map_status_bucket(repd_short: str, repd_long: str) -> Tuple[str, bool]:
    """
    Return (status_bucket, is_operating) using REPD status fields.
    Buckets are designed for clear 'not operating' flags.
    """
    short = (repd_short or "").strip().lower()
    long_ = (repd_long or "").strip().lower()

    # Operating
    if short == "operational" or "operational" in long_:
        return ("OPERATING", True)

    # Under construction / building
    if short in {"under construction", "awaiting construction"} or "construction" in short:
        return ("UNDER_CONSTRUCTION", False)

    # Consented / granted (but not operating yet)
    consent_terms = [
        "planning permission granted",
        "appeal granted",
        "secretary of state - granted",
        "consented",
    ]
    if any(t in long_ for t in consent_terms) or short in {"consented"}:
        return ("CONSENTED", False)

    # Active planning pipeline
    planning_terms = [
        "planning application submitted",
        "appeal lodged",
        "in planning",
        "pre-planning",
    ]
    if any(t in long_ for t in planning_terms) or short in {"in planning", "pre-planning application"}:
        return ("PLANNING", False)

    # Not proceeding / dead
    dead_terms = [
        "abandoned",
        "application refused",
        "planning permission refused",
        "planning application withdrawn",
        "application withdrawn",
        "appeal refused",
        "appeal withdrawn",
        "planning permission expired",
        "decommissioned",
    ]
    if short in {"abandoned", "decommissioned"} or any(t in long_ for t in dead_terms):
        return ("NOT_PROCEEDING", False)

    return ("OTHER", False)


# -----------------------------
# MERGE KEY STRATEGY
# -----------------------------

_CORP_SUFFIX = re.compile(r"\b(ltd|limited|plc|llp|inc|co|company)\b", re.I)
_GENERIC = re.compile(r"\b(offshore|wind|farm|project|owf|windfarm)\b", re.I)
_PUNCT = re.compile(r"[^a-z0-9\s]+", re.I)
_WS = re.compile(r"\s+")

_PHASE_EXT = re.compile(r"\b(phase|extension|ext)\b", re.I)
_ROMAN = {
    " i ": " 1 ",
    " ii ": " 2 ",
    " iii ": " 3 ",
    " iv ": " 4 ",
    " v ": " 5 ",
}

def normalise_name(name: str, drop_phase_ext: bool) -> str:
    if not name:
        return ""
    s = f" {name.strip().lower()} "
    # normalise common roman numerals (basic)
    for k, v in _ROMAN.items():
        s = s.replace(k, v)
    s = _PUNCT.sub(" ", s)
    s = _CORP_SUFFIX.sub(" ", s)
    s = _GENERIC.sub(" ", s)
    if drop_phase_ext:
        s = _PHASE_EXT.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s

def extract_numbers(s: str) -> List[str]:
    return re.findall(r"\b\d+\b", s or "")

def build_name_keys(name: str) -> Dict[str, Any]:
    full_key = normalise_name(name, drop_phase_ext=False)
    base_key = normalise_name(name, drop_phase_ext=True)
    nums = set(extract_numbers(full_key))
    return {"key_full": full_key, "key_base": base_key, "num_tokens": nums}


def best_match(
    target_keys: Dict[str, Any],
    candidates: pd.DataFrame,
    cand_name_col: str,
    cand_key_full_col: str,
    cand_key_base_col: str,
    score_cutoff: int = FUZZY_THRESHOLD,
) -> Optional[int]:
    """
    Return index of best candidate or None.
    Matching order:
      1) exact full key
      2) base key + numeric token overlap (if numbers exist)
      3) fuzzy on full key
    """
    t_full = target_keys["key_full"]
    t_base = target_keys["key_base"]
    t_nums = target_keys["num_tokens"]

    if not t_full:
        return None

    # 1) exact full
    exact = candidates.index[candidates[cand_key_full_col] == t_full]
    if len(exact) == 1:
        return int(exact[0])
    if len(exact) > 1:
        # disambiguate with numbers if possible
        if t_nums:
            for idx in exact:
                c_nums = candidates.at[idx, "num_tokens"]
                if t_nums & c_nums:
                    return int(idx)
        return int(exact[0])

    # 2) base + numbers overlap
    base_matches = candidates.index[candidates[cand_key_base_col] == t_base]
    if len(base_matches) == 1:
        return int(base_matches[0])
    if len(base_matches) > 1 and t_nums:
        for idx in base_matches:
            c_nums = candidates.at[idx, "num_tokens"]
            if t_nums & c_nums:
                return int(idx)

    # 3) fuzzy
    choices = candidates[cand_key_full_col].fillna("").tolist()
    if not choices:
        return None
    match = process.extractOne(
        t_full,
        choices,
        scorer=fuzz.token_set_ratio,
        score_cutoff=score_cutoff,
    )
    if not match:
        return None
    best_str, score, pos = match
    # pos is list position; map back to dataframe index
    return int(candidates.index[pos])


# -----------------------------
# LOAD + TRANSFORM
# -----------------------------

def load_repd_offshore() -> pd.DataFrame:
    print("=" * 80)
    print("📥 LOADING REPD OFFSHORE WIND DATA")
    print("=" * 80)
    print(f"Source: {REPD_CSV_URL}")
    print()
    
    # UK government CSVs often use ISO-8859-1 (Latin-1) encoding
    df = pd.read_csv(REPD_CSV_URL, dtype=str, encoding="ISO-8859-1", low_memory=False)

    # Offshore-only filter (robust to label variations)
    df["Technology Type"] = df["Technology Type"].fillna("")
    offshore_mask = df["Technology Type"].str.contains("offshore", case=False, na=False)
    df = df.loc[offshore_mask].copy()
    
    print(f"✅ Loaded {len(df):,} offshore wind entries from REPD")
    print()

    # Minimal columns (add more if you want)
    keep_cols = [
        "Ref ID",
        "Record Last Updated (dd/mm/yyyy)",
        "Operator (or Applicant)",
        "Site Name",
        "Technology Type",
        "Installed Capacity (MWelec)",
        "Turbine Capacity (MW)",
        "No. of Turbines",
        "Height of Turbines (m)",
        "Development Status",
        "Development Status (short)",
        "Offshore Wind Round",
        "Country",
        "X-coordinate",
        "Y-coordinate",
        "Planning Authority",
        "Planning Application Reference",
    ]
    # Keep only those that exist (REPD column sets can evolve)
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols].copy()

    # Coerce numeric turbine specs
    df["installed_capacity_mw"] = df["Installed Capacity (MWelec)"].map(to_float)
    df["turbine_capacity_mw"] = df.get("Turbine Capacity (MW)", pd.Series(dtype=object)).map(to_float)
    df["num_turbines"] = df["No. of Turbines"].map(to_int)
    df["turbine_height_m"] = df["Height of Turbines (m)"].map(to_float)

    # Parse dates
    df["repd_record_last_updated"] = df["Record Last Updated (dd/mm/yyyy)"].map(parse_ddmmyyyy)

    # Status mapping
    df["status_bucket"], df["is_operating"] = zip(*df.apply(
        lambda r: map_status_bucket(r.get("Development Status (short)", ""), r.get("Development Status", "")),
        axis=1
    ))

    # Optionally restrict to operational + active pipeline
    if ACTIVE_PIPELINE_ONLY:
        before = len(df)
        df = df.loc[df["status_bucket"].isin({"OPERATING", "UNDER_CONSTRUCTION", "CONSENTED", "PLANNING", "OTHER"})].copy()
        removed = before - len(df)
        print(f"📌 Active pipeline filter: Removed {removed} NOT_PROCEEDING entries")
        print(f"   Remaining: {len(df):,} operational/pipeline projects")
        print()

    # Join keys
    keys = df["Site Name"].fillna("").map(build_name_keys)
    df["key_full"] = keys.map(lambda d: d["key_full"])
    df["key_base"] = keys.map(lambda d: d["key_base"])
    df["num_tokens"] = keys.map(lambda d: d["num_tokens"])

    return df


def load_tce_agreements() -> pd.DataFrame:
    print("=" * 80)
    print("📥 LOADING THE CROWN ESTATE (ENGLAND/WALES/NI) AGREEMENTS")
    print("=" * 80)
    print(f"Source: {TCE_QUERY_URL}")
    print()
    
    # The Crown Estate layer fields (see ArcGIS layer page)
    out_fields = "Name_Prop,Name_Ten,Wind_Round,Lease_Stat,Inf_Status,ODP_Hyperlink,km2"
    feats = fetch_arcgis_all_features(TCE_QUERY_URL, out_fields=out_fields, return_geometry=False)

    rows = []
    for f in feats:
        a = f.get("attributes", {})
        rows.append({
            "tce_name": a.get("Name_Prop"),
            "tce_tenant": a.get("Name_Ten"),
            "tce_wind_round": a.get("Wind_Round"),
            "tce_lease_status": a.get("Lease_Stat"),
            "tce_infrastructure_status": a.get("Inf_Status"),
            "tce_link": a.get("ODP_Hyperlink"),
            "tce_area_km2": a.get("km2"),
        })

    df = pd.DataFrame(rows)
    
    print(f"✅ Loaded {len(df):,} TCE wind site agreements")
    print()

    keys = df["tce_name"].fillna("").map(build_name_keys)
    df["key_full"] = keys.map(lambda d: d["key_full"])
    df["key_base"] = keys.map(lambda d: d["key_base"])
    df["num_tokens"] = keys.map(lambda d: d["num_tokens"])

    return df


def load_ces_offshore() -> pd.DataFrame:
    print("=" * 80)
    print("📥 LOADING CROWN ESTATE SCOTLAND OFFSHORE WIND")
    print("=" * 80)
    print(f"Source: {CES_QUERY_URL}")
    print()
    
    # CES layer fields (see ArcGIS layer page)
    out_fields = "Property_Description,Tenant_Name,Lease_Type_Description,Property_Classification,Project_Phase,Capacity_MW"
    feats = fetch_arcgis_all_features(CES_QUERY_URL, out_fields=out_fields, return_geometry=False)

    rows = []
    for f in feats:
        a = f.get("attributes", {})
        rows.append({
            "ces_description": a.get("Property_Description"),
            "ces_tenant": a.get("Tenant_Name"),
            "ces_agreement_type": a.get("Lease_Type_Description"),
            "ces_classification": a.get("Property_Classification"),
            "ces_project_phase": a.get("Project_Phase"),
            "ces_capacity_mw": a.get("Capacity_MW"),
        })

    df = pd.DataFrame(rows)

    # Keep wind farms only (drop OFTO / substations if present)
    df["ces_classification"] = df["ces_classification"].fillna("")
    df = df.loc[df["ces_classification"].str.contains("wind farm", case=False, na=False)].copy()
    
    print(f"✅ Loaded {len(df):,} CES offshore wind entries")
    print()

    keys = df["ces_description"].fillna("").map(build_name_keys)
    df["key_full"] = keys.map(lambda d: d["key_full"])
    df["key_base"] = keys.map(lambda d: d["key_base"])
    df["num_tokens"] = keys.map(lambda d: d["num_tokens"])

    return df


def merge_repd_with_leases(repd: pd.DataFrame, tce: pd.DataFrame, ces: pd.DataFrame) -> pd.DataFrame:
    print("=" * 80)
    print("🔗 MERGING REPD WITH CROWN ESTATE LEASE DATA")
    print("=" * 80)
    print()
    
    repd = repd.copy()
    repd["seabed_manager"] = None
    repd["lease_status"] = None
    repd["infrastructure_or_phase"] = None
    repd["lease_round_source"] = None
    repd["lease_link"] = None
    repd["match_score_method"] = None

    # Split by jurisdiction
    repd["Country"] = repd.get("Country", "").fillna("")
    is_scotland = repd["Country"].str.lower().eq("scotland")

    # Pre-index candidates
    tce = tce.set_index(tce.index)
    ces = ces.set_index(ces.index)
    
    matched_count = 0

    for idx, row in repd.iterrows():
        target_keys = {
            "key_full": row.get("key_full", ""),
            "key_base": row.get("key_base", ""),
            "num_tokens": row.get("num_tokens", set()),
        }

        if bool(is_scotland.loc[idx]):
            cand = ces
            match_idx = best_match(
                target_keys,
                candidates=cand,
                cand_name_col="ces_description",
                cand_key_full_col="key_full",
                cand_key_base_col="key_base",
            )
            if match_idx is not None:
                matched_count += 1
                repd.at[idx, "seabed_manager"] = "Crown Estate Scotland"
                repd.at[idx, "lease_status"] = cand.at[match_idx, "ces_agreement_type"]
                repd.at[idx, "infrastructure_or_phase"] = cand.at[match_idx, "ces_project_phase"]
                repd.at[idx, "lease_round_source"] = "CES"
                repd.at[idx, "lease_link"] = None
                repd.at[idx, "match_score_method"] = "name_match"
        else:
            cand = tce
            match_idx = best_match(
                target_keys,
                candidates=cand,
                cand_name_col="tce_name",
                cand_key_full_col="key_full",
                cand_key_base_col="key_base",
            )
            if match_idx is not None:
                matched_count += 1
                repd.at[idx, "seabed_manager"] = "The Crown Estate"
                repd.at[idx, "lease_status"] = cand.at[match_idx, "tce_lease_status"]
                repd.at[idx, "infrastructure_or_phase"] = cand.at[match_idx, "tce_infrastructure_status"]
                repd.at[idx, "lease_round_source"] = "TCE"
                repd.at[idx, "lease_link"] = cand.at[match_idx, "tce_link"]
                repd.at[idx, "match_score_method"] = "name_match"

    print(f"✅ Matched {matched_count}/{len(repd)} REPD entries to Crown Estate leases ({matched_count/len(repd)*100:.1f}%)")
    print()
    
    # If Crown Estate provides an explicit operating flag, you can surface it too
    # e.g. TCE "Active/In Operation" should align with is_operating=True
    repd["lease_says_operating"] = repd["infrastructure_or_phase"].fillna("").str.lower().isin({"active/in operation", "operational"})

    # Snapshot date for partitioning/versioning
    repd["snapshot_date"] = dt.date.today()

    # Rename columns to snake_case for BigQuery compatibility
    repd = repd.rename(columns={
        "Ref ID": "ref_id",
        "Site Name": "site_name",
        "Operator (or Applicant)": "operator_or_applicant",
        "Technology Type": "technology_type",
        "Offshore Wind Round": "offshore_wind_round",
        "Country": "country",
        "Development Status": "development_status",
        "Development Status (short)": "development_status_short",
        "Planning Authority": "planning_authority",
        "Planning Application Reference": "planning_application_reference",
        "Record Last Updated (dd/mm/yyyy)": "record_last_updated_ddmmyyyy",
        "X-coordinate": "x_coordinate",
        "Y-coordinate": "y_coordinate",
    })

    return repd


# -----------------------------
# BIGQUERY LOAD
# -----------------------------

def ensure_dataset(client: bigquery.Client, dataset_id: str) -> None:
    dataset_ref = bigquery.Dataset(dataset_id)
    dataset_ref.location = "US"  # match existing dataset location
    try:
        client.get_dataset(dataset_id)
    except Exception:
        client.create_dataset(dataset_ref, exists_ok=True)

def load_to_bigquery(df: pd.DataFrame) -> None:
    print("=" * 80)
    print("📤 LOADING TO BIGQUERY")
    print("=" * 80)
    print()
    
    client = bigquery.Client(project=GCP_PROJECT)
    dataset_id = f"{GCP_PROJECT}.{BQ_DATASET}"
    table_id = f"{dataset_id}.{BQ_TABLE}"

    ensure_dataset(client, dataset_id)

    # Define a stable schema for key columns
    schema = [
        bigquery.SchemaField("snapshot_date", "DATE"),
        bigquery.SchemaField("ref_id", "STRING"),
        bigquery.SchemaField("site_name", "STRING"),
        bigquery.SchemaField("operator_or_applicant", "STRING"),
        bigquery.SchemaField("technology_type", "STRING"),
        bigquery.SchemaField("offshore_wind_round", "STRING"),
        bigquery.SchemaField("country", "STRING"),

        bigquery.SchemaField("installed_capacity_mw", "FLOAT"),
        bigquery.SchemaField("turbine_capacity_mw", "FLOAT"),
        bigquery.SchemaField("num_turbines", "INTEGER"),
        bigquery.SchemaField("turbine_height_m", "FLOAT"),

        bigquery.SchemaField("development_status", "STRING"),
        bigquery.SchemaField("development_status_short", "STRING"),
        bigquery.SchemaField("status_bucket", "STRING"),
        bigquery.SchemaField("is_operating", "BOOLEAN"),

        bigquery.SchemaField("seabed_manager", "STRING"),
        bigquery.SchemaField("lease_status", "STRING"),
        bigquery.SchemaField("infrastructure_or_phase", "STRING"),
        bigquery.SchemaField("lease_round_source", "STRING"),
        bigquery.SchemaField("lease_link", "STRING"),
        bigquery.SchemaField("lease_says_operating", "BOOLEAN"),
        bigquery.SchemaField("match_score_method", "STRING"),

        bigquery.SchemaField("repd_record_last_updated", "DATE"),
        bigquery.SchemaField("planning_authority", "STRING"),
        bigquery.SchemaField("planning_application_reference", "STRING"),

        # Optional debugging fields
        bigquery.SchemaField("key_full", "STRING"),
        bigquery.SchemaField("key_base", "STRING"),
        bigquery.SchemaField("x_coordinate", "STRING"),
        bigquery.SchemaField("y_coordinate", "STRING"),
        bigquery.SchemaField("operating_label", "STRING"),
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="snapshot_date",
        ),
    )

    # BigQuery can't store Python sets; drop/convert num_tokens
    df2 = df.copy()
    if "num_tokens" in df2.columns:
        df2["num_tokens"] = df2["num_tokens"].map(lambda s: ",".join(sorted(list(s))) if isinstance(s, set) else None)

    # Drop any remaining columns with spaces/special characters (already extracted to snake_case)
    drop_cols = [
        "Installed Capacity (MWelec)", 
        "Turbine Capacity (MW)", 
        "No. of Turbines", 
        "Height of Turbines (m)",
        "Record Last Updated (dd/mm/yyyy)",
    ]
    df2 = df2.drop(columns=[c for c in drop_cols if c in df2.columns])

    print(f"Target: {table_id}")
    print(f"Rows: {len(df2):,}")
    print()
    
    load_job = client.load_table_from_dataframe(df2, table_id, job_config=job_config)
    load_job.result()
    
    print(f"✅ Loaded {len(df2):,} rows into {table_id}")
    print()


def main() -> None:
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "OFFSHORE WIND TURBINE SPECS UPDATE (REPD + CROWN ESTATE)" + " " * 7 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Task 16: Update turbine specs from authoritative government sources")
    print("Sources: DESNZ REPD + The Crown Estate + Crown Estate Scotland")
    print()
    
    try:
        repd = load_repd_offshore()
        tce = load_tce_agreements()
        ces = load_ces_offshore()

        merged = merge_repd_with_leases(repd, tce, ces)

        # A friendly "not operating" clarity column
        merged["operating_label"] = merged["is_operating"].map(lambda x: "OPERATING" if x else "NOT OPERATING")

        load_to_bigquery(merged)
        
        print("=" * 80)
        print("✅ TASK 16 COMPLETE: Offshore Wind Turbine Specs Updated")
        print("=" * 80)
        print()
        print("Created Resources:")
        print(f"  • BigQuery table: {GCP_PROJECT}.{BQ_DATASET}.{BQ_TABLE}")
        print("  • Quarterly REPD data merged with Crown Estate lease info")
        print("  • Operational status flags (is_operating, status_bucket)")
        print("  • Seabed lease phase/status from TCE/CES")
        print()
        print("Usage:")
        print("  • Replace manual wind_turbine_specs with REPD/Crown Estate authoritative data")
        print("  • Enable quarterly updates via cron (REPD publishes Q1/Q2/Q3/Q4)")
        print("  • Track pipeline projects (consented/planning)")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
