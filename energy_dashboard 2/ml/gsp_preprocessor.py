import pandas as pd

def add_time_features(df: pd.DataFrame, ts_col: str = "timestamp") -> pd.DataFrame:
    df = df.copy()
    ts = pd.to_datetime(df[ts_col])
    df["hr"] = ts.dt.hour
    df["dow"] = ts.dt.dayofweek + 1
    df["month"] = ts.dt.month
    return df
