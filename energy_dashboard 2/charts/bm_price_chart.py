import matplotlib.pyplot as plt
import pandas as pd
from .chart_utils import ensure_out_dir, _empty_chart, _safe_ts

def build_bm_price_chart(df_bm: pd.DataFrame, out_path: str):
    ensure_out_dir()
    if df_bm is None or df_bm.empty:
        return _empty_chart("BM Price Forecast", out_path)
    df = df_bm.copy()
    df["timestamp"] = _safe_ts(df, "timestamp")
    fig, ax = plt.subplots(figsize=(6, 3))
    if "sbp" in df.columns:
        ax.plot(df["timestamp"], df["sbp"], label="SBP actual", linewidth=1)
    if "sbp_next" in df.columns:
        ax.plot(df["timestamp"], df["sbp_next"], label="SBP forecast", linestyle="--", linewidth=1)
    if "ssp" in df.columns:
        ax.plot(df["timestamp"], df["ssp"], label="SSP actual", linewidth=1)
    if "ssp_next" in df.columns:
        ax.plot(df["timestamp"], df["ssp_next"], label="SSP forecast", linestyle="--", linewidth=1)
    ax.set_title("BM Prices – Actual vs Forecast")
    ax.set_ylabel("£/MWh")
    ax.set_xlabel("Time")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    plt.xticks(rotation=45, ha="right", fontsize=7)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
