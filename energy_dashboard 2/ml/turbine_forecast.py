"""Turbine-level ML forecasting (Phase 11 – neural net hook).

This uses a joblib-saved neural network model if present.
If not, it falls back to a simple persistence-style forecast.
"""
import os
import joblib
import pandas as pd
from .gsp_preprocessor import add_time_features

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models_turbine_nn")

def forecast_turbine_output(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df = add_time_features(df, "timestamp")
    features = [
        "forecast_mw",
        "actual_mw",
        "hr",
        "dow",
        "month",
    ]
    for col in features:
        if col not in df.columns:
            df[col] = 0

    # Group by turbine and forecast horizon
    out_rows = []
    model_loaded = False
    model = None
    model_path = os.path.join(MODELS_DIR, "turbine_nn.joblib")
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        model_loaded = True

    for tid, g in df.groupby("turbine_id"):
        g = g.sort_values("timestamp")
        X = g[features]
        if model_loaded:
            y_hat = model.predict(X)
        else:
            # Fallback: use latest actual as forecast
            y_hat = g["actual_mw"].shift(1).fillna(method="bfill").values
        g_out = g[["turbine_id", "timestamp", "lat", "lon"]].copy()
        g_out["forecast_mw"] = y_hat
        g_out["forecast_err_mw"] = g["actual_mw"] - g_out["forecast_mw"]
        out_rows.append(g_out)

    return pd.concat(out_rows, ignore_index=True)
