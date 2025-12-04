import pandas as pd

def score_wind_deviation(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    def band(err):
        if pd.isna(err):
            return "unknown"
        if err < 0.05:
            return "excellent"
        if err < 0.15:
            return "good"
        if err < 0.30:
            return "moderate"
        return "poor"
    df["err_band"] = df["pct_err"].apply(band)
    df["err_direction"] = df["delta"].apply(
        lambda d: "over" if d > 0 else ("under" if d < 0 else "on_target")
    )
    return df
