#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UK Balancing Mechanism (BOD) deep-dive, 2016→present:
- Fetch: BOD acceptances (Bids/Offers), System Price (cashout), NIV, Demand, Fuel Mix
- Derive: daily/monthly/seasonal KPIs, wind curtailment proxy, constraint vs energy signals
- Visualize: trend charts saved to ./out/charts/*.png
- Report: Google Docs with stage-by-stage sections + tables + embedded charts
"""

import os
import io
import json
import time
import math
import gzip
import uuid
import shutil
import string
import random
import zipfile
import logging
import pathlib
import datetime as dt
from dataclasses import dataclass
from typing import Optional, List, Dict

import numpy as np
import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

# Google APIs
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# -------------------------
# CONFIG
# -------------------------

@dataclass
class Config:
    start_date: str = "2016-01-01"
    end_date: str = dt.date.today().isoformat()
    out_dir: str = "./out"
    cache_dir: str = "./cache"
    charts_dir: str = "./out/charts"
    tables_dir: str = "./out/tables"
    doc_title_prefix: str = "UK BM BOD Analysis"
    elexon_api_key: str = os.getenv("ELEXON_API_KEY", "")
    # BMRS endpoints (historical CSV API style). If your org uses the new Data Portal, you can swap these.
    bmrs_bod_url: str = "https://api.bmreports.com/BMRS/BOD/v1"
    bmrs_price_url: str = "https://api.bmreports.com/BMRS/IMP_BMART/v1"  # Imbalance price & NIV by period
    bmrs_demand_url: str = "https://api.bmreports.com/BMRS/DERSYSDATA/v1"  # Demand outturn (daily/half-hourly)
    bmrs_genmix_url: str = "https://api.bmreports.com/BMRS/B1620/v1"  # Fuel type generation mix (hh)
    # Optional weather (stub: plug your provider)
    weather_enabled: bool = False
    google_scopes: List[str] = None
    google_project_credentials: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    google_folder_id_for_images: Optional[str] = None  # If set, charts upload to this Drive folder
    # BM Unit → fuel-type mapping (optional). If you have an internal CSV, set path here.
    bmunit_map_csv: Optional[str] = None
    # Request & batching
    batch_days: int = 30   # call BMRS in 30-day chunks to be nice
    timeout_secs: int = 60

    def __post_init__(self):
        if self.google_scopes is None:
            self.google_scopes = [
                "https://www.googleapis.com/auth/documents",
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/drive.file"
            ]
        pathlib.Path(self.out_dir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.charts_dir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.tables_dir).mkdir(parents=True, exist_ok=True)
        if not self.elexon_api_key:
            raise RuntimeError("ELEXON_API_KEY not set")

CFG = Config()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("bod")

# -------------------------
# HELPERS
# -------------------------

def daterange(start: dt.date, end: dt.date, step_days: int):
    cur = start
    while cur <= end:
        nxt = min(end, cur + dt.timedelta(days=step_days - 1))
        yield cur, nxt
        cur = nxt + dt.timedelta(days=1)

def from_to_params(fr: dt.date, to: dt.date):
    return {"FromDate": fr.isoformat(), "ToDate": to.isoformat()}

def to_date(s):
    if pd.isna(s): return None
    return pd.to_datetime(s).date()

def safe_float(x):
    try: return float(x)
    except: return np.nan

def write_parquet(df: pd.DataFrame, path: str):
    df.to_parquet(path, index=False)

def read_parquet(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)

# -------------------------
# BMRS CLIENT (CSV API style)
# -------------------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
def _get_csv(url: str, params: Dict) -> pd.DataFrame:
    params = dict(params)
    params["APIKey"] = CFG.elexon_api_key
    params["ServiceType"] = "csv"
    r = requests.get(url, params=params, timeout=CFG.timeout_secs)
    r.raise_for_status()
    try:
        return pd.read_csv(io.StringIO(r.text))
    except Exception as e:
        # Sometimes BMRS returns "No data" HTML; return empty DF
        log.warning(f"No/Bad CSV for {url} {params}: {e}")
        return pd.DataFrame()

def fetch_bod_acceptances(start: dt.date, end: dt.date) -> pd.DataFrame:
    """
    BOD acceptances. Typical columns (varies with API version):
    Publication Date, Settlement Date, Settlement Period, BM Unit ID, Acceptance Time,
    Bid Offer Flag (B/O), Acceptance Volume (MWh), Acceptance Price (£/MWh), etc.
    """
    cache = f"{CFG.cache_dir}/bod_{start}_{end}.parquet"
    if pathlib.Path(cache).exists():
        return read_parquet(cache)

    frames = []
    for fr, to in tqdm(list(daterange(start, end, CFG.batch_days)), desc="BOD"):
        q = from_to_params(fr, to)
        df = _get_csv(CFG.bmrs_bod_url, q)
        if not df.empty:
            frames.append(df)
        time.sleep(0.3)  # be gentle

    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not out.empty:
        # Normalize likely columns across variants
        cols = {c.lower().strip().replace(" ", "_"): c for c in out.columns}
        out.columns = [c.lower().strip().replace(" ", "_") for c in out.columns]
        # Standardize canonical names
        rename_map = {
            "settlement_date": "settlement_date",
            "settlementperiod": "settlement_period",
            "settlement_period": "settlement_period",
            "bm_unit_id": "bm_unit_id",
            "bidofferflag": "bid_offer_flag",
            "bid_offer_flag": "bid_offer_flag",
            "acceptance_price": "price",
            "acceptance_volume": "volume",
            "acceptance_time": "acceptance_time",
        }
        out = out.rename(columns={k: v for k, v in rename_map.items() if k in out.columns})
        # types
        if "settlement_date" in out:
            out["settlement_date"] = pd.to_datetime(out["settlement_date"]).dt.date
        if "settlement_period" in out:
            out["settlement_period"] = pd.to_numeric(out["settlement_period"], errors="coerce").astype("Int64")
        if "price" in out:
            out["price"] = pd.to_numeric(out["price"], errors="coerce")
        if "volume" in out:
            out["volume"] = pd.to_numeric(out["volume"], errors="coerce")
        write_parquet(out, cache)
    return out

def fetch_imbalance_price_niv(start: dt.date, end: dt.date) -> pd.DataFrame:
    cache = f"{CFG.cache_dir}/impniv_{start}_{end}.parquet"
    if pathlib.Path(cache).exists():
        return read_parquet(cache)

    frames = []
    for fr, to in tqdm(list(daterange(start, end, CFG.batch_days)), desc="IMP/NIV"):
        df = _get_csv(CFG.bmrs_price_url, from_to_params(fr, to))
        if not df.empty:
            frames.append(df)
        time.sleep(0.3)

    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not out.empty:
        out.columns = [c.lower().strip().replace(" ", "_") for c in out.columns]
        # expected fields: settlement_date, settlement_period, imbalancedirection, imbalanceprice, netimbalancevolume
        rename = {
            "imbalanceprice": "imbalance_price",
            "netimbalancevolume": "niv",
            "imbalancedirection": "imbalance_direction"
        }
        out = out.rename(columns={k: v for k, v in rename.items() if k in out.columns})
        out["settlement_date"] = pd.to_datetime(out["settlement_date"]).dt.date
        out["settlement_period"] = pd.to_numeric(out["settlement_period"], errors="coerce").astype("Int64")
        out["imbalance_price"] = pd.to_numeric(out.get("imbalance_price", np.nan), errors="coerce")
        out["niv"] = pd.to_numeric(out.get("niv", np.nan), errors="coerce")
        write_parquet(out, cache)
    return out

def fetch_demand(start: dt.date, end: dt.date) -> pd.DataFrame:
    cache = f"{CFG.cache_dir}/demand_{start}_{end}.parquet"
    if pathlib.Path(cache).exists():
        return read_parquet(cache)

    frames = []
    for fr, to in tqdm(list(daterange(start, end, CFG.batch_days)), desc="Demand"):
        df = _get_csv(CFG.bmrs_demand_url, from_to_params(fr, to))
        if not df.empty:
            frames.append(df)
        time.sleep(0.3)

    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not out.empty:
        out.columns = [c.lower().strip().replace(" ", "_") for c in out.columns]
        # typical: settlement_date, settlement_period, demand
        if "settlement_date" in out:
            out["settlement_date"] = pd.to_datetime(out["settlement_date"]).dt.date
        # find demand column
        if "demand" not in out.columns:
            # try common names
            for cand in ["nd", "totalsystemdemand", "system_demand", "demand_outturn"]:
                if cand in out.columns:
                    out = out.rename(columns={cand: "demand"})
                    break
        if "demand" in out:
            out["demand"] = pd.to_numeric(out["demand"], errors="coerce")
        if "settlement_period" in out:
            out["settlement_period"] = pd.to_numeric(out["settlement_period"], errors="coerce").astype("Int64")
        write_parquet(out, cache)
    return out

def fetch_genmix(start: dt.date, end: dt.date) -> pd.DataFrame:
    cache = f"{CFG.cache_dir}/genmix_{start}_{end}.parquet"
    if pathlib.Path(cache).exists():
        return read_parquet(cache)

    frames = []
    for fr, to in tqdm(list(daterange(start, end, CFG.batch_days)), desc="FuelMix"):
        df = _get_csv(CFG.bmrs_genmix_url, from_to_params(fr, to))
        if not df.empty:
            frames.append(df)
        time.sleep(0.3)

    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not out.empty:
        out.columns = [c.lower().strip().replace(" ", "_") for c in out.columns]
        # Normalize: settlement_date, settlement_period, fueltype, gen_mw
        if "settlement_date" in out:
            out["settlement_date"] = pd.to_datetime(out["settlement_date"]).dt.date
        for cand in ["fueltype", "fuel_type", "fuel"]:
            if cand in out.columns:
                out = out.rename(columns={cand: "fueltype"})
                break
        # find generation value column
        for cand in ["intensity", "generation_mw", "genmw", "actualgenerationoutput"]:
            if cand in out.columns:
                out = out.rename(columns={cand: "genmw"})
                break
        if "genmw" in out:
            out["genmw"] = pd.to_numeric(out["genmw"], errors="coerce")
        if "settlement_period" in out:
            out["settlement_period"] = pd.to_numeric(out["settlement_period"], errors="coerce").astype("Int64")
        write_parquet(out, cache)
    return out

# -------------------------
# OPTIONAL WEATHER
# -------------------------

def fetch_weather_daily(start: dt.date, end: dt.date) -> pd.DataFrame:
    """
    Stub: Replace with your provider. Return columns: date, temp_c, windspeed_ms (daily avg).
    """
    if not CFG.weather_enabled:
        return pd.DataFrame()
    # Example: build from your data lake or API
    return pd.DataFrame()

# -------------------------
# TRANSFORM & KPIs
# -------------------------

def load_bmunit_map() -> Optional[pd.DataFrame]:
    """
    Optional BM Unit → fuel mapping to detect wind curtailment precisely.
    CSV columns expected: bm_unit_id, fuel (e.g., WIND, CCGT, NUCLEAR, etc.)
    """
    if CFG.bmunit_map_csv and pathlib.Path(CFG.bmunit_map_csv).exists():
        m = pd.read_csv(CFG.bmunit_map_csv)
        m.columns = [c.strip().lower() for c in m.columns]
        return m[["bm_unit_id","fuel"]]
    return None

def derive_daily_kpis(bod: pd.DataFrame,
                      imp: pd.DataFrame,
                      demand: pd.DataFrame,
                      genmix: pd.DataFrame,
                      weather: pd.DataFrame,
                      bmunit_map: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Core joins + derived drivers.
    """
    # Clean BOD
    req_cols = ["settlement_date","settlement_period","bm_unit_id","bid_offer_flag","price","volume"]
    for c in req_cols:
        if c not in bod.columns:
            bod[c] = np.nan
    bod = bod.dropna(subset=["settlement_date","settlement_period"])
    bod["abs_volume"] = bod["volume"].abs()

    # Attach fuel mapping (optional)
    if bmunit_map is not None and "bm_unit_id" in bod:
        bod = bod.merge(bmunit_map, on="bm_unit_id", how="left")
    else:
        bod["fuel"] = np.nan  # unknown; we’ll proxy wind from genmix

    # Daily aggregations
    grp = bod.groupby("settlement_date", dropna=True)
    daily = grp.agg(
        total_bal_vol=("abs_volume","sum"),
        total_offer_mwh=("volume", lambda x: x[x>0].sum()),
        total_bid_mwh=("volume",  lambda x: -x[x<0].sum()),  # positive magnitude
        vw_avg_price=("price", lambda p: np.average(p.dropna(), weights=bod.loc[p.index, "abs_volume"].reindex(p.index).fillna(0)) if p.notna().any() else np.nan),
        max_price=("price","max"),
        min_price=("price","min"),
        n_acceptances=("price","count")
    ).reset_index()

    # Wind curtailment proxy from BOD (if fuel map present)
    if "fuel" in bod.columns:
        wind_bids = bod[(bod["bid_offer_flag"].astype(str).str.upper().str.startswith("B")) &
                        (bod["volume"]<0) &
                        (bod["fuel"].str.upper()=="WIND")]
        wind_curt = wind_bids.groupby("settlement_date")["abs_volume"].sum().rename("wind_curtail_mwh")
        daily = daily.merge(wind_curt, on="settlement_date", how="left")
    else:
        daily["wind_curtail_mwh"] = np.nan

    # Imbalance price & NIV
    if not imp.empty:
        imp2 = imp[["settlement_date","settlement_period","imbalance_price","niv"]].copy()
        imp_day = imp2.groupby("settlement_date").agg(
            avg_imbalance_price=("imbalance_price","mean"),
            max_imbalance_price=("imbalance_price","max"),
            min_imbalance_price=("imbalance_price","min"),
            total_niv=("niv","sum"),
            avg_abs_niv=("niv", lambda s: s.abs().mean())
        ).reset_index()
        daily = daily.merge(imp_day, on="settlement_date", how="left")

    # Demand
    if not demand.empty and "demand" in demand.columns:
        d2 = demand[["settlement_date","settlement_period","demand"]].copy()
        d_day = d2.groupby("settlement_date").agg(
            daily_energy_mwh=("demand", "sum"),   # half-hour MW sum ≈ MWh
            peak_demand_mw=("demand","max")
        ).reset_index()
        daily = daily.merge(d_day, on="settlement_date", how="left")

    # Fuel mix → wind MWh per day
    if not genmix.empty and {"fueltype","genmw","settlement_period","settlement_date"} <= set(genmix.columns):
        g = genmix.copy()
        g["genmwh"] = g["genmw"] * 0.5  # MW * 0.5h = MWh
        g_wind = g[g["fueltype"].str.upper().str.contains("WIND", na=False)]
        wind_day = g_wind.groupby("settlement_date")["genmwh"].sum().rename("wind_mwh")
        total_gen_day = g.groupby("settlement_date")["genmwh"].sum().rename("total_gen_mwh")
        daily = daily.merge(wind_day, on="settlement_date", how="left")
        daily = daily.merge(total_gen_day, on="settlement_date", how="left")
        daily["wind_share"] = daily["wind_mwh"] / daily["total_gen_mwh"]

    # Weather (optional)
    if not weather.empty:
        w = weather.rename(columns={"date":"settlement_date"})
        daily = daily.merge(w, on="settlement_date", how="left")

    # Season, year-month
    sdate = pd.to_datetime(daily["settlement_date"])
    daily["year"] = sdate.dt.year
    daily["month"] = sdate.dt.month
    daily["season"] = sdate.dt.month%12//3 + 1  # 1:winter(Dec-Feb) … 4:autumn(Sept-Nov)
    season_map = {1:"Winter",2:"Spring",3:"Summer",4:"Autumn"}
    daily["season_name"] = daily["season"].map(season_map)

    return daily.sort_values("settlement_date").reset_index(drop=True)

def monthly_rollups(daily: pd.DataFrame) -> pd.DataFrame:
    m = daily.copy()
    m["ym"] = pd.to_datetime(m["settlement_date"]).dt.to_period("M").dt.to_timestamp()
    out = m.groupby("ym").agg(
        total_bal_vol=("total_bal_vol","sum"),
        avg_vw_price=("vw_avg_price","mean"),
        max_price=("max_price","max"),
        wind_mwh=("wind_mwh","sum"),
        wind_curtail_mwh=("wind_curtail_mwh","sum"),
        peak_demand_mw=("peak_demand_mw","max")
    ).reset_index()
    return out

def kpi_table(daily: pd.DataFrame) -> pd.DataFrame:
    # headline KPIs across full period
    return pd.DataFrame({
        "Metric": [
            "Total balancing volume (TWh)",
            "Avg volume-weighted price (£/MWh)",
            "Max accepted price (£/MWh)",
            "Wind curtailment (TWh)",
            "Avg daily NIV (abs) (MWh)"
        ],
        "Value": [
            daily["total_bal_vol"].sum()/1e6,
            daily["vw_avg_price"].mean(),
            daily["max_price"].max(),
            (daily["wind_curtail_mwh"].sum()/1e6) if "wind_curtail_mwh" in daily else np.nan,
            daily["avg_abs_niv"].mean() if "avg_abs_niv" in daily else np.nan
        ]
    })

# -------------------------
# PLOTS (matplotlib only; no styles/colors set)
# -------------------------

import matplotlib
import matplotlib.pyplot as plt

def _savefig(name: str):
    path = f"{CFG.charts_dir}/{name}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    return path

def plot_trend_bal_volume(daily: pd.DataFrame):
    s = daily.groupby(pd.to_datetime(daily["settlement_date"]).dt.to_period("M")).sum(numeric_only=True)
    s.index = s.index.to_timestamp()
    plt.figure(figsize=(10,5))
    plt.plot(s.index, s["total_bal_vol"])
    plt.title("Monthly Balancing Volume (MWh)")
    plt.xlabel("Month")
    plt.ylabel("MWh")
    return _savefig("trend_balancing_volume_monthly")

def plot_price_extremes(daily: pd.DataFrame):
    plt.figure(figsize=(10,5))
    t = daily.dropna(subset=["vw_avg_price"])
    plt.plot(pd.to_datetime(t["settlement_date"]), t["vw_avg_price"])
    plt.title("Daily Volume-Weighted Price (£/MWh)")
    plt.xlabel("Date")
    plt.ylabel("£/MWh")
    return _savefig("daily_vw_price")

def plot_wind_vs_balancing(daily: pd.DataFrame):
    t = daily.dropna(subset=["wind_mwh","total_bal_vol"])
    plt.figure(figsize=(7,6))
    plt.scatter(t["wind_mwh"], t["total_bal_vol"], alpha=0.3)
    plt.title("Wind MWh vs Balancing Volume (Daily)")
    plt.xlabel("Wind MWh (daily)")
    plt.ylabel("Balancing Volume (MWh, daily)")
    return _savefig("scatter_wind_vs_bal_vol")

def plot_curtailment_share(daily: pd.DataFrame):
    if "wind_curtail_mwh" not in daily: return None
    m = daily.copy()
    m["ratio"] = m["wind_curtail_mwh"] / (m["wind_mwh"] + 1e-9)
    s = m.groupby(pd.to_datetime(m["settlement_date"]).dt.to_period("M"))["ratio"].mean()
    s.index = s.index.to_timestamp()
    plt.figure(figsize=(10,5))
    plt.plot(s.index, s.values)
    plt.title("Average Wind Curtailment Share (Monthly)")
    plt.xlabel("Month")
    plt.ylabel("Curtailment / Wind Output")
    return _savefig("wind_curtailment_share_monthly")

def plot_price_histogram(daily: pd.DataFrame):
    plt.figure(figsize=(8,5))
    x = daily["max_price"].dropna().clip(-500, 4000)  # trim tails for view
    plt.hist(x, bins=60)
    plt.title("Distribution of Daily Max Accepted Prices")
    plt.xlabel("£/MWh")
    plt.ylabel("Count (days)")
    return _savefig("hist_daily_max_prices")

# -------------------------
# REPORT (Google Docs + Drive)
# -------------------------

def g_clients():
    if not CFG.google_project_credentials:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set")
    creds = service_account.Credentials.from_service_account_file(
        CFG.google_project_credentials, scopes=CFG.google_scopes
    )
    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return docs, drive

def drive_upload_image(drive, path: str, parent_folder_id: Optional[str]) -> str:
    file_metadata = {"name": pathlib.Path(path).name}
    if parent_folder_id:
        file_metadata["parents"] = [parent_folder_id]
    media = MediaFileUpload(path, mimetype="image/png", resumable=False)
    f = drive.files().create(body=file_metadata, media_body=media, fields="id,webContentLink,webViewLink").execute()
    file_id = f["id"]
    # Make it readable (optional – depends on your security posture)
    drive.permissions().create(fileId=file_id, body={"type":"anyone","role":"reader"}).execute()
    # Return a link usable by Docs insert (webContentLink is fine)
    # For Docs inline images, we can use "insertInlineImage" with a URI, but the Docs API
    # does not directly fetch Drive content URIs; safer approach: use "insertInlineImage" with "uri"
    # that is publicly reachable (webContentLink includes &export=download). We'll use webContentLink.
    info = drive.files().get(fileId=file_id, fields="webContentLink,webViewLink").execute()
    return info["webContentLink"]

def docs_create(docs, title: str) -> str:
    doc = docs.documents().create(body={"title": title}).execute()
    return doc["documentId"]

def docs_insert_text(docs, doc_id: str, text: str, heading: Optional[str]=None, style: Optional[str]=None):
    reqs = []
    if heading:
        reqs.append({"insertText":{"location":{"index":1},"text":heading + "\n"}})
        # Apply Heading 1
        reqs.append({
            "updateParagraphStyle":{
                "range":{"startIndex":1,"endIndex":1+len(heading)+1},
                "paragraphStyle":{"namedStyleType":"HEADING_1"},
                "fields":"namedStyleType"
            }
        })
        reqs.append({"insertText":{"location":{"index":1},"text":text + "\n"}})
    else:
        reqs.append({"insertText":{"location":{"index":1},"text":text + "\n"}})
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()

def docs_insert_table(docs, doc_id: str, df: pd.DataFrame, title: str):
    # Insert title
    docs_insert_text(docs, doc_id, "", heading=title)
    rows, cols = df.shape
    reqs = [{"insertTable":{"location":{"index":1},"rows":rows+1,"columns":cols}}]
    # Header
    for j, col in enumerate(df.columns):
        reqs.append({
            "insertText":{
                "location":{"index":1},
                "text":str(col)
            }
        })
    # The simple approach above appends at top; for robust cell addressing we'd track indices.
    # To keep this concise, we’ll insert a CSV below the header as plain text (readable & robust).
    # (Docs cell addressing is verbose. If you want per-cell precision, I can expand it.)
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()
    csv_text = df.to_csv(index=False)
    docs_insert_text(docs, doc_id, csv_text)

def docs_insert_image(docs, doc_id: str, image_uri: str, caption: Optional[str]=None):
    reqs = [{
        "insertInlineImage": {
            "location": {"index": 1},
            "uri": image_uri,
            "objectSize": {"height": {"magnitude": 320, "unit": "PT"}}
        }
    }]
    if caption:
        reqs.append({"insertText":{"location":{"index":1},"text": caption + "\n"}})
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()

# -------------------------
# MAIN PIPELINE
# -------------------------

def run_pipeline():
    start = pd.to_datetime(CFG.start_date).date()
    end = pd.to_datetime(CFG.end_date).date()
    log.info(f"Fetching BMRS data {start} → {end}")

    bod = fetch_bod_acceptances(start, end)
    imp = fetch_imbalance_price_niv(start, end)
    dem = fetch_demand(start, end)
    mix = fetch_genmix(start, end)
    wx  = fetch_weather_daily(start, end)
    bmap = load_bmunit_map()

    log.info("Deriving KPIs…")
    daily = derive_daily_kpis(bod, imp, dem, mix, wx, bmap)
    write_parquet(daily, f"{CFG.out_dir}/daily_kpis.parquet")
    daily.to_csv(f"{CFG.tables_dir}/daily_kpis.csv", index=False)

    monthly = monthly_rollups(daily)
    monthly.to_csv(f"{CFG.tables_dir}/monthly_rollup.csv", index=False)

    kpis = kpi_table(daily)
    kpis.to_csv(f"{CFG.tables_dir}/headline_kpis.csv", index=False)

    log.info("Generating charts…")
    c1 = plot_trend_bal_volume(daily)
    c2 = plot_price_extremes(daily)
    c3 = plot_wind_vs_balancing(daily) if "wind_mwh" in daily else None
    c4 = plot_curtailment_share(daily)
    c5 = plot_price_histogram(daily)

    log.info("Building Google Doc report…")
    docs, drive = g_clients()
    doc_title = f"{CFG.doc_title_prefix} ({CFG.start_date}–{CFG.end_date})"
    doc_id = docs_create(docs, doc_title)

    summary_text = (
        f"Period: {CFG.start_date} to {CFG.end_date}\n"
        f"Total balancing volume: {kpis.loc[kpis['Metric'].eq('Total balancing volume (TWh)'),'Value'].values[0]:.2f} TWh\n"
        f"Avg volume-weighted price: £{kpis.loc[kpis['Metric'].eq('Avg volume-weighted price (£/MWh)'),'Value'].values[0]:.2f}/MWh\n"
        f"Max accepted price (daily): £{kpis.loc[kpis['Metric'].eq('Max accepted price (£/MWh)'),'Value'].values[0]:.0f}/MWh\n"
    )
    docs_insert_text(docs, doc_id, summary_text, heading="Executive Summary")

    # Upload charts to Drive and insert
    for path, caption in [
        (c1, "Monthly balancing volume"),
        (c2, "Daily volume-weighted accepted price"),
        (c3, "Wind vs Balancing Volume (daily)"),
        (c4, "Wind curtailment share (monthly)"),
        (c5, "Distribution of daily max accepted prices"),
    ]:
        if path:
            uri = drive_upload_image(drive, path, CFG.google_folder_id_for_images)
            docs_insert_image(docs, doc_id, uri, caption=caption or "")

    # Insert KPI table as CSV text (simple & robust)
    docs_insert_text(docs, doc_id, "", heading="Headline KPIs")
    docs_insert_text(docs, doc_id, kpis.to_csv(index=False))

    # Insert a small methods section
    methods = (
        "Methods\n"
        "- Data: Elexon BMRS (BOD, Imbalance Price & NIV, Demand, Fuel Mix); optional weather provider\n"
        "- Granularity: half-hourly → daily/monthly aggregations\n"
        "- Wind curtailment proxy: sum of accepted BID volumes from WIND BM Units (if mapping present)\n"
        "- KPIs: total balancing volume, offer/bid split, VW avg price, price extremes, wind share, NIV\n"
        "- Plots: matplotlib PNGs uploaded to Drive and embedded into this Doc\n"
    )
    docs_insert_text(docs, doc_id, methods, heading="Methods & Notes")

    log.info(f"Report created: https://docs.google.com/document/d/{doc_id}/edit")
    return doc_id

if __name__ == "__main__":
    doc_id = run_pipeline()
    print("Google Doc:", f"https://docs.google.com/document/d/{doc_id}/edit")
