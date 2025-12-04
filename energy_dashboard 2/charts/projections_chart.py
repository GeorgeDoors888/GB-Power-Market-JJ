import matplotlib.pyplot as plt
from .chart_utils import ensure_out_dir, _empty_chart

def build_projections_chart(projections, out_path: str):
    ensure_out_dir()
    if not projections:
        return _empty_chart("10-Year Projection", out_path)
    years = [p.year for p in projections]
    net = [p.net for p in projections]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(years, net)
    ax.set_title("Net Revenue Projection (10 Years)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Net £/year")
    for x, v in zip(years, net):
        ax.text(x, v, f"{v/1e3:,.0f}k", ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
