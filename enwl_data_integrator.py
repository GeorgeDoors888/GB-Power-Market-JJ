#!/usr/bin/env python3
"""
ENWL Data Integration Script
Consolidates all ENWL (Electricity North West) data from various sources
and prepares for BigQuery integration
"""

import json
import logging
import os
from datetime import datetime

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ENWLDataIntegrator:
    """Integrates all ENWL data sources for comprehensive analysis"""

    def __init__(self):
        self.enwl_mpan_id = "14"
        self.enwl_region = "North West England"
        self.enwl_region_id = 3
        self.integrated_data = {}

    def load_carbon_intensity_data(self):
        """Load ENWL carbon intensity data"""
        logger.info("📊 Loading ENWL carbon intensity data...")

        carbon_file = "neso_data_comprehensive/carbon_intensity/regional_intensity.csv"
        if os.path.exists(carbon_file):
            try:
                df = pd.read_csv(carbon_file)
                enwl_data = df[df["dnoregion"] == "Electricity North West"].copy()

                # Add MPAN ID for consistency
                enwl_data["mpan_id"] = self.enwl_mpan_id
                enwl_data["data_source"] = "carbon_intensity"

                # Convert datetime columns
                enwl_data["from"] = pd.to_datetime(enwl_data["from"])
                enwl_data["to"] = pd.to_datetime(enwl_data["to"])

                self.integrated_data["carbon_intensity"] = enwl_data
                logger.info(f"✅ Loaded {len(enwl_data)} carbon intensity records")

                return enwl_data

            except Exception as e:
                logger.error(f"❌ Error loading carbon intensity: {e}")
                return None
        else:
            logger.warning(f"❌ Carbon intensity file not found: {carbon_file}")
            return None

    def load_capacity_market_data(self):
        """Load ENWL capacity market registrations"""
        logger.info("🏭 Loading ENWL capacity market data...")

        cmu_file = "neso_data_comprehensive/neso_portal/capacity-market-register_Capacity_Market_Unit_CMU.csv"
        components_file = "neso_data_comprehensive/neso_portal/capacity-market-register_Components.csv"

        capacity_data = {}

        # Load CMU data
        if os.path.exists(cmu_file):
            try:
                # Read in chunks due to large file size
                enwl_rows = []
                for chunk in pd.read_csv(cmu_file, chunksize=10000, low_memory=False):
                    chunk_str = chunk.astype(str)
                    enwl_mask = chunk_str.apply(
                        lambda x: x.str.contains(
                            "enwl|electricity north west|penwortham",
                            case=False,
                            na=False,
                        )
                    ).any(axis=1)
                    enwl_chunk = chunk[enwl_mask]
                    if len(enwl_chunk) > 0:
                        enwl_rows.append(enwl_chunk)

                if enwl_rows:
                    enwl_cmu = pd.concat(enwl_rows, ignore_index=True)
                    enwl_cmu["mpan_id"] = self.enwl_mpan_id
                    enwl_cmu["data_source"] = "capacity_market_cmu"

                    capacity_data["cmu_registrations"] = enwl_cmu
                    logger.info(f"✅ Loaded {len(enwl_cmu)} CMU registrations")

            except Exception as e:
                logger.error(f"❌ Error loading CMU data: {e}")

        # Load Components data
        if os.path.exists(components_file):
            try:
                # Read in chunks
                enwl_components = []
                for chunk in pd.read_csv(
                    components_file, chunksize=5000, low_memory=False
                ):
                    chunk_str = chunk.astype(str)
                    enwl_mask = chunk_str.apply(
                        lambda x: x.str.contains(
                            "penwortham|enwl|north west", case=False, na=False
                        )
                    ).any(axis=1)
                    enwl_chunk = chunk[enwl_mask]
                    if len(enwl_chunk) > 0:
                        enwl_components.append(enwl_chunk)

                if enwl_components:
                    enwl_comp = pd.concat(enwl_components, ignore_index=True)
                    enwl_comp["mpan_id"] = self.enwl_mpan_id
                    enwl_comp["data_source"] = "capacity_market_components"

                    capacity_data["components"] = enwl_comp
                    logger.info(f"✅ Loaded {len(enwl_comp)} component records")

            except Exception as e:
                logger.error(f"❌ Error loading components data: {e}")

        self.integrated_data["capacity_market"] = capacity_data
        return capacity_data

    def create_enwl_summary_dataset(self):
        """Create comprehensive ENWL summary dataset"""
        logger.info("📋 Creating ENWL summary dataset...")

        summary_data = {
            "enwl_profile": {
                "dno_name": "Electricity North West",
                "mpan_id": self.enwl_mpan_id,
                "region": self.enwl_region,
                "region_id": self.enwl_region_id,
                "website": "https://www.enwl.co.uk",
                "data_collection_date": datetime.now().isoformat(),
            },
            "data_availability": {},
            "key_metrics": {},
            "generation_assets": [],
            "carbon_profile": {},
        }

        # Summarize data availability
        for data_type, data in self.integrated_data.items():
            if data_type == "carbon_intensity" and data is not None:
                summary_data["data_availability"]["carbon_intensity"] = {
                    "records": len(data),
                    "date_range": f"{data['from'].min()} to {data['to'].max()}",
                    "avg_intensity": (
                        data["intensity_forecast"].mean()
                        if "intensity_forecast" in data.columns
                        else None
                    ),
                }

                # Carbon profile metrics
                if "intensity_forecast" in data.columns:
                    summary_data["carbon_profile"] = {
                        "avg_carbon_intensity": data["intensity_forecast"].mean(),
                        "renewable_percentage": (
                            (
                                data["gen_wind"].mean()
                                + data["gen_solar"].mean()
                                + data["gen_hydro"].mean()
                            )
                            if all(
                                col in data.columns
                                for col in ["gen_wind", "gen_solar", "gen_hydro"]
                            )
                            else None
                        ),
                    }

            elif data_type == "capacity_market" and data:
                total_registrations = 0
                total_capacity = 0

                if "cmu_registrations" in data:
                    cmu_data = data["cmu_registrations"]
                    total_registrations += len(cmu_data)

                    # Extract capacity information if available
                    capacity_cols = [
                        col
                        for col in cmu_data.columns
                        if "capacity" in col.lower() or "mw" in col.lower()
                    ]
                    if capacity_cols:
                        for col in capacity_cols:
                            try:
                                capacity_values = pd.to_numeric(
                                    cmu_data[col], errors="coerce"
                                )
                                total_capacity += capacity_values.sum()
                            except:
                                pass

                summary_data["data_availability"]["capacity_market"] = {
                    "total_registrations": total_registrations,
                    "estimated_capacity_mw": total_capacity,
                    "asset_types": list(
                        set(
                            data.get("cmu_registrations", {}).get("Technology Type", [])
                            if "cmu_registrations" in data
                            else []
                        )
                    ),
                }

        # Generate key insights
        insights = []

        if summary_data["carbon_profile"].get("avg_carbon_intensity"):
            intensity = summary_data["carbon_profile"]["avg_carbon_intensity"]
            if intensity < 50:
                insights.append(f"Low carbon intensity region ({intensity:.1f})")
            elif intensity < 100:
                insights.append(f"Medium carbon intensity region ({intensity:.1f})")
            else:
                insights.append(f"High carbon intensity region ({intensity:.1f})")

        if summary_data["carbon_profile"].get("renewable_percentage"):
            renewable = summary_data["carbon_profile"]["renewable_percentage"]
            insights.append(f"Renewable generation: {renewable:.1f}%")

        capacity_regs = (
            summary_data["data_availability"]
            .get("capacity_market", {})
            .get("total_registrations", 0)
        )
        if capacity_regs > 0:
            insights.append(f"{capacity_regs} capacity market registrations found")

        summary_data["key_insights"] = insights

        self.integrated_data["summary"] = summary_data
        return summary_data

    def export_for_bigquery(self):
        """Export ENWL data in BigQuery-ready format"""
        logger.info("📤 Exporting data for BigQuery...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exports = {}

        # Export carbon intensity data
        if (
            "carbon_intensity" in self.integrated_data
            and self.integrated_data["carbon_intensity"] is not None
        ):
            carbon_data = self.integrated_data["carbon_intensity"].copy()

            # Prepare for BigQuery
            carbon_data["collection_timestamp"] = datetime.now()
            carbon_data["dno_code"] = "ENWL"

            # Convert datetime columns to strings for JSON serialization
            carbon_data["from"] = carbon_data["from"].dt.strftime("%Y-%m-%d %H:%M:%S")
            carbon_data["to"] = carbon_data["to"].dt.strftime("%Y-%m-%d %H:%M:%S")

            carbon_export_file = f"enwl_carbon_intensity_bq_{timestamp}.csv"
            carbon_data.to_csv(carbon_export_file, index=False)
            exports["carbon_intensity"] = carbon_export_file

            logger.info(f"✅ Carbon intensity data exported: {carbon_export_file}")

        # Export capacity market data
        if "capacity_market" in self.integrated_data:
            capacity_data = self.integrated_data["capacity_market"]

            if "cmu_registrations" in capacity_data:
                cmu_data = capacity_data["cmu_registrations"].copy()
                cmu_data["collection_timestamp"] = datetime.now()
                cmu_data["dno_code"] = "ENWL"

                cmu_export_file = f"enwl_capacity_market_bq_{timestamp}.csv"
                cmu_data.to_csv(cmu_export_file, index=False)
                exports["capacity_market"] = cmu_export_file

                logger.info(f"✅ Capacity market data exported: {cmu_export_file}")

        # Export summary data
        if "summary" in self.integrated_data:
            summary_file = f"enwl_summary_analysis_{timestamp}.json"
            with open(summary_file, "w") as f:
                json.dump(self.integrated_data["summary"], f, indent=2, default=str)
            exports["summary"] = summary_file

            logger.info(f"✅ Summary analysis exported: {summary_file}")

        return exports

    def generate_integration_report(self):
        """Generate comprehensive integration report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            "integration_summary": {
                "timestamp": timestamp,
                "enwl_mpan_id": self.enwl_mpan_id,
                "total_data_sources": len(self.integrated_data),
                "total_records": sum(
                    (
                        len(data)
                        if isinstance(data, pd.DataFrame)
                        else (
                            sum(
                                len(d)
                                for d in data.values()
                                if isinstance(d, pd.DataFrame)
                            )
                            if isinstance(data, dict)
                            else 0
                        )
                    )
                    for data in self.integrated_data.values()
                ),
            },
            "data_sources_processed": list(self.integrated_data.keys()),
            "enwl_profile": self.integrated_data.get("summary", {}).get(
                "enwl_profile", {}
            ),
            "key_insights": self.integrated_data.get("summary", {}).get(
                "key_insights", []
            ),
            "bigquery_readiness": (
                "ready"
                if any(
                    isinstance(data, pd.DataFrame)
                    for data in self.integrated_data.values()
                )
                else "partial"
            ),
        }

        report_file = f"enwl_integration_report_{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return report, report_file


def main():
    """Main execution"""
    print("⚡ ENWL DATA INTEGRATION")
    print("=" * 50)

    integrator = ENWLDataIntegrator()

    # Load all data sources
    carbon_data = integrator.load_carbon_intensity_data()
    capacity_data = integrator.load_capacity_market_data()

    # Create summary dataset
    summary = integrator.create_enwl_summary_dataset()

    # Export for BigQuery
    exports = integrator.export_for_bigquery()

    # Generate report
    report, report_file = integrator.generate_integration_report()

    # Print summary
    print(f"\n📊 ENWL INTEGRATION SUMMARY")
    print("-" * 40)
    print(f"MPAN ID: {integrator.enwl_mpan_id} ({integrator.enwl_region})")
    print(f"Data sources processed: {len(integrator.integrated_data)}")
    print(f"Total records: {report['integration_summary']['total_records']}")

    print(f"\n📁 EXPORTED FILES")
    print("-" * 40)
    for data_type, filename in exports.items():
        print(f"✅ {data_type}: {filename}")

    print(f"\n🎯 KEY INSIGHTS")
    print("-" * 40)
    for insight in summary.get("key_insights", []):
        print(f"• {insight}")

    print(f"\n💾 Integration report: {report_file}")
    print(f"\n🚀 NEXT: Upload CSV files to BigQuery for comprehensive ENWL analysis")


if __name__ == "__main__":
    main()
