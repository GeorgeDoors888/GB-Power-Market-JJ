#!/usr/bin/env python3
"""
UKPN to BigQuery Uploader
=========================

Upload all collected UKPN CSV files to BigQuery tables.
"""

import logging
import os
from datetime import datetime

import pandas as pd
from google.cloud import bigquery

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class UKPNToBigQueryUploader:
    """Upload UKPN CSV data to BigQuery."""

    def __init__(self):
        self.client = bigquery.Client(project="jibber-jabber-knowledge")
        self.dataset_id = "uk_energy_insights"

    def upload_csv_to_bigquery(
        self, csv_path: str, table_suffix: str, description: str
    ) -> bool:
        """Upload a single CSV file to BigQuery."""

        table_name = f"ukpn_{table_suffix}"
        table_id = f"{self.client.project}.{self.dataset_id}.{table_name}"

        logger.info(f"📊 Uploading: {csv_path}")
        logger.info(f"📋 Target table: {table_name}")

        try:
            # Read CSV
            df = pd.read_csv(csv_path, sep=";")  # UKPN uses semicolon separator
            logger.info(f"📝 Records: {len(df):,}")
            logger.info(f"📊 Columns: {len(df.columns)}")

            # Add metadata
            df["ukpn_source_file"] = os.path.basename(csv_path)
            df["ingested_at"] = datetime.now()

            # Configure job
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Replace existing data
                autodetect=True,  # Auto-detect schema
                skip_leading_rows=0,  # We already read with pandas
            )

            # Create table reference
            table_ref = self.client.dataset(self.dataset_id).table(table_name)

            # Upload DataFrame
            job = self.client.load_table_from_dataframe(
                df, table_ref, job_config=job_config
            )
            job.result()  # Wait for completion

            # Update table description
            table = self.client.get_table(table_ref)
            table.description = description
            self.client.update_table(table, ["description"])

            logger.info(f"✅ SUCCESS: {table_name} ({len(df):,} rows)")
            return True

        except Exception as e:
            logger.error(f"❌ FAILED: {table_name} - {e}")
            return False

    def upload_all_ukpn_data(self):
        """Upload all UKPN CSV files."""

        logger.info("🚀 UKPN to BigQuery Upload Starting")
        logger.info("=" * 50)

        # Define all UKPN files and their BigQuery table mappings
        ukpn_files = [
            {
                "pattern": "ltds-table-1-circuit-data_*.csv",
                "table_suffix": "ltds_circuit_data",
                "description": "UKPN Long Term Development Statement - Circuit Data: Network connectivity, impedances, ratings",
            },
            {
                "pattern": "ltds-table-4a-3ph-fault-level_*.csv",
                "table_suffix": "ltds_fault_levels",
                "description": "UKPN LTDS Three-Phase Fault Levels: System impedance and fault current data",
            },
            {
                "pattern": "ltds-table-7-operational-restrictions_*.csv",
                "table_suffix": "ltds_operational_restrictions",
                "description": "UKPN LTDS Operational Restrictions: Network constraint and limitation data",
            },
            {
                "pattern": "ukpn-33kv-circuit-operational-data-monthly_*.csv",
                "table_suffix": "33kv_circuit_data",
                "description": "UKPN 33kV Circuit Operational Data: Monthly circuit performance and utilization",
            },
            {
                "pattern": "ukpn-primary-transformer-power-flow-historic-monthly_*.csv",
                "table_suffix": "primary_transformer_flows",
                "description": "UKPN Primary Transformer Power Flows: Historical monthly transformer loading data",
            },
            {
                "pattern": "ukpn-secondary-site-transformers_*.csv",
                "table_suffix": "secondary_transformers",
                "description": "UKPN Secondary Site Transformers: Distribution transformer asset and rating data",
            },
            {
                "pattern": "ukpn-network-losses_*.csv",
                "table_suffix": "network_losses",
                "description": "UKPN Network Losses: Distribution system loss calculations and efficiency metrics",
            },
            {
                "pattern": "ukpn-low-carbon-technologies-lsoa_*.csv",
                "table_suffix": "low_carbon_technologies",
                "description": "UKPN Low Carbon Technologies by LSOA: EV charging points, heat pumps, solar PV deployment",
            },
            {
                "pattern": "ukpn-distribution-use-of-system-charges-annex-1_*.csv",
                "table_suffix": "duos_charges_annex1",
                "description": "UKPN DUoS Charges Annex 1: LV/HV/UMS distribution tariffs and pricing",
            },
            {
                "pattern": "ukpn-distribution-use-of-system-charges-annex-2_*.csv",
                "table_suffix": "duos_charges_annex2",
                "description": "UKPN DUoS Charges Annex 2: EHV properties and LDNO distribution charges",
            },
        ]

        # Find and upload files
        import glob

        successful_uploads = 0
        failed_uploads = 0

        for file_def in ukpn_files:
            # Find matching files
            matching_files = glob.glob(file_def["pattern"])

            if matching_files:
                # Use the most recent file
                csv_file = max(matching_files, key=os.path.getmtime)

                if self.upload_csv_to_bigquery(
                    csv_file, file_def["table_suffix"], file_def["description"]
                ):
                    successful_uploads += 1
                else:
                    failed_uploads += 1
            else:
                logger.warning(f"⚠️  No files found for pattern: {file_def['pattern']}")
                failed_uploads += 1

        # Summary
        logger.info("\n🎉 UPLOAD COMPLETE")
        logger.info("=" * 30)
        logger.info(f"✅ Successful: {successful_uploads}")
        logger.info(f"❌ Failed: {failed_uploads}")
        logger.info(
            f"📊 Success rate: {(successful_uploads/(successful_uploads+failed_uploads)*100):.1f}%"
        )

        if successful_uploads > 0:
            logger.info("\n🚀 NEXT STEPS:")
            logger.info("1. ✅ UKPN data now available in BigQuery")
            logger.info("2. 🔄 Query tables with: uk_energy_insights.ukpn_*")
            logger.info("3. 📊 Combine with BMRS data for complete analysis")
            logger.info(
                "4. 💡 Run energy cost analysis across transmission + distribution"
            )


if __name__ == "__main__":
    uploader = UKPNToBigQueryUploader()

    # First, try to upload from the data collection directory
    data_dir = "ukpn_data_collection_20250911_134928"
    if os.path.exists(data_dir):
        print(f"📁 Uploading from: {data_dir}")
        os.chdir(data_dir)
        uploader.upload_all_ukpn_data()
        os.chdir("..")  # Return to parent directory

    # Also check for DUoS files in main directory
    print("\n📊 Checking for DUoS files in main directory...")
    duos_files = [
        {
            "pattern": "ukpn-distribution-use-of-system-charges-annex-1_*.csv",
            "table_suffix": "duos_charges_annex1",
            "description": "UKPN DUoS Charges Annex 1: LV/HV/UMS distribution tariffs and pricing",
        },
        {
            "pattern": "ukpn-distribution-use-of-system-charges-annex-2_*.csv",
            "table_suffix": "duos_charges_annex2",
            "description": "UKPN DUoS Charges Annex 2: EHV properties and LDNO distribution charges",
        },
    ]

    import glob

    for file_def in duos_files:
        matching_files = glob.glob(file_def["pattern"])
        if matching_files:
            csv_file = max(matching_files, key=os.path.getmtime)
            print(f"📋 Found: {csv_file}")
            uploader.upload_csv_to_bigquery(
                csv_file, file_def["table_suffix"], file_def["description"]
            )
