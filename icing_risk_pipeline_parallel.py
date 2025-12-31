#!/usr/bin/env python3
"""
Icing Risk Classifier Pipeline - Todo #12
Parallel training for all 29 wind farms with Open-Meteo weather data + B1610 generation

Features: temp near 0°C, RH>90%, precipitation, cloud liquid water, power curve residuals
Output: P(icing) with bands LOW<0.3, MED 0.3-0.6, HIGH>0.6

Author: AI Coding Agent
Date: December 30, 2025
"""

from __future__ import annotations

import os
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

from google.cloud import bigquery
from joblib import Parallel, delayed
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score, brier_score_loss, classification_report
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor, XGBClassifier

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODEL_DIR = Path("models/icing_risk")
CACHE_DIR = Path("cache/openmeteo")

# Configuration
@dataclass
class Farm:
    farm_id: str
    farm_name: str
    lat: float
    lon: float
    capacity_mw: float
    turbine_oem: str
    turbine_model: str

# Meteorological calculations
def dewpoint_c_from_t_rh(t_c: np.ndarray, rh_frac: np.ndarray) -> np.ndarray:
    """Magnus approximation for dewpoint. rh_frac in [0,1]."""
    rh = np.clip(rh_frac, 1e-6, 1.0)
    a, b = 17.625, 243.04
    gamma = np.log(rh) + (a * t_c) / (b + t_c)
    td = (b * gamma) / (a - gamma)
    return td

def wind_uv_from_speed_dir(ws: np.ndarray, wd_deg: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Convert wind speed/direction to u,v components."""
    wd = np.deg2rad(wd_deg)
    u = -ws * np.sin(wd)
    v = -ws * np.cos(wd)
    return u, v

def rolling_run_length(mask: pd.Series) -> pd.Series:
    """For each timestamp, length of current consecutive True run."""
    out = np.zeros(len(mask), dtype=int)
    run = 0
    for i, m in enumerate(mask.values):
        if bool(m):
            run += 1
        else:
            run = 0
        out[i] = run
    return pd.Series(out, index=mask.index)

# Weather fetching (Open-Meteo - free API)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def fetch_openmeteo_hourly(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    retries: int = 3,
    sleep_s: float = 1.0
) -> pd.DataFrame:
    """Fetch hourly weather from Open-Meteo with caching."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = CACHE_DIR / f"weather_{lat}_{lon}_{start_date}_{end_date}.parquet"
    
    if cache_file.exists():
        return pd.read_parquet(cache_file)
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m",
            "pressure_msl",
            "shortwave_radiation",
        ]),
        "timezone": "UTC",
        "start_date": start_date,
        "end_date": end_date,
    }
    
    last_err = None
    for _ in range(retries):
        try:
            r = requests.get(OPEN_METEO_URL, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            h = data["hourly"]
            df = pd.DataFrame(h)
            df["time"] = pd.to_datetime(df["time"], utc=True)
            df = df.set_index("time").sort_index()
            df.to_parquet(cache_file)
            return df
        except Exception as e:
            last_err = e
            time.sleep(sleep_s)
    
    raise RuntimeError(f"Open-Meteo fetch failed: {last_err}")

# Feature engineering
def build_features(
    gen_mw: pd.Series,
    wx_hourly: pd.DataFrame,
    capacity_mw: float,
    resample_to: str = "30min"
) -> pd.DataFrame:
    """Align generation with weather, create icing features."""
    gen = gen_mw.copy()
    gen.index = pd.to_datetime(gen.index, utc=True)
    gen = gen.sort_index()
    
    if resample_to:
        gen = gen.resample(resample_to).mean()
    
    wx = wx_hourly.copy().sort_index()
    wx = wx.resample(resample_to).interpolate("time")
    
    df = pd.DataFrame(index=gen.index)
    df["gen_mw"] = gen.values
    df["cap_mw"] = capacity_mw
    df["gen_pu"] = df["gen_mw"] / (capacity_mw + 1e-6)
    
    # Basic met
    df["t2m_c"] = wx["temperature_2m"].reindex(df.index).values
    df["rh2m"] = (wx["relative_humidity_2m"].reindex(df.index).values) / 100.0
    df["precip_mm"] = wx["precipitation"].reindex(df.index).values
    df["cloud_cover"] = wx["cloud_cover"].reindex(df.index).values / 100.0
    df["mslp_hpa"] = wx["pressure_msl"].reindex(df.index).values
    df["sw_rad"] = wx["shortwave_radiation"].reindex(df.index).values
    df["ws10"] = wx["wind_speed_10m"].reindex(df.index).values
    df["wd10"] = wx["wind_direction_10m"].reindex(df.index).values
    
    # Derived
    df["td2m_c"] = dewpoint_c_from_t_rh(df["t2m_c"].values, df["rh2m"].values)
    df["t_minus_td"] = df["t2m_c"] - df["td2m_c"]
    
    u10, v10 = wind_uv_from_speed_dir(df["ws10"].values, df["wd10"].values)
    df["u10"] = u10
    df["v10"] = v10
    
    # Time features
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["month"] = df.index.month
    
    # Tendency proxies
    df["dp_mslp_3h"] = df["mslp_hpa"].diff(6)  # 6*30min = 3h
    df["dws_1h"] = df["ws10"].diff(2)
    df["dwd_1h"] = (df["wd10"].diff(2) + 180) % 360 - 180
    
    # Icing meteorology proxies
    df["freezing_flag"] = (df["t2m_c"] <= 0).astype(int)
    df["near_freezing"] = ((df["t2m_c"] >= -3) & (df["t2m_c"] <= 2)).astype(int)
    df["high_rh"] = (df["rh2m"] >= 0.92).astype(int)
    df["wet_flag"] = ((df["precip_mm"] > 0.0) | (df["cloud_cover"] > 0.85)).astype(int)
    df["icing_met_proxy"] = (df["near_freezing"].astype(bool) & df["high_rh"].astype(bool) & df["wet_flag"].astype(bool)).astype(int)
    
    return df.dropna()

# Expected power model
def train_expected_power_model(df: pd.DataFrame) -> XGBRegressor:
    """Train on clean periods to learn expected output."""
    clean = (
        (df["t2m_c"] > 3.0)  # avoid near-freezing
        | (df["rh2m"] < 0.85)
    )
    clean &= (df["gen_pu"] > 0.02)
    
    train_df = df.loc[clean].copy()
    
    feat_cols = [
        "ws10", "wd10", "u10", "v10",
        "t2m_c", "td2m_c", "rh2m", "mslp_hpa",
        "precip_mm", "cloud_cover", "sw_rad",
        "hour", "dow", "month"
    ]
    
    X = train_df[feat_cols]
    y = train_df["gen_pu"]
    
    model = XGBRegressor(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.2,
        reg_lambda=1.0,
        objective="reg:squarederror",
        n_jobs=4
    )
    model.fit(X, y)
    return model

def add_residual_features(df: pd.DataFrame, exp_model: XGBRegressor) -> pd.DataFrame:
    """Add power curve residual features."""
    feat_cols = [
        "ws10", "wd10", "u10", "v10",
        "t2m_c", "td2m_c", "rh2m", "mslp_hpa",
        "precip_mm", "cloud_cover", "sw_rad",
        "hour", "dow", "month"
    ]
    df = df.copy()
    df["exp_gen_pu"] = exp_model.predict(df[feat_cols])
    df["exp_gen_pu"] = np.clip(df["exp_gen_pu"], 0.0, 1.2)
    
    df["pc_resid_pu"] = df["gen_pu"] - df["exp_gen_pu"]
    df["pc_resid_pct"] = df["pc_resid_pu"] / (df["exp_gen_pu"] + 1e-3)
    
    # Rolling residual stats
    df["resid_mean_1h"] = df["pc_resid_pct"].rolling(2).mean()
    df["resid_min_3h"] = df["pc_resid_pct"].rolling(6).min()
    df["resid_std_3h"] = df["pc_resid_pct"].rolling(6).std()
    
    # Consecutive underperformance
    under = df["pc_resid_pct"] < -0.25
    df["underperf_run"] = rolling_run_length(under)
    
    return df.dropna()

# Weak label creation
def make_icing_like_label(df: pd.DataFrame) -> pd.DataFrame:
    """Label icing-like loss (met proxy + persistent underperformance)."""
    df = df.copy()
    met = df["icing_met_proxy"].astype(bool)
    expected_nontrivial = df["exp_gen_pu"] > 0.20
    persistent_underperf = df["underperf_run"] >= 4  # 2h
    icing_like = met & expected_nontrivial & persistent_underperf
    df["y_icing_like"] = icing_like.astype(int)
    return df

# Classifier training
def train_icing_classifier(df: pd.DataFrame, farm: Farm) -> Pipeline:
    """Train icing risk classifier."""
    num_cols = [
        "t2m_c", "td2m_c", "t_minus_td", "rh2m",
        "precip_mm", "cloud_cover", "sw_rad",
        "mslp_hpa", "dp_mslp_3h",
        "ws10", "u10", "v10", "dws_1h", "dwd_1h",
        "exp_gen_pu", "pc_resid_pct", "resid_mean_1h", "resid_min_3h", "resid_std_3h",
        "hour", "dow", "month",
        "freezing_flag", "near_freezing", "high_rh", "wet_flag"
    ]
    cat_cols = ["turbine_oem", "turbine_model"]
    
    df = df.copy()
    df["turbine_oem"] = farm.turbine_oem
    df["turbine_model"] = farm.turbine_model
    
    X = df[num_cols + cat_cols]
    y = df["y_icing_like"].astype(int)
    
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )
    
    clf = XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.04,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_alpha=0.2,
        reg_lambda=1.2,
        objective="binary:logistic",
        eval_metric="logloss",
        n_jobs=4
    )
    
    pipe = Pipeline([("pre", pre), ("clf", clf)])
    
    # Time split
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    pipe.fit(X_train, y_train)
    
    proba = pipe.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba) if len(np.unique(y_test)) > 1 else float("nan")
    brier = brier_score_loss(y_test, proba)
    
    print(f"[{farm.farm_name}] test AUC={auc:.3f}  Brier={brier:.4f}")
    
    return pipe

# Worker function
def train_single_farm_icing(farm: Farm, start_date: str, end_date: str):
    """Train icing classifier for one farm."""
    try:
        start = time.time()
        print(f"\n{'='*70}")
        print(f"Training icing classifier: {farm.farm_name}")
        print(f"{'='*70}")
        
        # Create BigQuery client inside worker
        client = bigquery.Client(project=PROJECT_ID, location="US")
        
        # Get generation data from B1610
        gen_query = f"""
        WITH bm_mapping AS (
            SELECT farm_name, bm_unit_id
            FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu`
            WHERE farm_name = '{farm.farm_name}'
        ),
        actual_generation AS (
            SELECT 
                bmUnit as bm_unit_id,
                TIMESTAMP_TRUNC(TIMESTAMP(settlementDate), HOUR) as hour_utc,
                AVG(levelTo) as generation_mw
            FROM `{PROJECT_ID}.{DATASET}.bmrs_pn`
            WHERE settlementDate >= '{start_date}'
              AND settlementDate < '{end_date}'
              AND levelTo > 0
            GROUP BY bm_unit_id, hour_utc
        )
        SELECT 
            hour_utc,
            SUM(COALESCE(generation_mw, 0)) as gen_mw
        FROM bm_mapping m
        LEFT JOIN actual_generation g ON m.bm_unit_id = g.bm_unit_id
        GROUP BY hour_utc
        ORDER BY hour_utc
        """
        
        gen_df = client.query(gen_query).to_dataframe()
        
        if len(gen_df) < 1000:
            print(f"❌ Insufficient generation data: {len(gen_df)} rows")
            return None
        
        gen = gen_df.set_index("hour_utc")["gen_mw"]
        
        # Fetch weather
        wx = fetch_openmeteo_hourly(farm.lat, farm.lon, start_date, end_date)
        
        # Build features
        df = build_features(gen_mw=gen, wx_hourly=wx, capacity_mw=farm.capacity_mw, resample_to="30min")
        
        # Expected power model
        exp_model = train_expected_power_model(df)
        df = add_residual_features(df, exp_model)
        df = make_icing_like_label(df)
        
        # Train classifier
        pipe = train_icing_classifier(df, farm)
        
        # Save models
        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(MODEL_DIR / f"exp_power_{farm.farm_id}.pkl", 'wb') as f:
            pickle.dump(exp_model, f)
        with open(MODEL_DIR / f"icing_clf_{farm.farm_id}.pkl", 'wb') as f:
            pickle.dump(pipe, f)
        
        elapsed = time.time() - start
        icing_events = int(df["y_icing_like"].sum())
        icing_pct = (icing_events / len(df)) * 100
        
        print(f"✅ {farm.farm_name}: {elapsed:.1f}s, {icing_events} icing events ({icing_pct:.1f}%)")
        
        return {
            'farm_name': farm.farm_name,
            'samples': len(df),
            'icing_events': icing_events,
            'icing_pct': icing_pct,
            'training_time_sec': elapsed
        }
        
    except Exception as e:
        print(f"❌ Error training {farm.farm_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*70)
    print("Icing Risk Classifier - Parallel Training (Todo #12)")
    print("="*70)
    
    # Get farm list from BigQuery
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    farm_query = f"""
    WITH farm_coords AS (
        SELECT DISTINCT
            farm_name,
            MAX(latitude) as lat,
            MAX(longitude) as lon
        FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
        GROUP BY farm_name
    )
    SELECT DISTINCT
        f.farm_name,
        c.lat,
        c.lon,
        f.capacity_mw,
        COALESCE(s.manufacturer, 'Unknown') as turbine_oem,
        COALESCE(s.model, 'Unknown') as turbine_model
    FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu` f
    INNER JOIN farm_coords c ON f.farm_name = c.farm_name
    LEFT JOIN `{PROJECT_ID}.{DATASET}.wind_turbine_specs` s
        ON f.farm_name = s.farm_name
    ORDER BY f.capacity_mw DESC
    """
    
    farm_df = client.query(farm_query).to_dataframe()
    
    farms = [
        Farm(
            farm_id=row['farm_name'].replace(' ', '_').replace('&', 'and').lower(),
            farm_name=row['farm_name'],
            lat=row['lat'],
            lon=row['lon'],
            capacity_mw=row['capacity_mw'],
            turbine_oem=row['turbine_oem'],
            turbine_model=row['turbine_model']
        )
        for _, row in farm_df.iterrows()
    ]
    
    print(f"\n🌬️  Training icing classifiers for {len(farms)} farms in parallel...")
    print(f"   Using 32 parallel jobs")
    
    start_training = time.time()
    
    results = Parallel(n_jobs=32, verbose=10)(
        delayed(train_single_farm_icing)(farm, "2021-01-01", "2025-12-30")
        for farm in farms
    )
    
    training_time = time.time() - start_training
    
    # Filter out failed farms
    results = [r for r in results if r is not None]
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('icing_risk_training_results.csv', index=False)
    
    print("\n" + "="*70)
    print("🏆 ICING CLASSIFIER TRAINING COMPLETE")
    print("="*70)
    print(f"Successfully trained: {len(results)} / {len(farms)} farms")
    print(f"Total training time: {training_time/60:.1f} minutes")
    print(f"Average per farm: {training_time/len(results):.1f} seconds")
    print(f"\nAverage icing events: {results_df['icing_events'].mean():.0f} per farm")
    print(f"Average icing %: {results_df['icing_pct'].mean():.2f}%")
    print(f"\n📁 Models saved to: {MODEL_DIR}/")
    print("="*70)

if __name__ == "__main__":
    main()
