import os
import joblib
import pandas as pd
from .gsp_preprocessor import add_time_features

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models_constraints")

def predict_constraint_probability(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "gsp" not in df.columns:
        df["constraint_prob"] = None
        return df
    df = add_time_features(df, "timestamp")
    features = [
        "wind_delta_mw",
        "interconnector_flow_mw",
        "local_demand_mw",
        "embedded_generation_mw",
        "system_price",
        "hr",
        "dow",
    ]
    for col in features:
        if col not in df.columns:
            df[col] = 0
    df["constraint_prob"] = None
    for gsp, g in df.groupby("gsp"):
        path = os.path.join(MODELS_DIR, f"gsp_{gsp}.joblib")
        if not os.path.exists(path):
            continue
        model = joblib.load(path)
        df.loc[g.index, "constraint_prob"] = model.predict_proba(g[features])[:, 1]
    return df
