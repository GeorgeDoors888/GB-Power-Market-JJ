#!/usr/bin/env python3
"""
UK Energy Data Source Query Helper
Provides easy access to data by source type
"""

import json

import pandas as pd
from google.cloud import bigquery


class UKEnergyDataQuery:
    def __init__(
        self, project_id="jibber-jabber-knowledge", dataset_id="uk_energy_insights"
    ):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)

        # Load source mappings
        try:
            with open("data_source_analysis.json", "r") as f:
                self.source_analysis = json.load(f)
        except FileNotFoundError:
            print("⚠️ Source analysis not found. Run data_source_analyzer.py first.")
            self.source_analysis = None

    def list_tables_by_source(self, source_type):
        """List all tables for a specific data source"""
        if not self.source_analysis:
            return []

        source_mapping = {
            "elexon": "ELEXON/BMRS",
            "bmrs": "ELEXON/BMRS",
            "neso": "NESO Portal",
            "ukpn": "UKPN Distribution",
            "dno": "DNO General",
        }

        source_key = source_mapping.get(source_type.lower())
        if source_key and source_key in self.source_analysis["detailed_breakdown"]:
            return self.source_analysis["detailed_breakdown"][source_key]["tables"]
        else:
            print(f"❌ Unknown source type: {source_type}")
            print(f"Available sources: {list(source_mapping.keys())}")
            return []

    def query_elexon_market_data(self, limit=1000):
        """Query ELEXON market trading data"""
        query = f"""
        SELECT
            'BOD' as data_type,
            settlement_date,
            settlement_period,
            bm_unit_id,
            bid_offer_level_from,
            bid_offer_price
        FROM `{self.project_id}.{self.dataset_id}.bmrs_bod`
        WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        ORDER BY settlement_date DESC, settlement_period DESC
        LIMIT {limit}
        """
        return self.client.query(query).to_dataframe()

    def query_neso_balancing_costs(self, limit=1000):
        """Query NESO BSUoS balancing costs"""
        # Find BSUoS tables
        bsuos_tables = [
            t
            for t in self.list_tables_by_source("neso")
            if "bsuos" in t.lower() and "forecast" in t.lower()
        ]

        if not bsuos_tables:
            print("❌ No BSUoS forecast tables found")
            return pd.DataFrame()

        # Use the first available BSUoS table
        table_name = bsuos_tables[0]
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.dataset_id}.{table_name}`
        ORDER BY month DESC
        LIMIT {limit}
        """
        return self.client.query(query).to_dataframe()

    def query_ukpn_distribution_data(self, data_type="duos_charges", limit=1000):
        """Query UKPN distribution network data"""
        table_mapping = {
            "duos_charges": "ukpn_duos_charges_annex1",
            "network_losses": "ukpn_network_losses",
            "transformers": "ukpn_secondary_transformers",
            "low_carbon": "ukpn_low_carbon_technologies",
        }

        table_name = table_mapping.get(data_type)
        if not table_name:
            print(f"❌ Unknown UKPN data type: {data_type}")
            print(f"Available types: {list(table_mapping.keys())}")
            return pd.DataFrame()

        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.dataset_id}.{table_name}`
        LIMIT {limit}
        """
        return self.client.query(query).to_dataframe()

    def query_carbon_intensity(self, limit=1000):
        """Query NESO carbon intensity data"""
        query = f"""
        SELECT
            intensity_index,
            intensity_actual,
            intensity_forecast,
            timestamp
        FROM `{self.project_id}.{self.dataset_id}.neso_carbon_intensity__current_intensity`
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        return self.client.query(query).to_dataframe()

    def cross_source_analysis(self):
        """Example cross-source analysis combining multiple data sources"""
        print("🔄 Cross-Source Analysis Example")
        print("=" * 40)

        # Get market prices from ELEXON
        print("📊 ELEXON Market Data (Sample):")
        market_data = self.query_elexon_market_data(limit=5)
        if not market_data.empty:
            print(market_data.head())
        else:
            print("No market data available")
        print()

        # Get balancing costs from NESO
        print("💰 NESO Balancing Costs (Sample):")
        balancing_data = self.query_neso_balancing_costs(limit=5)
        if not balancing_data.empty:
            print(balancing_data.head())
        else:
            print("No balancing cost data available")
        print()

        # Get distribution charges from UKPN
        print("🔌 UKPN Distribution Charges (Sample):")
        ukpn_data = self.query_ukpn_distribution_data(limit=5)
        if not ukpn_data.empty:
            print(ukpn_data.head())
        else:
            print("No UKPN data available")
        print()

        # Get carbon intensity from NESO
        print("🌱 Carbon Intensity Data (Sample):")
        carbon_data = self.query_carbon_intensity(limit=5)
        if not carbon_data.empty:
            print(carbon_data.head())
        else:
            print("No carbon intensity data available")

    def source_summary(self):
        """Print summary of all data sources"""
        if not self.source_analysis:
            print("❌ No source analysis available")
            return

        print("🔍 UK ENERGY DATA SOURCES SUMMARY")
        print("=" * 40)

        for source, details in self.source_analysis["detailed_breakdown"].items():
            print(f"🏢 {source}: {details['count']} tables")

            # Show top 3 tables as examples
            example_tables = details["tables"][:3]
            for table in example_tables:
                print(f"   • {table}")
            if len(details["tables"]) > 3:
                print(f"   ... and {len(details['tables']) - 3} more")
            print()


def main():
    """Demonstration of data source queries"""
    print("🚀 UK Energy Data Source Query Helper")
    print("=" * 50)

    querier = UKEnergyDataQuery()

    # Show source summary
    querier.source_summary()

    # Demonstrate cross-source analysis
    print("\n" + "=" * 50)
    querier.cross_source_analysis()

    print("\n💡 Usage Examples:")
    print("python data_query_helper.py")
    print("# Or import in your own scripts:")
    print("from data_query_helper import UKEnergyDataQuery")
    print("querier = UKEnergyDataQuery()")
    print("elexon_data = querier.query_elexon_market_data()")
    print("neso_data = querier.query_neso_balancing_costs()")
    print("ukpn_data = querier.query_ukpn_distribution_data()")


if __name__ == "__main__":
    main()
