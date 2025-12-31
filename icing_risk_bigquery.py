#!/usr/bin/env python3
"""
Icing Risk Classifier - BigQuery Version (Todo #12)
Uses existing openmeteo_wind_historic data from BigQuery instead of API calls

Author: AI Coding Agent  
Date: December 30, 2025
"""

from __future__ import annotations

import os
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from google.cloud import bigquery
from joblib import Parallel, delayed
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor, XGBClassifier

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
MODEL_DIR = Path("models/icing_risk")

@dataclass
class Farm:
    farm_id: str
    farm_name: str
    capacity_mw: float
    turbine_oem: str
    turbine_model: str

def dewpoint_c_from_t_rh(t_c: np.ndarray, rh_frac: np.ndarray) -> np.ndarray:
    rh = np.clip(rh_frac, 1e-6, 1.0)
    a, b = 17.625, 243.04
    gamma = np.log(rh) + (a * t_c) / (b + t_c)
    td = (b * gamma) / (a - gamma)
    return td

def wind_uv_from_speed_dir(ws: np.ndarray, wd_deg: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    wd = np.deg2rad(wd_deg)
    u = -ws * np.sin(wd)
    v = -ws * np.cos(wd)
    return u, v

def rolling_run_length(mask: pd.Series) -> pd.Series:
    out = np.zeros(len(mask), dtype=int)
    run = 0
    for i, m in enumerate(mask.values):
        if bool(m):
            run += 1
        else:
            run = 0
        out[i] = run
    return pd.Series(out, index=mask.index)

def train_expected_power_model(df: pd.DataFrame) -> XGBRegressor:
    clean = (
        (df["t2m_c"] > 3.0) | (df["rh2m"] < 0.85)
    )
    clean &= (df["gen_pu"] > 0.02)
    train_df = df.loc[clean].copy()
    
    feat_cols = [
        "ws10", "wd10", "u10", "v10",
        "t2m_c", "td2m_c", "rh2m",
        "hour", "dow", "month"
    ]
    
    X = train_df[feat_cols]
    y = train_df["gen_pu"]
    
    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.2,
        reg_lambda=1.0,
        n_jobs=4
    )
    model.fit(X, y)
    return model

def add_residual_features(df: pd.DataFrame, exp_model: XGBRegressor) -> pd.DataFrame:
    feat_cols = [
        "ws10", "wd10", "u10", "v10",
        "t2m_c", "td2m_c", "rh2m",
        "hour", "dow", "month"
    ]
    df = df.copy()
    df["exp_gen_pu"] = exp_model.predict(df[feat_cols])
    df["exp_gen_pu"] = np.clip(df["exp_gen_pu"], 0.0, 1.2)
    
    df["pc_resid_pu"] = df["gen_pu"] - df["exp_gen_pu"]
    df["pc_resid_pct"] = df["pc_resid_pu"] / (df["exp_gen_pu"] + 1e-3)
    
    df["resid_mean_1h"] = df["pc_resid_pct"].rolling(2).mean()
    df["resid_min_3h"] = df["pc_resid_pct"].rolling(6).min()
    df["resid_std_3h"] = df["pc_resid_pct"].rolling(6).std()
    
    under = df["pc_resid_pct"] < -0.25
    df["underperf_run"] = rolling_run_length(under)
    
    return df.dropna()

def make_icing_like_label(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    met = df["icing_met_proxy"].astype(bool)
    expected_nontrivial = df["exp_gen_pu"] > 0.20
    persistent_underperf = df["underperf_run"] >= 4
    icing_like = met & expected_nontrivial & persistent_underperf
    df["y_icing_like"] = icing_like.astype(int)
    return df

def train_icing_classifier(df: pd.DataFrame, farm: Farm) -> Pipeline:
    num_cols = [
        "t2m_c", "td2m_c", "t_minus_td", "rh2m",
        "ws10", "u10", "v10",
        "exp_gen_pu", "pc_resid_pct", "resid_mean_1h", "resid_min_3h", "resid_std_3h",
        "hour", "dow", "month",
        "freezing_flag", "near_freezing", "high_rh"
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
        n_jobs=4
    )
    
    pipe = Pipeline([("pre", pre), ("clf", clf)])
    
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    pipe.fit(X_train, y_train)
    
    proba = pipe.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba) if len(np.unique(y_test)) > 1 else float("nan")
    brier = brier_score_loss(y_test, proba)
    
    print(f"[{farm.farm_name}] AUC={auc:.3f} Brier={brier:.4f}")
    
    return pipe

def train_single_farm_icing(farm: Farm):
    """Train icing classifier using BigQuery data."""
    try:
        start = time.time()
        print(f"\n{'='*70}")
        print(f"Training: {farm.farm_name}")
        print(f"{'='*70}")
        
        client = bigquery.Client(project=PROJECT_ID, location="US")
        
        # Fetch merged weather + generation data from BigQuery
        query = f"""
        WITH weather_data AS (
            SELECT 
                farm_name,
                TIMESTAMP_TRUNC(time_utc, HOUR) as hour_utc,
                AVG(wind_speed_100m) as wind_speed_100m,
                AVG(wind_speed_10m) as wind_speed_10m,
                AVG(wind_direction_10m) as wind_direction_10m,
                AVG(temperature_2m) as temperature_2m,
                AVG(relative_humidity_2m) as relative_humidity_2m,
                MAX(precipitation) as precipitation,
                MAX(cloud_cover) as cloud_cover,
                EXTRACT(HOUR FROM time_utc) as hour,
                EXTRACT(DAYOFWEEK FROM time_utc) as dow,
                EXTRACT(MONTH FROM time_utc) as month
            FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
            WHERE farm_name = '{farm.farm_name}'
              AND time_utc >= '2021-01-01'
              AND time_utc < '2025-12-30'
            GROUP BY farm_name, hour_utc, hour, dow, month
        ),
        bm_mapping AS (
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
            WHERE settlementDate >= '2021-01-01'
              AND settlementDate < '2025-12-30'
              AND levelTo > 0
            GROUP BY bm_unit_id, hour_utc
        )
        SELECT 
            w.*,
            COALESCE(g.generation_mw, 0) as generation_mw
        FROM weather_data w
        INNER JOIN bm_mapping m ON w.farm_name = m.farm_name
        LEFT JOIN actual_generation g ON m.bm_unit_id = g.bm_unit_id AND w.hour_utc = g.hour_utc
        ORDER BY w.hour_utc
        """
        
        df = client.query(query).to_dataframe()
        
        if len(df) < 1000:
            print(f"❌ Insufficient data: {len(df)} rows")
            return None
        
        # Feature engineering
        df["gen_pu"] = df["generation_mw"] / (farm.capacity_mw + 1e-6)
        df["t2m_c"] = df["temperature_2m"]
        df["rh2m"] = df["relative_humidity_2m"] / 100.0
        df["ws10"] = df["wind_speed_10m"]
        df["wd10"] = df["wind_direction_10m"]
        
        df["td2m_c"] = dewpoint_c_from_t_rh(df["t2m_c"].values, df["rh2m"].values)
        df["t_minus_td"] = df["t2m_c"] - df["td2m_c"]
        
        u10, v10 = wind_uv_from_speed_dir(df["ws10"].values, df["wd10"].values)
        df["u10"] = u10
        df["v10"] = v10
        
        # Icing proxies
        df["freezing_flag"] = (df["t2m_c"] <= 0).astype(int)
        df["near_freezing"] = ((df["t2m_c"] >= -3) & (df["t2m_c"] <= 2)).astype(int)
        df["high_rh"] = (df["rh2m"] >= 0.92).astype(int)
        df["wet_flag"] = ((df["precipitation"] > 0) | (df["cloud_cover"] > 85)).astype(int)
        df["icing_met_proxy"] = (df["near_freezing"].astype(bool) & df["high_rh"].astype(bool) & df["wet_flag"].astype(bool)).astype(int)
        
        df = df.dropna()
        
        if len(df) < 1000:
            print(f"❌ Insufficient data after dropna: {len(df)} rows")
            return None
        
        # Train models
        exp_model = train_expected_power_model(df)
        df = add_residual_features(df, exp_model)
        df = make_icing_like_label(df)
        
        pipe = train_icing_classifier(df, farm)
        
        # Save
        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(MODEL_DIR / f"exp_power_{farm.farm_id}.pkl", 'wb') as f:
            pickle.dump(exp_model, f)
        with open(MODEL_DIR / f"icing_clf_{farm.farm_id}.pkl", 'wb') as f:
            pickle.dump(pipe, f)
        
        elapsed = time.time() - start
        icing_events = int(df["y_icing_like"].sum())
        icing_pct = (icing_events / len(df)) * 100
        
        print(f"✅ {farm.farm_name}: {elapsed:.1f}s, {icing_events} events ({icing_pct:.1f}%)")
        
        return {
            'farm_name': farm.farm_name,
            'samples': len(df),
            'icing_events': icing_events,
            'icing_pct': icing_pct,
            'training_time_sec': elapsed
        }
        
    except Exception as e:
        print(f"❌ Error: {farm.farm_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*70)
    print("Icing Risk Classifier - BigQuery Version (Todo #12)")
    print("="*70)
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    farm_query = f"""
    SELECT DISTINCT
        f.farm_name,
        f.capacity_mw,
        COALESCE(s.manufacturer, 'Unknown') as turbine_oem,
        COALESCE(s.model, 'Unknown') as turbine_model
    FROM `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu` f
    LEFT JOIN `{PROJECT_ID}.{DATASET}.wind_turbine_specs` s
        ON f.farm_name = s.farm_name
    WHERE f.farm_name IN (
        SELECT DISTINCT farm_name 
        FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    )
    ORDER BY f.capacity_mw DESC
    """
    
    farm_df = client.query(farm_query).to_dataframe()
    
    farms = [
        Farm(
            farm_id=row['farm_name'].replace(' ', '_').replace('&', 'and').lower(),
            farm_name=row['farm_name'],
            capacity_mw=row['capacity_mw'],
            turbine_oem=row['turbine_oem'],
            turbine_model=row['turbine_model']
        )
        for _, row in farm_df.iterrows()
    ]
    
    print(f"\n🌬️  Training {len(farms)} farms in parallel (32 cores)...")
    
    start_training = time.time()
    
    results = Parallel(n_jobs=32, verbose=10)(
        delayed(train_single_farm_icing)(farm)
        for farm in farms
    )
    
    training_time = time.time() - start_training
    results = [r for r in results if r is not None]
    
    results_df = pd.DataFrame(results)
    results_df.to_csv('icing_risk_training_results.csv', index=False)
    
    print("\n" + "="*70)
    print("🏆 ICING CLASSIFIER TRAINING COMPLETE")
    print("="*70)
    print(f"Successfully trained: {len(results)} / {len(farms)} farms")
    print(f"Total time: {training_time/60:.1f} minutes")
    print(f"Avg per farm: {training_time/len(results):.1f} seconds")
    print(f"\nAvg icing events: {results_df['icing_events'].mean():.0f}")
    print(f"Avg icing %: {results_df['icing_pct'].mean():.2f}%")
    print(f"\n📁 Models: {MODEL_DIR}/")
    print("="*70)

if __name__ == "__main__":
    main()
