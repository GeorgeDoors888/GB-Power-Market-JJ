import matplotlib.pyplot as plt
import pandas as pd
from .chart_utils import ensure_out_dir, _empty_chart

def build_bess_chart(df_bess: pd.DataFrame, out_path: str):
    ensure_out_dir()
    if df_bess is None or df_bess.empty:
        return _empty_chart("BESS Availability", out_path)
    df = df_bess.copy()
    if "availability_ratio" not in df.columns:
        return _empty_chart("BESS Availability", out_path)
    df = df.sort_values("availability_ratio", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(df["bmUnit"], df["availability_ratio"] * 100.0)
    ax.set_title("Top BESS Units – Availability (%)")
    ax.set_ylabel("Availability %")
    ax.set_xticklabels(df["bmUnit"], rotation=45, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
