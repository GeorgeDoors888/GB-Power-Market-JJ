import os
import joblib
import pandas as pd
from .gsp_preprocessor import add_time_features

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models_bm")

def predict_bm_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df = add_time_features(df, "timestamp")
    features = [
        "sbp",
        "ssp",
        "system_imbalance_mw",
        "net_ic_flow_mw",
        "wind_delta_mw",
        "demand_delta_mw",
        "reserve_mw",
        "hr",
        "dow",
        "month",
    ]
    for col in features:
        if col not in df.columns:
            df[col] = 0
    sbp_path = os.path.join(MODELS_DIR, "sbp_next.joblib")
    ssp_path = os.path.join(MODELS_DIR, "ssp_next.joblib")
    if not (os.path.exists(sbp_path) and os.path.exists(ssp_path)):
        df["sbp_next"] = None
        df["ssp_next"] = None
        return df
    sbp_model = joblib.load(sbp_path)
    ssp_model = joblib.load(ssp_path)
    X = df[features]
    df["sbp_next"] = sbp_model.predict(X)
    df["ssp_next"] = ssp_model.predict(X)
    return df
