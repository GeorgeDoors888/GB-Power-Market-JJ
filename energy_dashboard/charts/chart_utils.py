import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

OUT_DIR = Path("out")

def ensure_out_dir():
    OUT_DIR.mkdir(exist_ok=True, parents=True)

def _empty_chart(title: str, out_path: str):
    ensure_out_dir()
    plt.figure(figsize=(6, 3))
    plt.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=12)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return out_path

def _safe_ts(df: pd.DataFrame, col: str = "timestamp"):
    if col in df.columns:
        return pd.to_datetime(df[col])
    return pd.to_datetime(df.index)
