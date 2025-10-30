#!/usr/bin/env python3
"""
Comprehensive Elexon/NESO dataset manifest
Based on official API documentation
"""

import json

# Complete list of all Elexon BMRS API endpoints
COMPLETE_DATASET_LIST = {
    # Generation Data
    "FUELINST": {
        "route": "/datasets/FUELINST/stream",
        "name": "Generation by Fuel Type (Instant)",
        "category": "generation",
        "bq_table": "uk_energy_prod.generation_fuel_instant"
    },
    "FUELHH": {
        "route": "/datasets/FUELHH/stream",
        "name": "Generation by Fuel Type (Half Hourly)",
        "category": "generation",
        "bq_table": "uk_energy_prod.generation_fuel_hh"
    },
    "GENERATION_ACTUAL_PER_TYPE": {
        "route": "/generation/actual/per-type",
        "name": "Actual Aggregated Generation per Type",
        "category": "generation",
        "bq_table": "uk_energy_prod.generation_actual_per_type"
    },
    "GENERATION_ACTUAL_DAY_TOTAL": {
        "route": "/generation/actual/per-type/day-total",
        "name": "Actual Generation Day Total",
        "category": "generation",
        "bq_table": "uk_energy_prod.generation_actual_day_total"
    },
    "GENERATION_WIND_SOLAR": {
        "route": "/generation/actual/per-type/wind-and-solar",
        "name": "Actual Wind and Solar Generation",
        "category": "generation",
        "bq_table": "uk_energy_prod.generation_wind_solar"
    },
    "GENERATION_OUTTURN": {
        "route": "/generation/outturn/summary",
        "name": "Generation Outturn Summary",
        "category": "generation",
        "bq_table": "uk_energy_prod.generation_outturn"
    },
    "INDGEN": {
        "route": "/datasets/INDGEN/stream",
        "name": "Indicated Generation by BM Unit",
        "category": "generation",
        "bq_table": "uk_energy_prod.indicated_generation"
    },
    
    # Demand Data
    "DEMAND_OUTTURN": {
        "route": "/demand/outturn",
        "name": "Demand Outturn (INDO/ITSDO)",
        "category": "demand",
        "bq_table": "uk_energy_prod.demand_outturn"
    },
    "DEMAND_OUTTURN_SUMMARY": {
        "route": "/demand/outturn/summary",
        "name": "Rolling System Demand",
        "category": "demand",
        "bq_table": "uk_energy_prod.demand_outturn_summary"
    },
    "DEMAND_OUTTURN_DAILY": {
        "route": "/demand/outturn/daily",
        "name": "Daily Energy Transmitted (INDOD)",
        "category": "demand",
        "bq_table": "uk_energy_prod.demand_outturn_daily"
    },
    "DEMAND_ACTUAL_TOTAL": {
        "route": "/demand/actual/total",
        "name": "Total Load Actual",
        "category": "demand",
        "bq_table": "uk_energy_prod.demand_actual_total"
    },
    
    # Demand Forecasts
    "NDF": {
        "route": "/datasets/NDF/stream",
        "name": "National Demand Forecast",
        "category": "forecast",
        "bq_table": "uk_energy_prod.demand_forecast_national"
    },
    "NDFD": {
        "route": "/datasets/NDFD/stream",
        "name": "National Demand Forecast Day Ahead",
        "category": "forecast",
        "bq_table": "uk_energy_prod.demand_forecast_day_ahead"
    },
    "NDFW": {
        "route": "/datasets/NDFW/stream",
        "name": "National Demand Forecast Week Ahead",
        "category": "forecast",
        "bq_table": "uk_energy_prod.demand_forecast_week_ahead"
    },
    "TSDF": {
        "route": "/datasets/TSDF/stream",
        "name": "Transmission System Demand Forecast",
        "category": "forecast",
        "bq_table": "uk_energy_prod.demand_forecast_transmission"
    },
    "TSDFD": {
        "route": "/datasets/TSDFD/stream",
        "name": "Transmission System Demand Forecast Day Ahead",
        "category": "forecast",
        "bq_table": "uk_energy_prod.demand_forecast_transmission_da"
    },
    "DEMAND_TOTAL_DAY_AHEAD": {
        "route": "/forecast/demand/total/day-ahead",
        "name": "Total Load Day Ahead Forecast",
        "category": "forecast",
        "bq_table": "uk_energy_prod.demand_total_forecast_da"
    },
    "DEMAND_PEAK_INDICATIVE": {
        "route": "/demand/peak/indicative/settlement",
        "name": "Indicative Peak Demand",
        "category": "demand",
        "bq_table": "uk_energy_prod.demand_peak_indicative"
    },
    "DEMAND_PEAK_TRIAD": {
        "route": "/demand/peak/triad",
        "name": "Triad Demand Peaks",
        "category": "demand",
        "bq_table": "uk_energy_prod.demand_peak_triad"
    },
    
    # Generation Forecasts
    "WINDFOR": {
        "route": "/datasets/WINDFOR/stream",
        "name": "Wind Generation Forecast",
        "category": "forecast",
        "bq_table": "uk_energy_prod.generation_forecast_wind"
    },
    "GENERATION_WIND_PEAK": {
        "route": "/forecast/generation/wind/peak",
        "name": "Wind & Solar Generation Forecast Peak",
        "category": "forecast",
        "bq_table": "uk_energy_prod.generation_forecast_wind_solar_peak"
    },
    "GENERATION_DAY_AHEAD": {
        "route": "/forecast/generation/day-ahead",
        "name": "Day-ahead Aggregated Generation",
        "category": "forecast",
        "bq_table": "uk_energy_prod.generation_forecast_day_ahead"
    },
    
    # Margin and Surplus
    "UOU2T14D": {
        "route": "/datasets/UOU2T14D/stream",
        "name": "Output Usable 2-14 Days Ahead",
        "category": "forecast",
        "bq_table": "uk_energy_prod.output_usable_2_14d"
    },
    "MARGIN_DAILY": {
        "route": "/forecast/margin/daily",
        "name": "Generating Plant Operating Margin Daily",
        "category": "forecast",
        "bq_table": "uk_energy_prod.margin_daily"
    },
    "SURPLUS_DAILY": {
        "route": "/forecast/surplus/daily",
        "name": "National Surplus Forecast Daily",
        "category": "forecast",
        "bq_table": "uk_energy_prod.surplus_daily"
    },
    
    # System Data
    "FREQ": {
        "route": "/datasets/FREQ/stream",
        "name": "System Frequency",
        "category": "system",
        "bq_table": "uk_energy_prod.system_frequency"
    },
    "SYSWARN": {
        "route": "/datasets/SYSWARN/stream",
        "name": "System Warnings",
        "category": "system",
        "bq_table": "uk_energy_prod.system_warnings"
    },
    
    # Balancing Mechanism
    "BOD": {
        "route": "/datasets/BOD/stream",
        "name": "Bid Offer Data",
        "category": "balancing",
        "bq_table": "uk_energy_prod.bid_offer_data"
    },
    "BALANCING_PHYSICAL": {
        "route": "/balancing/physical",
        "name": "Physical Notifications",
        "category": "balancing",
        "bq_table": "uk_energy_prod.balancing_physical"
    },
    "BALANCING_DYNAMIC": {
        "route": "/balancing/dynamic",
        "name": "Dynamic Data",
        "category": "balancing",
        "bq_table": "uk_energy_prod.balancing_dynamic"
    },
    "BALANCING_DYNAMIC_RATES": {
        "route": "/balancing/dynamic/rates",
        "name": "Dynamic Rates",
        "category": "balancing",
        "bq_table": "uk_energy_prod.balancing_dynamic_rates"
    },
    "BALANCING_BID_OFFER": {
        "route": "/balancing/bid-offer",
        "name": "Bid-Offer Pairs",
        "category": "balancing",
        "bq_table": "uk_energy_prod.balancing_bid_offer"
    },
    "BALANCING_ACCEPTANCES": {
        "route": "/balancing/acceptances",
        "name": "Balancing Mechanism Acceptances",
        "category": "balancing",
        "bq_table": "uk_energy_prod.balancing_acceptances"
    },
    "BALANCING_NONBM_VOLUMES": {
        "route": "/balancing/nonbm/volumes",
        "name": "Non-BM Balancing Services Volumes",
        "category": "balancing",
        "bq_table": "uk_energy_prod.balancing_nonbm_volumes"
    },
    
    # Settlement and Prices
    "NETBSAD": {
        "route": "/datasets/NETBSAD/stream",
        "name": "Net Balancing Services Adjustment Data",
        "category": "settlement",
        "bq_table": "uk_energy_prod.netbsad"
    },
    "DISBSAD": {
        "route": "/datasets/DISBSAD/stream",
        "name": "Disaggregated Balancing Services Adjustment",
        "category": "settlement",
        "bq_table": "uk_energy_prod.disbsad"
    },
    "MID": {
        "route": "/datasets/MID/stream",
        "name": "Market Index Data (Prices)",
        "category": "settlement",
        "bq_table": "uk_energy_prod.market_index_data"
    },
    "IMBALNGC": {
        "route": "/datasets/IMBALNGC/stream",
        "name": "Indicated Imbalance",
        "category": "settlement",
        "bq_table": "uk_energy_prod.indicated_imbalance"
    },
    "SYSTEM_PRICES": {
        "route": "/balancing/settlement/system-prices",
        "name": "System Buy and Sell Prices",
        "category": "settlement",
        "bq_table": "uk_energy_prod.system_prices"
    },
    
    # Other Services
    "NONBM": {
        "route": "/datasets/NONBM/stream",
        "name": "Short-term Operating Reserves (STOR)",
        "category": "services",
        "bq_table": "uk_energy_prod.stor_nonbm"
    },
    "QAS": {
        "route": "/datasets/QAS/stream",
        "name": "Quiescent Physical Notifications",
        "category": "balancing",
        "bq_table": "uk_energy_prod.quiescent_physical"
    },
    "SEL": {
        "route": "/datasets/SEL/stream",
        "name": "Stable Export Limit",
        "category": "system",
        "bq_table": "uk_energy_prod.stable_export_limit"
    },
}

def create_manifest():
    """Create comprehensive manifest file"""
    manifest = {
        "base_url": "https://data.elexon.co.uk/bmrs/api/v1",
        "auth": {
            "header": "apiKey",
            "value_env": "BMRS_API_KEY_1"
        },
        "datasets": COMPLETE_DATASET_LIST,
        "metadata": {
            "total_datasets": len(COMPLETE_DATASET_LIST),
            "categories": list(set(ds["category"] for ds in COMPLETE_DATASET_LIST.values())),
            "generated": "2025-10-25",
            "source": "Official Elexon BMRS API Documentation"
        }
    }
    
    return manifest

def main():
    manifest = create_manifest()
    
    print("=" * 80)
    print("📋 Comprehensive Elexon Dataset Manifest")
    print("=" * 80)
    print(f"Total datasets: {manifest['metadata']['total_datasets']}")
    print(f"Categories: {', '.join(manifest['metadata']['categories'])}")
    print()
    
    # Show datasets by category
    categories = {}
    for code, info in COMPLETE_DATASET_LIST.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((code, info["name"]))
    
    for category, datasets in sorted(categories.items()):
        print(f"\n📊 {category.upper()} ({len(datasets)} datasets):")
        for code, name in sorted(datasets):
            print(f"   • {code}: {name}")
    
    # Save manifest
    output_file = "insights_manifest_comprehensive.json"
    with open(output_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print()
    print("=" * 80)
    print(f"✅ Manifest saved to: {output_file}")
    print(f"📊 Total datasets: {len(COMPLETE_DATASET_LIST)}")
    print()
    print("To download all datasets:")
    print(f"  python download_last_7_days.py --manifest {output_file} --days 7")
    print()
    print("To download specific category:")
    print(f"  python download_last_7_days.py --manifest {output_file} --datasets FREQ FUELINST DEMAND_OUTTURN")
    print("=" * 80)

if __name__ == "__main__":
    main()
