import matplotlib.pyplot as plt
import pandas as pd
from .chart_utils import ensure_out_dir, _empty_chart, _safe_ts

def build_wind_chart(df_wind: pd.DataFrame, out_path: str):
    ensure_out_dir()
    if df_wind is None or df_wind.empty:
        return _empty_chart("Offshore Wind Forecast Error", out_path)
    df = df_wind.copy()
    if "pct_err" not in df.columns:
        return _empty_chart("Offshore Wind Forecast Error", out_path)
    df["timestamp"] = _safe_ts(df, "timestamp")
    df["abs_err"] = df["pct_err"].abs()
    daily = df.groupby(df["timestamp"].dt.date)["abs_err"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(daily["timestamp"], daily["abs_err"] * 100.0, marker="o", linewidth=1.5)
    ax.set_title("Offshore Wind – Avg Forecast Error")
    ax.set_ylabel("Mean absolute error (%)")
    ax.set_xlabel("Date")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    plt.xticks(rotation=45, ha="right", fontsize=7)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
