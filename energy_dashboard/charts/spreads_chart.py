import matplotlib.pyplot as plt
import pandas as pd
from .chart_utils import ensure_out_dir, _empty_chart, _safe_ts

def build_spreads_chart(df_spreads: pd.DataFrame, out_path: str):
    ensure_out_dir()
    if df_spreads is None or df_spreads.empty:
        return _empty_chart("SSP/SBP Spreads", out_path)
    df = df_spreads.copy()
    df["timestamp"] = _safe_ts(df, "timestamp")
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(df["timestamp"], df["ssp"], label="SSP")
    ax.plot(df["timestamp"], df["sbp"], label="SBP")
    if "spread" in df.columns:
        ax.plot(df["timestamp"], df["spread"], label="Spread")
    ax.set_title("System Prices & Spread")
    ax.set_ylabel("£/MWh")
    ax.set_xlabel("Time")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    plt.xticks(rotation=45, ha="right", fontsize=7)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
