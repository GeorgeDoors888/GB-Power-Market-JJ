"""
BtM PPA Revenue Chart

Visualizes Behind-the-Meter PPA revenue breakdown:
- Revenue by stream (Direct Import vs Battery+VLP)
- Charging strategy breakdown
- RED coverage visualization
- Annual profit waterfall
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, Any, Optional
import numpy as np


def build_btm_ppa_chart(btm_results: Dict[str, Any], curtailment: Dict[str, float], 
                         output_path: str = "out/btm_ppa_chart.png") -> str:
    """
    Build comprehensive BtM PPA revenue visualization.
    
    Args:
        btm_results: Results from calculate_btm_ppa_revenue()
        curtailment: Curtailment revenue dict from get_curtailment_annual()
        output_path: Where to save the PNG
        
    Returns:
        Path to saved chart
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('BtM PPA Revenue Analysis', fontsize=16, fontweight='bold')
    
    # Extract data
    s1 = btm_results["stream1"]
    s2 = btm_results["stream2"]
    
    # --------------------- Chart 1: Revenue Streams ---------------------
    ax1 = axes[0, 0]
    
    streams = ['Stream 1\n(Direct Import)', 'Stream 2\n(Battery+VLP)', 'Dynamic\nContainment', 'Total']
    revenues = [
        s1["profit"],
        s2["profit"],
        195458,  # DC_ANNUAL_REVENUE
        btm_results["total_profit"]
    ]
    colors = ['#3498db', '#2ecc71', '#9b59b6', '#e74c3c']
    
    bars = ax1.bar(streams, revenues, color=colors, edgecolor='black', linewidth=1.5)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax1.set_ylabel('Annual Profit (£)', fontsize=12, fontweight='bold')
    ax1.set_title('Revenue Streams Breakdown', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        label = f'£{height:,.0f}'
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                label, ha='center', va='bottom' if height >= 0 else 'top',
                fontsize=10, fontweight='bold')
    
    # --------------------- Chart 2: Charging Strategy ---------------------
    ax2 = axes[0, 1]
    
    charging_data = {
        'GREEN': s2["green_charge"],
        'AMBER': s2["amber_charge"],
        'RED': s2["red_charge"]
    }
    
    total_charging = sum(charging_data.values())
    
    if total_charging > 0:
        colors_charging = ['#2ecc71', '#f39c12', '#e74c3c']
        wedges, texts, autotexts = ax2.pie(
            charging_data.values(),
            labels=charging_data.keys(),
            colors=colors_charging,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': 'black', 'linewidth': 1.5}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)
        
        # Add legend with MWh values
        legend_labels = [f'{k}: {v:,.0f} MWh' for k, v in charging_data.items()]
        ax2.legend(legend_labels, loc='lower left', fontsize=9)
    else:
        # No charging data - show message
        ax2.text(0.5, 0.5, 'No Charging Data\n(System prices too high\nor no BMRS data)', 
                ha='center', va='center', fontsize=12, transform=ax2.transAxes)
        ax2.set_xlim(-1, 1)
        ax2.set_ylim(-1, 1)
    
    ax2.set_title(f'Battery Charging Strategy\n({s2["cycles"]:.1f} cycles/year)', 
                  fontsize=13, fontweight='bold')
    
    # --------------------- Chart 3: RED Coverage ---------------------
    ax3 = axes[1, 0]
    
    red_coverage = btm_results["red_coverage"]
    
    if red_coverage > 0:
        coverage_data = [red_coverage, 100 - red_coverage]
        colors_coverage = ['#2ecc71', '#ecf0f1']
        
        wedges, texts, autotexts = ax3.pie(
            coverage_data,
            labels=['Battery\nCovered', 'Direct Import\n(Not Economic)'],
            colors=colors_coverage,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': 'black', 'linewidth': 1.5}
        )
        
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)
    else:
        # No RED coverage - show message
        ax3.text(0.5, 0.5, 'No RED Coverage\n(Battery not charging)', 
                ha='center', va='center', fontsize=12, transform=ax3.transAxes)
        ax3.set_xlim(-1, 1)
        ax3.set_ylim(-1, 1)
    
    ax3.set_title(f'RED Period Coverage\n(Battery serves {s2["red_discharge"]:,.0f} MWh)', 
                  fontsize=13, fontweight='bold')
    
    # --------------------- Chart 4: Cost Breakdown ---------------------
    ax4 = axes[1, 1]
    
    costs_per_band = btm_results["costs_per_band"]
    system_prices = btm_results["system_prices"]
    
    bands = ['GREEN', 'AMBER', 'RED']
    x_pos = np.arange(len(bands))
    width = 0.25
    
    # System buy price
    sbp = [system_prices['green'], system_prices['amber'], system_prices['red']]
    # DUoS
    duos = [0.11, 2.05, 17.64]
    # Levies
    levies = [98.15, 98.15, 98.15]
    
    bars1 = ax4.bar(x_pos - width, sbp, width, label='System Buy Price', 
                    color='#3498db', edgecolor='black')
    bars2 = ax4.bar(x_pos, duos, width, label='DUoS', 
                    color='#f39c12', edgecolor='black')
    bars3 = ax4.bar(x_pos + width, levies, width, label='Fixed Levies', 
                    color='#e74c3c', edgecolor='black')
    
    ax4.set_ylabel('Cost (£/MWh)', fontsize=12, fontweight='bold')
    ax4.set_title('Import Cost Components by DUoS Band', fontsize=13, fontweight='bold')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(bands, fontsize=11, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(axis='y', alpha=0.3)
    
    # Add total cost line
    total_costs = [costs_per_band['green'], costs_per_band['amber'], costs_per_band['red']]
    ax4.plot(x_pos, total_costs, 'ko-', linewidth=2, markersize=8, label='Total Cost')
    
    # Add value labels for totals
    for i, cost in enumerate(total_costs):
        ax4.text(i, cost + 5, f'£{cost:.2f}', ha='center', va='bottom',
                fontsize=9, fontweight='bold')
    
    # Add PPA price reference line
    ax4.axhline(y=150, color='green', linestyle='--', linewidth=2, label='PPA Price (£150)')
    
    ax4.legend(fontsize=9, loc='upper left')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def build_btm_ppa_summary_text(btm_results: Dict[str, Any], curtailment: Dict[str, float]) -> str:
    """
    Generate text summary of BtM PPA results for logging/reporting.
    
    Returns:
        Formatted text summary
    """
    s1 = btm_results["stream1"]
    s2 = btm_results["stream2"]
    
    summary = f"""
    ═══════════════════════════════════════════════════════════
    BtM PPA REVENUE SUMMARY
    ═══════════════════════════════════════════════════════════
    
    STREAM 1 (Direct Import):
      - Volume: {s1['total_mwh']:,.0f} MWh
      - Revenue: £{s1['total_revenue']:,.0f}
      - Cost: £{s1['total_cost']:,.0f}
      - Profit: £{s1['profit']:,.0f}
    
    STREAM 2 (Battery + VLP):
      - Charged: {s2['charged_mwh']:,.0f} MWh ({s2['cycles']:.1f} cycles)
      - Discharged: {s2['discharged_mwh']:,.0f} MWh
      - PPA Revenue: £{s2['ppa_revenue']:,.0f}
      - VLP Revenue: £{s2['vlp_revenue']:,.0f}
      - Charging Cost: £{s2['charging_cost']:,.0f}
      - Profit: £{s2['profit']:,.0f}
    
    CURTAILMENT (BM):
      - Curtailment MWh: {curtailment['curtailment_mwh']:,.0f}
      - Curtailment Revenue: £{curtailment['curtailment_revenue']:,.0f}
      - Total BM Revenue: £{curtailment['total_bm_revenue']:,.0f}
    
    TOTAL ANNUAL PROFIT:
      - BtM PPA: £{btm_results['btm_ppa_profit']:,.0f}
      - Dynamic Containment: £195,458
      - TOTAL: £{btm_results['total_profit']:,.0f}
    
    BATTERY PERFORMANCE:
      - RED Coverage: {btm_results['red_coverage']:.1f}%
      - Annual Cycles: {s2['cycles']:.1f}
      - Efficiency: 85%
    
    ═══════════════════════════════════════════════════════════
    """
    
    return summary
