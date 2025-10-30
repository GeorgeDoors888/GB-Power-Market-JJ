#!/usr/bin/env python3
"""
Comprehensive DNO Data Integration Framework
===========================================

Since the DNO APIs are currently restricted, this creates a framework
for DNO data integration that can be populated when you have access.

Features:
- Database schema for DNO data
- Integration with your existing BMRS pipeline
- Documentation of available data sources
- Ready-to-use BigQuery tables
- Analysis templates for DNO + BMRS data

Usage:
    python dno_framework.py
"""

import logging
import os
import sqlite3
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

# Setup
OUT_DIR = Path("./dno_framework").resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DNOFramework:
    """Framework for DNO data integration with BMRS data."""

    def __init__(self):
        self.project_id = "jibber-jabber-knowledge"
        self.dataset_id = "uk_energy_insights"
        self.bq_client = self._setup_bigquery()

    def _setup_bigquery(self):
        """Setup BigQuery client."""
        try:
            return bigquery.Client(project=self.project_id)
        except Exception as e:
            logger.warning(f"BigQuery setup failed: {e}")
            return None

    def create_dno_schema(self):
        """Create standardized schemas for DNO data types."""

        schemas = {
            "dno_capacity_data": [
                ("dno_id", "STRING"),
                ("gsp_name", "STRING"),
                ("voltage_level", "STRING"),
                ("capacity_mva", "FLOAT"),
                ("available_capacity_mva", "FLOAT"),
                ("demand_mw", "FLOAT"),
                ("generation_mw", "FLOAT"),
                ("recorded_date", "DATE"),
                ("data_source", "STRING"),
            ],
            "dno_outage_data": [
                ("dno_id", "STRING"),
                ("incident_id", "STRING"),
                ("start_time", "TIMESTAMP"),
                ("end_time", "TIMESTAMP"),
                ("customers_affected", "INTEGER"),
                ("cause", "STRING"),
                ("area_affected", "STRING"),
                ("voltage_level", "STRING"),
                ("data_source", "STRING"),
            ],
            "dno_flexibility_data": [
                ("dno_id", "STRING"),
                ("service_type", "STRING"),
                ("location", "STRING"),
                ("capacity_mw", "FLOAT"),
                ("duration_hours", "FLOAT"),
                ("price_per_mwh", "FLOAT"),
                ("procurement_date", "DATE"),
                ("delivery_start", "TIMESTAMP"),
                ("delivery_end", "TIMESTAMP"),
                ("data_source", "STRING"),
            ],
            "dno_asset_data": [
                ("dno_id", "STRING"),
                ("asset_type", "STRING"),
                ("asset_id", "STRING"),
                ("location", "STRING"),
                ("voltage_level", "STRING"),
                ("capacity_rating", "FLOAT"),
                ("installation_date", "DATE"),
                ("condition_score", "FLOAT"),
                ("data_source", "STRING"),
            ],
        }

        # Create sample data for demonstration
        sample_data = self._create_sample_data()

        # Store schemas and sample data
        for table_name, schema in schemas.items():
            self._create_table_if_not_exists(table_name, schema)

            # Load sample data if available
            if table_name in sample_data:
                self._load_sample_data(table_name, sample_data[table_name])

        logger.info("✅ Created DNO data schemas in BigQuery")

    def _create_sample_data(self):
        """Create sample DNO data for demonstration."""

        return {
            "dno_capacity_data": pd.DataFrame(
                [
                    {
                        "dno_id": "UKPN-EPN",
                        "gsp_name": "BRAMFORD_T",
                        "voltage_level": "132kV",
                        "capacity_mva": 180.0,
                        "available_capacity_mva": 45.2,
                        "demand_mw": 89.5,
                        "generation_mw": 12.3,
                        "recorded_date": "2025-09-01",
                        "data_source": "LTDS_SAMPLE",
                    },
                    {
                        "dno_id": "NGED-WM",
                        "gsp_name": "BIRMINGHAM_T",
                        "voltage_level": "132kV",
                        "capacity_mva": 240.0,
                        "available_capacity_mva": 67.8,
                        "demand_mw": 156.7,
                        "generation_mw": 8.9,
                        "recorded_date": "2025-09-01",
                        "data_source": "NGED_SAMPLE",
                    },
                ]
            ),
            "dno_flexibility_data": pd.DataFrame(
                [
                    {
                        "dno_id": "UKPN-SPN",
                        "service_type": "Secure",
                        "location": "Surrey",
                        "capacity_mw": 5.0,
                        "duration_hours": 4.0,
                        "price_per_mwh": 120.0,
                        "procurement_date": "2025-08-15",
                        "delivery_start": "2025-11-01 17:00:00",
                        "delivery_end": "2025-11-01 21:00:00",
                        "data_source": "UKPN_FLEXIBILITY_SAMPLE",
                    }
                ]
            ),
        }

    def _create_table_if_not_exists(self, table_name: str, schema: list):
        """Create BigQuery table if it doesn't exist."""

        if not self.bq_client:
            return

        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"

        try:
            # Check if table exists
            self.bq_client.get_table(table_id)
            logger.info(f"Table {table_name} already exists")
        except:
            # Create table
            bq_schema = []
            for field_name, field_type in schema:
                bq_schema.append(bigquery.SchemaField(field_name, field_type))

            table = bigquery.Table(table_id, schema=bq_schema)
            table = self.bq_client.create_table(table)
            logger.info(f"✅ Created table {table_name}")

    def _load_sample_data(self, table_name: str, df: pd.DataFrame):
        """Load sample data into BigQuery table."""

        if not self.bq_client or df.empty:
            return

        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"

        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE", autodetect=False
        )

        try:
            job = self.bq_client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()
            logger.info(f"✅ Loaded {len(df)} sample rows to {table_name}")
        except Exception as e:
            logger.warning(f"Failed to load sample data to {table_name}: {e}")

    def create_analysis_queries(self):
        """Create SQL queries for DNO + BMRS analysis."""

        queries = {
            "dno_bmrs_correlation": """
-- Correlate DNO capacity constraints with BMRS balancing actions
SELECT
    d.dno_id,
    d.gsp_name,
    d.available_capacity_mva,
    DATE(b.settlement_date) as settlement_date,
    AVG(CAST(b.imbalance_volume AS FLOAT64)) as avg_imbalance_volume,
    COUNT(*) as balancing_actions
FROM `{project}.{dataset}.dno_capacity_data` d
JOIN `{project}.{dataset}.bmrs_bod` b
    ON DATE(b.settlement_date) = d.recorded_date
WHERE d.available_capacity_mva < 50  -- Low capacity
    AND b.settlement_date >= '2025-08-01'
GROUP BY d.dno_id, d.gsp_name, d.available_capacity_mva, DATE(b.settlement_date)
ORDER BY balancing_actions DESC
""",
            "flexibility_vs_frequency": """
-- Compare DNO flexibility procurement with system frequency issues
SELECT
    f.dno_id,
    f.service_type,
    f.capacity_mw,
    DATE(freq.settlement_date) as date,
    AVG(CAST(freq.frequency AS FLOAT64)) as avg_frequency,
    MIN(CAST(freq.frequency AS FLOAT64)) as min_frequency
FROM `{project}.{dataset}.dno_flexibility_data` f
JOIN `{project}.{dataset}.bmrs_freq` freq
    ON DATE(freq.settlement_date) = f.procurement_date
GROUP BY f.dno_id, f.service_type, f.capacity_mw, DATE(freq.settlement_date)
HAVING min_frequency < 49.8  -- Low frequency events
ORDER BY min_frequency ASC
""",
            "outage_impact_analysis": """
-- Analyze impact of DNO outages on national balancing
SELECT
    o.dno_id,
    o.customers_affected,
    o.start_time,
    o.end_time,
    DATETIME_DIFF(o.end_time, o.start_time, MINUTE) as duration_minutes,
    COUNT(b.settlement_period) as balancing_periods,
    AVG(CAST(b.so_flag AS FLOAT64)) as system_operator_actions
FROM `{project}.{dataset}.dno_outage_data` o
JOIN `{project}.{dataset}.bmrs_bod` b
    ON b.settlement_date BETWEEN DATE(o.start_time) AND DATE(o.end_time)
WHERE o.customers_affected > 1000  -- Major outages
GROUP BY o.dno_id, o.customers_affected, o.start_time, o.end_time
ORDER BY balancing_periods DESC
""",
        }

        # Save queries to files
        query_dir = OUT_DIR / "analysis_queries"
        query_dir.mkdir(exist_ok=True)

        for query_name, sql in queries.items():
            formatted_sql = sql.format(project=self.project_id, dataset=self.dataset_id)

            query_file = query_dir / f"{query_name}.sql"
            with open(query_file, "w") as f:
                f.write(formatted_sql)

        logger.info(f"✅ Created analysis queries in {query_dir}")

    def create_data_sources_guide(self):
        """Create comprehensive guide to DNO data sources."""

        guide = """# DNO Data Sources Guide

## 🏢 Distribution Network Operators (DNOs)

### UKPN (UK Power Networks)
- **Portal**: https://ukpowernetworks.opendatasoft.com/
- **Coverage**: London, East & South East England
- **Key Datasets**:
  - Network capacity data (LTDS)
  - Outage information
  - Flexibility services
  - Connection queue data
- **API**: OpenDataSoft API (currently restricted)
- **Update Frequency**: Monthly/Quarterly

### NGED (National Grid Electricity Distribution)
- **Portal**: https://connecteddata.nationalgrid.co.uk/
- **Coverage**: Midlands, South West, South Wales
- **Key Datasets**:
  - DFES (Distribution Future Energy Scenarios)
  - Flexibility procurement
  - Network capacity
  - Asset health data
- **API**: CKAN API (requires free token)
- **Update Frequency**: Monthly

### Northern Powergrid (NPg)
- **Portal**: https://northernpowergrid.opendatasoft.com/
- **Coverage**: North East, Yorkshire
- **Key Datasets**:
  - Network headroom
  - Generation connections
  - Demand data
- **API**: OpenDataSoft API
- **Update Frequency**: Quarterly

### SP Energy Networks (SPEN)
- **Portal**: https://spenergynetworks.opendatasoft.com/
- **Coverage**: Central & Southern Scotland, North Wales, Merseyside, Cheshire
- **Key Datasets**:
  - Network capacity
  - Flexibility markets
  - Outage data
- **API**: OpenDataSoft API
- **Update Frequency**: Monthly

### Electricity North West (ENWL)
- **Portal**: https://electricitynorthwest.opendatasoft.com/
- **Coverage**: North West England
- **Key Datasets**:
  - CLASS (Customer Load Active System Services)
  - Network capacity
  - Innovation projects
- **API**: OpenDataSoft API
- **Update Frequency**: Monthly

### SSE Networks (SSEN)
- **Portal**: https://data.ssen.co.uk/
- **Coverage**: Central Southern England, North Scotland
- **Key Datasets**:
  - Network data
  - Flexibility services
  - Future energy scenarios
- **API**: Mixed (some CSV, some API)
- **Update Frequency**: Quarterly

## 🔑 Getting API Access

### For NGED (National Grid):
1. Visit: https://connecteddata.nationalgrid.co.uk/
2. Register for free account
3. Request API token
4. Set environment variable: `export NGED_API_TOKEN="your_token"`

### For OpenDataSoft portals (UKPN, SPEN, NPg, ENWL):
- Currently restricted - contact DNO directly
- Some datasets available via direct CSV links
- Check for public datasets that don't require authentication

## 📊 Key Data Types

### Network Capacity Data
- **Purpose**: Identify constraint locations
- **Integration**: Compare with BMRS balancing actions
- **Frequency**: Monthly updates
- **Format**: CSV with GSP/BSP mappings

### Flexibility Services
- **Purpose**: Track local solution procurement
- **Integration**: Correlate with system frequency/voltage events
- **Frequency**: Real-time to daily
- **Format**: JSON/CSV with temporal data

### Outage Information
- **Purpose**: Understand supply interruptions
- **Integration**: Impact on national balancing
- **Frequency**: Real-time
- **Format**: Event logs with timestamps

### Asset Health Data
- **Purpose**: Predict network issues
- **Integration**: Correlate with market price volatility
- **Frequency**: Annual/bi-annual
- **Format**: GIS data with condition scores

## 🔄 Integration with BMRS Data

### Temporal Alignment
- Match DNO data timestamps with BMRS settlement periods
- Handle different time resolutions (5-min vs hourly vs daily)
- Account for BST/UTC timezone differences

### Geographic Mapping
- Map DNO areas to GSP groups in BMRS data
- Use postcode/geographic references for spatial analysis
- Link network constraints to balancing mechanism usage

### Cross-Dataset Analysis Opportunities
1. **Constraint Correlation**: DNO capacity limits vs BMRS constraint costs
2. **Flexibility Impact**: Local services vs system-wide balancing
3. **Outage Effects**: Supply interruptions vs frequency response
4. **Investment Planning**: Network capacity vs future BMRS trends

## 🛠 Technical Implementation

### Data Pipeline
1. **Extract**: Automated collection from DNO APIs
2. **Transform**: Standardize formats and timestamps
3. **Load**: Store in BigQuery alongside BMRS data
4. **Analyze**: Cross-dataset queries and visualizations

### Quality Assurance
- Validate timestamp formats and timezone handling
- Check for data completeness and accuracy
- Monitor for schema changes in source APIs
- Implement automated alerts for missing data

## 📈 Analysis Examples

See the `/analysis_queries/` folder for SQL examples of:
- DNO-BMRS correlation analysis
- Flexibility service effectiveness
- Outage impact assessment
- Network constraint prediction
"""

        guide_path = OUT_DIR / "dno_data_sources_guide.md"
        with open(guide_path, "w") as f:
            f.write(guide)

        logger.info(f"✅ Created data sources guide: {guide_path}")

    def create_integration_template(self):
        """Create template for DNO data integration."""

        template = '''#!/usr/bin/env python3
"""
DNO Data Integration Template
============================

Template for integrating DNO data with your existing BMRS pipeline.
Customize this for specific DNO data sources as they become available.
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta

class DNOIntegrator:
    """Integrate DNO data with BMRS data pipeline."""

    def __init__(self):
        self.client = bigquery.Client(project="jibber-jabber-knowledge")
        self.dataset = "uk_energy_insights"

    def ingest_dno_csv(self, csv_path: str, dno_id: str, data_type: str):
        """Ingest DNO CSV data into BigQuery."""

        # Read and clean data
        df = pd.read_csv(csv_path)
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]

        # Add metadata
        df['dno_id'] = dno_id
        df['data_source'] = f"{dno_id}_{data_type}"
        df['ingested_at'] = datetime.now()

        # Determine target table
        table_map = {
            'capacity': 'dno_capacity_data',
            'flexibility': 'dno_flexibility_data',
            'outage': 'dno_outage_data',
            'asset': 'dno_asset_data'
        }

        table_name = table_map.get(data_type, f'dno_{data_type}_data')
        table_id = f"{self.client.project}.{self.dataset}.{table_name}"

        # Load to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            autodetect=True
        )

        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()

        print(f"✅ Loaded {len(df)} rows to {table_name}")

    def analyze_dno_bmrs_correlation(self, start_date: str, end_date: str):
        """Analyze correlation between DNO and BMRS data."""

        query = f"""
        SELECT
            d.dno_id,
            d.gsp_name,
            d.available_capacity_mva,
            DATE(b.settlement_date) as date,
            COUNT(b.settlement_period) as balancing_actions,
            AVG(CAST(b.so_flag AS FLOAT64)) as avg_so_involvement
        FROM `{self.client.project}.{self.dataset}.dno_capacity_data` d
        JOIN `{self.client.project}.{self.dataset}.bmrs_bod` b
            ON DATE(b.settlement_date) = d.recorded_date
        WHERE d.recorded_date BETWEEN '{start_date}' AND '{end_date}'
            AND d.available_capacity_mva IS NOT NULL
        GROUP BY d.dno_id, d.gsp_name, d.available_capacity_mva, DATE(b.settlement_date)
        ORDER BY balancing_actions DESC
        LIMIT 100
        """

        return self.client.query(query).to_dataframe()

# Usage example:
if __name__ == "__main__":
    integrator = DNOIntegrator()

    # Example: Load DNO capacity data
    # integrator.ingest_dno_csv("ukpn_capacity.csv", "UKPN-EPN", "capacity")

    # Example: Analyze correlation
    # results = integrator.analyze_dno_bmrs_correlation("2025-08-01", "2025-09-01")
    # print(results.head())

    print("DNO integration template ready!")
'''

        template_path = OUT_DIR / "dno_integration_template.py"
        with open(template_path, "w") as f:
            f.write(template)

        logger.info(f"✅ Created integration template: {template_path}")


def main():
    """Main execution."""

    logger.info("🏗️ Setting up DNO Data Framework")
    logger.info("=" * 50)

    framework = DNOFramework()

    # Create database schemas
    framework.create_dno_schema()

    # Create analysis queries
    framework.create_analysis_queries()

    # Create documentation
    framework.create_data_sources_guide()

    # Create integration template
    framework.create_integration_template()

    logger.info("✅ DNO Framework setup complete!")
    logger.info(f"📁 Framework files created in: {OUT_DIR}")

    print("\n🎯 FRAMEWORK READY!")
    print("=" * 30)
    print("✅ BigQuery schemas created with sample data")
    print("✅ Analysis queries prepared")
    print("✅ Data sources guide documented")
    print("✅ Integration template provided")

    print(f"\n📂 Files created in: {OUT_DIR}")
    print("- dno_data_sources_guide.md")
    print("- dno_integration_template.py")
    print("- analysis_queries/*.sql")

    print("\n🚀 NEXT STEPS:")
    print("1. Review the data sources guide")
    print("2. Get API tokens for accessible DNO portals")
    print("3. Use integration template for custom data sources")
    print("4. Run analysis queries on your BMRS + DNO data")


if __name__ == "__main__":
    main()
