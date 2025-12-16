#!/usr/bin/env python3
"""
IRIS BOALF Price Derivation Enhancement

Purpose: Add real-time BOD price derivation to BOALF IRIS uploads
Deploy to: Dell SSH machine at /opt/iris-pipeline/

This script enhances iris_to_bigquery_unified.py to derive acceptance prices
in real-time by matching with bmrs_bod_iris table.

Installation:
1. SSH to Dell: ssh root@94.237.55.234
2. Backup current script: cp /opt/iris-pipeline/scripts/iris_to_bigquery_unified.py /opt/iris-pipeline/scripts/iris_to_bigquery_unified.py.backup
3. Copy this enhancement
4. Restart service: systemctl restart iris-pipeline

"""

# Add this after the IrisUploader class definition in iris_to_bigquery_unified.py

    def _derive_boalf_prices(self, boalf_records):
        """
        Derive acceptance prices for BOALF records by matching with BOD data
        
        Similar logic to derive_boalf_prices.py but for real-time IRIS data
        
        Args:
            boalf_records: List of BOALF record dicts
        
        Returns:
            list: Enhanced records with derived price fields
        """
        if not boalf_records:
            return []
        
        logger.info(f"Deriving prices for {len(boalf_records)} BOALF records...")
        
        try:
            # Extract unique bmUnit + settlementDate + settlementPeriod combinations
            lookup_keys = set()
            for record in boalf_records:
                key = (
                    record.get('bmUnit'),
                    record.get('settlementDate'),
                    record.get('settlementPeriod')
                )
                lookup_keys.add(key)
            
            # Build query to get matching BOD records
            conditions = []
            for bmUnit, settDate, settPeriod in lookup_keys:
                if bmUnit and settDate and settPeriod:
                    conditions.append(f"""
                        (bmUnit = '{bmUnit}' 
                         AND DATE(settlementDate) = DATE('{settDate}')
                         AND settlementPeriod = {settPeriod})
                    """)
            
            if not conditions:
                logger.warning("No valid lookup keys for BOD matching")
                return self._add_default_price_fields(boalf_records)
            
            # Query bmrs_bod_iris for matching bids/offers
            bod_query = f"""
            SELECT 
                bmUnit,
                DATE(settlementDate) as settlement_date,
                settlementPeriod,
                pairId,
                offer,
                bid
            FROM `{self.project_id}.{self.dataset}.bmrs_bod_iris`
            WHERE ({' OR '.join(conditions)})
              AND ABS(COALESCE(offer, 0)) <= 1000  -- Elexon B1610 filter
              AND ABS(COALESCE(bid, 0)) <= 1000
            """
            
            bod_df = self.client.query(bod_query).to_dataframe()
            
            if len(bod_df) == 0:
                logger.warning("No matching BOD records found")
                return self._add_default_price_fields(boalf_records)
            
            logger.info(f"Found {len(bod_df)} matching BOD records")
            
            # Match and derive prices
            enhanced_records = []
            for record in boalf_records:
                # Find matching BOD record
                matched_bod = bod_df[
                    (bod_df['bmUnit'] == record.get('bmUnit')) &
                    (bod_df['settlement_date'].astype(str) == record.get('settlementDate')[:10]) &
                    (bod_df['settlementPeriod'] == record.get('settlementPeriod'))
                ]
                
                if len(matched_bod) > 0:
                    # Use first match
                    bod = matched_bod.iloc[0]
                    
                    # Derive acceptance type from level change
                    level_from = record.get('levelFrom', 0)
                    level_to = record.get('levelTo', 0)
                    
                    if level_to > level_from:
                        acceptance_type = 'OFFER'
                        acceptance_price = bod['offer']
                    elif level_to < level_from:
                        acceptance_type = 'BID'
                        acceptance_price = bod['bid']
                    else:
                        acceptance_type = 'UNKNOWN'
                        acceptance_price = None
                    
                    # Derive volume
                    acceptance_volume = abs(level_to - level_from)
                    
                    # Determine validation flag (Elexon B1610 Section 4.3)
                    so_flag = record.get('soFlag', False)
                    
                    if so_flag:
                        validation_flag = 'SO_Test'
                    elif acceptance_volume < 0.001:
                        validation_flag = 'Low_Volume'
                    elif acceptance_price and abs(acceptance_price) > 1000:
                        validation_flag = 'Price_Outlier'
                    elif acceptance_price is not None:
                        validation_flag = 'Valid'
                    else:
                        validation_flag = 'Unmatched'
                    
                    # Add derived fields
                    record['acceptancePrice'] = float(acceptance_price) if acceptance_price is not None else None
                    record['acceptanceVolume'] = float(acceptance_volume)
                    record['acceptanceType'] = acceptance_type
                    record['validation_flag'] = validation_flag
                    record['_price_source'] = 'BOD_REALTIME'
                    record['_matched_pairId'] = str(bod['pairId'])
                else:
                    # No match found
                    record['acceptancePrice'] = None
                    record['acceptanceVolume'] = abs(record.get('levelTo', 0) - record.get('levelFrom', 0))
                    record['acceptanceType'] = 'UNKNOWN'
                    record['validation_flag'] = 'Unmatched'
                    record['_price_source'] = 'UNMATCHED'
                    record['_matched_pairId'] = None
                
                enhanced_records.append(record)
            
            # Log statistics
            matched = sum(1 for r in enhanced_records if r['_price_source'] == 'BOD_REALTIME')
            valid = sum(1 for r in enhanced_records if r.get('validation_flag') == 'Valid')
            
            logger.info(f"BOALF price derivation results:")
            logger.info(f"  Matched with BOD: {matched}/{len(enhanced_records)} ({matched/len(enhanced_records)*100:.1f}%)")
            logger.info(f"  Valid records: {valid}/{len(enhanced_records)} ({valid/len(enhanced_records)*100:.1f}%)")
            
            return enhanced_records
            
        except Exception as e:
            logger.error(f"Error in BOALF price derivation: {e}")
            return self._add_default_price_fields(boalf_records)
    
    def _add_default_price_fields(self, boalf_records):
        """Add default null price fields when derivation fails"""
        for record in boalf_records:
            record['acceptancePrice'] = None
            record['acceptanceVolume'] = abs(record.get('levelTo', 0) - record.get('levelFrom', 0))
            record['acceptanceType'] = 'UNKNOWN'
            record['validation_flag'] = 'Unmatched'
            record['_price_source'] = 'UNMATCHED'
            record['_matched_pairId'] = None
        return boalf_records
    
    # MODIFY the existing _extract_records method to call _derive_boalf_prices for BOALF data:
    
    def _extract_records_enhanced(self, data, report_type):
        """
        Enhanced version of _extract_records with BOALF price derivation
        
        REPLACE the existing _extract_records method with this
        """
        records = []
        
        # Handle array format (e.g., WINDFOR)
        if isinstance(data, list):
            records = data
        # Handle dict format with nested data
        elif 'data' in data:
            records = data['data']
        elif 'items' in data:
            records = data['items']
        else:
            # Single record format
            records = [data]
        
        # Add metadata to each record
        for record in records:
            record['ingested_utc'] = datetime.utcnow().isoformat()
            record['source'] = 'IRIS'
        
        # BOALF: Derive acceptance prices from BOD matching
        if report_type in ['BOALF', 'B1430']:
            records = self._derive_boalf_prices(records)
        
        return records


# ==============================================================================
# DEPLOYMENT INSTRUCTIONS
# ==============================================================================

# Step 1: SSH to Dell server
# ssh root@94.237.55.234

# Step 2: Backup current script
# cd /opt/iris-pipeline/scripts
# cp iris_to_bigquery_unified.py iris_to_bigquery_unified.py.backup_$(date +%Y%m%d_%H%M%S)

# Step 3: Edit the file
# nano iris_to_bigquery_unified.py

# Step 4: Add the two new methods (_derive_boalf_prices and _add_default_price_fields)
#         after the _upload_records method (around line 170)

# Step 5: Replace _extract_records with _extract_records_enhanced
#         Rename: def _extract_records( → def _extract_records_enhanced(
#         OR: Copy the "BOALF derivation" section into existing _extract_records

# Step 6: Update bmrs_boalf_iris table schema to match bmrs_boalf_complete
# bq update --schema acceptancePrice:FLOAT,acceptanceVolume:FLOAT,acceptanceType:STRING,validation_flag:STRING,_price_source:STRING,_matched_pairId:STRING \
#   inner-cinema-476211-u9:uk_energy_prod.bmrs_boalf_iris

# Step 7: Restart IRIS pipeline service
# systemctl restart iris-pipeline
# systemctl status iris-pipeline

# Step 8: Monitor logs for BOALF processing
# tail -f /opt/iris-pipeline/logs/iris_uploader.log | grep -E "BOALF|price derivation"

# Step 9: Verify data in BigQuery
# SELECT 
#   COUNT(*) as total,
#   SUM(CASE WHEN validation_flag='Valid' THEN 1 ELSE 0 END) as valid,
#   AVG(acceptancePrice) as avg_price
# FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
# WHERE _price_source = 'BOD_REALTIME'

# ==============================================================================
# TESTING ON DELL
# ==============================================================================

# Test the enhanced script before deployment:
# python3 -c "
# import sys
# sys.path.insert(0, '/opt/iris-pipeline/scripts')
# from iris_to_bigquery_unified import IrisUploader
# uploader = IrisUploader()
# print('✅ Import successful')
# print('Methods:', [m for m in dir(uploader) if 'boalf' in m.lower()])
# "
