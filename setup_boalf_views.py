#!/usr/bin/env python3
"""
Create BOALF Analysis Views and Tables

Purpose: Set up production-ready views for battery arbitrage analysis
         and audit compliance using derived BOALF acceptance prices

Creates:
  1. boalf_with_prices view - Filtered to Valid records, enriched with revenue fields
  2. boalf_outliers_excluded table - Audit trail of excluded acceptances
"""

from google.cloud import bigquery
import logging

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def create_analysis_view(client):
    """Create boalf_with_prices view for analysis"""
    
    logging.info("Creating boalf_with_prices view...")
    
    query = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.boalf_with_prices` AS
    WITH valid_acceptances AS (
      SELECT 
        -- Primary keys
        acceptanceNumber,
        acceptanceTime,
        bmUnit,
        settlementDate,
        settlementPeriod,
        
        -- Time periods
        timeFrom,
        timeTo,
        
        -- Levels (MW)
        levelFrom,
        levelTo,
        
        -- Derived price fields
        acceptancePrice,      -- £/MWh from BOD matching
        acceptanceVolume,     -- MWh (ABS of level change)
        acceptanceType,       -- BID | OFFER | UNKNOWN
        
        -- Metadata flags
        soFlag,
        storFlag,
        rrFlag,
        deemedBoFlag,
        
        -- Source tracking
        _price_source,
        _matched_pairId,
        _ingested_utc
        
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE validation_flag = 'Valid'
    ),
    
    enriched AS (
      SELECT 
        *,
        
        -- Revenue estimate (£)
        ROUND(acceptancePrice * acceptanceVolume, 2) AS revenue_estimate_gbp,
        
        -- Unit categorization
        CASE
          WHEN bmUnit IN ('FBPGM002', 'FFSEN005', 'FSSEN001', 'FBRGM003') 
            THEN 'VLP_Battery'
          WHEN bmUnit LIKE 'T_%' THEN 'Transmission_Generation'
          WHEN bmUnit IN ('E_ELEC', 'E_IFA', 'E_IFA2', 'E_NEMO', 'E_NRWL', 'E_MOYL', 'E_NSL') 
            THEN 'Interconnector'
          WHEN bmUnit LIKE 'E_%' THEN 'Embedded_Generation'
          WHEN bmUnit LIKE 'D_%' THEN 'Demand'
          ELSE 'Other'
        END AS unit_category,
        
        -- Time analysis fields
        FLOOR((settlementPeriod - 1) / 2) AS settlement_hour,
        DATE(settlementDate) AS settlement_date,
        EXTRACT(YEAR FROM settlementDate) AS year,
        EXTRACT(MONTH FROM settlementDate) AS month,
        EXTRACT(DAYOFWEEK FROM settlementDate) AS day_of_week,
        
        -- Peak vs Off-peak
        CASE
          WHEN EXTRACT(DAYOFWEEK FROM settlementDate) IN (1, 7) THEN 'Weekend'
          WHEN FLOOR((settlementPeriod - 1) / 2) BETWEEN 16 AND 19 THEN 'Peak'
          WHEN FLOOR((settlementPeriod - 1) / 2) BETWEEN 8 AND 15 THEN 'Shoulder'
          ELSE 'Off_Peak'
        END AS time_band
        
      FROM valid_acceptances
    )
    
    SELECT * FROM enriched
    ORDER BY settlementDate, settlementPeriod, acceptanceNumber
    """
    
    client.query(query).result()
    logging.info("✅ Created boalf_with_prices view")


def create_outliers_table(client):
    """Create boalf_outliers_excluded table for audit compliance"""
    
    logging.info("Creating boalf_outliers_excluded table...")
    
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.boalf_outliers_excluded` 
    PARTITION BY DATE(settlementDate)
    CLUSTER BY validation_flag, bmUnit
    AS
    SELECT 
      -- Primary keys
      acceptanceNumber,
      acceptanceTime,
      bmUnit,
      settlementDate,
      settlementPeriod,
      
      -- Original data
      levelFrom,
      levelTo,
      acceptancePrice,
      acceptanceVolume,
      acceptanceType,
      
      -- Validation status
      validation_flag,
      
      -- Detailed exclusion reason
      CASE validation_flag
        WHEN 'Price_Outlier' THEN CONCAT(
          'Acceptance price (£', 
          ROUND(acceptancePrice, 2), 
          '/MWh) exceeds Elexon B1610 ±£1,000/MWh threshold'
        )
        WHEN 'SO_Test' THEN CONCAT(
          'System Operator test/system record (soFlag=',
          CAST(soFlag AS STRING),
          ') per Elexon B1610 Section 4.3 exclusion criteria'
        )
        WHEN 'Low_Volume' THEN CONCAT(
          'Acceptance volume (',
          ROUND(acceptanceVolume, 4),
          ' MWh) below 0.001 MWh regulatory threshold'
        )
        WHEN 'Unmatched' THEN 
          'No matching BOD submission found (bmUnit + settlementDate + period)'
        ELSE 'Unknown exclusion reason'
      END AS exclusion_reason,
      
      -- Metadata
      soFlag,
      storFlag,
      rrFlag,
      deemedBoFlag,
      
      -- Source tracking
      _price_source,
      _matched_pairId,
      _ingested_utc,
      
      -- Audit timestamp
      CURRENT_TIMESTAMP() AS _excluded_at
      
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
    WHERE validation_flag != 'Valid'
    """
    
    client.query(query).result()
    logging.info("✅ Created boalf_outliers_excluded table")


def verify_views(client):
    """Verify created views and tables"""
    
    logging.info("\nVerifying created views and tables...")
    
    # Check view
    view_query = f"""
    SELECT 
      COUNT(*) as total_records,
      COUNT(DISTINCT bmUnit) as num_units,
      MIN(DATE(settlementDate)) as earliest_date,
      MAX(DATE(settlementDate)) as latest_date,
      ROUND(AVG(acceptancePrice), 2) as avg_price,
      SUM(CASE WHEN unit_category = 'VLP_Battery' THEN 1 ELSE 0 END) as vlp_records
    FROM `{PROJECT_ID}.{DATASET}.boalf_with_prices`
    """
    
    view_result = client.query(view_query).to_dataframe()
    logging.info("\n✅ boalf_with_prices view:")
    logging.info(f"  Total records: {view_result['total_records'].iloc[0]:,}")
    logging.info(f"  Unique units: {view_result['num_units'].iloc[0]}")
    logging.info(f"  Date range: {view_result['earliest_date'].iloc[0]} to {view_result['latest_date'].iloc[0]}")
    logging.info(f"  Average price: £{view_result['avg_price'].iloc[0]}/MWh")
    logging.info(f"  VLP battery records: {view_result['vlp_records'].iloc[0]:,}")
    
    # Check outliers table
    outlier_query = f"""
    SELECT 
      validation_flag,
      COUNT(*) as num_records,
      ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
    FROM `{PROJECT_ID}.{DATASET}.boalf_outliers_excluded`
    GROUP BY validation_flag
    ORDER BY num_records DESC
    """
    
    outlier_result = client.query(outlier_query).to_dataframe()
    logging.info("\n✅ boalf_outliers_excluded table:")
    for _, row in outlier_result.iterrows():
        logging.info(f"  {row['validation_flag']}: {int(row['num_records']):,} ({row['percentage']:.1f}%)")


def main():
    """Main execution"""
    
    logging.info("="*60)
    logging.info("BOALF Analysis Views Creation")
    logging.info("="*60)
    logging.info(f"Project: {PROJECT_ID}")
    logging.info(f"Dataset: {DATASET}")
    logging.info("")
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=PROJECT_ID, location="US")
        
        # Create views and tables
        create_analysis_view(client)
        create_outliers_table(client)
        
        # Verify creation
        verify_views(client)
        
        logging.info("\n" + "="*60)
        logging.info("✅ All views and tables created successfully")
        logging.info("="*60)
        
        logging.info("\nUsage examples:")
        logging.info("  # Battery revenue analysis")
        logging.info("  SELECT bmUnit, SUM(revenue_estimate_gbp) as total_revenue")
        logging.info("  FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices`")
        logging.info("  WHERE unit_category = 'VLP_Battery' AND acceptanceType = 'OFFER'")
        logging.info("  GROUP BY bmUnit;")
        logging.info("")
        logging.info("  # Outlier audit report")
        logging.info("  SELECT validation_flag, COUNT(*) as count")
        logging.info("  FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_outliers_excluded`")
        logging.info("  GROUP BY validation_flag;")
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
