#!/usr/bin/env python3
"""
Complete BMRS Dataset Analysis
=============================

Analyze all 53 BMRS datasets with detailed descriptions of what each contains.
"""

import json

import pandas as pd
from google.cloud import bigquery

# BMRS Dataset Descriptions
DATASET_DESCRIPTIONS = {
    "BOALF": {
        "name": "Bid Offer Acceptance Level Flagged",
        "description": "Acceptance/rejection status of bids and offers submitted to the balancing mechanism",
        "frequency": "Real-time",
        "key_fields": [
            "bmUnit",
            "settlementDate",
            "acceptanceFlag",
            "levelFrom",
            "levelTo",
        ],
    },
    "BOD": {
        "name": "Bid Offer Data",
        "description": "All bids and offers submitted to the balancing mechanism for energy trading",
        "frequency": "Real-time",
        "key_fields": [
            "bmUnit",
            "bidOfferPairNumber",
            "offerPrice",
            "bidPrice",
            "volume",
        ],
    },
    "DISBSAD": {
        "name": "Disbursement Schedule of Balancing Services Adjustment Data",
        "description": "System operator disbursements for balancing services and grid management",
        "frequency": "Daily",
        "key_fields": ["settlementDate", "disbursementAmount", "serviceType"],
    },
    "FREQ": {
        "name": "System Frequency",
        "description": "Real-time GB electricity system frequency measurements",
        "frequency": "2-second intervals",
        "key_fields": ["publishTime", "frequency"],
    },
    "FUELHH": {
        "name": "Half Hourly Fuel Mix",
        "description": "Generation by fuel type aggregated to half-hourly periods",
        "frequency": "30 minutes",
        "key_fields": ["settlementDate", "fuelType", "generation"],
    },
    "FUELINST": {
        "name": "Instantaneous Fuel Mix",
        "description": "Real-time generation breakdown by fuel type (coal, gas, nuclear, renewables)",
        "frequency": "5 minutes",
        "key_fields": ["publishTime", "fuelType", "generation"],
    },
    "IMBALNGC": {
        "name": "Imbalance Prices at National Grid Company",
        "description": "System buy and sell prices for energy imbalances",
        "frequency": "Settlement periods",
        "key_fields": ["settlementDate", "imbalancePriceBuy", "imbalancePriceSell"],
    },
    "INDDEM": {
        "name": "Initial National Demand Forecast",
        "description": "Initial demand forecasts for the GB electricity system",
        "frequency": "Daily",
        "key_fields": ["settlementDate", "demand"],
    },
    "INDGEN": {
        "name": "Initial National Generation Forecast",
        "description": "Initial generation forecasts for the GB electricity system",
        "frequency": "Daily",
        "key_fields": ["settlementDate", "generation"],
    },
    "INDO": {
        "name": "Initial National Demand Outturn",
        "description": "Actual initial demand outturn data",
        "frequency": "Settlement periods",
        "key_fields": ["settlementDate", "demandOutturn"],
    },
    "ITSDO": {
        "name": "Initial Transmission System Demand Outturn",
        "description": "Initial transmission system demand actuals",
        "frequency": "Settlement periods",
        "key_fields": ["settlementDate", "transmissionDemand"],
    },
    "MELNGC": {
        "name": "Miscellaneous Energy Loss National Grid Company",
        "description": "Energy losses within the transmission system",
        "frequency": "Settlement periods",
        "key_fields": ["settlementDate", "energyLoss"],
    },
    "MELS": {
        "name": "Marginal Energy Loss Stations",
        "description": "Marginal energy loss factors for individual power stations",
        "frequency": "Half-hourly",
        "key_fields": ["bmUnit", "settlementDate", "marginalLossFactor"],
    },
    "MID": {
        "name": "Market Index Data",
        "description": "Price indices and market reference data",
        "frequency": "Daily",
        "key_fields": ["settlementDate", "priceIndex", "marketType"],
    },
    "MILS": {
        "name": "Marginal Imbalance Loss Stations",
        "description": "Marginal loss factors for balancing mechanism units",
        "frequency": "Half-hourly",
        "key_fields": ["bmUnit", "settlementDate", "marginalLossFactor"],
    },
    "NETBSAD": {
        "name": "Net Balancing Services Adjustment Data",
        "description": "Net adjustments for balancing services costs",
        "frequency": "Settlement periods",
        "key_fields": ["settlementDate", "adjustmentAmount"],
    },
    "NDF": {
        "name": "National Demand Forecast",
        "description": "Updated national demand forecasts",
        "frequency": "Multiple daily updates",
        "key_fields": ["settlementDate", "demand", "forecastType"],
    },
    "NDFD": {
        "name": "National Demand Forecast Daily",
        "description": "Daily national demand forecasts",
        "frequency": "Daily",
        "key_fields": ["date", "peakDemand", "totalDemand"],
    },
    "NDFW": {
        "name": "National Demand Forecast Weekly",
        "description": "Weekly national demand forecasts",
        "frequency": "Weekly",
        "key_fields": ["week", "peakDemand", "totalDemand"],
    },
    "NONBM": {
        "name": "Non-Balancing Mechanism BMRA",
        "description": "Data for generators not participating in the balancing mechanism",
        "frequency": "Half-hourly",
        "key_fields": ["bmUnit", "settlementDate", "generation"],
    },
    "QAS": {
        "name": "Balancing Services Adjustment Data",
        "description": "Balancing services costs and adjustments by service type",
        "frequency": "Settlement periods",
        "key_fields": ["settlementDate", "serviceType", "adjustmentCost"],
    },
    "RDRE": {
        "name": "Run Down Rate Export",
        "description": "Maximum rate at which units can decrease export",
        "frequency": "As submitted",
        "key_fields": ["bmUnit", "runDownRate"],
    },
    "RDRI": {
        "name": "Run Down Rate Import",
        "description": "Maximum rate at which units can decrease import",
        "frequency": "As submitted",
        "key_fields": ["bmUnit", "runDownRate"],
    },
    "RURE": {
        "name": "Run Up Rate Export",
        "description": "Maximum rate at which units can increase export",
        "frequency": "As submitted",
        "key_fields": ["bmUnit", "runUpRate"],
    },
    "RURI": {
        "name": "Run Up Rate Import",
        "description": "Maximum rate at which units can increase import",
        "frequency": "As submitted",
        "key_fields": ["bmUnit", "runUpRate"],
    },
    "TEMP": {
        "name": "Temperature Data",
        "description": "Temperature measurements from weather stations",
        "frequency": "Regular intervals",
        "key_fields": ["location", "temperature", "measurementTime"],
    },
    "TSDF": {
        "name": "Transmission System Demand Forecast",
        "description": "Forecasts of transmission system demand",
        "frequency": "Regular updates",
        "key_fields": ["settlementDate", "transmissionDemand"],
    },
    "TSDFD": {
        "name": "Transmission System Demand Forecast Daily",
        "description": "Daily transmission system demand forecasts",
        "frequency": "Daily",
        "key_fields": ["date", "peakDemand"],
    },
    "TSDFW": {
        "name": "Transmission System Demand Forecast Weekly",
        "description": "Weekly transmission system demand forecasts",
        "frequency": "Weekly",
        "key_fields": ["week", "peakDemand"],
    },
    "WINDFOR": {
        "name": "Wind Generation Forecast",
        "description": "Forecasts of wind generation output",
        "frequency": "Regular updates",
        "key_fields": ["settlementDate", "windGeneration"],
    },
    "MDV": {
        "name": "Meter Data Version",
        "description": "Metering data versions and updates",
        "frequency": "As required",
        "key_fields": ["bmUnit", "meterDataVersion"],
    },
    # Additional datasets that might be present
    "UOU2T3YW": {
        "name": "Unit Output Unit Data (3 Year Window)",
        "description": "Historical unit output data over 3-year rolling window",
        "frequency": "Settlement periods",
        "key_fields": ["bmUnit", "settlementDate", "output"],
    },
    "UOU2T14D": {
        "name": "Unit Output Unit Data (14 Day Window)",
        "description": "Unit output data over 14-day rolling window",
        "frequency": "Settlement periods",
        "key_fields": ["bmUnit", "settlementDate", "output"],
    },
    "FOU2T3YW": {
        "name": "Forecast Output Unit Data (3 Year Window)",
        "description": "Historical forecast output data over 3-year rolling window",
        "frequency": "Settlement periods",
        "key_fields": ["bmUnit", "settlementDate", "forecastOutput"],
    },
    "FOU2T14D": {
        "name": "Forecast Output Unit Data (14 Day Window)",
        "description": "Forecast output data over 14-day rolling window",
        "frequency": "Settlement periods",
        "key_fields": ["bmUnit", "settlementDate", "forecastOutput"],
    },
    "NOU2T3YW": {
        "name": "Notice Output Unit Data (3 Year Window)",
        "description": "Historical notice data over 3-year rolling window",
        "frequency": "As submitted",
        "key_fields": ["bmUnit", "noticeTime", "outputLevel"],
    },
    "NOU2T14D": {
        "name": "Notice Output Unit Data (14 Day Window)",
        "description": "Notice data over 14-day rolling window",
        "frequency": "As submitted",
        "key_fields": ["bmUnit", "noticeTime", "outputLevel"],
    },
    "OCNMF3Y": {
        "name": "Operational Constraints Notice Market Forecast (3 Year)",
        "description": "Operational constraints forecasts over 3-year window",
        "frequency": "As required",
        "key_fields": ["constraintType", "forecastPeriod", "constraintLevel"],
    },
    "OCNMF3Y2": {
        "name": "Operational Constraints Notice Market Forecast (3 Year Secondary)",
        "description": "Secondary operational constraints forecasts over 3-year window",
        "frequency": "As required",
        "key_fields": ["constraintType", "forecastPeriod", "constraintLevel"],
    },
    "OCNMFD": {
        "name": "Operational Constraints Notice Market Forecast Daily",
        "description": "Daily operational constraints forecasts",
        "frequency": "Daily",
        "key_fields": ["constraintType", "date", "constraintLevel"],
    },
    "OCNMFD2": {
        "name": "Operational Constraints Notice Market Forecast Daily Secondary",
        "description": "Secondary daily operational constraints forecasts",
        "frequency": "Daily",
        "key_fields": ["constraintType", "date", "constraintLevel"],
    },
    "SEL": {
        "name": "System Energy Loss",
        "description": "System-wide energy losses",
        "frequency": "Settlement periods",
        "key_fields": ["settlementDate", "energyLoss"],
    },
    "SIL": {
        "name": "System Imbalance Loss",
        "description": "System imbalance and associated losses",
        "frequency": "Settlement periods",
        "key_fields": ["settlementDate", "imbalanceLoss"],
    },
    "MDP": {
        "name": "Market Domain Pricing",
        "description": "Market domain pricing data",
        "frequency": "Settlement periods",
        "key_fields": ["settlementDate", "domainPrice"],
    },
    "MZT": {
        "name": "Market Zone Transmission",
        "description": "Market zone transmission data",
        "frequency": "Settlement periods",
        "key_fields": ["zone", "transmissionData"],
    },
    "MNZT": {
        "name": "Market National Zone Transmission",
        "description": "National market zone transmission data",
        "frequency": "Settlement periods",
        "key_fields": ["nationalZone", "transmissionData"],
    },
    "NDZ": {
        "name": "National Demand Zone",
        "description": "Demand data by national zones",
        "frequency": "Settlement periods",
        "key_fields": ["zone", "demand"],
    },
    "NTB": {
        "name": "National Transmission Boundary",
        "description": "Transmission boundary flows and constraints",
        "frequency": "Settlement periods",
        "key_fields": ["boundary", "flow", "constraint"],
    },
    "NTO": {
        "name": "National Transmission Outturn",
        "description": "Actual transmission system outturns",
        "frequency": "Settlement periods",
        "key_fields": ["transmissionOutturn", "settlementDate"],
    },
}


def get_table_schema(client, table_name):
    """Gets the schema for a given table."""
    schema_query = f"""
    SELECT
        column_name,
        data_type
    FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{table_name}'
    ORDER BY ordinal_position
    """
    try:
        schema_df = client.query(schema_query).to_dataframe()
        return schema_df.to_string(index=False)
    except Exception:
        return "Could not retrieve schema."


def main():
    """Generate complete dataset analysis."""

    client = bigquery.Client(project="jibber-jabber-knowledge")

    # Get all BMRS tables with stats
    query = """
    SELECT
        table_id as table_name,
        row_count,
        ROUND(size_bytes / 1024 / 1024, 1) as size_mb
    FROM `uk_energy_insights.__TABLES__`
    WHERE table_id LIKE 'bmrs_%'
        AND table_id NOT LIKE '%_backup'
        AND table_id NOT LIKE '%_v2'
        AND table_id NOT LIKE '%_temp_%'
        AND row_count > 0
    ORDER BY row_count DESC
    """

    df = client.query(query).to_dataframe()

    print("🏆 COMPLETE BMRS DATASET INVENTORY")
    print("=" * 80)
    print(f"📊 Total Tables: {len(df)}")
    print(f"📈 Total Rows: {df['row_count'].sum():,}")
    print(f"💾 Total Size: {df['size_mb'].sum() / 1024:.1f} GB")
    print()

    # Categorize datasets
    categories = {
        "💰 Market & Trading Data": [
            "BOD",
            "BOALF",
            "IMBALNGC",
            "QAS",
            "DISBSAD",
            "NETBSAD",
            "MID",
        ],
        "⚡ Real-time System Data": ["FREQ", "FUELINST", "FUELHH"],
        "📊 Demand & Generation": [
            "INDDEM",
            "INDGEN",
            "INDO",
            "ITSDO",
            "TSDF",
            "TSDFD",
            "TSDFW",
        ],
        "🌪️ Forecasting Data": ["NDF", "NDFD", "NDFW", "WINDFOR"],
        "🏭 Unit Performance": [
            "UOU2T3YW",
            "UOU2T14D",
            "FOU2T3YW",
            "FOU2T14D",
            "NOU2T3YW",
            "NOU2T14D",
        ],
        "🔧 Technical Parameters": [
            "MELS",
            "MILS",
            "MELNGC",
            "RDRE",
            "RDRI",
            "RURE",
            "RURI",
        ],
        "🚫 Constraints & Losses": [
            "OCNMF3Y",
            "OCNMF3Y2",
            "OCNMFD",
            "OCNMFD2",
            "SEL",
            "SIL",
        ],
        "📡 Non-BM & Special": ["NONBM", "TEMP", "MDV"],
        "🌍 Transmission Zones": ["MZT", "MNZT", "NDZ", "NTB", "NTO", "MDP"],
    }

    for category, datasets in categories.items():
        print(f"\n{category}")
        print("-" * 60)

        for dataset_code in datasets:
            # Find matching table
            table_name = f"bmrs_{dataset_code.lower()}"
            table_data = df[df["table_name"] == table_name]

            if not table_data.empty:
                row = table_data.iloc[0]
                desc = DATASET_DESCRIPTIONS.get(dataset_code, {})
                schema = get_table_schema(client, table_name)

                print(
                    f"✅ {dataset_code:<12} | {row['row_count']:>12,} rows | {row['size_mb']:>8.1f} MB"
                )
                print(f"   � bq://jibber-jabber-knowledge/uk_energy_insights/{table_name}")
                print(f"   �📝 {desc.get('name', 'Unknown Dataset')}")
                print(f"   📄 {desc.get('description', 'No description available')}")
                print(f"   🔄 {desc.get('frequency', 'Unknown frequency')}")
                print(f"   📜 Schema:\n{schema}")
                print()

    # Show any unmatched tables
    all_expected = set()
    for datasets in categories.values():
        all_expected.update([f"bmrs_{d.lower()}" for d in datasets])

    actual_tables = set(df["table_name"].tolist())
    unmatched = actual_tables - all_expected

    if unmatched:
        print(f"\n🔍 ADDITIONAL DATASETS")
        print("-" * 30)
        for table in sorted(unmatched):
            table_data = df[df["table_name"] == table].iloc[0]
            schema = get_table_schema(client, table)
            print(
                f"✅ {table:<20} | {table_data['row_count']:>12,} rows | {table_data['size_mb']:>8.1f} MB"
            )
            print(f"   📍 bq://jibber-jabber-knowledge/uk_energy_insights/{table}")
            print(f"   📜 Schema:\n{schema}")


    print(f"\n🎯 ANALYSIS READY DATASETS")
    print("=" * 40)
    print("Your complete UK energy market data platform includes:")
    print("• Real-time electricity system monitoring")
    print("• Complete balancing mechanism trading data")
    print("• Generation and demand forecasting")
    print("• System constraints and losses")
    print("• Unit-level performance data")
    print("• Market pricing and adjustments")
    print("\n🚀 Ready for comprehensive energy market analysis!")



if __name__ == "__main__":
    main()
