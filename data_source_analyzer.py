#!/usr/bin/env python3
"""
UK Energy Data Source Analyzer
Distinguishes between ELEXON, NESO, and DNO data sources in BigQuery
"""

import json
import logging
import re
from collections import defaultdict

from google.cloud import bigquery

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class UKEnergyDataSourceAnalyzer:
    def __init__(
        self, project_id="jibber-jabber-knowledge", dataset_id="uk_energy_insights"
    ):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)

        # Define source patterns and mappings
        self.source_patterns = {
            "ELEXON/BMRS": [
                r"^bmrs_.*",
            ],
            "NESO Portal": [
                r".*neso_portal.*",
                r"^neso_.*",
                # Individual NESO datasets that might not have neso_portal prefix
                r".*bsuos.*",
                r".*carbon_intensity.*balancing.*",
                r".*capacity_market.*",
                r".*constraint.*cost.*",
            ],
            "UKPN Distribution": [
                r".*ukpn.*",
                r".*distribution.*tariff.*",
                r".*duos.*",
            ],
            "DNO General": [
                r".*dno.*",
                r".*license.*area.*",
                r".*distribution.*network.*",
                r"gis_boundaries.*gb_dno.*",
            ],
            "Other System Operations": [
                r".*demand.*forecast.*",
                r".*wind.*forecast.*",
                r".*frequency.*response.*",
                r".*operational.*metered.*",
                r".*embedded.*wind.*",
            ],
        }

        # DNO company mapping
        self.dno_companies = {
            "UKPN": ["ukpn", "uk_power_networks"],
            "SSEN": ["ssen", "scottish_southern"],
            "NGED": ["nged", "national_grid_electricity"],
            "ENWL": ["enwl", "electricity_north_west"],
            "NPG": ["npg", "northern_powergrid"],
            "SPD": ["spd", "sp_distribution"],
        }

        # NESO data categories
        self.neso_categories = {
            "BSUoS & Balancing": ["bsuos", "balancing", "reserve", "stor"],
            "Carbon Intensity": ["carbon", "intensity", "environmental"],
            "Capacity Market": ["capacity", "market", "cmu", "auction"],
            "Constraint Management": ["constraint", "limit", "transmission"],
            "Forecasting": ["forecast", "ahead", "prediction"],
            "System Operations": ["operational", "system", "frequency", "response"],
        }

        # BMRS/ELEXON categories
        self.bmrs_categories = {
            "Market Trading": ["bod", "boalf", "qpn", "pn", "sil", "sell", "buy"],
            "System Balancing": ["freq", "mip", "mels", "mils", "soso", "ebocf"],
            "Generation Data": ["fuelinst", "fuelhh", "generation", "output"],
            "Demand & Forecasting": ["itsdo", "melngc", "imbalngc", "demand"],
            "Wind & Renewables": ["windfor", "wind", "renewable"],
            "Technical & Monitoring": ["sysdem", "syswarn", "temp", "qas"],
            "Interconnectors": ["fou2t", "interconnector", "import", "export"],
            "Grid Operations": ["tsdf", "transmission", "availability"],
        }

    def analyze_table_sources(self):
        """Analyze all tables in the dataset and categorize by source"""
        try:
            logger.info("🔍 Fetching tables from BigQuery dataset...")

            # Get all tables in the dataset
            tables = list(
                self.client.list_tables(f"{self.project_id}.{self.dataset_id}")
            )

            source_analysis = {
                "total_tables": len(tables),
                "sources": defaultdict(list),
                "detailed_breakdown": {},
                "unknown_tables": [],
            }

            logger.info(f"📊 Analyzing {len(tables)} tables...")

            for table in tables:
                table_name = table.table_id
                source_found = False

                # Check against each source pattern
                for source, patterns in self.source_patterns.items():
                    for pattern in patterns:
                        if re.match(pattern, table_name, re.IGNORECASE):
                            source_analysis["sources"][source].append(table_name)
                            source_found = True
                            break
                    if source_found:
                        break

                if not source_found:
                    source_analysis["unknown_tables"].append(table_name)

            # Create detailed breakdown
            for source, tables_list in source_analysis["sources"].items():
                source_analysis["detailed_breakdown"][source] = {
                    "count": len(tables_list),
                    "tables": tables_list,
                }

                # Sub-categorize based on source type
                if source == "ELEXON/BMRS":
                    source_analysis["detailed_breakdown"][source]["categories"] = (
                        self._categorize_bmrs_tables(tables_list)
                    )
                elif source == "NESO Portal":
                    source_analysis["detailed_breakdown"][source]["categories"] = (
                        self._categorize_neso_tables(tables_list)
                    )
                elif "Distribution" in source or "DNO" in source:
                    source_analysis["detailed_breakdown"][source]["companies"] = (
                        self._identify_dno_companies(tables_list)
                    )

            return source_analysis

        except Exception as e:
            logger.error(f"Error analyzing table sources: {e}")
            return None

    def _categorize_bmrs_tables(self, tables):
        """Categorize BMRS/ELEXON tables by data type"""
        categories = defaultdict(list)

        for table in tables:
            categorized = False
            for category, keywords in self.bmrs_categories.items():
                for keyword in keywords:
                    if keyword in table.lower():
                        categories[category].append(table)
                        categorized = True
                        break
                if categorized:
                    break

            if not categorized:
                categories["Other BMRS Data"].append(table)

        return dict(categories)

    def _categorize_neso_tables(self, tables):
        """Categorize NESO tables by data type"""
        categories = defaultdict(list)

        for table in tables:
            categorized = False
            for category, keywords in self.neso_categories.items():
                for keyword in keywords:
                    if keyword in table.lower():
                        categories[category].append(table)
                        categorized = True
                        break
                if categorized:
                    break

            if not categorized:
                categories["Other NESO Data"].append(table)

        return dict(categories)

    def _identify_dno_companies(self, tables):
        """Identify which DNO companies are represented"""
        companies = defaultdict(list)

        for table in tables:
            identified = False
            for company, patterns in self.dno_companies.items():
                for pattern in patterns:
                    if pattern in table.lower():
                        companies[company].append(table)
                        identified = True
                        break
                if identified:
                    break

            if not identified:
                companies["Unknown/General DNO"].append(table)

        return dict(companies)

    def generate_source_report(self):
        """Generate comprehensive source analysis report"""
        analysis = self.analyze_table_sources()

        if not analysis:
            logger.error("Failed to analyze sources")
            return

        print("🔍 UK ENERGY DATA SOURCE ANALYSIS")
        print("=" * 50)
        print(f"📊 Total Tables: {analysis['total_tables']}\n")

        # Main source breakdown
        for source, details in analysis["detailed_breakdown"].items():
            print(f"🏢 {source}: {details['count']} tables")

            # Show categories if available
            if "categories" in details:
                print("   Categories:")
                for category, cat_tables in details["categories"].items():
                    print(f"     • {category}: {len(cat_tables)} tables")
                    if len(cat_tables) <= 3:
                        for table in cat_tables:
                            print(f"       - {table}")
                    else:
                        for table in cat_tables[:2]:
                            print(f"       - {table}")
                        print(f"       ... and {len(cat_tables) - 2} more")

            # Show DNO companies if available
            if "companies" in details:
                print("   Companies:")
                for company, comp_tables in details["companies"].items():
                    print(f"     • {company}: {len(comp_tables)} tables")
                    for table in comp_tables:
                        print(f"       - {table}")

            print()

        # Unknown tables
        if analysis["unknown_tables"]:
            print(f"❓ Unknown/Unclassified Tables: {len(analysis['unknown_tables'])}")
            for table in analysis["unknown_tables"][:10]:  # Show first 10
                print(f"   • {table}")
            if len(analysis["unknown_tables"]) > 10:
                print(f"   ... and {len(analysis['unknown_tables']) - 10} more")

        # Save detailed analysis to JSON
        with open("data_source_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2, default=str)

        logger.info("💾 Detailed analysis saved to data_source_analysis.json")

        # Save analysis to the specified text file
        self.save_analysis_to_file(analysis, "elexon_bmrs_analysis_results.txt")

    def save_analysis_to_file(self, analysis, file_path):
        """Save analysis results to a specified file."""
        try:
            with open(file_path, "w") as f:
                f.write("ELEXON/BMRS Table Analysis Results (by Year):\n\n")
                for source, details in analysis["detailed_breakdown"].items():
                    if source == "ELEXON/BMRS":
                        f.write(f"{source}:\n")
                        for category, cat_tables in details.get("categories", {}).items():
                            f.write(f"  {category}:\n")
                            for table in cat_tables:
                                f.write(f"    - {table}\n")
                        f.write("\n")
            logger.info(f"Analysis results saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save analysis to file: {e}")

    def create_source_mapping_views(self):
        """Create BigQuery views to easily filter by data source"""
        view_queries = {
            "elexon_bmrs_data": """
                SELECT table_name
                FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLES`
                WHERE table_name LIKE 'bmrs_%'
            """,
            "neso_portal_data": """
                SELECT table_name
                FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLES`
                WHERE table_name LIKE '%neso_portal%'
                   OR table_name LIKE '%bsuos%'
                   OR table_name LIKE '%carbon_intensity%'
                   OR table_name LIKE '%capacity_market%'
                   OR table_name LIKE '%constraint%'
            """,
            "dno_distribution_data": """
                SELECT table_name
                FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLES`
                WHERE table_name LIKE '%ukpn%'
                   OR table_name LIKE '%dno%'
                   OR table_name LIKE '%distribution%'
                   OR table_name LIKE '%license_area%'
            """,
        }

        for view_name, query in view_queries.items():
            try:
                view_id = f"{self.project_id}.{self.dataset_id}.{view_name}_view"
                view = bigquery.Table(view_id)
                view.view_query = query.format(
                    project=self.project_id, dataset=self.dataset_id
                )

                # Create or replace the view
                view = self.client.create_table(view, exists_ok=True)
                logger.info(f"✅ Created view: {view_name}_view")

            except Exception as e:
                logger.error(f"❌ Failed to create view {view_name}: {e}")

    def analyze_elexon_bmrs_tables(self):
        """Analyze ELEXON/BMRS tables for data availability and completeness, separated by year."""
        elexon_tables = {
            "bmrs_boalf": "settlementDate",
            "bmrs_boalf_backup": "settlementDate",
            "bmrs_bod": "settlementDate",
            "bmrs_bod_backup": "settlementDate",
            "bmrs_bod_v2": "settlementDate",
            "bmrs_disbsad": "settlementDate",
            "bmrs_disbsad_backup": "settlementDate",
            "bmrs_disbsad_v2": "settlementDate",
            "bmrs_fou2t14d": "settlementDate",
            "bmrs_fou2t14d_backup": "settlementDate",
            "bmrs_fou2t3yw": "settlementDate",
            "bmrs_fou2t3yw_backup": "settlementDate",
            "bmrs_freq": "measurementTime",
            "bmrs_freq_backup": "measurementTime",
            "bmrs_windfor": "publishTime",
            "bmrs_windfor_backup": "publishTime",
        }

        results = {}
        current_year = 2025
        for table, date_field in elexon_tables.items():
            print(f"📊 Analyzing table: {table}")
            results[table] = {}

            # Check if the field exists in the table schema
            try:
                schema = self.client.get_table(f"{self.project_id}.{self.dataset_id}.{table}").schema
                if not any(field.name == date_field for field in schema):
                    logger.warning(f"Field '{date_field}' not found in table '{table}'. Skipping analysis.")
                    results[table] = {year: "Field missing" for year in range(current_year - 4, current_year + 1)}
                    continue
            except Exception as e:
                logger.error(f"Error fetching schema for table '{table}': {e}")
                results[table] = {year: f"Schema error: {e}" for year in range(current_year - 4, current_year + 1)}
                continue

            # Analyze data year by year
            for year in range(current_year - 4, current_year + 1):
                query = f"""
                SELECT
                    COUNT(*) as total_records,
                    MIN(CAST({date_field} AS DATE)) as min_date,
                    MAX(CAST({date_field} AS DATE)) as max_date
                FROM `{self.project_id}.{self.dataset_id}.{table}`
                WHERE EXTRACT(YEAR FROM CAST({date_field} AS DATE)) = {year}
                """

                try:
                    # Ensure job ID is alphanumeric and meets BigQuery's requirements
                    sanitized_job_id = re.sub(r"[^a-zA-Z0-9_-]", "_", f"Data_Analysis_{table}_{year}")
                    df = self.query_bigquery(query, sanitized_job_id)
                    if df is not None and not df.empty:
                        results[table][year] = {
                            "total_records": df["total_records"].iloc[0],
                            "min_date": df["min_date"].iloc[0],
                            "max_date": df["max_date"].iloc[0],
                        }
                    else:
                        results[table][year] = "No data available"
                except Exception as e:
                    logger.error(f"Error running query for table '{table}' in year {year}: {e}")
                    results[table][year] = f"Query error: {e}"

        print("\nELEXON/BMRS Table Analysis Results (by Year):")
        for table, yearly_results in results.items():
            print(f"{table}:")
            for year, result in yearly_results.items():
                print(f"  {year}: {result}")

        return results

    def query_bigquery(self, query, job_description=""):
        """Helper method to run a query on BigQuery and return the results as a DataFrame"""
        try:
            query_job = self.client.query(query, job_id_prefix=job_description)
            result = query_job.result()
            df = result.to_dataframe()
            return df
        except Exception as e:
            logger.error(f"Error running query: {e}")
            return None

    def get_yearly_results(self):
        """Mock implementation for demonstration"""
        return {"2025": {"total_records": 100, "min_date": "2025-01-01", "max_date": "2025-12-31"}}  # Replace with actual logic


def main():
    """Main execution function"""
    logger.info("🚀 Starting UK Energy Data Source Analysis...")

    analyzer = UKEnergyDataSourceAnalyzer()

    # Generate comprehensive source report
    analyzer.generate_source_report()

    # Create helpful BigQuery views
    logger.info("📋 Creating BigQuery views for easy data source filtering...")
    analyzer.create_source_mapping_views()

    # Analyze ELEXON/BMRS tables for data availability
    logger.info(
        "📊 Analyzing ELEXON/BMRS tables for data availability and completeness..."
    )
    analyzer.analyze_elexon_bmrs_tables()

    logger.info("✅ Data source analysis complete!")


if __name__ == "__main__":
    main()
