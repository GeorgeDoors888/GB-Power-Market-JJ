from __future__ import annotations
import pandas as pd

def add_time_features(df: pd.DataFrame, ts_col: str = "ts_halfhour") -> pd.DataFrame:
    ts = pd.to_datetime(df[ts_col])
    df = df.copy()
    df["hour"] = ts.dt.hour
    df["dow"] = ts.dt.dayofweek
    df["month"] = ts.dt.month
    return df
