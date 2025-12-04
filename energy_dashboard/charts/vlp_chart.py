import matplotlib.pyplot as plt
import pandas as pd
from .chart_utils import ensure_out_dir, _empty_chart

def build_vlp_chart(df_vlp: pd.DataFrame, out_path: str):
    ensure_out_dir()
    if df_vlp is None or df_vlp.empty:
        return _empty_chart("VLP KPIs", out_path)
    row = df_vlp.iloc[0]
    units = int(row.get("unit_count", 0))
    cap = float(row.get("total_capacity_mw", 0.0))
    fig, ax = plt.subplots(figsize=(5, 3))
    labels = ["Units", "Capacity (MW)"]
    values = [units, cap]
    ax.bar(labels, values)
    ax.set_title("VLP Portfolio KPIs")
    ax.set_ylabel("Value")
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
